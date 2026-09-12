import { API_URL } from "../config.js";

/**
 * Calls against the admin endpoints (Phase 7 gate, Phase 8 user management).
 *
 * Same shape as lib/chapters.js, with one more error type: an admin route has
 * two distinct refusals and the console treats them differently. 401 means
 * the session is gone (send the user to sign in); 403 means the session is
 * fine but the account is not an admin (signing in again will not help).
 */

/** A 401: the session went away. */
export class UnauthorizedError extends Error {}

/** A 403: signed in, but not as an admin. */
export class ForbiddenError extends Error {}

/** Anything else. `status` and the server's `detail` are kept for the UI. */
export class AdminError extends Error {
  constructor(message, { status = 0, detail = null } = {}) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, query } = {}) {
  const url = new URL(`${API_URL}${path}`);
  for (const [k, v] of Object.entries(query ?? {})) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new AdminError(`network failure on ${path}: ${err.message}`);
  }

  if (response.status === 401) throw new UnauthorizedError(path);
  if (response.status === 403) throw new ForbiddenError(path);
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new AdminError(`${method} ${path} returned ${response.status}`, {
      status: response.status,
      detail: data?.detail ?? null,
    });
  }
  return data;
}

/**
 * A readable French message for a failed admin call. FastAPI's 422 detail is a
 * list of field errors; the password/name rules raise French messages already,
 * so the first one is shown as-is with pydantic's "Value error, " stripped.
 */
export function errorMessage(err) {
  if (!(err instanceof AdminError)) return "Une erreur est survenue.";
  const { status, detail } = err;
  if (Array.isArray(detail) && detail.length) {
    const d = detail[0];
    const field = d.loc?.[d.loc.length - 1];
    const msg = String(d.msg ?? "").replace(/^Value error, /, "");
    return field === "email" ? "Adresse e-mail invalide." : msg || "Données invalides.";
  }
  if (typeof detail === "string") {
    if (status === 409 && detail.includes("admin"))
      return "Un compte administrateur ne peut pas être supprimé ici. Retire d'abord le rôle avec promote_admin.py.";
    if (status === 400 && detail.includes("own account"))
      return "Tu ne peux pas supprimer ton propre compte.";
    if (status === 404) return "Compte introuvable.";
    return detail;
  }
  return status ? `Erreur ${status}.` : "Impossible de joindre le serveur.";
}

export const fetchAdminWhoAmI = () => request("/admin/whoami");
export const fetchAdminStats = () => request("/admin/stats");
export const fetchUsers = (query) => request("/admin/users", { query });
export const fetchUser = (id) => request(`/admin/users/${encodeURIComponent(id)}`);
export const createUser = (body) => request("/admin/users", { method: "POST", body });
export const updateUser = (id, body) =>
  request(`/admin/users/${encodeURIComponent(id)}`, { method: "PATCH", body });
export const revokeSessions = (id) =>
  request(`/admin/users/${encodeURIComponent(id)}/revoke-sessions`, { method: "POST" });
export const deleteUser = (id) =>
  request(`/admin/users/${encodeURIComponent(id)}`, { method: "DELETE" });

/** "il y a 3 j", "à l'instant" - for dense tables where a full date is noise. */
export function relativeTime(iso) {
  if (!iso) return "—";
  const seconds = Math.round((new Date(iso).getTime() - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("fr", { numeric: "auto", style: "short" });
  const steps = [
    ["year", 31536000],
    ["month", 2592000],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of steps) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return "à l'instant";
}

export function fullDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
