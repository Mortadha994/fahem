// Shiki themes for the Fahem pseudocode grammar (algoPseudocode.json).
//
// Colors extend App.css's existing --accent/--ok/--warn tokens rather than
// reusing only those three for every category - ten categories sharing three
// hues would make the highlighting close to useless. New hues were picked to
// sit at a similar saturation/lightness to the app's existing palette so a
// highlighted line doesn't look like it belongs to a different product.
//
// Two separate theme objects (not one theme read twice) because Shiki's
// dual-theme output (see highlightAlgoLine.js) needs a named light and a
// named dark theme to emit --shiki-light/--shiki-dark per token.

export const algoLightTheme = {
  name: "algo-pseudocode-light",
  type: "light",
  settings: [
    // No-scope default: matches App.css's light --fg exactly, so an
    // unstyled token (anything not in the grammar's keyword lists, e.g.
    // variable names or excluded control-structure words) renders as
    // ordinary text instead of Shiki's generic grey fallback.
    { settings: { foreground: "#18181b" } },
    { scope: "keyword.operator.assignment.algo", settings: { foreground: "#3f6fb5" } },
    { scope: "keyword.operator.comparison.algo", settings: { foreground: "#7c5cbf" } },
    { scope: "keyword.operator.arithmetic.algo", settings: { foreground: "#0f7b6c" } },
    { scope: "keyword.operator.logical.algo", settings: { foreground: "#b35900" } },
    { scope: "support.function.io.algo", settings: { foreground: "#8a5a00" } },
    { scope: "support.function.math.algo", settings: { foreground: "#b3266b" } },
    { scope: "support.function.string.algo", settings: { foreground: "#2b7a94" } },
    { scope: "support.function.random.algo", settings: { foreground: "#9b3fa6" } },
    { scope: "storage.type.algo", settings: { foreground: "#55607a" } },
    { scope: "constant.language.boolean.algo", settings: { foreground: "#166534" } },
  ],
};

export const algoDarkTheme = {
  name: "algo-pseudocode-dark",
  type: "dark",
  settings: [
    // Matches App.css's dark --fg exactly - see algoLightTheme's default.
    { settings: { foreground: "#ececf1" } },
    { scope: "keyword.operator.assignment.algo", settings: { foreground: "#5b8ad6" } },
    { scope: "keyword.operator.comparison.algo", settings: { foreground: "#b39ddb" } },
    { scope: "keyword.operator.arithmetic.algo", settings: { foreground: "#4fd1b8" } },
    { scope: "keyword.operator.logical.algo", settings: { foreground: "#f0a860" } },
    { scope: "support.function.io.algo", settings: { foreground: "#f0c674" } },
    { scope: "support.function.math.algo", settings: { foreground: "#f28fc0" } },
    { scope: "support.function.string.algo", settings: { foreground: "#7fd4ea" } },
    { scope: "support.function.random.algo", settings: { foreground: "#e08fe6" } },
    { scope: "storage.type.algo", settings: { foreground: "#9aa3bd" } },
    { scope: "constant.language.boolean.algo", settings: { foreground: "#7ee2a8" } },
  ],
};
