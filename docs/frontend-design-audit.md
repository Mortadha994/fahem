# Frontend design audit

Branch `phase-3b-frontend-chapters` @ `312a57f`. Audited against the running
application at `localhost:5173`, signed in, plus the source at `ui/src`.

**No code was changed in producing this document.**

## How to read the evidence

Every claim below is tagged with how it was established:

- **[observed]** — measured in the running app through the browser.
- **[source]** — read directly out of `ui/src`.
- **[derived]** — reasoned from the CSS, *not* seen rendering. Only used for the
  narrow-viewport section, and flagged again there.

One limitation up front, because it shapes section 6: `resize_window` reported
success but `window.innerWidth` stayed at 2048 every time, so **the application
was never actually rendered at a narrow viewport during this audit**. The
responsive findings are read out of the media queries and layout rules. They are
predictions, not observations, and they are the first thing to verify by hand.

A second, smaller caveat: the browser reports `devicePixelRatio: 0.9375`, so
pixel measurements below are CSS pixels as the page sees them.

---

## 1. Current architecture

**[source]** React 19.2 + Vite 8.2, `react-router-dom` 7.18. 24 files, 3,409
lines under `ui/src`.

```
main.jsx            BrowserRouter
└── App.jsx         auth gate (checking | out | in) + <Routes>
    └── AppLayout   appbar (brand · Chapitres · Poser une question · account)
        ├── /                Home.jsx          chapter catalogue
        ├── /chapitre/:id    ChapterPage.jsx   Documentation | Exercices tabs
        └── /chat            Chat.jsx          sidebar + thread + composer
```

| Concern | Implementation |
|---|---|
| Routing | `BrowserRouter`; nginx `try_files` serves the SPA |
| Auth | Three-state gate wrapping the router; `AuthContext` for `user`/`logout`/`onUnauthorized` |
| State | Local `useState` per route; no store, no query cache |
| Chat history | `localStorage` (`sessions.js`), browser-scoped |
| API | `lib/api.js` (SSE), `lib/auth.js`, `lib/chapters.js` — all `credentials: "include"` |
| Styling | **One global stylesheet**, `App.css`, 1,060 lines. No CSS modules, no utility framework, no CSS-in-JS |
| Markdown | `react-markdown` + `remark-gfm` + custom `remarkAlgoTable` + Shiki with a hand-written TextMate grammar |
| Icons | **None.** Text glyphs: `☰ × ✓ ⚠ ← →` |
| Components | 9 local components. No component library |
| Frontend tests | **None.** `oxlint` + `prettier` only |

**What is genuinely good here and should not be disturbed:** the streaming
pipeline, the Shiki grammar and the `Algorithme | Python` table rendering are
the product's actual differentiator and they work. The auth gate's structure —
`App` returning the sign-in screen before `<Routes>` ever mounts — is a real
architectural guarantee, not a convention. Leave all of it alone.

---

## 2. Current design system

There is a **colour system** and essentially nothing else.

### What exists

**[source]** 13 semantic colour tokens with a full dark-mode override:

```
--bg  --bg-alt  --side  --line  --fg  --fg-dim
--accent  --accent-fg  --ok/--ok-bg  --warn/--warn-bg  --err/--err-bg
```

This part is well-formed: semantic names, not literal ones, and every value has
a dark counterpart. It is the foundation to build the rest on.

**[source]** Typography base is sane — `body` sets `15px/1.55 system-ui`.

### What does not exist

**[source]** Counted across `App.css`:

| Scale | Distinct values | Token? |
|---|---|---|
| `border-radius` | **11** — 2, 4, 5, 6, 7, 8, 10, 12, 14px, 50%, 999px | none |
| `font-size` | **23** — 0.7 … 1.5rem, plus 3 `em` values | none |
| `padding` | **~25** distinct declarations | none |
| `box-shadow` | **0 uses** — the UI is entirely flat, borders only | none |
| transition / animation | **4 total**, two of them sidebar-only | none |

There is no `--space-*`, `--radius-*`, `--text-*`, `--shadow-*` or `--ease-*`.
Spacing values are chosen per-rule: `0.85rem`, `0.65rem`, `0.55rem`, `0.32rem`,
`0.28rem`, `0.12rem` all appear. That is not a system, it is 1,060 lines of
individual decisions — which is exactly why sections 8 and 9 read as they do.

