import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import { HOVER_LIFT, PRESS, SPRING_HOVER, rise, stagger } from "../lib/motion.js";
import Message from "../components/Message.jsx";
import Composer from "../components/Composer.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import {
  streamSolve,
  extractAttachment,
  GENERIC_ERROR,
  ATTACHMENT_TYPES,
  ATTACHMENT_MAX_BYTES,
} from "../lib/api.js";
import { titleFrom } from "../lib/sessions.js";
import { fetchChapters, fetchExercises } from "../lib/chapters.js";
import { exerciseTitle } from "../lib/exercises.js";
import { hasQuestion } from "../lib/sessionGroups.js";
import ChatResume from "../components/ChatResume.jsx";
import HistoryPanel from "../components/HistoryPanel.jsx";
import { hasRealAlgorithmeSolution } from "../lib/hasRealSolution.js";
import { useAuth } from "../lib/authContext.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { NIVEAU, CHAPITRE, SCOPE_LABEL } from "../config.js";
import { rateLimitMessage } from "../lib/rateLimit.js";

// For the shortcut hint only; the handler accepts both Ctrl and Cmd anyway.
const IS_MAC =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform ?? "");

/**
 * The chat screen.
 *
 * Lifted out of App.jsx in Phase 3b so App can be the auth + router shell.
 * Phase 6 moved the burger and the scope label to the app sidebar and the
 * session list to ChatSessionsProvider. The discussions list itself now lives
 * here again, but as the Historique panel behind the chat header rather than
 * a second sidebar (HistoryPanel.jsx), with recent discussions offered as
 * cards in an empty thread (ChatResume.jsx).
 *
 * What stayed here is what belongs to the conversation: the streaming call,
 * the draft, the autoscroll, the live region, and the abort on unmount.
 */
