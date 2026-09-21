# Audit — learning features (2026-09-17)

Scope: Mode guidé, Vérifier ma réponse, Exercices similaires, Python runner,
Ma progression, the redesigned IA controls, and their animations.

## How it was checked

- Backend: 8 suites run in the deployed container — **191 checks, 0 failures**
  (`test_practice_progress` 12, `test_guided_check` 21, `test_chat_flow` 22,
  `test_session_memory` 24, `test_admin_controls` 45, `test_llm_usage` 21,
  `test_algo_notation` 33, `test_public_overview` 13).
- Frontend: `vite build` (bundle sizes), oxlint clean.
- Accessibility: axe-core 4.10 on `/progression`, `/chat`,
  `/admin/ia?onglet=controles`, `/admin/ia?onglet=journal`, `/chapitre/1`.
- Responsive: Playwright at 1280 px and 390 px — no horizontal scroll.
- Performance: timing of `/progress`, `/chat/sessions`, `/chat/features`.
- Code review of the new server paths (`app/main.py`, `app/routes/progress.py`).

---

## 🔴 Fix first

### 1. The gatekeeper can be bypassed through the new modes

- `skips_classifier` (`app/main.py:516`) skips the topic classifier for
  `mode: "check"`, `mode: "practice"` and the guided buttons.
- The `exercise` field (up to 2000 characters, `app/main.py:272`) is never part of
  `gate_text` (`app/main.py:281`), so it goes through neither the length check nor
  the classifier.
- Someone calling the API directly can put any text in `exercise` and get
  model output, including a prompt injection, without the off-topic filter.

**Fix:** run the length check and a light topic check on `exercise`, or better,
have the server read the exercise from the saved discussion instead of
trusting the client.

### 2. The Groq budget is exhausted today

- 239 406 / 200 000 tokens used over 24 h; a live check got
  « service très sollicité ».
- The daily budget guard is set to « Jamais ».

**Fix:** set the guard to 90 %, and see idea 1 (ready-made answers).

### 3. « Réussi » can be gamed

A student can open the full solution, paste it into « Vérifier ma réponse »,
get **Correct**, and the exercise counts as solved alone.

**Fix:** only count it when the check comes before the solution was shown, or
label it « Réussi après correction ».

---

## 🟠 Should fix

### 4. Accessibility (axe-core)

| Page | Rule | Impact | Where |
|---|---|---|---|
| Contrôles | color-contrast | serious | `.cx-big-btn` (orange on light) |
| Contrôles | aria-allowed-role | minor | `h2` with `role="status"` |
| Contrôles | heading-order | moderate | `#cx-features` |
| Chat | landmark-one-main | moderate | no `<main>` |
| Chat | heading-order | moderate | `h3` |
| Chat | region | moderate | messages outside landmarks |
| Progression, Journal, Chapitre | — | — | no violations |

### 5. One 1.1 MB JavaScript bundle

`index.js` is 1 116 kB (345 kB gzip). Students download the admin console and
Shiki on first visit. Lazy-loading the admin routes and the heavy libraries
(`React.lazy` + dynamic `import()`) would roughly halve it for students.

### 6. A practice slot is used before generating

`take_practice_slot` (`app/main.py:586`) counts the request before Groq answers. If
the call fails or the student stops, the daily slot is still gone.

**Fix:** give the slot back on error or on stop.

### 7. `/progress` reads every message

It loads all messages of all discussions, full answers included. It takes
24 ms today (8 kB response) but grows with history.

**Fix:** select only the columns it needs (user text, status, `extra` keys),
or keep a small progress table updated at the end of each answer.

---

## 🟡 Minor

8. **Celebrations can replay:** `freshId` (Chat.jsx) stays set, so switching
   discussions and coming back replays that answer's animation. Clear it
   after it plays.
9. **The difficulty menu** (« Exercice similaire ») does not close with Escape
   or a click outside.
10. **Exercises solved from a photo never count in progress:** progress
    matches the exercise text exactly.

---

## 💡 Creative ideas

### Zero tokens

1. **Ready-made answers for catalogue exercises.** Generate hints, skeletons
   and solutions for the 19 exercises once, at night, then serve them
   instantly. Instant answers, far fewer tokens — directly addresses finding 2.
2. **🎬 Animated trace.** The Python runner steps through the program line by
   line: the matching Algorithme line lights up and the variable table fills
   in as values change, with play / pause / step buttons.
3. **🧩 Parsons puzzles.** Shuffled algorithm lines to drag into the right
   order, checked automatically. Ideal for chapter 1 and on phones.
4. **🐞 Bug hunt.** A correct solution with 1–3 planted mistakes (`//` instead
   of `div`, `=` instead of `←`, a missing `Lire`); the student taps the wrong
   lines. Trains exactly the mistakes that cost points.
5. **🏅 XP, levels and badges.** « Maître du div/mod » after 5 checks with no
   operator mistake, « Sans filet » for 3 exercises solved without hints, a
   daily streak with a 🔥 flame — all from data already stored.
6. **🧠 Flashcards from the student's own mistakes.** « Mes erreurs
   fréquentes » becomes a 2-minute daily quiz, repeated until it sticks.
7. **🔀 Automatic flowchart.** Draw the flowchart from the Algorithme column,
   animated block by block.

### A few tokens, big « wow »

8. **📸 Red-pen correction on the photo.** The student photographs their copy;
   « Vérifier ma réponse » draws red circles and notes on the image.
9. **📝 Mock Bac exam.** Three timed exercises, graded with the check, ending
   with a grade out of 20 and a printable report.
10. **⚔️ Duel.** Two friends get the same generated exercise; the first with a
    Correct check wins, with a shared animated result screen.
11. **🗣️ « Explique-moi autrement ».** Re-explain a notion with an everyday
    analogy or in simple Darija, with text-to-speech.

### For schools

12. **👩‍🏫 Class mode.** A teacher shares a class code, assigns exercises and
    sees a heatmap of common mistakes (« 60 % confuse `mod` and `div` »).
13. **📱 Installable app (PWA).** Chapters, the runner and puzzles work
    offline, which suits unreliable connections.

---

## Recommended order

1. Fix findings **1–3** (bypass, budget guard, « Réussi » integrity).
2. Build **ready-made answers (idea 1)** — solves the budget problem.
3. Build the **animated trace (idea 2)** and **XP and badges (idea 5)** —
   make practice feel like a game.
