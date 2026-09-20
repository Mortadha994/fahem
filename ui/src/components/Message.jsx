import { memo, useState } from "react";
import * as m from "motion/react-m";
import Markdown from "./Markdown.jsx";
import GroundingStrip from "./GroundingStrip.jsx";
import Alert from "./ui/Alert.jsx";
import { SPRING_ENTER, pop } from "../lib/motion.js";
import { practiceStatement } from "../lib/learning.js";
import {
  ActionButton,
  ActionRow,
  CheckedAnswer,
  GuidedSteps,
  PracticeCard,
  PracticeMenu,
} from "./learning/Learning.jsx";

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

function Message({
  message,
  streaming,
  onRetry,
  onEdit,
  onFeedback,
  onGuided,
  guidedStep,
  onPropose,
  onPractice,
  onPracticeStart,
  guidedAvailable,
  fresh = false,
  live = false,
}) {
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
          {message.mode === "check" && (
            <span className="msg-mode-tag">Vérifier ma réponse</span>
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
          {message.guided && (
            <GuidedSteps step={message.guided.step} fresh={fresh} live={live} />
          )}
          {content ? (
            message.check || message.route === "CHECK" ? (
              <CheckedAnswer
                content={content}
                verdict={message.check?.verdict}
                fresh={fresh}
              />
            ) : message.practice ? (
              <PracticeCard
                content={content}
                difficulty={message.practice.difficulty}
                fresh={fresh}
              />
            ) : (
              <Markdown>{content}</Markdown>
            )
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

          {status === "stopped" && (
            <p className="msg-stopped">Réponse arrêtée avant la fin.</p>
          )}

          {/* The guided exercise's next move: another hint, the student's own
              attempt (checked), or the whole solution. */}
          {/* A generated exercise: take it on, guided or not, or answer it. */}
          {finished && message.practice && (onPracticeStart || onPropose) && (
            <ActionRow fresh={fresh}>
              {onPracticeStart && guidedAvailable && (
                <ActionButton
                  tone="primary"
                  onClick={() => onPracticeStart(practiceStatement(content), "guided")}
                >
                  {/* The emoji is decoration on a labelled button. Left bare
                      it joins the accessible name, and the button announces
                      as "compass Me guider pas à pas". */}
                  <span aria-hidden="true">🧭</span> Me guider pas à pas
                </ActionButton>
              )}
              {onPropose && (
                <ActionButton onClick={onPropose}>
                  <span aria-hidden="true">✍️</span> Je propose ma solution
                </ActionButton>
              )}
              {onPracticeStart && (
                <ActionButton
                  tone="quiet"
                  onClick={() => onPracticeStart(practiceStatement(content), "full")}
                >
                  Voir la solution
                </ActionButton>
              )}
            </ActionRow>
          )}

          {finished && !message.practice && (onGuided || onPropose) && (
            <ActionRow fresh={fresh}>
              {onGuided && (
                <ActionButton tone="primary" onClick={() => onGuided("next_step")}>
                  <span aria-hidden="true">{guidedStep === 3 ? "🏁" : "💡"}</span>{" "}
                  {guidedStep === 3 ? "Dernière étape" : "Indice suivant"}
                  <span className="guided-arrow" aria-hidden="true">
                    →
                  </span>
                </ActionButton>
              )}
              {onPropose && (
                <ActionButton onClick={onPropose}>
                  <span aria-hidden="true">✍️</span> Je propose ma solution
                </ActionButton>
              )}
              {onGuided && (
                <ActionButton tone="quiet" onClick={() => onGuided("show_solution")}>
                  Voir la solution
                </ActionButton>
              )}
            </ActionRow>
          )}

          {/* One strip under the answer, not four.
              What the answer IS (the checker's verdict, the chapter sources it
              was built on) sits on the left as quiet chips; what you can DO
              with it sits on the right and stays out of sight until the
              pointer or the keyboard reaches this answer (.msg-foot-tools in
              App.css). The next move - another hint, your own attempt, the
              solution - is not here: it is the ActionRow above, where it can
              be seen without hunting. */}
          <MessageFooter
            status={status}
            warnings={warnings}
            pinned={pinned}
            retrieved={retrieved}
            tools={
              finished && (
                <>
                  <CopyAnswer text={content} />
                  {onRetry && (
                    <button type="button" className="msg-action" onClick={onRetry}>
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" />
                      </svg>
                      <span className="msg-action-label">Régénérer</span>
                    </button>
                  )}
                  {onPractice && <PracticeMenu onPick={onPractice} />}
                  {onFeedback && status !== "stopped" && (
                    <Feedback
                      value={message.feedback}
                      onRate={(rating) => onFeedback(message.id, rating)}
                    />
                  )}
                </>
              )
            }
          />
        </>
      )}
    </m.div>
  );
}

/**
 * Everything that is true *about* an answer, on one line under it.
 *
 * It replaced three stacked strips - a full-width verdict badge, a bordered
 * grounding box, and a row of text buttons - which together put four bands of
 * furniture under every single answer and made a two-line reply look like a
 * dashboard. They say small things, so they are small: chips on the left,
 * tools on the right.
 *
 * The row wraps, and the grounding body is 100% wide, so opening it drops it
 * onto its own line underneath without a wrapper of its own.
 *
 * The verdict reports what the checker found - not that the answer is right,
 * which is why it says "syntaxe" rather than "vérifié".
 */
function MessageFooter({ status, warnings, pinned, retrieved, tools }) {
  const verdict = VERDICTS[status];
  const grounded = pinned?.length || retrieved?.length;
  if (!verdict && !grounded && !tools) return null;

  return (
    <footer className="msg-foot">
      {verdict &&
        (status === "checking" ? (
          <span className="msg-chip is-checking">{verdict.label}</span>
        ) : (
          // Pops from its left edge when it resolves - the one moment here
          // worth noticing.
          <m.span
            className={`msg-chip is-${verdict.tone}`}
            variants={pop}
            initial="hidden"
            animate="show"
            title={verdict.title}
          >
            <span className="msg-chip-dot" aria-hidden="true" />
            {verdict.label}
          </m.span>
        ))}

      <GroundingStrip pinned={pinned} retrieved={retrieved} />

      {tools && <div className="msg-foot-tools">{tools}</div>}

      {status === "warned" && warnings?.length > 0 && (
        <ul className="warn-list">
          {warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </footer>
  );
}

const VERDICTS = {
  checking: { label: "Vérification de la syntaxe…" },
  clean: {
    tone: "ok",
    label: "Syntaxe du chapitre respectée",
    title: "Aucune syntaxe hors chapitre détectée",
  },
  warned: {
    tone: "warn",
    label: "Syntaxe à vérifier",
    title: "Le vérificateur a relevé de la syntaxe hors chapitre",
  },
};

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
        {/* Short, because the icon already says what it does and the whole
            footer has to stay on one line beside the chips. */}
        <span className="msg-action-label">{copied ? "Copié" : "Copier"}</span>
      </button>
    </>
  );
}
