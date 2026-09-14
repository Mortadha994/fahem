import { useState } from "react";
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

export default function Message({ message, streaming, onRetry }) {
  if (message.role === "user") {
    return (
      <m.div className="msg msg-user" {...enterUser}>
        <div className="bubble">
          {/* A photo or PDF the exercise came from. Once read, the bubble
              holds what was read from it, so the student can check the
              transcription before trusting the answer. */}
          {message.attachment && (
            <span
              className={`msg-attachment${
                message.content || message.note ? "" : " is-alone"
              }`}
            >
              <span className="msg-attachment-icon" aria-hidden="true">
                {message.attachment.kind === "pdf" ? "PDF" : "IMG"}
              </span>
              <span className="msg-attachment-name">{message.attachment.name}</span>
              <span className="msg-attachment-state">
                {message.reading ? "lecture…" : message.content ? "texte lu" : ""}
              </span>
            </span>
          )}
          {/* The student's own question about the attached exercise, above
              what was read from the file. */}
          {message.note && (
            <span className={`msg-note${message.content ? "" : " is-alone"}`}>
              {message.note}
            </span>
          )}
          {message.content}
        </div>
      </m.div>
    );
  }

  const { content, pinned, retrieved, warnings, status, error } = message;
  const writing = status === "streaming" && streaming;
  const finished = content && !writing;

  return (
    <m.div className="msg msg-assistant" {...enterAssistant}>
      {/* Who is speaking, once per answer. Without it a long thread of
          unboxed answers and short bubbles is hard to scan back through.
          Decorative for screen readers, which already get each answer as its
          own block after the student's question - and hear "writing" through
          the thinking indicator's status role and the chat's live region. */}
      <p className="msg-author" aria-hidden="true">
        <span className="brand-mark">←</span>
        Fahem
        {writing && content && (
          <span className="msg-writing">
            <span className="msg-writing-dot" />
            rédige…
          </span>
        )}
      </p>
      {error ? (
        // "Réessayer" sends the same question again (Chat.jsx retryLast);
        // offered on the latest answer only.
        <Alert
          className="msg-error"
          action={onRetry ? { label: "Réessayer", onClick: onRetry } : undefined}
        >
          {error}
        </Alert>
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
                <span className="thinking-text">
                  {status === "reading"
                    ? message.readingKind === "pdf"
                      ? "Lecture de ton PDF…"
                      : "Lecture de ta photo…"
                    : "Recherche dans le chapitre…"}
                </span>
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

          {status === "stopped" && (
            <p className="msg-stopped">Réponse arrêtée avant la fin.</p>
          )}

          <GroundingStrip pinned={pinned} retrieved={retrieved} />

          {/* Actions on a finished answer: copy all of it (the Algorithme
              column has its own copy button for the pseudocode alone), and
              ask again when it was cut short. */}
          {finished && (
            <div className="msg-actions">
              <CopyAnswer text={content} />
              {status === "stopped" && onRetry && (
                <button type="button" className="msg-action" onClick={onRetry}>
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" />
                  </svg>
                  Régénérer
                </button>
              )}
            </div>
          )}
        </>
      )}
    </m.div>
  );
}

/** Copies the whole answer as the markdown it arrived as, and says so. */
function CopyAnswer({ text }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Denied or insecure context: no confirmation rather than an error.
    }
  }

  return (
    <>
      {/* Announced separately: a change to a button's own name is not read
        out reliably, a status message is. */}
      <span className="sr-only" role="status">
        {copied ? "Réponse copiée" : ""}
      </span>
      <button
        type="button"
        className={`msg-action${copied ? " is-done" : ""}`}
        onClick={copy}
      >
        {copied ? (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 12.5 10 17l9-10" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="9" y="9" width="11" height="11" rx="2" />
            <path d="M5 15V6a2 2 0 0 1 2-2h8" />
          </svg>
        )}
        {copied ? "Copié" : "Copier la réponse"}
      </button>
    </>
  );
}
