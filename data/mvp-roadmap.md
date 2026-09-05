# MVP roadmap — AI algorithm learning assistant

**Guiding rule:** prove the RAG loop works on paper before touching UI or auth. You're the domain expert (you teach algo), so use that — validate every output against your own teaching standard as you go, not at the end.

## Phase 0 — Prep (do this first, before any code)
- [ ] Pick **one** chapter you teach well and **one** niveau (e.g. 2ème — tableaux)
- [ ] Gather source material: official curriculum content + your own materials, 5–10 solved exercises for that chapter
- [ ] Write out, by hand, what a correct answer looks like for 3 sample problems (exact syntax + reasoning). This is your test set — you'll compare pipeline output against it later.

## Phase 1 — RAG pipeline, no UI yet
- [ ] Chunk your chapter material — keep pseudocode blocks intact, don't let a generic splitter cut them mid-block
- [ ] Tag each chunk: `niveau`, `chapitre`, `type` (syntax rule vs worked example)
- [ ] Embed and store — pgvector (reuse your existing Postgres from ProManager, no new infra) or Chroma if you want something simpler
- [ ] Build retrieval: filter by niveau + chapitre first, semantic search second
- [ ] Test retrieval alone — print what gets retrieved for your 3 sample problems, confirm it's actually relevant, before wiring anything to the LLM

## Phase 2 — Generation + self-check
- [ ] Prompt template with three jobs: retrieved syntax context, an instruction to only use techniques taught in that chapter, and an instruction to trace the solution against a sample input before presenting it
- [ ] Run your 3 sample problems through it — does a teacher (you) accept the syntax and logic?
- [ ] Iterate the prompt until all 3 pass, then expand to the full 10

## Phase 3 — Thin API
- [ ] One FastAPI endpoint: problem + niveau + chapitre in, solution out
- [ ] Reuse your existing Groq/Llama integration pattern from ProManager
- [ ] No auth yet — just prove the endpoint works end to end

## Phase 4 — Minimal UI
- [ ] One screen: chapitre dropdown, textarea to paste the problem, submit button, solution display
- [ ] Reuse Angular from ProManager
- [ ] Explicitly skip: login, dashboard, chapter browsing UI, quiz mode, file upload

## Phase 5 — Real test
- [ ] Give it to 2–3 actual students with real homework problems
- [ ] Where it breaks tells you what to fix before adding any scope

## Not on the MVP path (v2 territory)
- Login / auth
- Quiz mode (build this after chat mode proves the concept works)
- "Ask anything" — image/PDF/doc upload
- Multiple chapters or niveaux
- Progress tracking, gamification, dashboards

## Time discipline
Phases 1–4 are realistic in a few weeks of solo evenings/weekends if scope stays fixed. The moment you're building something not on this list, stop — it's not MVP, park it for later.
