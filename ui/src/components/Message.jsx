import * as m from "motion/react-m";
import Markdown from "./Markdown.jsx";
import GroundingStrip from "./GroundingStrip.jsx";
import Alert from "./ui/Alert.jsx";
import Badge from "./ui/Badge.jsx";
import { SPRING_ENTER, pop } from "../lib/motion.js";

/**
 * Student messages are shaded and constrained in width; assistant messages are
 * full-width with no bubble, which is what Claude and ChatGPT do for long
 * technical answers - a bubble around a wide Algorithme|Python table just
 * wastes horizontal space.
 *
 * Each message slides up into the thread when it is added. Chat.jsx wraps the
 * list in AnimatePresence with initial={false}, keyed by discussion, so
 * opening an existing discussion shows it still - only new messages move.
 */

// The student's bubble comes in from its own side; the answer rises in place.
const enterUser = {
  initial: { opacity: 0, y: 10, x: 12 },
  animate: { opacity: 1, y: 0, x: 0, transition: SPRING_ENTER },
};
const enterAssistant = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { ...SPRING_ENTER, delay: 0.08 } },
};

export default function Message({ message, streaming }) {
  if (message.role === "user") {
    return (
      <m.div className="msg msg-user" {...enterUser}>
        <div className="bubble">{message.content}</div>
      </m.div>
    );
  }

  const { content, pinned, retrieved, warnings, status, error } = message;

  return (
    <m.div className="msg msg-assistant" {...enterAssistant}>
      {/* Who is speaking, once per answer. Without it a long thread of
          unboxed answers and short bubbles is hard to scan back through.
          Decorative for screen readers, which already get each answer as its
          own block after the student's question. */}
      <p className="msg-author" aria-hidden="true">
        <span className="brand-mark">←</span>
        Fahem
      </p>
      {error ? (
        <Alert className="msg-error">{error}</Alert>
      ) : (
        <>
          {content ? (
            <Markdown>{content}</Markdown>
          ) : (
            streaming && (
              <p className="thinking" role="status">
                {/* Three dots rising in turn - a Motion loop, so it stops with
                    the rest of the app's motion under reduced motion. */}
                {[0, 1, 2].map((i) => (
                  <m.span
                    key={i}
                    className="dot"
                    animate={{ y: [0, -4, 0], opacity: [0.3, 1, 0.3] }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: i * 0.15,
                    }}
                  />
                ))}
                <span className="thinking-text">Recherche dans le chapitre…</span>
              </p>
            )
          )}

          {/* The badge only resolves once the whole answer exists and the
              checker has run. It reports what the checker found - it is not a
              correctness guarantee, and the label says "syntaxe" for that
              reason rather than something like "vérifié" alone. It pops in
              when it resolves, which is the moment worth noticing. */}
          {status === "checking" && (
            <Badge tone="neutral" className="msg-verdict">
              Vérification de la syntaxe…
            </Badge>
          )}
          {status === "clean" && (
            <m.div
              className="msg-verdict-wrap"
              variants={pop}
              initial="hidden"
              animate="show"
            >
              <Badge
                tone="success"
                className="msg-verdict"
                title="Aucune syntaxe hors chapitre détectée"
              >
                ✓ Syntaxe du chapitre respectée
              </Badge>
            </m.div>
          )}
          {status === "warned" && (
            <m.div
              className="badge-warn-wrap msg-verdict-wrap"
              variants={pop}
              initial="hidden"
              animate="show"
            >
              <Badge tone="warning" className="msg-verdict">
                ⚠ Syntaxe à vérifier
              </Badge>
              <ul className="warn-list">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </m.div>
          )}

          <GroundingStrip pinned={pinned} retrieved={retrieved} />
        </>
      )}
    </m.div>
  );
}
