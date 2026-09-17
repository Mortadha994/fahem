import { visit } from "unist-util-visit";
import { realignPairs } from "./alignAlgoTable.js";
import { algoText } from "./algoNotation.js";

/**
 * Locates the "Algorithme | Python" solution table (prompts.py §6) in the
 * parsed markdown tree and marks its Algorithme-column cells so the
 * Markdown component's th/td overrides can render them as a highlighted,
 * copyable code panel instead of an ordinary table cell.
 *
 * Runs at the mdast stage (before react-markdown ever builds React
 * elements) so cell text can be read directly off the tree via a plain
 * walk, rather than reverse-engineering it from already-rendered React
 * children later. Only structural markers are added here (hProperties,
 * the standard mdast->hast interop field) - no rendering, no Shiki. That
 * happens in the th/td overrides, which just read the props this plugin
 * stamped on.
 *
 * Other tables (the Objet|Nature/type declaration table, anything in the
 * GroundingStrip) never match the header-text check below and pass through
 * completely untouched.
 */
export default function remarkAlgoTable() {
  return (tree) => {
    visit(tree, "table", (table) => {
      const headerRow = table.children?.[0];
      if (!headerRow || headerRow.type !== "tableRow") return;

      const headerTexts = headerRow.children.map((cell) =>
        extractCellText(cell).trim().toLowerCase()
      );
      const algoIndex = headerTexts.indexOf("algorithme");
      const pythonIndex = headerTexts.indexOf("python");
      if (algoIndex === -1 || pythonIndex === -1) return;

      realignPythonColumn(table, algoIndex, pythonIndex);

      // Collected first so the header cell can carry the whole column's
      // text - the copy button lives in the header (one button for the
      // full listing), not one per row.
      const bodyLines = [];
      let headerCell = null;

      table.children.forEach((row, rowIndex) => {
        if (row.type !== "tableRow") return;
        const cell = row.children?.[algoIndex];
        if (!cell) return;

        if (rowIndex === 0) {
          headerCell = cell;
          return;
        }
        // Course notation (div, mod, ≠, ≤, ET...), even if the model wrote a
        // Python operator here - see lib/algoNotation.js. The copy button
        // gets the same text the student sees.
        const text = algoText(extractCellText(cell));
        bodyLines.push(text);

        cell.data ??= {};
        cell.data.hProperties = {
          ...cell.data.hProperties,
          "data-algo-col": "true",
          "data-algo-text": text,
        };
      });

      // The Python column as one program, for "Exécuter le Python"
      // (components/PythonRunner.jsx), read after the realignment above.
      const pythonLines = pythonProgram(
        table.children
          .slice(1)
          .filter((row) => row.type === "tableRow")
          .map((row) => ({
            algo: extractCellText(row.children?.[algoIndex] ?? { children: [] }),
            py: extractCellText(row.children?.[pythonIndex] ?? { children: [] }),
          }))
      );
      table.data ??= {};
      table.data.hProperties = {
        ...table.data.hProperties,
        "data-python-code": pythonLines.join("\n"),
      };

      if (headerCell) {
        headerCell.data ??= {};
        headerCell.data.hProperties = {
          ...headerCell.data.hProperties,
          "data-algo-header": "true",
          "data-algo-full-text": bodyLines.join("\n"),
        };
      }
    });
  };
}

/**
 * The Python column as a runnable program. A table cell loses its leading
 * spaces, so blocks are re-indented: a line ending with ":" opens one,
 * `else` / `elif` sit one level out, and the algorithm's "Fin si" / "Fin pour"
 * / "Fin tant que" row closes it.
 */
export function pythonProgram(rows) {
  const lines = [];
  let level = 0;
  for (const { algo, py } of rows) {
    if (/^\s*fin\s*(si|pour|tant)/i.test(algo) && !py.trim()) {
      level = Math.max(0, level - 1);
      continue;
    }
    for (const raw of py.split("\n")) {
      const line = raw.trim();
      if (!line) continue;
      const branch = /^(else|elif)\b/.test(line);
      const indent = branch ? Math.max(0, level - 1) : level;
      lines.push(`${"    ".repeat(indent)}${line}`);
      if (line.endsWith(":") && !branch) level += 1;
    }
  }
  return lines;
}

/**
 * When the model listed the Python lines out of step with the instructions,
 * re-pair them (lib/alignAlgoTable.js decides whether that can be done with
 * certainty). The Python cells' own nodes are moved, not rebuilt from text,
 * so inline code or emphasis inside them survives the move.
 */
function realignPythonColumn(table, algoIndex, pythonIndex) {
  const body = table.children.slice(1).filter((row) => row.type === "tableRow");
  const rows = body.map((row) => ({
    algo: extractCellText(row.children?.[algoIndex] ?? { children: [] }),
    py: extractCellText(row.children?.[pythonIndex] ?? { children: [] }),
  }));
  const paired = realignPairs(rows);
  if (!paired) return;

  // The non-empty Python cells' contents, in their original order - the same
  // queue realignPairs consumed.
  const contents = body
    .map((row) => row.children?.[pythonIndex])
    .filter((cell) => cell && extractCellText(cell).trim())
    .map((cell) => cell.children);

  body.forEach((row, i) => {
    const cell = row.children?.[pythonIndex];
    if (!cell) return;
    cell.children = paired[i] ? contents.shift() : [];
  });
}

/**
 * Plain text of a table cell's phrasing content, preserving a literal <br>
 * as a newline. generate.py's own comment notes the model sometimes packs
 * several instructions into one cell separated by <br> - without this, all
 * of them would run together into one unreadable tokenizer line.
 *
 * A hand-written walk rather than mdast-util-to-string: that utility drops
 * raw `html` nodes entirely, which is exactly the node type a literal <br>
 * parses as, so it would silently rejoin the lines it's supposed to split.
 */
function extractCellText(node) {
  if (node.type === "text") return node.value;
  if (node.type === "inlineCode") return node.value;
  if (node.type === "html") return /^<br\s*\/?>$/i.test(node.value.trim()) ? "\n" : "";
  if (Array.isArray(node.children)) {
    return node.children.map(extractCellText).join("");
  }
  return "";
}
