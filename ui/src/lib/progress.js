/**
 * Practice history, derived from the student's chat sessions.
 *
 * The sessions are the account's own, loaded from the server
 * (ChatSessionsProvider), so the streak and the week's count follow the
 * student across devices and never mix two students on one browser. The
 * callers pass the live list in.
 *
 * What counts as a solved exercise: an assistant message whose stored checker
 * status is "clean" or "warned". Both mean a real Algorithme solution existed
 * and the checker ran over it (see hasRealAlgorithmeSolution in Chat.jsx);
 * "none" means the model asked for the statement instead of answering, and
 * "error"/"stopped" never produced an answer at all. Counting those would
 * inflate a streak for days when nothing was actually solved.
 *
 * Where the timestamp comes from: messages carry no time field, but their ids
 * are minted as `a_${Date.now()}` when the answer starts (Chat.jsx), so the id
 * *is* the timestamp. The session's updatedAt is the fallback for any message
 * whose id does not parse, so an older or hand-edited entry still counts on
 * some real day rather than being dropped.
 */

const GOAL_KEY = "fahem.weeklyGoal.v1";
export const DEFAULT_WEEKLY_GOAL = 6;
const MIN_GOAL = 1;
const MAX_GOAL = 30;

const SOLVED_STATUSES = new Set(["clean", "warned"]);

/** Local calendar day, not UTC: a student's "today" is their own midnight. */
function dayKey(timestamp) {
  const d = new Date(timestamp);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
}

function startOfDay(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

/** Monday, because a Tunisian school week is read Monday-first (L M M J V S D). */
function startOfWeek(date) {
  const d = startOfDay(date);
  const shift = (d.getDay() + 6) % 7; // Sunday (0) is 6 days after Monday
  d.setDate(d.getDate() - shift);
  return d;
}

/** Timestamps of every solved exercise, oldest first. */
export function solvedTimestamps(sessions = []) {
  const stamps = [];
  for (const session of sessions) {
    for (const message of session?.messages ?? []) {
      if (message?.role !== "assistant") continue;
      if (!SOLVED_STATUSES.has(message.status)) continue;
      const fromId = Number(/^a_(\d+)$/.exec(String(message.id ?? ""))?.[1]);
      const stamp = Number.isFinite(fromId)
        ? fromId
        : (session.updatedAt ?? session.createdAt);
      if (Number.isFinite(stamp)) stamps.push(stamp);
    }
  }
  return stamps.sort((a, b) => a - b);
}

/** day key -> how many exercises were solved that day. */
export function solvedByDay(stamps = solvedTimestamps()) {
  const byDay = new Map();
  for (const stamp of stamps) {
    const key = dayKey(stamp);
    byDay.set(key, (byDay.get(key) ?? 0) + 1);
  }
  return byDay;
}

/**
 * Consecutive days of practice, counting back from today.
 *
 * A day with nothing solved *today* does not end the streak - it is still
 * today, and the widget's job is to invite the student to keep it, not to
 * announce a loss. So counting starts at today when today has activity and at
 * yesterday otherwise; the streak only breaks on a day that has passed
 * entirely with nothing solved.
 */
export function currentStreak(byDay = solvedByDay(), now = Date.now()) {
  const today = startOfDay(now);
  const cursor = new Date(today);
  if (!byDay.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1);

  let days = 0;
  while (byDay.has(dayKey(cursor))) {
    days += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return days;
}

const WEEK_LABELS = ["L", "M", "M", "J", "V", "S", "D"];

/**
 * The seven days of the current week, for the marker row.
 * `state` is what the marker should look like:
 *   "done"   - at least one exercise solved that day
 *   "today"  - today, nothing solved yet (an outlined ring, an invitation)
 *   "empty"  - a past day with nothing solved
 *   "future" - later this week; drawn faintest, nothing to say about it yet
 */
export function weekMarkers(byDay = solvedByDay(), now = Date.now()) {
  const monday = startOfWeek(now);
  const todayKey = dayKey(now);
  return WEEK_LABELS.map((label, i) => {
    const day = new Date(monday);
    day.setDate(day.getDate() + i);
    const key = dayKey(day);
    const count = byDay.get(key) ?? 0;
    const isToday = key === todayKey;
    let state = "empty";
    if (count > 0) state = "done";
    else if (isToday) state = "today";
    else if (day > startOfDay(now)) state = "future";
    return { label, key, count, isToday, state };
  });
}

/** Exercises solved since Monday. */
export function weeklySolved(byDay = solvedByDay(), now = Date.now()) {
  return weekMarkers(byDay, now).reduce((total, day) => total + day.count, 0);
}

// The target is a preference of this student on this browser, so its key
// carries the account id: a second student on the same computer does not
// inherit the first one's goal.
const goalKey = (userId) => `${GOAL_KEY}.${userId ?? "anon"}`;

export function loadWeeklyGoal(userId) {
  try {
    const raw = Number(localStorage.getItem(goalKey(userId)));
    if (Number.isFinite(raw) && raw >= MIN_GOAL && raw <= MAX_GOAL) return raw;
  } catch {
    // Blocked storage: fall through to the default.
  }
  return DEFAULT_WEEKLY_GOAL;
}

export function saveWeeklyGoal(goal, userId) {
  const clamped = Math.min(MAX_GOAL, Math.max(MIN_GOAL, Math.round(goal)));
  try {
    localStorage.setItem(goalKey(userId), String(clamped));
  } catch {
    // Not persisted; the chosen value still applies for this session.
  }
  return clamped;
}

export const WEEKLY_GOAL_RANGE = { min: MIN_GOAL, max: MAX_GOAL };
