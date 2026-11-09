/**
 * Making a list of seven énoncés readable.
 *
 * The API gives one field per exercise, `question`: the full statement, one to
 * four lines of French, every one of them opening with some variant of "Ecrire
 * un programme qui…". Rendered as-is they are a wall of near-identical prose
 * (see the chapter page before this change). These helpers derive what a
 * student actually scans for - what it is about, how long it is, whether they
 * already started it - without touching the backend or its data.
 *
 * Derived, so occasionally a title reads a little flat. That is the trade
 * chosen deliberately over writing a title per exercise into the corpus: it
 * works for a chapter that has not been ingested yet, and nothing can drift
 * out of sync with the énoncé it came from.
 */

// The stock openings, longest first so "Ecrire un programme python qui" is
// stripped before the shorter "Ecrire un programme".
const OPENINGS = [
  /^écrire\s+l['’]algorithme\s+et\s+(le\s+)?(programme\s+)?python\s+(du\s+programme\s+|de\s+l['’]application\s+)?/i,
  /^ecrire\s+l['’]algorithme\s+et\s+(le\s+)?(programme\s+)?python\s+(du\s+programme\s+|de\s+l['’]application\s+)?/i,
  /^écrire\s+un\s+algorithme\s+et\s+sa\s+traduction\s+en\s+python\s+(intitulé\s+)?/i,
  /^ecrire\s+un\s+algorithme\s+et\s+sa\s+traduction\s+en\s+python\s+(intitulé\s+)?/i,
  /^[ée]crire\s+un\s+programme\s+(modulaire\s+)?(en\s+(langage\s+)?)?(python\s+)?(qui\s+|que\s+|permettant\s+de\s+)?/i,
  /^[ée]crire\s+un\s+algorithme\s+(modulaire\s+)?(qui\s+|permettant\s+de\s+)?/i,
];

