import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChatSessionsContext } from "../lib/chatSessionsContext.js";
import { useAuth } from "../lib/authContext.js";
import {
  clearLegacySessions,
  deleteSessionRemote,
  fetchSession,
  fetchSessions,
  HistoryStale,
  HistoryUnauthorized,
  isBusy,
  isFailedReadOnly,
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
 * Merge a discussion the server holds with the copy on screen, after a save
 * was refused as stale (another tab or device saved in between).
 *
 * The server's messages come first, in its order; a message the screen has
 * too keeps the screen's version when it is finished there (its status, its
 * feedback); messages only on screen (just written here) follow at the end.
 */
function mergeStale(server, local) {
  const localById = new Map(local.messages.map((m) => [m.id, m]));
  const serverIds = new Set(server.messages.map((m) => m.id));
  const merged = server.messages.map((m) => {
    const mine = localById.get(m.id);
    return mine && mine.content ? { ...m, ...mine } : m;
  });
  for (const m of local.messages) if (!serverIds.has(m.id)) merged.push(m);
  return { ...local, ...server, title: local.title || server.title, messages: merged };
}

/**
 * Owns the signed-in student's discussions for the whole app.
 *
 * The list comes from the server (/chat/sessions), so it belongs to the
 * account rather than to the browser. It arrives light - each discussion with
 * `loaded: false` and only a skeleton of its messages (enough for the history
 * panel, the home screen, the progress cards) - and a discussion is loaded in
 * full when the chat opens it (ensureLoaded). A discussion that is not loaded
 * is never saved: its skeleton would stand for answers it does not hold.
 *
 * The chat edits the list in memory - an answer streams in token by token -
 * and this saves each discussion once it settles: debounced, skipped while a
 * message is still being written, and only when it actually changed since the
 * last save. Every save carries the version it was based on; the server
 * refuses a stale one (409), and the discussion is then reloaded, merged with
 * what is on screen, and saved again - so two tabs never erase each other's
 * messages. The server also saves each finished exchange itself (see
 * /solve/stream); the chat takes that version from the answer's done frame
 * (setVersion).
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
  const loading = useRef(new Map()); // id -> promise of the full discussion

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

  /** Load one discussion in full (once), keeping anything written meanwhile. */
  const ensureLoaded = useCallback(
    (id) => {
      const current = latest.current.find((s) => s.id === id);
      if (!current || current.loaded !== false) return Promise.resolve(current);
      if (loading.current.has(id)) return loading.current.get(id);
      const promise = fetchSession(id)
        .then((full) => {
          saved.current.set(id, JSON.stringify(sessionPayload(full)));
          setSessions((prev) =>
            prev.map((s) =>
              s.id !== id
                ? s
                : s.loaded === false && s.messages.length <= full.messages.length
                  ? full
                  : mergeStale(full, s)
            )
          );
          return full;
        })
        .catch((err) => {
          if (err instanceof HistoryUnauthorized) onUnauthorized();
          throw err;
        })
        .finally(() => loading.current.delete(id));
      loading.current.set(id, promise);
      return promise;
    },
    [onUnauthorized]
  );

  /** The version the server gave a discussion (after its own save of an answer). */
  const setVersion = useCallback((id, version) => {
    if (!Number.isFinite(version)) return;
    setSessions((prev) =>
      prev.map((s) =>
        s.id === id && (s.version ?? 0) < version ? { ...s, version } : s
      )
    );
  }, []);

  const flush = useCallback(
    ({ keepalive = false } = {}) => {
      if (!loaded.current) return;
      for (const session of latest.current) {
        if (
          session.loaded === false ||
          !session.messages.length ||
          isBusy(session) ||
          isFailedReadOnly(session)
        )
          continue;
        const snapshot = JSON.stringify(sessionPayload(session));
        if (saved.current.get(session.id) === snapshot) continue;
        saved.current.set(session.id, snapshot);
        saveSession(session, { keepalive })
          .then((result) => result && setVersion(session.id, result.version))
          .catch((err) => {
            if (err instanceof HistoryUnauthorized) return onUnauthorized();
            if (saved.current.get(session.id) === snapshot)
              saved.current.delete(session.id);
            if (err instanceof HistoryStale) {
              // Someone saved this discussion since: take theirs, keep ours on
              // top of it, and let the next save go out on the new version.
              fetchSession(session.id)
                .then((server) =>
                  setSessions((prev) =>
                    prev.map((s) => (s.id === session.id ? mergeStale(server, s) : s))
                  )
                )
                .catch(() => {});
              return;
            }
            if (!keepalive)
              setTimeout(() => setRetryTick((t) => t + 1), RETRY_DELAY_MS);
          });
      }
    },
    [onUnauthorized, setVersion]
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
      const target = latest.current.find((s) => s.id === id);
      const remaining = latest.current.filter((s) => s.id !== id);
      setSessions(remaining);
      setActiveId((current) => (current === id ? (remaining[0]?.id ?? null) : current));
      saved.current.delete(id);
      // Anything the server may hold: a listed discussion, or one whose answer
      // the server saved itself (version > 0).
      if (target && (target.loaded === false || (target.version ?? 0) > 0)) {
        deleteSessionRemote(id).catch((err) => {
          if (err instanceof HistoryUnauthorized) onUnauthorized();
        });
      }
    },
    [onUnauthorized]
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

  /** Patch one message, by id, anywhere in a session. */
  const patchMessage = useCallback((sessionId, messageId, patch) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id !== sessionId
          ? s
          : {
              ...s,
              messages: s.messages.map((m) =>
                m.id === messageId
                  ? typeof patch === "function"
                    ? patch(m)
                    : { ...m, ...patch }
                  : m
              ),
            }
      )
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
      patchMessage,
      ensureLoaded,
      setVersion,
      flush,
      historyStatus,
    }),
    [
      sessions,
      activeId,
      createSession,
      deleteSession,
      patchLast,
      patchMessage,
      ensureLoaded,
      setVersion,
      flush,
      historyStatus,
    ]
  );

  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
}
