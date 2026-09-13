import { useEffect, useState } from "react";
import { Link, Navigate, NavLink, Outlet } from "react-router-dom";
import {
  fetchAdminWhoAmI,
  ForbiddenError,
  UnauthorizedError,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import "./admin.css";

/**
 * Fahem Console: the admin shell (Phase 8).
 *
 * Deliberately NOT inside AppLayout. The student app is a study space - warm,
 * roomy, one thing at a time. The console is an operations tool - dense tables,
 * a dark command bar, monospace ids - so it gets its own layout, its own
 * stylesheet scoped under `.adm`, and none of the student sidebar. It is the
 * same deployment, the same session and the same API; only the frame differs.
 *
 * It is also where the gate lives for every /admin/* page, so each page does
 * not re-implement it:
 *   1. App.jsx registers /admin/* only when /auth/me says admin - a student
 *      never mounts this component.
 *   2. Before drawing anything, this asks the server (/admin/whoami). The
 *      client's role can be stale (demoted in another tab, or by the script),
 *      so nothing admin-looking renders until the server says yes now.
 * The server check on every API call is the one that actually holds; these
 * two only decide what is drawn.
 */
export default function AdminLayout() {
  const { user, logout, onUnauthorized } = useAuth();
  // checking | ok | forbidden | failed
  const [gate, setGate] = useState("checking");
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAdminWhoAmI()
      .then(() => !cancelled && setGate("ok"))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else if (err instanceof ForbiddenError) setGate("forbidden");
        else setGate("failed");
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  if (gate === "forbidden") return <Navigate to="/" replace />;

  if (gate !== "ok") {
    return (
      <div className="adm adm-boot" role="status">
        {gate === "checking" ? (
          <span className="adm-spinner" aria-label="Vérification de l'accès…" />
        ) : (
          <p>
            Impossible de vérifier l'accès administrateur.{" "}
            <button className="adm-link" onClick={() => window.location.reload()}>
              Réessayer
            </button>
          </p>
        )}
      </div>
    );
  }

  const close = () => setNavOpen(false);
  const navClass = ({ isActive }) => `adm-nav-link${isActive ? " is-active" : ""}`;
  const label = user?.display_name || user?.email || "Admin";

  return (
    <div className={`adm${navOpen ? " adm-nav-open" : ""}`}>
      <header className="adm-bar">
        <button
          className="adm-burger"
          aria-label="Menu"
          aria-expanded={navOpen}
          onClick={() => setNavOpen((v) => !v)}
        >
          <span />
        </button>
        <Link to="/admin" className="adm-brand" onClick={close}>
          <span className="adm-brand-mark" aria-hidden="true">
            F
          </span>
          <span>
            Fahem <strong>Console</strong>
          </span>
        </Link>
        <span className="adm-env">Administration</span>

        <div className="adm-bar-right">
          <Link to="/" className="adm-bar-link">
            ↩ Retour à l'app
          </Link>
          <span className="adm-who" title={user?.email}>
            <span className="adm-avatar" aria-hidden="true">
              {label.charAt(0).toUpperCase()}
            </span>
            <span className="adm-who-name">{label}</span>
          </span>
          <button className="adm-bar-link" onClick={logout}>
            Déconnexion
          </button>
        </div>
      </header>

      <div className="adm-body">
        <aside className="adm-rail" aria-label="Navigation administration">
          <p className="adm-rail-title">Général</p>
          <NavLink to="/admin" end className={navClass} onClick={close}>
            <span className="adm-ico" aria-hidden="true">
              ◧
            </span>
            Tableau de bord
          </NavLink>
          <p className="adm-rail-title">Gestion</p>
          <NavLink to="/admin/utilisateurs" className={navClass} onClick={close}>
            <span className="adm-ico" aria-hidden="true">
              ◉
            </span>
            Utilisateurs
          </NavLink>
          <NavLink to="/admin/chapitres" className={navClass} onClick={close}>
            <span className="adm-ico" aria-hidden="true">
              ▤
            </span>
            Chapitres
          </NavLink>
          {/* Also here, not only in the bar: the bar's copy is hidden on a
              phone, and the console must never be a dead end. */}
          <p className="adm-rail-title">Fahem</p>
          <Link to="/" className="adm-nav-link">
            <span className="adm-ico" aria-hidden="true">
              ↩
            </span>
            Retour à l'app
          </Link>
          <p className="adm-rail-foot">
            Les rôles se gèrent en ligne de commande :<code>promote_admin.py</code>
          </p>
        </aside>
        {navOpen && <div className="adm-scrim" onClick={close} aria-hidden="true" />}

        <main className="adm-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
