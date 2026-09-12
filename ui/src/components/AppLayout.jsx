import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import AppSidebar from "./AppSidebar.jsx";
import ChatSessionsProvider from "./ChatSessionsProvider.jsx";
import VerifyEmailBanner from "./VerifyEmailBanner.jsx";
import Button from "./ui/Button.jsx";

/**
 * The shell every authenticated route sits in.
 *
 * Phase 6 turns the top appbar into a persistent left sidebar. The nav, the
 * account block and - on /chat - the session history all live in that one
 * sidebar now, which is what finally removes the audit's "two stacked bars"
 * (P2-5): the chat no longer carries a bar of its own, because the burger and
 * the scope label it existed for are in the sidebar.
 *
 * Narrow viewports: the sidebar becomes a drawer behind a toggle, the same
 * pattern the chat's own sidebar already used, with the scrim and the
 * Escape-to-close it had. The mobile bar exists only to hold that toggle -
 * on a wide screen there is no horizontal bar at all.
 *
 * ChatSessionsProvider wraps both the sidebar and the routes, since the
 * session list is now read in two places (see chatSessionsContext.js).
 */
export default function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);

  // Closing on navigation is handled by the links themselves (onNavigate
  // below), not by an effect watching the pathname: every way out of the
  // drawer goes through a click here, the scrim, or Escape, and while it is
  // open the scrim covers everything else - so there is no navigation this
  // could miss, and no reason to spend a second render pass on it.

  // Escape closes it, as it does the delete confirmation in the session list.
  useEffect(() => {
    if (!navOpen) return undefined;
    const onKey = (e) => e.key === "Escape" && setNavOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [navOpen]);

  return (
    <ChatSessionsProvider>
      <div className={`shell${navOpen ? " shell-nav-open" : ""}`}>
        {/* Narrow screens only. Nothing here duplicates the sidebar: it is a
            toggle and the brand, so there is something to tap and something
            to recognise. */}
        <header className="mobilebar">
          <Button
            variant="ghost"
            className="btn-burger"
            aria-label="Afficher la navigation"
            aria-expanded={navOpen}
            aria-controls="app-nav"
            onClick={() => setNavOpen((v) => !v)}
          >
            ☰
          </Button>
          <Link to="/" className="mobilebar-brand">
            Fahem
          </Link>
        </header>

        <div
          className={`scrim ${navOpen ? "scrim-open" : ""}`}
          onClick={() => setNavOpen(false)}
          aria-hidden="true"
        />

        <div id="app-nav" className="appnav-holder">
          <AppSidebar onNavigate={() => setNavOpen(false)} />
        </div>

        <div className="shell-main">
          <VerifyEmailBanner />
          <div className="shell-body">
            <Outlet />
          </div>
        </div>
      </div>
    </ChatSessionsProvider>
  );
}
