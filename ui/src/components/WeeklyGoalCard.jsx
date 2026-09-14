import { useId, useMemo, useState } from "react";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import Button from "./ui/Button.jsx";
import CountUp from "./CountUp.jsx";
import { SPRING_ENTER, rise } from "../lib/motion.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import { useAuth } from "../lib/authContext.js";
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
 * The count is real - solved exercises from the student's own chat history,
 * since Monday (lib/progress.js). The target is remembered in localStorage,
 * under a key that carries the account id.
 *
 * The ring is an SVG arc rather than a div trick so it scales cleanly and can
 * carry its own accessible value; the visible "4/6" is hidden from screen
 * readers, which get the progressbar's value instead.
 */
export default function WeeklyGoalCard() {
  const { sessions } = useChatSessions();
  const { user } = useAuth();
  const inputId = useId();
  const gradientId = `goal-grad-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const [goal, setGoal] = useState(() => loadWeeklyGoal(user?.id));
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(() => String(loadWeeklyGoal(user?.id)));

  const done = useMemo(
    () => weeklySolved(solvedByDay(solvedTimestamps(sessions))),
    [sessions]
  );

  const ratio = goal > 0 ? Math.min(1, done / goal) : 0;
  const remaining = Math.max(0, goal - done);

  function save(event) {
    event.preventDefault();
    const next = saveWeeklyGoal(Number(draft), user?.id);
    setGoal(next);
    setDraft(String(next));
    setEditing(false);
  }

  return (
    <m.section
      className={`widget surface${remaining === 0 && !editing ? " is-reached" : ""}`}
      aria-labelledby="goal-title"
      variants={rise}
    >
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

      {/* The ring and the edit form cross-fade rather than swapping in one
          frame; `initial={false}` keeps the first render still, so only a
          switch the student makes is animated. */}
      <AnimatePresence mode="wait" initial={false}>
        {editing ? (
          <m.form
            key="form"
            className="goal-form"
            onSubmit={save}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0, transition: SPRING_ENTER }}
            exit={{ opacity: 0, y: -6, transition: { duration: 0.12 } }}
          >
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
          </m.form>
        ) : (
          <m.div
            key="ring"
            className="goal-view"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0, transition: SPRING_ENTER }}
            exit={{ opacity: 0, y: -6, transition: { duration: 0.12 } }}
          >
            <div
              className="goal-ring"
              role="progressbar"
              aria-labelledby="goal-title"
              aria-valuenow={done}
              aria-valuemin={0}
              aria-valuemax={goal}
              aria-valuetext={`${done} exercice${done > 1 ? "s" : ""} sur ${goal} cette semaine`}
            >
              <svg viewBox="0 0 100 100" aria-hidden="true">
                {/* Blue to violet along the arc, the brand pair. The id is made
                  from useId without its punctuation, which url(#…) would not
                  accept. */}
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0" stopColor="var(--brand-blue)" />
                    <stop offset="1" stopColor="var(--brand-violet)" />
                  </linearGradient>
                </defs>
                <circle className="goal-ring-track" cx="50" cy="50" r={RADIUS} />
                {/* Drawn in from empty with a spring, and springs to the new
                  length when the count or the goal changes. */}
                <m.circle
                  className="goal-ring-arc"
                  cx="50"
                  cy="50"
                  r={RADIUS}
                  stroke={`url(#${gradientId})`}
                  strokeDasharray={CIRCUMFERENCE}
                  initial={{ strokeDashoffset: CIRCUMFERENCE }}
                  animate={{
                    strokeDashoffset: CIRCUMFERENCE * (1 - ratio),
                    transition: {
                      ...SPRING_ENTER,
                      visualDuration: 1,
                      bounce: 0.1,
                      delay: 0.3,
                    },
                  }}
                />
              </svg>
              <span className="goal-ring-center" aria-hidden="true">
                <span className="goal-count">
                  <CountUp value={done} delay={0.35} />/{goal}
                </span>
                <span className="goal-unit">exercices</span>
              </span>
            </div>

            <p className="widget-note">
              {remaining > 0
                ? `Plus que ${remaining} exercice${remaining > 1 ? "s" : ""} pour atteindre ton objectif.`
                : "Objectif atteint pour cette semaine."}
            </p>
          </m.div>
        )}
      </AnimatePresence>
    </m.section>
  );
}
