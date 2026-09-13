// How the chat's history panel and hub read the session list: which
// discussions have something in them, what state each one is in, and which
// day it belongs to. Pure functions over the list ChatSessionsProvider holds.

/** A discussion the student actually asked something in. */
export function hasQuestion(session) {
  return Boolean(session.messages?.some((msg) => msg.role === "user"));
}

/**
 * "clean" / "warned" when the last answer went through the checker (the same
 * test the home screen's "Corrigé" and lib/progress.js use), "open" otherwise.
 */
export function statusOf(session) {
  const last = [...(session.messages ?? [])]
    .reverse()
    .find((msg) => msg.role === "assistant");
  if (last?.status === "clean") return "clean";
  if (last?.status === "warned") return "warned";
  return "open";
}

/** The student's first question, for a one-line preview under the title. */
export function firstQuestion(session) {
  return session.messages?.find((msg) => msg.role === "user")?.content ?? "";
}

const DAY = 86400000;

/**
 * Buckets by calendar day in the student's own timezone - "Hier" means
 * yesterday on their clock, not "between 24 and 48 hours ago". Empty groups
 * are dropped, and order inside a group is most recent first.
 */
export function groupByDay(sessions, now = new Date()) {
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  ).getTime();
  const groups = [
    { key: "today", label: "Aujourd'hui", from: startOfToday, items: [] },
    { key: "yesterday", label: "Hier", from: startOfToday - DAY, items: [] },
    { key: "week", label: "Cette semaine", from: startOfToday - 6 * DAY, items: [] },
    { key: "older", label: "Plus ancien", from: -Infinity, items: [] },
  ];
  const sorted = [...sessions].sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0));
  for (const s of sorted) {
    const t = s.updatedAt ?? s.createdAt ?? 0;
    groups.find((g) => t >= g.from).items.push(s);
  }
  return groups.filter((g) => g.items.length > 0);
}
