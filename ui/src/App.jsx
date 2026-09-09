import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import SignInScreen from "./components/SignInScreen.jsx";
import { streamSolve, GENERIC_ERROR } from "./lib/api.js";
import { fetchMe, signInWithGoogle, logout } from "./lib/auth.js";
import { loadSessions, saveSessions, newSession, titleFrom } from "./lib/sessions.js";
import { hasRealAlgorithmeSolution } from "./lib/hasRealSolution.js";
import { NIVEAU, CHAPITRE, SCOPE_LABEL } from "./config.js";
import "./App.css";

const SIGNIN_FAILED =
  "La connexion a échoué. Réessaie, ou vérifie que tu utilises un compte Google valide.";
const SIGNIN_UNREACHABLE =
  "Impossible de joindre le serveur. Vérifie ta connexion et réessaie.";

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

export default function App() {
  // Three states, not a boolean: "checking" has to be distinguishable from
  // "signed out", otherwise the sign-in screen flashes on every reload before
  // /auth/me answers, and a logged-in student sees a login form for a moment.
  const [authState, setAuthState] = useState("checking"); // checking|out|in
  const [user, setUser] = useState(null);
  const [signinBusy, setSigninBusy] = useState(false);
  const [signinError, setSigninError] = useState(null);

  const [sessions, setSessions] = useState(() => loadSessions());
  const [activeId, setActiveId] = useState(() => loadSessions()[0]?.id ?? null);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const abortRef = useRef(null);
  const listRef = useRef(null);
  const pinnedToBottom = useRef(true);

  useEffect(() => saveSessions(sessions), [sessions]);

  // One /auth/me on load. The cookie is httpOnly, so asking the server is the
  // only way to know whether there is a session - there is nothing readable
  // in the browser to check first.
  useEffect(() => {
    let cancelled = false;
    fetchMe()
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setAuthState(me ? "in" : "out");
      })
      .catch(() => {
        // A backend outage is not a logged-out user, but there is nothing
        // useful to render either - the sign-in screen at least offers an
        // action, and the error explains why it may not work yet.
        if (cancelled) return;
        setAuthState("out");
        setSigninError(SIGNIN_UNREACHABLE);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCredential = useCallback(async (idToken) => {
    setSigninBusy(true);
    setSigninError(null);
    try {
      const me = await signInWithGoogle(idToken);
      setUser(me);
      setAuthState("in");
    } catch {
      setSigninError(SIGNIN_FAILED);
    } finally {
      setSigninBusy(false);
    }
  }, []);

  const handleLogout = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    try {
      await logout();
    } finally {
      // Local state resets either way: if the network call failed the cookie
      // may survive, but leaving the UI in a signed-in state it cannot use is
      // worse than showing the sign-in screen.
      //
      // localStorage chat history is deliberately NOT cleared - it is
      // browser-scoped, not identity-scoped, in this phase.
      setUser(null);
      setAuthState("out");
      setSidebarOpen(false);
    }
  }, []);

  /** The session went away mid-use (expired, or logged out in another tab). */
  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setAuthState("out");
    setSigninError("Ta session a expiré. Reconnecte-toi pour continuer.");
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
        onUnauthorized: () => {
          patchLast(sessionId, {
            error: "Ta session a expiré. Reconnecte-toi pour continuer.",
            status: "error",
          });
          handleUnauthorized();
        },
        // Stays in the chat, unlike onUnauthorized: the session is still
        // valid, the student just has to wait. Bouncing them to the sign-in
        // screen would be both wrong and infuriating.
        onRateLimited: (retryAfter) =>
          patchLast(sessionId, {
            error: rateLimitMessage(retryAfter),
            status: "error",
          }),
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
  }, [draft, streaming, active, handleNew, patchLast, handleUnauthorized]);

  // Neither the chat nor the sign-in screen, until /auth/me has answered -
  // rendering either one early means a visible flash of the wrong app.
  if (authState === "checking") {
    return (
      <div className="boot" role="status" aria-live="polite">
        <span className="brand">Fahem</span>
        <span className="boot-dots" aria-hidden="true" />
        <span className="sr-only">Chargement…</span>
      </div>
    );
  }

  if (authState === "out") {
    return (
      <SignInScreen
        onCredential={handleCredential}
        busy={signinBusy}
        error={signinError}
      />
    );
  }

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
        user={user}
        onLogout={handleLogout}
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
