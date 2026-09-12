import { useRef, useState } from "react";
import AuthDemo from "./AuthDemo.jsx";
import Badge from "./ui/Badge.jsx";
import { SCOPE_LABEL } from "../config.js";

/*
 * The background is made of the syntax Fahem teaches, not generic shapes:
 * the assignment arrow, the chapter's keywords and operators, drifting at
 * different depths behind the glass. Positions are fixed, not random, so the
 * page looks the same on every load and nothing lands on the card's edge.
 */
const GLYPHS = [
  { t: "←", x: "6%", y: "14%", s: "4.5rem", d: "19s", b: "0px", o: 0.22 },
  { t: "Lire", x: "82%", y: "10%", s: "1.6rem", d: "23s", b: "1px", o: 0.16 },
  { t: "mod", x: "90%", y: "62%", s: "2.2rem", d: "21s", b: "0px", o: 0.18 },
  { t: "≠", x: "12%", y: "78%", s: "3rem", d: "25s", b: "2px", o: 0.14 },
  { t: "Ecrire", x: "70%", y: "88%", s: "1.4rem", d: "27s", b: "1px", o: 0.14 },
  { t: "div", x: "3%", y: "46%", s: "1.5rem", d: "22s", b: "3px", o: 0.12 },
  { t: "≤", x: "94%", y: "32%", s: "2.6rem", d: "24s", b: "2px", o: 0.14 },
  { t: "←", x: "58%", y: "4%", s: "2rem", d: "26s", b: "3px", o: 0.12 },
  { t: "Si", x: "40%", y: "92%", s: "1.8rem", d: "20s", b: "2px", o: 0.12 },
  { t: "*", x: "28%", y: "6%", s: "2.4rem", d: "28s", b: "4px", o: 0.1 },
];

/**
 * The frame around every signed-out screen: sign-in, account creation,
 * forgotten password, and the reset page.
 *
 * Layout after 21st.dev's "Sign In Split Screen"; the drifting background
 * after its "LiquidAurora"; the rotating edge after the "Shine Border"
 * technique; the cursor glow after the familiar "spotlight card". All plain
 * CSS on the app's tokens (see the showcase sections of App.css), and all of
 * it stops under prefers-reduced-motion.
 *
 * Pointer tracking writes CSS custom properties straight onto the elements
 * rather than going through React state: it fires on every mouse move, and
 * re-rendering the whole screen for a glow would be wasteful.
 *
 * The page's single <h1> is `title`, on the form side, because that is what
 * this screen is *for*; the panel's headline is supporting text.
 */
export default function AuthShell({ title, subtitle, children }) {
  const shellRef = useRef(null);
  const panelRef = useRef(null);
  // The demo holds still while the student is in the form.
  const [formActive, setFormActive] = useState(false);

  function handlePointerMove(event) {
    if (event.pointerType !== "mouse") return;
    const shell = shellRef.current;
    const box = shell.getBoundingClientRect();
    shell.style.setProperty("--mx", `${event.clientX - box.left}px`);
    shell.style.setProperty("--my", `${event.clientY - box.top}px`);

    const panel = panelRef.current;
    const p = panel.getBoundingClientRect();
    // -1..1 across the panel, clamped so the tilt eases off outside it.
    const nx = Math.max(-1, Math.min(1, ((event.clientX - p.left) / p.width) * 2 - 1));
    const ny = Math.max(-1, Math.min(1, ((event.clientY - p.top) / p.height) * 2 - 1));
    panel.style.setProperty("--tilt-x", `${(-ny * 4).toFixed(2)}deg`);
    panel.style.setProperty("--tilt-y", `${(nx * 5).toFixed(2)}deg`);
  }

  function handlePointerLeave() {
    panelRef.current?.style.setProperty("--tilt-x", "0deg");
    panelRef.current?.style.setProperty("--tilt-y", "0deg");
  }

  return (
    <div className="signin">
      <div className="aurora" aria-hidden="true">
        <span className="aurora-blob aurora-blob-1" />
        <span className="aurora-blob aurora-blob-2" />
        <span className="aurora-blob aurora-blob-3" />
        <span className="aurora-grid" />
        <div className="aurora-glyphs">
          {GLYPHS.map((g, i) => (
            <span
              key={i}
              style={{
                "--x": g.x,
                "--y": g.y,
                "--s": g.s,
                "--d": g.d,
                "--b": g.b,
                "--o": g.o,
                "--delay": `${-i * 1.7}s`,
              }}
            >
              {g.t}
            </span>
          ))}
        </div>
      </div>

      <div
        ref={shellRef}
        className="auth-shell surface"
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
      >
        <aside ref={panelRef} className="auth-panel" aria-label="Fahem en bref">
          <span className="auth-brand">
            {/* ← is the assignment arrow - the one symbol every Fahem answer
                is built around, and the one generic AI gets wrong. */}
            <span className="auth-mark" aria-hidden="true">
              <span className="auth-mark-arrow">←</span>
            </span>
            Fahem
          </span>

          <div className="auth-panel-body">
            <p className="auth-panel-title">
              Ton tuteur d'algorithmique,{" "}
              <span className="auth-gradient-text">dans la syntaxe de ton cours.</span>
            </p>
            <p className="auth-panel-lead">
              Colle l'énoncé d'un exercice : Fahem le résout avec ce que ton chapitre
              t'a appris — et te montre sur quelles parties du cours il s'appuie.
            </p>

            <AuthDemo paused={formActive} />

            {/* Phones only: the demo is hidden there, so the verdict it ends
                on is stated once, statically, in the strip. */}
            <Badge tone="success" className="auth-mobile-badge">
              ✓ Syntaxe du chapitre respectée
            </Badge>
          </div>

          <p className="auth-panel-foot">{SCOPE_LABEL}</p>
        </aside>

        <main
          className="auth-main"
          onFocus={() => setFormActive(true)}
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget))
              setFormActive(false);
          }}
        >
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
