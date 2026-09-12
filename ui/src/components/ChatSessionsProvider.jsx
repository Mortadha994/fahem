import { useCallback, useEffect, useMemo, useState } from "react";
import { ChatSessionsContext } from "../lib/chatSessionsContext.js";
import { loadSessions, newSession, saveSessions } from "../lib/sessions.js";
import { CHAPITRE, NIVEAU } from "../config.js";

/**
 * Owns the session list for the whole signed-in app.
 *
 * Lifted out of Chat.jsx in Phase 6: the sidebar that lists sessions now
 * belongs to AppLayout, and the chat screen that reads and appends to them is
 * a route inside it. Nothing about how a session is stored changed -
 * sessions.js still owns localStorage, and this still saves the whole list on
 * every change.
 *
 * Mounted above <Outlet>, so the list survives moving between Chapitres and
 * the chat. The streak and weekly-goal widgets read it too (via
 * useChatSessions), which is how they pick up a freshly solved exercise
 * without a reload.
 */
export default function ChatSessionsProvider({ children }) {
  const [sessions, setSessions] = useState(loadSessions);
  const [activeId, setActiveId] = useState(() => loadSessions()[0]?.id ?? null);

  useEffect(() => saveSessions(sessions), [sessions]);

  const createSession = useCallback(() => {
    const session = newSession({ niveau: NIVEAU, chapitre: CHAPITRE });
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
    },
    [sessions]
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
    }),
    [sessions, activeId, createSession, deleteSession, patchLast]
  );

  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
}
