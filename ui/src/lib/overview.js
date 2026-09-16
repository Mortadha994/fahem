import { API_URL } from "../config.js";

/**
 * What Fahem offers right now - chapters, counts, features - for the public
 * landing page (GET /public/overview, no sign-in; see public_overview.py).
 *
 * Resolves to null instead of throwing: the landing page must render without
 * it, and it gives up after `timeoutMs` so a slow backend never holds the page's
 * entrance animations.
 */
export async function fetchOverview({ timeoutMs = 2500 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}/public/overview`, {
      signal: controller.signal,
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** "1 exercice" / "12 exercices". */
export function plural(n, word, pluralWord = `${word}s`) {
  return `${n} ${n === 1 ? word : pluralWord}`;
}

/** "a", "a et b", "a, b et c". */
export function listFr(items) {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} et ${items[items.length - 1]}`;
}
