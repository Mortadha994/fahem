import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChatSessionsContext } from "../lib/chatSessionsContext.js";
import { useAuth } from "../lib/authContext.js";
import {
  clearLegacySessions,
  deleteSessionRemote,
  fetchSessions,
  HistoryUnauthorized,
  isBusy,
  newSession,
  saveSession,
  sessionPayload,
} from "../lib/sessions.js";
import { CHAPITRE, NIVEAU } from "../config.js";

// How long a discussion has to stay unchanged before it is saved. Short
// enough that closing the tab rarely loses anything, long enough that a burst
// of edits (a message, then its answer's first frames) is one request.
const SAVE_DELAY_MS = 700;
const RETRY_DELAY_MS = 5000;

/**
 * Owns the signed-in student's discussions for the whole app.
 *
 * The list comes from the server (/chat/sessions), so it belongs to the
 * account rather than to the browser: two students on one computer each see
 * only their own history, and a student sees theirs on any device. It is
 * mounted inside the signed-in app, so signing out unmounts it and the next
 * account starts from its own list, never from the previous one's memory.
 *
 * The chat still edits the list in memory - an answer streams in token by
 * token - and this saves each discussion once it settles: debounced, skipped
 * while a message is still being written, and only when it actually changed
 * since the last save. A discussion with no message is never saved, so an
 * opened-then-abandoned "Nouvelle discussion" leaves nothing behind.
 */
export default function ChatSessionsProvider({ children }) {
  const { onUnauthorized } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [historyStatus, setHistoryStatus] = useState("loading"); // loading|ready|error
  const [retryTick, setRetryTick] = useState(0);

  // id -> the payload last saved, as a string. What makes "changed?" cheap.
  const saved = useRef(new Map());
  const latest = useRef(sessions);
  const loaded = useRef(false);

  // Declared before the save effects so they always read the current list.
  useEffect(() => {
    latest.current = sessions;
  }, [sessions]);

  // Load this account's history once, and drop the old shared browser copy.
  useEffect(() => {
    clearLegacySessions();
    let cancelled = false;
    fetchSessions()
      .then((list) => {
        if (cancelled) return;
        for (const s of list)
          saved.current.set(s.id, JSON.stringify(sessionPayload(s)));
        // Keep anything started while the list was loading (an exercise sent
        // from a chapter page the moment the app opened).
        setSessions((prev) => [
          ...prev.filter((p) => !list.some((s) => s.id === p.id)),
          ...list,
        ]);
        setActiveId((current) => current ?? list[0]?.id ?? null);
        loaded.current = true;
        setHistoryStatus("ready");
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof HistoryUnauthorized) onUnauthorized();
        else setHistoryStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  const flush = useCallback(
    ({ keepalive = false } = {}) => {
      if (!loaded.current) return;
      for (const session of latest.current) {
        if (!session.messages.length || isBusy(session)) continue;
        const snapshot = JSON.stringify(sessionPayload(session));
        if (saved.current.get(session.id) === snapshot) continue;
        saved.current.set(session.id, snapshot);
        saveSession(session, { keepalive }).catch((err) => {
          if (err instanceof HistoryUnauthorized) return onUnauthorized();
          // Forget the snapshot so the next attempt sends it again.
          if (saved.current.get(session.id) === snapshot)
            saved.current.delete(session.id);
          if (!keepalive) setTimeout(() => setRetryTick((t) => t + 1), RETRY_DELAY_MS);
        });
      }
    },
    [onUnauthorized]
  );

  // Save shortly after the list stops changing.
  useEffect(() => {
    const timer = setTimeout(() => flush(), SAVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [sessions, retryTick, flush]);

  // And right away when the page is hidden or the app unmounts (sign-out),
  // so the last change is not left waiting on a timer that never fires.
  useEffect(() => {
    const onHide = () => {
      if (document.visibilityState === "hidden") flush({ keepalive: true });
    };
    document.addEventListener("visibilitychange", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      flush({ keepalive: true });
    };
  }, [flush]);

  // Phase 9: a discussion belongs to one chapter, chosen when it starts (the
  // chapter page an exercise came from, or the picker in an empty chat).
  const createSession = useCallback((chapitre = CHAPITRE) => {
    const session = newSession({ niveau: NIVEAU, chapitre: String(chapitre) });
    setSessions((prev) => [session, ...prev]);
    setActiveId(session.id);
    return session;
  }, []);

  /** Deleting the active session selects the next one, not nothing. */
  const deleteSession = useCallback(
    (id) => {
      const remaining = sessions.filter((s) => s.id !== id);
      setSessions(remaining);
      setActiveId((current) => (current === id ? (remaining[0]?.id ?? null) : current));
      const wasSaved = saved.current.delete(id);
      if (wasSaved) {
        deleteSessionRemote(id).catch((err) => {
          if (err instanceof HistoryUnauthorized) onUnauthorized();
        });
      }
    },
    [sessions, onUnauthorized]
  );

  /** Patch the last assistant message of a session. */
  const patchLast = useCallback((sessionId, patch) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const msgs = s.messages.slice();
        const i = msgs.length - 1;
        if (i < 0 || msgs[i].role !== "assistant") return s;
        msgs[i] =
          typeof patch === "function" ? patch(msgs[i]) : { ...msgs[i], ...patch };
        return { ...s, messages: msgs, updatedAt: Date.now() };
      })
    );
  }, []);

  const value = useMemo(
    () => ({
      sessions,
      setSessions,
      activeId,
      setActiveId,
      createSession,
      deleteSession,
      patchLast,
      historyStatus,
    }),
    [sessions, activeId, createSession, deleteSession, patchLast, historyStatus]
  );

  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
}
