import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import Message from "../components/Message.jsx";
import Composer from "../components/Composer.jsx";
import { streamSolve, GENERIC_ERROR } from "../lib/api.js";
import { loadSessions, saveSessions, newSession, titleFrom } from "../lib/sessions.js";
import { hasRealAlgorithmeSolution } from "../lib/hasRealSolution.js";
import { useAuth } from "../lib/authContext.js";
import { NIVEAU, CHAPITRE, SCOPE_LABEL } from "../config.js";

/**
 * The chat screen.
 *
 * Lifted out of App.jsx in Phase 3b so App can be the auth + router shell.
 * This is a move, not a rewrite: the session state, the streaming call, the
 * badge logic and the autoscroll behaviour are the code that was already
 * verified, unchanged. The only additions are the auth values now coming from
 * context instead of props, and the prefill handling below.
 */

/**
 * Rate-limit message. Retry-After is turned into something a student can read
 * rather than a raw seconds count - "réessaie dans 47 secondes" is actionable,
 * "retry_after: 47" is not. Falls back to a vague-but-honest wording when the
 * header is missing, rather than inventing a number.
 */
function rateLimitMessage(retryAfterSeconds) {
  if (!retryAfterSeconds) {
    return "Tu as atteint la limite de requêtes. Réessaie dans quelques instants.";
  }
  if (retryAfterSeconds < 60) {
    return `Tu as atteint la limite de requêtes. Réessaie dans ${retryAfterSeconds} secondes.`;
  }
  const minutes = Math.ceil(retryAfterSeconds / 60);
  return `Tu as atteint la limite de requêtes. Réessaie dans ${minutes} minute${
    minutes > 1 ? "s" : ""
  }.`;
}

export default function Chat() {
  const { onUnauthorized } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState(() => loadSessions());
  const [activeId, setActiveId] = useState(() => loadSessions()[0]?.id ?? null);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* One short line, replaced once per finished answer. See the live region in
     the markup for why this is not driven off the streaming text. */
  const [announcement, setAnnouncement] = useState("");

  const abortRef = useRef(null);
  const listRef = useRef(null);
  const pinnedToBottom = useRef(true);

  useEffect(() => saveSessions(sessions), [sessions]);

  // Abort any stream still running when this screen goes away.
  //
  // Phase 3b made this necessary and then forgot it. Before routing, chat was
  // the whole app and the only way to leave a stream was logging out, which
  // App.jsx handled by aborting before it called /auth/logout. Splitting Chat
  // into a route moved abortRef here and added a second exit that never
  // existed: clicking "Chapitres" or "Poser une question" mid-generation
  // unmounts this component. Without this cleanup the fetch keeps reading the
  // SSE and the backend keeps generating against Groq for a conversation
  // nobody is watching - burning exactly the budget Phase 2's limiter exists
  // to cap, just through a different door.
  //
  // Written as an unmount cleanup rather than a logout-specific call because
  // it covers every cause at once - route change, logout, or anything added
  // later - instead of one that has to be remembered per exit path. Logging
  // out reaches it too: App stops rendering <Routes> when the session goes,
  // which unmounts this subtree.
  //
  // Empty deps so it runs only on unmount; the ref is read at cleanup time,
  // so it always sees the current controller.
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      abortRef.current = null;
    };
  }, []);

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

  /**
   * Send one problem. Split out of handleSend so an exercise arriving by
   * navigation and a question typed into the composer go through exactly the
   * same request and streaming path - there is deliberately no second way to
   * call the backend.
   */
  const send = useCallback(
    (problem, session) => {
      const sessionId = session.id;
      // Cleared per send so an identical verdict is announced again rather
      // than being swallowed as an unchanged live-region value.
      setAnnouncement("");
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
          onDelta: (t) =>
            patchLast(sessionId, (m) => ({ ...m, content: m.content + t })),
          onDone: (done) => {
            setAnnouncement(
              done.warnings?.length
                ? `Réponse terminée. ${done.warnings.length} point${
                    done.warnings.length > 1 ? "s" : ""
                  } de syntaxe à vérifier.`
                : "Réponse terminée. Syntaxe du chapitre respectée."
            );
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
            }));
          },
          onError: (message) => {
            setAnnouncement("La réponse a échoué.");
            patchLast(sessionId, { error: message, status: "error" });
          },
          onUnauthorized: () => {
            patchLast(sessionId, {
              error: "Ta session a expiré. Reconnecte-toi pour continuer.",
              status: "error",
            });
            setAnnouncement("Session expirée.");
            onUnauthorized();
          },
          // Stays in the chat, unlike onUnauthorized: the session is still
          // valid, the student just has to wait. Bouncing them to the sign-in
          // screen would be both wrong and infuriating.
          onRateLimited: (retryAfter) => {
            setAnnouncement(rateLimitMessage(retryAfter));
            patchLast(sessionId, {
              error: rateLimitMessage(retryAfter),
              status: "error",
            });
          },
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
              ? {
                  ...m,
                  status: hasRealAlgorithmeSolution(m.content) ? "clean" : "none",
                }
              : m
          );
        });
    },
    [patchLast, onUnauthorized]
  );

  const handleSend = useCallback(() => {
    const problem = draft.trim();
    if (!problem || streaming) return;
    const session = active ?? handleNew();
    setDraft("");
    send(problem, session);
  }, [draft, streaming, active, handleNew, send]);

  /**
   * An exercise clicked on a chapter page arrives as router state and is sent
   * immediately, in a fresh session.
   *
   * Auto-send rather than pre-fill: the exercise list already shows the full
   * énoncé, so the student has read it before clicking, and clicking an item
   * in a list called "Exercices" is an unambiguous request to solve that one.
   * Pre-filling the box and waiting would make the click look broken - the
   * page changes and then nothing happens. The cost is one rate-limit slot per
   * click, which is the same cost as the student pasting it themselves.
   *
   * The ref guard and the history replace both matter. StrictMode mounts
   * effects twice in development, and the router keeps location.state across a
   * reload - without these, one click could send two generations, or a
   * refresh could silently re-send an old one.
   */
  const prefillSent = useRef(false);
  useEffect(() => {
    const problem = location.state?.problem;
    if (!problem || prefillSent.current) return;
    prefillSent.current = true;
    navigate("/chat", { replace: true, state: null });
    send(problem, handleNew());
  }, [location.state, navigate, send, handleNew]);

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
        {/* The page's only <h1>, and it is here rather than inside the empty
            state because the empty state disappears the moment a conversation
            starts - which left this screen with no headings at all once it
            was actually in use. Visually hidden: the topbar already says what
            this is on screen, and a second visible title would be noise. */}
        <h1 className="sr-only">Discussion — {SCOPE_LABEL}</h1>

        {/* Announces one short line per finished answer. Deliberately NOT
            aria-live on the message list itself: that streams token by token,
            and a live region there makes a screen reader restart on every
            fragment, which is worse than saying nothing. The full answer is
            long technical markdown, so this reports that it is ready and what
            the checker concluded, and leaves the reading to the user. The
            "searching" half is already covered - Message.jsx's thinking
            indicator carries role="status". */}
        <p className="sr-only" role="status" aria-live="polite">
          {announcement}
        </p>

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
              {/* h2, not h1: the page-level h1 above is persistent, and this
                  prompt only exists while the thread is empty. */}
              <h2>Pose ta question sur le chapitre</h2>
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
