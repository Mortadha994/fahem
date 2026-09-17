"""Settings an admin changes from the console while Fahem runs.

config.py still holds every default, read once at start. This module lets a
handful of them be changed live - no restart, no redeploy - from the admin
console's "Contrôle de l'IA" panel:

  ai_paused                 bool   every model call refused with the pause
                                   message (maintenance)
  ai_pause_message          str    what students read while paused
  daily_budget_guard_pct    int    0 = off (default 90); else refuse new model calls once
                                   the text model has used this % of Groq's
                                   daily token limit (keeps a reserve)
  solve_rate_limit          str    the per-student limit, "10/minute;100/hour"
  queue_timeout_seconds     int    how long one request may wait for Groq
  retry_max                 int    429 retries inside a slot
  attachments_enabled       bool   photo / PDF reading on or off
  guided_mode_enabled       bool   the chat's "Mode guidé" (hints before the solution)
  check_answer_enabled      bool   the chat's "Vérifier ma réponse"
  default_chat_mode         str    "full" or "guided": a new discussion's mode
  practice_enabled          bool   the chat's "Exercice similaire"
  practice_daily_limit      int    similar exercises one student may generate per day

A row in app_settings exists only for a key that was changed; get() falls
back to the default. Values are validated on the way in (set_many), so
readers never see a malformed one.

Reads are on hot paths (every solve checks the pause and the rate limit), so
they come from a per-process cache refreshed every CACHE_SECONDS. A change is
applied at once in the process that made it and within CACHE_SECONDS in any
other. A database that cannot be read serves the defaults, logged: a settings
outage must not take solving down with it.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from limits import parse_many

from config import GROQ_QUEUE_TIMEOUT_SECONDS, GROQ_RETRY_MAX, RATE_LIMIT_SOLVE

log = logging.getLogger("fahem.runtime_settings")

CACHE_SECONDS = 5.0


class InvalidSetting(ValueError):
    """A value an admin tried to set that is not allowed; the message is French."""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    raise InvalidSetting("Valeur attendue : vrai ou faux.")


def _int_between(low: int, high: int) -> Callable[[Any], int]:
    def check(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise InvalidSetting(f"Valeur attendue : un nombre entier entre {low} et {high}.")
        value = int(value)
        if not low <= value <= high:
            raise InvalidSetting(f"Valeur attendue : un nombre entier entre {low} et {high}.")
        return value

    return check


def _budget_pct(value: Any) -> int:
    value = _int_between(0, 100)(value)
    if 0 < value < 50:
        raise InvalidSetting("Le garde-fou se règle entre 50 et 100 %, ou 0 pour le désactiver.")
    return value


def rate_limit(value: Any) -> str:
    """ "10/minute;100/hour" - checked with the same parser slowapi uses."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidSetting("Limite attendue, par exemple « 10/minute;100/hour ».")
    text = value.strip()
    try:
        items = parse_many(text)
    except ValueError as exc:
        raise InvalidSetting("Limite illisible, par exemple « 10/minute;100/hour ».") from exc
    if not items or any(item.amount < 1 for item in items):
        raise InvalidSetting("Chaque limite doit autoriser au moins une requête.")
    return text


