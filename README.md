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
covered, it says so instead of inventing it. Every answer shows the exact
curriculum text it was built on.

---

## What a student gets

- **Sign in with Google or an email and password.** Every screen sits behind
  the sign-in; there is no anonymous access. Email accounts get address
  verification and password reset by email.
- **A one-time class question.** On the first sign-in a student picks their
  **niveau** (2ème, 3ème, Bac) and **section** (Informatique, Mathématiques,
  Sciences expérimentales, Sciences techniques, Économie et gestion, Lettres);
  it is kept on the account and changeable later from the sidebar.
- **Chapters, filtered to the student's year.** The home page lists the
  chapters of the student's own niveau — including the ones not ready yet,
  marked *À venir*, so the list never overstates coverage. A year whose corpus
  is not in yet gets an honest empty state rather than a bare grid.
- **A chapter page** with two tabs: the lesson itself (the course PDF, in the
  browser's own viewer) and its exercise series. Clicking an exercise sends it
  straight to the tutor.
- **A chat** for anything the student brings — an exercise pasted in, a
  question about the course, or their own half-written program to be corrected.
  Answers stream in as they are written and arrive as a declaration table, an
  *Algorithme | Python* solution side by side, and an execution trace.
- **A photo or a PDF of an exercise.** Attach one (paperclip, `Ctrl+V` a
  screenshot, or drag-and-drop); Fahem reads the statement out of it and solves
  it like a typed message.
- **A syntax verdict** under each answer — *Syntaxe du chapitre respectée* or
  *Syntaxe à vérifier* with the exact lines — from a mechanical checker.
- **A grounding strip** that opens to show the pinned syntax tables and the
  retrieved excerpts the answer was built on.
- **Discussions kept in the browser**, in a Historique panel, with a confirm
  step before one is deleted.
- **A light / dark theme toggle**, defaulting to the OS setting.

Admins get a separate console (users and uploaded chapters) — see *History*.

---

## How it works

```
chapter PDF  →  extract  →  patch  →  embed  →  retrieve  →  assemble  →  generate  →  check  →  API  →  UI
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

Before any of that, a **gatekeeper** decides what a message is — an exercise,
the student's own code, a course question, small talk, or off-topic (see
*Notes*) — and after it a **constraint checker** scans the answer for syntax
the chapter has not taught. An attached photo or PDF is transcribed first and
then goes through the same gatekeeper.

### The pipeline

| Stage | What it does |
| --- | --- |
| **Extraction** | `extract_chapter.py` turns a chapter PDF into tagged chunks. Tables are pulled out whole (the two-column *Algorithme \| Python* blocks are nonsense when flattened), prose splits at the document's own sub-boundaries rather than a character cap, and pseudocode blocks are never cut. |
| **Correction** | `patch_chunks.py` applies pinned, hand-verified fixes. The PDFs draw the assignment arrow `←` with a custom font glyph that decodes as `-`, turning an assignment into a subtraction. This is deliberately **not** automated — a regex would also rewrite genuine subtraction in the same tables. |
| **Embedding + retrieval** | `rag_store.py` embeds with a multilingual model into Qdrant; `retrieval.py` filters by scope, then searches semantically inside it. |
| **Context assembly** | `context.py` builds the pinned core + retrieved extras, with a build check that fails loudly if a pinned table is missing or its arrows were lost. |
| **Gatekeeper** | `gatekeeper.py` routes each message: `PROBLEM`, `CODE`, `QUESTION`, `META` or `OFF_TOPIC`. The three grounded routes each get their own prompt. |
| **Attachments** | `attachments.py` turns a photo or PDF into the exercise text — `pdfplumber` for a PDF with a text layer, a Groq vision model (`GROQ_VISION_MODEL`) for photos and scans, asked only to transcribe — then it re-enters the pipeline as if typed. |
| **Generation** | `prompts.py` holds the teaching constraints (a prompt per grounded route, plus a per-student "profil de l'élève" note that steers tone only); `generate.py` / `llm_stream.py` call the model (Groq, `openai/gpt-oss-120b`) and stream the answer. |
| **Checking** | `checker.py` runs a mechanical constraint check over the finished answer. |
| **API** | `api.py` (FastAPI) — solving and attachment reading, plus the auth, chapter and admin routers. |
| **UI** | `ui/` — React 19 + Vite, served by nginx in Docker. |

### Platform

| Concern | How |
| --- | --- |
| **Vector store** | Qdrant (replaced an on-disk ChromaDB in Phase 0b). |
| **Relational store** | PostgreSQL via SQLAlchemy, schema managed by Alembic: users (with role, niveau, section), chat sessions, chat messages, emailed auth tokens, and uploaded chapters. |
| **Auth** | Two ways in. Google Identity Services on the frontend, verified server-side against Google's keys; and email + password (Argon2id), with emailed verification and reset links. Either way the backend issues its own signed session in an `httpOnly` cookie (PyJWT); the Google token is never treated as a session. A closed `role` (`student` / `admin`) gates the console; the admin role is granted only out of band by `promote_admin.py`. |
| **Rate limiting** | slowapi over Redis. Solving and attachment reading are limited **per user** (`10/minute;100/hour` by default, a shared budget); sign-in is limited **per IP** (`30/minute`). A 429 carries `Retry-After`, which the UI turns into *"Réessaie dans 47 secondes."* |
| **Chapters** | `chapters.py` serves the catalogue (scoped to the signed-in student's niveau), each chapter's exercises and the lesson PDF — all behind sign-in. `admin_chapters.py` + `chapter_store.py` back the admin upload/publish workflow; `course_markdown.py` reads a Markdown-authored chapter. |

### API at a glance

| Route | Auth | What |
| --- | --- | --- |
| `GET /health` | — | `{"status":"ok","model":"…"}` |
| `POST /auth/google` | — (IP-limited) | Exchange a Google ID token for a session cookie |
| `POST /auth/signup` · `/login` | — (IP-limited) | Email + password account creation / sign-in |
| `POST /auth/forgot-password` · `/reset-password` · `/resend-verification` · `GET /auth/verify-email` | — | The emailed verification and reset flow |
| `GET /auth/me` | cookie | The signed-in user (incl. niveau/section), or 401 |
| `PUT /auth/me/profile` | cookie | Set the student's niveau and section |
| `POST /auth/logout` | cookie | Clear the session |
| `GET /chapters` | cookie | Chapter catalogue for the student's year, including *coming soon* ones |
| `GET /chapters/{id}/exercises` · `/pdf` | cookie | A chapter's exercise series / lesson PDF |
| `POST /solve` · `/solve/stream` | cookie (user-limited) | One-shot / streamed (SSE) solution — the UI uses the stream |
| `POST /solve/extract` | cookie (user-limited) | Read the exercise text out of an attached photo or PDF |
| `/admin/*` · `/admin/chapters/*` | cookie + admin | The console: users, stats, and the chapter upload/publish workflow |

Request/response shapes, the SSE event contract and the pre-launch checklist
are in [`README_API.md`](README_API.md).

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

## Running it

Docker is the recommended way: the stack is five services (Postgres, Qdrant,
Redis, backend, frontend) and compose wires them together. On some Windows
machines the native route cannot load PyTorch at all (application-control
policy blocks `torch.dll`), and the container sidesteps that.

### 1. Configure

```bash
cp .env.example .env
```

Then fill in at least:

```
GROQ_API_KEY=your_key_here
GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
```

`GOOGLE_CLIENT_ID` is the OAuth 2.0 Client ID from Google Cloud Console
(*APIs & Services → Credentials*). The backend refuses to verify any sign-in
while it is empty, and compose passes the same value into the frontend build,
so the two cannot drift. `.env` is gitignored — never commit it.

### 2. Start the stack

```bash
docker compose up --build -d      # UI on http://localhost:5173, API on :8000
docker compose exec backend alembic upgrade head      # first run: create the tables
docker compose logs -f backend
```

Open the UI at **`http://localhost:5173`** — `localhost`, not `127.0.0.1`.
The session cookie is `SameSite=Lax`, and `localhost:5173 → 127.0.0.1:8000`
is a cross-site request, so sign-in would fail with a silent 401.

### 3. Build the index from your PDF

```bash
python extract_chapter.py "data/your-chapter.pdf" --niveau 2eme --chapitre 1
python patch_chunks.py          # applies pinned fixes, prints the arrow check
docker compose exec backend python rag_store.py --reset      # load chunks.json into Qdrant
docker compose exec backend python rag_store.py --describe   # what is in the store
```

**Read the `patch_chunks.py` output.** It lists every surviving `←` and every
line shaped like a corrupted one. The automated check only catches shapes it
has been told about — skim any declaration- or affectation-heavy page by hand.

`chunks.json`, `sample_problems.json` and `data/` are bind-mounted, so
rebuilding an image does not discard them. Qdrant, Postgres and the embedding
model cache live in named volumes and survive `docker compose down`. Redis
deliberately keeps nothing on disk — rate-limit counters are meant to be
short-lived. The frontend image bakes `VITE_API_URL` and
`VITE_GOOGLE_CLIENT_ID` in at build time, so changing either means rebuilding
it.

### 4. Check retrieval before involving a model

```bash
cp sample_problems.example.json sample_problems.json   # then add your own problems
docker compose exec backend python test_retrieval.py   # prints retrieved chunks
docker compose exec backend python context.py          # pinned core + extras, with build check
```

### 5. Generate from the command line

```bash
python generate.py                          # all problems
python generate.py --only demo01            # one
python generate.py --temperature 0          # deterministic-ish
```

### Without Docker

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt    # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

docker compose up -d postgres qdrant redis                     # the stores still come from compose
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn api:app --port 8000

cd ui && npm install && npm run dev
```

The first run downloads the embedding model (~470 MB). Vite's dev server needs
`VITE_API_URL` and `VITE_GOOGLE_CLIENT_ID` in its environment (or in
`ui/.env.local`). Ports 5173 and 5174 are allowed by CORS; for any other, set
`CORS_ORIGINS`.

> **Testing the exercise click-through?** Use a production build
> (`npm run build && npx vite preview --port 5174`) or the Docker frontend,
> not `npm run dev`. React's StrictMode mounts effects twice in development,
> and the second mount cancels the auto-sent exercise before it reaches the
> server — so under the dev server the click posts the question and nothing
> answers. Production is unaffected.

### Configuration

Everything tunable is in `config.py`, read from env with working defaults:

| Variable | Default | |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | |
| `GROQ_VISION_MODEL` | `qwen/qwen3.8-27b` | reads attached photos / scanned PDFs |
| `GOOGLE_CLIENT_ID` | *(required for sign-in)* | also baked into the frontend |
| `SESSION_SECRET_KEY` | a **published** dev string | **must** be set to a random value in any deployment |
| `SESSION_TTL_SECONDS` | `604800` (7 days) | |
| `SESSION_COOKIE_SECURE` | `false` | set `true` wherever the site is served over https |
| `SESSION_COOKIE_SAMESITE` | `lax` | |
| `DATABASE_URL` | `postgresql+psycopg://fahem:fahem@localhost:5432/fahem` | |
| `QDRANT_URL` | `http://localhost:6333` | |
| `REDIS_URL` | `redis://localhost:6379` | |
| `RATE_LIMIT_SOLVE` | `10/minute;100/hour` | per user |
| `RATE_LIMIT_AUTH` | `30/minute` | per IP |
| `CORS_ORIGINS` | localhost 5173/5174 | comma-separated |
| `CHUNKS_PATH` / `PROBLEMS_PATH` | `chunks.json` / `sample_problems.json` | |
| `GATEKEEPER_MAX_INPUT_CHARS` | `2000` | |
| `GATEKEEPER_ROUTER_MAX_TOKENS` / `_META_MAX_TOKENS` | `250` / `250` | |
| `ATTACHMENT_MAX_BYTES` | `10485760` (10 MB) | per attached photo / PDF |
| `ATTACHMENT_MAX_PDF_PAGES` | `3` | pages read from a PDF |
| `ATTACHMENT_MAX_TEXT_CHARS` | `1800` | cap on the extracted text (kept under the gatekeeper input cap) |

Inside compose, `DATABASE_URL`, `QDRANT_URL` and `REDIS_URL` are overridden to
point at the sibling containers.

---

## Tests

```bash
docker compose exec backend python test_checker.py    # checker pass/fail suite
docker compose exec backend python test_auth.py       # token verification, sessions, config guards
docker compose exec backend python test_db.py         # models, constraints, cascades
docker compose exec backend python test_admin.py      # admin role gate and user management
docker compose exec backend python test_chapters_admin.py   # chapter upload/publish workflow
docker compose exec backend python test_course_markdown.py  # Markdown chapter parsing
docker compose exec backend python test_retrieval.py  # retrieval inspection (no assertions)
docker compose exec backend python test_gatekeeper_adversarial.py   # adversarial transcripts; calls the model
```

They are standalone scripts that print `[PASS]` lines and end with
`ALL PASSED`. `test_gatekeeper_adversarial.py` makes real model calls and
spends API quota; the others do not.

```bash
.venv/Scripts/python.exe -m ruff check .     # lint
.venv/Scripts/python.exe -m ruff format .    # format
cd ui && npm run lint && npm run format:check && npm run build
```

Config lives in `pyproject.toml` (ruff) and `ui/.prettierrc.json` +
`ui/.oxlintrc.json`. `E501` is off and `F401` is ignored in the two
re-exporting modules — both deliberate, see the comments in `pyproject.toml`.

---

## Notes

**The constraint checker is advisory.** It has both missed real violations and
raised false ones. It validates the Python column and, since the model once
fabricated `Lire moyenne1 ← réel`, the Algorithme column too. A clean result
means "no known pattern matched", not "correct" — which is why the UI says
*Syntaxe du chapitre respectée* rather than *vérifié*. An answer with no real
Algorithme solution in it (the model asking for the full statement, say) gets
no verdict at all, rather than a pass on content the checker never looked at.

**The self-check is unproven.** The prompt asks the model to trace its solution
before presenting it. Across every test round the trace has confirmed already
correct work; it has never had an error to catch, so there is no evidence it
would catch one.

**Not every message reaches the pipeline the same way.** `gatekeeper.py`
classifies each incoming message first. `PROBLEM` (an exercise), `CODE` (the
student's own algorithm or program) and `QUESTION` (a question about a course
notion) all go to the grounded RAG pipeline, each with its own prompt. `META`
("what is this?", "what does chapter 1 cover?", greetings) is answered by a
second model that has *no* retrieval and *no* pinned tables in its context — so
it has nothing curriculum-related to leak even if fully compromised — and
`OFF_TOPIC` gets a fixed sentence with no model call at all. Messages over
2000 characters are declined before any model call, and an attachment's
extracted text is capped below that. A meta reply is also run through an
output-side check (length, system-prompt phrases, algorithm-shaped content)
before it is shown.

**An attachment is transcribed, never trusted.** A photo or PDF is read by a
vision model asked only to copy the text, and the result re-enters the same
gatekeeper as a typed message — so a photo of "ignore your instructions" is
exactly as harmless as typing it. File types are recognised from the bytes,
not the filename or the request's content type.

**Reasoning tokens never reach the student.** gpt-oss streams its chain of
thought before the answer; `llm_stream.py` forwards only the answer channel.
That reasoning phase is ~1.2s of silence, which is why the UI shows a
*Recherche dans le chapitre…* indicator.

**A stream stops when nobody is watching it.** Leaving the chat, or logging
out, aborts the in-flight generation instead of letting it keep spending
model quota on a page no one is looking at.

**Retrieval is symmetric.** Queries are instructions ("Ecrire un programme
qui…") and the corpus is exposition, so scoring rewards shared vocabulary over
relevance. This is why the syntax core is pinned rather than retrieved. An
asymmetric model (e5 with `query:`/`passage:` prefixes) is the principled fix,
deferred until a chapter's universal table set is too large to curate by hand.

**Discussions live in the browser.** Chat history is `localStorage`, keyed per
browser, not per account — the Postgres chat tables exist but nothing writes
to them yet. Logging out does not clear it.

---

## Frontend

The UI deliberately stays flat and restrained — hairline borders, one accent,
no decoration — and gets its consistency from a small design system rather
than from a redesign. It was built out step by step against
[`docs/frontend-design-audit.md`](docs/frontend-design-audit.md):

- **Tokens.** Spacing, radius, type, elevation, motion, focus and layout
  scales in `App.css`, alongside the colour tokens. Body text is 16px.
- **Accessibility.** One `<h1>` per page, a live region announcing each
  finished answer (not the token stream), WAI-ARIA tabs with arrow-key
  navigation, AA contrast on the accent in both themes, a designed double
  focus ring, and `prefers-reduced-motion` respected everywhere something
  moves.
- **Touch targets.** Every control has a 44px minimum hit area.
- **Safe deletion.** Deleting a discussion asks *Supprimer ?* inline first;
  blur or Escape backs out.
- **Primitives** in `ui/src/components/ui/`:

  | Primitive | Use |
  | --- | --- |
  | `Button` | variants `primary` / `secondary` / `ghost` / `danger`, sizes `sm` / `md` — both keep the 44px floor |
  | `Badge` | tones `neutral` / `success` / `warning` / `danger` |
  | `Alert` | error and info blocks, with an optional action |
  | `Skeleton` | loading placeholders sized to the real content |
  | `EmptyState` | "nothing here yet", at screen or panel size |
  | `.surface` | the one bordered panel (a CSS class, since it lands on links, buttons and `<object>` alike) |

  Screen-specific rules only *place* a primitive — width, margin, show/hide —
  and never restyle it.

Light and dark are driven off `<html data-theme>`: a toggle sets it, and it
defaults to the OS setting. The palette is the "Violet Dusk" token set, and
every colour keeps AA contrast in both themes.

---

## Layout

**Backend** (flat at repo root — deliberately, see *Structure notes*)

```
config.py            all env/config: endpoints, model names, paths, limits
api.py               FastAPI app: /health, /solve, /solve/stream, /solve/extract; mounts the routers
auth.py              /auth: Google token exchange, session cookie, current user, profile
password_auth.py     /auth: email+password signup/login, verification, reset
admin.py             /admin: role gate, stats, user management
admin_chapters.py    /admin/chapters: upload → extract → review → publish
chapter_store.py     the uploaded-chapter store behind the admin workflow
chapters.py          /chapters: catalogue (year-scoped), exercises, lesson PDF
attachments.py       reads an exercise from an attached photo or PDF
course_markdown.py   reads a Markdown-authored chapter
emails.py            sends verification / reset mail
ratelimit.py         slowapi limiter over Redis; per-user and per-IP keys
db.py / models.py    SQLAlchemy engine + User, ChatSession, ChatMessage, AuthToken, UploadedChapter
alembic/             migrations
gatekeeper.py        routes each message PROBLEM / CODE / QUESTION / META / OFF_TOPIC
                     before the pipeline sees it; meta-responder + output safety net
checker.py           the constraint checker (rules, patterns, thresholds)
generate.py          Groq/Ollama HTTP clients + CLI harness
llm_stream.py        streaming Groq call; filters the reasoning channel
prompts.py           the teaching constraints (a prompt per grounded route)
context.py           pinned syntax core + retrieved extras
retrieval.py         scope-filtered semantic search
rag_store.py         embedding + Qdrant storage
extract_chapter.py   PDF → tagged chunks          (offline tool)
patch_chunks.py      pinned corrections           (offline tool)
promote_admin.py     grant/revoke the admin role  (offline tool)
```

**Frontend** (`ui/src`)

```
config.js            NIVEAU / CHAPITRE / SCOPE_LABEL / API_URL / GOOGLE_CLIENT_ID
App.jsx              auth gate (checking / signed out / signed in / needs-profile) + routes
App.css              tokens, primitives, then per-screen placement
routes/              Home, ChapterPage, Chat, ResetPassword, admin/*
components/          AppLayout, AppSidebar, Message, Composer, Markdown,
                     AlgoCode, GroundingStrip, HistoryPanel, ThemeToggle,
                     SignInScreen, PasswordAuthForm, GoogleSignIn,
                     AuthShell, ProfileSetup, admin/*
components/ui/       Button, Badge, Alert, Skeleton, EmptyState
lib/                 api.js (SSE client + attachment upload), auth.js,
                     authContext.js, profile.js, theme.js, chapters.js,
                     sessions.js (localStorage), algoHighlighter.js,
                     alignAlgoTable.js, remarkAlgoTable.js, hasRealSolution.js
grammar/             algoPseudocode.json (TextMate grammar), algoThemes.js
```

### Structure notes

The backend is intentionally flat rather than split into packages. A
restructure was scoped and deliberately kept conservative: only the
constraint checker was extracted out of `generate.py` (which was doing HTTP
clients *and* the checker *and* a CLI), because only the checker has a real
test suite behind it. `llm_stream.py`, `api.py`, and the RAG modules were left
in place — their behaviour is subtle (the reasoning-channel filter, the SSE
generator, the pin anchors) and nothing but manual verification would catch a
mistake in moving them.

`config.py` is the single source for values that used to be scattered.
`generate.py` and `rag_store.py` re-export the names they used to define, so
older imports elsewhere keep working.

---

## History

| Milestone | What landed |
| --- | --- |
| **MVP** | Extraction, patching, RAG with a pinned syntax core, prompt, checker, `/solve`, a one-screen React UI — verified end to end against seven real exercises. |
| **Streaming UI** | `/solve/stream` over SSE, the grounding strip, the syntax verdict, discussions in the sidebar, Shiki-highlighted Algorithme column. |
| **Gatekeeper** | `PROBLEM` / `META` / `OFF_TOPIC` routing; checker and config extracted into their own modules. |
| **Phase 0a** | PostgreSQL, SQLAlchemy models, Alembic migrations. |
| **Phase 0b** | Qdrant replaces ChromaDB. |
| **Phase 0c** | Google sign-in and backend session issuance. |
| **Phase 1** | Sign-in required everywhere; the frontend auth gate. |
| **Phase 2** | Rate limiting per user (solving) and per IP (sign-in), on Redis. |
| **Phase 3a** | Chapter catalogue, exercises and the lesson PDF on the backend. |
| **Phase 3b** | Home, chapter pages and routing around the chat; streams abort on leaving it; the PDF keeps its page across tab switches. |
| **Frontend audit, steps 1–4** | Design tokens; the accessibility set; delete confirmation and 44px targets; the six UI primitives. |
| **Phases 4–5** | Email + password accounts (Argon2id), with emailed verification and password reset. |
| **Phase 6** | The app sidebar as navigation and identity; discussions moved into a Historique panel; the landing page. |
| **Phase 7** | An enforced `student` / `admin` role, granted out of band by `promote_admin.py`. |
| **Phase 8** | The admin console: users, stats, session revocation. |
| **Phase 9** | Uploaded chapters — an admin upload → extract → review → publish workflow (9b: Markdown-authored chapters). |
| **This batch (PR #11)** | Solve from a photo or PDF; `CODE` / `QUESTION` gatekeeper routes and line-by-line answers; a slimmed sign-in screen; a light/dark toggle; the student profile (niveau + section) that scopes the chapter list and steers the tutor's tone. |

## Status and what's next

The product works end to end: sign in, answer the one-time class question,
pick a chapter for your year, read the lesson, click an exercise or paste one
(or send a photo of it), get a grounded, checked answer.

Next, roughly in order:

- **Before anyone else can reach it** — set a real `SESSION_SECRET_KEY`,
  `SESSION_COOKIE_SECURE=true` and `CORS_ORIGINS`; enable Qdrant's API key;
  and close the items in `README_API.md`'s pre-launch list (generic error
  bodies, and who may receive curriculum excerpts).
- **More chapters, more years** — the profile already scopes the chapter list
  by niveau, so a 3ème/Bac student currently lands on an honest empty state.
  Each new chapter needs its PDF (or Markdown), its pinned-table anchors in
  `context.py`, and a check with `test_retrieval.py`. This is the main unlock.
- **Scope the chat to the profile** — the freeform chat still defaults to the
  2ème corpus; point it at the student's own niveau once that year has content.
- **Section-aware chapters** — tag chapters with a section so the catalogue can
  filter on it too, not only the niveau (`catalogue(niveau=…)` is written for
  this).
- **Server-side history** — write discussions to the Postgres chat tables so
  they follow the account rather than the browser.
