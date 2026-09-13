import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AuthDemo from "./AuthDemo.jsx";
import Badge from "./ui/Badge.jsx";
import { SCOPE_LABEL } from "../config.js";

/*
 * The public page: what Fahem is, for a student who has never heard of it and
 * has not been asked for an e-mail address yet.
 *
 * Everything stated here is checkable against the app, on purpose. There are
 * no testimonials, no student counts and no "utilisé par N lycées": the three
 * numbers in the strip are the chapter list in chapters.py, the exercises in
 * sample_problems.json and the corpus the retriever actually holds. A landing
 * page for 16-year-olds can be loud without being untrue, and an invented
 * figure is the one thing a student would be right to distrust.
 *
 * Visually it reuses the signed-out showcase treatment wholesale - the same
 * aurora, the same glass, the same gradient text, the same AuthDemo the
 * sign-in panel runs - so arriving on /connexion from here reads as a
 * continuation rather than a different product. See the landing section of
 * App.css; every loop and entrance there stops under prefers-reduced-motion.
 *
 * Two layers of motion. CSS carries what must play at once (the hero, the
 * syntax strip, the loops). Motion - springs, scroll-linked effects, counters,
 * cursor-following cards - lives in landingMotion.js, imported on demand so
 * it is a separate chunk only this page downloads. The markup here is always
 * the finished page; that module only ever animates *towards* it.
 */

/* Same idea as AuthShell's GLYPHS: the background is the syntax the course
   uses, not generic shapes. Fixed positions, spread wider because this page
   is several screens tall. */
const GLYPHS = [
  { t: "←", x: "5%", y: "8%", s: "5rem", d: "21s", b: "0px", o: 0.2 },
  { t: "Lire", x: "86%", y: "6%", s: "1.7rem", d: "24s", b: "1px", o: 0.16 },
  { t: "mod", x: "91%", y: "40%", s: "2.3rem", d: "22s", b: "0px", o: 0.16 },
  { t: "≠", x: "8%", y: "52%", s: "3.2rem", d: "26s", b: "2px", o: 0.13 },
  { t: "Ecrire", x: "74%", y: "72%", s: "1.5rem", d: "28s", b: "1px", o: 0.14 },
  { t: "div", x: "4%", y: "88%", s: "1.6rem", d: "23s", b: "3px", o: 0.12 },
  { t: "≤", x: "93%", y: "86%", s: "2.7rem", d: "25s", b: "2px", o: 0.13 },
  { t: "←", x: "52%", y: "34%", s: "2.1rem", d: "27s", b: "3px", o: 0.1 },
  { t: "Si", x: "36%", y: "94%", s: "1.9rem", d: "20s", b: "2px", o: 0.11 },
  { t: "*", x: "26%", y: "22%", s: "2.5rem", d: "29s", b: "4px", o: 0.1 },
];

/** The three honest numbers: each one is a fact in this repo, not a claim. */
const FACTS = [
  { n: "2", unit: "langages", label: "Algorithme et Python, côte à côte" },
  { n: "7", unit: "exercices", label: "de la série, corrigés à la demande" },
  { n: "117", unit: "extraits", label: "de ton cours, cités à l'appui" },
];

/* The syntax strip: chapter 1 notation beside its Python, which is the whole
   pitch in one line. Only what the available chapter covers - no Si or Pour
   while those chapters are "à venir". */
const SYNTAX = [
  ["x ← x + 1", "x = x + 1"],
  ["Lire (x)", "x = input()"],
  ['Ecrire ("Bonjour")', 'print("Bonjour")'],
  ["a mod b", "a % b"],
  ["a div b", "a // b"],
  ["carre ← x * x", "carre = x * x"],
  ["réel", "float"],
  ["entier", "int"],
  ["chaîne", "str"],
  ["booléen", "bool"],
];

