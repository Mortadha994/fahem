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
| **3. Embedding + retrieval** | `rag_store.py` embeds with a multilingual model into Qdrant; `retrieval.py` filters by scope, then searches semantically inside it. |
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

Vite prints the URL it picks. 5173 and 5174 are allowed by default; for any
other port, set the `CORS_ORIGINS` env var (comma-separated) rather than
editing code.

### 7. Or run both in Docker

```bash
docker compose up --build -d      # UI on :5173, API on :8000
docker compose logs -f backend
```

`chunks.json`, `sample_problems.json` and `data/` are bind-mounted, so
rebuilding the image does not discard them. The vector store is the `qdrant`
service, holding its data in the `qdrant-data` named volume - it survives
`docker compose down`, and is rebuilt from `chunks.json` with
`docker compose exec backend python rag_store.py --reset`. Postgres likewise
keeps `pg-data`. `GROQ_API_KEY` comes from `.env` via compose's `env_file`. The frontend image bakes `VITE_API_URL` at
build time — changing the backend URL means rebuilding that image.

**Configuration.** Everything tunable is in `config.py`, read from env with
working defaults, so no edit is needed for local use:

| Variable | Default |
|---|---|
| `GROQ_API_KEY` | *(required)* |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `CORS_ORIGINS` | localhost 5173/5174 |
| `QDRANT_URL` / `CHUNKS_PATH` | `http://localhost:6333` / `chunks.json` |
| `DATABASE_URL` | `postgresql+psycopg://fahem:fahem@localhost:5432/fahem` |
| `GATEKEEPER_MAX_INPUT_CHARS` | `2000` |
| `GATEKEEPER_ROUTER_MAX_TOKENS` / `_META_MAX_TOKENS` | `250` / `250` |

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

**Not every message reaches the pipeline.** `gatekeeper.py` classifies each
incoming message first: `PROBLEM` goes to the RAG pipeline unchanged, `META`
("what is this?", "what does chapter 1 cover?") is answered by a second model
that has *no* retrieval and *no* pinned tables in its context — so it has
nothing curriculum-related to leak even if fully compromised — and
`OFF_TOPIC` gets a fixed sentence with no model call at all. Messages over
2000 characters are declined before any model call. A meta reply is also
run through an output-side check (length, system-prompt phrases,
algorithm-shaped content) before it is shown.

**Retrieval is symmetric.** Queries are instructions ("Ecrire un programme
qui…") and the corpus is exposition, so scoring rewards shared vocabulary over
relevance. This is why the syntax core is pinned rather than retrieved. An
asymmetric model (e5 with `query:`/`passage:` prefixes) is the principled fix,
deferred until a chapter's universal table set is too large to curate by hand.

---

## Layout

### Where does X live?

**Backend** (flat at repo root — deliberately, see *Structure notes* below)

```
config.py            all env/config: endpoints, model names, paths, limits
api.py               FastAPI app: /health, /solve, /solve/stream
gatekeeper.py        routes each message PROBLEM / META / OFF_TOPIC before
                     the pipeline sees it; meta-responder + output safety net
checker.py           the constraint checker (rules, patterns, thresholds)
generate.py          Groq/Ollama HTTP clients + CLI harness
llm_stream.py        streaming Groq call; filters the reasoning channel
prompts.py           the teaching constraints (generation prompt)
context.py           pinned syntax core + retrieved extras
retrieval.py         scope-filtered semantic search
rag_store.py         embedding + Qdrant storage
extract_chapter.py   PDF → tagged chunks          (offline tool)
patch_chunks.py      pinned corrections           (offline tool)
```

**Frontend** (`ui/src`)

```
config.js            NIVEAU / CHAPITRE / SCOPE_LABEL / API_URL
App.jsx              session state, streaming orchestration, layout
App.css              all styling
components/          Message, Composer, Sidebar, Markdown, AlgoCode,
                     GroundingStrip
lib/                 api.js (SSE client), sessions.js (localStorage),
                     algoHighlighter.js, remarkAlgoTable.js,
                     hasRealSolution.js
grammar/             algoPseudocode.json (TextMate grammar), algoThemes.js
```

**Tests**

```
test_checker.py               real pass/fail suite for checker.py (16 cases)
test_retrieval.py             retrieval inspection harness (no assertions)
test_gatekeeper_adversarial.py  adversarial transcripts (no assertions)
```

### Structure notes

The backend is intentionally flat rather than split into packages. A
restructure was scoped and deliberately kept conservative: only the
constraint checker was extracted out of `generate.py` (which was doing HTTP
clients *and* the checker *and* a CLI), because only the checker has a real
test suite behind it. `llm_stream.py`, `api.py`, and the RAG modules
(`rag_store.py`, `retrieval.py`, `context.py`) were left in place — their
behaviour is subtle (the reasoning-channel filter, the SSE generator, the pin
anchors) and nothing but manual verification would catch a mistake in moving
them.

`config.py` is the single source for values that used to be scattered.
`generate.py` and `rag_store.py` re-export the names they used to define, so
older imports elsewhere keep working.

### Linting and formatting

```bash
.venv/Scripts/python.exe -m ruff check .     # lint
.venv/Scripts/python.exe -m ruff format .    # format
cd ui && npm run lint && npm run format      # oxlint + prettier
```

Config lives in `pyproject.toml` (ruff) and `ui/.prettierrc.json` +
`ui/.oxlintrc.json`. `E501` is off and `F401` is ignored in the two
re-exporting modules — both deliberate, see the comments in `pyproject.toml`.

## Status

Phases 1–4 of the MVP are complete: extraction, RAG, prompt, API, UI, verified
end to end against seven real exercises. Next is putting it in front of actual
students.
