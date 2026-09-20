import { useId, useMemo, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { inputCalls, runPython } from "../lib/pythonRunner.js";
import { SPRING_ENTER, SPRING_HOVER } from "../lib/motion.js";

/**
 * "▶ Exécuter le Python", under a solution table: one field per input() of
 * the program (labelled with its prompt), then the output as a terminal would
 * show it - line after line, with a cursor while it runs. The program runs in
 * the browser (lib/pythonRunner.js).
 */
export default function PythonRunner({ code }) {
  const calls = useMemo(() => inputCalls(code), [code]);
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState([]);
  const [state, setState] = useState("idle"); // idle | loading | running | done
  const [result, setResult] = useState(null);
  const [runs, setRuns] = useState(0);
  const baseId = useId();

  if (!code.trim()) return null;

  async function run(e) {
    e.preventDefault();
    setState("loading");
    setResult(null);
    const started = performance.now();
    const inputs = calls.map((_, i) => values[i] ?? "");
    const res = await runPython(code, inputs, { onStarted: () => setState("running") });
    setResult({ ...res, ms: Math.round(performance.now() - started) });
    setRuns((n) => n + 1);
    setState("done");
  }

  const busy = state === "loading" || state === "running";
  const lines = result
    ? (result.output || (result.ok ? "(le programme n'a rien affiché)" : "")).split(
        "\n"
      )
    : [];

  return (
    <div className="py-run-wrap">
      <AnimatePresence initial={false} mode="wait">
        {!open ? (
          <m.button
            key="open"
            type="button"
            className="py-run-open"
            onClick={() => setOpen(true)}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.1 } }}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <span className="py-run-play" aria-hidden="true">
              ▶
            </span>
            Exécuter le Python
          </m.button>
        ) : (
          <m.form
            key="panel"
            className="py-run"
            onSubmit={run}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1, transition: SPRING_ENTER }}
            exit={{ height: 0, opacity: 0, transition: { duration: 0.18 } }}
          >
            <div className="py-run-inner">
              <div className="py-run-head">
                <span className="py-run-title">
                  <span className="py-run-logo" aria-hidden="true">
                    🐍
                  </span>
                  Exécuter le programme Python
                </span>
                <button
                  type="button"
                  className="py-run-close"
                  onClick={() => setOpen(false)}
                  aria-label="Fermer l'exécution"
                >
                  ×
                </button>
              </div>
              {calls.length > 0 ? (
                <div className="py-run-inputs">
                  {calls.map((call, i) => (
                    <m.label
                      key={i}
                      className="py-run-field"
                      htmlFor={`${baseId}-${i}`}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{
                        opacity: 1,
                        y: 0,
                        transition: { ...SPRING_HOVER, delay: 0.05 * i },
                      }}
                    >
                      <span className="py-run-label">
                        {call.prompt || `Valeur ${i + 1}`}
                      </span>
                      <input
                        id={`${baseId}-${i}`}
                        className="py-run-input"
                        value={values[i] ?? ""}
                        onChange={(e) =>
                          setValues((prev) => {
                            // By index, not prev.map: the runner can mount while the
                            // answer still streams, before every input() is there.
                            const next = [...prev];
                            next[i] = e.target.value;
                            return next;
                          })
                        }
                        placeholder="ta valeur"
                        autoComplete="off"
                      />
                    </m.label>
                  ))}
                </div>
              ) : (
                <p className="py-run-note">Ce programme ne lit aucune valeur.</p>
              )}
              <div className="py-run-actions">
                <m.button
                  type="submit"
                  className={`py-run-btn${busy ? " is-busy" : ""}`}
                  disabled={busy}
                  whileHover={busy ? undefined : { y: -2 }}
                  whileTap={busy ? undefined : { scale: 0.95 }}
                >
                  {busy && <span className="py-run-spinner" aria-hidden="true" />}
                  {state === "loading"
                    ? "Chargement de Python…"
                    : state === "running"
                      ? "Exécution…"
                      : // The triangle is decoration: bare, the button
                        // announces as "black right-pointing triangle
                        // Exécuter".
                        [
                          <span key="i" aria-hidden="true">
                            ▶{" "}
                          </span>,
                          "Exécuter",
                        ]}
                </m.button>
                {state === "loading" && (
                  <span className="py-run-hint">
                    La première fois, Python met quelques secondes à se charger.
                  </span>
                )}
              </div>

              {(busy || result) && (
                <m.div
                  key={runs}
                  className={`py-run-output${result ? (result.ok ? " is-ok" : " is-error") : ""}`}
                  role="status"
                  initial={{ opacity: 0, y: 6 }}
                  animate={
                    result && !result.ok
                      ? { opacity: 1, y: 0, x: [0, -6, 6, -3, 3, 0] }
                      : { opacity: 1, y: 0 }
                  }
                  transition={{ duration: 0.4 }}
                >
                  <div className="py-term-bar" aria-hidden="true">
                    <i />
                    <i />
                    <i />
                    <span>
                      {result
                        ? result.ok
                          ? `Terminé ✓ · ${result.ms} ms`
                          : "Erreur"
                        : "en cours…"}
                    </span>
                  </div>
                  <pre>
                    {lines.map((line, i) => (
                      <m.span
                        key={i}
                        className="py-term-line"
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: Math.min(i, 30) * 0.045, duration: 0.18 }}
                      >
                        {line || " "}
                      </m.span>
                    ))}
                    {!result && <span className="py-term-cursor" aria-hidden="true" />}
                  </pre>
                  {result?.error && (
                    <m.p
                      className="py-run-error"
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0, transition: { delay: 0.2 } }}
                    >
                      ⚠ {result.error}
                    </m.p>
                  )}
                </m.div>
              )}
            </div>
          </m.form>
        )}
      </AnimatePresence>
    </div>
  );
}
