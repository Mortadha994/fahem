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
                className="session-del"
                onClick={() => onDelete(s.id)}
                aria-label={`Supprimer ${s.title}`}
                title="Supprimer"
              >
                ×
              </button>
            </div>
          ))}
        </nav>

        <p className="sidebar-foot">{scopeLabel}</p>
      </aside>
    </>
  );
}
