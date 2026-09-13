import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import Button from "./ui/Button.jsx";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { ago } from "../lib/relativeTime.js";
import { groupByDay, hasQuestion, statusOf } from "../lib/sessionGroups.js";
import { SPRING_ENTER, rise, stagger } from "../lib/motion.js";

/**
 * The chat's history, as a panel that slides over from the right.
 *
 * Replaces the discussions list that used to sit inside the app sidebar,
 * under the navigation: two different kinds of thing - where you can go, and
 * everything you have ever asked - stacked in one narrow column, with the
 * list squeezing the account block and every title cut after a few words.
 * Here the list has the width to show whole titles, a search, and day groups.
 *
 * A modal dialog: focus moves to the search on open, Tab stays inside, Escape
 * or the scrim closes it, and Chat.jsx puts focus back on the button that
 * opened it. Up/Down move between results; Enter in the search opens the
 * first match.
 *
 * Deleting still asks first (unchanged from SessionHistory): localStorage is
 * the only copy of a transcript, so the first click turns the control into
 * "Supprimer ?" and the second confirms. Blur or Escape backs out.
 */

const STATUS = {
  clean: { label: "Corrigé", glyph: "✓" },
  warned: { label: "Syntaxe à vérifier", glyph: "!" },
  open: { label: "En cours", glyph: "" },
};

export default function HistoryPanel({ open, onClose }) {
  // The dialog only exists while open, so its search and any half-finished
  // delete confirmation start fresh every time without an effect resetting
  // them; AnimatePresence keeps it mounted long enough to slide out.
  return (
    <AnimatePresence>
      {open && <HistoryDialog key="history" onClose={onClose} />}
    </AnimatePresence>
  );
}

