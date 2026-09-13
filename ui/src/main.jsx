import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
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
