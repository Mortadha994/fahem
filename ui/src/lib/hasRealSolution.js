import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import { visit } from "unist-util-visit";

/**
 * Decides whether a completed answer has an actual Algorithme-column
 * solution worth showing the constraint-checker badge for.
 *
 * Why this exists: prompts.py now has the model reply with a short question
 * instead of the 5-section template when the student's message isn't a real
 * problem ("hi", empty, off-topic) - see its "pas de problème réel" branch.
 * check_constraints() still runs on whatever text comes back and, having
 * nothing to flag, reports zero violations - which is not the same thing as
 * "the syntax was verified". A response with no Algorithme content at all
 * trivially passes for the same reason an unproctored exam has no wrong
 * answers. Message.jsx uses this to decide whether the badge (in any of its
 * three states - pending, clean, warned) should render at all.
 *
 * A parse-only pass (unified().parse, not .process()): this only needs the
 * mdast tree to look for the table, not rendered output. remark-gfm is
 * still required at parse time - GFM tables aren't in the CommonMark core
 * grammar remark-parse implements alone.
 */
export function hasRealAlgorithmeSolution(markdownText) {
  if (!markdownText) return false;

  const tree = unified().use(remarkParse).use(remarkGfm).parse(markdownText);
  let found = false;

  visit(tree, "table", (table) => {
    if (found) return;
    const headerRow = table.children?.[0];
    if (!headerRow || headerRow.type !== "tableRow") return;

    const headerTexts = headerRow.children.map((cell) =>
      extractCellText(cell).trim().toLowerCase()
    );
    const algoIndex = headerTexts.indexOf("algorithme");
    if (algoIndex === -1 || headerTexts.indexOf("python") === -1) return;

    for (const row of table.children.slice(1)) {
      const cell = row.children?.[algoIndex];
      if (!cell) continue;
      if (isRealContent(extractCellText(cell))) {
        found = true;
        break;
      }
    }
  });

  return found;
}

// A cell only counts as real content once it clears both: not just dashes/
// whitespace (the placeholder the old forced template used - "Objet: –
// Nature/type: –"), and not one of the model's own declining phrasings for
// "no problem was given" ("Aucune solution ne peut être écrite tant que...").
// These aren't near-misses to fine-tune against a corpus; a real Algorithme
// line is imperative ("Lire (x)", "y ← ..."), so any of these words in it
// would already be a strange answer regardless of this check.
const DASH_ONLY_RE = /^[\s\-–—.:]*$/;
const PLACEHOLDER_RE =
  /\b(aucun|aucune|impossible|tant que|n['’]est pas connu|ne peut|inconnue?)\b/i;

function isRealContent(text) {
  const trimmed = text.trim();
  if (!trimmed || DASH_ONLY_RE.test(trimmed)) return false;
  return !PLACEHOLDER_RE.test(trimmed);
}

// Same walk as remarkAlgoTable.js's extractCellText, kept as its own copy
// rather than a shared import: that one runs on every render of a streaming
// answer to mark cells for the highlighter; this one runs once, after the
// answer is complete, to decide whether the badge should appear at all -
// different lifecycles, so coupling them isn't worth it for ~10 lines.
function extractCellText(node) {
  if (node.type === "text") return node.value;
  if (node.type === "inlineCode") return node.value;
  if (node.type === "html") return /^<br\s*\/?>$/i.test(node.value.trim()) ? "\n" : "";
  if (Array.isArray(node.children)) return node.children.map(extractCellText).join("");
  return "";
}
