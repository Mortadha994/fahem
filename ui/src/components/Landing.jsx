import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AuthDemo from "./AuthDemo.jsx";
import LandingDemo from "./LandingDemo.jsx";
import Badge from "./ui/Badge.jsx";
import ThemeToggle from "./ThemeToggle.jsx";
import { fetchOverview, listFr, plural } from "../lib/overview.js";

/*
 * The public page: what Fahem is, for a student who has never heard of it and
 * has not been asked for an e-mail address yet.
 *
 * Everything stated here is checkable against the app, on purpose. There are
 * no testimonials, no student counts and no "utilisé par N lycées".
 *
 * And it follows the app by itself: the numbers, the programme, the scope
 * label, the chapter FAQ, the syntax strip's extra pairs and the photo claims
 * all come from GET /public/overview (public_overview.py), which counts the
 * published chapters, their exercises and the extracts the retriever holds.
 * Publish a chapter or add exercises in the console and this page says so
 * within a minute - no edit here. Only a brand-new *kind* of feature needs a
 * card added to FEATURES below. If the overview cannot be fetched, the page
 * still renders, without the figures it could not check.
 *
 * A landing page for 16-year-olds can be loud without being untrue, and an
 * invented figure is the one thing a student would be right to distrust.
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

/** The honest numbers, counted by the backend (public_overview.py). Without
 *  the overview only the one that needs no counting is shown. */
function factsFrom(overview) {
  const facts = [
    { n: "4", unit: "étapes", label: "pour comprendre, avant la solution" },
  ];
  if (!overview) return facts;
  const { exercises, chapters_available: ready } = overview.totals;
  facts.push({
    n: String(exercises),
    unit: exercises === 1 ? "exercice corrigé" : "exercices corrigés",
    label: `de ${plural(ready, "chapitre")}, prêts à essayer`,
  });
  facts.push({ n: "0", unit: "dinar", label: "gratuit pour les élèves" });
  return facts;
}

const shortNiveau = (label) => label.replace(/ année$/, "");
const lowerFirst = (text) => text.charAt(0).toLowerCase() + text.slice(1);
const isReady = (chapter) => chapter.status === "active";

/** "2ème — 2 chapitres disponibles": the hero badge and the footer. */
function scopeLabel(overview) {
  if (!overview) return "Algorithmique — lycée";
  const n = overview.totals.chapters_available;
  const years = overview.totals.niveaux.map(shortNiveau).join(" · ") || "Lycée";
  return `${years} — ${plural(n, "chapitre")} disponible${n > 1 ? "s" : ""}`;
}

/** The FAQ's "which chapters" answer, written from the live list. */
function chaptersAnswer(overview) {
  if (!overview)
    return "La section Programme, plus haut, liste les chapitres disponibles.";
  const name = (c) =>
    `le chapitre ${c.id} de ${shortNiveau(c.niveau_label)} (${lowerFirst(c.title)})`;
  const ready = overview.chapters.filter(isReady);
  const coming = overview.chapters.filter((c) => !isReady(c));
  let answer = ready.length
    ? `Aujourd'hui : ${listFr(ready.map(name))}, avec ${plural(overview.totals.exercises, "exercice")} à résoudre.`
    : "Aucun chapitre n'est encore publié.";
  if (coming.length) {
    answer += ` ${listFr(coming.map((c, i) => `${i === 0 ? "Le" : "le"} chapitre ${c.id}`))} ${
      coming.length > 1 ? "sont annoncés" : "est annoncé"
    } « à venir » — Fahem préfère le dire plutôt que répondre à côté.`;
  }
  return answer;
}

/* The syntax strip: course notation beside its Python, which is the whole
   pitch in one line. Chapter 1's pairs always; a later chapter's pairs join
   only once that chapter is published - no Si or Pour while "à venir". */
const CHAPTER_SYNTAX = {
  2: [
    ["Si x > 0 Alors", "if x > 0 :"],
    ["Sinon", "else :"],
    ["a ET b", "a and b"],
    ["a OU b", "a or b"],
    ["a ≠ b", "a != b"],
    ["Selon mois", "match mois :"],
  ],
  3: [
    ["Pour i de 1 à n Faire", "for i in range(1, n + 1) :"],
    ["Tant que x > 0 Faire", "while x > 0 :"],
  ],
};

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

/* The phone menu lists every section, including the interactive one the
   desktop bar leaves out for width. */
const MENU = [
  { href: "#essayer", label: "Essayer sans compte" },
  { href: "#fonctionnalites", label: "Ce que ça fait" },
  { href: "#etapes", label: "Comment ça marche" },
  { href: "#programme", label: "Programme" },
  { href: "#questions", label: "Questions" },
  { href: "#parents", label: "Parents et profs" },
];