The monospace stack `ui-monospace, SFMono-Regular, Menlo, monospace` is repeated
inline **3 times** rather than tokenised.

---

## 3. Page-by-page UX analysis

### 3.1 Sign-in — `/` when signed out

**Goal:** establish what Fahem is, then get out of the way.

**[observed]** Card renders centred; brand, one-line value proposition, Google
button, scope label. The gate is real — typing `/chapitre/1`, `/chat` or `/`
while signed out mounts **no** `.shell`, `.appbar`, `.app` or `.page`, and the
only backend call is `/auth/me`.

Works. The weakness is that it is the product's entire first impression and
currently reads as a utility dialog — no visual identity beyond a blue wordmark.

### 3.2 Home — `/`

**Goal:** choose a chapter, or jump straight to a free question.

**[observed]** 1 `<h1>`, 1 `<nav>`, 1 `<main>`, **2 `<header>`** (appbar +
`.page-head`). 5 interactive elements. Contrast: 16 of 17 text nodes pass;
the one failure is the avatar initial, which is `aria-hidden`.

The `coming_soon` handling is genuinely right: `<div aria-disabled="true">`, no
`href`, no hover affordance — nothing that invites a click that cannot happen.

**Problems:**
- **[observed]** On a 2048px-wide window the page is three ~256px cards at the
  top of an otherwise empty screen. `.page` caps at `62rem` and centres, so the
  layout is *correct*; it simply has nothing to say. There is no sense of
  progress, no "continue where you left off", no recent activity — all of which
  the app already has data for in `localStorage`.
- **[source]** If `fetchChapters` fails the page shows one line of red text and
  nothing else. No retry control.
- **[source]** No skeleton — the chapter grid pops in after `Chargement…`.

### 3.3 Chapter — `/chapitre/:id`

**Goal:** read the cours, or pick an exercise to solve.

**[observed]** 1 `<h1>`; both tab panels mounted with `hidden` toggling (the
recent fix — the PDF keeps page and zoom across tab flips, verified at page 6 /
94%). PDF frame renders 730px tall in a 935px viewport. 7 exercises matching the
API byte-for-byte.

**Problems:**
- **[observed] Every one of the 7 interactive elements is under 44px tall.**
  `.page-back` ("← Chapitres") is **17px** — the smallest hit target in the app.
- **[observed] The tab pattern is structurally incomplete.** `role="tablist"`
  and `role="tab"` are present, but **0 of 2** tabs have `aria-controls`, **0 of
  2** panels have `aria-labelledby`, and panels are not focusable. A screen
  reader cannot associate a tab with its panel.
- **[observed] No arrow-key navigation.** Dispatching `ArrowRight` on the
  focused tab does not move focus. WAI-ARIA's tabs pattern requires it.
- **[source]** No `<h2>` for the panels — the page is one `h1` and then content.
- **[source]** Tab state is component-local, so it is not in the URL: a student
  cannot link to the exercise list, and a reload always returns to Documentation.

### 3.4 Chat — `/chat`

**Goal:** ask, read the answer, trust it.

**[observed]** 31 interactive elements. 1 `<main>`, 2 `<nav>`, 2 `<header>`,
1 `<aside>`.

**Problems:**
- **[observed] Zero headings on the page.** `headings: []` once a conversation
  exists — the `.empty` `<h1>` disappears with the first message. There is no
  document structure for a screen reader to navigate.
- **[observed] `.messages` has no `aria-live`.** Answers stream in token by
  token and **none of it is announced.** For a product whose core interaction is
  a streaming answer, this is the most consequential accessibility gap found.
- **[observed] `.session-del` is 26×20px** and **deletes on a single click with
  no confirmation and no undo.** Nine sessions were present during the audit;
  each is one mis-click from gone. `localStorage` is the only copy.
- **[observed] Two stacked bars**, 92px of chrome before content: the appbar
  (51px) plus the chat's own `.topbar` carrying the burger and the scope label.
- **[observed] "Poser une question" fails contrast at 3.47:1** (`--accent` on
  `--side`), against a 4.5:1 requirement. It is a primary navigation control.
- **[source]** `Message.jsx:46` renders `status === "checking"` — a state
  nothing ever sets. Dead code.
