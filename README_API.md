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

## Notes

- The embedding model is loaded at app startup (`lifespan`), so no request
  pays the ~6s SentenceTransformer initialisation.
- `niveau` is stored/queried unaccented (`2eme`) and shown to the student
  accented (`2ème`) via `niveau_label()`. Requests should send the raw
  store form.
