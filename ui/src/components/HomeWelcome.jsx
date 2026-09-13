import { useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CHAPITRE } from "../config.js";
import { useAuth } from "../lib/authContext.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { solvedByDay, solvedTimestamps, weeklySolved } from "../lib/progress.js";

/**
 * The top of the home screen: who you are, where you left off, one way in.
 *
 * Everything in it is read from what the app already holds - the signed-in
 * user and this browser's discussions - so nothing here is a claim. The week's
 * count is the same number the goal widget shows (lib/progress.js), and is
 * browser-local for the same reason.
 *
 * The greeting uses the first word of the Google display name only. A
 * password account has no display name, and an e-mail address is not a name:
 * those students get "Bonjour" on its own rather than "Bonjour, eleve2008".
 *
 * Laid out as a grid - the copy, and a decorative tile beside it - rather than
 * text over an absolutely positioned watermark, so nothing can ever sit under
 * the greeting and the card's height is always its content's.
 */

function greeting(now = new Date()) {
  const h = now.getHours();
  return h >= 18 || h < 5 ? "Bonsoir" : "Bonjour";
}

const DATE = new Intl.DateTimeFormat("fr", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

/** The discussion to resume: the most recently touched one that has content. */
function lastDiscussion(sessions) {
  return sessions
    .filter((s) => s.messages?.some((m) => m.role === "user"))
    .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))[0];
}

export default function HomeWelcome() {
  const { user } = useAuth();
  const { sessions, setActiveId, createSession } = useChatSessions();
  const navigate = useNavigate();

  const firstName = user?.display_name?.trim().split(/\s+/)[0] ?? "";
  const weekDone = useMemo(
    () => weeklySolved(solvedByDay(solvedTimestamps(sessions))),
    [sessions]
  );
  const resume = useMemo(() => lastDiscussion(sessions), [sessions]);

  // A new question reuses an empty discussion if one is already open, so
  // pressing this twice does not leave two blank "Nouvelle discussion" rows
  // in the sidebar.
  const askNew = () => {
    const blank = sessions.find((s) => !s.messages?.length);
    if (blank) setActiveId(blank.id);
    else createSession();
    navigate("/chat");
  };

  return (
    <section className="hero" aria-labelledby="welcome-title">
      {/* Soft light, clipped to the card, so the rest of the app stays calm. */}
      <span className="hero-glow hero-glow-1" aria-hidden="true" />
      <span className="hero-glow hero-glow-2" aria-hidden="true" />

      <div className="hero-copy">
        <p className="hero-eyebrow">{DATE.format(new Date())}</p>
        <h1 id="welcome-title" className="hero-title">
          {greeting()}
          {firstName ? `, ${firstName}` : ""}
        </h1>
        <p className="hero-lead">
          {weekDone > 0
            ? `Tu as résolu ${weekDone} exercice${weekDone > 1 ? "s" : ""} cette semaine. Continue sur ta lancée.`
            : "Choisis un chapitre ou pose ta question : ton premier exercice de la semaine t'attend."}
        </p>

        <div className="hero-actions">
          {resume ? (
            <button
              type="button"
              className="btn btn-md hero-primary"
              onClick={() => {
                setActiveId(resume.id);
                navigate("/chat");
              }}
            >
              <span className="hero-primary-label">Reprendre</span>
              <span className="hero-primary-sub">{resume.title}</span>
            </button>
          ) : (
            <button type="button" className="btn btn-md hero-primary" onClick={askNew}>
              <span className="hero-primary-label">Poser ma première question</span>
            </button>
          )}
          {resume ? (
            <button
              type="button"
              className="btn btn-md btn-secondary hero-secondary"
              onClick={askNew}
            >
              Nouvelle question
            </button>
          ) : (
            <Link
              to={`/chapitre/${CHAPITRE}`}
              className="btn btn-md btn-secondary hero-secondary"
            >
              Ouvrir le chapitre {CHAPITRE}
            </Link>
          )}
        </div>
      </div>

      {/* The course's assignment arrow, the mark the whole product is named
          around. Pure decoration, and dropped when the card is narrow. */}
      <div className="hero-art" aria-hidden="true">
        <span className="hero-art-arrow">←</span>
        <code className="hero-art-code">
          x <b>←</b> x + 1
        </code>
      </div>
    </section>
  );
}