const FEATURES = [
  {
    glyph: "←",
    title: "La syntaxe de ton cours",
    body: "Affectation avec ←, mod et div, Lire et Ecrire. Une réponse que tu peux recopier sur ta copie sans rien retraduire.",
  },
  {
    glyph: "⇄",
    title: "Algorithme, puis Python",
    body: "Les deux versions dans la même réponse, ligne pour ligne. Tu vois ce que devient chaque instruction.",
  },
  {
    glyph: "❝",
    title: "Chaque réponse est sourcée",
    body: "Fahem montre les passages du cours sur lesquels il s'appuie. Tu peux vérifier au lieu de croire.",
  },
  {
    glyph: "✓",
    title: "Une relecture avant la tienne",
    body: "Un vérificateur repasse sur la réponse et signale une syntaxe douteuse, plutôt que de te la laisser apprendre.",
  },
  {
    glyph: "☰",
    title: "Les exercices de la série",
    body: "Ouvre un exercice du chapitre : l'énoncé part tout seul, tu n'as rien à recopier.",
  },
  {
    glyph: "⊘",
    title: "Il reste dans le programme",
    body: "Une question hors chapitre ? Il le dit. Un tuteur qui refuse d'inventer vaut mieux qu'un qui invente bien.",
  },
];

const STEPS = [
  {
    title: "Choisis, ou colle",
    body: "Prends un exercice du chapitre, ou colle l'énoncé que ton prof a donné aujourd'hui.",
  },
  {
    title: "Lis la réponse",
    body: "Algorithme, Python, et les parties du cours utilisées — rien qui sorte de ton chapitre.",
  },
  {
    title: "Refais-le seul",
    body: "C'est le but : la réponse est détaillée pour que tu puisses la refermer et recommencer sans elle.",
  },
];

const VERSUS = {
  them: [
    "Écrit x = x + 1 là où ton cours écrit x ← x + 1",
    "Mélange les niveaux et sort du programme",
    "Invente une syntaxe qui ressemble à la bonne",
    "Aucune source : à toi de deviner si c'est juste",
  ],
  us: [
    "Écrit la syntaxe de ton chapitre, à la lettre",
    "Ne répond que sur ce que ton cours couvre",
    "Relit sa propre réponse et signale ce qui cloche",
    "Montre les extraits du cours qu'il a utilisés",
  ],
};

const FAQ = [
  {
    q: "C'est gratuit ?",
    a: "Oui. Une adresse e-mail et un mot de passe, ou ton compte Google, et tu peux poser ta première question. Aucune carte bancaire.",
  },
  {
    q: "Quels chapitres sont couverts ?",
    a: "Pour l'instant le chapitre 1 de 2ème : les structures de données et les structures simples. Les chapitres 2 et 3 sont annoncés comme « à venir » — Fahem préfère le dire plutôt que répondre à côté.",
  },
  {
    q: "Ce n'est pas de la triche ?",
    a: "Fahem fait ce qu'un bon corrigé fait : il montre la démarche, pas seulement le résultat. Ton prof, lui, te demandera de refaire l'exercice seul le jour du devoir — c'est pour ça que chaque réponse est expliquée et sourcée.",
  },
  {
    q: "En quoi c'est différent d'une IA classique ?",
    a: "Un modèle généraliste a appris la syntaxe d'internet. Fahem ne répond qu'avec ton cours sous les yeux, dans la notation de ton manuel, et il indique d'où vient chaque élément de sa réponse.",
  },
  {
    q: "Ça marche sur téléphone ?",
    a: "Oui, dans le navigateur, sans rien installer. Il n'y a pas d'application à télécharger.",
  },
];

/** The hero demo tilts toward the cursor, exactly as the sign-in panel's copy
 *  of it does - .auth-sample reads --tilt-x/--tilt-y, wherever they are set. */