const FEATURES = [
  {
    glyph: "🧭",
    title: "Il t'aide avant de te donner la réponse",
    body: "Mode guidé : d'abord comprendre l'énoncé, puis un indice, puis un squelette à compléter. La solution, seulement quand tu la demandes.",
  },
  {
    glyph: "✓",
    title: "Tu écris, il corrige",
    body: "Colle ta propre solution : il te dit ce qui est juste, ce qui est faux et pourquoi — ligne par ligne, comme un prof qui relit ta copie.",
  },
  {
    glyph: "←",
    title: "La syntaxe de ton cours",
    body: "← pour affecter, div et mod, Lire et Ecrire. Tu recopies sur ta copie sans rien retraduire.",
  },
  {
    glyph: "▶",
    title: "Tu peux lancer le programme",
    body: "Le Python de la solution tourne dans ton navigateur : donne tes valeurs, vois le résultat, comprends ce que fait chaque ligne.",
  },
  {
    glyph: "🎲",
    title: "Un exercice de plus, à ta demande",
    body: "Tu as compris celui-là ? Il t'en écrit un autre, plus facile ou plus dur, sur la même leçon.",
  },
  {
    glyph: "📸",
    title: "Une photo suffit",
    body: "Photo de ton cahier, capture d'écran ou PDF : il lit l'énoncé et le résout comme si tu l'avais tapé.",
    // Shown only while the backend has a vision model (public_overview.py).
    requires: "photo_attachments",
  },
  {
    glyph: "📈",
    title: "Tu vois où tu en es",
    body: "Chaque exercice réussi tout seul est compté. Tu sais ce qu'il te reste à faire avant le devoir.",
  },
];

const STEPS = [
  {
    title: "Envoie ton exercice",
    body: "Colle l'énoncé, prends-le en photo, ou choisis-en un dans la série de ton chapitre.",
  },
  {
    title: "Choisis : guidé ou direct",
    body: "Un indice pour chercher toi-même, ou la solution complète tout de suite. C'est toi qui décides.",
  },
  {
    title: "Vérifie ta réponse",
    body: "Écris ta solution, Fahem la corrige. Réussi tout seul = un exercice de plus dans ta progression.",
  },
];

const VERSUS = {
  them: [
    "Écrit x = x + 1 là où ton cours écrit x ← x + 1",
    "Utilise des boucles et des fonctions pas encore vues en classe",
    "Te donne la réponse, jamais l'envie de chercher",
    "Tu ne sais pas si c'est juste pour ton programme",
  ],
  us: [
    "Écrit la syntaxe de ton chapitre, à la lettre",
    "Ne sort jamais de ce que tu as vu en cours",
    "Te guide d'abord, et corrige ce que tu écris",
    "Te montre le passage du cours qu'il a utilisé",
  ],
};

/** The FAQ, with the answers that depend on what is published built from the
 *  overview. */
