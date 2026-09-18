import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useScroll, useSpring, useTransform } from "motion/react";
import * as m from "motion/react-m";

/**
 * The hero: a dark, lit stage with the product on it.
 *
 * The visual is not a screenshot but the real interface rebuilt in markup -
 * the question, the Algorithme | Python answer, and the three moments that
 * make Fahem different (the guided step, the verdict, the program running).
 * They drift at different speeds as the page scrolls (useScroll +
 * useTransform, GPU-friendly transforms only), so the stage has depth
 * without a single image to download.
 *
 * Under prefers-reduced-motion, MotionConfig (Landing.jsx) drops the
 * transforms and everything simply sits where it lands.
 */

const EASE_OUT = { type: "spring", visualDuration: 0.7, bounce: 0.18 };

const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { ...EASE_OUT, delay } },
});

export default function Hero({ exercises }) {
  const stage = useRef(null);
  const { scrollYProgress } = useScroll({
    target: stage,
    offset: ["start start", "end start"],
  });
  const soft = useSpring(scrollYProgress, { stiffness: 120, damping: 30, mass: 0.4 });
  // Each layer leaves at its own speed: the window barely, the cards sooner.
  const windowY = useTransform(soft, [0, 1], [0, -40]);
  const frontY = useTransform(soft, [0, 1], [0, -130]);
  const backY = useTransform(soft, [0, 1], [0, -80]);
  const glow = useTransform(soft, [0, 1], [1, 0.35]);

  // On a phone the cards are laid out under the window rather than floating
  // over it (landing.css), so the parallax would simply push them into it.
  const [stacked, setStacked] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 720px)");
    const apply = () => setStacked(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);
  const drift = (value) => (stacked ? undefined : value);

  return (
    <section className="fx-hero" ref={stage}>
      <div className="fx-hero-sky" aria-hidden="true">
        <m.span className="fx-aurora fx-aurora-1" style={{ opacity: glow }} />
        <m.span className="fx-aurora fx-aurora-2" style={{ opacity: glow }} />
        <m.span className="fx-aurora fx-aurora-3" style={{ opacity: glow }} />
        <span className="fx-grid" />
      </div>

      <div className="fx-hero-inner">
        <div className="fx-hero-copy">
          <m.h1 className="fx-h1" {...rise(0.06)}>
            Ton prof d'algo,
            <br />
            <span className="fx-h1-grad">à 22 h, un dimanche.</span>
          </m.h1>

          <m.p className="fx-hero-lead" {...rise(0.12)}>
            Tu bloques sur un exercice ? Fahem te met sur la piste, corrige ce que{" "}
            <b>tu</b> écris, et répond dans la notation de ton manuel : <code>←</code>,{" "}
            <code>div</code>, <code>Lire</code>, <code>Ecrire</code>.
          </m.p>

          <m.div className="fx-hero-cta" {...rise(0.18)}>
            <Link
              className="fx-btn fx-btn-primary"
              to="/connexion"
              state={{ authMode: "signup" }}
            >
              Commencer — c'est gratuit
            </Link>
            <a className="fx-btn fx-btn-ghost" href="#essayer">
              <span aria-hidden="true">▶</span> Voir un exercice résolu
            </a>
          </m.div>

          <m.ul className="fx-hero-trust" {...rise(0.24)}>
            <li>Sans carte bancaire</li>
            <li>Rien à installer</li>
            <li>
              {exercises ? `${exercises} exercices corrigés` : "Programme tunisien"}
            </li>
          </m.ul>
        </div>

        {/* --- the product, rebuilt --------------------------------------- */}
        <div className="fx-stage">
          <m.div
            className="fx-window"
            style={{ y: drift(windowY) }}
            initial={{ opacity: 0, y: 40, rotateX: 12, scale: 0.96 }}
            animate={{
              opacity: 1,
              y: 0,
              rotateX: 0,
              scale: 1,
              transition: { ...EASE_OUT, delay: 0.1, visualDuration: 0.9 },
            }}
          >
            <div className="fx-window-bar" aria-hidden="true">
              <i />
              <i />
              <i />
              <span>Fahem — chapitre 1</span>
            </div>

            <div className="fx-window-body">
              <p className="fx-ask">
                Écrire un algorithme qui lit un entier N de deux chiffres et affiche ses
                chiffres.
              </p>

              <div className="fx-answer">
                <p className="fx-answer-who">
                  <span aria-hidden="true">←</span> Fahem
                </p>
                <div className="fx-code">
                  <div className="fx-code-head">
                    <span>Algorithme</span>
                    <span>Python</span>
                  </div>
                  {[
                    ["Lire (N)", "N = int(input())"],
                    ["d ← N div 10", "d = N // 10"],
                    ["u ← N mod 10", "u = N % 10"],
                    ['Ecrire ("d :", d)', 'print("d :", d)'],
                  ].map(([algo, py], i) => (
                    <m.div
                      className="fx-code-row"
                      key={algo}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{
                        opacity: 1,
                        x: 0,
                        transition: { delay: 0.5 + i * 0.09, duration: 0.3 },
                      }}
                    >
                      <code className="fx-code-algo">{algo}</code>
                      <code className="fx-code-py">{py}</code>
                    </m.div>
                  ))}
                </div>
                <m.p
                  className="fx-answer-badge"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                    transition: { ...EASE_OUT, delay: 0.95 },
                  }}
                >
                  ✓ Syntaxe du chapitre respectée
                </m.p>
              </div>
            </div>
          </m.div>

          {/* Guided step, floating behind */}
          <m.figure
            className="fx-float fx-float-steps"
            style={{ y: drift(backY) }}
            initial={{ opacity: 0, x: -30, y: 20 }}
            animate={{
              opacity: 1,
              x: 0,
              y: 0,
              transition: { ...EASE_OUT, delay: 0.5 },
            }}
          >
            <figcaption>Mode guidé</figcaption>
            <ol className="fx-mini-rail">
              {["Comprendre", "Indice", "Squelette", "Solution"].map((label, i) => (
                <li
                  key={label}
                  className={i === 1 ? "is-current" : i < 1 ? "is-done" : ""}
                >
                  <span aria-hidden="true">{i < 1 ? "✓" : i + 1}</span>
                  {label}
                </li>
              ))}
            </ol>
          </m.figure>

          {/* Verdict, floating in front */}
          <m.figure
            className="fx-float fx-float-verdict"
            style={{ y: drift(frontY) }}
            initial={{ opacity: 0, x: 30, y: 30 }}
            animate={{
              opacity: 1,
              x: 0,
              y: 0,
              transition: { ...EASE_OUT, delay: 0.7 },
            }}
          >
            <span className="fx-float-emoji" aria-hidden="true">
              🎉
            </span>
            <figcaption>
              <b>Correct !</b>
              <span>Tu as résolu celui-là tout seul.</span>
            </figcaption>
          </m.figure>

          {/* The program, running */}
          <m.figure
            className="fx-float fx-float-term"
            style={{ y: drift(frontY) }}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0, transition: { ...EASE_OUT, delay: 0.85 } }}
          >
            <div className="fx-term-bar" aria-hidden="true">
              <i />
              <i />
              <i />
              <span>Terminé ✓</span>
            </div>
            <pre>
              {"Donner N : 47\n"}
              {"d : 4\n"}
              {"u : 7"}
            </pre>
          </m.figure>
        </div>
      </div>
    </section>
  );
}
