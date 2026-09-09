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
  { onMeta, onDelta, onDone, onError, signal } = {}
) {
  let response;
  try {
    response = await fetch(`${API_URL}/solve/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem, niveau, chapitre, k }),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") return;
    onError?.(GENERIC_ERROR);
    return;
  }

  if (!response.ok) {
    onError?.(response.status === 429 ? BUSY_ERROR : GENERIC_ERROR);
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
