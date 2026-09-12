import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/authContext.js";
import Button from "./ui/Button.jsx";
import VerifyEmailBanner from "./VerifyEmailBanner.jsx";

/**
 * The header every authenticated route sits under.
 *
 * One place for the brand, the freeform-chat entry point and the account
 * controls, so a new route gets all three by being a child of this rather
 * than by remembering to re-implement them. The account block used to live at
 * the bottom of the chat's sidebar; it moved here in Phase 3b, because a
 * second logout button on one screen and none on the others is exactly the
 * inconsistency this layout exists to prevent.
 */
export default function AppLayout() {
  const { user, logout } = useAuth();

  const label = user?.display_name || user?.email || "Compte";
  const initial = label.trim().charAt(0).toUpperCase() || "?";

  return (
    <div className="shell">
      <header className="appbar">
        <Link to="/" className="appbar-brand">
          Fahem
        </Link>

        <nav className="appbar-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `appbar-link${isActive ? " appbar-link-on" : ""}`
            }
          >
            Chapitres
          </NavLink>
          {/* The freeform path: reachable from anywhere, without going
              through a chapter first. */}
          <NavLink
            to="/chat"
            className={({ isActive }) =>
              `appbar-cta${isActive ? " appbar-cta-on" : ""}`
            }
          >
            Poser une question
          </NavLink>
        </nav>

        <div className="appbar-account">
          <span className="account-avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="appbar-name" title={user?.email || label}>
            {label}
          </span>
          <Button variant="secondary" size="sm" className="btn-logout" onClick={logout}>
            Déconnexion
          </Button>
        </div>
      </header>

      <VerifyEmailBanner />

      <div className="shell-body">
        <Outlet />
      </div>
    </div>
  );
}
