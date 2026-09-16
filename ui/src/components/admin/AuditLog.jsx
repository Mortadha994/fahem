import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import {
  errorMessage,
  fetchAudit,
  fullDate,
  revertAudit,
  UnauthorizedError,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import {
  CATEGORY_OF,
  changesOf,
  dayLabel,
  timeOf,
  titleOf,
} from "../../lib/auditFormat.js";
import AdminAvatar from "./AdminAvatar.jsx";
import {
  IconClock,
  IconCornerDownLeft,
  IconSearch,
  IconShield,
  IconSliders,
  IconUser,
} from "./icons.jsx";

/**
 * Journal des actions: every change an admin made from the console, as a
 * timeline - who, when, what, and what it was before.
 *
 *   - filters by family (IA, Comptes, Files d'attente) and a search on the
 *     admin's e-mail or the account concerned, both server-side
 *     (GET /admin/audit), with "Charger plus" paging;
 *   - grouped by day, each entry showing its changes as before -> after;
 *   - an account action links to the account;
 *   - a settings change can be put back ("Rétablir", confirmed inline):
 *     POST /admin/audit/{id}/revert, which is itself logged.
 *
 * `version` changes whenever the controls above change something, so the log
 * shows the new entry at once; `onReverted` hands the controls panel the
 * settings a revert produced.
 */

const FILTERS = [
  { id: "", label: "Tout" },
  { id: "ia", label: "IA" },
  { id: "comptes", label: "Comptes" },
  { id: "files", label: "Files d'attente" },
];

const CATEGORY_ICON = {
  ia: IconSliders,
  comptes: IconUser,
  files: IconClock,
  autre: IconShield,
};

const PAGE = 25;

export default function AuditLog({ version = 0, onReverted, queueLabels = {} }) {
  const { onUnauthorized } = useAuth();
  const [category, setCategory] = useState("");
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState(null);
  const [nextBefore, setNextBefore] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [confirming, setConfirming] = useState(null); // entry id
  const [reverting, setReverting] = useState(null);
  const [flash, setFlash] = useState(null);
  const request = useRef(0);

  const fail = useCallback(
    (err) => {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
    },
    [onUnauthorized]
  );

  // Search as you type, debounced.
  useEffect(() => {
    const t = setTimeout(() => setQuery(draft.trim()), 250);
    return () => clearTimeout(t);
  }, [draft]);

  // First page, again whenever the filter, the search or the controls change.
  useEffect(() => {
    const id = ++request.current;
    fetchAudit({ category: category || undefined, q: query || undefined, limit: PAGE })
      .then((page) => {
        if (id !== request.current) return;
        setItems(page.items);
        setNextBefore(page.next_before);
        setError(null);
      })
      .catch((err) => id === request.current && fail(err));
  }, [category, query, version, fail]);

  async function loadMore() {
    setLoadingMore(true);
    try {
      const page = await fetchAudit({
        category: category || undefined,
        q: query || undefined,
        limit: PAGE,
        before: nextBefore,
      });
      setItems((list) => [...list, ...page.items]);
      setNextBefore(page.next_before);
    } catch (err) {
      fail(err);
    } finally {
      setLoadingMore(false);
    }
  }

  async function revert(entry) {
    setReverting(entry.id);
    setError(null);
    try {
      const controls = await revertAudit(entry.id);
      setConfirming(null);
      setFlash("Réglages rétablis.");
      onReverted?.(controls);
    } catch (err) {
      fail(err);
    } finally {
      setReverting(null);
    }
  }

  // Entries grouped under their day, keeping the newest-first order.
  const groups = [];
  for (const entry of items ?? []) {
    const label = dayLabel(entry.at);
    const last = groups[groups.length - 1];
    if (last?.label === label) last.entries.push(entry);
    else groups.push({ label, entries: [entry] });
  }

  return (
    <m.section className="adm-panel log" aria-label="Journal des actions">
      <header className="log-head">
        <div>
          <h2 className="adm-h2">Journal des actions</h2>
          <p className="adm-muted adm-small">
            Qui a changé quoi, et quand. Un changement de réglage peut être rétabli.
          </p>
        </div>
        <label className="log-search">
          <IconSearch size={16} />
          <input
            className="adm-input"
            type="search"
            placeholder="Admin ou compte…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            aria-label="Rechercher dans le journal"
          />
        </label>
      </header>

      <div className="adm-seg log-filters" role="radiogroup" aria-label="Type d'action">
        {FILTERS.map((f) => (
          <button
            key={f.id || "all"}
            type="button"
            role="radio"
            aria-checked={category === f.id}
            className={`adm-seg-btn${category === f.id ? " is-on" : ""}`}
            onClick={() => setCategory(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {flash && (
        <p className="adm-notice" role="status">
          {flash}
        </p>
      )}
      {error && (
        <p className="adm-alert" role="alert">
          {error}
        </p>
      )}

      {items === null ? (
        <div className="adm-skel adm-skel-block" aria-hidden="true" />
      ) : items.length === 0 ? (
        <p className="log-empty">
          {query || category
            ? "Aucune action ne correspond à ce filtre."
            : "Aucune action pour l'instant. Chaque changement fait depuis la console apparaîtra ici."}
        </p>
      ) : (
        <div className="log-days">
          {groups.map((group) => (
            <section key={group.label} className="log-day">
              <h3 className="log-day-title">{group.label}</h3>
              <ol className="log-list">
                <AnimatePresence initial={false}>
                  {group.entries.map((entry) => {
                    const category_ = CATEGORY_OF(entry.action);
                    const Icon = CATEGORY_ICON[category_];
                    const changes = changesOf(entry);
                    const reason =
                      entry.action === "user.suspend" ? entry.detail?.reason : null;
                    return (
                      <m.li
                        key={entry.id}
                        layout="position"
                        className={`log-entry is-${category_}`}
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <span className="log-icon" aria-hidden="true">
                          <Icon size={15} />
                        </span>
                        <div className="log-body">
                          <p className="log-title">
                            <span className="adm-strong">
                              {titleOf(entry, (model) => queueLabels[model] ?? model)}
                            </span>
                            {entry.action.startsWith("user.") && entry.target && (
                              <>
                                {" — "}
                                {entry.target_id ? (
                                  <Link
                                    className="log-target"
                                    to={`/admin/utilisateurs/${entry.target_id}`}
                                  >
                                    {entry.target}
                                  </Link>
                                ) : (
                                  <span className="log-target">{entry.target}</span>
                                )}
                              </>
                            )}
                            <time
                              className="log-time"
                              dateTime={entry.at}
                              title={fullDate(entry.at)}
                            >
                              {timeOf(entry.at)}
                            </time>
                          </p>

                          {changes.length > 0 && (
                            <ul className="log-changes">
                              {changes.map((c) => (
                                <li key={c.key}>
                                  <span className="log-field">{c.label}</span>
                                  <span className="log-old">{c.old}</span>
                                  <span className="log-arrow" aria-label="devient">
                                    →
                                  </span>
                                  <span className="log-new">{c.new}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                          {reason && <p className="log-reason">« {reason} »</p>}
                          {entry.action === "settings.revert" && (
                            <p className="adm-muted adm-small log-note">
                              Annule l'action n° {entry.target}
                            </p>
                          )}

                          <div className="log-meta">
                            <span className="log-by">
                              <AdminAvatar
                                seed={entry.admin_email}
                                label={entry.admin_email}
                                size="xs"
                              />
                              {entry.admin_email}
                            </span>
                            {entry.revertible &&
                              (confirming === entry.id ? (
                                <span className="adm-confirm log-confirm">
                                  <span className="adm-small">
                                    Remettre les valeurs d'avant ?
                                  </span>
                                  <button
                                    className="adm-btn"
                                    onClick={() => setConfirming(null)}
                                  >
                                    Non
                                  </button>
                                  <button
                                    className="adm-btn adm-btn-warn"
                                    disabled={reverting === entry.id}
                                    onClick={() => revert(entry)}
                                  >
                                    {reverting === entry.id ? "…" : "Rétablir"}
                                  </button>
                                </span>
                              ) : (
                                <button
                                  className="log-revert"
                                  onClick={() => {
                                    setFlash(null);
                                    setConfirming(entry.id);
                                  }}
                                >
                                  <IconCornerDownLeft size={14} /> Rétablir
                                </button>
                              ))}
                          </div>
                        </div>
                      </m.li>
                    );
                  })}
                </AnimatePresence>
              </ol>
            </section>
          ))}
        </div>
      )}

      {nextBefore && (
        <div className="log-more">
          <button className="adm-btn" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? "Chargement…" : "Charger plus"}
          </button>
        </div>
      )}
    </m.section>
  );
}
