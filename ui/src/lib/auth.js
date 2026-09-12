import { API_URL } from "../config.js";
import { GENERIC_ERROR } from "./api.js";
import { rateLimitMessage } from "./rateLimit.js";

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

// --- email + password (Phase 5) -----------------------------------------------

/** Where the reset email's link lands. The one route reachable signed out. */
export const RESET_PASSWORD_PATH = "/reinitialiser-mot-de-passe";

/** Mirrors the backend's PASSWORD_MIN_LENGTH. The backend stays the authority;
 * this only lets the form say so before a round trip. */
export const PASSWORD_MIN_LENGTH = 12;

/** A failed auth request, carrying a message already fit to show a student. */
export class AuthRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

/**
 * Turn a non-2xx body into one French sentence.
 *
 * The backend's own wording is used wherever it has one - every string
 * `detail` from the password routes is already written for students. The one
 * exception is a 422 on the email field: that message comes from the
 * email-validator library, in English, so it is replaced here.
 */
function messageFrom(data) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : null;
    if (field === "email") return "Cette adresse e-mail n'est pas valide.";
    if (field === "display_name") return "Indique ton prénom ou ton nom.";
    // Our own password rules arrive as pydantic's "Value error, <our text>".
    if (typeof first.msg === "string" && first.msg.startsWith("Value error, ")) {
      return first.msg.slice("Value error, ".length);
    }
  }
  return GENERIC_ERROR;
}

async function authRequest(path, body) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      // No Content-Type without a body: it would force a CORS preflight for
      // nothing on the bodiless resend call.
      headers: body ? { "Content-Type": "application/json" } : undefined,
      credentials: "include",
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new AuthRequestError(GENERIC_ERROR, 0);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // A body that is not JSON is treated as having no detail.
  }
  if (response.ok) return data;

  // Same treatment as the chat's 429: tell the student how long, from the
  // header, instead of leaving them pressing the button.
  if (response.status === 429) {
    const header = Number(response.headers.get("Retry-After"));
    throw new AuthRequestError(
      rateLimitMessage(Number.isFinite(header) && header > 0 ? header : null),
      429
    );
  }
  throw new AuthRequestError(messageFrom(data), response.status);
}

export const signUp = ({ email, password, displayName }) =>
  authRequest("/auth/signup", { email, password, display_name: displayName });

export const logIn = ({ email, password }) =>
  authRequest("/auth/login", { email, password });

/** Always resolves with the same generic acknowledgement on 202. */
export const forgotPassword = (email) =>
  authRequest("/auth/forgot-password", { email });

export const resetPassword = (token, newPassword) =>
  authRequest("/auth/reset-password", { token, new_password: newPassword });

export const resendVerification = () => authRequest("/auth/resend-verification");
