import { useId, useMemo, useState } from "react";
import { inputCalls, runPython } from "../lib/pythonRunner.js";

/**
 * "▶ Exécuter le Python", under a solution table: one field per input() of
 * the program (labelled with its prompt), then the output as a terminal would
 * show it. The program runs in the browser (lib/pythonRunner.js).
 */
export default function PythonRunner({ code }) {
  const calls = useMemo(() => inputCalls(code), [code]);
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState(() => calls.map(() => ""));
  const [state, setState] = useState("idle"); // idle | loading | running | done
  const [result, setResult] = useState(null);
  const baseId = useId();

  if (!code.trim()) return null;

  async function run(e) {
    e.preventDefault();
    setState("loading");
    setResult(null);
    const inputs = calls.map((_, i) => values[i] ?? "");
    const res = await runPython(code, inputs, { onStarted: () => setState("running") });
    setResult(res);
    setState("done");
  }

  if (!open) {
    return (
      <button type="button" className="py-run-open" onClick={() => setOpen(true)}>
        <span aria-hidden="true">▶</span> Exécuter le Python
      </button>
    );
  }

  const busy = state === "loading" || state === "running";
  return (
    <form className="py-run" onSubmit={run}>
      <div className="py-run-head">
        <span className="py-run-title">Exécuter le programme Python</span>
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
            <label key={i} className="py-run-field" htmlFor={`${baseId}-${i}`}>
              <span className="py-run-label">{call.prompt || `Valeur ${i + 1}`}</span>
              <input
                id={`${baseId}-${i}`}
                className="py-run-input"
                value={values[i] ?? ""}
                onChange={(e) =>
                  setValues((prev) =>
                    prev.map((v, j) => (j === i ? e.target.value : v))
                  )
                }
                placeholder="ta valeur"
                autoComplete="off"
                inputMode="decimal"
              />
            </label>
          ))}
        </div>
      ) : (
        <p className="py-run-note">Ce programme ne lit aucune valeur.</p>
      )}
      <div className="py-run-actions">
        <button type="submit" className="py-run-btn" disabled={busy}>
          {state === "loading"
            ? "Chargement de Python…"
            : state === "running"
              ? "Exécution…"
              : "▶ Exécuter"}
        </button>
        {state === "loading" && (
          <span className="py-run-hint">
            La première fois, Python met quelques secondes à se charger.
          </span>
        )}
      </div>
      {result && (
        <div className="py-run-output" role="status">
          <pre>
            {result.output || (result.ok ? "(le programme n'a rien affiché)" : "")}
          </pre>
          {result.error && <p className="py-run-error">⚠ {result.error}</p>}
        </div>
      )}
    </form>
  );
}
