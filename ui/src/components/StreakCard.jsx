import { useMemo } from "react";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import {
  currentStreak,
  solvedByDay,
  solvedTimestamps,
  weekMarkers,
} from "../lib/progress.js";

const DAY_NAMES = [
  "lundi",
  "mardi",
  "mercredi",
  "jeudi",
  "vendredi",
  "samedi",
  "dimanche",
];

/**
 * Consecutive days of practice, and the week so far.
 *
 * Counts real solved exercises only - an answer the checker actually ran over
 * (see lib/progress.js). Browser-local, like the chat history it is derived
 * from: this streak does not follow a student to another device, and cannot
 * until sessions are stored server-side.
 *
 * The tone is deliberately supportive rather than loss-framed: "continue
 * aujourd'hui pour la garder", never "tu vas perdre ta série". This is a
 * revision tool for an exam, not an app trying to maximise daily opens, and a
 * student who misses a day should not be punished by their tutor.
 */
export default function StreakCard() {
  const { sessions } = useChatSessions();

  const { streak, markers } = useMemo(() => {
    const byDay = solvedByDay(solvedTimestamps(sessions));
    return { streak: currentStreak(byDay), markers: weekMarkers(byDay) };
  }, [sessions]);

  return (
    <section className="widget surface" aria-labelledby="streak-title">
      <h2 id="streak-title" className="widget-label">
        Série actuelle
      </h2>

      <p className="streak-value">
        <span className="streak-number">{streak}</span>
        <span className="streak-unit">jour{streak === 1 ? "" : "s"} d'affilée</span>
      </p>

      {/* The letters are decoration for sighted readers; each marker carries
          its own sentence for a screen reader, since a row of coloured dots
          says nothing on its own. */}
      <ul className="streak-days">
        {markers.map((day, i) => (
          <li
            key={day.key}
            className={`streak-day is-${day.state}`}
            style={{ "--d": i }}
          >
            <span aria-hidden="true">{day.label}</span>
            <span className="sr-only">
              {DAY_NAMES[i]}
              {day.count > 0
                ? ` : ${day.count} exercice${day.count > 1 ? "s" : ""} résolu${
                    day.count > 1 ? "s" : ""
                  }`
                : day.state === "today"
                  ? " : aujourd'hui, rien encore"
                  : day.state === "future"
                    ? " : à venir"
                    : " : rien"}
            </span>
          </li>
        ))}
      </ul>

      <p className="widget-note">
        {streak > 0
          ? "Continue aujourd'hui pour la garder."
          : "Résous un exercice aujourd'hui pour commencer ta série."}
      </p>
    </section>
  );
}
