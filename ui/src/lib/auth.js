import { API_URL } from "../config.js";

/**
 * Calls against the Phase 0c auth endpoints.
 *
 * Every request here sends `credentials: "include"`. The session is an
 * httpOnly cookie, which means JS cannot read it or attach it by hand - the
 * browser only sends it when the request opts in, and only when the call is
 * same-site (see config.js's API_URL note). Omitting the flag on any single
 * call makes that call silently anonymous.
 */

/** Distinguishes "not signed in" from "the request failed". */
export class AuthError extends Error {}

/**
 * GET /auth/me - who the session cookie belongs to.
 *
 * Returns the user on 200, null on 401. A 401 is not an error here: "no valid
 * session" is the expected answer for a first-time visitor, and the caller
 * renders the sign-in screen for it. Anything else throws, so a backend
 * outage does not get mistaken for a logged-out user and silently drop
 * someone at the sign-in screen when their session was fine.
 */
export async function fetchMe() {
  const response = await fetch(`${API_URL}/auth/me`, {
    credentials: "include",
  });
  if (response.status === 401) return null;
  if (!response.ok) throw new AuthError(`/auth/me returned ${response.status}`);
  return response.json();
}

/**
 * POST /auth/google - exchange a Google ID token for a session cookie.
 *
 * The token goes in the body, not a header: it is a bearer credential and a
 * URL or header would be likelier to end up in a log.
 */
export async function signInWithGoogle(idToken) {
  const response = await fetch(`${API_URL}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!response.ok) throw new AuthError(`/auth/google returned ${response.status}`);
  return response.json();
}

/**
 * POST /auth/logout - clear the session cookie.
 *
 * Deliberately does not touch localStorage: chat history is browser-scoped in
 * this phase, not identity-scoped, so wiping it on logout would destroy the
 * student's transcripts for no reason. Revisit when history moves server-side.
 */
export async function logout() {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}
