import { visit } from "unist-util-visit";

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
        bodyLines.push(extractCellText(cell));

        cell.data ??= {};
        cell.data.hProperties = {
          ...cell.data.hProperties,
          "data-algo-col": "true",
          "data-algo-text": extractCellText(cell),
        };
      });

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
