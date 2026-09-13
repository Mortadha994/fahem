import { Link, NavLink, useLocation } from "react-router-dom";
import SessionHistory from "./SessionHistory.jsx";
import Button from "./ui/Button.jsx";
import { useAuth } from "../lib/authContext.js";
import { isAdmin } from "../lib/auth.js";
import { SCOPE_LABEL } from "../config.js";

/**
 * The app's one sidebar: where a student is, where they can go, and who they
 * are signed in as.
 *
 * It replaces the top appbar's navigation role (Phase 6) and absorbs the
 * chat's own session-history sidebar, which used to sit beside it on /chat -
 * two sidebars and two bars on one screen, the audit's P2-5. The history
 * appears here, as a section, only on the route it belongs to.
 *
 * Only real destinations. Fahem has chapters and a freeform chat; it has no
 * leaderboard, shop, wallet or live sessions, so there are no items for them.
 * A nav entry that leads nowhere is worse than one that is missing: it makes
 * the product feel broken rather than small.
 */
export default function AppSidebar({ onNavigate }) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const onChat = pathname === "/chat";

  const label = user?.display_name || user?.email || "Compte";
  const initial = label.trim().charAt(0).toUpperCase() || "?";

  const linkClass = ({ isActive }) => `appnav-link${isActive ? " appnav-link-on" : ""}`;

  return (
    <aside className="appnav" aria-label="Navigation principale">
      <Link to="/" className="appnav-brand" onClick={onNavigate}>
        <span className="brand-mark" aria-hidden="true">
          ←
        </span>
        Fahem
      </Link>

      <nav aria-label="Sections">
        <ul className="appnav-list">
          <li>
            {/* `end`, so "Chapitres" is only current on / and not on every
                route beneath it. */}
            <NavLink to="/" end className={linkClass} onClick={onNavigate}>
              Chapitres
            </NavLink>
          </li>
          <li>
            <NavLink to="/chat" className={linkClass} onClick={onNavigate}>
              Poser une question
            </NavLink>
          </li>
          {/* Phase 7. Not rendered at all for a student - absent from the DOM,
              not disabled - so there is nothing to find, inspect or re-enable.
              It is still only a convenience: the route and the server both
              refuse a non-admin independently of whether this link exists. */}
          {isAdmin(user) && (
            <li>
              <NavLink to="/admin" className={linkClass} onClick={onNavigate}>
                Administration
              </NavLink>
            </li>
          )}
        </ul>
      </nav>

      {/* The discussions list, only where it means anything. */}
      {onChat && <SessionHistory onNavigate={onNavigate} />}

      <div className="appnav-foot">
        <p className="appnav-scope">{SCOPE_LABEL}</p>
        <div className="account">
          <span className="account-avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="account-id">
            <span className="account-name">{label}</span>
            {user?.email && <span className="account-mail">{user.email}</span>}
          </span>
        </div>
        <Button
          variant="secondary"
          size="sm"
          className="appnav-logout"
          onClick={logout}
        >
          Déconnexion
        </Button>
      </div>
    </aside>
  );
}
