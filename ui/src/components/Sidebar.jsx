import { useState } from "react";

/**
 * Deleting a discussion asks first.
 *
 * localStorage is the only copy of a student's transcripts, so a stray click
 * on a 26x20 "x" used to destroy one permanently with no undo. The first
 * click now turns the control into "Supprimer ?" in place and the second
 * confirms.
 *
 * Inline rather than a modal because the choice is small, local and
 * reversible-by-doing-nothing; a dialog would steal focus from the sidebar
 * and be heavier than the decision deserves.
 *
 * Backing out is blur or Escape, not a second visible button. A cancel
 * control would double the number of targets in an already cramped row -
 * exactly what the 44px work in this same change is trying to relieve - and a
 * timeout would be worse still, since it can fire while the student is
 * reading the question. Clicking anywhere else is the instinctive way out of
 * an inline prompt, and Escape is what a keyboard user will reach for.
 *
 * sessions.js is untouched: this gates the call, it does not change how a
 * deletion is stored.
 */
export default function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  open,
  onClose,
  scopeLabel,
}) {
  // Which row is currently asking. Only ever one at a time - opening a second
  // confirm implicitly abandons the first, which is what a student expects.
  const [confirmingId, setConfirmingId] = useState(null);

  return (
    <>
      <div
        className={`scrim ${open ? "scrim-open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="sidebar-head">
          <span className="brand">Fahem</span>
          <button type="button" className="btn-new" onClick={onNew}>
            + Nouvelle discussion
          </button>
        </div>

        <nav className="session-list" aria-label="Discussions">
          {sessions.length === 0 && (
            <p className="session-empty">Aucune discussion pour l'instant.</p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session ${s.id === activeId ? "session-active" : ""}`}
            >
              <button
                type="button"
                className="session-btn"
                onClick={() => onSelect(s.id)}
              >
                <span className="session-title">{s.title}</span>
                <span className="session-sub">
                  {s.niveau} · ch. {s.chapitre}
                </span>
              </button>
              <button
                type="button"
                className={`session-del${
                  confirmingId === s.id ? " session-del-confirm" : ""
                }`}
                onClick={(e) => {
                  if (confirmingId === s.id) {
                    onDelete(s.id);
                    setConfirmingId(null);
                  } else {
                    setConfirmingId(s.id);
                    // Focus explicitly on entering the confirm state, because
                    // blur is what cancels it. A click does not reliably focus
                    // a button - Safari notably does not - so without this the
                    // prompt could be left stuck open with no way back except
                    // confirming, which is the one outcome this guard exists
                    // to prevent.
                    e.currentTarget.focus();
                  }
                }}
                /* Functional updater, not `confirmingId === s.id && ...`:
                   the handler closes over the render that attached it, so the
                   plain comparison can read a stale value and silently skip
                   the cancel - which it did, leaving the prompt stuck open. */
                onBlur={() => setConfirmingId((cur) => (cur === s.id ? null : cur))}
                onKeyDown={(e) => {
                  if (e.key !== "Escape") return;
                  e.stopPropagation();
                  setConfirmingId((cur) => (cur === s.id ? null : cur));
                }}
                /* The name changes with the state so a screen reader hears
                   what the next click will actually do, rather than the same
                   "Supprimer" in both. */
                aria-label={
                  confirmingId === s.id
                    ? `Confirmer la suppression de ${s.title}`
                    : `Supprimer ${s.title}`
                }
                title={confirmingId === s.id ? "Confirmer" : "Supprimer"}
              >
                {confirmingId === s.id ? "Supprimer ?" : "×"}
              </button>
            </div>
          ))}
        </nav>

        <p className="sidebar-foot">{scopeLabel}</p>
      </aside>
    </>
  );
}
