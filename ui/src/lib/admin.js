import { API_URL } from "../config.js";

/**
 * Calls against the Phase 7 admin endpoints.
 *
 * Same shape as lib/chapters.js, with one more error type: an admin route has
 * two distinct refusals and the screen must treat them differently. 401 means
 * the session is gone (send the user to sign in); 403 means the session is
 * fine but the account is not an admin (signing in again will not help).
 */

/** A 401: the session went away. */
export class UnauthorizedError extends Error {}

/** A 403: signed in, but not as an admin. */
export class ForbiddenError extends Error {}

/** Anything else; the caller shows a retry. */
export class AdminError extends Error {}

/** The server's confirmation that the caller is an admin. */
export async function fetchAdminWhoAmI() {
  let response;
  try {
    response = await fetch(`${API_URL}/admin/whoami`, { credentials: "include" });
  } catch (err) {
    throw new AdminError(`network failure on /admin/whoami: ${err.message}`);
  }
  if (response.status === 401) throw new UnauthorizedError("/admin/whoami");
  if (response.status === 403) throw new ForbiddenError("/admin/whoami");
  if (!response.ok) throw new AdminError(`/admin/whoami returned ${response.status}`);
  return response.json();
}
