import { useState } from "react";

/**
 * Fahem's differentiator: the exact curriculum text the answer was built on.
 *
 * Two kinds of grounding, kept visually distinct because they mean different
 * things. Pinned tables are the chapter's reference sheet, included in every
 * answer regardless of the question. Retrieved excerpts are the topic-specific
 * material semantic search found for this problem, so they carry a relevance
 * score and the pinned ones do not.
 *
 * Collapsed by default - it should not compete with the answer - but the
 * summary line states the counts so it reads as a claim worth opening rather
 * than a debug toggle.
 */
export default function GroundingStrip({ pinned = [], retrieved = [] }) {
  const [open, setOpen] = useState(false);
  const [openId, setOpenId] = useState(null);

  if (!pinned.length && !retrieved.length) return null;

  const toggleItem = (id) => setOpenId((cur) => (cur === id ? null : id));

  const renderItem = (item, label, meta) => {
    const isOpen = openId === item.id;
    return (
      <li key={item.id} className="ground-item">
        <button
          type="button"
          className="ground-item-head"
          aria-expanded={isOpen}
          onClick={() => toggleItem(item.id)}
        >
          <span className="ground-caret" aria-hidden="true">
            {isOpen ? "▾" : "▸"}
          </span>
          <span className="ground-label">{label}</span>
          {meta && <span className="ground-meta">{meta}</span>}
        </button>
        {isOpen && <pre className="ground-excerpt">{item.content}</pre>}
      </li>
    );
  };

  return (
    <div className="grounding">
      <button
        type="button"
        className="grounding-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="ground-caret" aria-hidden="true">
          {open ? "▾" : "▸"}
        </span>
        Fondé sur {pinned.length} table{pinned.length > 1 ? "s" : ""} de syntaxe
        {retrieved.length > 0 && (
          <>
            {" "}
            et {retrieved.length} extrait{retrieved.length > 1 ? "s" : ""} du chapitre
          </>
        )}
      </button>

      {open && (
        <div className="grounding-body">
          {pinned.length > 0 && (
            <>
              <p className="ground-group">
                Syntaxe de référence — incluse dans chaque réponse
              </p>
              <ul className="ground-list">
                {pinned.map((p) => renderItem(p, p.label, p.section))}
              </ul>
            </>
          )}

          {retrieved.length > 0 && (
            <>
              <p className="ground-group">
                Extraits liés à ce problème — sélectionnés par recherche
              </p>
              <ul className="ground-list">
                {retrieved.map((r) =>
                  renderItem(r, r.section, `${r.type} · ${(r.score * 100).toFixed(0)}%`)
                )}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
