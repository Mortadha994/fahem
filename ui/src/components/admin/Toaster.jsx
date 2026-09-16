import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { ToastContext } from "../../lib/toast.js";
import { IconX } from "./icons.jsx";

/**
 * Toasts at the bottom of the page, for the console.
 *
 * What an action says when it is done ("Réglages enregistrés.") used to be a
 * green block inserted at the top of the panel, which pushed the page down and
 * was often off-screen by the time it appeared. A toast rises from the bottom
 * centre instead, over the page, without moving anything:
 *
 *   - success, info or error, each with its icon and colour; errors stay
 *     longer (DURATION) and are announced assertively (role="alert");
 *   - a thin bar shows the time left; hovering or focusing the stack pauses
 *     every timer, so a toast is never taken away mid-read;
 *   - an optional action button (e.g. "Annuler" to revert a setting);
 *   - closed by its button, by Escape, or by swiping it down;
 *   - at most MAX at once (the oldest goes), and the same message twice in a
 *     row only restarts the existing toast.
 *
 * Motion: AnimatePresence with popLayout and `layout` on each toast, so the
 * stack reflows smoothly when one leaves (the "notifications list" pattern);
 * drag="y" for the swipe. Needs the console's domMax LazyMotion (AdminLayout).
 */

const DURATION = { success: 4000, info: 5000, error: 7000 };
const MAX = 3;
let nextId = 1;

const ICONS = {
  success: <path d="M20 6L9 17l-5-5" />,
  error: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5" />
      <path d="M12 16.5h.01" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 7.5h.01" />
    </>
  ),
};

export default function Toaster({ children }) {
  const [toasts, setToasts] = useState([]);
  const [paused, setPaused] = useState(false);

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((tone, message, options = {}) => {
    const id = nextId++;
    setToasts((list) => {
      const last = list[list.length - 1];
      // The same message again: restart that toast rather than stack a copy.
      if (last && last.message === message && last.tone === tone) {
        return [...list.slice(0, -1), { ...last, id, ...options }];
      }
      return [...list, { id, tone, message, ...options }].slice(-MAX);
    });
    return id;
  }, []);

  const api = useMemo(
    () => ({
      success: (message, options) => push("success", message, options),
      error: (message, options) => push("error", message, options),
      info: (message, options) => push("info", message, options),
      dismiss,
    }),
    [push, dismiss]
  );

  // Escape closes the newest toast (when focus is not in a dialog of its own).
  useEffect(() => {
    if (!toasts.length) return undefined;
    const onKey = (event) => {
      if (event.key !== "Escape" || event.defaultPrevented) return;
      if (document.querySelector("[role=dialog]")) return;
      dismiss(toasts[toasts.length - 1].id);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [toasts, dismiss]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <section
        className="adm-toaster"
        aria-label="Notifications"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        onFocus={() => setPaused(true)}
        onBlur={() => setPaused(false)}
      >
        <ol className="adm-toast-list">
          <AnimatePresence mode="popLayout" initial={false}>
            {toasts.map((toast) => (
              <Toast
                key={toast.id}
                toast={toast}
                paused={paused}
                onDismiss={() => dismiss(toast.id)}
              />
            ))}
          </AnimatePresence>
        </ol>
      </section>
    </ToastContext.Provider>
  );
}

function Toast({ toast, paused, onDismiss }) {
  const duration = toast.duration ?? DURATION[toast.tone];
  const remaining = useRef(duration);
  const dismissRef = useRef(onDismiss);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    dismissRef.current = onDismiss;
  }, [onDismiss]);

  // One timer, stopped and resumed with `paused`: the time already spent is
  // kept, so hovering does not restart the countdown. The bar below is a CSS
  // animation of the same length, paused by the same state.
  const running = !paused && !busy;
  useEffect(() => {
    if (!running) return undefined;
    const started = Date.now();
    const t = setTimeout(() => dismissRef.current(), remaining.current);
    return () => {
      clearTimeout(t);
      remaining.current = Math.max(0, remaining.current - (Date.now() - started));
    };
  }, [running]);

  async function runAction() {
    setBusy(true);
    try {
      await toast.action.run();
    } finally {
      onDismiss();
    }
  }

  return (
    <m.li
      layout
      className={`adm-toast is-${toast.tone}`}
      role={toast.tone === "error" ? "alert" : "status"}
      initial={{ opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 12, scale: 0.97, transition: { duration: 0.16 } }}
      transition={{ type: "spring", visualDuration: 0.35, bounce: 0.2 }}
      drag="y"
      dragConstraints={{ top: 0, bottom: 0 }}
      dragElastic={{ top: 0.05, bottom: 0.6 }}
      onDragEnd={(_, info) =>
        (info.offset.y > 48 || info.velocity.y > 400) && onDismiss()
      }
    >
      <span className="adm-toast-icon" aria-hidden="true">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {ICONS[toast.tone]}
        </svg>
      </span>
      <p className="adm-toast-message">{toast.message}</p>
      {toast.action && (
        <button className="adm-toast-action" onClick={runAction} disabled={busy}>
          {busy ? "…" : toast.action.label}
        </button>
      )}
      <button
        className="adm-toast-close"
        onClick={onDismiss}
        aria-label="Fermer la notification"
      >
        <IconX size={14} />
      </button>
      {/* Time left. */}
      <span
        className="adm-toast-timer"
        aria-hidden="true"
        style={{
          animationDuration: `${duration}ms`,
          animationPlayState: running ? "running" : "paused",
        }}
      />
    </m.li>
  );
}