- **[source]** The composer's "Envoyer" is `disabled` on empty input with no
  explanation of why.

---

## 4. Visual problems

1. **No elevation language at all.** Zero `box-shadow` in 1,060 lines. Every
   surface — card, sidebar, dropdown-less menu, composer — is separated only by
   a 1px border. Nothing can ever sit *above* anything else, which is why the
   sidebar drawer has to rely on a scrim to read as overlaid.
2. **11 border-radius values.** A card is 12px, another card 14px, a button 7px,
   a badge 999px, a tag 6px, a code panel 10px. No two components agree.
3. **23 font sizes** across a 1,060-line sheet — 0.7, 0.72, 0.74, 0.75, 0.78,
   0.8, 0.82, 0.83, 0.85, 0.88, 0.9, 0.95rem all exist. Several pairs differ by
   0.02rem, which is a third of a pixel: invisible, but each one is a decision
   someone has to make again next time.
4. **Home is mostly empty space** on a laptop screen, with no visual anchor.
5. **Glyph icons instead of an icon set** — `☰ × ✓ ⚠ ← →` render in the user's
   emoji font, so weight and baseline vary by platform and cannot be aligned
   with adjacent text.
6. **Two `<header>` elements per page**, visually stacked on `/chat`.

---

## 5. UX problems

1. **Destructive delete with no confirm and no undo** (P1 — see §10). The
   product's entire history lives in one `localStorage` key.
2. **No aria-live on a streaming surface** — also a UX problem, not only an
   accessibility one: there is no non-visual signal that generation finished.
3. **Loading states are text, not structure.** "Chargement…", "Chargement du
   cours…" — the layout jumps when content arrives instead of being reserved.
4. **Error states offer no recovery.** Every failure path renders a sentence
   ending in "Recharge la page pour réessayer" — asking the user to do manually
   what a Retry button would do.
5. **No success feedback anywhere except the checker badge.** Sign-in, logout,
   and session deletion all happen silently.
6. **Chapter tab state is not in the URL** — nothing on this screen is linkable.
7. **The free-question path is unexplained.** "Poser une question" sits in the
   nav with no indication that it is scoped to chapter 1 only.
8. **Session titles are truncated énoncés**, so a sidebar of nine sessions reads
   "Ecrire un programme qui…" five times over. There is no other way to tell
   them apart.

---

## 6. Responsive problems — **[derived], not observed**

The window would not resize; none of this was seen rendering. Treat as a
to-verify list.

**[source]** There are exactly two breakpoints, and they disagree:

```
@media (max-width: 760px)  → sidebar becomes a drawer, .msg full-width, tables 0.8rem
@media (max-width: 720px)  → .appbar-name hidden, .page padding reduced
```

1. **A 40px dead band (721–760px)** where the sidebar is already a drawer but
   the appbar still shows the full user name and the page keeps desktop padding.
   Nothing breaks; the two rules simply were not written together.
2. **The appbar has no narrow-viewport layout.** **[observed]** at desktop its
   three children measure 52 + 222 + 260 = **534px** of content. Below ~534px it
   must wrap or overflow, and the only mobile rule hides the name (~100px). At
   390px this is the most likely visible breakage.
3. **92px of stacked chrome** on `/chat` before any content, on the screens with
   the least vertical room.
4. **`.pdf-frame` is `min(78vh, 900px)`** — on a 844px phone that is ~658px of
   PDF in a viewport that already spent 92px on bars.
5. **`.exo` rows are `display: flex`** with a non-wrapping "Résoudre →". The
   énoncé column absorbs all compression; the longest exercise is ~290
   characters.
6. **Touch targets** — **[observed]** 22 of 31 elements on `/chat` and 7 of 7 on
   the chapter page are under 44px. This is a mobile problem measured on
   desktop; it does not improve on a phone.

---

## 7. Accessibility problems

Ordered by consequence. Two things commonly assumed broken are **not**, and are
recorded as such.

