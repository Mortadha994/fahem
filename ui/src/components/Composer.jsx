import { useEffect, useRef } from "react";
import Button from "./ui/Button.jsx";

/**
 * Auto-resizing textarea. Enter sends, Shift+Enter breaks the line.
 *
 * `inputRef` lets the chat put the caret in the box after filling it from a
 * suggested exercise; it points at the same textarea as the internal ref.
 */
export default function Composer({
  value,
  onChange,
  onSend,
  onStop,
  streaming,
  inputRef,
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

  return (
    <div className="composer">
      <div className="composer-inner surface">
        <textarea
          ref={setRef}
          value={value}
          rows={1}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Colle ton énoncé d'exercice…"
          aria-label="Énoncé de l'exercice"
        />
        {streaming ? (
          <Button
            variant="secondary"
            className="btn-composer"
            onClick={onStop}
            aria-label="Arrêter"
          >
            <span className="stop-square" aria-hidden="true" /> Arrêter
          </Button>
        ) : (
          <Button
            variant="primary"
            className="btn-composer"
            onClick={onSend}
            disabled={!value.trim()}
            aria-label="Envoyer"
          >
            Envoyer
          </Button>
        )}
      </div>
      <p className="composer-hint">
        Entrée pour envoyer · Maj+Entrée pour un retour à la ligne
      </p>
    </div>
  );
}
