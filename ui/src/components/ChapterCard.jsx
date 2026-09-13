import { Link } from "react-router-dom";
import Badge from "./ui/Badge.jsx";
import Skeleton from "./ui/Skeleton.jsx";

/**
 * One chapter on the home screen.
 *
 * Three bands, in the order a student reads them: which chapter and whether it
 * is open, what it is about, how far they are and the way in. The foot is
 * pinned to the bottom so the progress bars and "Ouvrir" line up across cards
 * whose titles wrap to a different number of lines.
 *
 * An available chapter is a link - the whole card is the target. A coming-soon
 * chapter is a plain element, not a disabled link: there is no destination, so
 * nothing about it should look clickable. It is quieter, but not faded with
 * opacity, which would take its text under AA.
 *
 * `progress` is { done, total } counted from this browser's history (see
 * Home.jsx), or undefined while it loads or when the exercise list failed -
 * the card then simply has no progress band rather than a made-up zero.
 */

/** "2eme" is the corpus key; students read "2ème". */
function niveauLabel(niveau) {
  return String(niveau ?? "").replace(/eme$/, "ème");
}

export default function ChapterCard({ chapter, progress, index = 0 }) {
  const active = chapter.status === "active";
  const hasProgress = active && progress && progress.total > 0;
  const ratio = hasProgress ? progress.done / progress.total : 0;

  const body = (
    <>
      <span className="chapter-card-head">
        {/* The chapter's id as a large numeral. Decoration: the meta line
            below says "Chapitre 1" in words. */}
        <span className="chapter-num" aria-hidden="true">
          {String(chapter.id).padStart(2, "0")}
        </span>
        <Badge tone={active ? "success" : "neutral"}>
          {active ? "Disponible" : "À venir"}
        </Badge>
      </span>

      <span className="chapter-card-body">
        <span className="chapter-meta">
          Chapitre {chapter.id} · {niveauLabel(chapter.niveau)}
        </span>
        <span className="chapter-title">{chapter.title}</span>
      </span>

      <span className="chapter-card-foot">
        {hasProgress && (
          <span className="chapter-progress">
            <span className="chapter-progress-row">
              <span>Exercices commencés</span>
              <span className="chapter-progress-count">
                {progress.done} / {progress.total}
              </span>
            </span>
            {/* Hidden from screen readers: the row above says it in words, and
                a progressbar inside a link leaks its bare value into the
                link's name. */}
            <span className="chapter-bar" aria-hidden="true">
              <span className="chapter-bar-fill" style={{ "--ratio": ratio }} />
            </span>
          </span>
        )}
        {active ? (
          <span className="chapter-open" aria-hidden="true">
            Ouvrir <span className="chapter-open-arrow">→</span>
          </span>
        ) : (
          <span className="chapter-soon-note">Bientôt disponible</span>
        )}
      </span>
    </>
  );

  return (
    <li className="chapter-cell" style={{ "--i": index }}>
      {active ? (
        <Link to={`/chapitre/${chapter.id}`} className="chapter-card is-active">
          {body}
        </Link>
      ) : (
        <div className="chapter-card is-soon">{body}</div>
      )}
    </li>
  );
}

/** Stands in while the list loads, built from the same bands so nothing jumps. */
export function ChapterCardSkeleton() {
  return (
    <li className="chapter-cell" aria-hidden="true">
      <div className="chapter-card">
        <span className="chapter-card-head">
          <Skeleton width="2.5rem" height="1.9rem" />
          <Skeleton width="5rem" height="1.4rem" radius="full" />
        </span>
        <span className="chapter-card-body">
          <Skeleton width="45%" height="0.8rem" />
          <Skeleton width="90%" height="1.1rem" />
          <Skeleton width="60%" height="1.1rem" />
        </span>
        <span className="chapter-card-foot">
          <Skeleton width="100%" height="0.4rem" radius="full" />
        </span>
      </div>
    </li>
  );
}