| # | Finding | Evidence |
|---|---|---|
| A1 | `.messages` has no `aria-live` — streamed answers are never announced | [observed] |
| A2 | `/chat` has **zero headings** once a conversation exists | [observed] |
| A3 | Tabs: 0/2 `aria-controls`, 0/2 `aria-labelledby`, panels not focusable | [observed] |
| A4 | Tabs: no arrow-key navigation (`ArrowRight` does not move focus) | [observed] |
| A5 | "Poser une question" at **3.47:1** — below AA for 13.6px text | [observed] |
| A6 | Touch targets 17–33px throughout; `.page-back` is 17px | [observed] |
| A7 | Destructive delete reachable by a 26×20px button, no confirmation | [observed] |
| A8 | Only **1 author focus rule in 170** — focus is undesigned | [observed] |

**Not problems, verified rather than assumed:**

- **Focus *is* visible.** Every interactive element matches `:focus-visible` and
  the browser's default `outline: auto` renders. A8 is a polish gap — the ring
  is the 1px UA default and matches nothing in the design — **not** an
  accessibility failure.
- **Contrast is largely fine.** 16 of 17 text nodes pass on Home; the only real
  failure is A5. The colour tokens were chosen carefully.
- **Every interactive element has an accessible name.** `interactiveWithoutName`
  returned empty on all three pages — the `aria-label`s on the burger, delete
  and composer are doing their job.
- **Console is clean** — no errors or warnings on load.

---

## 8. Component duplication

**[source]**

**Buttons — 5 independent implementations, no shared base:**
`.btn-new`, `.btn-send`, `.btn-stop`, `.btn-logout`, `.btn-burger`. Each
redeclares its own padding, radius, font-size and colour. There is no `.btn`.

**Badges — 2 systems, 5 variants, one concept:**
`.badge` + `.badge-pending/-ok/-warn` (radius 999px) and `.chapter-tag` +
`-on/-soon` (radius 6px). Same job — a small status pill — different radius,
padding and font-size.

**Surfaces — `border: 1px solid var(--line)` appears 12 times**, across
`.chapter-card`, `.exo`, `.signin-card`, `.composer-inner`, `.pdf-frame`,
`.ground-*`, `.tabs`, `.btn-logout`. No shared surface primitive; each redefines
radius and padding.

**Muted text — 5 idioms:** `.page-muted`, `.session-sub`, `.scope`,
`.composer-hint`, `.signin-lead`. All are "small, `--fg-dim`", at 0.72 / 0.75 /
0.8 / 0.85 / 0.9rem respectively.

**Error text — 3 implementations:** `.page-error`, `.signin-error`, and
`.error` in `Message.jsx`. Same red-on-`--err-bg` block, three sets of numbers.

**Loading — 2 implementations:** `.boot-dots` (spinner) and `.thinking` (three
pulsing dots), plus bare `Chargement…` strings in two routes.

---

## 9. Design-system inconsistencies

1. Two breakpoints 40px apart (§6.1).
2. Two `<header>` elements per page; two visible bars on `/chat`.
3. Radius: 6px tags, 7px buttons, 8px inputs, 10px code, 12px cards, 14px
   sign-in card.
4. Small text at 0.7, 0.72, 0.74, 0.75, 0.78, 0.8, 0.82, 0.83, 0.85rem.
5. `.account-avatar` is styled in the Phase-1 block but now only used by
   `AppLayout`; `.account-id`, `.account-name`, `.account-mail` are **dead CSS**
   left behind when the account block moved out of the sidebar.
6. Hover is defined on 12 selectors out of ~60 interactive rules — most
   controls have no hover response.
7. `.tabpanel` has a rule for `[hidden]` only; the class carries no styling and
   exists purely as a hook.

---

## 10. Priority matrix

**P0 — broken functionality: none found.** Every flow works, the console is
clean, and the recent review fixes hold. Recording that plainly rather than
inventing a P0.

### P1 — serious UX or accessibility problems

| | Item | Why it ranks here |
|---|---|---|
| P1-1 | Session delete: no confirm, no undo, 26×20px target | Only copy of the data; one mis-click is permanent |
| P1-2 | `.messages` has no `aria-live` | Core interaction is invisible to assistive tech |
| P1-3 | Appbar has no narrow layout (534px of content) | Likely visible breakage on a phone — **verify first** |
| P1-4 | Touch targets 17–33px | Whole product is hard to use on the device students have |
| P1-5 | `/chat` has zero headings | No document structure at all |
| P1-6 | "Poser une question" at 3.47:1 | AA failure on a primary control |
| P1-7 | Tabs: incomplete ARIA + no arrow keys | Announced as tabs, does not behave as tabs |

