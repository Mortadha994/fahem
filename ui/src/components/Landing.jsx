import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  LazyMotion,
  MotionConfig,
  domAnimation,
  useScroll,
  useSpring,
} from "motion/react";
import * as m from "motion/react-m";
import Hero from "./landing/Hero.jsx";
import Bento from "./landing/Bento.jsx";
import LandingDemo from "./LandingDemo.jsx";
import CountUp from "./CountUp.jsx";
import ThemeToggle from "./ThemeToggle.jsx";
import { fetchOverview, listFr, plural } from "../lib/overview.js";
import "./landing/landing.css";

/*
 * The public page: what Fahem is, for a student who has never heard of it and
 * has not been asked for an e-mail address yet.
 *
 * Everything stated here is checkable against the app, on purpose: no
 * testimonials, no student counts, no "utilisé par N lycées". The figures,
 * the programme, the chapter answer in the FAQ and the
 * syntax strip all come from GET /public/overview (public_overview.py), so
 * publishing a chapter updates this page within a minute.
 *
 * Shape: a dark, lit hero with the product rebuilt in markup (landing/Hero),
 * then light sections alternating with dark bands, and one thing a visitor
 * can actually touch before signing up (LandingDemo) - three real exercises,
 * answered without a model call.
 *
 * Motion: this page renders outside the app's provider, so it carries its own
 * LazyMotion. Everything animated is transform/opacity, reveals are
 * whileInView with `once`, and MotionConfig reducedMotion="user" drops the
 * movement when the system asks for it.
 */

const shortNiveau = (label) => label.replace(/ année$/, "");
const lowerFirst = (text) => text.charAt(0).toLowerCase() + text.slice(1);
const isReady = (chapter) => chapter.status === "active";

function chaptersAnswer(overview) {
  if (!overview)
    return "La section Programme, plus bas, liste les chapitres disponibles.";
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

/* Course notation beside its Python: the whole pitch in one line. A later
   chapter's pairs join only once that chapter is published. */
const CHAPTER_SYNTAX = {
  2: [
    ["Si x > 0 Alors", "if x > 0 :"],
    ["Sinon", "else :"],
    ["a ET b", "a and b"],
    ["a ≠ b", "a != b"],
  ],
  3: [
    ["Pour i de 1 à n", "for i in range(1, n+1) :"],
    ["Tant que x > 0", "while x > 0 :"],
  ],
};

const SYNTAX = [
  ["x ← x + 1", "x = x + 1"],
  ["Lire (x)", "x = input()"],
  ['Ecrire ("Bonjour")', 'print("Bonjour")'],
  ["a mod b", "a % b"],
  ["a div b", "a // b"],
  ["réel", "float"],
  ["entier", "int"],
];

const STEPS = [
  {
    title: "Envoie ton exercice",
    body: "Colle l'énoncé, prends-le en photo, ou choisis-en un dans la série de ton chapitre.",
  },
  {
    title: "Guidé, ou direct",
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
    "Utilise des boucles pas encore vues en classe",
    "Donne la réponse, jamais l'envie de chercher",
    "Tu ne sais pas si c'est juste pour ton programme",
  ],
  us: [
    "Écrit la syntaxe de ton chapitre, à la lettre",
    "Ne sort jamais de ce que tu as vu en cours",
    "Te guide d'abord, puis corrige ce que tu écris",
    "Montre le passage du cours qu'il a utilisé",
  ],
};

const faqFrom = (overview) => [
  {
    q: "C'est vraiment gratuit ?",
    a: "Oui. Une adresse e-mail et un mot de passe, ou ton compte Google, et tu peux poser ta première question. Aucune carte bancaire.",
  },
  { q: "Quels chapitres sont couverts ?", a: chaptersAnswer(overview) },
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
    a: "Le mode guidé te fait chercher avant de montrer quoi que ce soit, et « Vérifier ma réponse » corrige ce que tu as écrit toi-même. Le jour du devoir, c'est ça qui compte.",
  },
  {
    q: "En quoi c'est différent de ChatGPT ?",
    a: "Une IA généraliste a appris la syntaxe d'internet. Fahem ne répond qu'avec ton cours sous les yeux, dans la notation de ton manuel, et il te montre d'où vient sa réponse.",
  },
  {
    q: "Ça marche sur téléphone ?",
    a: "Oui, dans le navigateur, sans rien installer.",
  },
];

