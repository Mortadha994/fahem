import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import remarkAlgoTable from "../lib/remarkAlgoTable.js";
import { AlgoHeaderCell, AlgoBodyCell } from "./AlgoCode.jsx";

// Highlighting is deliberately tag-only (`detect: false`, the default, set
// explicitly here so nobody "fixes" it later).
//
// Checked against real output before choosing: across all seven test answers
// there are 12 fenced blocks and every one is UNTAGGED, and every one is a
// program-output transcript ("La somme des carrés est 14"), not source. With
// detection on, highlight.js would guess a language and colourise that output
// as if it were code.
//
// The actual code lives in markdown tables - the two-column Algorithme|Python
// layout - which a highlighter never touches. The Algorithme column is not a
// language highlight.js knows anyway: `Lire (x)`, `Ecrire`, `←`, `div`, `mod`.
// So tables are styled in CSS instead, and only an explicitly tagged block
// (```python) gets highlighted.
const REHYPE_PLUGINS = [[rehypeHighlight, { detect: false, ignoreMissing: true }]];

// remarkAlgoTable runs before rendering and marks the Algorithme column of
// the Algorithme|Python solution table (prompts.py §6); AlgoHeaderCell/
// AlgoBodyCell read those markers and are the only th/td instances that
// render any differently - every other table (declaration table,
// GroundingStrip) is untouched. See remarkAlgoTable.js and AlgoCode.jsx.
const REMARK_PLUGINS = [remarkGfm, remarkAlgoTable];
const COMPONENTS = { th: AlgoHeaderCell, td: AlgoBodyCell };

export default function Markdown({ children }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={REMARK_PLUGINS}
        rehypePlugins={REHYPE_PLUGINS}
        components={COMPONENTS}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