### P2 — design-system inconsistencies

P2-1 no spacing / radius / type scales · P2-2 five button implementations ·
P2-3 two badge systems · P2-4 three error implementations · P2-5 two stacked
bars on `/chat` · P2-6 undesigned focus ring · P2-7 no elevation language ·
P2-8 breakpoint dead band · P2-9 loading states are text, not structure ·
P2-10 errors offer no retry

### P3 — visual polish

P3-1 Home is empty on desktop · P3-2 glyph icons · P3-3 dead `.account-*` CSS ·
P3-4 `status === "checking"` dead code · P3-5 chapter tab not in URL ·
P3-6 session titles indistinguishable · P3-7 bundle 728KB / 229KB gzipped

---

## 11. Proposed design direction

**Keep the restraint. Add the system.**

The instinct already in this codebase — flat surfaces, hairline borders, one
accent, semantic colour tokens, no decoration — is the right one for a study
tool, and it is closer to Linear than most first drafts get. The gap is not
taste, it is **consistency**: the same good decision made 23 slightly different
ways.

So the direction is not a redesign. It is:

1. **Tokenise what is already there.** Collapse 11 radii to 4, 23 sizes to 7,
   ~25 paddings to an 8-step scale. Nothing should *look* very different on the
   first pass — that is the point.
2. **Introduce one elevation step.** Not shadows everywhere; one `--shadow-sm`
   so overlays and the composer can sit above the page.
3. **Design the states that were never designed** — focus, hover, disabled,
   loading — once, at the primitive level.
4. **Give the product a spine.** Right now it is a chat app with a chapter list
   bolted in front. The home page should answer "where was I, and what next?"
   using history the app already stores.

Explicitly rejected: gradients, decorative illustration, rounded-everything,
animation beyond 150ms functional transitions, and any redesign of the
`Algorithme | Python` rendering — that is the product working correctly.

---

## 12. Proposed design tokens

Additive to the existing colour block. No colour values change.

```css
:root {
  /* Spacing — 4px base */
  --space-1: 0.25rem;  --space-2: 0.5rem;   --space-3: 0.75rem;
  --space-4: 1rem;     --space-5: 1.5rem;   --space-6: 2rem;
  --space-7: 3rem;     --space-8: 4rem;

  /* Radius — 11 values collapse to 4 */
  --radius-sm: 6px;    /* badges, tags, small controls */
  --radius-md: 10px;   /* buttons, inputs, list rows   */
  --radius-lg: 14px;   /* cards, panels, dialogs       */
  --radius-full: 999px;

  /* Type — 23 sizes collapse to 7 */
  --text-xs: 0.75rem;  --text-sm: 0.8125rem; --text-base: 0.9375rem;
  --text-md: 1rem;     --text-lg: 1.125rem;  --text-xl: 1.375rem;
  --text-2xl: 1.75rem;
  --leading-tight: 1.3; --leading-normal: 1.55;
  --font-sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;

  /* Elevation — restrained on purpose */
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.06), 0 1px 3px rgb(0 0 0 / 0.08);
  --shadow-md: 0 4px 12px rgb(0 0 0 / 0.10);

  /* Motion */
  --ease: cubic-bezier(0.2, 0, 0.2, 1);
  --dur-fast: 120ms;  --dur-base: 180ms;

  /* Focus — the missing state */
  --focus-ring: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent);

  /* Layout */
  --bar-h: 48px;  --content-max: 62rem;  --sidebar-w: 264px;
}
```

Dark mode needs `--shadow-*` re-stated at higher opacity; shadows on a dark
ground read as noise at 6%.

**Two token decisions worth arguing about before adopting:**
- `--text-base: 0.9375rem` (15px) matches today's body size. Bumping to 16px
  would be more readable for teenagers on phones but reflows every screen.
- `--focus-ring` uses a double ring so it stays visible on both `--bg` and
  `--side`. A single ring is cheaper but disappears on the sidebar.

---

## 13. Proposed component improvements

Refactors of what exists. Nothing here is a rewrite.

