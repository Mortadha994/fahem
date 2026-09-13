import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { ago } from "../lib/relativeTime.js";
import * as m from "motion/react-m";
import { rise, stagger } from "../lib/motion.js";

/**
 * The last few discussions, one tap from the home screen.
 *
 * The same list the chat sidebar shows (this browser's localStorage), trimmed
 * to the three most recent that have a question in them. Opening one selects
 * it and goes to the chat - exactly what clicking it in the sidebar does, so
 * there is no second way of resuming a discussion to keep in sync.
 *
 * "Corrigé" is only shown when the last answer is one the checker ran over
 * (status clean/warned, the same test lib/progress.js counts as solved). A
 * discussion where the model only asked for the énoncé is not called solved.
 *
 * Renders nothing at all for a student with no history: an empty "Tes
 * discussions" box on a first visit would be a section about nothing.
 */

const SOLVED = new Set(["clean", "warned"]);
const LIMIT = 3;

export default function RecentSessions() {
  const { sessions, setActiveId } = useChatSessions();
  const navigate = useNavigate();

  const recent = useMemo(
    () =>
      sessions
        .filter((s) => s.messages?.some((msg) => msg.role === "user"))
        .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))
        .slice(0, LIMIT),
    [sessions]
  );

  if (recent.length === 0) return null;

  return (
    <m.section className="home-section" aria-labelledby="recent-title" variants={rise}>
      <header className="section-head">
        <h2 id="recent-title" className="section-title">
          Tes dernières discussions
        </h2>
      </header>
      {/* One panel with dividers rather than a bordered box per row: three
          stacked outlines read as three separate things competing for
          attention, when this is one short list. */}
      <m.ul className="recent-list" variants={stagger(0.06, 0.1)}>
        {recent.map((s) => {
          const last = [...s.messages]
            .reverse()
            .find((msg) => msg.role === "assistant");
          const solved = SOLVED.has(last?.status);
          const when = s.updatedAt ? ago(s.updatedAt) : "";
          return (
            <m.li key={s.id} variants={rise}>
              <button
                type="button"
                className="recent-item"
                onClick={() => {
                  setActiveId(s.id);
                  navigate("/chat");
                }}
              >
                <span
                  className={`recent-dot${solved ? " is-solved" : ""}`}
                  aria-hidden="true"
                />
                <span className="recent-body">
                  <span className="recent-title">{s.title}</span>
                  <span className="recent-meta">
                    Chapitre {s.chapitre}
                    {when && ` · ${when}`}
                  </span>
                </span>
                {solved && <span className="recent-badge">Corrigé</span>}
                <span className="recent-go" aria-hidden="true">
                  →
                </span>
              </button>
            </m.li>
          );
        })}
      </m.ul>
    </m.section>
  );
}