def _message(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidSetting("Le message ne peut pas être vide.")
    if len(value) > 300:
        raise InvalidSetting("Le message est limité à 300 caractères.")
    return value.strip()


def _chat_mode(value: Any) -> str:
    if value not in ("full", "guided"):
        raise InvalidSetting("Mode attendu : « full » (solution complète) ou « guided » (guidé).")
    return value


@dataclass(frozen=True)
class Spec:
    default: Any
    validate: Callable[[Any], Any]


SPECS: dict[str, Spec] = {
    "ai_paused": Spec(False, _bool),
    "ai_pause_message": Spec(
        "Fahem est en maintenance pour quelques minutes. Réessaie un peu plus tard.", _message
    ),
    # On by default: the free tier's daily tokens run out long before the
    # per-minute ones, and an exhausted day answers every student "service
    # très sollicité". 90 % keeps a reserve for the rest of the day.
    "daily_budget_guard_pct": Spec(90, _budget_pct),
    "solve_rate_limit": Spec(RATE_LIMIT_SOLVE, rate_limit),
    "queue_timeout_seconds": Spec(int(GROQ_QUEUE_TIMEOUT_SECONDS), _int_between(15, 600)),
    "retry_max": Spec(GROQ_RETRY_MAX, _int_between(0, 5)),
    "attachments_enabled": Spec(True, _bool),
    "guided_mode_enabled": Spec(True, _bool),
    "check_answer_enabled": Spec(True, _bool),
    "default_chat_mode": Spec("full", _chat_mode),
    "practice_enabled": Spec(True, _bool),
    "practice_daily_limit": Spec(10, _int_between(1, 100)),
}


@dataclass(frozen=True)
class Stored:
    value: Any
    updated_at: datetime | None
    updated_by: str | None


_cache: tuple[float, dict[str, Stored]] | None = None
_lock = threading.Lock()


def _load() -> dict[str, Stored]:
    from db import session_scope
    from models import AppSetting

    with session_scope() as s:
        rows = s.query(AppSetting).all()
        return {r.key: Stored(r.value, r.updated_at, r.updated_by) for r in rows if r.key in SPECS}


def _stored() -> dict[str, Stored]:
    global _cache
    now = time.monotonic()
    with _lock:
        if _cache is not None and now - _cache[0] < CACHE_SECONDS:
            return _cache[1]
    try:
        stored = _load()
    except Exception:
        log.warning("could not read app_settings; serving defaults", exc_info=True)
        stored = {} if _cache is None else _cache[1]
    with _lock:
        _cache = (now, stored)
    return stored


def clear_cache() -> None:
    global _cache
    with _lock:
        _cache = None


def get(key: str) -> Any:
    spec = SPECS[key]
    stored = _stored().get(key)
    if stored is None:
        return spec.default
    try:
        return spec.validate(stored.value)
    except InvalidSetting:
        log.warning("stored value for %s is invalid; using the default", key)
        return spec.default


def snapshot() -> dict[str, dict[str, Any]]:
    """Every setting with its value, default, and who last changed it."""
    stored = _stored()
    out = {}
    for key, spec in SPECS.items():
        row = stored.get(key)
        out[key] = {
            "value": get(key),
            "default": spec.default,
            "updated_at": row.updated_at if row else None,
            "updated_by": row.updated_by if row else None,
        }
    return out


def set_many(
    values: dict[str, Any],
    admin_email: str,
    *,
    action: str = "settings.update",
    target: str | None = None,
) -> dict[str, tuple[Any, Any]]:
    """Validate every value, then write them in one transaction and log the
    change. Returns {key: (old, new)} for the keys whose value changed.
    Raises InvalidSetting (naming the key) before writing anything.
    `action`/`target` name the log entry (revert() logs settings.revert,
    with the reverted entry's id as target)."""
    from db import session_scope
    from models import AdminAuditEntry, AppSetting

    unknown = [k for k in values if k not in SPECS]
    if unknown:
        raise InvalidSetting(f"Réglage inconnu : {', '.join(unknown)}.")
    clean: dict[str, Any] = {}
    for key, value in values.items():
        try:
            clean[key] = SPECS[key].validate(value)
        except InvalidSetting as exc:
            raise InvalidSetting(f"{key} : {exc}") from exc

    changed: dict[str, tuple[Any, Any]] = {}
    with session_scope() as s:
        for key, value in clean.items():
            old = get(key)
            if old == value:
                continue
            row = s.get(AppSetting, key)
            if row is None:
                s.add(AppSetting(key=key, value=value, updated_by=admin_email))
            else:
                row.value = value
                row.updated_by = admin_email
            changed[key] = (old, value)
        if changed:
            s.add(
                AdminAuditEntry(
                    admin_email=admin_email,
                    action=action,
                    target=target or "ia",
                    detail={k: {"old": o, "new": n} for k, (o, n) in changed.items()},
                )
            )
    clear_cache()
    return changed


def audit(
    admin_email: str,
    action: str,
    target: str | None,
    detail: dict | None = None,
    *,
    target_id: str | None = None,
) -> None:
    """Record one admin action (outside settings) in admin_audit."""
    from db import session_scope
    from models import AdminAuditEntry

    with session_scope() as s:
        s.add(
            AdminAuditEntry(
                admin_email=admin_email,
                action=action,
                target=target,
                target_id=target_id,
                detail=detail,
            )
        )


# --- the action log ---------------------------------------------------------------

# What the console's log filters on. Every action name starts with its family.
AUDIT_CATEGORIES = {
    "ia": ("settings.",),
    "comptes": ("user.",),
    "files": ("queue.",),
}
REVERTIBLE_ACTIONS = ("settings.update", "settings.revert")


def _entry(r) -> dict[str, Any]:
    return {
        "id": r.id,
        "at": r.created_at,
        "admin_email": r.admin_email,
        "action": r.action,
        "target": r.target,
        "target_id": r.target_id,
        "detail": r.detail,
        "revertible": r.action in REVERTIBLE_ACTIONS and bool(r.detail),
    }


def query_audit(
    *,
    category: str | None = None,
    q: str = "",
    before: int | None = None,
    limit: int = 30,
) -> tuple[list[dict[str, Any]], int | None]:
    """A page of the log, newest first. `before` is the id to continue from;
    the second value is the id to pass for the next page, or None at the end."""
    from sqlalchemy import or_

    from db import session_scope
    from models import AdminAuditEntry

    with session_scope() as s:
        query = s.query(AdminAuditEntry)
        if category in AUDIT_CATEGORIES:
            query = query.filter(
                or_(
                    *(
                        AdminAuditEntry.action.startswith(prefix)
                        for prefix in AUDIT_CATEGORIES[category]
                    )
                )
            )
        if q.strip():
            term = (
                "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
            query = query.filter(
                or_(
                    AdminAuditEntry.admin_email.ilike(term, escape="\\"),
                    AdminAuditEntry.target.ilike(term, escape="\\"),
                )
            )
        if before is not None:
            query = query.filter(AdminAuditEntry.id < before)
        rows = query.order_by(AdminAuditEntry.id.desc()).limit(limit + 1).all()
        items = [_entry(r) for r in rows[:limit]]
    next_before = items[-1]["id"] if len(rows) > limit else None
    return items, next_before


def recent_audit(limit: int = 15) -> list[dict[str, Any]]:
    return query_audit(limit=limit)[0]


def revert(entry_id: int, admin_email: str) -> dict[str, tuple[Any, Any]]:
    """Put back the values a settings change replaced. Logged as its own
    settings.revert entry (target = the reverted entry's id). Raises
    LookupError for an unknown entry, InvalidSetting if it is not a settings
    change or nothing would change."""
    from db import session_scope
    from models import AdminAuditEntry

    with session_scope() as s:
        row = s.get(AdminAuditEntry, entry_id)
        if row is None:
            raise LookupError(entry_id)
        if row.action not in REVERTIBLE_ACTIONS or not row.detail:
            raise InvalidSetting("Seuls les changements de réglages peuvent être rétablis.")
        old_values = {
            key: change.get("old")
            for key, change in row.detail.items()
            if key in SPECS and isinstance(change, dict)
        }
    changed = set_many(old_values, admin_email, action="settings.revert", target=str(entry_id))
    if not changed:
        raise InvalidSetting("Les réglages ont déjà ces valeurs : rien à rétablir.")
    return changed
