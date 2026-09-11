"""Per-user and per-IP rate limiting, backed by Redis.

Phase 2. The counter arithmetic is not implemented here: slowapi wraps the
`limits` library, which owns the window algorithm and the Redis storage. This
module supplies the three things that are actually specific to Fahem - what to
key a limit on, what a 429 looks like, and where the store lives.

Two keying strategies, because the endpoints differ in what they know:

- /solve and /solve/stream run behind auth, so they key on the authenticated
  user's id. That is more precise than an IP and much harder to route around -
  and it avoids bucketing a whole school behind one NAT into a single budget,
  which is exactly what IP limiting would do to the students this is for.

- /auth/google is reachable before a user exists, so it keys on client IP.
  See config.RATE_LIMIT_AUTH for why that limit is deliberately loose and what
  it does and does not protect against.

Why user_key() reads request.state rather than re-decoding the cookie: the
limit must be keyed on the *same* identity the auth gate authorised. Decoding
the token again would key on whoever the token claims to be, which can differ
from what get_current_user resolved - a deleted account still has a
well-formed unexpired token, and would be rejected by the gate while
consuming a rate-limit slot under its own key. bind_user() is what puts the
resolved identity where the key function can see it.
"""

from __future__ import annotations

import hashlib
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from limits import parse_many
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import RATE_LIMIT_RETRY_AFTER_FALLBACK, REDIS_URL

# This module deliberately does NOT import auth. auth.py imports it (for the
# /auth/google decorator), so importing auth back would be a cycle. The
# dependency that resolves the user and publishes the id this module keys on
# lives in auth.py as bind_user() - the identity half is an auth concern
# anyway; only the key function belongs here.

# Scope name shared by /solve and /solve/stream so they draw on one budget.
# Separate buckets would let a caller double the spend by alternating between
# two endpoints that do identical work.
SOLVE_SCOPE = "solve"

# Attribute name on request.state. Not a magic string at two call sites.
STATE_USER_ID = "rate_limit_user_id"


def user_key(request: Request) -> str:
    """Rate-limit key for an authenticated route: the resolved user's id.

    Falls back to the client IP if the identity is missing. That should be
    unreachable - bind_user() depends on get_current_user, which 401s before
    this runs - but a key function that returns None makes slowapi bucket
    every caller together, which would turn a bug here into a global limit
    for all users at once. Failing to an IP key keeps the blast radius small.
    """
    user_id = getattr(request.state, STATE_USER_ID, None)
    if user_id is None:
        return f"ip:{get_remote_address(request)}"
    return f"user:{user_id}"


def ip_key(request: Request) -> str:
    """Rate-limit key for a pre-login route.

    get_remote_address reads request.client.host directly and does NOT trust
    X-Forwarded-For. That is correct while nothing sits in front of uvicorn:
    honouring a client-supplied header would let anyone reset their own
    counter by inventing an IP. Behind a real proxy this needs revisiting
    together with uvicorn's --proxy-headers, or every request will key on the
    proxy's address and share one bucket.
    """
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=user_key,
    storage_uri=REDIS_URL,
    # Emit X-RateLimit-* on every response, not just rejections, so a client
    # can see it approaching the ceiling instead of discovering it by being
    # refused.
    headers_enabled=True,
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 with a Retry-After the client can actually act on.

    slowapi's stock handler is replaced rather than reused because Retry-After
    is a requirement here, and the stock one does not guarantee it. The real
    reset time comes from the limiter's own window state when available; the
    configured fallback covers the case where it cannot be derived, since a
    429 with no Retry-After leaves a client guessing.
    """
    retry_after = RATE_LIMIT_RETRY_AFTER_FALLBACK
    try:
        # slowapi stashes (RateLimitItem, key_parts) here while evaluating the
        # limit, and its own header injection reads exactly this. Reconstructing
        # the key any other way gets the scope arguments wrong and silently
        # falls back, which is what an earlier version of this handler did -
        # every 429 reported the fallback rather than the real reset.
        limit_item, key_parts = request.state.view_rate_limit
        reset_at, _remaining = request.app.state.limiter.limiter.get_window_stats(
            limit_item, *key_parts
        )
        # get_window_stats returns an absolute reset epoch; Retry-After is
        # defined as relative seconds. Floor at 1 so a sub-second remainder
        # never renders as "retry in 0 seconds".
        retry_after = max(1, int(reset_at - time.time()))
    except Exception:
        # Any failure to introspect the window falls back to the configured
        # value. A slightly-too-large Retry-After beats a missing one, and
        # beats a 500 raised from inside an error handler.
        pass

    return _too_many(str(exc.limit.limit), retry_after)


def _too_many(limit: str, retry_after: int) -> JSONResponse:
    """The one 429 shape, shared by the decorator limits and hit_keyed()."""
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "rate limit exceeded",
            "limit": limit,
            "retry_after": retry_after,
        },
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


# --- limits keyed on something inside the request body -------------------------
#
# slowapi's key functions run before the body is parsed, so they cannot key on
# an email address. hit_keyed() is the same `limits` storage and window
# arithmetic, called from inside a handler once the body is known.


class KeyedRateLimitExceeded(Exception):
    def __init__(self, limit: str, retry_after: int) -> None:
        super().__init__(limit)
        self.limit = limit
        self.retry_after = retry_after


def email_key(email: str) -> str:
    """A rate-limit key for an address, without putting the address in Redis."""
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
    return f"email:{digest[:32]}"


def hit_keyed(limits_spec: str, scope: str, key: str) -> None:
    """Count one hit against every window in `limits_spec`; raise on the first
    exceeded. Uses slowapi's own strategy object, so it shares storage and
    configuration with the decorator limits."""
    strategy = limiter.limiter
    for item in parse_many(limits_spec):
        if not strategy.hit(item, scope, key):
            reset_at, _remaining = strategy.get_window_stats(item, scope, key)
            raise KeyedRateLimitExceeded(str(item), max(1, int(reset_at - time.time())))


def keyed_rate_limit_handler(request: Request, exc: KeyedRateLimitExceeded) -> JSONResponse:
    return _too_many(exc.limit, exc.retry_after)