function handleDemoPointer(event) {
  if (event.pointerType !== "mouse") return;
  const box = event.currentTarget;
  const r = box.getBoundingClientRect();
  // -1..1 across the window, clamped so the tilt eases off at the edges.
  const nx = Math.max(-1, Math.min(1, ((event.clientX - r.left) / r.width) * 2 - 1));
  const ny = Math.max(-1, Math.min(1, ((event.clientY - r.top) / r.height) * 2 - 1));
  box.style.setProperty("--tilt-x", `${(-ny * 4).toFixed(2)}deg`);
  box.style.setProperty("--tilt-y", `${(nx * 5).toFixed(2)}deg`);
}

/** Pointer-following highlight on a card, written straight to CSS custom
 *  properties - the same trick AuthShell uses, for the same reason: this fires
 *  on every mouse move, and re-rendering a section for a glow is wasteful. */
function handleCardPointer(event) {
  if (event.pointerType !== "mouse") return;
  const card = event.currentTarget;
  const box = card.getBoundingClientRect();
  card.style.setProperty("--mx", `${event.clientX - box.left}px`);
  card.style.setProperty("--my", `${event.clientY - box.top}px`);
}

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** A heading's words as separate boxes, so CSS can bring them in one after
 *  another. The spaces stay outside the inline-blocks, or lines could not
 *  break between words. */
function Words({ text }) {
  return text.split(" ").flatMap((word, i) => [
    i > 0 ? " " : null,
    <span className="lp-word" key={i} style={{ "--w": i }}>
      {word}
    </span>,
  ]);
}

/*
 * The notation correction, as a small card: the line a generic model writes,
 * struck out, over the line the course writes - Fahem's whole argument in
 * eight characters. The resting markup is the finished correction;
 * landingMotion.js replays the strike and the arrow when it scrolls in.
 */
function SyntaxFix({ className = "" }) {
  return (
    <figure
      className={`lp-fix ${className}`}
      role="img"
      aria-label="Correction : x = x + 1, la notation d'une IA généraliste, devient x ← x + 1, la notation de ton cours."
    >
      <div className="lp-fix-line lp-fix-wrong" aria-hidden="true">
        <span className="lp-fix-icon">✕</span>
        <code className="lp-fix-code">
          x = x + 1
          <span className="lp-fix-strike" />
        </code>
        <span className="lp-fix-tag">IA généraliste</span>
      </div>
      <div className="lp-fix-line lp-fix-right" aria-hidden="true">
        <span className="lp-fix-icon lp-fix-check">✓</span>
        <code className="lp-fix-code">
          x <span className="lp-fix-arrow">←</span> x + 1
        </code>
        <span className="lp-fix-tag">ton cours</span>
      </div>
    </figure>
  );
}

