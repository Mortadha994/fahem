import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Message from "../components/Message.jsx";
import Composer from "../components/Composer.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import { streamSolve, GENERIC_ERROR } from "../lib/api.js";
import { titleFrom } from "../lib/sessions.js";
import { fetchChapters, fetchExercises } from "../lib/chapters.js";
import { exerciseTitle } from "../lib/exercises.js";
import { hasRealAlgorithmeSolution } from "../lib/hasRealSolution.js";
import { useAuth } from "../lib/authContext.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { NIVEAU, CHAPITRE, SCOPE_LABEL } from "../config.js";
import { rateLimitMessage } from "../lib/rateLimit.js";

/**
 * The chat screen.
 *
 * Lifted out of App.jsx in Phase 3b so App can be the auth + router shell.
 * Phase 6 took two more things out of it: the session-history sidebar, which
 * is now a section of the one app sidebar (AppSidebar), and the topbar that
 * held the burger and the scope label, which the sidebar carries instead -
 * the audit's "two stacked bars" (P2-5). The session list itself moved to
 * ChatSessionsProvider, because the sidebar reads it too.
 *
 * What stayed here is what belongs to the conversation: the streaming call,
 * the draft, the autoscroll, the live region, and the abort on unmount.
 */
export default function Chat() {
  const { onUnauthorized } = useAuth();
  const { sessions, setSessions, activeId, createSession, patchLast } =
    useChatSessions();
  const location = useLocation();
  const navigate = useNavigate();

  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);

  /* One short line, replaced once per finished answer. See the live region in
     the markup for why this is not driven off the streaming text. */
  const [announcement, setAnnouncement] = useState("");

  const abortRef = useRef(null);
  const listRef = useRef(null);
  const pinnedToBottom = useRef(true);

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

  // Phase 9: the chapters a new discussion can be about. Fetched once; a
  // failure just leaves the picker hidden and the default chapter in place.
  const [chapterList, setChapterList] = useState([]);
  const [chapterChoice, setChapterChoice] = useState(CHAPITRE);
  useEffect(() => {
    let cancelled = false;
    fetchChapters()
      .then(
        (list) =>
          !cancelled && setChapterList(list.filter((c) => c.status === "active"))
      )
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // In an empty discussion the picker changes that discussion's chapter; once
  // a message is sent the chapter is fixed, so the answers in one thread never
  // mix two chapters' syntax.
  const currentChapter = active?.chapitre ?? chapterChoice;
  function chooseChapter(id) {
    setChapterChoice(id);
    if (active && active.messages.length === 0) {
      setSessions((prev) =>
        prev.map((s) => (s.id === active.id ? { ...s, chapitre: id } : s))
      );
    }
  }
  const currentTitle = chapterList.find((c) => c.id === currentChapter)?.title;

  // A few real exercises from the chosen chapter, offered while the thread is
  // empty. Only fetched then, and a failure just means no suggestions - the
  // composer is still the way in.
  const [suggestions, setSuggestions] = useState([]);
  const isEmpty = messages.length === 0;
  useEffect(() => {
    if (!isEmpty) return undefined;
    let cancelled = false;
    fetchExercises(currentChapter)
      .then(
        (list) => !cancelled && setSuggestions(list.slice(0, 3).map((e) => e.question))
      )
      .catch(() => !cancelled && setSuggestions([]));
    return () => {
      cancelled = true;
    };
  }, [isEmpty, currentChapter]);
  const composerRef = useRef(null);

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
        // The session's own chapter, not a global: an older discussion keeps
        // answering in the chapter it was started in.
        {
          problem,
          niveau: session.niveau ?? NIVEAU,
          chapitre: session.chapitre ?? CHAPITRE,
        },
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
    [patchLast, setSessions, onUnauthorized]
  );

  const handleSend = useCallback(() => {
    const problem = draft.trim();
    if (!problem || streaming) return;
    const session = active ?? createSession(chapterChoice);
    setDraft("");
    send(problem, session);
  }, [draft, streaming, active, createSession, send, chapterChoice]);

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
    const chapitre = location.state?.chapitre ?? CHAPITRE;
    navigate("/chat", { replace: true, state: null });
    send(problem, createSession(chapitre));
  }, [location.state, navigate, send, createSession]);

  return (
    <div className="chat">
      {/* The page's only <h1>. Visually hidden: the sidebar already says what
          this screen is, and a second visible title would be noise. */}
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

      <div className="messages" ref={listRef} onScroll={onScroll}>
        {messages.length === 0 ? (
          /* One column in normal flow: the prompt, the chapter, then a way in.
             The picker used to be pulled up under the prompt with a negative
             margin, which laid it over the prompt's second line as soon as
             the text wrapped. */
          <div className="chat-welcome">
            {/* h2, not h1: the page-level h1 above is persistent, and this
                prompt only exists while the thread is empty. */}
            <EmptyState titleAs="h2" title="Pose ta question sur le chapitre">
              Colle l'énoncé d'un exercice. Fahem le résout avec la syntaxe de ton
              chapitre — et te montre exactement sur quelles parties du cours il
              s'appuie.
            </EmptyState>

            {chapterList.length > 1 && (
              <label className="chat-chapter-pick">
                <span>Chapitre</span>
                <select
                  value={currentChapter}
                  onChange={(e) => chooseChapter(e.target.value)}
                >
                  {chapterList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} — {c.title}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {suggestions.length > 0 && (
              <section className="chat-suggest" aria-labelledby="chat-suggest-title">
                <h3 id="chat-suggest-title" className="chat-suggest-title">
                  Ou commence par un exercice de la série
                </h3>
                <ul className="chat-suggest-list">
                  {suggestions.map((q) => (
                    <li key={q}>
                      {/* Fills the box rather than sending: the student sees
                          the full énoncé in the composer and can edit it or
                          add their own attempt first. */}
                      <button
                        type="button"
                        className="chat-suggest-item"
                        onClick={() => {
                          setDraft(q);
                          composerRef.current?.focus();
                        }}
                      >
                        <span className="chat-suggest-name">{exerciseTitle(q)}</span>
                        <span className="chat-suggest-q">{q}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        ) : null}
        {messages.length === 0 ? null : (
          <>
            {chapterList.length > 1 && currentTitle && (
              <p className="chat-chapter-tag">
                Chapitre {currentChapter} — {currentTitle}
              </p>
            )}
            {messages.map((m) => (
              <Message key={m.id} message={m} streaming={streaming} />
            ))}
          </>
        )}
      </div>

      <Composer
        value={draft}
        onChange={setDraft}
        onSend={handleSend}
        onStop={handleStop}
        streaming={streaming}
        inputRef={composerRef}
      />
    </div>
  );
}
