import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
// Plus Jakarta Sans, the 21st.dev "Violet Dusk" theme's typeface - self-hosted
// from npm rather than loaded from Google Fonts, so there is no third-party
// request and it works offline. Variable weight, and the browser only
// downloads the unicode-range subset a page actually uses (Latin here).
import "@fontsource-variable/plus-jakarta-sans";
import App from "./App.jsx";
import { initTheme } from "./lib/theme.js";

// Follows the device's light/dark setting until the student picks one.
initTheme();

createRoot(document.getElementById("root")).render(
  <StrictMode>
    {/* BrowserRouter, not HashRouter: ui/nginx.conf already serves index.html
        for unknown paths, so a typed /chapitre/1 reaches the app rather than
        404ing, and the URLs stay clean. */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
