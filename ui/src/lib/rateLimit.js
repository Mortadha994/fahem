/**
 * Rate-limit message. Retry-After is turned into something a student can read
 * rather than a raw seconds count - "réessaie dans 47 secondes" is actionable,
 * "retry_after: 47" is not. Falls back to a vague-but-honest wording when the
 * header is missing, rather than inventing a number.
 *
 * Shared by the chat and the sign-in forms (Phase 5), so a 429 reads the same
 * wherever a student meets one.
 */
export function rateLimitMessage(retryAfterSeconds) {
  if (!retryAfterSeconds) {
    return "Tu as atteint la limite de requêtes. Réessaie dans quelques instants.";
  }
  if (retryAfterSeconds < 60) {
    return `Tu as atteint la limite de requêtes. Réessaie dans ${retryAfterSeconds} secondes.`;
  }
  const minutes = Math.ceil(retryAfterSeconds / 60);
  return `Tu as atteint la limite de requêtes. Réessaie dans ${minutes} minute${
    minutes > 1 ? "s" : ""
  }.`;
}
