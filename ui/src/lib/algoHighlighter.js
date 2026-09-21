// The pure-JS regex engine (oniguruma-to-es under the hood) rather than the
// default WASM/oniguruma engine: no wasm fetch, no async init beyond promise
// resolution, and the grammar's patterns are plain lookaround + literal
// alternation - nothing that needs real Oniguruma-only features.
const LANG = "algo-pseudocode-fahem";
const THEMES = { light: "algo-pseudocode-light", dark: "algo-pseudocode-dark" };

let highlighter = null;
let loading = null;
const readyCallbacks = [];

/**
 * Shiki, its engine and the grammar are ~250 kB of the bundle and colour
 * nothing until an answer exists, so they are their own chunk, imported
 * here rather than at the top of the file. Warming still happens as early
 * as the browser is idle - by the time an answer finishes streaming
 * (seconds away) this has long since resolved; the not-ready path only
 * matters for a pathologically fast response or a very slow device.
 */
function warm() {
  loading ??= Promise.all([
    import("shiki/core"),
    import("shiki/engine/javascript"),
    import("../grammar/algoPseudocode.json"),
    import("../grammar/algoThemes.js"),
  ])
    .then(([core, engine, grammar, themes]) =>
      core.createHighlighterCore({
        langs: [grammar.default],
        themes: [themes.algoLightTheme, themes.algoDarkTheme],
        engine: engine.createJavaScriptRegexEngine(),
      })
    )
    .then((hl) => {
      highlighter = hl;
      readyCallbacks.splice(0).forEach((cb) => cb());
      return hl;
    })
    .catch(() => {
      // Uncoloured lines are still correct: a failed chunk is not an error
      // the student should ever see.
      loading = null;
      return null;
    });
  return loading;
}

if (typeof window !== "undefined") {
  const idle = window.requestIdleCallback ?? ((cb) => setTimeout(cb, 300));
  idle(() => warm());
}

/** Registers `cb` to run once the highlighter is ready. Fires immediately if it already is. */
export function onAlgoHighlighterReady(cb) {
  if (highlighter) return cb();
  readyCallbacks.push(cb);
  warm();
}

/**
 * Tokenizes one Algorithme-column line into segments carrying both theme
 * colors, so the same output works in light and dark mode without
 * re-tokenizing on a theme change: the CSS picks --algo-light or --algo-dark
 * from <html data-theme> (lib/theme.js), so switching themes recolours every
 * rendered line instantly with no JavaScript involved.
 *
 * Returns null when the highlighter isn't ready yet - callers fall back to
 * plain text, which is always correct, just temporarily uncolored.
 */
export function tokenizeAlgoLine(line) {
  if (!line) return null;
  if (!highlighter) {
    warm();
    return null;
  }
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
