import { memo, useState } from "react";
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

/**
 * Memoized: an answer streams in token by token, and each token used to
 * re-render - and re-parse the Markdown tables of - every earlier message in
 * the thread. Chat.jsx gives earlier messages constant props, so only the
 * message being written renders again.
 */
export default memo(Message);

function Message({ message, streaming, onRetry, onEdit, onFeedback }) {
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
        {/* Take the last question back into the composer, to fix and resend. */}
        {onEdit && (
          <button type="button" className="msg-edit" onClick={onEdit}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 20h4L18.5 9.5a2.1 2.1 0 0 0-3-3L5 17v3z" />
            </svg>
            Modifier
          </button>
        )}
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
                  {status === "waiting"
                    ? waitingText(message.waiting)
                    : status === "reading"
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
              {onRetry && (
                <button type="button" className="msg-action" onClick={onRetry}>
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" />
                  </svg>
                  Régénérer
                </button>
              )}
              {onFeedback && status !== "stopped" && (
                <Feedback
                  value={message.feedback}
                  onRate={(rating) => onFeedback(message.id, rating)}
                />
              )}
            </div>
          )}
        </>
      )}
    </m.div>
  );
}

/**
 * The line shown while the request waits in Groq's queue - for the
 * gatekeeper's classification or for the solve, the same words for both. The
 * position counts requests ahead of this one. A rate-limited wait shows
 * Groq's own Retry-After; a queue wait never shows the queue's estimate,
 * which is not yet trusted (llm_queue.estimate_seconds).
 */
function waitingText(waiting) {
  const base = "Fahem est très sollicité, ta demande est en file d'attente…";
  if (!waiting) return base;
  const seconds = waiting.seconds ? Math.max(1, Math.round(waiting.seconds)) : null;
  if (waiting.reason === "rate_limited") {
    return seconds ? `${base} reprise dans environ ${seconds} s.` : base;
  }
  if (waiting.position > 0) {
    const ahead = waiting.position;
    return `${base} ${ahead} demande${ahead > 1 ? "s" : ""} avant la tienne.`;
  }
  return `${base} c'est bientôt ton tour.`;
}

/**
 * 👍 / 👎 on an answer - how the answers' quality is measured (the admin
 * console counts them, and lists the 👎). Pressing the chosen one again takes
 * it back.
 */
function Feedback({ value, onRate }) {
  return (
    <span className="msg-feedback" role="group" aria-label="Cette réponse t'a aidé ?">
      <button
        type="button"
        className={`msg-action msg-rate${value === 1 ? " is-on" : ""}`}
        aria-pressed={value === 1}
        title="Réponse utile"
        onClick={() => onRate(1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 11v9H4v-9h3zm0 0 4-7a2 2 0 0 1 3 1.7V9h5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.8 20H7" />
        </svg>
        <span className="sr-only">Utile</span>
      </button>
      <button
        type="button"
        className={`msg-action msg-rate${value === -1 ? " is-on is-down" : ""}`}
        aria-pressed={value === -1}
        title="Réponse fausse ou pas claire"
        onClick={() => onRate(-1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M17 13V4h3v9h-3zm0 0-4 7a2 2 0 0 1-3-1.7V15H5a2 2 0 0 1-2-2.3l1.2-7A2 2 0 0 1 6.2 4H17" />
        </svg>
        <span className="sr-only">Pas utile</span>
      </button>
      {value && (
        <span className="msg-feedback-thanks" role="status">
          {value === 1 ? "Merci !" : "Merci, on va l'améliorer."}
        </span>
      )}
    </span>
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
