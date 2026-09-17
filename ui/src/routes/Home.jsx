import { useEffect, useMemo, useState } from "react";
import * as m from "motion/react-m";
import { rise, stagger } from "../lib/motion.js";
import { useNavigate } from "react-router-dom";
import { fetchChapters, fetchExercises, UnauthorizedError } from "../lib/chapters.js";
import { fetchProgress } from "../lib/progressApi.js";
import { useAuth } from "../lib/authContext.js";
import { profileLabel } from "../lib/profile.js";
import EmptyState from "../components/ui/EmptyState.jsx";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { isStarted, startedExerciseTexts } from "../lib/exercises.js";
import Alert from "../components/ui/Alert.jsx";
import ChapterCard, { ChapterCardSkeleton } from "../components/ChapterCard.jsx";
import HomeWelcome from "../components/HomeWelcome.jsx";
import RecentSessions from "../components/RecentSessions.jsx";
import StreakCard from "../components/StreakCard.jsx";
import WeeklyGoalCard from "../components/WeeklyGoalCard.jsx";

/**
 * Where a student lands after signing in.
 *
 * The backend already scopes the list to the student's year (their profile
 * niveau), so this renders whatever it returns, including the chapters of
 * that year that are not ready yet. Filtering the coming_soon ones out
 * client-side would undo the point of listing them: a short list reads as
 * "this is all there is" rather than "more is coming". When the year has no
 * chapters at all (its corpus is not in yet), an honest empty state says so
 * rather than showing a bare grid.
 *
 * Layout: a main column (welcome, chapters, recent discussions) and a
 * supporting column (streak, weekly goal) that moves under the main one when
 * the space beside the sidebar gets narrow. Every number on the screen is
 * derived from the API or this browser's own history; none is decorative.
 */
export default function Home() {
  const { user, onUnauthorized } = useAuth();
  const { sessions } = useChatSessions();
  const navigate = useNavigate();
  const klass = profileLabel(user);
  const [chapters, setChapters] = useState(null);
  const [failed, setFailed] = useState(false);
  // chapter id -> exercise énoncés, for the available chapters only.
  const [exercises, setExercises] = useState({});
  // chapter id -> { done, started, total } from the server (progress.py);
  // the browser-side count below stands in until it arrives.
  const [serverProgress, setServerProgress] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchProgress()
      .then((p) => {
        if (cancelled) return;
        setServerProgress(
          Object.fromEntries(
            p.chapters.map((c) => [
              c.id,
              { done: c.done, started: c.started, total: c.total },
            ])
          )
        );
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [sessions.length]);

  useEffect(() => {
    let cancelled = false;
    fetchChapters()
      .then((list) => {
        if (cancelled) return;
        setChapters(list);
        // The progress line is extra: one failed exercise list simply leaves
        // that card without it, rather than failing the screen.
        const active = list.filter((c) => c.status === "active");
        Promise.allSettled(active.map((c) => fetchExercises(c.id))).then((results) => {
          if (cancelled) return;
          const next = {};
          results.forEach((r, i) => {
            if (r.status === "fulfilled")
              next[active[i].id] = r.value.map((e) => e.question);
            else if (r.reason instanceof UnauthorizedError) onUnauthorized();
          });
          setExercises(next);
        });
      })
      .catch((err) => {
        if (cancelled) return;
        // A dead session is not a failed request: it sends the student to the
        // sign-in screen, the same way an expired session mid-chat does.
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  // "Started" = sent to the chat from this browser, the same test the chapter
  // page's "déjà commencé" marker uses. Recomputed when the sessions change,
  // so an exercise sent a moment ago counts on the way back here.
  const started = useMemo(() => {
    const texts = startedExerciseTexts(sessions);
    const counts = {};
    for (const [id, list] of Object.entries(exercises)) {
      counts[id] = {
        done: list.filter((q) => isStarted(q, texts)).length,
        total: list.length,
      };
    }
    return counts;
  }, [exercises, sessions]);

  const availableCount = (chapters ?? []).filter((c) => c.status === "active").length;

  return (
    // Two elements on purpose. .page is the scroll container, so it has a
    // fixed height. The layout grid used to be that same element, and a grid
    // with a fixed height shrinks its rows to fit: the welcome card - a
    // clipping box, whose automatic minimum height is 0 - lost its bottom and
    // the chapters were laid over its buttons. The grid now lives inside,
    // with no height of its own, so every row is as tall as its content.
    <main className="page page-home">
      <div className="home">
        {/* Sections rise in one after another (lib/motion.js). */}
        <m.div
          className="home-main"
          variants={stagger(0.08)}
          initial="hidden"
          animate="show"
        >
          <HomeWelcome />

          <m.section
            className="home-section"
            aria-labelledby="chapters-title"
            variants={rise}
          >
            <header className="section-head">
              <div>
                <h2 id="chapters-title" className="section-title">
                  Chapitres
                </h2>
                <p className="section-lead">
                  {klass
                    ? `Le programme de ta classe · ${klass}`
                    : "Lis le cours et entraîne-toi sur les exercices de la série."}
                </p>
              </div>
              {chapters && chapters.length > 0 && (
                <p className="section-meta">
                  {availableCount} sur {chapters.length} disponible
                  {availableCount > 1 ? "s" : ""}
                </p>
              )}
            </header>

            {failed && (
              <Alert className="page-alert">
                Impossible de charger les chapitres. Recharge la page pour réessayer.
              </Alert>
            )}

            {chapters === null && !failed && (
              <p className="sr-only" role="status">
                Chargement…
              </p>
            )}

            {/* Skeletons are a plain list; the real cards get their own
                staggered list once the data lands, so they animate in when
                they exist rather than while the placeholders are showing. */}
            {chapters === null && !failed && (
              <ul className="chapter-grid">
                {/* Three placeholders because that is the catalogue today. */}
                {[0, 1, 2].map((i) => (
                  <ChapterCardSkeleton key={`skeleton-${i}`} />
                ))}
              </ul>
            )}
            {/* The student's year with no chapters in the corpus yet: an
                honest message, not a bare grid. The chat still works, so it
                is the way forward offered here. */}
            {chapters && chapters.length === 0 && (
              <EmptyState
                title="Les chapitres de ta classe arrivent bientôt"
                action={{
                  label: "Poser une question",
                  onClick: () => navigate("/chat"),
                }}
              >
                {klass
                  ? `Le programme de ${klass} n'est pas encore en ligne. En attendant, tu peux poser une question ou coller un exercice dans le chat.`
                  : "En attendant, tu peux poser une question ou coller un exercice dans le chat."}
              </EmptyState>
            )}
            {chapters && chapters.length > 0 && (
              <m.ul
                className="chapter-grid"
                variants={stagger(0.07)}
                initial="hidden"
                animate="show"
              >
                {chapters.map((c) => (
                  <ChapterCard
                    key={c.id}
                    chapter={c}
                    progress={serverProgress?.[c.id] ?? started[c.id]}
                  />
                ))}
              </m.ul>
            )}
          </m.section>

          <RecentSessions />
        </m.div>

        {/* Progress, derived from this browser's own chat history - see
            lib/progress.js on why that is temporary. */}
        <m.aside
          className="home-side"
          aria-label="Ta progression"
          variants={stagger(0.1, 0.15)}
          initial="hidden"
          animate="show"
        >
          <StreakCard />
          <WeeklyGoalCard />
        </m.aside>
      </div>
    </main>
  );
}
