import { Link, NavLink, useLocation } from "react-router-dom";
import Icon, { LogoMark } from "./ui/Icon.jsx";
import ThemeToggle from "./ThemeToggle.jsx";
import { useAuth } from "../lib/authContext.js";
import { isAdmin } from "../lib/auth.js";
import { profileLabel } from "../lib/profile.js";
import { SCOPE_LABEL } from "../config.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { MODES } from "../lib/learning.js";

/**
 * The app's one sidebar: where a student is, where they can go, and who they
 * are signed in as.
 *
 * It replaces the top appbar's navigation role (Phase 6). It briefly carried
 * the chat's discussions list as well; that moved to the chat's Historique
 * panel, so this column is navigation and identity only.
 *
 * Only real destinations. Fahem has chapters and a freeform chat; it has no
 * leaderboard, shop, wallet or live sessions, so there are no items for them.
 * A nav entry that leads nowhere is worse than one that is missing: it makes
 * the product feel broken rather than small.
 */
export default function AppSidebar({ onNavigate }) {
  const { user, logout, editProfile } = useAuth();
  const profile = profileLabel(user);

  const label = user?.display_name || user?.email || "Compte";
  const initial = label.trim().charAt(0).toUpperCase() || "?";

  const linkClass = ({ isActive }) => `appnav-link${isActive ? " appnav-link-on" : ""}`;
  // The chat's two modes, each its own entry: highlighted while the chat is
  // open in it (the chat publishes its mode through the sessions context).
  const { chatMode } = useChatSessions();
  const { pathname } = useLocation();
  const modes = chatMode.guided ? ["full", "guided"] : [];

  return (
    <aside className="appnav" aria-label="Navigation principale">
      <Link to="/" className="appnav-brand" onClick={onNavigate}>
        <LogoMark size={30} />
        <span className="appnav-brand-name">Fahem</span>
      </Link>

      <nav aria-label="Sections">
        <ul className="appnav-list">
          <li>
            {/* `end`, so "Chapitres" is only current on / and not on every
                route beneath it. */}
            <NavLink to="/" end className={linkClass} onClick={onNavigate}>
              <Icon name="home" />
              Chapitres
            </NavLink>
          </li>
          <li>
            <NavLink to="/chat" className={linkClass} onClick={onNavigate}>
              <Icon name="chat" />
              Poser une question
            </NavLink>
            {modes.length > 0 && (
              <ul className="appnav-sublist" aria-label="Modes de réponse">
                {modes.map((mode) => {
                  const on = pathname === "/chat" && chatMode.current === mode;
                  return (
                    <li key={mode}>
                      <Link
                        to="/chat"
                        state={{ mode }}
                        className={`appnav-link appnav-sublink${on ? " appnav-sublink-on" : ""}`}
                        aria-current={on ? "true" : undefined}
                        title={MODES[mode].title}
                        onClick={onNavigate}
                      >
                        <Icon name={MODES[mode].icon} size={16} />
                        {MODES[mode].label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </li>
          <li>
            <NavLink to="/progression" className={linkClass} onClick={onNavigate}>
              <Icon name="progress" />
              Ma progression
            </NavLink>
          </li>
          {/* Phase 7. Not rendered at all for a student - absent from the DOM,
              not disabled - so there is nothing to find, inspect or re-enable.
              It is still only a convenience: the route and the server both
              refuse a non-admin independently of whether this link exists. */}
          {isAdmin(user) && (
            <li>
              <NavLink to="/admin" className={linkClass} onClick={onNavigate}>
                <Icon name="admin" />
                Administration
              </NavLink>
            </li>
          )}
        </ul>
      </nav>

      {/* No discussions list here any more: it lives in the chat's own
          Historique panel (HistoryPanel.jsx). Navigation and history are
          different kinds of thing, and stacking them in one column squeezed
          both. */}

      <div className="appnav-foot">
        {/* The student's class, and the way to change it. An admin without
            a profile keeps the corpus scope line instead. */}
        {profile ? (
          <button
            type="button"
            className="appnav-profile"
            onClick={() => {
              onNavigate?.();
              editProfile();
            }}
            aria-label={`Ma classe : ${profile}. Modifier`}
          >
            <span className="appnav-profile-label">Ma classe</span>
            <span className="appnav-profile-value">{profile}</span>
            <span className="appnav-profile-edit" aria-hidden="true">
              Modifier
            </span>
          </button>
        ) : (
          <p className="appnav-scope">{SCOPE_LABEL}</p>
        )}
        {/* Who is signed in, with the two things about this browser session
            beside it: the theme and signing out. Icon buttons, so the row
            stays one line instead of a full-width Déconnexion button. */}
        <div className="account">
          <span className="account-avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="account-id">
            <span className="account-name">{label}</span>
            {user?.email && <span className="account-mail">{user.email}</span>}
          </span>
          <span className="account-actions">
            <ThemeToggle className="appnav-theme" />
            <button
              type="button"
              className="icon-btn appnav-logout"
              onClick={logout}
              aria-label="Déconnexion"
              title="Déconnexion"
            >
              <Icon name="logout" />
            </button>
          </span>
        </div>
      </div>
    </aside>
  );
}
