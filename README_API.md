## Running the API

```
.venv/Scripts/python.exe -m uvicorn api:app --reload --port 8000
```

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

Status codes: 422 for a bad request body or a niveau/chapitre with no pinned
syntax core; 429 when the upstream token-per-minute cap is hit (passed
through, not masked as a server error); 502 if the model backend is
unreachable.

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
- [ ] **Restrict CORS to the real origin.** `allow_origins` currently lists
      localhost dev ports (5173 and 5174) only, which is correct for now and
      wrong the moment this is hosted anywhere.

## Notes

- The embedding model is loaded at app startup (`lifespan`), so no request
  pays the ~6s SentenceTransformer initialisation.
- `niveau` is stored/queried unaccented (`2eme`) and shown to the student
  accented (`2ème`) via `niveau_label()`. Requests should send the raw
  store form.
