import { useState } from "react";
import Button from "./ui/Button.jsx";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { ago } from "../lib/relativeTime.js";

/**
 * The chat's discussions, as a section of the app sidebar.
 *
 * Was Sidebar.jsx, a sidebar of its own rendered by the chat route. Phase 6
 * makes it a section inside the single app sidebar, shown only on /chat: the
 * drawer, the scrim and the aside belong to AppLayout now, and this owns the
 * list and nothing else. The delete confirmation below is unchanged from
 * Step 3 of the audit work.
 *
 * Deleting a discussion asks first.
 *
 * localStorage is the only copy of a student's transcripts, so a stray click
 * on a 26x20 "x" used to destroy one permanently with no undo. The first
 * click now turns the control into "Supprimer ?" in place and the second
 * confirms.
 *
 * Backing out is blur or Escape, not a second visible button. A cancel
 * control would double the number of targets in an already cramped row, and a
 * timeout would be worse still, since it can fire while the student is
 * reading the question.
 */
export default function SessionHistory({ onNavigate }) {
  const { sessions, activeId, setActiveId, createSession, deleteSession } =
    useChatSessions();

  // Which row is currently asking. Only ever one at a time - opening a second
  // confirm implicitly abandons the first, which is what a student expects.
  const [confirmingId, setConfirmingId] = useState(null);

  return (
    <section className="session-section" aria-labelledby="session-section-title">
      <h2 id="session-section-title" className="appnav-heading">
        Discussions
      </h2>

      <Button
        variant="secondary"
        className="btn-new"
        onClick={() => {
          createSession();
          onNavigate?.();
        }}
      >
        + Nouvelle discussion
      </Button>

      <div className="session-list">
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
              aria-current={s.id === activeId ? "true" : undefined}
              onClick={() => {
                setActiveId(s.id);
                onNavigate?.();
              }}
            >
              <span className="session-title">{s.title}</span>
              {/* Chapter and recency - what tells two similar titles apart. The
                  niveau is the same for every discussion, so it is not
                  repeated on each row. */}
              <span className="session-sub">
                Chapitre {s.chapitre}
                {s.messages?.length > 0 && s.updatedAt ? ` · ${ago(s.updatedAt)}` : ""}
              </span>
            </button>
            {/* ghost at rest, danger while asking: the variant is what turns
                the bare glyph into the red "Supprimer ?" chip. The
                session-del classes only handle the hover/focus reveal. */}
            <Button
              variant={confirmingId === s.id ? "danger" : "ghost"}
              size="sm"
              className={`session-del${
                confirmingId === s.id ? " session-del-confirm" : ""
              }`}
              onClick={(e) => {
                if (confirmingId === s.id) {
                  deleteSession(s.id);
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
            </Button>
          </div>
        ))}
      </div>
    </section>
  );
}
