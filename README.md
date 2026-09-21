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

- **A landing page to try, not only to read.** Before any account, the
  *Essaie* section runs three real chapter exercises through Fahem's three
  modes — *La solution*, *Mode guidé*, *Ma réponse* — from canned answers:
  no sign-in, no model call, and nothing that scrolls inside the page.
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
- **Discussions saved to the account**, in a Historique panel, with a confirm
  step before one is deleted — each student sees only their own, on any device.
- **A wait message instead of an error when the service is busy.** Every model
  call queues for Groq; a student who has to wait sees their place in line.
- **A light / dark theme toggle**, defaulting to the OS setting.

Learning features on top of the tutor:

- **Session memory.** Each discussion remembers its last three exchanges, so
  « et si N a 4 chiffres ? » or « explique la ligne 3 » continue the exercise
  instead of starting over.
- **Mode guidé.** A switch in the message box: instead of the full solution,
  Fahem leads the exercise in four steps — 🔍 Comprendre, 💡 Indice,
  🧩 Squelette (declaration table + algorithm with blanks), 🏁 Solution — with
  « Indice suivant », « Je propose ma solution » and « Voir la solution ».
  It is now what a new discussion opens in — the student switches to the full
  solution when they want it, and `default_chat_mode` in *Contrôles* moves
  everyone back the other way.
- **Vérifier ma réponse.** The student pastes (or photographs) their own
  solution and gets a verdict (Correct / Presque / À revoir), a line-by-line
  correction table, a test on an example, and the full correction folded away.
  Notation mistakes (`//`, `%`, `=` instead of `←`, a type inside `Lire`, no
  declaration table) are detected by code before the model answers.
- **Exercice similaire.** A new exercise on the same notions — plus facile,
  même niveau or plus difficile — never with its solution, never with a notion
  the chapter does not teach.
- **▶ Exécuter le Python.** Every solution table can run its Python column in
  the browser (Pyodide in a Web Worker): one field per `input()`, the output in
  a terminal, errors explained in French.
- **Ma progression.** Each chapter exercise is *commencé*, *solution vue* or
  *réussi* (solved alone: « Vérifier ma réponse » said Correct), with the next
  exercise to do, the solutions checked and the recurring notation mistakes.
- **👍 / 👎 on every answer**, « Modifier » on the last question and
  « Régénérer » on the last answer.
- **Motion that rewards.** The step rail fills up, a Correct verdict bursts
  into confetti, a generated exercise arrives as a « Nouveau défi » card — only
  for the answer that just finished, and never under « reduce motion ».

Content today: 2ème informatique, chapter 1 (*structures de données et
structures simples*) and chapter 2 (*structures conditionnelles*, with a
12-exercise série: Si, ET/OU, Si imbriqués, Selon).

