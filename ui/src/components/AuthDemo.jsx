import { useEffect, useState } from "react";
import Badge from "./ui/Badge.jsx";

/*
 * Three real exercises in chapter 1 syntax. Each one plays as: the énoncé is
 * typed, the Algorithme and Python answers are typed, then the checker's
 * verdict lands and the parts of the course the answer relied on slide in.
 * It is Fahem's actual loop - question, grounded answer, verdict - shown
 * before the student has an account.
 *
 * Every answer is at most four lines and fits half the panel unwrapped.
 */
const SCENES = [
  {
    question: "Calcule le carré d'un nombre saisi.",
    algo: `Lire (x)
carre ← x * x
Ecrire ("Carré :", carre)`,
    python: `x = float(input())
carre = x * x
print("Carré :", carre)`,
    chips: ["Entrée / sortie", "Affectation ←", "Opérateurs"],
  },
  {
    question: "Affiche la moyenne de deux notes.",
    algo: `Lire (a)
Lire (b)
moy ← (a + b) / 2
Ecrire ("Moyenne :", moy)`,
    python: `a = float(input())
b = float(input())
moy = (a + b) / 2
print("Moyenne :", moy)`,
    chips: ["Entrée / sortie", "Opérateurs arithmétiques"],
  },
  {
    question: "Donne le reste de la division de a par b.",
    algo: `Lire (a)
Lire (b)
r ← a mod b
Ecrire ("Reste :", r)`,
    python: `a = int(input())
b = int(input())
r = a % b
print("Reste :", r)`,
    chips: ["mod → %", "Types entiers", "Affectation ←"],
  },
];

// One pass of lightweight highlighting. Longest alternatives first, and
// strings before everything so a keyword inside quotes stays a string.
const TOKEN =
  /("[^"\n]*"?)|\b(Lire|Ecrire|Si|Alors|Sinon|Pour|Faire|mod|div)\b|\b(print|input|float|int)\b|(←|[*+/%=-])|(\d+)/g;
const KINDS = ["str", "kw", "fn", "op", "num"];

function tokenize(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(TOKEN)) {
    if (m.index > last) out.push({ text: text.slice(last, m.index) });
    const kind = KINDS[m.slice(1).findIndex((g) => g !== undefined)];
    out.push({ text: m[0], kind });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ text: text.slice(last) });
  return out;
}

/** The first `count` characters of `text`, highlighted, plus the rest as an
 * invisible ghost that holds the final size so nothing shifts while typing. */
function Typed({ text, count, caret }) {
  const nodes = [];
  let left = count;
  tokenize(text).forEach((tok, i) => {
    if (left <= 0) return;
    const shown = tok.text.slice(0, left);
    left -= shown.length;
    nodes.push(
      tok.kind ? (
        <span key={i} className={`tk-${tok.kind}`}>
          {shown}
        </span>
      ) : (
        shown
      )
    );
  });
  return (
    <>
      {nodes}
      {caret && <span className="type-caret" />}
      <span className="type-ghost">{text.slice(Math.min(count, text.length))}</span>
    </>
  );
}

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

const FULL = Number.MAX_SAFE_INTEGER;

/**
 * The panel's live demo. `paused` is set while the student is in the form:
 * the loop freezes where it is instead of moving beside what they type. It
 * also freezes while the tab is hidden. Under prefers-reduced-motion it shows
 * the first exercise complete and never moves.
 *
 * One accessible name for the whole figure; the characters are aria-hidden,
 * so a screen reader is not read half-typed code.
 */
export default function AuthDemo({ paused }) {
  const [reduced] = useState(prefersReducedMotion);
  const [scene, setScene] = useState(0);
  const [qCount, setQCount] = useState(reduced ? FULL : 0);
  const [codeCount, setCodeCount] = useState(reduced ? FULL : 0);
  const [phase, setPhase] = useState(reduced ? "verdict" : "question");
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const onVisibility = () => setHidden(document.hidden);
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  const current = SCENES[scene];

  useEffect(() => {
    if (reduced || paused || hidden) return undefined;
    const codeLength = current.algo.length + current.python.length;
    let run;
    let delay;

    if (phase === "question") {
      if (qCount < current.question.length) {
        run = () => setQCount((n) => n + 1);
        delay = qCount === 0 ? 500 : 26;
      } else {
        run = () => setPhase("code");
        delay = 380;
      }
    } else if (phase === "code") {
      if (codeCount < codeLength) {
        const ch =
          codeCount < current.algo.length
            ? current.algo[codeCount]
            : current.python[codeCount - current.algo.length];
        run = () => setCodeCount((n) => n + 1);
        delay = ch === "\n" ? 150 : 19;
      } else {
        run = () => setPhase("verdict");
        delay = 260;
      }
    } else if (phase === "verdict") {
      run = () => setPhase("out");
      delay = 4200;
    } else {
      run = () => {
        setScene((s) => (s + 1) % SCENES.length);
        setQCount(0);
        setCodeCount(0);
        setPhase("question");
      };
      delay = 480;
    }

    const timer = setTimeout(run, delay);
    return () => clearTimeout(timer);
  }, [reduced, paused, hidden, current, phase, qCount, codeCount]);

  const algoCount = Math.min(codeCount, current.algo.length);
  const pythonCount = Math.max(0, codeCount - current.algo.length);
  const typingQuestion = phase === "question";
  const typingAlgo = phase === "code" && codeCount < current.algo.length;
  const typingPython = phase === "code" && !typingAlgo;

  return (
    <figure
      className={`auth-demo phase-${phase}`}
      role="img"
      aria-label="Démonstration : Fahem résout un exercice en Algorithme et en Python, avec la syntaxe du chapitre, puis montre les parties du cours utilisées."
    >
      <div className="demo-question" aria-hidden="true">
        <span className="demo-question-label">Exercice</span>
        <span className="demo-question-text">
          <Typed text={current.question} count={qCount} caret={typingQuestion} />
        </span>
      </div>

      <div className="auth-sample" aria-hidden="true">
        <div className="auth-sample-col auth-sample-algo">
          <span className="auth-sample-label">Algorithme</span>
          <pre>
            <Typed text={current.algo} count={algoCount} caret={typingAlgo} />
          </pre>
        </div>
        <div className="auth-sample-col">
          <span className="auth-sample-label">Python</span>
          <pre>
            <Typed text={current.python} count={pythonCount} caret={typingPython} />
          </pre>
        </div>
      </div>

      <div className="demo-verdict" aria-hidden="true">
        <Badge tone="success">✓ Syntaxe du chapitre respectée</Badge>
        <div className="demo-chips">
          {current.chips.map((chip, i) => (
            <span key={chip} className="demo-chip" style={{ "--i": i }}>
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="demo-dots" aria-hidden="true">
        {SCENES.map((s, i) => (
          <span key={s.question} className={i === scene ? "is-on" : ""} />
        ))}
      </div>
    </figure>
  );
}
