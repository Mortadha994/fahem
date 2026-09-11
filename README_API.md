## Running the API

```
docker compose up --build -d                      # recommended: the whole stack
.venv/Scripts/python.exe -m uvicorn api:app --reload --port 8000   # or natively
```

Natively, Postgres, Qdrant and Redis still have to be running
(`docker compose up -d postgres qdrant redis`).

## Authentication and rate limits

Everything except `GET /health` and `POST /auth/google` needs a signed-in
session. Sign-in exchanges a Google ID token for Fahem's own session, carried
in an `httpOnly` cookie (`fahem_session` by default), so a browser client must
send requests with credentials (`fetch(..., { credentials: "include" })`).
Without a valid session a route answers **401** `{"detail": "not
authenticated"}`.

The cookie is `SameSite=Lax`, so the UI and the API must be *same-site*:
`localhost:5173 → localhost:8000` works, `localhost:5173 → 127.0.0.1:8000`
does not (the browser withholds the cookie and every call 401s).

| Limit | Keyed by | Default | Env var |
| --- | --- | --- | --- |
| `/solve` + `/solve/stream`, one shared budget | user | `10/minute;100/hour` | `RATE_LIMIT_SOLVE` |
| `POST /auth/google` | client IP | `30/minute` | `RATE_LIMIT_AUTH` |

Over the limit, a route answers **429** with a `Retry-After` header (seconds)
and:

```json
{ "detail": "rate limit exceeded", "limit": "10 per 1 minute", "retry_after": 47 }
```

Counters live in Redis. The stack waits for Redis to be healthy before
starting the backend, so a missing store never looks like an unlimited one.

`POST /solve`

```json
{ "problem": "Ecrire un programme qui ...", "niveau": "2eme", "chapitre": "1", "k": 5 }
```

Response:

```json
{
  "solution": "**1. Résumé du problème** ...",
  "niveau": "2eme",
  "chapitre": "1",
  "model": "openai/gpt-oss-120b",
  "pinned":    [{ "id": "...", "label": "Opérateurs arithmétiques et relationnels" }],
  "retrieved": [{ "id": "...", "section": "III. Les types standards",
                  "type": "prose", "score": 0.6691 }],
  "warnings": [],
  "elapsed_ms": 3730
}
```

`GET /health` returns `{"status":"ok","model":"..."}`.

Status codes: 401 without a valid session; 422 for a bad request body or a
niveau/chapitre with no pinned syntax core; 429 either from Fahem's own
per-user limit (with `Retry-After`, see above) or when the upstream
token-per-minute cap is hit (passed through, not masked as a server error);
502 if the model backend is unreachable.

`warnings` carries constraint-checker findings and is advisory only — the
checker has both missed real violations and raised false ones, so an empty
list is not a correctness guarantee.

## `POST /solve/stream`

Same request body as `/solve`. Returns `text/event-stream`. This is what the
UI uses; `/solve` is unchanged and still serves the non-streaming path.

| event | when | payload |
| --- | --- | --- |
| `meta` | once, before generation | `pinned` and `retrieved`, each **with its full `content`** — so the grounding strip can render while the answer is still arriving |
| `delta` | many | `{"t": "…"}`, one answer fragment |
| `done` | once, after the checker runs | `{warnings, notes, chars, elapsed_ms}` |
| `error` | on failure mid-stream | `{message: "busy"\|"backend", status}` — generic by design; detail stays server-side |

Context assembly happens *before* the response starts, so an unresolvable
niveau/chapitre is still a clean 422 rather than an error frame inside a 200.

**Reasoning tokens are filtered out.** gpt-oss streams its chain of thought
first as `delta.reasoning` (`channel: "analysis"`) — measured at 407 reasoning
frames over the first 1.23s before any content. `llm_stream.stream_groq`
yields `delta.content` only. Do not "fix" this by forwarding every delta: it
would show students the model's private monologue.

Because of that reasoning phase there is ~1.2s of silence before the first
visible token, which is why the UI shows a typing indicator rather than an
empty bubble.

## Sign-in routes (`/auth`)

| Route | Body / result |
| --- | --- |
| `POST /auth/google` | `{"id_token": "<Google ID token>"}` → sets the session cookie, returns the user. 401 for a token Google's keys reject; 503 if `GOOGLE_CLIENT_ID` is unset (the backend refuses to verify rather than skip the audience check). |
| `GET /auth/me` | The current user, or 401. This is how the UI learns whether it is signed in — the cookie is `httpOnly`, so there is nothing to read client-side. |
| `POST /auth/logout` | 204; clears the session. |

