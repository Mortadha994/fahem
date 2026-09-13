import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchChapters, fetchExercises, UnauthorizedError } from "../lib/chapters.js";
import { useAuth } from "../lib/authContext.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { isStarted, startedExerciseTexts } from "../lib/exercises.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Skeleton from "../components/ui/Skeleton.jsx";
import HomeWelcome from "../components/HomeWelcome.jsx";
import RecentSessions from "../components/RecentSessions.jsx";
import StreakCard from "../components/StreakCard.jsx";
import WeeklyGoalCard from "../components/WeeklyGoalCard.jsx";

/**
 * Where a student lands after signing in.
 *
 * Renders whatever the backend says, including the chapters that are not
 * ready. Filtering those out client-side would undo the point of the backend
 * listing them: a short list reads as "this is all there is" rather than
 * "more is coming", and the app would be quietly overstating its coverage.
 *
 * Top to bottom: a welcome card with the way back into the last discussion,
 * the chapters (each available one with how many of its exercises this
 * browser has already started), and the recent discussions - with the streak
 * and the weekly goal beside them. Every number on the screen is derived from
 * the API or this browser's own history; none is decorative.
 */
export default function Home() {
  const { onUnauthorized } = useAuth();
  const { sessions } = useChatSessions();
  const [chapters, setChapters] = useState(null);
  const [failed, setFailed] = useState(false);
  // chapter id -> exercise énoncés, for the available chapters only.
  const [exercises, setExercises] = useState({});

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

  return (
    <main className="page home">
      <HomeWelcome />

      <div className="home-main">
        <header className="home-section-head">
          <h2 className="home-h2">Chapitres</h2>
          <p className="page-lead">
            Lis le cours et entraîne-toi sur les exercices de la série.
          </p>
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

        <ul className="chapter-grid">
          {/* Placeholder cards while the list loads, built from the same card
            classes so the grid is already standing when the real cards land.
            Three because that is the catalogue today; the bar heights add up
            to a real card with a two-line title. */}
          {chapters === null &&
            !failed &&
            [0, 1, 2].map((i) => (
              <li key={`skeleton-${i}`} className="chapter-cell" aria-hidden="true">
                <div className="chapter-card surface">
                  <Skeleton width="3rem" height="0.9rem" />
                  <Skeleton width="85%" height="1.1rem" />
                  <Skeleton width="60%" height="1.1rem" />
                  <Skeleton
                    width="4.5rem"
                    height="1.475rem"
                    radius="full"
                    className="chapter-tag"
                  />
                </div>
              </li>
            ))}
          {(chapters ?? []).map((c, i) => {
            const active = c.status === "active";
            const progress = started[c.id];
            const ratio = progress?.total ? progress.done / progress.total : 0;
            const inner = (
              <>
                <span className="chapter-top">
                  {/* The chapter's own id, as a big numeral: "01". Decoration -
                      the niveau line beside it already says which chapter. */}
                  <span className="chapter-num" aria-hidden="true">
                    {String(c.id).padStart(2, "0")}
                  </span>
                  <Badge tone={active ? "success" : "neutral"} className="chapter-tag">
                    {active ? "Disponible" : "À venir"}
                  </Badge>
                </span>
                <span className="chapter-niveau">{c.niveau}</span>
                <span className="chapter-title">{c.title}</span>

                {active && progress && progress.total > 0 && (
                  <span className="chapter-progress">
                    <span className="chapter-progress-text">
                      {progress.done} / {progress.total} exercices commencés
                    </span>
                    {/* Hidden from screen readers: the line above already says
                        it in words, and a progressbar inside a link leaked its
                        bare value into the link's name ("… commencés 0"). */}
                    <span className="chapter-bar" aria-hidden="true">
                      <span className="chapter-bar-fill" style={{ "--ratio": ratio }} />
                    </span>
                  </span>
                )}
                {active && (
                  <span className="chapter-open" aria-hidden="true">
                    Ouvrir <span className="chapter-open-arrow">→</span>
                  </span>
                )}
              </>
            );

            // A coming_soon chapter is rendered as a plain element, not a
            // disabled link: there is no destination, so there should be nothing
            // to click and nothing that looks clickable.
            return (
              <li key={c.id} className="chapter-cell" style={{ "--i": i }}>
                {active ? (
                  <Link
                    to={`/chapitre/${c.id}`}
                    className="chapter-card surface surface-interactive is-active"
                  >
                    {inner}
                  </Link>
                ) : (
                  <div
                    className="chapter-card surface chapter-card-soon"
                    aria-disabled="true"
                  >
                    {inner}
                  </div>
                )}
              </li>
            );
          })}
        </ul>

        <RecentSessions />
      </div>

      {/* Progress, derived from this browser's own chat history - see
          lib/progress.js on why that is temporary. */}
      <aside className="home-side" aria-label="Ta progression">
        <StreakCard />
        <WeeklyGoalCard />
      </aside>
    </main>
  );
}
