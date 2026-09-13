import { useMemo } from "react";
import * as m from "motion/react-m";
import CountUp from "./CountUp.jsx";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { pop, rise, stagger } from "../lib/motion.js";
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
    <m.section
      className="widget surface"
      aria-labelledby="streak-title"
      variants={rise}
    >
      {/* In a head row like the goal card's, so both labels sit at the same
          height when the widgets are side by side. */}
      <div className="widget-head">
        <h2 id="streak-title" className="widget-label">
          Série actuelle
        </h2>
      </div>

      <p className="streak-value">
        {/* The count climbs to the real streak for sighted readers; a screen
            reader gets the final number once, not every step of the climb. */}
        <CountUp
          value={streak}
          className="streak-number"
          delay={0.35}
          aria-hidden="true"
        />
        <span className="sr-only">{streak}</span>
        <span className="streak-unit">jour{streak === 1 ? "" : "s"} d'affilée</span>
      </p>

      {/* The letters are decoration for sighted readers; each marker carries
          its own sentence for a screen reader, since a row of coloured dots
          says nothing on its own. The days pop in left to right. */}
      <m.ul className="streak-days" variants={stagger(0.045, 0.2)}>
        {markers.map((day, i) => (
          <m.li key={day.key} className={`streak-day is-${day.state}`} variants={pop}>
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
          </m.li>
        ))}
      </m.ul>

      <p className="widget-note">
        {streak > 0
          ? "Continue aujourd'hui pour la garder."
          : "Résous un exercice aujourd'hui pour commencer ta série."}
      </p>
    </m.section>
  );
}
