/**
 * Re-pairs the rows of an Algorithme | Python solution table when the model
 * listed the Python lines out of step with the instructions.
 *
 * Seen in real output: every Python line packed into the first rows, so
 * "Algorithme Somme_Produit" sat beside `a = int(input(...))` and
 * "somme ← a + b" beside nothing - which defeats a table whose whole point is
 * reading each instruction next to its translation. app/llm/prompts.py now asks for
 * row-by-row pairing; this is the safety net for answers that still drift,
 * and for answers already saved in a student's history.
 *
 * Deliberately conservative. It only re-pairs when every Python line can be
 * matched, in order, to an instruction of the same kind (a Lire to an input,
 * an assignment to an assignment, an Ecrire to a print, a Si to an if), with
 * nothing left over. Anything it cannot place with certainty - an unknown
 * instruction, a multi-line cell, a leftover line - and it returns null, and
 * the table is shown exactly as the model wrote it. A wrong "fix" would be
 * worse than the original.
 *
 * Works on plain strings so it can be tested on its own; remarkAlgoTable.js
 * applies the result to the markdown tree.
 */

const clean = (s) => String(s ?? "").trim();

/** The kind of one Algorithme instruction. */
export function algoKind(text) {
  const t = clean(text);
  if (!t) return "empty";
  if (/^(Algorithme\b|D[ée]but$|Fin$)/i.test(t)) return "frame";
  if (/^Lire\s*\(/i.test(t)) return "read";
  if (
    /^(Si|Sinon|Fin\s*Si|Pour|Fin\s*Pour|Tant\s*que|Fin\s*Tant\s*que|R[ée]p[ée]ter|Jusqu)/i.test(
      t
    )
  )
    return "control";
  if (/^Ecrire\s*\(/i.test(t)) return "write";
  if (/←|<-/.test(t)) return "assign";
  return "other";
}

/** The kind of one Python line. */
export function pyKind(text) {
  const t = clean(text);
  if (!t) return "empty";
  if (/\binput\s*\(/.test(t)) return "read";
  if (/^(if|elif|else|for|while)\b/.test(t)) return "control";
  if (/^print\s*\(/.test(t)) return "write";
  if (/^[A-Za-z_][\w[\]., ]*\s*[+\-*/%]?=(?!=)/.test(t)) return "assign";
  return "other";
}

/** Does a row already pair an instruction with a translation of its kind? */
function rowFits(algo, py) {
  const a = algoKind(algo);
  const p = pyKind(py);
  if (a === "frame") return p === "empty";
  // A prompt message may be folded into the next Lire's input(...).
  if (a === "write") return p === "write" || p === "empty";
  return a === p;
}

/**
 * @param {{algo: string, py: string}[]} rows body rows, header excluded
 * @returns {string[] | null} the Python text for each row, re-paired, or
 *   null when the table is already aligned or cannot be re-paired safely.
 */
export function realignPairs(rows) {
  if (!Array.isArray(rows) || rows.length < 3) return null;
  // Multi-instruction cells (<br>) cannot be paired one-to-one.
  if (rows.some((r) => /\n/.test(clean(r.algo)) || /\n/.test(clean(r.py)))) return null;

  const misfits = rows.filter((r) => !rowFits(r.algo, r.py)).length;
  if (misfits < 2) return null;

  const queue = rows.map((r) => clean(r.py)).filter(Boolean);
  const out = [];
  for (let i = 0; i < rows.length; i++) {
    const kind = algoKind(rows[i].algo);
    const head = queue[0];
    const headKind = head === undefined ? "none" : pyKind(head);

    if (kind === "frame" || kind === "empty") {
      out.push("");
    } else if (kind === "write") {
      // A print pairs with this Ecrire; an input waiting next means this
      // Ecrire is the prompt for the Lire that follows, folded into input().
      if (headKind === "write") out.push(queue.shift());
      else if (headKind === "read" && algoKind(rows[i + 1]?.algo) === "read")
        out.push("");
      else return null;
    } else if (kind === "read" || kind === "assign" || kind === "control") {
      if (headKind !== kind) return null;
      out.push(queue.shift());
    } else {
      return null;
    }
  }
  if (queue.length > 0) return null;
  return out;
}
