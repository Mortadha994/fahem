import { API_URL } from "../config.js";

/**
 * Calls against the Phase 3a chapter endpoints.
 *
 * Same rule as lib/auth.js: every request sends credentials so the httpOnly
 * session cookie goes with it. All three routes are behind get_current_user,
 * so a call without it is simply anonymous and 401s.
 */

/** A 401 from any chapter call - the session went away mid-browse. */
export class UnauthorizedError extends Error {}

/** Anything else that went wrong; the caller shows a retry, not a sign-in. */
export class ChapterError extends Error {}

async function get(path, { as = "json" } = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { credentials: "include" });
  } catch (err) {
    throw new ChapterError(`network failure on ${path}: ${err.message}`);
  }

  // 401 is its own type, not a generic failure: the caller has to send the
  // student back to the sign-in screen rather than offer a retry that cannot
  // succeed. Same distinction api.js draws for /solve/stream.
  if (response.status === 401) throw new UnauthorizedError(path);
  if (!response.ok) throw new ChapterError(`${path} returned ${response.status}`);

  return as === "blob" ? response.blob() : response.json();
}

/** Every chapter, real and planned, each with a status. */
export function fetchChapters() {
  return get("/chapters");
}

/** Exercises for one active chapter. 404s for a coming_soon chapter. */
export function fetchExercises(chapterId) {
  return get(`/chapters/${encodeURIComponent(chapterId)}/exercises`);
}

/**
 * The lesson PDF, as a Blob.
 *
 * A Blob rather than pointing an <embed> straight at the URL: the document is
 * behind an authenticated endpoint, and a plain src= would be a browser
 * navigation that carries the cookie only when same-site holds - the same
 * trap config.js documents for API_URL. Fetching it with credentials and
 * handing the viewer an object URL keeps it working regardless, and keeps the
 * 401 in JavaScript where it can be handled, instead of rendering the JSON
 * error body inside the PDF frame.
 *
 * The caller owns the object URL it creates from this and must revoke it.
 */
export function fetchChapterPdf(chapterId) {
  return get(`/chapters/${encodeURIComponent(chapterId)}/pdf`, { as: "blob" });
}
