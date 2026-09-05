# Fahem

**Fahem** — an AI tutor that solves algorithmique homework using exactly the
syntax a Tunisian student has actually been taught, grounded in the real
curriculum instead of generic AI knowledge.

Ask a general-purpose chatbot to solve a 2ème Info exercise and it answers in
whatever Python it likes: a `for` loop, a helper function, an f-string. All
correct Python. All useless to a student who will be marked against the
notation in their own textbook, and who has not been taught any of it yet.

Fahem retrieves the actual chapter the student is working through and
constrains the answer to the syntax that chapter contains — `Lire (x)` and
`Ecrire`, `←` for assignment, `div` and `mod`, the `Objet | Nature/type`
declaration table. If a problem genuinely needs something the chapter has not
covered, it says so instead of inventing it.

---

## How it works

```
chapter PDF  →  extract  →  patch  →  embed  →  retrieve  →  assemble  →  generate  →  API  →  UI
```

The core idea is that **retrieval alone is not enough**. Early rounds showed
the vector search reliably surfacing generic prose about float notation while
the operator table — needed by nearly every exercise in the chapter — never
made the top-k. So the context is built in two parts:

1. **A pinned syntax core.** Seven reference tables (operators, assignment,
   input, output, math functions, type conversion, string functions) are
   included unconditionally, before any retrieval runs. Their relevance is not
   a ranking question — they are the chapter's reference sheet.
2. **Retrieved extras.** Semantic search supplies only the topic-specific
   supplement, filtered to the requested `niveau` + `chapitre` *before* the
   vector search runs, so bac-level material can never leak into a 2ème
   session.

### The phases

| Phase | What it does |
| --- | --- |
| **1. Extraction** | `extract_chapter.py` turns a chapter PDF into tagged chunks. Tables are pulled out whole (the two-column *Algorithme \| Python* blocks are nonsense when flattened), prose splits at the document's own sub-boundaries rather than a character cap, and pseudocode blocks are never cut. |
| **2. Correction** | `patch_chunks.py` applies pinned, hand-verified fixes. The PDFs draw the assignment arrow `←` with a custom font glyph that decodes as `-`, turning an assignment into a subtraction. This is deliberately **not** automated — a regex would also rewrite genuine subtraction in the same tables. |
| **3. Embedding + retrieval** | `rag_store.py` embeds with a multilingual model into Chroma; `retrieval.py` filters by scope, then searches semantically inside it. |
| **4. Context assembly** | `context.py` builds the pinned core + retrieved extras, with a build check that fails loudly if a pinned table is missing or its arrows were lost. |
| **5. Generation** | `prompts.py` holds the teaching constraints; `generate.py` calls the model and runs a mechanical constraint check over the answer. |
| **6. API** | `api.py` — one FastAPI endpoint, `POST /solve`. See `README_API.md`. |
| **7. UI** | `ui/` — one React screen: paste a problem, get a solution. |

---

## You must supply your own curriculum material

**No curriculum PDFs or extracted text are included in this repository.** The
source documents belong to their authors and are not ours to redistribute, so
`data/*.pdf`, `chunks.json` and `sample_problems.json` are all gitignored.

To run Fahem you need your own chapter PDF. The pipeline expects a document
with roman-numeral sections and a `Série d'exercices`; other layouts will need
`extract_chapter.py`'s heading patterns adjusted.

The pinned tables in `context.py` are located by **anchor strings matched
against your corpus** — they are specific to the chapter this was built
against, and will need replacing for a different chapter. `context.py` fails
loudly rather than silently dropping a pin, so you will know immediately.

---

## Running locally

### 1. Install

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux
```

First run downloads the embedding model (~470 MB).

### 2. Add your API key

```bash
cp .env.example .env
# then edit .env and paste your key
```

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

`.env` is gitignored. Never commit it.

### 3. Build the index from your PDF

```bash
python extract_chapter.py "data/your-chapter.pdf" --niveau 2eme --chapitre 1
python patch_chunks.py          # applies pinned fixes, prints the arrow check
python rag_store.py --chunks chunks.json --reset
python rag_store.py --describe  # what is in the store, by niveau/chapitre/type
```

**Read the `patch_chunks.py` output.** It lists every surviving `←` and every
line shaped like a corrupted one. The automated check only catches shapes it
has been told about — skim any declaration- or affectation-heavy page by hand.

### 4. Check retrieval before involving a model

```bash
cp sample_problems.example.json sample_problems.json   # then add your own problems
python test_retrieval.py                               # prints retrieved chunks
python context.py                                      # pinned core + extras, with build check
```

### 5. Generate

```bash
python generate.py                          # all problems
python generate.py --only demo01            # one
python generate.py --temperature 0          # deterministic-ish
```

### 6. API + UI

```bash
# terminal 1
.venv/Scripts/python.exe -m uvicorn api:app --port 8000

# terminal 2
cd ui && npm install && npm run dev
```

Vite prints the URL it picks. If it is not 5173, add that origin to the CORS
allowlist in `api.py`.

---

## Notes

**The constraint checker is advisory.** It has both missed real violations and
raised false ones. It validates the Python column and, since the model once
fabricated `Lire moyenne1 ← réel`, the Algorithme column too. A clean result
means "no known pattern matched", not "correct" — always read the output.

**The self-check is unproven.** The prompt asks the model to trace its solution
before presenting it. Across every test round the trace has confirmed already
correct work; it has never had an error to catch, so there is no evidence it
would catch one.

**Retrieval is symmetric.** Queries are instructions ("Ecrire un programme
qui…") and the corpus is exposition, so scoring rewards shared vocabulary over
relevance. This is why the syntax core is pinned rather than retrieved. An
asymmetric model (e5 with `query:`/`passage:` prefixes) is the principled fix,
deferred until a chapter's universal table set is too large to curate by hand.

---

## Layout

```
extract_chapter.py   PDF → tagged chunks
patch_chunks.py      pinned corrections + standing arrow check
rag_store.py         embedding + Chroma storage
retrieval.py         scope-filtered semantic search
context.py           pinned syntax core + retrieved extras
prompts.py           the teaching constraints
generate.py          model call + constraint checking
api.py               POST /solve
ui/                  React frontend
```

## Status

Phases 1–4 of the MVP are complete: extraction, RAG, prompt, API, UI, verified
end to end against seven real exercises. Next is putting it in front of actual
students.
