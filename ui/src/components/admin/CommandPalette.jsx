import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { fetchUsers, updateControls } from "../../lib/admin.js";
import { useAdminStatus } from "../../lib/adminStatus.js";
import AdminAvatar from "./AdminAvatar.jsx";
import {
  IconActivity,
  IconArrowLeft,
  IconBook,
  IconChat,
  IconCornerDownLeft,
  IconDashboard,
  IconGauge,
  IconPause,
  IconPlay,
  IconPlus,
  IconSearch,
  IconShield,
  IconSliders,
  IconUpload,
  IconUsers,
} from "./icons.jsx";

/**
 * Ctrl+K: go anywhere in the console, or do the most common things, by typing.
 *
 * The keyboard-driven palette pattern (a filtered list, arrow keys, Enter),
 * with Motion's shared-layout highlight gliding between results (layoutId)
 * and AnimatePresence for the overlay. Three kinds of entries:
 *   - pages (and useful filtered views of them);
 *   - actions - pausing the AI asks for a second Enter, because it affects
 *     every student at once;
 *   - accounts, searched on the server once two characters are typed.
 * Matching ignores case and accents ("eleve" finds "Élèves").
 */

const fold = (text) =>
  text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const { status, refresh } = useAdminStatus();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [users, setUsers] = useState([]);
  const [confirmPause, setConfirmPause] = useState(false);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const returnFocus = useRef(null);

  // Opening: remember where focus was, start clean, focus the input.
  useEffect(() => {
    if (open) {
      returnFocus.current = document.activeElement;
      setQuery("");
      setActive(0);
      setUsers([]);
      setConfirmPause(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    } else {
      returnFocus.current?.focus?.();
    }
  }, [open]);

  // Account search, debounced.
  useEffect(() => {
    if (!open || query.trim().length < 2) {
      setUsers([]);
      return undefined;
    }
    let cancelled = false;
    const t = setTimeout(() => {
      fetchUsers({ q: query.trim(), limit: 5 })
        .then((page) => !cancelled && setUsers(page.items))
        .catch(() => !cancelled && setUsers([]));
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [open, query]);

  const go = (to) => () => {
    navigate(to);
    onClose();
  };
  // (The layout closes its phone menu from the sidebar links; a palette jump
  // happens with the menu shut, since the palette covers it.)

  const paused = status === "paused";
  const commands = useMemo(
    () => [
      {
        group: "Pages",
        label: "Tableau de bord",
        Icon: IconDashboard,
        run: go("/admin"),
        keys: "accueil dashboard",
      },
      {
        group: "Pages",
        label: "Surveillance IA — en direct",
        Icon: IconActivity,
        run: go("/admin/ia"),
        keys: "monitoring groq charge temperature",
      },
      {
        group: "Pages",
        label: "Contrôle de l'IA",
        Icon: IconSliders,
        run: go("/admin/ia?onglet=controles"),
        keys: "reglages limites budget garde-fou photos file",
      },
      {
        group: "Pages",
        label: "Historique 24 h",
        Icon: IconGauge,
        run: go("/admin/ia?onglet=historique"),
        keys: "echecs appels tokens",
      },
      {
        group: "Pages",
        label: "Utilisateurs",
        Icon: IconUsers,
        run: go("/admin/utilisateurs"),
        keys: "eleves comptes",
      },
      {
        group: "Pages",
        label: "Comptes suspendus",
        Icon: IconShield,
        run: go("/admin/utilisateurs?state=suspended"),
        keys: "suspension bloques",
      },
      {
        group: "Pages",
        label: "Chapitres",
        Icon: IconBook,
        run: go("/admin/chapitres"),
        keys: "cours exercices contenu",
      },
      {
        group: "Actions",
        label: paused
          ? "Relancer l'IA"
          : confirmPause
            ? "Confirmer : mettre l'IA en pause"
            : "Mettre l'IA en pause",
        hint: paused
          ? null
          : confirmPause
            ? "Entrée pour confirmer"
            : "demande confirmation",
        Icon: paused ? IconPlay : IconPause,
        tone: paused ? "ok" : "danger",
        keys: "pause maintenance relancer reprendre",
        keepOpen: true,
        run: async () => {
          if (!paused && !confirmPause) {
            setConfirmPause(true);
            return;
          }
          setBusy(true);
          try {
            await updateControls({ ai_paused: !paused });
            refresh();
            onClose();
          } finally {
            setBusy(false);
          }
        },
      },
      {
        group: "Actions",
        label: "Créer un compte élève",
        Icon: IconPlus,
        run: go("/admin/utilisateurs/nouveau"),
        keys: "nouvel utilisateur ajouter",
      },
      {
        group: "Actions",
        label: "Importer un chapitre",
        Icon: IconUpload,
        run: go("/admin/chapitres"),
        keys: "pdf markdown upload",
      },
      {
        group: "Actions",
        label: "Tester dans le chat",
        Icon: IconChat,
        run: go("/chat"),
        keys: "essayer eleve",
      },
      {
        group: "Actions",
        label: "Retour à l'app",
        Icon: IconArrowLeft,
        run: go("/"),
        keys: "quitter sortir",
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [paused, confirmPause]
  );

  const q = fold(query.trim());
  const items = [
    ...commands.filter((c) => !q || fold(`${c.label} ${c.keys}`).includes(q)),
    ...users.map((u) => ({
      group: "Comptes",
      label: u.display_name || u.email,
      hint: u.email,
      user: u,
      run: go(`/admin/utilisateurs/${u.id}`),
    })),
  ];
  const current = Math.min(active, Math.max(0, items.length - 1));

  useEffect(() => {
    listRef.current
      ?.querySelector(`[data-index="${current}"]`)
      ?.scrollIntoView({ block: "nearest" });
  }, [current]);

  function onKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) =>
        items.length ? (Math.min(i, items.length - 1) + 1) % items.length : 0
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) =>
        items.length
          ? (Math.min(i, items.length - 1) - 1 + items.length) % items.length
          : 0
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (!busy) items[current]?.run();
    }
  }

  let lastGroup = null;

  return (
    <AnimatePresence>
      {open && (
        <m.div
          className="adm-cmd-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onMouseDown={(e) => e.target === e.currentTarget && onClose()}
        >
          <m.div
            className="adm-cmd"
            role="dialog"
            aria-modal="true"
            aria-label="Rechercher dans la console"
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -6 }}
            transition={{ type: "spring", visualDuration: 0.25, bounce: 0.15 }}
          >
            <div className="adm-cmd-input">
              <IconSearch />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActive(0);
                  setConfirmPause(false);
                }}
                onKeyDown={onKeyDown}
                placeholder="Page, action ou élève…"
                aria-label="Rechercher"
                role="combobox"
                aria-expanded="true"
                aria-controls="adm-cmd-list"
                aria-activedescendant={items.length ? `adm-cmd-${current}` : undefined}
              />
              <kbd>Échap</kbd>
            </div>

            <ul className="adm-cmd-list" id="adm-cmd-list" role="listbox" ref={listRef}>
              {items.length === 0 && (
                <li className="adm-cmd-empty">
                  {q.length >= 2 ? "Aucun résultat." : "Tape au moins deux lettres."}
                </li>
              )}
              {items.map((item, i) => {
                const heading = item.group !== lastGroup ? item.group : null;
                lastGroup = item.group;
                const Icon = item.Icon;
                return (
                  <li key={`${item.group}-${item.label}-${i}`} role="presentation">
                    {heading && <p className="adm-cmd-group">{heading}</p>}
                    <div
                      id={`adm-cmd-${i}`}
                      data-index={i}
                      role="option"
                      aria-selected={i === current}
                      className={`adm-cmd-item${item.tone ? ` is-${item.tone}` : ""}`}
                      onMouseMove={() => i !== current && setActive(i)}
                      onClick={() => !busy && item.run()}
                    >
                      {i === current && (
                        <m.span
                          layoutId="adm-cmd-highlight"
                          className="adm-cmd-highlight"
                          transition={{
                            type: "spring",
                            visualDuration: 0.2,
                            bounce: 0.1,
                          }}
                        />
                      )}
                      {item.user ? (
                        <AdminAvatar seed={item.user.id} label={item.label} size="sm" />
                      ) : (
                        <span className="adm-cmd-icon">
                          <Icon size={16} />
                        </span>
                      )}
                      <span className="adm-cmd-label">{item.label}</span>
                      {item.hint && <span className="adm-cmd-hint">{item.hint}</span>}
                      {i === current && (
                        <IconCornerDownLeft size={14} className="adm-cmd-enter" />
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>

            <footer className="adm-cmd-foot">
              <span>
                <kbd>↑</kbd>
                <kbd>↓</kbd> naviguer
              </span>
              <span>
                <kbd>Entrée</kbd> ouvrir
              </span>
              <span>
                <kbd>Ctrl K</kbd> fermer
              </span>
            </footer>
          </m.div>
        </m.div>
      )}
    </AnimatePresence>
  );
}
