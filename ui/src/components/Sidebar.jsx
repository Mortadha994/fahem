export default function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  open,
  onClose,
  scopeLabel,
  user,
  onLogout,
}) {
  // Google may return neither name nor email; the initial still needs a
  // character, and "?" is better than an empty circle.
  const label = user?.display_name || user?.email || "Compte";
  const initial = label.trim().charAt(0).toUpperCase() || "?";
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

        {user && (
          <div className="account">
            <span className="account-avatar" aria-hidden="true">
              {initial}
            </span>
            <span className="account-id">
              <span className="account-name" title={label}>
                {label}
              </span>
              {user.email && user.email !== label && (
                <span className="account-mail" title={user.email}>
                  {user.email}
                </span>
              )}
            </span>
            <button
              type="button"
              className="btn-logout"
              onClick={onLogout}
              title="Se déconnecter"
            >
              Déconnexion
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
