import { useEffect, useState } from "react";
import { onAlgoHighlighterReady, tokenizeAlgoLine } from "../lib/algoHighlighter.js";

/**
 * th/td overrides passed to react-markdown (see Markdown.jsx). Only cells
 * remarkAlgoTable.js marked - the Algorithme column of the Algorithme|Python
 * solution table - render any differently here; every other table (the
 * Objet|Nature/type declaration table, GroundingStrip's tables) has no
 * data-algo-* props and falls through to a plain <th>/<td>.
 */

export function AlgoHeaderCell({
  node: _node,
  children,
  "data-algo-header": isAlgoHeader,
  "data-algo-full-text": fullText,
  ...rest
}) {
  if (!isAlgoHeader) return <th {...rest}>{children}</th>;
  return (
    <th {...rest} className="algo-col-header">
      <div className="algo-header-bar">
        <span className="algo-header-label">{children}</span>
        <CopyButton getText={() => fullText ?? ""} />
      </div>
    </th>
  );
}

export function AlgoBodyCell({
  node: _node,
  children,
  "data-algo-col": isAlgoCol,
  "data-algo-text": text,
  ...rest
}) {
  if (!isAlgoCol) return <td {...rest}>{children}</td>;
  return (
    <td {...rest} className="algo-col-cell">
      <AlgoLine text={text ?? ""} />
    </td>
  );
}

/**
 * One cell's content, tokenized. A cell can hold several instructions
 * joined by a literal <br> (remarkAlgoTable.js turns each into "\n") - each
 * segment is tokenized on its own line and rejoined with a real <br/>.
 */
function AlgoLine({ text }) {
  const [, forceRender] = useState(0);

  useEffect(() => onAlgoHighlighterReady(() => forceRender((n) => n + 1)), []);

  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const tokens = tokenizeAlgoLine(line);
        return (
          <span key={i} className="algo-line">
            {i > 0 && <br />}
            {tokens
              ? tokens.map((t, j) => (
                  <span
                    key={j}
                    style={{ "--algo-light": t.light, "--algo-dark": t.dark }}
                    className="algo-tok"
                  >
                    {t.text}
                  </span>
                ))
              : line}
          </span>
        );
      })}
    </>
  );
}

/** Copies plain text via the Clipboard API; swaps to a checkmark for 1.5s. */
function CopyButton({ getText }) {
  const [copied, setCopied] = useState(false);

  async function handleClick() {
    try {
      await navigator.clipboard.writeText(getText());
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API can be denied (permissions, insecure context); the
      // button just doesn't confirm rather than throwing in the UI.
    }
  }

  return (
    <button
      type="button"
      className="algo-copy-btn"
      onClick={handleClick}
      aria-label={copied ? "Copié" : "Copier le pseudocode"}
      title={copied ? "Copié" : "Copier le pseudocode"}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
    </button>
  );
}

function CopyIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
