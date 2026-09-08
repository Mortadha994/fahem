import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import { streamSolve, GENERIC_ERROR } from "./lib/api.js";
import { loadSessions, saveSessions, newSession, titleFrom } from "./lib/sessions.js";
import { hasRealAlgorithmeSolution } from "./lib/hasRealSolution.js";
import { NIVEAU, CHAPITRE, SCOPE_LABEL } from "./config.js";
import "./App.css";

export default function App() {
  const [sessions, setSessions] = useState(() => loadSessions());
  const [activeId, setActiveId] = useState(() => loadSessions()[0]?.id ?? null);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const abortRef = useRef(null);
  const listRef = useRef(null);
  const pinnedToBottom = useRef(true);

  useEffect(() => saveSessions(sessions), [sessions]);

  const active = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? null,
    [sessions, activeId]
  );
  const messages = active?.messages ?? [];

  // Only autoscroll when the student is already at the bottom, so scrolling up
  // to re-read the declaration table mid-stream is not fought by the app.
  const onScroll = useCallback(() => {
    const el = listRef.current;
    if (!el) return;
    pinnedToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }, []);

  useEffect(() => {
    if (pinnedToBottom.current && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  });

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

  const handleNew = useCallback(() => {
    const s = newSession({ niveau: NIVEAU, chapitre: CHAPITRE });
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
    setSidebarOpen(false);
    return s;
  }, []);

  const handleDelete = useCallback(
    (id) => {
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        if (id === activeId) setActiveId(next[0]?.id ?? null);
        return next;
      });
    },
    [activeId]
  );

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    // Keep whatever arrived; mark it as interrupted rather than verified.
    if (activeId) patchLast(activeId, { status: "stopped" });
  }, [activeId, patchLast]);

  const handleSend = useCallback(() => {
    const problem = draft.trim();
    if (!problem || streaming) return;

    let session = active;
    if (!session) session = handleNew();
    const sessionId = session.id;

    setDraft("");
    setStreaming(true);
    pinnedToBottom.current = true;

    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              title: s.messages.length === 0 ? titleFrom(problem) : s.title,
              updatedAt: Date.now(),
              messages: [
                ...s.messages,
                { id: `u_${Date.now()}`, role: "user", content: problem },
                {
                  id: `a_${Date.now()}`,
                  role: "assistant",
                  content: "",
                  pinned: [],
                  retrieved: [],
                  warnings: [],
                  status: "streaming",
                },
              ],
            }
          : s
      )
    );

    const controller = new AbortController();
    abortRef.current = controller;

    streamSolve(
      { problem, niveau: NIVEAU, chapitre: CHAPITRE },
      {
        signal: controller.signal,
        onMeta: (meta) =>
          patchLast(sessionId, {
            pinned: meta.pinned ?? [],
            retrieved: meta.retrieved ?? [],
          }),
        onDelta: (t) => patchLast(sessionId, (m) => ({ ...m, content: m.content + t })),
        onDone: (done) =>
          patchLast(sessionId, (m) => ({
            ...m,
            // "none" when there's no real Algorithme solution to have
            // checked - e.g. the model asked for the problem statement
            // instead of answering (see prompts.py). Zero violations on
            // that isn't "verified", it's "nothing to verify" - see
            // hasRealAlgorithmeSolution's comment. Checked ahead of
            // warned/clean so an empty warnings list doesn't read as a
            // pass on content the checker never meaningfully looked at.
            status: !hasRealAlgorithmeSolution(m.content)
              ? "none"
              : done.warnings?.length
                ? "warned"
                : "clean",
            warnings: done.warnings ?? [],
          })),
        onError: (message) => patchLast(sessionId, { error: message, status: "error" }),
      }
    )
      .catch(() => patchLast(sessionId, { error: GENERIC_ERROR, status: "error" }))
      .finally(() => {
        abortRef.current = null;
        setStreaming(false);
        // A stream that ended without a done frame still needs to leave the
        // pending badge behind - same real-content gate as onDone, since an
        // aborted stream's partial content has no real solution either.
        patchLast(sessionId, (m) =>
          m.status === "streaming"
            ? { ...m, status: hasRealAlgorithmeSolution(m.content) ? "clean" : "none" }
            : m
        );
      });
  }, [draft, streaming, active, handleNew, patchLast]);

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={(id) => {
          setActiveId(id);
          setSidebarOpen(false);
        }}
        onNew={handleNew}
        onDelete={handleDelete}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        scopeLabel={SCOPE_LABEL}
      />

      <main className="main">
        <header className="topbar">
          <button
            type="button"
            className="btn-burger"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Afficher les discussions"
          >
            ☰
          </button>
          <span className="scope">{SCOPE_LABEL}</span>
        </header>

        <div className="messages" ref={listRef} onScroll={onScroll}>
          {messages.length === 0 ? (
            <div className="empty">
              <h1>Pose ta question sur le chapitre</h1>
              <p>
                Colle l'énoncé d'un exercice. Fahem le résout avec la syntaxe de ton
                chapitre — et te montre exactement sur quelles parties du cours il
                s'appuie.
              </p>
            </div>
          ) : (
            messages.map((m) => (
              <Message key={m.id} message={m} streaming={streaming} />
            ))
          )}
        </div>

        <Composer
          value={draft}
          onChange={setDraft}
          onSend={handleSend}
          onStop={handleStop}
          streaming={streaming}
        />
      </main>
    </div>
  );
}