export default function Chat() {
  const { onUnauthorized } = useAuth();
  const { sessions, setSessions, activeId, setActiveId, createSession, patchLast } =
    useChatSessions();
  const location = useLocation();
  const navigate = useNavigate();

  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);

  /* A photo or PDF of an exercise waiting in the composer:
     { file, url, name, size, kind: "image" | "pdf" }. `url` is an object URL
     for the thumbnail, revoked whenever the attachment changes or goes. */
  const [attachment, setAttachment] = useState(null);
  const [attachError, setAttachError] = useState("");
  useEffect(() => {
    const url = attachment?.url;
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [attachment]);
  const acceptFile = useCallback((file) => {
    if (!ATTACHMENT_TYPES.includes(file.type)) {
      setAttachError("Envoie une photo (JPEG, PNG ou WebP) ou un PDF.");
      return;
    }
    if (file.size > ATTACHMENT_MAX_BYTES) {
      setAttachError("Le fichier est trop volumineux (maximum 10 Mo).");
      return;
    }
    const kind = file.type === "application/pdf" ? "pdf" : "image";
    setAttachError("");
    setAttachment({
      file,
      kind,
      name: file.name || (kind === "image" ? "capture.png" : "exercice.pdf"),
      size: file.size,
      url: kind === "image" ? URL.createObjectURL(file) : null,
    });
  }, []);

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
  // String on both sides: a session stores its chapter as a string, the API
  // returns ids as numbers, and a strict comparison never matched.
  const currentTitle = chapterList.find(
    (c) => String(c.id) === String(currentChapter)
  )?.title;

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

  // The history panel. Ctrl+K / Cmd+K toggles it from anywhere on this
  // screen - the shortcut chat apps have taught students - and closing it
  // hands focus back to the button, so a keyboard user lands where they were.
  const [historyOpen, setHistoryOpen] = useState(false);
  const historyButtonRef = useRef(null);
  const closeHistory = useCallback(() => {
    setHistoryOpen(false);
    // Next frame, not synchronously: the key press that closed the panel is
    // still being dispatched, and a button focused mid-press can receive it
    // as a click and open the panel straight back up.
    requestAnimationFrame(() => historyButtonRef.current?.focus());
  }, []);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setHistoryOpen((v) => !v);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);
  const historyCount = sessions.filter(hasQuestion).length;

  // A new question reuses a discussion that is still empty instead of adding
  // another blank one, the same rule as the home screen's button.
  const newDiscussion = () => {
    const blank = sessions.find((s) => !s.messages?.length);
    if (blank) setActiveId(blank.id);
    else createSession(chapterChoice);
    setDraft("");
    composerRef.current?.focus();
  };

  // Only autoscroll when the student is already at the bottom, so scrolling up
  // to re-read the declaration table mid-stream is not fought by the app.
  // The same measure drives the "back to the latest message" button: it shows
  // exactly when autoscroll has let go.
  const [showJump, setShowJump] = useState(false);
  const onScroll = useCallback(() => {
    const el = listRef.current;
    if (!el) return;
    pinnedToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    setShowJump(!pinnedToBottom.current);
  }, []);
  const jumpToLatest = () => {
    const el = listRef.current;
    if (!el) return;
    pinnedToBottom.current = true;
    setShowJump(false);
    el.scrollTo({
      top: el.scrollHeight,
      behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  };

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
    (problem, session, { reuse, note, attachment } = {}) => {
      const sessionId = session.id;
      // Cleared per send so an identical verdict is announced again rather
      // than being swallowed as an unchanged live-region value.
      setAnnouncement("");
      setStreaming(true);
      pinnedToBottom.current = true;

      // `reuse`: the exchange is already on screen - an attachment was read
      // first (sendAttachment) - so its two messages are filled in rather
      // than appended again.
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== sessionId) return s;
          if (reuse) {
            return {
              ...s,
              title: s.messages.length <= 2 ? titleFrom(problem) : s.title,
              updatedAt: Date.now(),
              messages: s.messages.map((msg) =>
                msg.id === reuse.userId
                  ? { ...msg, content: problem, reading: false }
                  : msg.id === reuse.assistantId
                    ? { ...msg, status: "streaming" }
                    : msg
              ),
            };
          }
          return {
            ...s,
            title: s.messages.length === 0 ? titleFrom(problem) : s.title,
            updatedAt: Date.now(),
            messages: [
              ...s.messages,
              {
                id: `u_${Date.now()}`,
                role: "user",
                content: problem,
                // A retried attachment keeps its note and its file chip.
                ...(note ? { note } : {}),
                ...(attachment ? { attachment } : {}),
              },
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
          };
        })
      );

      const controller = new AbortController();
      abortRef.current = controller;

      // Session memory: what was said before this message, from the
      // discussion as it is on screen (an answer that just finished is not
      // saved yet, but it is here). Failed answers and the exchange being
      // filled in (`reuse`) are left out; the server keeps the last exchanges
      // and caps their size.
      const skip = new Set(reuse ? [reuse.userId, reuse.assistantId] : []);
      const history = session.messages
        .filter(
          (msg) =>
            !skip.has(msg.id) &&
            msg.content?.trim() &&
            !(msg.role === "assistant" && (msg.error || msg.status === "error"))
        )
        .slice(-6)
        .map((msg) => ({ role: msg.role, content: msg.content }));

      streamSolve(
        // The session's own chapter, not a global: an older discussion keeps
        // answering in the chapter it was started in.
        {
          problem,
          niveau: session.niveau ?? NIVEAU,
          chapitre: session.chapitre ?? CHAPITRE,
          note,
          history,
        },
        {
          signal: controller.signal,
          // meta arrives once the gatekeeper has classified the message: if that
          // classification was waiting in Groq's queue, the wait is over, so the
          // bubble goes back to "Recherche dans le chapitre…".
          onMeta: (meta) =>
            patchLast(sessionId, (msg) => {
              const next = {
                ...msg,
                pinned: meta.pinned ?? [],
                retrieved: meta.retrieved ?? [],
              };
              if (msg.status === "waiting") {
                next.status = "streaming";
                delete next.waiting;
              }
              return next;
            }),
          // In the queue: shown in place of "Recherche dans le chapitre…"
          // until the first fragment arrives.
          onWaiting: (waiting) => {
            setAnnouncement(
              "Fahem est très sollicité, ta demande est en file d'attente."
            );
            patchLast(sessionId, (msg) =>
              msg.content
                ? msg
                : {
                    ...msg,
                    status: "waiting",
                    waiting: {
                      position: waiting.position ?? 0,
                      seconds: waiting.seconds ?? null,
                      reason: waiting.reason ?? "queue",
                      kind: waiting.kind ?? null,
                    },
                  }
            );
          },
          onDelta: (t) =>
            patchLast(sessionId, (msg) => {
              const next = { ...msg, content: msg.content + t };
              if (msg.status === "waiting") {
                next.status = "streaming";
                delete next.waiting;
              }
              return next;
            }),
          onDone: (done) => {
            setAnnouncement(
              done.warnings?.length
                ? `Réponse terminée. ${done.warnings.length} point${
                    done.warnings.length > 1 ? "s" : ""
                  } de syntaxe à vérifier.`
                : "Réponse terminée. Syntaxe du chapitre respectée."
            );
            patchLast(sessionId, (msg) => ({
              ...msg,
              // "none" when there's no real Algorithme solution to have
              // checked - e.g. the model asked for the problem statement
              // instead of answering (see prompts.py). Zero violations on
              // that isn't "verified", it's "nothing to verify" - see
              // hasRealAlgorithmeSolution's comment. Checked ahead of
              // warned/clean so an empty warnings list doesn't read as a
              // pass on content the checker never meaningfully looked at.
              status: !hasRealAlgorithmeSolution(msg.content)
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
          patchLast(sessionId, (msg) => {
            if (msg.status !== "streaming" && msg.status !== "waiting") return msg;
            const { waiting: _waiting, ...rest } = msg;
            return {
              ...rest,
              status: hasRealAlgorithmeSolution(msg.content) ? "clean" : "none",
            };
          });
        });
    },
    [patchLast, setSessions, onUnauthorized]
  );

  /**
   * Send a photo or PDF: show the exchange straight away with a "reading"
   * state, turn the file into the exercise's text (POST /solve/extract), then
   * hand that text to send() like a typed message - so the gatekeeper, the
   * grounded answer and the checker all apply unchanged. The student's own
   * words, if any, travel beside the transcription as `note` - shown in the
   * bubble, and sent apart so the model answers the question in them instead
   * of treating them as more of the statement.
   */
  const sendAttachment = useCallback(
    async (file, kind, name, note, session) => {
      const sessionId = session.id;
      const stamp = Date.now();
      const userId = `u_${stamp}`;
      const assistantId = `a_${stamp}`;
      setAnnouncement("");
      setStreaming(true);
      pinnedToBottom.current = true;
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                title: s.messages.length === 0 ? titleFrom(note || name) : s.title,
                updatedAt: stamp,
                messages: [
                  ...s.messages,
                  {
                    id: userId,
                    role: "user",
                    // Filled with the exercise text once the file is read;
                    // left empty when it cannot be, so no retry is offered
                    // for a file that has to be attached again.
                    content: "",
                    ...(note ? { note } : {}),
                    attachment: { name, kind },
                    reading: true,
                  },
                  {
                    id: assistantId,
                    role: "assistant",
                    content: "",
                    pinned: [],
                    retrieved: [],
                    warnings: [],
                    status: "reading",
                    readingKind: kind,
                  },
                ],
              }
            : s
        )
      );

      const controller = new AbortController();
      abortRef.current = controller;
      const result = await extractAttachment(file, { signal: controller.signal });
      const markRead = () =>
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: s.messages.map((msg) =>
                    msg.id === userId ? { ...msg, reading: false } : msg
                  ),
                }
              : s
          )
        );

      // Stopped while reading: handleStop already marked the answer.
      if (result.aborted || abortRef.current !== controller) {
        markRead();
        return;
      }
      abortRef.current = null;

      if (!result.ok) {
        markRead();
        setStreaming(false);
        let error = result.error ?? GENERIC_ERROR;
        if (result.unauthorized) {
          error = "Ta session a expiré. Reconnecte-toi pour continuer.";
          onUnauthorized();
        } else if (result.rateLimited) {
          error = rateLimitMessage(result.retryAfter);
        }
        setAnnouncement("Lecture du fichier impossible.");
        patchLast(sessionId, { error, status: "error" });
        return;
      }

      const problem = result.text.slice(0, 2000);
      send(problem, session, { reuse: { userId, assistantId }, note });
    },
    [patchLast, setSessions, onUnauthorized, send]
  );

  const handleSend = useCallback(() => {
    const problem = draft.trim();
    if (streaming) return;
    if (attachment) {
      const session = active ?? createSession(chapterChoice);
      setDraft("");
      setAttachment(null);
      setAttachError("");
      sendAttachment(
        attachment.file,
        attachment.kind,
        attachment.name,
        problem,
        session
      );
      return;
    }
    if (!problem) return;
    const session = active ?? createSession(chapterChoice);
    setDraft("");
    send(problem, session);
  }, [
    draft,
    streaming,
    active,
    createSession,
    send,
    sendAttachment,
    attachment,
    chapterChoice,
  ]);

  /**
   * "Réessayer" on a failed answer: drop the failed exchange (the question
   * and its error) and send the same question again, through the same send()
   * as everything else. Dropping first keeps the thread from showing the
   * question twice.
   */
  const retryLast = useCallback(() => {
    if (!active || streaming) return;
    const msgs = active.messages;
    const lastUserIndex = msgs.findLastIndex((msg) => msg.role === "user");
    if (lastUserIndex < 0) return;
    const lastUserMsg = msgs[lastUserIndex];
    const question = lastUserMsg.content;
    if (!question) return;
    const kept = msgs.slice(0, lastUserIndex);
    setSessions((prev) =>
      prev.map((s) => (s.id === active.id ? { ...s, messages: kept } : s))
    );
    // The file chip and the note come back with the retried question.
    send(
      question,
      { ...active, messages: kept },
      { attachment: lastUserMsg.attachment, note: lastUserMsg.note }
    );
  }, [active, streaming, setSessions, send]);

  // Retry is offered on the last answer only, and only once nothing is
  // streaming - an older failure further up has been superseded.
  const lastMessageId = messages[messages.length - 1]?.id;
  // A photo that could not be read left no text to resend; the student
  // attaches it again (or a better one) instead.
  const lastUserHasText = Boolean(
    messages.findLast((msg) => msg.role === "user")?.content
  );

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
      {/* The discussion's own bar: what this thread is, and the two ways out
          of it - the history and a new question. It replaces the discussions
          list that used to sit in the app sidebar; the sidebar is navigation
          only again. Its title is the page's <h1>, so a screen reader hears
          which discussion is open, not a generic "Discussion". */}
      <header className="chat-head">
        <div className="chat-head-text">
          <h1 className="chat-title">
            {isEmpty ? "Nouvelle discussion" : active.title}
          </h1>
          <p className="chat-head-meta">
            <span className="chat-head-chip">Chapitre {currentChapter}</span>
            <span className="chat-head-scope">{currentTitle ?? SCOPE_LABEL}</span>
          </p>
        </div>
        <div className="chat-head-actions">
          <m.button
            ref={historyButtonRef}
            type="button"
            className="btn btn-md btn-secondary chat-history-btn"
            aria-haspopup="dialog"
            aria-expanded={historyOpen}
            aria-keyshortcuts="Control+K Meta+K"
            onClick={() => setHistoryOpen(true)}
            whileTap={PRESS}
          >
            <span className="chat-history-icon" aria-hidden="true">
              ▤
            </span>
            <span className="chat-history-label">Historique</span>
            {historyCount > 0 && (
              <span
                className="chat-history-count"
                aria-label={`${historyCount} discussions`}
              >
                {historyCount}
              </span>
            )}
            <kbd className="chat-history-kbd" aria-hidden="true">
              {IS_MAC ? "⌘K" : "Ctrl K"}
            </kbd>
          </m.button>
          <m.button
            type="button"
            className="btn btn-md chat-new-btn"
            onClick={newDiscussion}
            whileTap={PRESS}
            aria-label="Nouvelle discussion"
          >
            <span aria-hidden="true">+</span>
            <span className="chat-new-label">Nouvelle</span>
          </m.button>
        </div>
      </header>

      <HistoryPanel open={historyOpen} onClose={closeHistory} />

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

      <div className="messages-wrap">
        <div className="messages" ref={listRef} onScroll={onScroll}>
          {messages.length === 0 ? (
            /* One column in normal flow: the prompt, the chapter, then a way in.
             The picker used to be pulled up under the prompt with a negative
             margin, which laid it over the prompt's second line as soon as
             the text wrapped. */
            <m.div
              className="chat-welcome"
              variants={stagger(0.08)}
              initial="hidden"
              animate="show"
            >
              {/* h2, not h1: the page-level h1 above is persistent, and this
                prompt only exists while the thread is empty. */}
              <m.div variants={rise}>
                {/* The three kinds of message the backend routes (gatekeeper.py):
                    an exercise, a question on the course, the student's own
                    program - said up front so a first-time student knows all
                    three are welcome. */}
                <EmptyState titleAs="h2" title="Pose ta question sur le chapitre">
                  Colle l'énoncé d'un exercice — ou envoie sa photo ou son PDF —, pose
                  une question sur le cours, ou colle ton propre programme pour le faire
                  corriger. Fahem répond avec la syntaxe de ton chapitre — et te montre
                  sur quelles parties du cours il s'appuie.
                </EmptyState>
              </m.div>

              {chapterList.length > 1 && (
                <m.label className="chat-chapter-pick" variants={rise}>
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
                </m.label>
              )}

              <m.div variants={rise}>
                <ChatResume />
              </m.div>

              {suggestions.length > 0 && (
                <section className="chat-suggest" aria-labelledby="chat-suggest-title">
                  <h3 id="chat-suggest-title" className="chat-suggest-title">
                    Ou commence par un exercice de la série
                  </h3>
                  {/* The suggestions arrive after the prompt (they are fetched),
                    so they run their own stagger when they land. */}
                  <m.ul
                    className="chat-suggest-list"
                    variants={stagger(0.07)}
                    initial="hidden"
                    animate="show"
                  >
                    {suggestions.map((q, i) => (
                      <m.li
                        key={q}
                        variants={rise}
                        whileHover={HOVER_LIFT}
                        whileTap={PRESS}
                      >
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
                          <span className="chat-suggest-head">
                            <span className="chat-suggest-index" aria-hidden="true">
                              {String(i + 1).padStart(2, "0")}
                            </span>
                            <span className="chat-suggest-go" aria-hidden="true">
                              ↵
                            </span>
                          </span>
                          <span className="chat-suggest-name">{exerciseTitle(q)}</span>
                          <span className="chat-suggest-q">{q}</span>
                        </button>
                      </m.li>
                    ))}
                  </m.ul>
                </section>
              )}
            </m.div>
          ) : null}
          {messages.length === 0 ? null : (
            <>
              {/* Keyed by discussion with initial={false}: opening a thread shows
                it as it is, and only messages added while watching animate. */}
              <AnimatePresence initial={false} key={activeId}>
                {messages.map((msg) => (
                  <Message
                    key={msg.id}
                    message={msg}
                    streaming={streaming}
                    onRetry={
                      msg.id === lastMessageId &&
                      (msg.error || msg.status === "stopped") &&
                      lastUserHasText &&
                      !streaming
                        ? retryLast
                        : undefined
                    }
                  />
                ))}
              </AnimatePresence>
            </>
          )}
        </div>

        {/* Back to the latest message, once the student has scrolled away
            from it - most useful while an answer is still streaming below. */}
        <AnimatePresence>
          {showJump && messages.length > 0 && (
            <m.button
              type="button"
              className="chat-jump"
              onClick={jumpToLatest}
              aria-label="Aller au dernier message"
              initial={{ opacity: 0, y: 12, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1, transition: SPRING_HOVER }}
              exit={{ opacity: 0, y: 12, scale: 0.9, transition: { duration: 0.15 } }}
              whileTap={PRESS}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14M5.5 12.5 12 19l6.5-6.5" />
              </svg>
              {streaming && <span className="chat-jump-label">Réponse en cours</span>}
            </m.button>
          )}
        </AnimatePresence>
      </div>

      <Composer
        value={draft}
        onChange={setDraft}
        onSend={handleSend}
        onStop={handleStop}
        streaming={streaming}
        inputRef={composerRef}
        followUp={!isEmpty}
        chapterLabel={`Chapitre ${currentChapter}`}
        attachment={attachment}
        attachError={attachError}
        onAttach={acceptFile}
        onRemoveAttachment={() => {
          setAttachment(null);
          setAttachError("");
          composerRef.current?.focus();
        }}
      />
    </div>
  );
}
