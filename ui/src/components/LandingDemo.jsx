import { useState } from "react";
import { Link } from "react-router-dom";
import { LazyMotion, MotionConfig, domAnimation } from "motion/react";
import Markdown from "./Markdown.jsx";
import { CheckedAnswer, GuidedSteps } from "./learning/Learning.jsx";
import { DEMO_EXERCISES } from "../data/demoExercises.js";

/**
 * "Essaie tout de suite" on the landing page: the real product, without an
 * account.
 *
 * The three exercises and their answers are written by hand
 * (data/demoExercises.js) and rendered by the components the chat itself uses
 * - the Algorithme | Python table, the guided step rail, the verdict card -
 * so a visitor sees exactly what they would get, while no model is called and
 * no token is spent. "▶ Exécuter le Python" under the solution runs for real.
 *
 * Motion lives in the signed-in app's provider, which the landing page is
 * outside of, so this section brings its own (same features, same
 * reduced-motion rule).
 */

const MODES = [
  {
    id: "solution",
    label: "La solution",
    hint: "Algorithme et Python, ligne par ligne.",
  },
  { id: "guided", label: "Mode guidé", hint: "Des indices avant la solution." },
  { id: "check", label: "Ma réponse", hint: "Fahem corrige ce que tu as écrit." },
];

export default function LandingDemo() {
  const [exercise, setExercise] = useState(DEMO_EXERCISES[0]);
  const [mode, setMode] = useState("solution");
  const current = MODES.find((m) => m.id === mode);

  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <div className="lpd">
          <div className="lpd-pickers">
            <div className="lpd-tabs" role="tablist" aria-label="Exercice à essayer">
              {DEMO_EXERCISES.map((ex) => (
                <button
                  key={ex.id}
                  type="button"
                  role="tab"
                  aria-selected={ex.id === exercise.id}
                  className={`lpd-tab${ex.id === exercise.id ? " is-on" : ""}`}
                  onClick={() => setExercise(ex)}
                >
                  {ex.tab}
                </button>
              ))}
            </div>
            <div className="lpd-modes" role="tablist" aria-label="Façon de répondre">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  role="tab"
                  aria-selected={m.id === mode}
                  className={`lpd-mode${m.id === mode ? " is-on" : ""}`}
                  onClick={() => setMode(m.id)}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <p className="lpd-hint">{current.hint}</p>

          <div className="lpd-window">
            <div className="lpd-bubble">
              {mode === "check" ? (
                <>
                  <span className="lpd-bubble-tag">Vérifier ma réponse</span>
                  <pre className="lpd-attempt">{exercise.attempt}</pre>
                </>
              ) : (
                exercise.statement
              )}
            </div>

            <div className="lpd-answer">
              <p className="lpd-who" aria-hidden="true">
                <span className="brand-mark">←</span> Fahem
              </p>
              {mode === "guided" && (
                <>
                  <GuidedSteps step={2} />
                  <Markdown>{exercise.hint}</Markdown>
                  <p className="lpd-note">
                    Étape suivante, squelette à compléter, puis solution — c'est toi qui
                    décides quand.
                  </p>
                </>
              )}
              {mode === "solution" && (
                <>
                  <Markdown>{exercise.answer}</Markdown>
                  <p className="lpd-note">
                    ▲ Le bouton « Exécuter le Python » marche vraiment : donne tes
                    valeurs et le programme tourne dans ton navigateur.
                  </p>
                </>
              )}
              {mode === "check" && (
                <CheckedAnswer
                  content={exercise.check.content}
                  verdict={exercise.check.verdict}
                />
              )}
            </div>
          </div>

          <p className="lpd-cta">
            C'est exactement ce que tu auras sur tes propres exercices.{" "}
            <Link
              className="lp-textlink lp-textlink-strong"
              to="/connexion"
              state={{ authMode: "signup" }}
            >
              Créer mon compte gratuit →
            </Link>
          </p>
        </div>
      </MotionConfig>
    </LazyMotion>
  );
}