// Left behind once an opening is stripped: "…du programme SOMME_CARRE" +
// "qui calcule…" would otherwise title a row "SOMME_CARRE qui calcule".
const CONNECTORS =
  /^(qui|que|qu['’]il|permettant\s+de|permet\s+de|permettant|de\s+lire|de\s+saisir)\s+/i;

// A program named in the statement ("« Substitution »", "intitulé Permutation",
// "du programme SOMME_CARRE") is the best title there is: it is what the
// exercise is called in class.
const NAMED =
  /(?:«\s*([A-Za-zÀ-ÿ_][\w\-À-ÿ ]{2,28}?)\s*»)|(?:\b(?:intitulé|programme|application)\s+(?!Python\b)([A-Z][A-Z0-9_]{2,}|[A-Z][\wÀ-ÿ]{2,}))/;

const MAX_TITLE = 52;

// "*Série N° 2 : Les chaînes de caractères*": the line every énoncé imported
// from a série sheet opens with. Left in, it became the title of every row.
const SERIE =
  /^\s*\**\s*s[ée]rie\s*n\s*°?\s*(\d+)\s*[:\-–]\s*([^*\n]*?)\s*\**\s*(?:\n|$)/i;

/**
 * The série an énoncé belongs to, and the énoncé without that heading line.
 * `serie` is null for exercises that were never part of one (chapter 1).
 */
export function splitSerie(question) {
  const text = String(question ?? "");
  const match = SERIE.exec(text);
  if (!match) return { serie: null, body: text.trim() };
  return {
    serie: { num: Number(match[1]), title: match[2].trim() },
    body: text.slice(match[0].length).trim(),
  };
}

/**
 * The énoncé as plain prose: Markdown emphasis and list dashes removed, which
 * otherwise show up literally ("« **traitement** »") in a title or preview.
 */
export function plainText(markdown) {
  return String(markdown ?? "")
    .replace(/(\*{1,3}|_{2})(\S(?:[^*]*?\S)?)\1/g, "$2")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/^\s*[-*•]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Exercises grouped by série, in their original order. Each item keeps its
 * number within the série, which is how a class refers to it ("série 2,
 * exercice 3"). A chapter without séries comes back as a single untitled group.
 */
export function groupBySerie(exercises = []) {
  const groups = [];
  for (const exercise of exercises) {
    const { serie } = splitSerie(exercise.question);
    const key = serie ? `serie-${serie.num}` : "none";
    let group = groups.at(-1);
    if (!group || group.key !== key) {
      group = { key, serie, items: [] };
      groups.push(group);
    }
    group.items.push({ exercise, number: group.items.length + 1 });
  }
  return groups;
}

/**
 * A short subject line for an énoncé: the stock opening removed, cut before
 * the first worked example, trimmed at a word boundary.
 *
 * Falls back to the trimmed énoncé itself - a slightly long title is better
 * than an empty one if a future exercise is phrased unusually.
 */
export function exerciseTitle(question) {
  let text = plainText(splitSerie(question).body);
  if (!text) return "Exercice";

  // Everything from "Exemple :" on is illustration, never the subject.
  text = text.split(/\s(?:Exemple|Exemples)\s*[:.]/i)[0];

  // A named program wins outright: "Substitution", "SOMME_CARRE".
  const named = NAMED.exec(text);
  if (named) {
    const name = (named[1] ?? named[2]).trim();
    return name.length > 2 ? name : text.slice(0, MAX_TITLE);
  }

  for (const opening of OPENINGS) {
    if (opening.test(text)) {
      text = text.replace(opening, "");
      break;
    }
  }
  // The opening's trailing connector goes with it, or the title reads as a
  // fragment ("qui calcule", "permet de lire…").
  text = text.replace(CONNECTORS, "").replace(/^[\s:–-]+/, "");
  // "Remplir un tableau T de n entiers, puis calculer leur somme": the input
  // step is the same across a whole série, the step after "puis" is what
  // tells these exercises apart.
  const [input, after] = text.split(/,?\s+puis\s+/i);
  if (after && /^(remplir|saisir|lire)\b/i.test(input)) text = after;
  // First clause only: these statements chain with "puis", "et d'afficher"…
  // unless that leaves a lone verb ("Trouver").
  const clause = text.split(/,\s|\spuis\s|\set\s+d['’]/i)[0].trim();
  if (clause.includes(" ")) text = clause;
  text = text.replace(/[.;:]+$/, "");

  // Cut at the last complete word, and never mid-connector, so a shortened
  // title still reads as a phrase rather than as a severed sentence.
  if (text.length > MAX_TITLE) {
    const cut = text.slice(0, MAX_TITLE);
    const lastSpace = cut.lastIndexOf(" ");
    let head = (lastSpace > 20 ? cut.slice(0, lastSpace) : cut).trim();
    head = head.replace(/\s+(et|de|du|des|la|le|les|un|une|d['’]|à|en|sur)$/i, "");
    text = `${head}…`;
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * How much work the statement describes, by its own length. A rough signal on
 * purpose: it says "this one is short" honestly without claiming to judge
 * difficulty, which the text cannot tell us.
 */
export function exerciseLength(question) {
  const n = plainText(splitSerie(question).body).length;
  if (n < 120) return "courte";
  if (n < 260) return "moyenne";
  return "longue";
}

/** Same normalisation on both sides of the "already started" comparison. */
function normalise(text) {
  return String(text ?? "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

/**
 * The set of énoncés this browser has already sent to the chat.
 *
 * Read from the student's own chat history (the sessions context) - clicking an
 * exercise sends its text as the session's first student message, so an exact
 * match on that message is what "déjà commencé" means here. Callers pass the
 * live list in.
 */
export function startedExerciseTexts(sessions = []) {
  const started = new Set();
  for (const session of sessions) {
    const first = session?.messages?.find((m) => m.role === "user");
    if (first?.content) started.add(normalise(first.content));
  }
  return started;
}

/** Whether this exercise is among them. */
export function isStarted(question, startedTexts) {
  return startedTexts.has(normalise(question));
}