const faqFrom = (overview) => [
  {
    q: "C'est gratuit ?",
    a: "Oui. Une adresse e-mail et un mot de passe, ou ton compte Google, et tu peux poser ta première question. Aucune carte bancaire.",
  },
  {
    q: "Quels chapitres sont couverts ?",
    a: chaptersAnswer(overview),
  },
  ...(overview?.features.photo_attachments
    ? [
        {
          q: "Je peux envoyer une photo de mon exercice ?",
          a: "Oui : une photo, une capture d'écran ou un PDF. Fahem recopie l'énoncé, puis le résout comme un message tapé.",
        },
      ]
    : []),
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
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef(null);
  // What is published right now (null until known, or if it cannot be read).
  const [overview, setOverview] = useState(null);
  const [settled, setSettled] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchOverview().then((data) => {
      if (cancelled) return;
      setOverview(data);
      setSettled(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Motion is loaded here rather than imported at the top: a static import
  // would put it in the main bundle the student app and the console share.
  // Reduced motion never downloads it, and if the import fails the page is
  // simply static - nothing waits on it to become visible.
  //
  // It starts once the overview has settled (fetchOverview gives up after
  // 2.5s): landingMotion reads the page once - which elements to reveal, what
  // each counter counts to - so it must see the real chapters and numbers.
  useEffect(() => {
    const root = pageRef.current;
    if (!settled || !root || prefersReducedMotion()) return undefined;
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
  }, [settled]);

  const facts = factsFrom(overview);
  const scope = scopeLabel(overview);
  const faq = faqFrom(overview);
  const features = FEATURES.filter(
    (f) => !f.requires || overview?.features[f.requires]
  );
  const programme = overview?.chapters ?? [];
  const readyCount = programme.filter(isReady).length;
  const comingCount = programme.length - readyCount;
  const syntax = [
    ...SYNTAX,
    ...programme.filter(isReady).flatMap((c) => CHAPTER_SYNTAX[c.id] ?? []),
  ];

  // The phone menu closes on Escape (focus goes back to its button, where the
  // student was) and whenever the window grows past the breakpoint that hides
  // its button - otherwise it could stay open with no way to close it.
  useEffect(() => {
    if (!menuOpen) return undefined;
    const onKey = (event) => {
      if (event.key !== "Escape") return;
      setMenuOpen(false);
      menuButtonRef.current?.focus();
    };
    const wide = window.matchMedia("(min-width: 981px)");
    const onWide = () => wide.matches && setMenuOpen(false);
    document.addEventListener("keydown", onKey);
    wide.addEventListener("change", onWide);
    return () => {
      document.removeEventListener("keydown", onKey);
      wide.removeEventListener("change", onWide);
    };
  }, [menuOpen]);

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
            <ThemeToggle className="lp-theme" />
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
            {/* Only below 980px, where the section links above are hidden. */}
            <button
              ref={menuButtonRef}
              type="button"
              className="lp-menu-btn"
              aria-expanded={menuOpen}
              aria-controls="lp-menu"
              aria-label={menuOpen ? "Fermer le menu" : "Ouvrir le menu"}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="lp-menu-icon" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* The phone menu. Always in the DOM so it can animate open and shut;
            `inert` while closed keeps its links out of the tab order and away
            from screen readers. */}
        <nav
          id="lp-menu"
          className="lp-menu"
          aria-label="Menu"
          data-open={menuOpen ? "" : undefined}
          inert={!menuOpen}
        >
          <div className="lp-menu-inner">
            {MENU.map((item, i) => (
              <a
                key={item.href}
                href={item.href}
                style={{ "--i": i }}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
                <span aria-hidden="true">→</span>
              </a>
            ))}
            <Link
              className="lp-menu-signin"
              to="/connexion"
              style={{ "--i": MENU.length }}
            >
              Se connecter
            </Link>
          </div>
        </nav>
        {/* Reading progress, bound to scroll by landingMotion.js. */}
        <span className="lp-progress" aria-hidden="true" />
      </header>

      <main id="top">
        {/* --- hero ------------------------------------------------------- */}
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <Badge className="lp-eyebrow">{scope}</Badge>

            {/* Word by word: the plain words rise, then the gradient phrase
                fades in as one inline run - split into boxes it could not wrap
                on a phone, and each box would restart the gradient. */}
            <h1 className="lp-title">
              <Words text="Bloqué sur un exercice" />{" "}
              <span className="auth-gradient-text lp-title-accent">
                d'algorithmique ?
              </span>
              <span className="type-caret lp-title-caret" aria-hidden="true" />
            </h1>

            <p className="lp-lead">
              Fahem t'explique, te guide et corrige ce que <strong>tu</strong> écris —
              avec <code>←</code>, <code>div</code>, <code>Lire</code> et{" "}
              <code>Ecrire</code>, exactement comme ton prof les attend sur ta copie.
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
              Gratuit, rien à installer. Et tu peux{" "}
              <a className="lp-textlink" href="#essayer">
                essayer sans compte
              </a>{" "}
              juste en dessous.
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
            {[...syntax, ...syntax].map(([algo, py], i) => (
              <span className="lp-marquee-item" key={i}>
                <code className="lp-marquee-algo">{algo}</code>
                <span className="lp-marquee-sep">⇄</span>
                <code className="lp-marquee-py">{py}</code>
              </span>
            ))}
          </div>
        </div>

        {/* --- the three numbers ------------------------------------------ */}
        <section className="lp-facts" aria-label="Fahem en chiffres">
          {facts.map((f, i) => (
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

        {/* --- try it, no account ----------------------------------------- */}
        <section className="lp-section lp-try" id="essayer">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Essaie tout de suite</p>
            <h2 className="lp-h2">
              Un exercice, <span className="auth-gradient-text">trois façons</span> de
              s'en sortir.
            </h2>
            <p className="lp-section-lead">
              Choisis un exercice et regarde : la solution complète, le mode guidé, ou
              la correction de ta propre réponse. Sans compte, sans rien installer.
            </p>
          </header>
          <div data-reveal="">
            <LandingDemo />
          </div>
        </section>

        {/* --- features --------------------------------------------------- */}
        <section className="lp-section" id="fonctionnalites">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Ce que tu peux faire</p>
            <h2 className="lp-h2">
              Plus qu'une réponse :{" "}
              <span className="auth-gradient-text">apprendre</span> à la trouver.
            </h2>
            <p className="lp-section-lead">
              Fahem connaît le chapitre que tu as en classe cette semaine — pas le
              programme d'un autre pays, ni la syntaxe d'un forum.
            </p>
          </header>

          <div className="lp-grid">
            {features.map((f, i) => (
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
              {overview
                ? `${plural(readyCount, "chapitre")} prêt${readyCount > 1 ? "s" : ""}${
                    comingCount ? `, ${comingCount} à venir` : ""
                  }. La liste est courte parce qu'elle est vraie : elle se met à jour dès qu'un chapitre est publié.`
                : "La liste est courte parce qu'elle est vraie : un chapitre entièrement couvert vaut mieux que trois à moitié."}
            </p>
          </header>

          {/* One card per chapter in the catalogue, published or announced,
              straight from /public/overview. */}
          <div className="lp-chapters">
            {programme.map((c, i) => (
              <article
                className={`lp-chapter${isReady(c) ? " is-ready" : ""}`}
                key={`${c.niveau}-${c.id}`}
                data-reveal=""
                style={{ "--i": i }}
              >
                <div className="lp-chapter-top">
                  <span className="lp-chapter-n">
                    {shortNiveau(c.niveau_label)} · Chapitre {c.id}
                  </span>
                  {isReady(c) ? (
                    <Badge tone="success">Disponible</Badge>
                  ) : (
                    <Badge>À venir</Badge>
                  )}
                </div>
                <h3 className="lp-chapter-title">{c.title}</h3>
                {c.topics.length > 0 && (
                  <p className="lp-chapter-body">{c.topics.join(" · ")}</p>
                )}
                {isReady(c) && (
                  <p className="lp-chapter-meta">
                    {c.exercises > 0
                      ? `${plural(c.exercises, "exercice")} corrigé${c.exercises > 1 ? "s" : ""} à la demande`
                      : "Pose tes propres exercices"}
                    {c.excerpts ? ` · ${c.excerpts} extraits du cours` : ""}
                  </p>
                )}
              </article>
            ))}
            {settled && !overview && (
              <p className="lp-chapter-body">
                Le programme n'a pas pu être chargé. Connecte-toi pour voir les
                chapitres de ton année.
              </p>
            )}
          </div>
        </section>

        {/* --- FAQ -------------------------------------------------------- */}
        <section className="lp-section lp-section-narrow" id="questions">
          <header className="lp-section-head" data-reveal="">
            <p className="lp-kicker">Questions</p>
            <h2 className="lp-h2">Ce que les élèves demandent.</h2>
          </header>

          <div className="lp-faq">
            {faq.map((item, i) => (
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

        {/* --- parents and teachers --------------------------------------- */}
        <section className="lp-section lp-section-narrow" id="parents">
          <div className="lp-parents" data-reveal="">
            <h2 className="lp-parents-title">Tu es parent ou professeur ?</h2>
            <ul className="lp-parents-list">
              <li>
                <b>Gratuit</b>, sans publicité et sans carte bancaire.
              </li>
              <li>
                <b>Le programme tunisien</b> : Fahem répond avec la notation du manuel
                et refuse ce que le chapitre n'a pas encore couvert.
              </li>
              <li>
                <b>Il fait chercher l'élève</b> : mode guidé par indices, et correction
                de ce que l'élève a écrit lui-même.
              </li>
              <li>
                <b>Chaque réponse est sourcée</b> : l'élève voit les passages du cours
                utilisés et peut vérifier.
              </li>
            </ul>
          </div>
        </section>

        {/* --- closing CTA ------------------------------------------------ */}
        <section className="lp-final" data-reveal="">
          <h2 className="lp-final-title">
            Ton prochain exercice, <span className="auth-gradient-text">compris</span>.
          </h2>
          <p className="lp-final-lead">
            Deux minutes pour créer ton compte. Ton devoir n'attend pas.
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

      {/* On a phone the only call to action was at the very top; this one
          follows the visitor down the page. */}
      <aside className="lp-sticky-cta" aria-label="Créer un compte">
        <Link
          className="btn btn-primary btn-md lp-btn"
          to="/connexion"
          state={{ authMode: "signup" }}
        >
          Commencer — c'est gratuit
        </Link>
      </aside>

      <footer className="lp-foot">
        <p className="lp-foot-brand">
          <span className="auth-mark" aria-hidden="true">
            <span>←</span>
          </span>
          Fahem
        </p>
        <p className="lp-foot-scope">{scope}</p>
        <nav className="lp-foot-nav" aria-label="Pied de page">
          <a href="#essayer">Essayer</a>
          <a href="#fonctionnalites">Ce que ça fait</a>
          <a href="#parents">Parents et profs</a>
          <a href="#questions">Questions</a>
          <Link to="/connexion">Se connecter</Link>
        </nav>
      </footer>
    </div>
  );
}
