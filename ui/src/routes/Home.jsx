import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchChapters, UnauthorizedError } from "../lib/chapters.js";
import { useAuth } from "../lib/authContext.js";

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
        <p className="page-error" role="alert">
          Impossible de charger les chapitres. Recharge la page pour réessayer.
        </p>
      )}

      {chapters === null && !failed && (
        <p className="page-muted" role="status">
          Chargement…
        </p>
      )}

      <ul className="chapter-grid">
        {(chapters ?? []).map((c) => {
          const active = c.status === "active";
          const inner = (
            <>
              <span className="chapter-niveau">{c.niveau}</span>
              <span className="chapter-title">{c.title}</span>
              <span className={`chapter-tag chapter-tag-${active ? "on" : "soon"}`}>
                {active ? "Disponible" : "À venir"}
              </span>
            </>
          );

          // A coming_soon chapter is rendered as a plain element, not a
          // disabled link: there is no destination, so there should be nothing
          // to click and nothing that looks clickable.
          return (
            <li key={c.id} className="chapter-cell">
              {active ? (
                <Link to={`/chapitre/${c.id}`} className="chapter-card chapter-card-on">
                  {inner}
                </Link>
              ) : (
                <div className="chapter-card chapter-card-soon" aria-disabled="true">
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
