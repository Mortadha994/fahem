import { useId, useMemo, useState } from "react";
import Button from "./ui/Button.jsx";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import {
  WEEKLY_GOAL_RANGE,
  loadWeeklyGoal,
  saveWeeklyGoal,
  solvedByDay,
  solvedTimestamps,
  weeklySolved,
} from "../lib/progress.js";

// A 44-radius ring in a 100x100 box: big enough to read the count inside,
// small enough for the sidebar column at its narrowest.
const RADIUS = 44;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * Exercises solved this week against a target the student sets.
 *
 * The count is real - solved exercises from this browser's chat history, since
 * Monday (lib/progress.js) - and browser-local for the same reason the streak
 * is. The target itself is remembered in localStorage.
 *
 * The ring is an SVG arc rather than a div trick so it scales cleanly and can
 * carry its own accessible value; the visible "4/6" is hidden from screen
 * readers, which get the progressbar's value instead.
 */
export default function WeeklyGoalCard() {
  const { sessions } = useChatSessions();
  const inputId = useId();
  const [goal, setGoal] = useState(loadWeeklyGoal);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(() => String(loadWeeklyGoal()));

  const done = useMemo(
    () => weeklySolved(solvedByDay(solvedTimestamps(sessions))),
    [sessions]
  );

  const ratio = goal > 0 ? Math.min(1, done / goal) : 0;
  const remaining = Math.max(0, goal - done);

  function save(event) {
    event.preventDefault();
    const next = saveWeeklyGoal(Number(draft));
    setGoal(next);
    setDraft(String(next));
    setEditing(false);
  }

  return (
    <section className="widget surface" aria-labelledby="goal-title">
      <div className="widget-head">
        <h2 id="goal-title" className="widget-label">
          Objectif hebdomadaire
        </h2>
        <Button
          variant="ghost"
          size="sm"
          className="widget-action"
          aria-expanded={editing}
          onClick={() => setEditing((v) => !v)}
        >
          {editing ? "Annuler" : "Modifier"}
        </Button>
      </div>

      {editing ? (
        <form className="goal-form" onSubmit={save}>
          <label className="field-label" htmlFor={inputId}>
            Exercices par semaine
          </label>
          <div className="goal-form-row">
            <input
              id={inputId}
              className="field-input goal-input"
              type="number"
              inputMode="numeric"
              min={WEEKLY_GOAL_RANGE.min}
              max={WEEKLY_GOAL_RANGE.max}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <Button type="submit" variant="primary">
              Enregistrer
            </Button>
          </div>
        </form>
      ) : (
        <>
          <div
            className="goal-ring"
            role="progressbar"
            aria-valuenow={done}
            aria-valuemin={0}
            aria-valuemax={goal}
            aria-valuetext={`${done} exercice${done > 1 ? "s" : ""} sur ${goal} cette semaine`}
          >
            <svg viewBox="0 0 100 100" aria-hidden="true">
              <circle className="goal-ring-track" cx="50" cy="50" r={RADIUS} />
              <circle
                className="goal-ring-arc"
                cx="50"
                cy="50"
                r={RADIUS}
                strokeDasharray={CIRCUMFERENCE}
                strokeDashoffset={CIRCUMFERENCE * (1 - ratio)}
              />
            </svg>
            <span className="goal-ring-center" aria-hidden="true">
              <span className="goal-count">
                {done}/{goal}
              </span>
              <span className="goal-unit">exercices</span>
            </span>
          </div>

          <p className="widget-note">
            {remaining > 0
              ? `Plus que ${remaining} exercice${remaining > 1 ? "s" : ""} pour atteindre ton objectif.`
              : "Objectif atteint pour cette semaine."}
          </p>
        </>
      )}
    </section>
  );
}
