import Markdown from "./Markdown.jsx";
import GroundingStrip from "./GroundingStrip.jsx";

/**
 * Student messages are shaded and constrained in width; assistant messages are
 * full-width with no bubble, which is what Claude and ChatGPT do for long
 * technical answers - a bubble around a wide Algorithme|Python table just
 * wastes horizontal space.
 */
export default function Message({ message, streaming }) {
  if (message.role === "user") {
    return (
      <div className="msg msg-user">
        <div className="bubble">{message.content}</div>
      </div>
    );
  }

  const { content, pinned, retrieved, warnings, status, error } = message;

  return (
    <div className="msg msg-assistant">
      {error ? (
        <p className="error" role="alert">{error}</p>
      ) : (
        <>
          {content ? (
            <Markdown>{content}</Markdown>
          ) : (
            streaming && (
              <p className="thinking" role="status">
                <span className="dot" /><span className="dot" /><span className="dot" />
                <span className="thinking-text">Recherche dans le chapitre…</span>
              </p>
            )
          )}

          {/* The badge only resolves once the whole answer exists and the
              checker has run. It reports what the checker found - it is not a
              correctness guarantee, and the label says "syntaxe" for that
              reason rather than something like "vérifié" alone. */}
          {status === "checking" && (
            <span className="badge badge-pending">Vérification de la syntaxe…</span>
          )}
          {status === "clean" && (
            <span className="badge badge-ok" title="Aucune syntaxe hors chapitre détectée">
              ✓ Syntaxe du chapitre respectée
            </span>
          )}
          {status === "warned" && (
            <div className="badge-warn-wrap">
              <span className="badge badge-warn">⚠ Syntaxe à vérifier</span>
              <ul className="warn-list">
                {warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          <GroundingStrip pinned={pinned} retrieved={retrieved} />
        </>
      )}
    </div>
  );
}