function HistoryDialog({ onClose }) {
  const { sessions, activeId, setActiveId, deleteSession } = useChatSessions();
  const [query, setQuery] = useState("");
  const [confirmingId, setConfirmingId] = useState(null);
  const panelRef = useRef(null);
  const searchRef = useRef(null);

  // Blank "Nouvelle discussion" rows are noise in a history - except the one
  // that is open right now, which the student would otherwise not find.
  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = sessions.filter(
      (s) =>
        (hasQuestion(s) || s.id === activeId) &&
        (!q || s.title.toLowerCase().includes(q))
    );
    return groupByDay(list);
  }, [sessions, activeId, query]);
  const resultCount = groups.reduce((n, g) => n + g.items.length, 0);

  useEffect(() => {
    // After the slide has started, so the browser does not scroll the panel
    // into view mid-animation.
    const t = setTimeout(() => searchRef.current?.focus(), 30);
    return () => clearTimeout(t);
  }, []);

  // Escape is heard on the document, not only inside the panel: after a
  // delete the focused button no longer exists, focus falls back to <body>,
  // and a panel-level handler would never see the key. The delete confirm's
  // own Escape stops propagation, so backing out of it does not also close.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const rowButtons = () => [
    ...(panelRef.current?.querySelectorAll(".history-row-btn") ?? []),
  ];

  function pick(id) {
    setActiveId(id);
    onClose();
  }

  function onKeyDown(e) {
    // Keep Tab inside the dialog.
    if (e.key === "Tab") {
      const focusables = [
        ...panelRef.current.querySelectorAll("button:not([disabled]), input"),
      ];
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      const rows = rowButtons();
      if (!rows.length) return;
      e.preventDefault();
      const i = rows.indexOf(document.activeElement);
      const next =
        e.key === "ArrowDown"
          ? rows[i < 0 ? 0 : Math.min(rows.length - 1, i + 1)]
          : i <= 0
            ? searchRef.current
            : rows[i - 1];
      next.focus();
    }
  }

  return (
    <>
      <m.div
        key="scrim"
        className="history-scrim"
        aria-hidden="true"
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      />
      <m.aside
        key="panel"
        ref={panelRef}
        className="history-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="history-title"
        onKeyDown={onKeyDown}
        initial={{ x: "100%", opacity: 0.6 }}
        animate={{
          x: 0,
          opacity: 1,
          transition: { ...SPRING_ENTER, bounce: 0.12 },
        }}
        exit={{ x: "100%", opacity: 0, transition: { duration: 0.22 } }}
      >
        <header className="history-head">
          <h2 id="history-title" className="history-title">
            Historique
          </h2>
          <Button
            variant="ghost"
            size="sm"
            className="history-close"
            onClick={onClose}
            aria-label="Fermer l'historique"
          >
            ×
          </Button>
        </header>

        <div className="history-search">
          <span className="history-search-icon" aria-hidden="true">
            ⌕
          </span>
          <input
            ref={searchRef}
            type="search"
            className="history-search-input"
            placeholder="Chercher une discussion…"
            aria-label="Chercher une discussion"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== "Enter" || !groups[0]) return;
              // preventDefault matters: closing hands focus to the Historique
              // button, and without it the rest of this same Enter press
              // lands on that button as a click and reopens the panel.
              e.preventDefault();
              pick(groups[0].items[0].id);
            }}
          />
        </div>
        <p className="sr-only" role="status" aria-live="polite">
          {query ? `${resultCount} résultat${resultCount > 1 ? "s" : ""}` : ""}
        </p>

        <div className="history-body">
          {groups.length === 0 ? (
            <p className="history-empty">
              {query
                ? "Aucune discussion ne correspond à ta recherche."
                : "Aucune discussion pour l'instant. Ta première question apparaîtra ici."}
            </p>
          ) : (
            <m.div variants={stagger(0.05, 0.08)} initial="hidden" animate="show">
              {groups.map((g) => (
                <m.section
                  key={g.key}
                  className="history-group"
                  aria-labelledby={`history-${g.key}`}
                  variants={rise}
                >
                  <h3 id={`history-${g.key}`} className="history-group-title">
                    {g.label}
                  </h3>
                  <ul className="history-list">
                    <AnimatePresence initial={false}>
                      {g.items.map((s) => {
                        const status = statusOf(s);
                        const isActive = s.id === activeId;
                        const confirming = confirmingId === s.id;
                        return (
                          <m.li
                            key={s.id}
                            className={`history-row${isActive ? " is-active" : ""}`}
                            exit={{
                              opacity: 0,
                              height: 0,
                              transition: { duration: 0.2 },
                            }}
                          >
                            <button
                              type="button"
                              className="history-row-btn"
                              aria-current={isActive ? "true" : undefined}
                              onClick={() => pick(s.id)}
                            >
                              <span
                                className={`history-status is-${status}`}
                                title={STATUS[status].label}
                                aria-hidden="true"
                              >
                                {STATUS[status].glyph}
                              </span>
                              <span className="history-row-body">
                                <span className="history-row-title">{s.title}</span>
                                <span className="history-row-meta">
                                  Chapitre {s.chapitre}
                                  {hasQuestion(s) && s.updatedAt
                                    ? ` · ${ago(s.updatedAt)}`
                                    : ""}
                                  {status !== "open" && (
                                    <span className="sr-only">
                                      {" "}
                                      · {STATUS[status].label}
                                    </span>
                                  )}
                                </span>
                              </span>
                            </button>
                            <Button
                              variant={confirming ? "danger" : "ghost"}
                              size="sm"
                              className={`history-del${confirming ? " is-confirming" : ""}`}
                              onClick={(e) => {
                                if (confirming) {
                                  deleteSession(s.id);
                                  setConfirmingId(null);
                                  // The row - and this button - is going away;
                                  // keep focus inside the dialog.
                                  searchRef.current?.focus();
                                } else {
                                  setConfirmingId(s.id);
                                  // Focus explicitly: blur is what cancels, and a
                                  // click does not reliably focus a button (Safari).
                                  e.currentTarget.focus();
                                }
                              }}
                              onBlur={() =>
                                setConfirmingId((cur) => (cur === s.id ? null : cur))
                              }
                              onKeyDown={(e) => {
                                if (e.key !== "Escape" || !confirming) return;
                                // Backs out of the confirm without closing the panel.
                                e.stopPropagation();
                                setConfirmingId(null);
                              }}
                              aria-label={
                                confirming
                                  ? `Confirmer la suppression de ${s.title}`
                                  : `Supprimer ${s.title}`
                              }
                              title={confirming ? "Confirmer" : "Supprimer"}
                            >
                              {confirming ? "Supprimer ?" : "×"}
                            </Button>
                          </m.li>
                        );
                      })}
                    </AnimatePresence>
                  </ul>
                </m.section>
              ))}
            </m.div>
          )}
        </div>

        <footer className="history-foot" aria-hidden="true">
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> naviguer
          </span>
          <span>
            <kbd>Entrée</kbd> ouvrir
          </span>
          <span>
            <kbd>Échap</kbd> fermer
          </span>
        </footer>
      </m.aside>
    </>
  );
}
