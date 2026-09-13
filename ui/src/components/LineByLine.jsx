import { useId, useRef, useState } from "react";
import { tokenize } from "../lib/tokenizeAlgo.js";

/*
 * "Ligne à ligne": the landing page's one interactive section.
 *
 * The feature list says Fahem gives the Algorithme and the Python "ligne pour
 * ligne". This shows it instead of saying it: pick an exercise, point at (or
 * tab to) a line, and both versions of that line light up with one sentence
 * on what changed between them.
 *
 * The three exercises are the ones AuthDemo types, so the page never shows
 * two different answers to the same énoncé. Every note is a statement about
 * chapter 1 syntax that a teacher would sign - no line is explained with
 * something the chapter does not cover.
 *
 * Plain React and CSS, no Motion: this section has to work fully on the
 * reduced-motion path, where the Motion chunk is never loaded.
 */
const EXERCISES = [
  {
    tab: "Le carré",
    question: "Calcule le carré d'un nombre saisi.",
    rows: [
      {
        algo: "Lire (x)",
        python: "x = float(input())",
        note: "Lire (x) range la valeur saisie dans x. En Python, input() la lit comme du texte : float() la convertit en réel.",
      },
      {
        algo: "carre ← x * x",
        python: "carre = x * x",
        note: "L'affectation : ← dans ton cours, = en Python. Même sens, « carre reçoit x fois x ».",
      },
      {
        algo: 'Ecrire ("Carré :", carre)',
        python: 'print("Carré :", carre)',
        note: "Ecrire affiche à l'écran, print aussi. Le texte entre guillemets s'affiche tel quel, carre est remplacé par sa valeur.",
      },
    ],
  },
  {
    tab: "La moyenne",
    question: "Affiche la moyenne de deux notes.",
    rows: [
      {
        algo: "Lire (a)",
        python: "a = float(input())",
        note: "Une note peut valoir 12.5 : on la lit comme un réel, d'où float().",
      },
      {
        algo: "Lire (b)",
        python: "b = float(input())",
        note: "Un Lire par variable, comme dans ton cours : chaque ligne lit une seule valeur.",
      },
      {
        algo: "moy ← (a + b) / 2",
        python: "moy = (a + b) / 2",
        note: "Les parenthèses d'abord, comme en maths. Sans elles, seul b serait divisé par 2.",
      },
      {
        algo: 'Ecrire ("Moyenne :", moy)',
        python: 'print("Moyenne :", moy)',
        note: "La virgule sépare ce qu'on affiche : le texte, puis la valeur de moy.",
      },
    ],
  },
  {
    tab: "Le reste",
    question: "Donne le reste de la division de a par b.",
    rows: [
      {
        algo: "Lire (a)",
        python: "a = int(input())",
        note: "Ici int() et pas float() : le reste d'une division n'a de sens qu'entre entiers.",
      },
      {
        algo: "Lire (b)",
        python: "b = int(input())",
        note: "b est aussi un entier. S'il vaut 0, la division est impossible - dans les deux langages.",
      },
      {
        algo: "r ← a mod b",
        python: "r = a % b",
        note: "mod devient % en Python. Par exemple 17 mod 5 vaut 2, car 17 = 3 × 5 + 2.",
      },
      {
        algo: 'Ecrire ("Reste :", r)',
        python: 'print("Reste :", r)',
        note: "Même affichage qu'avant : seul le nom de la variable change.",
      },
    ],
  },
];

function Code({ text }) {
  return tokenize(text).map((tok, i) =>
    tok.kind ? (
      <span key={i} className={`tk-${tok.kind}`}>
        {tok.text}
      </span>
    ) : (
      tok.text
    )
  );
}

export default function LineByLine() {
  const [exercise, setExercise] = useState(0);
  const [row, setRow] = useState(0);
  const tabRefs = useRef([]);
  const id = useId();
  const current = EXERCISES[exercise];
  const active = current.rows[Math.min(row, current.rows.length - 1)];

  const select = (index) => {
    setExercise(index);
    setRow(0);
  };

  // The WAI-ARIA tabs pattern: arrows move between tabs, Home/End jump to the
  // ends, and focus follows the selection (automatic activation).
  const onTabKey = (event) => {
    const last = EXERCISES.length - 1;
    const next = {
      ArrowRight: exercise === last ? 0 : exercise + 1,
      ArrowLeft: exercise === 0 ? last : exercise - 1,
      Home: 0,
      End: last,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    select(next);
    tabRefs.current[next]?.focus();
  };

  return (
    <div className="lbl" style={{ "--tab": exercise, "--tabs": EXERCISES.length }}>
      <div className="lbl-tabs" role="tablist" aria-label="Exercices">
        {/* Slides to the selected tab: equal-width tabs, so its offset is
            simply the index times its own width. */}
        <span className="lbl-tab-indicator" aria-hidden="true" />
        {EXERCISES.map((ex, i) => (
          <button
            key={ex.tab}
            ref={(el) => (tabRefs.current[i] = el)}
            type="button"
            role="tab"
            id={`${id}-tab-${i}`}
            aria-selected={i === exercise}
            aria-controls={`${id}-panel`}
            tabIndex={i === exercise ? 0 : -1}
            className="lbl-tab"
            onClick={() => select(i)}
            onKeyDown={onTabKey}
          >
            {ex.tab}
          </button>
        ))}
      </div>

      <div
        className="lbl-panel"
        role="tabpanel"
        id={`${id}-panel`}
        aria-labelledby={`${id}-tab-${exercise}`}
      >
        <p className="lbl-question">
          <span className="demo-question-label">Exercice</span>
          {current.question}
        </p>

        <div className="lbl-scroll">
          {/* Keyed by exercise so the rows remount and replay their entrance
              when the tab changes. */}
          <div className="lbl-table" key={exercise} style={{ "--row": row }}>
            <div className="lbl-head" aria-hidden="true">
              <span>Algorithme</span>
              <span>Python</span>
            </div>
            <div className="lbl-rows">
              <span className="lbl-highlight" aria-hidden="true" />
              {current.rows.map((r, i) => (
                // A button per line: reachable by keyboard, and it names both
                // halves, so a screen reader hears the pair it selects.
                <button
                  key={r.algo + i}
                  type="button"
                  className="lbl-row"
                  style={{ "--r": i }}
                  aria-pressed={i === row}
                  aria-label={`Ligne ${i + 1} : ${r.algo}, en Python ${r.python}`}
                  onPointerEnter={(event) => {
                    if (event.pointerType === "mouse") setRow(i);
                  }}
                  onFocus={() => setRow(i)}
                  onClick={() => setRow(i)}
                >
                  <code aria-hidden="true">
                    <Code text={r.algo} />
                  </code>
                  <code aria-hidden="true">
                    <Code text={r.python} />
                  </code>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Polite: announced after the line the student moved to, never over it. */}
        <p className="lbl-note" aria-live="polite">
          <span className="lbl-note-n" aria-hidden="true">
            {Math.min(row, current.rows.length - 1) + 1}
          </span>
          <span key={`${exercise}-${row}`} className="lbl-note-text">
            {active.note}
          </span>
        </p>
      </div>
    </div>
  );
}
