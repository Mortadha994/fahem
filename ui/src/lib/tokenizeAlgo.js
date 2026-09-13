// One pass of lightweight highlighting for chapter-1 Algorithme and Python.
// Longest alternatives first, and strings before everything so a keyword
// inside quotes stays a string. Shared by AuthDemo and the landing page's
// LineByLine so both colour code the same way; kinds map to the .tk-* classes.
const TOKEN =
  /("[^"\n]*"?)|\b(Lire|Ecrire|Si|Alors|Sinon|Pour|Faire|mod|div)\b|\b(print|input|float|int)\b|(←|[*+/%=-])|(\d+)/g;
const KINDS = ["str", "kw", "fn", "op", "num"];

export function tokenize(text) {
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
