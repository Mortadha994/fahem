// "à l'instant", "il y a 5 minutes", "hier", "il y a 3 jours"…
//
// Shared by the home screen's recent discussions and the chat sidebar's
// history, so the same discussion is never "il y a 2 heures" in one place and
// a raw date in the other.

const relative = new Intl.RelativeTimeFormat("fr", { numeric: "auto" });

const STEPS = [
  [60, "second", 1],
  [3600, "minute", 60],
  [86400, "hour", 3600],
  [604800, "day", 86400],
  [Infinity, "week", 604800],
];

export function ago(timestamp, now = Date.now()) {
  const seconds = Math.round((timestamp - now) / 1000);
  if (Math.abs(seconds) < 45) return "à l'instant";
  for (const [limit, unit, size] of STEPS) {
    if (Math.abs(seconds) < limit)
      return relative.format(Math.round(seconds / size), unit);
  }
  return "";
}
