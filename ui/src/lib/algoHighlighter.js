import { createHighlighterCore } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";
import grammar from "../grammar/algoPseudocode.json";
import { algoLightTheme, algoDarkTheme } from "../grammar/algoThemes.js";

// The pure-JS regex engine (oniguruma-to-es under the hood) rather than the
// default WASM/oniguruma engine: no wasm fetch, no async init beyond promise
// resolution, and the grammar's patterns are plain lookaround + literal
// alternation - nothing that needs real Oniguruma-only features.
const LANG = "algo-pseudocode-fahem";
const THEMES = { light: "algo-pseudocode-light", dark: "algo-pseudocode-dark" };

let highlighter = null;
const readyCallbacks = [];

const highlighterPromise = createHighlighterCore({
  langs: [grammar],
  themes: [algoLightTheme, algoDarkTheme],
  engine: createJavaScriptRegexEngine(),
}).then((hl) => {
  highlighter = hl;
  readyCallbacks.splice(0).forEach((cb) => cb());
  return hl;
});

// Warm at module load - mirrors api.py's lifespan warmup for the embedding
// model. By the time any answer finishes streaming (seconds away), this has
// long since resolved; the not-ready path only matters for a pathologically
// fast response or a very slow device.
void highlighterPromise;

/** Registers `cb` to run once the highlighter is ready. Fires immediately if it already is. */
export function onAlgoHighlighterReady(cb) {
  if (highlighter) cb();
  else readyCallbacks.push(cb);
}

/**
 * Tokenizes one Algorithme-column line into segments carrying both theme
 * colors, so the same output works in light and dark mode without
 * re-tokenizing on a theme change (the app follows prefers-color-scheme via
 * CSS, not a JS-visible state, so re-tokenizing on theme change isn't
 * practical anyway).
 *
 * Returns null when the highlighter isn't ready yet - callers fall back to
 * plain text, which is always correct, just temporarily uncolored.
 */
export function tokenizeAlgoLine(line) {
  if (!highlighter || !line) return null;
  const [tokens] = highlighter.codeToTokensWithThemes(line, {
    lang: LANG,
    themes: THEMES,
  });
  return tokens.map((t) => ({
    text: t.content,
    light: t.variants.light?.color,
    dark: t.variants.dark?.color,
  }));
}