const MENU = [
  { href: "#essayer", label: "Essayer" },
  { href: "#fonctionnalites", label: "Ce que ça fait" },
  { href: "#etapes", label: "Comment ça marche" },
  { href: "#programme", label: "Programme" },
  { href: "#questions", label: "Questions" },
];

const rise = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", visualDuration: 0.6, bounce: 0.2 },
  },
};
const inView = {
  initial: "hidden",
  whileInView: "show",
  viewport: { once: true, amount: 0.2 },
};

/** A section title block, always the same rhythm: kicker, title, lead. */
function Head({ kicker, title, lead }) {
  return (
    <m.header className="fx-head" variants={rise} {...inView}>
      <p className="fx-kicker">{kicker}</p>
      <h2 className="fx-h2">{title}</h2>
      {lead && <p className="fx-lead">{lead}</p>}
    </m.header>
  );
}

export default function Landing() {
  const [overview, setOverview] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const menuButton = useRef(null);
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, {
    stiffness: 140,
    damping: 30,
    mass: 0.3,
  });

  useEffect(() => {
    let cancelled = false;
    fetchOverview()
      .then((data) => !cancelled && setOverview(data))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        menuButton.current?.focus();
      }
    };
    const onResize = () => window.innerWidth > 860 && setMenuOpen(false);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
    };
  }, [menuOpen]);

  const faq = faqFrom(overview);
  const programme = overview?.chapters ?? [];
  const ready = programme.filter(isReady);
  const exercises = overview?.totals.exercises ?? 0;
  const photos = Boolean(overview?.features.photo_attachments);
  const syntax = [...SYNTAX, ...ready.flatMap((c) => CHAPTER_SYNTAX[c.id] ?? [])];

  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <div className="fx" id="top">
          <m.span
            className="fx-progress"
            style={{ scaleX: progress }}
            aria-hidden="true"
          />

          {/* --- bar ------------------------------------------------------ */}
          <header className={`fx-bar${scrolled ? " is-scrolled" : ""}`}>
            <a className="fx-brand" href="#top">
              <span className="fx-brand-mark" aria-hidden="true">
                ←
              </span>
              Fahem
            </a>
            <nav className="fx-nav" aria-label="Sections de la page">
              {MENU.map((item) => (
                <a key={item.href} href={item.href}>
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="fx-bar-end">
              <ThemeToggle className="fx-theme" />
              <Link className="fx-textlink" to="/connexion">
                Se connecter
              </Link>
              <Link
                className="fx-btn fx-btn-primary fx-btn-sm"
                to="/connexion"
                state={{ authMode: "signup" }}
              >
                Créer un compte
              </Link>
              <button
                type="button"
                ref={menuButton}
                className="fx-burger"
                aria-expanded={menuOpen}
                aria-controls="fx-menu"
                onClick={() => setMenuOpen((v) => !v)}
              >
                <span aria-hidden="true">{menuOpen ? "✕" : "☰"}</span>
                <span className="sr-only">Menu</span>
              </button>
            </div>
          </header>
          {menuOpen && (
            <div className="fx-menu" id="fx-menu">
              {MENU.map((item) => (
                <a key={item.href} href={item.href} onClick={() => setMenuOpen(false)}>
                  {item.label}
                </a>
              ))}
              <Link to="/connexion" onClick={() => setMenuOpen(false)}>
                Se connecter
              </Link>
            </div>
          )}

          <main>
            <Hero exercises={exercises} />

            {/* --- syntax strip ------------------------------------------- */}
            <div className="fx-marquee" aria-hidden="true">
              <div className="fx-marquee-track">
                {[...syntax, ...syntax].map(([algo, py], i) => (
                  <span className="fx-marquee-item" key={i}>
                    <code className="is-algo">{algo}</code>
                    <span>⇄</span>
                    <code className="is-py">{py}</code>
                  </span>
                ))}
              </div>
            </div>

            {/* --- try it ------------------------------------------------- */}
            <section className="fx-section fx-tint" id="essayer">
              <Head
                kicker="Essaie tout de suite"
                title={
                  <>
                    Un exercice, <em>trois façons</em> de s'en sortir.
                  </>
                }
                lead="Choisis un exercice : la solution complète, le mode guidé, ou la correction de ta propre réponse. Sans compte, sans rien installer."
              />
              <m.div variants={rise} {...inView}>
                <LandingDemo />
              </m.div>
            </section>

            {/* --- features ----------------------------------------------- */}
            <section className="fx-section" id="fonctionnalites">
              <Head
                kicker="Ce que tu peux faire"
                title={
                  <>
                    Plus qu'une réponse : <em>apprendre</em> à la trouver.
                  </>
                }
                lead="Fahem connaît le chapitre que tu as en classe cette semaine — pas le programme d'un autre pays, ni la syntaxe d'un forum."
              />
              <Bento photos={photos} />
            </section>

            {/* --- numbers ------------------------------------------------ */}
            <section className="fx-band">
              <m.div className="fx-stats" variants={rise} {...inView}>
                <div className="fx-stat">
                  <CountUp className="fx-stat-n" value={4} />
                  <span className="fx-stat-unit">étapes</span>
                  <span className="fx-stat-label">
                    pour comprendre, avant la solution
                  </span>
                </div>
                <div className="fx-stat">
                  <CountUp className="fx-stat-n" value={exercises} />
                  <span className="fx-stat-unit">exercices corrigés</span>
                  <span className="fx-stat-label">
                    de {plural(ready.length || 1, "chapitre")}, prêts à essayer
                  </span>
                </div>
                <div className="fx-stat">
                  <span className="fx-stat-n">0</span>
                  <span className="fx-stat-unit">dinar</span>
                  <span className="fx-stat-label">gratuit pour les élèves</span>
                </div>
              </m.div>
            </section>

            {/* --- steps -------------------------------------------------- */}
            <section className="fx-section" id="etapes">
              <Head kicker="Comment ça marche" title="Trois minutes, trois étapes." />
              <m.ol
                className="fx-steps"
                variants={{ show: { transition: { staggerChildren: 0.1 } } }}
                {...inView}
              >
                {STEPS.map((step, i) => (
                  <m.li className="fx-step" key={step.title} variants={rise}>
                    <span className="fx-step-n" aria-hidden="true">
                      {i + 1}
                    </span>
                    <h3>{step.title}</h3>
                    <p>{step.body}</p>
                  </m.li>
                ))}
              </m.ol>
            </section>

            {/* --- versus ------------------------------------------------- */}
            <section className="fx-section fx-section-narrow fx-tint">
              <Head
                kicker="La différence"
                title={
                  <>
                    Pourquoi pas <em>n'importe quelle IA</em> ?
                  </>
                }
                lead="Une réponse juste dans la mauvaise notation reste fausse sur une copie."
              />
              <m.div
                className="fx-versus"
                variants={{ show: { transition: { staggerChildren: 0.12 } } }}
                {...inView}
              >
                <m.div className="fx-versus-col is-them" variants={rise}>
                  <h3>Une IA généraliste</h3>
                  <ul>
                    {VERSUS.them.map((line) => (
                      <li key={line}>
                        <span aria-hidden="true">✕</span>
                        {line}
                      </li>
                    ))}
                  </ul>
                </m.div>
                <m.div className="fx-versus-col is-us" variants={rise}>
                  <h3>
                    Fahem <span className="fx-tag is-ready">ton chapitre</span>
                  </h3>
                  <ul>
                    {VERSUS.us.map((line) => (
                      <li key={line}>
                        <span aria-hidden="true">✓</span>
                        {line}
                      </li>
                    ))}
                  </ul>
                </m.div>
              </m.div>
            </section>

            {/* --- programme ---------------------------------------------- */}
            <section className="fx-section" id="programme">
              <Head
                kicker="Programme"
                title="Ce qui est prêt, et ce qui arrive."
                lead="La liste est courte parce qu'elle est vraie : elle se met à jour dès qu'un chapitre est publié."
              />
              <m.div
                className="fx-chapters"
                variants={{ show: { transition: { staggerChildren: 0.06 } } }}
                {...inView}
              >
                {programme.map((c) => (
                  <m.article
                    className={`fx-chapter${isReady(c) ? " is-ready" : ""}`}
                    key={`${c.niveau}-${c.id}`}
                    variants={rise}
                  >
                    <p className="fx-chapter-top">
                      <span>
                        {shortNiveau(c.niveau_label)} · Chapitre {c.id}
                      </span>
                      <span className={`fx-tag${isReady(c) ? " is-ready" : ""}`}>
                        {isReady(c) ? "Disponible" : "À venir"}
                      </span>
                    </p>
                    <h3>{c.title}</h3>
                    {c.topics.length > 0 && (
                      <p className="fx-chapter-topics">{c.topics.join(" · ")}</p>
                    )}
                    {isReady(c) && c.exercises > 0 && (
                      <p className="fx-chapter-meta">
                        {plural(c.exercises, "exercice")} corrigé
                        {c.exercises > 1 ? "s" : ""}
                      </p>
                    )}
                  </m.article>
                ))}
              </m.div>
            </section>

            {/* --- parents and teachers ----------------------------------- */}
            <section className="fx-section fx-section-narrow fx-tint" id="parents">
              <m.div className="fx-parents" variants={rise} {...inView}>
                <h2>Tu es parent ou professeur ?</h2>
                <ul>
                  <li>
                    <b>Gratuit</b>, sans publicité et sans carte bancaire.
                  </li>
                  <li>
                    <b>Le programme tunisien</b> : la notation du manuel, et rien que le
                    chapitre en cours.
                  </li>
                  <li>
                    <b>L'élève cherche d'abord</b> : indices étape par étape, puis
                    correction de ce qu'il a écrit lui-même.
                  </li>
                  <li>
                    <b>Chaque réponse est sourcée</b> : le passage du cours utilisé est
                    affiché.
                  </li>
                </ul>
              </m.div>
            </section>

            {/* --- FAQ ---------------------------------------------------- */}
            <section className="fx-section fx-section-narrow" id="questions">
              <Head kicker="Questions" title="Ce que les élèves demandent." />
              <m.div
                className="fx-faq"
                variants={{ show: { transition: { staggerChildren: 0.05 } } }}
                {...inView}
              >
                {faq.map((item) => (
                  <m.details className="fx-faq-item" key={item.q} variants={rise}>
                    <summary>
                      {item.q}
                      <span aria-hidden="true" className="fx-faq-sign" />
                    </summary>
                    <p>{item.a}</p>
                  </m.details>
                ))}
              </m.div>
            </section>

            {/* --- final --------------------------------------------------- */}
            <section className="fx-final">
              <div className="fx-hero-sky" aria-hidden="true">
                <span className="fx-aurora fx-aurora-1" />
                <span className="fx-aurora fx-aurora-3" />
              </div>
              <m.div className="fx-final-inner" variants={rise} {...inView}>
                <h2>
                  Ton prochain exercice, <em>compris</em>.
                </h2>
                <p>Deux minutes pour créer ton compte. Ton devoir n'attend pas.</p>
                <div className="fx-hero-cta">
                  <Link
                    className="fx-btn fx-btn-primary"
                    to="/connexion"
                    state={{ authMode: "signup" }}
                  >
                    Créer mon compte gratuit
                  </Link>
                  <Link className="fx-btn fx-btn-ghost" to="/connexion">
                    J'ai déjà un compte →
                  </Link>
                </div>
              </m.div>
            </section>
          </main>

          {/* The bar the visitor keeps on a phone. */}
          <aside className="fx-sticky" aria-label="Créer un compte">
            <Link
              className="fx-btn fx-btn-primary"
              to="/connexion"
              state={{ authMode: "signup" }}
            >
              Commencer — c'est gratuit
            </Link>
          </aside>

          <footer className="fx-foot">
            <p className="fx-foot-brand">
              <span className="fx-brand-mark" aria-hidden="true">
                ←
              </span>
              Fahem
            </p>
            <nav aria-label="Pied de page">
              <a href="#essayer">Essayer</a>
              <a href="#fonctionnalites">Ce que ça fait</a>
              <a href="#parents">Parents et profs</a>
              <Link to="/connexion">Se connecter</Link>
            </nav>
          </footer>
        </div>
      </MotionConfig>
    </LazyMotion>
  );
}