export default function Landing() {
  const pageRef = useRef(null);
  // The bar is transparent over the hero and becomes a solid strip once the
  // page has moved, so the headline is not sitting behind a band.
  const [scrolled, setScrolled] = useState(false);

  // Motion is loaded here rather than imported at the top: a static import
  // would put it in the main bundle the student app and the console share.
  // Reduced motion never downloads it, and if the import fails the page is
  // simply static - nothing waits on it to become visible.
  useEffect(() => {
    const root = pageRef.current;
    if (!root || prefersReducedMotion()) return undefined;
    let cleanup;
    let cancelled = false;
    import("./landingMotion.js")
      .then(({ enhanceLanding }) => {
        if (!cancelled) cleanup = enhanceLanding(root);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="landing" ref={pageRef}>
      <div className="aurora" aria-hidden="true">
        <span className="aurora-blob aurora-blob-1" />
        <span className="aurora-blob aurora-blob-2" />
        <span className="aurora-blob aurora-blob-3" />
        <span className="aurora-grid" />
        <div className="aurora-glyphs">
          {GLYPHS.map((g, i) => (
            <span
              key={i}
              style={{
                "--x": g.x,
                "--y": g.y,
                "--s": g.s,
                "--d": g.d,
                "--b": g.b,
                "--o": g.o,
                "--delay": `${-i * 1.7}s`,
              }}
            >
              {g.t}
            </span>
          ))}
        </div>
      </div>

      <header className="lp-bar" data-scrolled={scrolled ? "" : undefined}>
        <div className="lp-bar-inner">
          <a className="lp-brand" href="#top">
            <span className="auth-mark" aria-hidden="true">
              <span className="auth-mark-arrow">←</span>
            </span>
            Fahem
          </a>

          <nav className="lp-nav" aria-label="Sections de la page">
            {/* Slides under the current section's link (landingMotion.js). */}
            <span className="lp-nav-pill" aria-hidden="true" />
            <a href="#fonctionnalites">Ce que ça fait</a>
            <a href="#etapes">Comment ça marche</a>
            <a href="#programme">Programme</a>
            <a href="#questions">Questions</a>
          </nav>

          <div className="lp-bar-actions">
            <Link className="lp-textlink" to="/connexion">
              Se connecter
            </Link>
            {/* A Link with the button classes, not a <Button> inside a Link:
                a button nested in an anchor is invalid, and this is a
                navigation, not an action. */}
            <Link
              className="btn btn-primary btn-sm lp-btn"
              to="/connexion"
              state={{ authMode: "signup" }}
            >
              Créer un compte
            </Link>
          </div>
        </div>
        {/* Reading progress, bound to scroll by landingMotion.js. */}
        <span className="lp-progress" aria-hidden="true" />
      </header>

      <main id="top">
        {/* --- hero ------------------------------------------------------- */}
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <Badge className="lp-eyebrow">{SCOPE_LABEL}</Badge>

            {/* Word by word: the plain words rise, then the gradient phrase
                fades in as one inline run - split into boxes it could not wrap
                on a phone, and each box would restart the gradient. */}
            <h1 className="lp-title">
              <Words text="L'algorithmique, corrigée" />{" "}
              <span className="auth-gradient-text lp-title-accent">
                dans la syntaxe de ton cours.
              </span>
              <span className="type-caret lp-title-caret" aria-hidden="true" />
            </h1>

            <p className="lp-lead">
              Colle l'énoncé d'un exercice. Fahem le résout en Algorithme et en Python —
              avec <code>←</code>, <code>Lire</code>, <code>Ecrire</code> et{" "}
              <code>mod</code> comme ton manuel — et te montre les parties du cours sur
              lesquelles il s'appuie.
            </p>

            <div className="lp-cta-row">
              <Link
                className="btn btn-primary btn-md lp-btn lp-btn-lg"
                to="/connexion"
                state={{ authMode: "signup" }}
              >
                Commencer — c'est gratuit
              </Link>
              <Link className="lp-textlink lp-textlink-strong" to="/connexion">
                J'ai déjà un compte →
              </Link>
            </div>

            <p className="lp-fineprint">
              Pas de carte bancaire, rien à installer. Une adresse e-mail suffit.
            </p>
          </div>

          {/* A wrapper for the scroll parallax, so it never competes with the
              demo window's own CSS entrance over `transform`. */}
          <div className="lp-hero-visual">
            {/* The same demo the sign-in panel runs: the product, typing. */}
            <div
              className="lp-hero-demo"
              onPointerMove={handleDemoPointer}
              onPointerLeave={(event) => {
                event.currentTarget.style.setProperty("--tilt-x", "0deg");
                event.currentTarget.style.setProperty("--tilt-y", "0deg");
              }}
            >
              <AuthDemo paused={false} />
            </div>
            {/* Phones do not get the demo (its code columns are unreadable
                there), so the hero shows the one-line version of the pitch. */}
            <SyntaxFix className="lp-hero-fix" />
          </div>
        </section>

        {/* --- syntax strip ----------------------------------------------- */}
        {/* Decorative: every pair is also said in words on the page. Listed
            twice so the loop wraps without a seam. */}
        <div className="lp-marquee" aria-hidden="true">
          <div className="lp-marquee-track">
            {[...SYNTAX, ...SYNTAX].map(([algo, py], i) => (
              <span className="lp-marquee-item" key={i}>
                <code className="lp-marquee-algo">{algo}</code>
                <span className="lp-marquee-sep">⇄</span>
                <code className="lp-marquee-py">{py}</code>
              </span>
            ))}
          </div>
        </div>

        {/* --- the three numbers ------------------------------------------ */}
        <section className="lp-facts" aria-label="Fahem en trois chiffres">
          {FACTS.map((f, i) => (
            <div className="lp-fact" key={f.unit} data-reveal="" style={{ "--i": i }}>
              {/* Counts up on arrival; the moving digits are hidden from
                  screen readers, the real number beside them is not. */}
              <span className="lp-fact-n" aria-hidden="true" data-count={f.n}>
                {f.n}
              </span>
              <span className="sr-only">{f.n}</span>
              <span className="lp-fact-unit">{f.unit}</span>
              <span className="lp-fact-label">{f.label}</span>
            </div>
          ))}
        </section>

        {/* --- features --------------------------------------------------- */}
        <section className="lp-section" id="fonctionnalites">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Ce que ça fait</p>
            <h2 className="lp-h2">
              Un tuteur qui a lu <span className="auth-gradient-text">ton</span> cours.
            </h2>
            <p className="lp-section-lead">
              Pas le programme d'un autre pays, ni la syntaxe d'un forum : le chapitre
              que tu as en classe cette semaine.
            </p>
          </header>

          <div className="lp-grid">
            {FEATURES.map((f, i) => (
              <article
                className="lp-card"
                key={f.title}
                data-reveal=""
                style={{ "--i": i }}
                onPointerMove={handleCardPointer}
              >
                <span className="lp-card-glyph" aria-hidden="true">
                  {f.glyph}
                </span>
                <h3 className="lp-card-title">{f.title}</h3>
                <p className="lp-card-body">{f.body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* --- how it works ----------------------------------------------- */}
        <section className="lp-section" id="etapes">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Comment ça marche</p>
            <h2 className="lp-h2">Trois minutes, trois étapes.</h2>
          </header>

          <div className="lp-steps-wrap">
            {/* Fills with scroll between the numbers (landingMotion.js). */}
            <span className="lp-steps-track" aria-hidden="true">
              <span className="lp-steps-fill" />
            </span>
            <ol className="lp-steps">
              {STEPS.map((s, i) => (
                <li
                  className="lp-step"
                  key={s.title}
                  data-reveal=""
                  style={{ "--i": i }}
                >
                  <span className="lp-step-n" aria-hidden="true">
                    {i + 1}
                  </span>
                  <h3 className="lp-step-title">{s.title}</h3>
                  <p className="lp-step-body">{s.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* --- versus a generic chatbot ----------------------------------- */}
        <section className="lp-section lp-section-narrow">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">La différence</p>
            <h2 className="lp-h2">
              Pourquoi pas{" "}
              <span className="auth-gradient-text">n'importe quelle IA</span> ?
            </h2>
            <p className="lp-section-lead">
              Une réponse juste dans la mauvaise notation reste fausse sur une copie.
            </p>
          </header>

          <div className="lp-fix-row" data-reveal="">
            <SyntaxFix />
          </div>

          <div className="lp-versus">
            <div className="lp-versus-col lp-versus-them" data-reveal="">
              <h3 className="lp-versus-title">Une IA généraliste</h3>
              <ul>
                {VERSUS.them.map((line) => (
                  <li key={line}>
                    <span className="lp-versus-icon" aria-hidden="true">
                      ✕
                    </span>
                    {line}
                  </li>
                ))}
              </ul>
            </div>

            <div
              className="lp-versus-col lp-versus-us"
              data-reveal=""
              style={{ "--i": 1 }}
            >
              <h3 className="lp-versus-title">
                Fahem <Badge tone="success">ton chapitre</Badge>
              </h3>
              <ul>
                {VERSUS.us.map((line) => (
                  <li key={line}>
                    <span className="lp-versus-icon" aria-hidden="true">
                      ✓
                    </span>
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* --- programme -------------------------------------------------- */}
        <section className="lp-section" id="programme">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Programme</p>
            <h2 className="lp-h2">Ce qui est prêt, et ce qui arrive.</h2>
            <p className="lp-section-lead">
              La liste est courte parce qu'elle est vraie : un chapitre entièrement
              couvert vaut mieux que trois à moitié.
            </p>
          </header>

          <div className="lp-chapters">
            <article className="lp-chapter is-ready" data-reveal="">
              <div className="lp-chapter-top">
                <span className="lp-chapter-n">2ème · Chapitre 1</span>
                <Badge tone="success">Disponible</Badge>
              </div>
              <h3 className="lp-chapter-title">
                Les structures de données et les structures simples
              </h3>
              <p className="lp-chapter-body">
                Types et constantes, affectation, entrée / sortie, opérateurs
                arithmétiques — <code>mod</code>, <code>div</code> — et les structures
                simples du chapitre. Le cours en PDF, la série d'exercices, et un
                corrigé quand tu le demandes.
              </p>
            </article>

            <article className="lp-chapter" data-reveal="" style={{ "--i": 1 }}>
              <div className="lp-chapter-top">
                <span className="lp-chapter-n">2ème · Chapitre 2</span>
                <Badge>À venir</Badge>
              </div>
              <h3 className="lp-chapter-title">
                Les structures de contrôle conditionnelles
              </h3>
              <p className="lp-chapter-body">
                <code>Si … Alors … Sinon</code>, les conditions composées, le choix
                multiple.
              </p>
            </article>

            <article className="lp-chapter" data-reveal="" style={{ "--i": 2 }}>
              <div className="lp-chapter-top">
                <span className="lp-chapter-n">2ème · Chapitre 3</span>
                <Badge>À venir</Badge>
              </div>
              <h3 className="lp-chapter-title">
                Les structures de contrôle itératives
              </h3>
              <p className="lp-chapter-body">
                <code>Pour</code>, <code>Tant que</code>, <code>Répéter</code>, et le
                parcours d'un tableau.
              </p>
            </article>
          </div>
        </section>

        {/* --- FAQ -------------------------------------------------------- */}
        <section className="lp-section lp-section-narrow" id="questions">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Questions</p>
            <h2 className="lp-h2">Ce que les élèves demandent.</h2>
          </header>

          <div className="lp-faq">
            {FAQ.map((item, i) => (
              <details
                className="lp-faq-item"
                key={item.q}
                data-reveal=""
                style={{ "--i": i }}
              >
                <summary>
                  {item.q}
                  <span className="lp-faq-sign" aria-hidden="true" />
                </summary>
                <p>{item.a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* --- closing CTA ------------------------------------------------ */}
        <section className="lp-final" data-reveal="">
          <h2 className="lp-final-title">
            Ton prochain exercice, <span className="auth-gradient-text">compris</span>.
          </h2>
          <p className="lp-final-lead">
            Crée ton compte et pose la question que tu gardes depuis ce matin.
          </p>
          <div className="lp-cta-row lp-cta-center">
            <Link
              className="btn btn-primary btn-md lp-btn lp-btn-lg"
              to="/connexion"
              state={{ authMode: "signup" }}
            >
              Créer mon compte
            </Link>
            <Link className="lp-textlink lp-textlink-strong" to="/connexion">
              Se connecter →
            </Link>
          </div>
        </section>
      </main>

      <footer className="lp-foot">
        <p className="lp-foot-brand">
          <span className="auth-mark" aria-hidden="true">
            <span>←</span>
          </span>
          Fahem
        </p>
        <p className="lp-foot-scope">{SCOPE_LABEL}</p>
        <nav className="lp-foot-nav" aria-label="Pied de page">
          <a href="#fonctionnalites">Ce que ça fait</a>
          <a href="#programme">Programme</a>
          <a href="#questions">Questions</a>
          <Link to="/connexion">Se connecter</Link>
        </nav>
      </footer>
    </div>
  );
}
