import { API_URL } from "../config.js";

// Chat history, per account. Discussions are saved on the server
// (/chat/sessions, chat_history.py), scoped to whoever is signed in, so they
// follow a student to any device and nobody sees anyone else's. The in-memory
// list and the save timing live in ChatSessionsProvider.

// Where history used to live: one browser key shared by every account that
// signed in on that browser - the leak this module replaced. It is deleted,
// not imported: nothing in it says whose each discussion was.
const LEGACY_KEY = "fahem.sessions.v1";

export function clearLegacySessions() {
  try {
    localStorage.removeItem(LEGACY_KEY);
  } catch {
    // Blocked storage: there is nothing readable to clear either.
  }
}

/** A random v4 UUID - the server keys discussions by one. */
function uuid() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function newSession({ niveau, chapitre }) {
  return {
    id: uuid(),
    title: "Nouvelle discussion",
    niveau,
    chapitre,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    // Never saved yet: version 0, and nothing to load from the server.
    version: 0,
    loaded: true,
    messages: [],
  };
}

/**
 * First student message becomes the discussion's title. An exercise's own
 * heading gets a separator, so "Exercice 3" does not run into its statement.
 */
export function titleFrom(text) {
  const clean = text.trim().replace(/\s+/g, " ");
  const withSeparator = clean.replace(/^(Exercice\s*\d+)\s+/i, "$1 — ");
  return withSeparator.length > 48
    ? `${withSeparator.slice(0, 48)}…`
    : withSeparator || "Nouvelle discussion";
}

/** A message still being written: saving it now would store half an answer. */
export function isBusy(session) {
  return session.messages.some(
    (m) => m.status === "streaming" || m.status === "reading" || m.status === "waiting"
  );
}

/**
 * A discussion that is nothing but a file Fahem could not read: one attached
 * message with no text read from it, and its error. Kept on screen, so the
 * student sees what went wrong, but never saved - it would only come back as
 * an empty "photo.png" entry in their history.
 */
export function isFailedReadOnly(session) {
  const [first, second, ...rest] = session.messages;
  return (
    rest.length === 0 &&
    Boolean(first?.attachment) &&
    !first.content &&
    second?.role === "assistant" &&
    second.status === "error"
  );
}

/** What the server stores - the fields the chat renders, nothing transient. */
export function sessionPayload(session) {
  return {
    title: session.title,
    niveau: session.niveau,
    chapitre: String(session.chapitre),
    createdAt: session.createdAt,
    messages: session.messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content ?? "",
      status: m.status ?? null,
      warnings: m.warnings ?? [],
      pinned: m.pinned ?? [],
      retrieved: m.retrieved ?? [],
      error: m.error ?? null,
      attachment: m.attachment ?? null,
      note: m.note ?? null,
      readingKind: m.readingKind ?? null,
      route: m.route ?? null,
    })),
  };
}

/** Thrown on 401: the caller hands over to the sign-in screen. */
export class HistoryUnauthorized extends Error {}

/** Thrown on 409 "stale": another tab or device saved this discussion since. */
export class HistoryStale extends Error {
  constructor(version) {
    super("stale");
    this.version = version;
  }
}

async function call(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...options,
  });
  if (response.status === 401) throw new HistoryUnauthorized(path);
  if (response.status === 409) {
    const body = await response.json().catch(() => null);
    if (body?.detail?.code === "stale") throw new HistoryStale(body.detail.version);
  }
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.status === 204 ? null : response.json();
}

/**
 * The signed-in student's discussions, newest first - light: each comes with
 * `loaded: false` and a skeleton of its messages (who spoke, each answer's
 * status, the student's text), enough for the history panel and the home
 * screen. The chat loads a discussion in full when it is opened.
 */
export function fetchSessions() {
  return call("/chat/sessions");
}

/** One discussion in full (`loaded: true`). */
export function fetchSession(id) {
  return call(`/chat/sessions/${encodeURIComponent(id)}`);
}

/**
 * Save one discussion. `keepalive` lets the request finish while the page is
 * being hidden or closed (the browser caps such a body at ~64 KB, so it is
 * the backstop, not the normal path).
 */
export function saveSession(session, { keepalive = false } = {}) {
  return call(`/chat/sessions/${encodeURIComponent(session.id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    // baseVersion: the server refuses a save from a copy older than its own
    // (409 -> HistoryStale) instead of overwriting what another tab added.
    body: JSON.stringify({
      ...sessionPayload(session),
      baseVersion: session.version ?? null,
    }),
    keepalive,
  });
}

/** A 👍 (1) / 👎 (-1) on an answer, or 0 to take it back. */
export function sendFeedback(sessionId, messageId, rating) {
  return call("/chat/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, rating }),
  });
}

export function deleteSessionRemote(id) {
  return call(`/chat/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
}