A user is `{"id": "<uuid>", "email": "…", "display_name": "…"}`. Google's
internal subject id never leaves the backend.

## Chapter routes (`/chapters`)

All need a session.

| Route | Returns |
| --- | --- |
| `GET /chapters` | `[{"id": "1", "title": "…", "niveau": "2eme", "status": "active"}, …]` — including chapters with `"status": "coming_soon"`, so a client can show what is on the way rather than a list that looks complete. |
| `GET /chapters/{id}/exercises` | `[{"id": "…", "question": "Ecrire un programme qui …"}, …]` |
| `GET /chapters/{id}/pdf` | The lesson PDF (`application/pdf`). |

404 for a chapter with no content behind it; 503 if the exercise file or the
PDF is missing on the server. The PDF and exercises are the author's
material — see the curriculum-text item below, which applies here too.

## Pre-launch items (before anyone else can reach this endpoint)

These are required regardless of whether auth is added — "don't leak
internals in error text" is a separate threshold from "add a login".

- [ ] **Tighten the 422 body for an unresolvable scope.** It currently
      inlines the full pin-resolution failure, naming all seven pinned
      anchors and their exact corpus text. Fine for solo testing; it
      discloses corpus structure to any caller. Return a generic
      "niveau/chapitre not available" and log the detail server-side.
- [ ] Review the other error paths for the same leak class (502 currently
      passes the upstream reason through).
- [ ] **Decide who may receive curriculum text.** `POST /solve/stream`'s
      `meta` event carries the *full text* of every pinned table and every
      retrieved excerpt — roughly 6.6 KB of the chapter per request. This is
      deliberate: it is what the UI's grounding strip renders, and showing a
      student the exact syntax table an answer was built on is the product's
      whole trust argument. But it means the endpoint serves copyrighted
      chapter material to any caller who can reach it, which is a different
      exposure than the label-and-score payload `/solve` returns. Note the
      repo deliberately excludes the source PDF and `chunks.json` for exactly
      this reason, so a deployed endpoint would be redistributing what the
      repo declines to. Before opening this up, decide whether excerpts are
      gated behind whatever identifies a legitimate student, or trimmed to
      the pinned tables only.
- [x] **Restrict CORS to the real origin.** No longer a code change: origins
      come from the `CORS_ORIGINS` env var (comma-separated) via `config.py`,
      defaulting to the same localhost dev ports (5173, 5174). Set the var to
      the real origin when hosting — but note the default is still permissive
      for local dev, so a deployment that *forgets* to set it falls back to
      localhost-only rather than to a wildcard, which fails closed.

## Notes

- The embedding model is loaded at app startup (`lifespan`), so no request
  pays the ~6s SentenceTransformer initialisation.
- `niveau` is stored/queried unaccented (`2eme`) and shown to the student
  accented (`2ème`) via `niveau_label()`. Requests should send the raw
  store form.

## Gatekeeper (added after the pre-launch list above)

Every request to `/solve` and `/solve/stream` now passes through
`gatekeeper.py` before `build_context` runs:

- **> 2000 characters** → fixed decline, zero model calls.
- **Classifier** (one cheap call, output forced to one of three words) →
  `PROBLEM` continues to the unchanged pipeline; `META` goes to a
  zero-context responder; `OFF_TOPIC` gets a fixed decline with no further
  model call. Anything unparseable falls back to `OFF_TOPIC` — the only
  branch that makes no further calls and never touches curriculum content.
- **Meta replies** are checked before being returned (length cap,
  system-prompt phrases, algorithm-shaped content); a failure returns the
  same decline sentence.

For `/solve/stream`, gatekeeper replies reuse the existing SSE contract
exactly — a `meta` event with empty `pinned`/`retrieved`, one `delta`, and a
clean `done` — so the frontend needs no special handling and the grounding
strip and constraint badge correctly stay hidden.

This does **not** change the exposure noted above: a `PROBLEM`-classified
request still receives the full pinned/retrieved excerpts in its `meta`
event. The gatekeeper reduces *how many* requests reach that path; it does
not gate who may receive curriculum text once they do.
