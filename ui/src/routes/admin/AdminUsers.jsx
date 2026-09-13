import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { fetchUsers, relativeTime, UnauthorizedError } from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import * as m from "motion/react-m";
import AdminAvatar from "../../components/admin/AdminAvatar.jsx";
import { rise, stagger } from "../../lib/motion.js";

const PAGE_SIZE = 20;

/**
 * The account table. Filters live in the URL (?q=&role=&method=&page=), so a
 * filtered view survives a reload, the back button, and being pasted to
 * another admin.
 */
export default function AdminUsers() {
  const { onUnauthorized } = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const role = params.get("role") ?? "";
  const method = params.get("method") ?? "";
  const page = Math.max(1, Number(params.get("page")) || 1);

  const [draft, setDraft] = useState(q);
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  function setFilter(key, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setParams(next, { replace: key === "q" });
  }

  // Search as you type, debounced: one request per pause, not per keystroke.
  useEffect(() => {
    if (draft === q) return undefined;
    const t = setTimeout(() => setFilter("q", draft.trim()), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft]);

  useEffect(() => {
    let cancelled = false;
    setFailed(false);
    fetchUsers({ q, role, method, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE })
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [q, role, method, page, onUnauthorized]);

  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="adm-page">
      <header className="adm-head">
        <div>
          <h1 className="adm-h1">Utilisateurs</h1>
          <p className="adm-sub">
            {data ? `${data.total} compte${data.total > 1 ? "s" : ""}` : "Chargement…"}
          </p>
        </div>
        <Link to="/admin/utilisateurs/nouveau" className="adm-btn adm-btn-primary">
          + Nouvel utilisateur
        </Link>
      </header>

      <div className="adm-toolbar">
        <input
          type="search"
          className="adm-input adm-search"
          placeholder="Rechercher un nom ou un e-mail…"
          aria-label="Rechercher"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <select
          className="adm-input"
          aria-label="Rôle"
          value={role}
          onChange={(e) => setFilter("role", e.target.value)}
        >
          <option value="">Tous les rôles</option>
          <option value="student">Élèves</option>
          <option value="admin">Admins</option>
        </select>
        <select
          className="adm-input"
          aria-label="Méthode de connexion"
          value={method}
          onChange={(e) => setFilter("method", e.target.value)}
        >
          <option value="">Toutes les méthodes</option>
          <option value="password">E-mail</option>
          <option value="google">Google</option>
        </select>
      </div>

      {failed && <p className="adm-alert">Impossible de charger les comptes.</p>}

      <div className="adm-table-wrap">
        <table className="adm-table adm-table-cards">
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Rôle</th>
              <th>Connexion</th>
              <th>E-mail</th>
              <th>Inscrit</th>
              <th>Dernière activité</th>
            </tr>
          </thead>
          {/* Keyed by the page's query so each new result set staggers in. */}
          <m.tbody
            key={`${q}|${role}|${method}|${page}|${data ? "ok" : "loading"}`}
            variants={stagger(0.03)}
            initial="hidden"
            animate="show"
          >
            {data?.items.map((u) => (
              <m.tr
                key={u.id}
                className="adm-row-link"
                tabIndex={0}
                variants={rise}
                onClick={() => navigate(`/admin/utilisateurs/${u.id}`)}
                onKeyDown={(e) =>
                  e.key === "Enter" && navigate(`/admin/utilisateurs/${u.id}`)
                }
              >
                {/* data-label: on a phone the table becomes one card per
                    account, and each cell shows its column name beside it. */}
                <td data-label="Utilisateur">
                  <span className="adm-cell-user">
                    <AdminAvatar
                      seed={u.id}
                      label={u.display_name || u.email}
                      size="sm"
                    />
                    <span className="adm-list-main">
                      {u.display_name ? (
                        <span className="adm-strong">{u.display_name}</span>
                      ) : (
                        <span className="adm-noname">Sans nom</span>
                      )}
                      <span className="adm-muted">{u.email}</span>
                    </span>
                  </span>
                </td>
                <td data-label="Rôle">
                  <span className={`adm-tag adm-tag-${u.role}`}>
                    {u.role === "admin" ? "Admin" : "Élève"}
                  </span>
                </td>
                <td data-label="Connexion">
                  {u.auth_method === "google" ? "Google" : "E-mail"}
                </td>
                <td data-label="E-mail">
                  <span
                    className={`adm-tag ${u.email_verified ? "adm-tag-ok" : "adm-tag-dim"}`}
                  >
                    {u.email_verified ? "Confirmé" : "Non confirmé"}
                  </span>
                </td>
                <td data-label="Inscrit" className="adm-muted">
                  {relativeTime(u.created_at)}
                </td>
                <td data-label="Activité" className="adm-muted">
                  {relativeTime(u.last_login_at)}
                </td>
              </m.tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="adm-empty">
                  Aucun compte ne correspond.
                </td>
              </tr>
            )}
            {!data &&
              !failed &&
              [0, 1, 2, 3].map((i) => (
                <tr key={i} aria-hidden="true">
                  <td colSpan={6}>
                    <div className="adm-skel adm-skel-row" />
                  </td>
                </tr>
              ))}
          </m.tbody>
        </table>
      </div>

      {data && pages > 1 && (
        <nav className="adm-pager" aria-label="Pagination">
          <button
            className="adm-btn"
            disabled={page <= 1}
            onClick={() => setFilter("page", String(page - 1))}
          >
            ← Précédent
          </button>
          <span className="adm-muted">
            Page {page} / {pages}
          </span>
          <button
            className="adm-btn"
            disabled={page >= pages}
            onClick={() => setFilter("page", String(page + 1))}
          >
            Suivant →
          </button>
        </nav>
      )}
    </div>
  );
}
