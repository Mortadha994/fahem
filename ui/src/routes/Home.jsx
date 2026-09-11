import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchChapters, UnauthorizedError } from "../lib/chapters.js";
import { useAuth } from "../lib/authContext.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Skeleton from "../components/ui/Skeleton.jsx";

/**
 * Where a student lands after signing in.
 *
 * Renders whatever the backend says, including the chapters that are not
 * ready. Filtering those out client-side would undo the point of the backend
 * listing them: a short list reads as "this is all there is" rather than
 * "more is coming", and the app would be quietly overstating its coverage.
 */
export default function Home() {
  const { onUnauthorized } = useAuth();
  const [chapters, setChapters] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchChapters()
      .then((list) => !cancelled && setChapters(list))
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

  return (
    <main className="page">
      <header className="page-head">
        <h1>Chapitres</h1>
        <p className="page-lead">
          Choisis un chapitre pour lire le cours et t'entraîner sur ses exercices — ou
          pose directement ta question.
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
        {(chapters ?? []).map((c) => {
          const active = c.status === "active";
          const inner = (
            <>
              <span className="chapter-niveau">{c.niveau}</span>
              <span className="chapter-title">{c.title}</span>
              <Badge tone={active ? "success" : "neutral"} className="chapter-tag">
                {active ? "Disponible" : "À venir"}
              </Badge>
            </>
          );

          // A coming_soon chapter is rendered as a plain element, not a
          // disabled link: there is no destination, so there should be nothing
          // to click and nothing that looks clickable.
          return (
            <li key={c.id} className="chapter-cell">
              {active ? (
                <Link
                  to={`/chapitre/${c.id}`}
                  className="chapter-card surface surface-interactive"
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
    </main>
  );
}
