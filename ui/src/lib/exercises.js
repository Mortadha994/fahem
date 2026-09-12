import { loadSessions } from "./sessions.js";

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
  /^écrire\s+un\s+programme\s+(python\s+)?(qui\s+|que\s+|permettant\s+de\s+)?/i,
  /^ecrire\s+un\s+programme\s+(python\s+)?(qui\s+|que\s+|permettant\s+de\s+)?/i,
  /^écrire\s+un\s+algorithme\s+(qui\s+|permettant\s+de\s+)?/i,
  /^ecrire\s+un\s+algorithme\s+(qui\s+|permettant\s+de\s+)?/i,
];

// Left behind once an opening is stripped: "…du programme SOMME_CARRE" +
// "qui calcule…" would otherwise title a row "SOMME_CARRE qui calcule".
const CONNECTORS =
  /^(qui|que|qu['’]il|permettant\s+de|permet\s+de|permettant|de\s+lire|de\s+saisir)\s+/i;

// A program named in the statement ("« Substitution »", "intitulé Permutation",
// "du programme SOMME_CARRE") is the best title there is: it is what the
// exercise is called in class.
const NAMED =
  /(?:«\s*([A-Za-zÀ-ÿ_][\w\-À-ÿ ]{2,28}?)\s*»)|(?:\b(?:intitulé|programme|application)\s+([A-Z][A-Z0-9_]{2,}|[A-Z][\wÀ-ÿ]{2,}))/;

const MAX_TITLE = 52;

/**
 * A short subject line for an énoncé: the stock opening removed, cut before
 * the first worked example, trimmed at a word boundary.
 *
 * Falls back to the trimmed énoncé itself - a slightly long title is better
 * than an empty one if a future exercise is phrased unusually.
 */
export function exerciseTitle(question) {
  let text = String(question ?? "")
    .replace(/\s+/g, " ")
    .trim();
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
  text = text.replace(CONNECTORS, "");
  // First clause only: these statements chain with "puis", "et d'afficher"…
  text = text.split(/,\s|\spuis\s|\set\s+d['’]/i)[0].trim();
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
  const n = String(question ?? "").trim().length;
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
 * Read from the same localStorage history the sidebar uses - clicking an
 * exercise sends its text as the session's first student message, so an exact
 * match on that message is what "déjà commencé" means here. Browser-local,
 * like the history itself: it will not follow a student to another device, and
 * the page simply shows no markers then.
 *
 * Read-only: sessions.js owns that storage and is not touched.
 */
export function startedExerciseTexts() {
  const started = new Set();
  for (const session of loadSessions()) {
    const first = session?.messages?.find((m) => m.role === "user");
    if (first?.content) started.add(normalise(first.content));
  }
  return started;
}

/** Whether this exercise is among them. */
export function isStarted(question, startedTexts) {
  return startedTexts.has(normalise(question));
}
