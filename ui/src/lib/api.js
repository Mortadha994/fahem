import { API_URL } from "../config.js";

// The student never sees a status code or a raw error body.
export const GENERIC_ERROR =
  "Une erreur est survenue. Merci de réessayer dans un instant.";
export const BUSY_ERROR =
  "Le service est très sollicité en ce moment. Merci de réessayer dans une minute.";

/**
 * POST /solve/stream and dispatch Server-Sent Events as they arrive.
 *
 * SSE frames are separated by a blank line, and a single network chunk can
 * hold several frames or split one in half, so the buffer is only consumed up
 * to the last complete frame.
 *
 * `signal` comes from an AbortController - that is what the stop button uses.
 */
export async function streamSolve(
  { problem, niveau, chapitre, k = 5 },
  { onMeta, onDelta, onDone, onError, onUnauthorized, onRateLimited, signal } = {}
) {
  let response;
  try {
    response = await fetch(`${API_URL}/solve/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Sends the httpOnly session cookie. /solve/stream requires a signed-in
      // user since Phase 1, so without this every request is anonymous and
      // 401s.
      credentials: "include",
      body: JSON.stringify({ problem, niveau, chapitre, k }),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") return;
    onError?.(GENERIC_ERROR);
    return;
  }

  // 401 is handled apart from the generic error path: the session expired or
  // was cleared in another tab, and the fix is to sign in again, not to
  // retry. Showing GENERIC_ERROR here would leave the student pressing send
  // against a wall with no way to learn what is wrong.
  //
  // The backend rejects before the stream opens (the dependency resolves
  // ahead of the handler body), so this branch is reachable on a plain JSON
  // 401 and never mid-frame.
  if (response.status === 401) {
    onUnauthorized?.();
    return;
  }

  // 429 is the per-user rate limit (Phase 2), and it is separate from the
  // generic error path for the same reason 401 is: retrying immediately
  // cannot work, and the student needs to be told to wait rather than left
  // pressing send. Retry-After carries how long, in seconds.
  //
  // Like the 401, the backend rejects before the stream opens, so this is a
  // plain JSON response and never a half-read stream.
  if (response.status === 429) {
    const header = Number(response.headers.get("Retry-After"));
    onRateLimited?.(Number.isFinite(header) && header > 0 ? header : null);
    return;
  }

  if (!response.ok) {
    onError?.(GENERIC_ERROR);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let split;
      while ((split = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, split);
        buffer = buffer.slice(split + 2);

        let event = "message";
        const dataLines = [];
        for (const line of frame.split("\n")) {
          if (line.startsWith("event: ")) event = line.slice(7).trim();
          else if (line.startsWith("data: ")) dataLines.push(line.slice(6));
        }
        if (!dataLines.length) continue;

        let payload;
        try {
          payload = JSON.parse(dataLines.join("\n"));
        } catch {
          continue;
        }

        if (event === "meta") onMeta?.(payload);
        else if (event === "delta") onDelta?.(payload.t);
        else if (event === "done") onDone?.(payload);
        else if (event === "error") {
          onError?.(payload.message === "busy" ? BUSY_ERROR : GENERIC_ERROR);
          return;
        }
      }
    }
  } catch (err) {
    // An abort mid-stream is the stop button, not a failure.
    if (err.name !== "AbortError") onError?.(GENERIC_ERROR);
  }
}

/** The file types /solve/extract reads, and its size cap (config.py). */
export const ATTACHMENT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
];
export const ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024;

/**
 * POST /solve/extract: read the exercise out of a photo or a PDF.
 *
 * Returns the text only; the chat then sends it through streamSolve like a
 * typed message. The raw file is the body (its own Content-Type), not
 * multipart - the backend checks the real type from the bytes anyway.
 *
 * Resolves to one of:
 *   { ok: true, text, source, pages }
 *   { ok: false, unauthorized: true }
 *   { ok: false, rateLimited: true, retryAfter }
 *   { ok: false, error }        - a sentence the student can act on
 *   { aborted: true }           - the stop button
 * The backend's own 413/415/422 details are written for the student (see
 * attachments.py), so they are shown as they are; anything else is generic.
 */
export async function extractAttachment(file, { signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}/solve/extract`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") return { aborted: true };
    return { ok: false, error: GENERIC_ERROR };
  }

  if (response.status === 401) return { ok: false, unauthorized: true };
  if (response.status === 429) {
    const header = Number(response.headers.get("Retry-After"));
    return {
      ok: false,
      rateLimited: true,
      retryAfter: Number.isFinite(header) && header > 0 ? header : null,
    };
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // Non-JSON error page: fall through to the generic message.
  }
  if (!response.ok) {
    const readable = [413, 415, 422].includes(response.status);
    return {
      ok: false,
      error: readable && typeof body?.detail === "string" ? body.detail : GENERIC_ERROR,
    };
  }
  if (!body?.text) return { ok: false, error: GENERIC_ERROR };
  return { ok: true, text: body.text, source: body.source, pages: body.pages };
}
