import { useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, LazyMotion, MotionConfig, domAnimation } from "motion/react";
import * as m from "motion/react-m";
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
 * Nothing here scrolls inside anything else. Each answer is short enough to
 * read where it stands, and the one part that would make it long - the
 * execution trace - opens in place, so the page grows rather than a box
 * inside it.
 *
 * Motion lives in the signed-in app's provider, which the landing page is
 * outside of, so this section brings its own (same features, same
 * reduced-motion rule).
 */

const MODES = [
  {
    id: "solution",
    label: "La solution",
    icon: "📖",
    hint: "Algorithme et Python côte à côte — et le programme tourne pour de vrai.",
  },
  {
    id: "guided",
    label: "Mode guidé",
    icon: "🧭",
    hint: "Un indice d'abord : à toi de chercher, Fahem ne donne pas tout.",
  },
  {
    id: "check",
    label: "Ma réponse",
    icon: "✍️",
    hint: "Tu colles ce que tu as écrit, Fahem te dit où ça coince.",
  },
];

const panel = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.26, ease: "easeOut" } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.14 } },
};

export default function LandingDemo() {
  const [exercise, setExercise] = useState(DEMO_EXERCISES[0]);
  const [mode, setMode] = useState("solution");
  const [trace, setTrace] = useState(false);
  const current = MODES.find((x) => x.id === mode);

  const pickExercise = (ex) => {
    setExercise(ex);
    setTrace(false);
  };
  const pickMode = (id) => {
    setMode(id);
    setTrace(false);
  };

  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <div className="lpd">
          {/* 1. which exercise - cards, so the choice itself shows what it is */}
          <div className="lpd-choose" role="tablist" aria-label="Exercice à essayer">
            {DEMO_EXERCISES.map((ex) => {
              const on = ex.id === exercise.id;
              return (
                <m.button
                  key={ex.id}
                  type="button"
                  role="tab"
                  aria-selected={on}
                  className={`lpd-choice${on ? " is-on" : ""}`}
                  onClick={() => pickExercise(ex)}
                  whileHover={{ y: -3 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="lpd-choice-tab">{ex.tab}</span>
                  <span className="lpd-choice-text">{ex.short || ex.statement}</span>
                </m.button>
              );
            })}
          </div>

          {/* 2. how you want it answered */}
          <div className="lpd-modes" role="tablist" aria-label="Façon de répondre">
            {MODES.map((x) => (
              <button
                key={x.id}
                type="button"
                role="tab"
                aria-selected={x.id === mode}
                className={`lpd-mode${x.id === mode ? " is-on" : ""}`}
                onClick={() => pickMode(x.id)}
              >
                <span aria-hidden="true">{x.icon}</span> {x.label}
              </button>
            ))}
          </div>
          <p className="lpd-hint">{current.hint}</p>

          {/* 3. the answer */}
          <div className="lpd-window">
            <div className="fx-window-bar" aria-hidden="true">
              <i />
              <i />
              <i />
              <span>Fahem — {exercise.tab.toLowerCase()}</span>
            </div>

            <div className="lpd-body">
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

              <AnimatePresence mode="wait" initial={false}>
                <m.div
                  key={`${exercise.id}-${mode}`}
                  className="lpd-answer"
                  variants={panel}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                >
                  <p className="lpd-who" aria-hidden="true">
                    <span className="brand-mark">←</span> Fahem
                  </p>

                  {mode === "guided" && (
                    <>
                      <GuidedSteps step={2} />
                      <Markdown>{exercise.hint}</Markdown>
                      <p className="lpd-note">
                        Ensuite le squelette à compléter, puis la solution — quand
                        <b> tu </b>
                        le décides.
                      </p>
                    </>
                  )}

                  {mode === "solution" && (
                    <>
                      <Markdown>{exercise.answer}</Markdown>
                      {exercise.trace && (
                        <div className="lpd-more">
                          <button
                            type="button"
                            className="lpd-more-btn"
                            aria-expanded={trace}
                            onClick={() => setTrace((v) => !v)}
                          >
                            <span aria-hidden="true">{trace ? "▴" : "▾"}</span>{" "}
                            {trace ? "Masquer la trace" : "Voir la trace d'exécution"}
                          </button>
                          <AnimatePresence initial={false}>
                            {trace && (
                              <m.div
                                key="trace"
                                className="lpd-trace"
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.28, ease: "easeOut" }}
                              >
                                <Markdown>{exercise.trace}</Markdown>
                              </m.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}
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
                </m.div>
              </AnimatePresence>
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
