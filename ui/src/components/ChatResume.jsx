import { useMemo } from "react";
import * as m from "motion/react-m";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { ago } from "../lib/relativeTime.js";
import { hasQuestion, statusOf } from "../lib/sessionGroups.js";
import { HOVER_LIFT, PRESS, rise, stagger } from "../lib/motion.js";

/**
 * "Reprends où tu t'es arrêté": the latest discussions as cards, shown in an
 * empty discussion. With the list out of the sidebar, this is the one-click
 * way back into recent work; the full history is the Historique panel.
 *
 * Renders nothing when there is no history yet - a first-time student gets
 * the prompt and the suggested exercises, not an empty section.
 */

const LIMIT = 3;
const VERDICT = { clean: "Corrigé", warned: "À vérifier" };

export default function ChatResume() {
  const { sessions, setActiveId } = useChatSessions();

  const recent = useMemo(
    () =>
      sessions
        .filter(hasQuestion)
        .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))
        .slice(0, LIMIT),
    [sessions]
  );

  if (recent.length === 0) return null;

  return (
    <section className="chat-resume" aria-labelledby="chat-resume-title">
      <h2 id="chat-resume-title" className="chat-suggest-title">
        Reprends où tu t'es arrêté
      </h2>
      <m.ul
        className="chat-resume-list"
        variants={stagger(0.06)}
        initial="hidden"
        animate="show"
      >
        {recent.map((s) => {
          const status = statusOf(s);
          return (
            <m.li key={s.id} variants={rise} whileHover={HOVER_LIFT} whileTap={PRESS}>
              <button
                type="button"
                className="chat-resume-item"
                onClick={() => setActiveId(s.id)}
              >
                <span className="chat-resume-top">
                  <span className="chat-resume-chip">Chapitre {s.chapitre}</span>
                  {VERDICT[status] && (
                    <span className={`chat-resume-verdict is-${status}`}>
                      {VERDICT[status]}
                    </span>
                  )}
                </span>
                <span className="chat-resume-title">{s.title}</span>
                <span className="chat-resume-when">
                  {s.updatedAt ? ago(s.updatedAt) : ""}
                </span>
              </button>
            </m.li>
          );
        })}
      </m.ul>
    </section>
  );
}
