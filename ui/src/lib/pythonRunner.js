/**
 * Runs the Python column of a solution in the browser, with Pyodide.
 *
 * Nothing reaches the server: the code runs in a Web Worker, so a student's
 * `while True` freezes nothing - the worker is terminated after RUN_TIMEOUT_MS
 * and a new one starts on the next run. Pyodide (~10 MB) is fetched from
 * jsDelivr the first time a student presses "Exécuter", never before.
 *
 * `input()` reads the values the student typed beside the program, in order,
 * and echoes them after their prompt the way a terminal would show them.
 */

export const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
export const RUN_TIMEOUT_MS = 5000;
const LOAD_TIMEOUT_MS = 90000;

const WORKER_SOURCE = `
let ready = null;
self.onmessage = async (event) => {
  const { id, code, inputs, url } = event.data;
  try {
    if (!ready) {
      importScripts(url + "pyodide.js");
      ready = loadPyodide({ indexURL: url });
    }
    const py = await ready;
    self.postMessage({ id, type: "started" });
    const out = [];
    py.setStdout({ batched: (s) => out.push(s) });
    py.setStderr({ batched: (s) => out.push(s) });
    const ns = py.globals.get("dict")();
    ns.set("__fahem_inputs", py.toPy(inputs));
    py.runPython(
      [
        "import builtins",
        "def __fahem_input(prompt=''):",
        "    if not __fahem_inputs:",
        "        raise EOFError('__fahem_missing_input__')",
        "    value = str(__fahem_inputs.pop(0))",
        "    print(str(prompt) + value)",
        "    return value",
        "builtins.input = __fahem_input",
      ].join("\\n"),
      { globals: ns }
    );
    try {
      py.runPython(code, { globals: ns });
      self.postMessage({ id, type: "done", output: out.join("\\n") });
    } catch (err) {
      self.postMessage({ id, type: "error", output: out.join("\\n"), error: String(err.message || err) });
    } finally {
      ns.destroy();
    }
  } catch (err) {
    ready = null;
    self.postMessage({ id, type: "load-error", error: String(err.message || err) });
  }
};
`;

let worker = null;
let nextId = 1;

function getWorker() {
  if (!worker) {
    const blob = new Blob([WORKER_SOURCE], { type: "text/javascript" });
    worker = new Worker(URL.createObjectURL(blob));
  }
  return worker;
}

function resetWorker() {
  worker?.terminate();
  worker = null;
}

/**
 * Run `code` with `inputs` (strings, in order). Resolves to
 * { ok, output, error, loading } - `error` already in the student's words.
 * `onStarted` fires once Pyodide is loaded and the program itself starts.
 */
export function runPython(code, inputs = [], { onStarted } = {}) {
  return new Promise((resolve) => {
    const id = nextId++;
    const w = getWorker();
    let runTimer = null;
    const loadTimer = setTimeout(() => {
      finish({
        ok: false,
        output: "",
        error: "Impossible de charger Python. Vérifie ta connexion et réessaie.",
      });
      resetWorker();
    }, LOAD_TIMEOUT_MS);

    function finish(result) {
      clearTimeout(loadTimer);
      clearTimeout(runTimer);
      w.removeEventListener("message", onMessage);
      resolve(result);
    }

    function onMessage(event) {
      const msg = event.data;
      if (msg.id !== id) return;
      if (msg.type === "started") {
        clearTimeout(loadTimer);
        onStarted?.();
        runTimer = setTimeout(() => {
          resetWorker();
          finish({
            ok: false,
            output: "",
            error: `Le programme a dépassé ${RUN_TIMEOUT_MS / 1000} secondes : il tourne peut-être sans fin.`,
          });
        }, RUN_TIMEOUT_MS);
      } else if (msg.type === "done") {
        finish({ ok: true, output: msg.output, error: null });
      } else if (msg.type === "error") {
        finish({ ok: false, output: msg.output, error: explainPythonError(msg.error) });
      } else if (msg.type === "load-error") {
        resetWorker();
        finish({
          ok: false,
          output: "",
          error: "Impossible de charger Python. Vérifie ta connexion et réessaie.",
        });
      }
    }

    w.addEventListener("message", onMessage);
    w.postMessage({ id, code, inputs, url: PYODIDE_URL });
  });
}

/** The input() calls of a program, in order: [{ prompt }]. */
export function inputCalls(code) {
  const calls = [];
  const re = /\binput\s*\(([^()]*)\)/g;
  let match;
  while ((match = re.exec(code))) {
    // "Saisir la moyenne de " + mat1 + " : "  ->  Saisir la moyenne de ‹mat1› :
    const prompt = match[1]
      .split("+")
      .map((part) => {
        const p = part.trim();
        const quoted = /^(["'])(.*)\1$/.exec(p);
        return quoted ? quoted[2] : p ? `‹${p}›` : "";
      })
      .join("")
      .replace(/\s+/g, " ")
      .trim();
    calls.push({ prompt });
  }
  return calls;
}

/** A Python traceback as one sentence a student can act on. */
export function explainPythonError(raw = "") {
  const text = String(raw);
  const last =
    text
      .trim()
      .split("\n")
      .filter((l) => l.trim())
      .pop() ?? text;
  const line = [...text.matchAll(/line (\d+)/g)].pop()?.[1];
  const at = line ? ` (ligne ${line})` : "";
  let m;
  if (last.includes("__fahem_missing_input__"))
    return "Le programme demande plus de valeurs que tu n'en as donné : ajoute une valeur.";
  if ((m = /invalid literal for int\(\) with base 10: '(.*)'/.exec(last)))
    return m[1] === ""
      ? `Une valeur est vide alors que le programme attend un entier${at}.`
      : `« ${m[1]} » n'est pas un nombre entier : int() attend un entier${at}.`;
  if ((m = /could not convert string to float: '(.*)'/.exec(last)))
    return m[1] === ""
      ? `Une valeur est vide alors que le programme attend un nombre${at}.`
      : `« ${m[1]} » n'est pas un nombre : float() attend un nombre (avec un point : 12.5)${at}.`;
  if (last.startsWith("ZeroDivisionError")) return `Division par zéro${at}.`;
  if ((m = /NameError: name '(.*)' is not defined/.exec(last)))
    return `La variable « ${m[1]} » est utilisée sans avoir reçu de valeur${at}.`;
  if (last.startsWith("SyntaxError") || last.startsWith("IndentationError"))
    return `Erreur de syntaxe Python${at} : ${last.replace(/^\w+Error:\s*/, "")}`;
  if (last.startsWith("TypeError"))
    return `Opération impossible entre ces types${at} : ${last.replace(/^TypeError:\s*/, "")}`;
  return last.length > 200 ? `${last.slice(0, 200)}…` : last;
}
