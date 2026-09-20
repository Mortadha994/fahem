import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate, NavLink, useLocation, useOutlet } from "react-router-dom";
import { AnimatePresence, LazyMotion, MotionConfig, domMax } from "motion/react";
import * as m from "motion/react-m";
import {
  fetchAdminWhoAmI,
  fetchControls,
  ForbiddenError,
  UnauthorizedError,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import {
  AdminStatusContext,
  STATUS_LABELS,
  statusFrom,
} from "../../lib/adminStatus.js";
import AdminAvatar from "./AdminAvatar.jsx";
import CommandPalette from "./CommandPalette.jsx";
import Toaster from "./Toaster.jsx";
import ThemeToggle from "../ThemeToggle.jsx";
import {
  IconArrowLeft,
  IconBook,
  IconDashboard,
  IconGauge,
  IconLogout,
  IconMenu,
  IconSearch,
  IconUsers,
  IconX,
} from "./icons.jsx";
import "./admin.css";
// The console dressed in the "Industry" design system. Layered after
// admin.css because it is token overrides and frame treatment only - delete
// this one line to put the console back as it was.
import "./industry.css";

/**
 * Fahem Console: the admin shell.
 *
 * Deliberately NOT inside AppLayout. The student app is a study space; the
 * console is an operations tool, so it has its own layout and its own
 * stylesheet scoped under `.adm`. Same deployment, session and API.
 *
 * Organised around three things an admin always needs within reach:
 *   - where they are: a sidebar of four pages in two groups, the current one
 *     marked by a highlight that slides between links (Motion layoutId, the
 *     "shared layout" pattern), and the page title in the top bar;
 *   - the state of the AI: a status card in the sidebar and a pill in the top
 *     bar (active / en pause / garde-fou atteint), polled every POLL_MS and
 *     refreshed at once by anything that changes it (AdminStatusContext);
 *   - a way to anything: Ctrl+K opens the command palette - pages, the AI
 *     pause, account search.
 * Page changes cross-fade (AnimatePresence over the outlet).
 *
 * It is also where the gate lives for every /admin/* page:
 *   1. App.jsx registers /admin/* only when /auth/me says admin.
 *   2. Before drawing anything, this asks the server (/admin/whoami) - the
 *      client's role can be stale.
 * The server check on every API call is the one that actually holds.
 *
 * Motion: the console gets its own LazyMotion with domMax (layout animations
 * for the sliding highlights), separate from the student app's lighter
 * domAnimation; same reduced-motion rule.
 */

const POLL_MS = 30_000;

const NAV = [
  {
    title: "Pilotage",
    items: [
      { to: "/admin", end: true, label: "Tableau de bord", Icon: IconDashboard },
      { to: "/admin/ia", label: "Surveillance IA", Icon: IconGauge, status: true },
    ],
  },
  {
    title: "Contenu et comptes",
    items: [
      { to: "/admin/utilisateurs", label: "Utilisateurs", Icon: IconUsers },
      { to: "/admin/chapitres", label: "Chapitres", Icon: IconBook },
    ],
  },
];

/** The top bar's title for a path. */
function pageTitle(pathname) {
  if (pathname.startsWith("/admin/ia")) return "Surveillance IA";
  if (pathname === "/admin/utilisateurs/nouveau") return "Nouvel utilisateur";
  if (pathname.startsWith("/admin/utilisateurs/")) return "Utilisateur";
  if (pathname.startsWith("/admin/utilisateurs")) return "Utilisateurs";
  if (pathname.startsWith("/admin/chapitres/")) return "Chapitre";
  if (pathname.startsWith("/admin/chapitres")) return "Chapitres";
  return "Tableau de bord";
}

const NAV_SPRING = { type: "spring", visualDuration: 0.35, bounce: 0.18 };

export default function AdminLayout() {
  const { user, logout, onUnauthorized } = useAuth();
  const location = useLocation();
  const outlet = useOutlet();
  // checking | ok | forbidden | failed
  const [gate, setGate] = useState("checking");
  const [navOpen, setNavOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [controls, setControls] = useState(null);

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

  const refresh = useCallback(() => {
    fetchControls()
      .then(setControls)
      .catch((err) => {
        if (err instanceof UnauthorizedError) onUnauthorized();
      });
  }, [onUnauthorized]);

  useEffect(() => {
    if (gate !== "ok") return undefined;
    refresh();
    const id = setInterval(() => !document.hidden && refresh(), POLL_MS);
    return () => clearInterval(id);
  }, [gate, refresh]);

  // Ctrl+K / Cmd+K anywhere in the console.
  useEffect(() => {
    const onKey = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const status = statusFrom(controls);
  const statusValue = useMemo(
    () => ({ status, controls, refresh }),
    [status, controls, refresh]
  );

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

  const label = user?.display_name || user?.email || "Admin";
  // Following any sidebar link on a phone closes the menu it lives in.
  const closeNav = () => setNavOpen(false);
  // One key per top-level section, so moving between a list and its detail
  // pages is not a full cross-fade of the shell.
  const section = location.pathname.split("/").slice(0, 4).join("/");

  return (
    <LazyMotion features={domMax} strict>
      <MotionConfig reducedMotion="user">
        <AdminStatusContext.Provider value={statusValue}>
          <div className={`adm adm-shell${navOpen ? " adm-nav-open" : ""}`}>
            {/* Notifications at the bottom of the page, for every console screen. */}
            <Toaster>
              <aside className="adm-side" aria-label="Navigation administration">
                <div className="adm-side-top">
                  <Link to="/admin" className="adm-brand" onClick={closeNav}>
                    <span className="adm-brand-mark" aria-hidden="true">
                      ←
                    </span>
                    <span className="adm-brand-text">
                      Fahem
                      <small>Console</small>
                    </span>
                  </Link>
                  <button
                    className="adm-icon-btn adm-side-close"
                    aria-label="Fermer le menu"
                    onClick={() => setNavOpen(false)}
                  >
                    <IconX />
                  </button>
                </div>

                <button className="adm-search-btn" onClick={() => setPaletteOpen(true)}>
                  <IconSearch size={16} />
                  <span>Rechercher…</span>
                  <kbd>Ctrl K</kbd>
                </button>

                <nav className="adm-side-nav">
                  {NAV.map((group) => (
                    <div className="adm-side-group" key={group.title}>
                      <p className="adm-side-title">{group.title}</p>
                      {group.items.map(
                        ({ to, end, label: text, Icon, status: withStatus }) => (
                          <NavLink
                            key={to}
                            to={to}
                            end={end}
                            className="adm-side-link"
                            onClick={closeNav}
                          >
                            {({ isActive }) => (
                              <>
                                {isActive && (
                                  <m.span
                                    layoutId="adm-side-pill"
                                    className="adm-side-pill"
                                    transition={NAV_SPRING}
                                  />
                                )}
                                <Icon className="adm-side-icon" />
                                <span className="adm-side-label">{text}</span>
                                {withStatus && status && status !== "on" && (
                                  <span
                                    className={`adm-dot is-${status}`}
                                    title={STATUS_LABELS[status]}
                                  />
                                )}
                              </>
                            )}
                          </NavLink>
                        )
                      )}
                    </div>
                  ))}
                </nav>

                <Link
                  to="/admin/ia?onglet=controles"
                  className={`adm-status-card is-${status ?? "unknown"}`}
                  onClick={closeNav}
                >
                  <span className="adm-status-card-dot" aria-hidden="true" />
                  <span>
                    <span className="adm-status-card-title">
                      {status ? STATUS_LABELS[status] : "État de l'IA…"}
                    </span>
                    <span className="adm-status-card-sub">
                      {controls
                        ? `${Math.round((controls.budget.used / (controls.budget.limit || 1)) * 100)} % du budget du jour`
                        : "Chargement"}
                    </span>
                  </span>
                </Link>

                <div className="adm-side-foot">
                  <div className="adm-me">
                    <AdminAvatar seed={user?.id} label={label} />
                    <span className="adm-me-text">
                      <span className="adm-me-name">{label}</span>
                      <span className="adm-me-mail">{user?.email}</span>
                    </span>
                  </div>
                  <div className="adm-me-actions">
                    <ThemeToggle className="adm-theme" />
                    <Link to="/" className="adm-icon-btn" title="Retour à l'app">
                      <IconArrowLeft />
                      <span className="sr-only">Retour à l'app</span>
                    </Link>
                    <button
                      className="adm-icon-btn"
                      title="Déconnexion"
                      onClick={logout}
                    >
                      <IconLogout />
                      <span className="sr-only">Déconnexion</span>
                    </button>
                  </div>
                </div>
              </aside>
              {navOpen && (
                <div
                  className="adm-scrim"
                  onClick={() => setNavOpen(false)}
                  aria-hidden="true"
                />
              )}

              <div className="adm-content">
                <header className="adm-top">
                  <button
                    className="adm-icon-btn adm-top-menu"
                    aria-label="Menu"
                    aria-expanded={navOpen}
                    onClick={() => setNavOpen(true)}
                  >
                    <IconMenu />
                  </button>
                  <p className="adm-top-title">
                    <span className="adm-top-crumb">Console</span>
                    <span aria-hidden="true">/</span>
                    <span className="adm-top-page">{pageTitle(location.pathname)}</span>
                  </p>
                  <div className="adm-top-right">
                    {status && (
                      <Link
                        to="/admin/ia?onglet=controles"
                        className={`adm-pill is-${status}`}
                        aria-label={`${STATUS_LABELS[status]} — ouvrir les contrôles`}
                      >
                        <span className="adm-pill-dot" aria-hidden="true" />
                        {STATUS_LABELS[status]}
                      </Link>
                    )}
                    <button
                      className="adm-icon-btn adm-top-search"
                      aria-label="Rechercher"
                      onClick={() => setPaletteOpen(true)}
                    >
                      <IconSearch />
                    </button>
                  </div>
                </header>

                <main className="adm-main">
                  <AnimatePresence mode="wait" initial={false}>
                    <m.div
                      key={section}
                      className="adm-route"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.18, ease: "easeOut" }}
                    >
                      {outlet}
                    </m.div>
                  </AnimatePresence>
                </main>
              </div>

              <CommandPalette
                open={paletteOpen}
                onClose={() => setPaletteOpen(false)}
              />
            </Toaster>
          </div>
        </AdminStatusContext.Provider>
      </MotionConfig>
    </LazyMotion>
  );
}