| Component | Change | Solves |
|---|---|---|
| `Button` **(new)** | One primitive, variants `primary` / `secondary` / `ghost` / `danger`, sizes `sm` / `md`. The 5 `.btn-*` classes become variants | P2-2, P1-4, P2-6 |
| `Badge` **(new)** | One primitive, tones `neutral` / `success` / `warning` / `danger`. Absorbs `.badge-*` and `.chapter-tag-*` | P2-3 |
| `Surface` / `.card` **(new)** | One bordered-surface class with `--radius-lg` + `--space-4`. Replaces 12 ad-hoc declarations | P2-1, §8 |
| `Alert` **(new)** | One error/info block with an optional retry action. Absorbs the 3 error implementations | P2-4, P2-10 |
| `Skeleton` **(new)** | Reserve layout for chapter cards, exercise rows, PDF frame | P2-9 |
| `EmptyState` **(new)** | Icon + line + action. For zero chapters, zero exercises, failed loads | P2-10, P3-1 |
| `Tabs` (refactor) | Add `aria-controls` / `aria-labelledby` / roving tabindex + arrow keys; sync to `?tab=` | P1-7, P3-5 |
| `Sidebar` (refactor) | Delete confirmation (inline "Supprimer ?" swap, not a modal); enlarge target to 44px; drop dead `.account-*` CSS | P1-1, P1-4, P3-3 |
| `Chat` (refactor) | `aria-live="polite"` on `.messages`; visually-hidden `<h1>`; merge `.topbar` into the appbar | P1-2, P1-5, P2-5 |
| `AppLayout` (refactor) | Narrow-viewport layout: collapse account to avatar-only, then to an overflow menu | P1-3 |
| `Composer` (refactor) | Explain the disabled state; keep auto-resize as-is | §3.4 |
| `Message` (refactor) | Remove `status === "checking"` dead branch | P3-4 |

**Not touched:** `Markdown`, `AlgoCode`, `GroundingStrip`, `algoHighlighter`,
the grammar, `sessions.js`, and every `lib/*` API module. They work, and the
grammar in particular was expensive to get right.

---

## 14. Implementation roadmap

Each step is independently shippable and independently verifiable. **Verify
P1-3 first** — it is the one finding that is a prediction rather than a
measurement, and if the appbar does not actually break on a phone it drops to
P2, which changes the order below.

**Step 0 — confirm the responsive predictions** (no code)
Render at 390 / 744 / 1024px by hand. Confirm or discharge §6. Half an hour,
and it is the input to everything else.

**Step 1 — tokens, no visual change intended** (P2-1)
Add the §12 block. Replace raw values with tokens file by file. Screenshot every
page before and after; differences should be sub-pixel. This is the enabling
step — every later one is cheaper once it lands.

**Step 2 — the P1 accessibility set** (P1-2, P1-5, P1-6, P1-7)
`aria-live` on the message list, a visually-hidden `<h1>` on `/chat`, darken
`--accent` until the CTA clears 4.5:1, complete the tab ARIA and add arrow keys.
Verify with the same probe used for this audit.

**Step 3 — destructive actions and hit targets** (P1-1, P1-4)
Delete confirmation, 44px minimum on every control. Highest user-visible safety
gain of anything here.

**Step 4 — primitives** (P2-2, P2-3, P2-4, P2-6, P2-7)
`Button`, `Badge`, `Surface`, `Alert`, the focus ring, one elevation step.
Migrate call sites as each lands; no big-bang swap.

**Step 5 — responsive** (P1-3, P2-5, P2-8)
Single breakpoint set, appbar narrow layout, merge the two bars on `/chat`.
Gated on Step 0's findings.

**Step 6 — states and polish** (P2-9, P2-10, P3-*)
Skeletons, empty states, retry actions, icon set, Home that answers "where was
I". Everything here is optional and none of it blocks a release.

### Suggested sequencing

Steps 0 → 2 → 3 are the ones worth doing regardless: they are correctness and
safety, they are small, and none of them depends on the redesign. Step 1 before
Step 4, always — building primitives on untokenised values just moves the
inconsistency inside the components.

Steps 5 and 6 are where the product starts to *feel* like the reference
products named in the brief. They are also the ones I would happily defer if
launch timing matters, because a student with a 17px back-link and no undo is
hurt more by Steps 2–3 being skipped than by Home looking sparse.
