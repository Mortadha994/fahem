import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useChatSessions } from "../lib/chatSessionsContext.js";

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

const relative = new Intl.RelativeTimeFormat("fr", { numeric: "auto" });

/** "à l'instant", "il y a 5 minutes", "hier", "il y a 3 jours"… */
function ago(timestamp, now = Date.now()) {
  const seconds = Math.round((timestamp - now) / 1000);
  const steps = [
    [60, "second"],
    [3600, "minute", 60],
    [86400, "hour", 3600],
    [604800, "day", 86400],
    [Infinity, "week", 604800],
  ];
  if (Math.abs(seconds) < 45) return "à l'instant";
  for (const [limit, unit, size = 1] of steps) {
    if (Math.abs(seconds) < limit)
      return relative.format(Math.round(seconds / size), unit);
  }
  return "";
}

export default function RecentSessions() {
  const { sessions, setActiveId } = useChatSessions();
  const navigate = useNavigate();

  const recent = useMemo(
    () =>
      sessions
        .filter((s) => s.messages?.some((m) => m.role === "user"))
        .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))
        .slice(0, LIMIT),
    [sessions]
  );

  if (recent.length === 0) return null;

  return (
    <section className="recent" aria-labelledby="recent-title">
      <h2 id="recent-title" className="home-h2">
        Tes dernières discussions
      </h2>
      <ul className="recent-list">
        {recent.map((s, i) => {
          const last = [...s.messages].reverse().find((m) => m.role === "assistant");
          const solved = SOLVED.has(last?.status);
          const when = s.updatedAt ? ago(s.updatedAt) : "";
          return (
            <li key={s.id} style={{ "--i": i }}>
              <button
                type="button"
                className="recent-item surface surface-interactive"
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
            </li>
          );
        })}
      </ul>
    </section>
  );
}
