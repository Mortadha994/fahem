import { useEffect, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { ATTACHMENT_TYPES } from "../lib/api.js";
import { SPRING_HOVER } from "../lib/motion.js";
import { MODES } from "../lib/learning.js";
import Icon from "./ui/Icon.jsx";

const OTHER_MODE = { full: "guided", guided: "full" };

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
 * (`mode` is the discussion's). Once the discussion has started, its mode is
 * fixed (`modeLocked`): the switch gives way to the mode's name and a button
 * that opens a new discussion in the other one (`onSwitchMode`). And `onCheck` the "Vérifier ma réponse"
 * button, which sends the box's content to be corrected instead of answered.
 * Either is hidden when the admin turned it off.
 *
 * `followUp` switches the placeholder once the thread has messages.
 * `note` is one quiet sentence beside the clip - the chat puts what Fahem
 * remembers of this discussion there. It used to be a band of its own above
 * the composer, next to a chip repeating the chapter already named in the
 * header and a permanent keyboard legend: three strips of explanation around
 * a box whose placeholder already says what to do. The legend now appears
 * while the box has focus, which is when it is of any use, and never on a
 * phone, where none of those keys exist.
 * `inputRef` lets the chat put the caret in the box.
 */
export default function Composer({
  value,
  onChange,
  onSend,
  onCheck,
  mode = "full",
  onModeChange,
  modeLocked = false,
  onSwitchMode,
  onStop,
  streaming,
  disabled = false,
  maxLength = 2000,
  inputRef,
  followUp = false,
  note,
  attachment,
  attachError,
  onAttach,
  onRemoveAttachment,
}) {
  const ref = useRef(null);
  const fileRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  // The keyboard legend is only worth screen space while the box is in use.
  const [focused, setFocused] = useState(false);
  const keys = focused && !dragging;
  const setRef = (el) => {
    ref.current = el;
    if (inputRef) inputRef.current = el;
  };

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Reset before measuring or the box can only ever grow.
    el.style.height = "auto";
    // The cap is 13.75rem, matching the stylesheet's max-height, and read from
    // the root font size rather than hardcoded at 220px: at 200% text zoom a
    // fixed pixel cap is half the lines it should be, and the box stops
    // growing while the text keeps coming.
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    el.style.height = `${Math.min(el.scrollHeight, 13.75 * rem)}px`;
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
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={
            attachment
              ? "Ajoute une précision si tu veux (facultatif)…"
              : mode === "guided"
                ? followUp
                  ? "Réponds à la question de Fahem, ou colle un autre énoncé…"
                  : "Colle ton énoncé : Fahem te guide étape par étape…"
                : followUp
                  ? "Pose une question de suivi, ou colle un autre énoncé…"
                  : "Un exercice, une question, ton programme…"
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
        {/* One row under the text: the paperclip and the discussion's mode on
            the left, Vérifier and send on the right. The mode, the switch,
            Vérifier and a note used to be two rows of their own here, which
            on a phone made the box a quarter of the screen. */}
        <div className="composer-bar">
          <div className="composer-tools">
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
              <Icon name="paperclip" size={18} />
            </button>
            {onModeChange && modeLocked && (
              <div className={`mode-locked is-${mode}`}>
                <span className="mode-locked-name" title={MODES[mode].title}>
                  <Icon name={MODES[mode].icon} size={16} />
                  {MODES[mode].label}
                </span>
                {onSwitchMode && (
                  <button
                    type="button"
                    className="mode-locked-switch"
                    onClick={() => onSwitchMode(OTHER_MODE[mode])}
                    disabled={streaming}
                    title={`Ouvre une nouvelle discussion en ${MODES[OTHER_MODE[mode]].label}`}
                    aria-label={`Nouvelle discussion en ${MODES[OTHER_MODE[mode]].label}`}
                  >
                    <Icon name="swap" size={15} className="mode-locked-icon" />
                    <span className="mode-locked-long">
                      Nouvelle discussion en {MODES[OTHER_MODE[mode]].label}
                    </span>
                    <span className="mode-locked-short">
                      Passer en {OTHER_MODE[mode] === "guided" ? "guidé" : "solution"}
                    </span>
                  </button>
                )}
              </div>
            )}
            {onModeChange && !modeLocked && (
              <div
                className={`mode-switch is-${mode}`}
                role="radiogroup"
                aria-label="Façon de répondre"
              >
                {/* One pill sliding under the two choices (a transform: the
                      student app has no layout animations). */}
                <m.span
                  className="mode-pill"
                  aria-hidden="true"
                  initial={false}
                  animate={{ x: mode === "guided" ? "100%" : "0%" }}
                  transition={SPRING_HOVER}
                />
                {["full", "guided"]
                  .map((value) => [
                    value,
                    MODES[value].icon,
                    MODES[value].label,
                    MODES[value].title,
                  ])
                  .map(([value, icon, label, title]) => (
                    <m.button
                      key={value}
                      type="button"
                      role="radio"
                      aria-checked={mode === value}
                      className={`mode-option${mode === value ? " is-on" : ""}`}
                      onClick={() => onModeChange(value)}
                      disabled={streaming}
                      title={title}
                      whileTap={{ scale: 0.95 }}
                    >
                      <m.span
                        className="mode-icon"
                        aria-hidden="true"
                        animate={
                          mode === value
                            ? { scale: [1, 1.35, 1], rotate: [0, -12, 0] }
                            : { scale: 1 }
                        }
                        transition={{ duration: 0.45 }}
                      >
                        <Icon name={icon} size={16} />
                      </m.span>
                      <span className="mode-label">{label}</span>
                    </m.button>
                  ))}
              </div>
            )}
          </div>
          <div className="composer-actions">
            {onCheck && (
              <m.button
                type="button"
                className="composer-check"
                onClick={onCheck}
                disabled={!canSend}
                title="Colle ton algorithme ou ton programme : Fahem le corrige ligne par ligne"
                whileHover={canSend ? { y: -2 } : undefined}
                whileTap={canSend ? { scale: 0.95 } : undefined}
              >
                <Icon name="checkCircle" size={17} />
                <span className="composer-check-long">Vérifier ma réponse</span>
                <span className="composer-check-short">Vérifier</span>
              </m.button>
            )}
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
                  <Icon name="arrowUp" size={18} strokeWidth={2.2} />
                </m.button>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
      {/* The quiet line under the box: what Fahem remembers, the keys while
          the box has focus, or where to drop a file. */}
      {/* is-keys marks the one variant that assumes a keyboard, so a
          touch screen can drop it and keep the note. */}
      <span className={`composer-hint${keys ? " is-keys" : ""}`}>
        {dragging
          ? "Dépose ta photo ou ton PDF ici"
          : keys
            ? "Entrée pour envoyer · Maj+Entrée pour aller à la ligne · Ctrl+V une capture"
            : note}
      </span>
    </div>
  );
}

function formatSize(bytes = 0) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`;
}
