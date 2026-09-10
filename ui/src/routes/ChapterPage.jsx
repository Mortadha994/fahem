import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  fetchChapterPdf,
  fetchChapters,
  fetchExercises,
  UnauthorizedError,
} from "../lib/chapters.js";
import { useAuth } from "../lib/authContext.js";

const DOC = "doc";
const EXOS = "exos";

/**
 * Router element. Its only job is to key the view on the chapter id.
 *
 * Remounting on a chapter change is what makes the view's state per-chapter:
 * without it, moving from one chapter to another would keep the previous
 * document and exercise list in state until the new fetches resolved, and the
 * fix would be to null them out inside the effects - which is the cascading
 * setState-in-effect React documents `key` as the answer to. Not reachable
 * today (only chapter 1 is active, so there is nowhere to navigate) but it
 * would become a stale-content bug the moment a second chapter ships.
 */
export default function ChapterRoute() {
  const { id } = useParams();
  return <ChapterView key={id} id={id} />;
}

/**
 * One chapter: the lesson document and its exercises.
 *
 * The PDF is rendered with <object> over a blob URL rather than a full PDF.js
 * build. The document is served from an authenticated endpoint, so it has to
 * be fetched with credentials and handed to the viewer as a blob either way -
 * and once it is a blob, the browser's own viewer already does everything
 * this MVP needs: pagination, zoom, search, text selection. PDF.js would add
 * ~1MB to the bundle and a worker to configure, and its case is custom
 * rendering - annotations, per-page control, extracting text into the app -
 * none of which is wanted here. Worth revisiting if any of that becomes a
 * requirement.
 */
function ChapterView({ id }) {
  const { onUnauthorized } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab] = useState(DOC);
  const [chapter, setChapter] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfFailed, setPdfFailed] = useState(false);
  const [exercises, setExercises] = useState(null);
  const [exosFailed, setExosFailed] = useState(false);

  // Title for the header. Cheap: the list is three entries and already cached
  // by the browser from the home page in the usual flow.
  useEffect(() => {
    let cancelled = false;
    fetchChapters()
      .then((list) => !cancelled && setChapter(list.find((c) => c.id === id) ?? null))
      .catch((err) => {
        if (!cancelled && err instanceof UnauthorizedError) onUnauthorized();
      });
    return () => {
      cancelled = true;
    };
  }, [id, onUnauthorized]);

  // The PDF. The object URL is revoked on unmount and whenever the chapter
  // changes - a blob URL pins its blob in memory until it is released, so
  // leaking one per visit would grow the tab's footprint by the size of the
  // document each time.
  useEffect(() => {
    let cancelled = false;
    let url = null;

    fetchChapterPdf(id)
      .then((blob) => {
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        setPdfUrl(url);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setPdfFailed(true);
      });

    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, onUnauthorized]);

  useEffect(() => {
    let cancelled = false;
    fetchExercises(id)
      .then((list) => !cancelled && setExercises(list))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setExosFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [id, onUnauthorized]);

  /**
   * Hand the exercise to the chat route, which sends it through the same
   * streamSolve path a typed question uses. The problem travels as router
   * state rather than a query string: an énoncé is a paragraph of French, and
   * putting it in the URL would be both ugly and length-limited.
   */
  const solve = (question) => navigate("/chat", { state: { problem: question } });

  return (
    <main className="page">
      <header className="page-head">
        <Link to="/" className="page-back">
          ← Chapitres
        </Link>
        <h1>{chapter?.title ?? `Chapitre ${id}`}</h1>
      </header>

      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === DOC}
          className={`tab${tab === DOC ? " tab-on" : ""}`}
          onClick={() => setTab(DOC)}
        >
          Documentation
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === EXOS}
          className={`tab${tab === EXOS ? " tab-on" : ""}`}
          onClick={() => setTab(EXOS)}
        >
          Exercices{exercises ? ` (${exercises.length})` : ""}
        </button>
      </div>

      {tab === DOC && (
        <section className="tabpanel" role="tabpanel" aria-label="Documentation">
          {pdfFailed ? (
            <p className="page-error" role="alert">
              Impossible d'afficher le cours. Recharge la page pour réessayer.
            </p>
          ) : pdfUrl ? (
            <object className="pdf-frame" data={pdfUrl} type="application/pdf">
              {/* Shown only if the browser has no built-in PDF viewer. */}
              <p className="page-muted">
                Ton navigateur ne peut pas afficher le PDF directement.{" "}
                <a href={pdfUrl} download={`fahem-chapitre-${id}.pdf`}>
                  Télécharge le cours
                </a>
                .
              </p>
            </object>
          ) : (
            <p className="page-muted" role="status">
              Chargement du cours…
            </p>
          )}
        </section>
      )}

      {tab === EXOS && (
        <section className="tabpanel" role="tabpanel" aria-label="Exercices">
          {exosFailed && (
            <p className="page-error" role="alert">
              Impossible de charger les exercices. Recharge la page pour réessayer.
            </p>
          )}
          {exercises === null && !exosFailed && (
            <p className="page-muted" role="status">
              Chargement…
            </p>
          )}
          {exercises?.length === 0 && (
            <p className="page-muted">Aucun exercice pour ce chapitre.</p>
          )}

          <ul className="exo-list">
            {(exercises ?? []).map((e) => (
              <li key={e.id}>
                <button
                  type="button"
                  className="exo"
                  onClick={() => solve(e.question)}
                  title="Résoudre avec Fahem"
                >
                  <span className="exo-q">{e.question}</span>
                  <span className="exo-go" aria-hidden="true">
                    Résoudre →
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
