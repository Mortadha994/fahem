import { useEffect, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { ATTACHMENT_TYPES } from "../lib/api.js";
import { SPRING_HOVER } from "../lib/motion.js";

/**
 * The message box: an auto-resizing textarea on a card, with the send (or
 * stop) control and the thread's context underneath. Enter sends,
 * Shift+Enter breaks the line.
 *
 * Attachments: a photo or a PDF of an exercise can be added with the paperclip
 * button, pasted (Ctrl+V a screenshot or a copied image), or dropped on the
 * card. The chat reads it (POST /solve/extract) and solves what it says; the
 * text is optional then - it travels with the file as a note. The file itself
 * is held by Chat.jsx (`attachment`), which also validates it (`onAttach`),
 * so this component only collects it and shows it.
 *
 * Modes: `onModeChange` shows the Solution complète / Mode guidé switch
 * (`mode` is the discussion's), and `onCheck` the "Vérifier ma réponse"
 * button, which sends the box's content to be corrected instead of answered.
 * Either is hidden when the admin turned it off.
 *
 * `followUp` switches the placeholder once the thread has messages.
 * `chapterLabel` is shown as a chip, because the chapter decides which syntax
 * the answer will use. `inputRef` lets the chat put the caret in the box.
 */
export default function Composer({
  value,
  onChange,
  onSend,
  onCheck,
  mode = "full",
  onModeChange,
  onStop,
  streaming,
  disabled = false,
  maxLength = 2000,
  inputRef,
  followUp = false,
  chapterLabel,
  attachment,
  attachError,
  onAttach,
  onRemoveAttachment,
}) {
  const ref = useRef(null);
  const fileRef = useRef(null);
  const [dragging, setDragging] = useState(false);
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

  // The server declines anything past its cap; say so here, before sending,
  // instead of letting a long statement come back as a refusal.
  const length = value.length;
  const tooLong = length > maxLength;
  const showCount = length > maxLength * 0.8;
  const canSend =
    !streaming &&
    !disabled &&
    !tooLong &&
    (value.trim().length > 0 || Boolean(attachment));

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (canSend) onSend();
    }
  }

  // A pasted screenshot or copied image becomes the attachment; pasted text
  // still goes into the box as usual.
  function handlePaste(e) {
    const file = [...(e.clipboardData?.files ?? [])].find((f) =>
      ATTACHMENT_TYPES.includes(f.type)
    );
    if (file) {
      e.preventDefault();
      onAttach(file);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) onAttach(file);
  }

  return (
    <div className="composer">
      <div
        className={`composer-card${dragging ? " is-dragging" : ""}`}
        onDragOver={(e) => {
          if ([...(e.dataTransfer?.types ?? [])].includes("Files")) {
            e.preventDefault();
            setDragging(true);
          }
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false);
        }}
        onDrop={handleDrop}
      >
        {/* The file waiting to be sent: a thumbnail for a photo, an icon for
            a PDF, and a way to take it back out. */}
        <AnimatePresence initial={false}>
          {attachment && (
            <m.div
              key={attachment.url ?? attachment.name}
              className="composer-attachment"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0, transition: SPRING_HOVER }}
              exit={{ opacity: 0, y: 6, transition: { duration: 0.12 } }}
            >
              {attachment.kind === "image" ? (
                <img
                  className="composer-attachment-thumb"
                  src={attachment.url}
                  alt=""
                />
              ) : (
                <span className="composer-attachment-icon" aria-hidden="true">
                  PDF
                </span>
              )}
              <span className="composer-attachment-text">
                <span className="composer-attachment-name">{attachment.name}</span>
                <span className="composer-attachment-meta">
                  {attachment.kind === "image" ? "Photo" : "PDF"} ·{" "}
                  {formatSize(attachment.size)} · l'énoncé sera lu puis résolu
                </span>
              </span>
              <button
                type="button"
                className="composer-attachment-remove"
                onClick={onRemoveAttachment}
                aria-label={`Retirer ${attachment.name}`}
                title="Retirer"
              >
                ×
              </button>
            </m.div>
          )}
        </AnimatePresence>

        <textarea
          ref={setRef}
          value={value}
          rows={1}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={
            attachment
              ? "Ajoute une précision si tu veux (facultatif)…"
              : mode === "guided"
                ? followUp
                  ? "Réponds à la question de Fahem, ou colle un autre énoncé…"
                  : "Colle ton énoncé : Fahem te guide étape par étape…"
                : followUp
                  ? "Pose une question de suivi, ou colle un autre énoncé…"
                  : "Un exercice, une question, ton programme… ou une photo 📎"
          }
          aria-label="Ton message"
          aria-describedby={showCount ? "composer-count" : undefined}
          disabled={disabled}
        />
        {showCount && (
          <p
            id="composer-count"
            className={`composer-count${tooLong ? " is-over" : ""}`}
            role={tooLong ? "alert" : undefined}
          >
            {tooLong
              ? attachment
                ? `Ta précision est trop longue : ${length} / ${maxLength} caractères.`
                : `Message trop long : ${length} / ${maxLength} caractères. Envoie seulement l'énoncé, ou découpe ta question.`
              : `${length} / ${maxLength} caractères`}
          </p>
        )}
        {attachError && (
          <p className="composer-error" role="alert">
            {attachError}
          </p>
        )}
        {(onModeChange || onCheck) && (
          <div className="composer-modes">
            {onModeChange && (
              <div
                className="mode-switch"
                role="radiogroup"
                aria-label="Façon de répondre"
              >
                {[
                  [
                    "full",
                    "Solution complète",
                    "La solution entière, avec le tableau et la trace",
                  ],
                  [
                    "guided",
                    "Mode guidé",
                    "Des indices étape par étape avant la solution",
                  ],
                ].map(([value, label, title]) => (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={mode === value}
                    className={`mode-option${mode === value ? " is-on" : ""}`}
                    onClick={() => onModeChange(value)}
                    disabled={streaming}
                    title={title}
                  >
                    {mode === value && (
                      <m.span
                        layoutId="mode-pill"
                        className="mode-pill"
                        transition={SPRING_HOVER}
                      />
                    )}
                    <span className="mode-label">{label}</span>
                  </button>
                ))}
              </div>
            )}
            {onCheck && (
              <button
                type="button"
                className="composer-check"
                onClick={onCheck}
                disabled={!canSend}
                title="Colle ton algorithme ou ton programme : Fahem le corrige ligne par ligne"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M9 11.5 11.5 14 16 9.5M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18z" />
                </svg>
                Vérifier ma réponse
              </button>
            )}
          </div>
        )}
        <div className="composer-bar">
          <div className="composer-context">
            <input
              ref={fileRef}
              type="file"
              accept={ATTACHMENT_TYPES.join(",")}
              className="sr-only"
              tabIndex={-1}
              aria-hidden="true"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onAttach(file);
                // Reset so choosing the same file again still fires onChange.
                e.target.value = "";
              }}
            />
            <button
              type="button"
              className="composer-attach"
              onClick={() => fileRef.current?.click()}
              disabled={streaming}
              aria-label="Joindre une photo ou un PDF de l'exercice"
              title="Joindre une photo ou un PDF"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M20.5 11.5 12.4 19.6a5 5 0 0 1-7.1-7.1l8.5-8.5a3.4 3.4 0 0 1 4.8 4.8l-8.5 8.5a1.7 1.7 0 0 1-2.4-2.4l7.8-7.8" />
              </svg>
            </button>
            {chapterLabel && <span className="composer-chip">{chapterLabel}</span>}
            <span className="composer-hint">
              {dragging
                ? "Dépose ta photo ou ton PDF ici"
                : "Entrée pour envoyer · Maj+Entrée pour aller à la ligne · Ctrl+V une capture"}
            </span>
          </div>
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
                aria-label={attachment ? "Envoyer et résoudre" : "Envoyer"}
                title={attachment ? "Envoyer et résoudre" : "Envoyer"}
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

function formatSize(bytes = 0) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`;
}
