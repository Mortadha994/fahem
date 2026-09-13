import { useEffect, useRef } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { SPRING_HOVER } from "../lib/motion.js";

/**
 * The message box: an auto-resizing textarea on a card, with the send (or
 * stop) control and the thread's context underneath. Enter sends,
 * Shift+Enter breaks the line.
 *
 * `followUp` switches the placeholder once the thread has messages, so an
 * empty box in the middle of a discussion invites a follow-up question rather
 * than asking for "an exercise statement" again. `chapterLabel` is shown as a
 * chip, because the chapter decides which syntax the answer will use.
 *
 * `inputRef` lets the chat put the caret in the box (suggested exercise, new
 * discussion); it points at the same textarea as the internal ref.
 *
 * Send and stop are round icon buttons, each with a spoken name, rather than
 * the shared text Button: at this size the icon is the familiar control, and
 * the text version was the widest thing in the row.
 */
export default function Composer({
  value,
  onChange,
  onSend,
  onStop,
  streaming,
  inputRef,
  followUp = false,
  chapterLabel,
}) {
  const ref = useRef(null);
  const setRef = (el) => {
    ref.current = el;
    if (inputRef) inputRef.current = el;
  };

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Reset before measuring or the box can only ever grow.
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  }, [value]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (!streaming && value.trim()) onSend();
    }
  }

  const canSend = !streaming && value.trim().length > 0;

  return (
    <div className="composer">
      <div className="composer-card">
        <textarea
          ref={setRef}
          value={value}
          rows={1}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            followUp
              ? "Pose une question de suivi, ou colle un autre énoncé…"
              : "Un exercice, une question sur le cours, ou ton programme…"
          }
          aria-label="Ton message"
        />
        <div className="composer-bar">
          <p className="composer-context">
            {chapterLabel && <span className="composer-chip">{chapterLabel}</span>}
            <span className="composer-hint">
              Entrée pour envoyer · Maj+Entrée pour aller à la ligne
            </span>
          </p>
          {/* Send and stop swap with a quick scale-fade; the one showing
              presses with a spring. */}
          <AnimatePresence mode="wait" initial={false}>
            {streaming ? (
              <m.button
                key="stop"
                type="button"
                className="composer-btn is-stop"
                onClick={onStop}
                aria-label="Arrêter la réponse"
                title="Arrêter"
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1, transition: SPRING_HOVER }}
                exit={{ opacity: 0, scale: 0.7, transition: { duration: 0.1 } }}
                whileTap={{ scale: 0.9 }}
              >
                <span className="stop-square" aria-hidden="true" />
              </m.button>
            ) : (
              <m.button
                key="send"
                type="button"
                className="composer-btn is-send"
                onClick={onSend}
                disabled={!canSend}
                aria-label="Envoyer"
                title="Envoyer"
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1, transition: SPRING_HOVER }}
                exit={{ opacity: 0, scale: 0.7, transition: { duration: 0.1 } }}
                whileTap={canSend ? { scale: 0.9 } : undefined}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" />
                </svg>
              </m.button>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
