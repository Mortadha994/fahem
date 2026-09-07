// Session persistence, browser-local by design: no auth, no student identity,
// no backend table. Sessions live in localStorage keyed by chapter, which is
// enough for the sidebar and for the Phase 5 student test. They do not follow
// a student to another device and are lost if site data is cleared.

const KEY = "fahem.sessions.v1";

export function loadSessions() {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    // Private mode, blocked storage, corrupt value - start empty rather than
    // taking the app down.
    return [];
  }
}

export function saveSessions(sessions) {
  try {
    localStorage.setItem(KEY, JSON.stringify(sessions));
  } catch {
    // Quota or blocked storage: the conversation still works in memory.
  }
}

export function newSession({ niveau, chapitre }) {
  return {
    id:
      globalThis.crypto?.randomUUID?.() ??
      `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    title: "Nouvelle discussion",
    niveau,
    chapitre,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [],
  };
}

/** First student message becomes the sidebar title. */
export function titleFrom(text) {
  const clean = text.trim().replace(/\s+/g, " ");
  return clean.length > 48 ? `${clean.slice(0, 48)}…` : clean || "Nouvelle discussion";
}
