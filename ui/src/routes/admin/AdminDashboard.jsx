import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchAdminStats,
  fetchUsers,
  relativeTime,
  UnauthorizedError,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";

/** Console home: the numbers, the newest accounts, and the way to the rest. */
export default function AdminDashboard() {
  const { onUnauthorized } = useAuth();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchAdminStats(), fetchUsers({ limit: 6 })])
      .then(([s, page]) => {
        if (cancelled) return;
        setStats(s);
        setRecent(page.items);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  const pct = (n) => (stats?.users ? Math.round((n / stats.users) * 100) : 0);

  const cards = stats && [
    {
      label: "Comptes",
      value: stats.users,
      hint: `${stats.students} élèves · ${stats.admins} admin`,
    },
    {
      label: "Nouveaux (7 j)",
      value: stats.new_last_7_days,
      hint: "créés cette semaine",
    },
    {
      label: "Actifs (7 j)",
      value: stats.active_last_7_days,
      hint: `${pct(stats.active_last_7_days)} % des comptes`,
    },
    {
      label: "E-mail confirmé",
      value: stats.verified,
      hint: `${pct(stats.verified)} % des comptes`,
    },
  ];

  return (
    <div className="adm-page">
      <header className="adm-head">
        <div>
          <h1 className="adm-h1">Tableau de bord</h1>
          <p className="adm-sub">Vue d'ensemble des comptes Fahem.</p>
        </div>
        <Link to="/admin/utilisateurs/nouveau" className="adm-btn adm-btn-primary">
          + Nouvel utilisateur
        </Link>
      </header>

      {failed && <p className="adm-alert">Impossible de charger les statistiques.</p>}

      <section className="adm-stats" aria-label="Statistiques">
        {(cards ?? [0, 1, 2, 3]).map((c, i) =>
          c ? (
            <div className="adm-stat" key={c.label}>
              <span className="adm-stat-label">{c.label}</span>
              <span className="adm-stat-value">{c.value}</span>
              <span className="adm-stat-hint">{c.hint}</span>
            </div>
          ) : (
            <div className="adm-stat adm-skel" key={i} aria-hidden="true" />
          )
        )}
      </section>

      <div className="adm-grid-2">
        <section className="adm-panel">
          <header className="adm-panel-head">
            <h2 className="adm-h2">Derniers inscrits</h2>
            <Link to="/admin/utilisateurs" className="adm-link">
              Tout voir →
            </Link>
          </header>
          {recent === null && !failed ? (
            <div className="adm-skel adm-skel-block" aria-hidden="true" />
          ) : (
            <ul className="adm-list">
              {(recent ?? []).map((u) => (
                <li key={u.id}>
                  <Link to={`/admin/utilisateurs/${u.id}`} className="adm-list-row">
                    <span className="adm-avatar adm-avatar-sm" aria-hidden="true">
                      {(u.display_name || u.email).charAt(0).toUpperCase()}
                    </span>
                    <span className="adm-list-main">
                      <span className="adm-strong">{u.display_name || "—"}</span>
                      <span className="adm-muted">{u.email}</span>
                    </span>
                    <span className="adm-muted">{relativeTime(u.created_at)}</span>
                  </Link>
                </li>
              ))}
              {recent?.length === 0 && <li className="adm-empty">Aucun compte.</li>}
            </ul>
          )}
        </section>

        <section className="adm-panel">
          <header className="adm-panel-head">
            <h2 className="adm-h2">Méthodes de connexion</h2>
          </header>
          {stats && (
            <div className="adm-split">
              <div
                className="adm-bar-track"
                role="img"
                aria-label={`${stats.password_accounts} comptes e-mail, ${stats.google_accounts} comptes Google`}
              >
                <span
                  className="adm-bar-fill"
                  style={{ width: `${pct(stats.password_accounts)}%` }}
                />
              </div>
              <dl className="adm-legend">
                <div>
                  <dt>
                    <i className="adm-dot adm-dot-a" /> E-mail + mot de passe
                  </dt>
                  <dd>{stats.password_accounts}</dd>
                </div>
                <div>
                  <dt>
                    <i className="adm-dot adm-dot-b" /> Google
                  </dt>
                  <dd>{stats.google_accounts}</dd>
                </div>
              </dl>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
