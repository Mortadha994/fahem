import { Link } from "react-router-dom";
import ThemeToggle from "./ThemeToggle.jsx";

/**
 * The frame around every signed-out screen: sign-in, account creation,
 * forgotten password, and the reset page.
 *
 * Deliberately plain: one centred card with the wordmark, the heading and
 * the form. It used to repeat the landing page beside the form (pitch,
 * animated demo, aurora background, glowing edge), but a student reaches
 * this screen from the landing page, having already read all of that - here
 * the only job left is signing in, so nothing else competes with the form.
 *
 * The page's single <h1> is `title`.
 */
export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="signin signin-simple">
      {/* Top-right corner, outside the card: the choice belongs to the page,
          not to the form. */}
      <ThemeToggle className="auth-theme" />

      <div className="auth-shell surface">
        <main className="auth-main">
          {/* The brand is the way back out. Every screen wearing this shell is
              signed out, so "/" is the landing page, never the app. */}
          <Link className="auth-brand" to="/" aria-label="Fahem — retour à l'accueil">
            {/* ← is the assignment arrow - the one symbol every Fahem answer
                is built around. */}
            <span className="auth-mark" aria-hidden="true">
              <span className="auth-mark-arrow">←</span>
            </span>
            Fahem
          </Link>
          <header className="auth-head">
            <h1 className="auth-title">{title}</h1>
            {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          </header>
          {children}
        </main>
      </div>
    </div>
  );
}