Admins get a separate console: users, uploaded chapters, and **Surveillance IA**
with four tabs — *En direct* (Groq load, token usage against the daily limit),
*Contrôles* (pause the AI, budget guard, one switch per student feature, limits,
queues), *Journal* (every admin action, with revert) and *24 heures* (usage,
answers per prompt, students' 👍 / 👎, guided steps and verdicts).

Each account carries an **Activité** tab of its own: twelve weeks of that one
student — questions per week split by mode, the mix of modes, discussions,
tokens and calls — each chart under a sentence saying what it reads as
(growing, steady or fading; learning with the tutor or taking solutions off
it). It exists to answer one question per account: does this person need more
room, or an offer.

---

## How it works

```mermaid
flowchart LR
    subgraph offline["Offline, once per chapter"]
        PDF["Chapter PDF / Markdown"] --> EX["scripts/extract_chapter.py"] --> PA["scripts/patch_chunks.py"] --> EMB["app/rag/rag_store.py<br/>embed into Qdrant"]
    end
    subgraph online["Each student message"]
        MSG["Message<br/>(+ photo / PDF)"] --> GK["app/llm/gatekeeper.py<br/>route"]
        GK --> CTX["app/rag/context.py<br/>pinned syntax + retrieval"]
        CTX --> GEN["app/llm/prompts.py + app/llm/llm_stream.py<br/>Groq, streamed"]
        GEN --> CHK["app/grading/algo_notation.py + app/grading/checker.py"]
        CHK --> UI["React chat"]
    end
    EMB -. scoped search .-> CTX
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

### One message, end to end

```mermaid
sequenceDiagram
    autonumber
    actor S as Student
    participant UI as Chat (React)
    participant API as /solve/stream
    participant GK as Gatekeeper
    participant Q as Groq queue (Redis)
    participant G as Groq
    participant DB as Postgres

    S->>UI: types, pastes or photographs
    UI->>API: problem + mode + last exchanges + ids
    alt button or check (route already known)
        API->>API: skip the classifier
    else free message
        API->>Q: wait for a slot
        Q->>G: classify
        G-->>API: PROBLEM / CODE / QUESTION / META / OFF_TOPIC
    end
    API->>API: learning_route → prompt (PROBLEM, GUIDED, CHECK, PRACTICE, FOLLOW_UP…)
    API-->>UI: meta (grounding, route, step)
    API->>Q: wait for a slot
    Q->>G: generate
    G-->>UI: delta, delta, delta…
    API->>API: notation fix + syntax check + verdict
    API->>DB: save the exchange (even if the tab closed)
    API-->>UI: done (warnings, route, step, verdict, version)
```

### Which prompt answers

The classifier says what a message is; the student's mode and buttons decide
how it is answered (`app/main.py` `learning_route`):

```mermaid
flowchart TD
    M["Message"] --> TL{"over 2000 characters?"}
    TL -- yes --> TOO["Clear « trop long » message"]
    TL -- no --> K{"mode = check,<br/>or « voici ma solution » + code?"}
    K -- yes --> CHECK["CHECK<br/>verdict + correction"]
    K -- no --> P{"mode = practice?"}
    P -- yes --> PR["PRACTICE<br/>new statement, no solution"]
    P -- no --> G{"mode = guided?"}
    G -- "button" --> STEP["GUIDED<br/>next step / step 4"]
    G -- "new statement" --> G1["GUIDED step 1"]
    G -- "reply mid-exercise" --> GS["GUIDED<br/>same step"]
    G -- no --> C{"classifier"}
    C -- "OFF_TOPIC" --> OFF["Fixed sentence, no model"]
    C -- "META" --> META["Isolated responder, no curriculum"]
    C -- "short follow-up" --> FU["FOLLOW_UP<br/>uses the memory"]
    C -- "PROBLEM / CODE / QUESTION" --> GR["Grounded prompt of that route"]
```

### Mode guidé

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Comprendre: new exercise
    Comprendre --> Indice: « Indice suivant »
    Indice --> Squelette: « Indice suivant »
    Squelette --> Solution: « Dernière étape »
    Comprendre --> Solution: « Voir la solution »
    Indice --> Solution: « Voir la solution »
    Squelette --> Solution: « Voir la solution »
    Comprendre --> Comprendre: student replies
    Indice --> Indice: student replies
    Squelette --> Squelette: student replies
    Indice --> Verification: « Je propose ma solution »
    Squelette --> Verification: « Je propose ma solution »
    Verification --> Indice: buttons stay
    Solution --> [*]
```

Steps 1–3 never contain the full solution; one that does is flagged as a
*leak* and counted in the console.

### Progress, derived from the discussions

```mermaid
flowchart LR
    E["Exercise of the série"] -->|"its statement appears in a discussion"| ST["Commencé"]
    ST -->|"a checked full solution is shown"| SV["Solution vue"]
    ST -->|"« Vérifier ma réponse » → Correct"| OK["Réussi ✓"]
    SV -->|"« Vérifier ma réponse » → Correct"| OK
```

`app/routes/progress.py` computes this on each `GET /progress` from the chat tables, so
past work counts and it can never drift from the history.

### The pipeline

| Stage | What it does |
| --- | --- |
| **Extraction** | `scripts/extract_chapter.py` turns a chapter PDF into tagged chunks. Tables are pulled out whole (the two-column *Algorithme \| Python* blocks are nonsense when flattened), prose splits at the document's own sub-boundaries rather than a character cap, and pseudocode blocks are never cut. |
| **Correction** | `scripts/patch_chunks.py` applies pinned, hand-verified fixes. The PDFs draw the assignment arrow `←` with a custom font glyph that decodes as `-`, turning an assignment into a subtraction. This is deliberately **not** automated — a regex would also rewrite genuine subtraction in the same tables. |
| **Embedding + retrieval** | `app/rag/rag_store.py` embeds with a multilingual model into Qdrant; `app/rag/retrieval.py` filters by scope, then searches semantically inside it. |
| **Context assembly** | `app/rag/context.py` builds the pinned core + retrieved extras, with a build check that fails loudly if a pinned table is missing or its arrows were lost. |
| **Gatekeeper** | `app/llm/gatekeeper.py` routes each message: `PROBLEM`, `CODE`, `QUESTION`, `META` or `OFF_TOPIC`. The three grounded routes each get their own prompt. |
| **Session memory** | `app/grading/session_memory.py` compacts the last three exchanges (answer tables kept, sizes capped) into quoted data for the prompt, an excerpt for the gatekeeper and the retrieval query; a short follow-up gets the `FOLLOW_UP` prompt. |
| **Learning modes** | `app/main.py` `learning_route` picks `GUIDED` (step 1–4), `CHECK` or `PRACTICE`; `app/grading/answer_check.py` proves notation mistakes in the student's work before the model sees it, and reads the verdict line back. |
| **Attachments** | `app/routes/attachments.py` turns a photo or PDF into the exercise text — `pdfplumber` for a PDF with a text layer, a Groq vision model (`GROQ_VISION_MODEL`) for photos and scans, asked only to transcribe — then it re-enters the pipeline as if typed. |
| **Generation** | `app/llm/prompts.py` holds the teaching constraints (a prompt per grounded route, plus a per-student "profil de l'élève" note that steers tone only); `app/llm/generate.py` / `app/llm/llm_stream.py` call the model (Groq, `openai/gpt-oss-120b`) and stream the answer. |
| **Checking** | `app/grading/algo_notation.py` rewrites any Python operator left in the Algorithme column (`//` → `div`); `app/grading/checker.py` then runs a mechanical constraint check over the finished answer. |
| **API** | `app/main.py` (FastAPI) — solving and attachment reading, plus the auth, chapter and admin routers. |
| **UI** | `ui/` — React 19 + Vite, served by nginx in Docker. |

### Platform

| Concern | How |
| --- | --- |
| **Vector store** | Qdrant (replaced an on-disk ChromaDB in Phase 0b). |
| **Relational store** | PostgreSQL via SQLAlchemy, schema managed by Alembic: users (with role, niveau, section), chat sessions, chat messages, emailed auth tokens, and uploaded chapters. |
| **Auth** | Two ways in. Google Identity Services on the frontend, verified server-side against Google's keys; and email + password (Argon2id), with emailed verification and reset links. Either way the backend issues its own signed session in an `httpOnly` cookie (PyJWT); the Google token is never treated as a session. A closed `role` (`student` / `admin`) gates the console; the admin role is granted only out of band by `scripts/promote_admin.py`. |
| **Rate limiting** | slowapi over Redis. Solving and attachment reading are limited **per user** (`10/minute;100/hour` by default, a shared budget); sign-in is limited **per IP** (`30/minute`). A 429 carries `Retry-After`, which the UI turns into *"Réessaie dans 47 secondes."* |
| **Groq queue** | `app/llm/llm_queue.py`: a Redis priority queue per model in front of every Groq call. Classifications rank ahead of solves, a solve waiting 20 s can no longer be jumped, a 429 is retried in the slot with `Retry-After`, and one request never waits more than 120 s in total. The UI gets `waiting` SSE events with the position. |
| **AI monitoring** | `app/llm/llm_usage.py` records each Groq call (tokens, latency, queue wait, 429s, outcome) to `llm_calls` from a background writer; `app/routes/admin/admin_monitoring.py` serves `/admin/monitoring` — per-model temperature (tokens/min, tokens/day, queue), 24 h KPIs, per-kind p50/p95, recent failures. Each row also carries the `user_id` that caused it, so spend can be read per account. |
| **Per-account activity** | `app/routes/admin/admin_user_activity.py` serves `GET /admin/users/{id}/activity`: weekly buckets (1–52, 12 by default) of questions by mode, discussions, tokens and calls, plus the exercise mix. Weeks with nothing are still emitted, so a gap reads as a gap rather than closing up. Spend only goes back to the migration that added `llm_calls.user_id`, and the response says when the meter starts instead of implying the whole history is there. |
| **Landing page** | Updates itself: `app/routes/public_overview.py` serves `GET /public/overview` (no sign-in, cached 60 s) — every chapter with its topics, exercise count and course-extract count, the totals, and feature switches — and `Landing.jsx` builds its numbers, programme cards, scope badge, chapter FAQ, syntax strip and photo claims from it. Publishing a chapter or adding exercises in the console shows up there within a minute; only a new *kind* of feature needs a card in `FEATURES`. |
| **Chat history** | `app/routes/chat_history.py` stores each account's discussions; every route is scoped to the caller's own rows. The list arrives light and a discussion loads in full when opened; saves upsert messages by id and carry a version (a stale save is a 409, merged and retried); the server saves each finished exchange itself. |
| **Live controls** | `app/core/runtime_settings.py` (cached, validated) + `app/llm/ai_control.py` + `app/routes/admin/admin_controls.py`: pause, daily budget guard, per-student limit, queue timeout, retries, and a switch per student feature — applied within seconds, each change written to `admin_audit` with who made it, revertible. |
| **Progress** | `app/routes/progress.py` derives each exercise's status, the next exercise, the latest checks and the recurring mistakes from the chat tables. |
| **Chapters** | `app/routes/chapters.py` serves the catalogue (scoped to the signed-in student's niveau), each chapter's exercises and the lesson PDF — all behind sign-in. `app/routes/admin/admin_chapters.py` + `app/rag/chapter_store.py` back the admin upload/publish workflow; `app/rag/course_markdown.py` reads a Markdown-authored chapter. |

### Data model

```mermaid
erDiagram
    USERS ||--o{ CHAT_SESSIONS : owns
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
    CHAT_SESSIONS ||--o{ ANSWER_FEEDBACK : receives
    USERS ||--o{ ANSWER_FEEDBACK : gives
    USERS ||--o{ AUTH_TOKENS : "verify / reset"
    USERS ||--o{ LLM_CALLS : spends
    UPLOADED_CHAPTERS }o--|| USERS : "published by"

    USERS {
        uuid id
        string role "student | admin"
        string niveau
        string section
        string plan
        string solve_rate_limit "personal override"
    }
    CHAT_SESSIONS {
        uuid id
        string title
        string chapitre
        int version "stale saves refused"
    }
    CHAT_MESSAGES {
        string client_id "the chat's own id"
        string role
        text content
        string checker_status
        jsonb extra "route, guided, check, practice, mode"
    }
    ANSWER_FEEDBACK {
        string message_client_id
        int rating "-1 | 1"
    }
    LLM_CALLS {
        uuid user_id "whose call — nullable, from a2c7e4b9d631"
        string kind
        string route
        int tokens
        int memory_chars
    }
    APP_SETTINGS {
        string key
        jsonb value
    }
    ADMIN_AUDIT {
        string action
        jsonb detail "before / after"
    }
```

### API at a glance

| Route | Auth | What |
| --- | --- | --- |
| `GET /health` | — | `{"status":"ok","model":"…"}` |
| `GET /public/overview` | — | What the landing page shows: chapters, exercise and extract counts, features |
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
| `GET /chat/sessions` · `GET` / `PUT` / `DELETE /chat/sessions/{id}` | cookie | The signed-in student's own discussions (light list, full on open, versioned saves) |
| `POST /chat/feedback` | cookie | 👍 / 👎 on an answer (0 takes it back) |
| `GET /chat/features` | cookie | Which learning features the admin turned on, and the default mode |
| `GET /progress` | cookie | Per chapter: each exercise's status, the next one, recent checks, recurring mistakes |
| `/admin/*` · `/admin/chapters/*` | cookie + admin | The console: users, stats, and the chapter upload/publish workflow |
| `GET /admin/monitoring` | cookie + admin | Groq load and usage, chat activity, routes, feedback, learning stats (Surveillance IA) |
| `GET /admin/users/{id}/activity` | cookie + admin | One account's weekly activity and spend (`?weeks=1…52`, 12 by default) |
| `GET` / `PUT /admin/controls` · `POST /admin/controls/queues/reset` | cookie + admin | Live AI controls |
| `GET /admin/audit` · `POST /admin/audit/{id}/revert` | cookie + admin | The action log, and putting a settings change back |

Request/response shapes, the SSE event contract and the pre-launch checklist
are in [`README_API.md`](README_API.md).

### Where the code lives

The backend is one package, grouped by what a module depends on rather than
by what it is called. The direction is one-way — `core` knows nothing about
`routes` — so an import that has to go backwards is a design problem showing
itself, not a reason to add a package.

```
app/
  main.py              FastAPI app; /solve, /solve/stream, /solve/extract,
                       and the learning_route switch
  core/                config · db · models · runtime_settings · ratelimit
  auth/                auth · password_auth · emails
  llm/                 llm_queue · llm_stream · llm_usage · generate ·
                       prompts · gatekeeper · ai_control
  rag/                 rag_store · retrieval · context · chapter_store ·
                       course_markdown
  grading/             checker · answer_check · algo_notation ·
                       session_memory
  routes/              chapters · progress · chat_history ·
                       public_overview · attachments
    admin/             admin · admin_chapters · admin_controls ·
                       admin_monitoring · admin_user_activity
scripts/               promote_admin · seed_demo_activity ·
                       extract_chapter · patch_chunks
tests/                 the suite
alembic/               migrations
docker/                the Dockerfile, its ignore file, and the three
                       compose files
env/                   .env (gitignored) and .env.example
ui/                    the React app (see Frontend, below)
```

Everything runs as a module, never as a path: `python -m scripts.promote_admin`,
`python -m tests.test_chat_flow`. Running a file inside a package by path puts
that file's own directory on `sys.path` instead of the repository root, and
`import app…` then fails.

---

## You must supply your own curriculum material

**No curriculum PDFs or extracted text are included in this repository.** The
source documents belong to their authors and are not ours to redistribute, so
`data/*.pdf`, `chunks.json` and `sample_problems.json` are all gitignored.

To run Fahem you need your own chapter PDF. The pipeline expects a document
with roman-numeral sections and a `Série d'exercices`; other layouts will need
`scripts/extract_chapter.py`'s heading patterns adjusted.

The pinned tables in `app/rag/context.py` are located by **anchor strings matched
against your corpus** — they are specific to the chapter this was built
against, and will need replacing for a different chapter. `app/rag/context.py` fails
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

The compose files live in `docker/` and the environment in `env/`, so every
command carries two flags. They are not optional: Compose takes the directory
of the first `-f` file as the project directory, so without
`--project-directory .` it resolves the bind mounts against `docker/` and
looks for `docker/.env`.

Run from the repository root. Worth an alias:

```powershell
# PowerShell profile
function dc { docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml @args }
```

```bash
# bash
alias dc='docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml'
```

```bash
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml up --build -d      # UI on http://localhost:5173, API on :8000
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend alembic upgrade head      # first run: create the tables
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml logs -f backend
```

Open the UI at **`http://localhost:5173`** — `localhost`, not `127.0.0.1`.
The session cookie is `SameSite=Lax`, and `localhost:5173 → 127.0.0.1:8000`
is a cross-site request, so sign-in would fail with a silent 401.

### 3. Build the index from your PDF

```bash
python -m scripts.extract_chapter "data/your-chapter.pdf" --niveau 2eme --chapitre 1
python -m scripts.patch_chunks          # applies pinned fixes, prints the arrow check
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m app.rag.rag_store --reset      # load chunks.json into Qdrant
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m app.rag.rag_store --describe   # what is in the store
```

**Read the `scripts/patch_chunks.py` output.** It lists every surviving `←` and every
line shaped like a corrupted one. The automated check only catches shapes it
has been told about — skim any declaration- or affectation-heavy page by hand.

`chunks.json`, `sample_problems.json` and `data/` are bind-mounted, so
rebuilding an image does not discard them. Qdrant, Postgres and the embedding
model cache live in named volumes and survive a `down`. Redis
deliberately keeps nothing on disk — rate-limit counters are meant to be
short-lived. The frontend image bakes `VITE_API_URL` and
`VITE_GOOGLE_CLIENT_ID` in at build time, so changing either means rebuilding
it.

### 4. Check retrieval before involving a model

```bash
cp sample_problems.example.json sample_problems.json   # then add your own problems
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_retrieval   # prints retrieved chunks
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m app.rag.context          # pinned core + extras, with build check
```

### 5. Generate from the command line

```bash
python -m app.llm.generate                          # all problems
python -m app.llm.generate --only demo01            # one
python -m app.llm.generate --temperature 0          # deterministic-ish
```

### Without Docker

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt    # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml up -d postgres qdrant redis                     # the stores still come from compose
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

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

Everything tunable is in `app/core/config.py`, read from env with working defaults:

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
| `GATEKEEPER_REASONING_EFFORT` | `low` | keeps gpt-oss from spending the gatekeeper's token budget on reasoning |
| `GROQ_MAX_CONCURRENT` / `GROQ_VISION_MAX_CONCURRENT` | `1` / `1` | slots per model queue |
| `GROQ_QUEUE_TIMEOUT_SECONDS` | `120` | total wait budget of one request |
| `GROQ_RETRY_MAX` | `3` | 429 retries inside a slot |
| `GROQ_QUEUE_AGING_SECONDS` | `20` | after this, later classifications can no longer jump a solve |
| `GROQ_TPM_LIMIT` / `GROQ_TPD_LIMIT` | `8000` / `200000` | limits the monitoring measures load against |
| `LLM_USAGE_RECORDING` / `LLM_USAGE_RETENTION_DAYS` | `1` / `7` | per-call monitoring rows |
| `TRUSTED_CLIENT_IP_HEADER` | *(empty)* | set by the share modes only (`CF-Connecting-IP`, `X-Forwarded-For`) |

Inside compose, `DATABASE_URL`, `QDRANT_URL` and `REDIS_URL` are overridden to
point at the sibling containers.

### Sharing a test link (free)

To let friends try Fahem without renting a server, run the stack on your own
PC and publish it through a free Cloudflare quick tunnel (no account, no
domain):

```powershell
powershell -ExecutionPolicy Bypass -File share.ps1
```

It rebuilds the frontend to call the API on the same address (`/api`, proxied
by nginx), starts a `cloudflared` container, and prints a
`https://<random>.trycloudflare.com` link. Friends sign up with e-mail and
password - the share build hides the Google button, because Google refuses
sign-ins from an origin not registered in its console (`origin_mismatch`) and
the tunnel's address is random. The link lives as long as your PC and Docker are on, and
changes when the tunnel restarts. Stop sharing with
`dc -f docker/docker-compose.share.yml stop tunnel` (the alias from *Start the
stack*); go back to local-only with a plain `dc up -d --build`.

**With Google sign-in (fixed address).** Google only accepts sign-ins from
origins registered for the OAuth client, so it needs an address that does not
change: an ngrok free static domain.

1. Create a free account at ngrok.com; copy your authtoken and claim your free
   domain (Dashboard → Domains).
2. In `.env`: `NGROK_AUTHTOKEN=…` and `NGROK_DOMAIN=your-name.ngrok-free.app`
   (no `https://`).
3. Google Cloud Console → APIs & Services → Credentials → your OAuth client →
   *Authorised JavaScript origins* → add `https://your-name.ngrok-free.app`.
   If the OAuth consent screen is in *Testing*, only the listed test users can
   sign in: add your friends' Gmail addresses there, or publish the app.
4. `powershell -ExecutionPolicy Bypass -File share-ngrok.ps1` (it stops the
   Cloudflare link if one is running).

ngrok's free plan shows visitors a one-time "You are about to visit" page;
they click *Visit Site*. Stop with
`dc -f docker/docker-compose.ngrok.yml stop ngrok`.

Mind Groq's free tier: about 200,000 tokens a day for the text model, roughly
35 solves shared by everyone. Admin → Surveillance IA shows how much is left.

---

## Tests

```bash
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_checker    # checker pass/fail suite
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_auth       # token verification, sessions, config guards
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_db         # models, constraints, cascades
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_admin      # admin role gate and user management
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_chapters_admin   # chapter upload/publish workflow
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_course_markdown  # Markdown chapter parsing
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_llm_queue  # Groq queue: priority, aging, deadline, 429 retry
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_llm_usage  # per-call recording and /admin/monitoring
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_public_overview  # what the landing page is told
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_admin_controls   # live controls, audit log, revert
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_algo_notation    # div / mod in the Algorithme column
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_session_memory   # compaction, prompts, follow-ups (--live calls the model)
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_chat_flow        # light list, versioned saves, server save, feedback
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_guided_check     # Mode guidé steps, Vérifier ma réponse, notation pre-check
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_practice_progress  # Exercice similaire, daily limit, progress
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_gatekeeper_meta  # meta answers never leak reasoning (--live calls the model)
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_retrieval  # retrieval inspection (no assertions)
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_gatekeeper_adversarial   # adversarial transcripts; calls the model
```

They are standalone scripts that print `[PASS]` lines and end with
`ALL PASSED`. `tests/test_gatekeeper_adversarial.py` makes real model calls and
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

**Not every message reaches the pipeline the same way.** `app/llm/gatekeeper.py`
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
thought before the answer; `app/llm/llm_stream.py` forwards only the answer channel.
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

**Discussions belong to the account.** Chat history is stored server-side
(`app/routes/chat_history.py`), so two students on the same browser never see each
other's discussions, and a student finds theirs on any device.

**Groq's daily limit is the one that runs out.** On the free tier gpt-oss-120b
allows 8,000 tokens a minute but only 200,000 a day — about 35 solves shared by
everyone — and the per-day figure never appears in the response headers, only
in a 429's body. `app/llm/llm_usage.py` keeps that figure, and Surveillance IA shows the
day's usage against it.

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
  moves. Every signed-in screen opens on a skip link to the content, shown on
  plain `:focus` — `:focus-visible` is not reliably raised when a link is
  focused from script, which hid it the first time.
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

Motion (`motion/react`) animates the app through `LazyMotion`: the student
app loads `domAnimation` (no layout animations), the admin console `domMax`.
Everything that moves respects `prefers-reduced-motion`.

Light and dark are driven off `<html data-theme>`: a toggle sets it, and it
defaults to the OS setting. The palette is the "Violet Dusk" token set, and
every colour keeps AA contrast in both themes.

---

## Layout

**Backend** (one package, grouped by dependency — see *Structure notes*)

```
app/main.py                FastAPI app: /health, /solve, /solve/stream,
                           /solve/extract; mounts every router

app/core/                  the bottom of the stack: imports no other app package
  config.py                all env/config: endpoints, model names, paths, limits
  db.py / models.py        SQLAlchemy engine + User, ChatSession, ChatMessage,
                           AuthToken, UploadedChapter, LlmCall
  runtime_settings.py      settings an admin changes live (cached, validated, audited)
  ratelimit.py             slowapi limiter over Redis; per-user and per-IP keys

app/auth/
  auth.py                  /auth: Google token exchange, session cookie, current user
  password_auth.py         /auth: email+password signup/login, verification, reset
  emails.py                sends verification / reset mail

app/llm/                   everything that reaches Groq
  llm_queue.py             Redis priority queue in front of every Groq call
  llm_stream.py            streaming Groq call; filters the reasoning channel
  llm_usage.py             records every Groq call for the monitoring
  generate.py              Groq/Ollama HTTP clients + CLI harness
  prompts.py               the teaching constraints (a prompt per grounded route)
  gatekeeper.py            routes each message PROBLEM / CODE / QUESTION / META /
                           OFF_TOPIC before the pipeline sees it; meta-responder
                           + output safety net
  ai_control.py            pause, budget guard, live limits applied to requests

app/rag/                   the curriculum
  rag_store.py             embedding + Qdrant storage
  retrieval.py             scope-filtered semantic search
  context.py               pinned syntax core + retrieved extras
  chapter_store.py         the uploaded-chapter store behind the admin workflow
  course_markdown.py       reads a Markdown-authored chapter

app/grading/               what happens to an answer once it exists
  checker.py               the constraint checker (rules, patterns, thresholds)
  answer_check.py          notation mistakes in a student's own solution; verdicts
  algo_notation.py         course operators in the Algorithme column (div, mod, ≠…)
  session_memory.py        what a discussion remembers, compacted for the prompt

app/routes/
  chapters.py              /chapters: catalogue (year-scoped), exercises, lesson PDF
  progress.py              /progress: exercise statuses derived from the discussions
  chat_history.py          /chat: discussions, feedback, features
  public_overview.py       /public/overview: live facts for the landing page
  attachments.py           reads an exercise from an attached photo or PDF
  admin/
    admin.py               /admin: role gate, stats, user management
    admin_chapters.py      /admin/chapters: upload → extract → review → publish
    admin_monitoring.py    /admin/monitoring: Groq load, usage, chat activity
    admin_controls.py      /admin/controls, /admin/audit
    admin_user_activity.py /admin/users/{id}/activity: one account, week by week

scripts/                   offline tools, run as `python -m scripts.<name>`
  extract_chapter.py       PDF → tagged chunks
  patch_chunks.py          pinned corrections
  promote_admin.py         grant/revoke the admin role
  seed_demo_activity.py    a demo account with twelve weeks of activity, for the
                           charts (--tokens, --remove)

tests/                     the suite, run as `python -m tests.<name>`
alembic/                   migrations

docker/
  Dockerfile               the backend image; context is the repository root
  Dockerfile.dockerignore  named for the Dockerfile, not .dockerignore - see
                           the comment at its head before renaming it
  docker-compose.yml       the stack
  docker-compose.share.yml    free test link (Cloudflare quick tunnel), with share.ps1
  docker-compose.ngrok.yml    fixed test link with Google sign-in, with share-ngrok.ps1

env/
  .env                     secrets and local overrides; gitignored
  .env.example             the committed template
```

**Frontend** (`ui/src`)

```
config.js            NIVEAU / CHAPITRE / SCOPE_LABEL / API_URL / GOOGLE_CLIENT_ID
App.jsx              auth gate (checking / signed out / signed in / needs-profile) + routes
App.css              tokens, primitives, then per-screen placement
routes/              Home, ChapterPage, Chat, ProgressPage, ResetPassword, admin/*
components/          AppLayout, AppSidebar, Message, Composer, Markdown,
                     AlgoCode, GroundingStrip, HistoryPanel, ThemeToggle,
                     SignInScreen, PasswordAuthForm, GoogleSignIn,
                     AuthShell, ProfileSetup, PythonRunner, admin/*
components/landing/  Hero.jsx, Bento.jsx and landing.css — the signed-out page
components/learning/ Learning.jsx: step rail, verdict card, confetti, challenge card
components/ui/       Button, Badge, Alert, Skeleton, EmptyState
lib/                 api.js (SSE client + attachment upload), auth.js,
                     authContext.js, profile.js, theme.js, chapters.js,
                     sessions.js (server-side history), admin.js, algoHighlighter.js,
                     alignAlgoTable.js, remarkAlgoTable.js, hasRealSolution.js,
                     learning.js (guided state, verdicts), pythonRunner.js (Pyodide worker),
                     progressApi.js, algoNotation.js
data/                demoExercises.js: the landing demo's canned answers
grammar/             algoPseudocode.json (TextMate grammar), algoThemes.js
```

### Structure notes

The backend was flat at the repository root until it reached 39 modules, at
which point the directory listing stopped being something you could read.
They are grouped now, by what a module *depends on* rather than by what it is
called, and the direction is one-way: `core` knows nothing about `routes`, so
an import that has to go backwards is a design problem showing itself rather
than a reason to add a package.

The move was mechanical on purpose — files moved with `git mv` so blame
follows them, every import rewritten to its `app.*` path, and nothing else
touched. The one behavioural constraint it introduced is the `-m` form:
`python -m scripts.promote_admin`, not `python scripts/promote_admin.py`.
Running a file inside a package by path puts that file's own directory on
`sys.path` instead of the repository root, and `import app…` then fails.

An earlier, smaller restructure is still visible in the shape of the code:
the constraint checker was extracted out of `app/llm/generate.py` (which was
doing HTTP clients *and* the checker *and* a CLI) because only the checker
had a real test suite behind it. `app/core/config.py` is the single source
for values that used to be scattered, and `app/llm/generate.py` and
`app/rag/rag_store.py` re-export the names they used to define, so older
imports elsewhere keep working.

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
| **Phase 7** | An enforced `student` / `admin` role, granted out of band by `scripts/promote_admin.py`. |
| **Phase 8** | The admin console: users, stats, session revocation. |
| **Phase 9** | Uploaded chapters — an admin upload → extract → review → publish workflow (9b: Markdown-authored chapters). |
| **PR #11** | Solve from a photo or PDF; `CODE` / `QUESTION` gatekeeper routes and line-by-line answers; a slimmed sign-in screen; a light/dark toggle; the student profile (niveau + section) that scopes the chapter list and steers the tutor's tone; per-account chat history. |
| **PR #12** | The Groq priority queue (phases A and B): `users.plan`, a Redis queue per model, 429 retry inside the slot. |
| **PR #13** | Queue follow-ups (one wait deadline, gatekeeper `waiting` events, classifications ahead of solves, aging); the gatekeeper fix (no raw reasoning, identity and own-level questions answered); Surveillance IA; the free share modes (Cloudflare, ngrok with Google sign-in). Chapter 2's 12 exercises were added through the console (database, not code). |
| **PR #14** | Surveillance IA KPIs; live AI controls with an action log and revert; the self-updating landing page; bottom toasts; `div` / `mod` guaranteed in the Algorithme column. Session memory and the `FOLLOW_UP` route; the chat audit (per-discussion stop, light history, versioned and server-side saves, feedback, edit / regenerate); Mode guidé; Vérifier ma réponse; Exercice similaire; ▶ Exécuter le Python; Ma progression; the redesigned Contrôles page with a separate Journal tab; Motion throughout. Audit: [`docs/audit-2026-09-17-learning-features.md`](docs/audit-2026-09-17-learning-features.md). |
| **PR #15** | The audit's first findings closed (the learning modes' `exercise` field through the gatekeeper, « Réussi » only when the check came first, the budget guard on, heading order and live regions, the student bundle down to 695 kB). A landing page rebuilt around a demo anyone can play without an account. The chat's four strips of explanation folded into one line under an answer and one under the composer, and a skip link ahead of both. **Mode guidé as the default.** `llm_calls.user_id`, and an **Activité** tab per account: twelve weeks of charts to decide quotas and offers on. |

## Status and what's next

The product works end to end: sign in, answer the one-time class question,
pick a chapter for your year, read the lesson, click an exercise or paste one
(or send a photo of it), get a grounded, checked answer. Friends can test it
from a share link (see *Sharing a test link*).

Next, roughly in order (details and more ideas in
[`docs/audit-2026-09-17-learning-features.md`](docs/audit-2026-09-17-learning-features.md)):

- **Act on what the Activité tab shows** — the per-account charts are in; the
  decision they were built for is still made by hand. `users.plan` and the
  per-student solve limit are the levers already wired for it, so the missing
  piece is the policy, not the plumbing.
- **Ready-made answers for catalogue exercises** — generate hints, skeletons
  and solutions once, serve them instantly, and spare the daily Groq budget.
- **Make practice a game** — an animated execution trace, Parsons puzzles, a bug
  hunt, XP and badges.

- **Before a real deployment** — set a real `SESSION_SECRET_KEY`,
  `SESSION_COOKIE_SECURE=true` and `CORS_ORIGINS`; enable Qdrant's API key;
  stop publishing Postgres/Qdrant/Redis ports; and close the items in
  `README_API.md`'s pre-launch list (generic error bodies, and who may receive
  curriculum excerpts).
- **More Groq budget** — the free tier's 200,000 tokens a day is the real
  ceiling on how many students can use Fahem at once; a paid tier or a second
  model for the gatekeeper is the lever.
- **More chapters, more years** — the profile already scopes the chapter list
  by niveau, so a 3ème/Bac student currently lands on an honest empty state.
  Each new chapter needs its PDF (or Markdown), its pinned-table anchors in
  `app/rag/context.py`, and a check with `tests/test_retrieval.py`. This is the main unlock.
- **Scope the chat to the profile** — the freeform chat still defaults to the
  2ème corpus; point it at the student's own niveau once that year has content.
- **Section-aware chapters** — tag chapters with a section so the catalogue can
  filter on it too, not only the niveau (`catalogue(niveau=…)` is written for
  this).
- **Chapter 3 (structures itératives)** — still *À venir*; author it in
  Markdown like chapter 2 and publish it with its série.
