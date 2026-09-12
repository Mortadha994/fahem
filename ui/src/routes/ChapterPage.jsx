import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  fetchChapterPdf,
  fetchChapters,
  fetchExercises,
  UnauthorizedError,
} from "../lib/chapters.js";
import { useAuth } from "../lib/authContext.js";
import Alert from "../components/ui/Alert.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import {
  exerciseLength,
  exerciseTitle,
  isStarted,
  startedExerciseTexts,
} from "../lib/exercises.js";
import Skeleton from "../components/ui/Skeleton.jsx";

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

  // Which énoncés this browser has already sent to the chat. Read once on
  // mount: the history only changes from the chat screen, and coming back
  // here remounts this component (see the key in ChapterRoute).
  const [startedTexts] = useState(startedExerciseTexts);

  // Title for the header.
  //
  // This is a second, genuinely redundant round trip: Home has usually just
  // fetched the same list, and /chapters sends no cache-control or etag, so
  // nothing is reused - the request goes out again and the header reads
  // "Chapitre 1" until it lands. Accepted for now because the payload is
  // three entries and the endpoint does no work, not because it is free.
  // Passing the chapter through router state from Home, or caching in
  // lib/chapters.js, would remove it.
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
   * WAI-ARIA tabs keyboard behaviour.
   *
   * The pattern is not optional decoration: a tablist announces itself as one
   * widget, so a screen-reader user expects Left/Right to move between tabs
   * and Home/End to jump to the ends, the same way they would in any other
   * tablist. Before this, the tabs announced as tabs and then behaved like
   * two unrelated buttons.
   *
   * Selection follows focus, which is the right choice here because both
   * panels are already mounted - switching is instant and costs no fetch, so
   * there is nothing to protect the user from arrowing through.
   */
  const tabRefs = useRef({});
  const onTabKeyDown = (event) => {
    const order = [DOC, EXOS];
    const current = order.indexOf(tab);
    let next = null;
    if (event.key === "ArrowRight") next = order[(current + 1) % order.length];
    else if (event.key === "ArrowLeft")
      next = order[(current - 1 + order.length) % order.length];
    else if (event.key === "Home") next = order[0];
    else if (event.key === "End") next = order[order.length - 1];
    if (next === null) return;
    event.preventDefault();
    setTab(next);
    tabRefs.current[next]?.focus();
  };

  /**
   * Hand the exercise to the chat route, which sends it through the same
   * streamSolve path a typed question uses. The problem travels as router
   * state rather than a query string: an énoncé is a paragraph of French, and
   * putting it in the URL would be both ugly and length-limited.
   */
  const solve = (question) => navigate("/chat", { state: { problem: question } });

  return (
    <main className="page">
      {/* Compact on purpose: the back link and the chapter number share one
          row with the title, which gives the cours viewer below roughly 80px
          more height on a laptop screen. */}
      <header className="page-head chapter-head">
        <div className="chapter-head-row">
          <Link to="/" className="page-back">
            ← Chapitres
          </Link>
          <span className="chapter-head-id">Chapitre {id}</span>
        </div>
        <h1>{chapter?.title ?? `Chapitre ${id}`}</h1>
      </header>

      <div className="tabs" role="tablist" aria-label="Contenu du chapitre">
        <button
          type="button"
          role="tab"
          id="tab-doc"
          aria-controls="panel-doc"
          aria-selected={tab === DOC}
          /* Roving tabindex: one stop for the whole tablist, then arrows move
             within it. Leaving both tabs at 0 would make Tab walk through
             every tab before reaching the panel. */
          tabIndex={tab === DOC ? 0 : -1}
          ref={(el) => (tabRefs.current[DOC] = el)}
          className={`tab${tab === DOC ? " tab-on" : ""}`}
          onClick={() => setTab(DOC)}
          onKeyDown={onTabKeyDown}
        >
          Documentation
        </button>
        <button
          type="button"
          role="tab"
          id="tab-exos"
          aria-controls="panel-exos"
          aria-selected={tab === EXOS}
          tabIndex={tab === EXOS ? 0 : -1}
          ref={(el) => (tabRefs.current[EXOS] = el)}
          className={`tab${tab === EXOS ? " tab-on" : ""}`}
          onClick={() => setTab(EXOS)}
          onKeyDown={onTabKeyDown}
        >
          Exercices{exercises ? ` (${exercises.length})` : ""}
        </button>
      </div>

      {/* Both panels stay mounted; only visibility is toggled. Unmounting
          the <object> on every tab flip would hand the browser a brand-new
          PDF viewer each time, resetting the student back to page 1 at
          default zoom - so glancing at the exercise list would cost them
          their place in the cours, on the most common move this screen has.
          The exercise list is a handful of buttons and costs nothing to keep
          around. */}
      {/* tabIndex 0 so the panel itself is a tab stop: with no focusable
          child - the Documentation panel is a single <object> - a keyboard
          user would otherwise have no way to reach or scroll it. */}
      <section
        className="tabpanel"
        role="tabpanel"
        id="panel-doc"
        aria-labelledby="tab-doc"
        tabIndex={0}
        hidden={tab !== DOC}
      >
        {pdfFailed ? (
          <Alert className="page-alert">
            Impossible d'afficher le cours. Recharge la page pour réessayer.
          </Alert>
        ) : pdfUrl ? (
          <object className="pdf-frame surface" data={pdfUrl} type="application/pdf">
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
          <>
            <p className="sr-only" role="status">
              Chargement du cours…
            </p>
            <Skeleton radius="lg" className="pdf-skeleton" />
          </>
        )}
      </section>

      <section
        className="tabpanel"
        role="tabpanel"
        id="panel-exos"
        aria-labelledby="tab-exos"
        tabIndex={0}
        hidden={tab !== EXOS}
      >
        {exosFailed && (
          <Alert className="page-alert">
            Impossible de charger les exercices. Recharge la page pour réessayer.
          </Alert>
        )}
        {exercises === null && !exosFailed && (
          <p className="sr-only" role="status">
            Chargement…
          </p>
        )}
        {exercises?.length === 0 && (
          <EmptyState size="sm">Aucun exercice pour ce chapitre.</EmptyState>
        )}

        <ul className="exo-list">
          {/* One-line-row placeholders, the height of the shortest real
              exercise, so the list has a shape before the énoncés arrive. */}
          {exercises === null &&
            !exosFailed &&
            [0, 1, 2].map((i) => (
              <li key={`skeleton-${i}`} aria-hidden="true">
                <Skeleton height="4.5rem" radius="lg" />
              </li>
            ))}
          {(exercises ?? []).map((e, index) => {
            const started = isStarted(e.question, startedTexts);
            return (
              <li key={e.id}>
                <button
                  type="button"
                  className="exo surface surface-interactive"
                  onClick={() => solve(e.question)}
                >
                  {/* The number is what a student and a teacher say out loud
                      ("exercice 3"), so it leads the row. */}
                  <span className="exo-num" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span className="exo-body">
                    <span className="exo-head">
                      <span className="exo-title">{exerciseTitle(e.question)}</span>
                      <span className="exo-meta">
                        <span className="exo-len">{exerciseLength(e.question)}</span>
                        {started && <span className="exo-started">à finir</span>}
                      </span>
                    </span>
                    {/* The full énoncé stays on the page - clamped to two
                        lines so seven rows still fit a screen, and never
                        truncated in the DOM, so a screen reader and a
                        find-in-page both get all of it. */}
                    <span className="exo-q">{e.question}</span>
                  </span>
                  <span className="exo-go" aria-hidden="true">
                    Résoudre →
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
