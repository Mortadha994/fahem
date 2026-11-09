/**
 * Tunisian algorithm notation for one Algorithme-column line - the browser
 * twin of app/grading/algo_notation.py (same rules, same tests' cases).
 *
 * The course writes `div`, `mod`, `=`, `≠`, `≤`, `≥`, `←`, `ET`, `OU`, `NON`,
 * `Vrai`, `Faux`; Python writes `//`, `%`, `==`, `!=`, `<=`, `>=`, `<-`-style
 * arrows, `and`, `or`, `not`, `True`, `False`. The prompts forbid the Python
 * spellings in the Algorithme column, but when the model slips, a student
 * copying `Res ← X // Y` into their exercise book is marked wrong - so the
 * column is displayed (and copied) in course notation regardless.
 *
 * Text inside double quotes is never touched: `Ecrire ("Remise de 5 %")`.
 * Used by remarkAlgoTable.js, so it covers the streamed answer and every
 * saved discussion alike; the Python column and the prose are left as written.
 */

const OPERATORS = [
  [/\s*\/\/\s*/g, " div "],
  [/\s*%\s*/g, " mod "],
  [/\s*==\s*/g, " = "],
  [/\s*!=\s*/g, " ≠ "],
  [/\s*<=\s*/g, " ≤ "],
  [/\s*>=\s*/g, " ≥ "],
  [/\s*<-\s*/g, " ← "],
  [/\band\b/g, "ET"],
  [/\bor\b/g, "OU"],
  [/\bnot\b/g, "NON"],
  [/\bTrue\b/g, "Vrai"],
  [/\bFalse\b/g, "Faux"],
];

function fixCode(segment) {
  let count = 0;
  let out = segment;
  for (const [pattern, replacement] of OPERATORS) {
    out = out.replace(pattern, () => {
      count += 1;
      return replacement;
    });
  }
  if (!count) return [segment, 0];
  const leading = out.match(/^ */)[0];
  const body = out.slice(leading.length).replace(/(?<=\S) {2,}(?=\S)/g, " ");
  return [leading + body, count];
}

/** [line in course notation, number of operators rewritten]. */
export function toAlgoNotation(line) {
  let count = 0;
  const pieces = String(line).split(/("[^"]*"?)/);
  const out = pieces.map((piece) => {
    if (piece.startsWith('"')) return piece;
    const [fixed, n] = fixCode(piece);
    count += n;
    return fixed;
  });
  const result = out.join("");
  return [count ? result.trimEnd() : result, count];
}

/** Several lines (a cell with <br>s, or the whole column for copying). */
export const algoText = (text) =>
  String(text)
    .split("\n")
    .map((line) => toAlgoNotation(line)[0])
    .join("\n");

// A remark about a declaration table the solution does not need ("Aucun type
// nouveau n'est nécessaire, donc pas de T.D.N.T."): the browser twin of
// strip_absent_table_notes in app/grading/algo_notation.py. One line, never a
// table row, never inside a code fence.
const ABSENCE =
  /aucun|aucune|pas d[e']|pas besoin|sans |néant|neant|inutile|n[’']est (?:pas )?(?:nécessaire|necessaire|utile)|n[’']y a pas/i;
const TABLE_WORDS =
  /t\.d\.n\.t|t\.d\.o\.l|tdnt|tdol|nouveaux? types?|types? nouveaux?|objets? locau[xl]|types? non primitifs?/i;

export function stripAbsentTableNotes(markdown) {
  const text = String(markdown);
  let inFence = false;
  let removed = 0;
  const kept = [];
  for (const line of text.split("\n")) {
    const s = line.trim();
    if (s.startsWith("```")) inFence = !inFence;
    else if (
      !inFence &&
      s &&
      !s.startsWith("|") &&
      s.length <= 300 &&
      ABSENCE.test(s) &&
      TABLE_WORDS.test(s)
    ) {
      removed += 1;
      continue;
    }
    kept.push(line);
  }
  return removed ? kept.join("\n").replace(/\n{3,}/g, "\n\n") : text;
}
