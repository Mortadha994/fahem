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
  // A refused publish lists what blocks it (admin_chapters.publish_chapter).
  if (detail && Array.isArray(detail.problems)) {
    return `${detail.message ?? "Publication impossible."} ${detail.problems.join(" ")}`;
  }
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
    if (status === 404 && detail === "user not found") return "Compte introuvable.";
    return detail;
  }
  return status ? `Erreur ${status}.` : "Impossible de joindre le serveur.";
}

export const fetchAdminWhoAmI = () => request("/admin/whoami");
export const fetchAdminStats = () => request("/admin/stats");
/** Groq load, usage and chat activity (admin_monitoring.py). */
export const fetchMonitoring = () => request("/admin/monitoring");
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

// --- uploaded chapters (Phase 9) ---------------------------------------------

export const fetchChaptersAdmin = () => request("/admin/chapters");
export const fetchChapterAdmin = (id) =>
  request(`/admin/chapters/${encodeURIComponent(id)}`);
export const updateChapter = (id, body) =>
  request(`/admin/chapters/${encodeURIComponent(id)}`, { method: "PATCH", body });
export const deleteChapter = (id) =>
  request(`/admin/chapters/${encodeURIComponent(id)}`, { method: "DELETE" });
export const publishChapter = (id) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/publish`, { method: "POST" });
export const unpublishChapter = (id) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/unpublish`, { method: "POST" });
export const updateChunk = (id, chunkId, body) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/chunks/${chunkId}`, {
    method: "PATCH",
    body,
  });
export const deleteChunk = (id, chunkId) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/chunks/${chunkId}`, {
    method: "DELETE",
  });
export const addExercise = (id, body) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/exercises`, {
    method: "POST",
    body,
  });
export const updateExercise = (id, exId, body) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/exercises/${exId}`, {
    method: "PATCH",
    body,
  });
export const deleteExercise = (id, exId) =>
  request(`/admin/chapters/${encodeURIComponent(id)}/exercises/${exId}`, {
    method: "DELETE",
  });
export const chapterPdfUrl = (id) =>
  `${API_URL}/admin/chapters/${encodeURIComponent(id)}/pdf`;

const isMarkdown = (file) => /.(md|markdown)$/i.test(file.name);

async function sendFile(url, method, file, contentType) {
  let response;
  try {
    response = await fetch(url, {
      method,
      credentials: "include",
      headers: { "Content-Type": contentType },
      body: file,
    });
  } catch (err) {
    throw new AdminError(`network failure on upload: ${err.message}`);
  }
  if (response.status === 401) throw new UnauthorizedError("upload");
  if (response.status === 403) throw new ForbiddenError("upload");
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new AdminError(`upload returned ${response.status}`, {
      status: response.status,
      detail: data?.detail ?? null,
    });
  }
  return data;
}

/**
 * Send a chapter source: a PDF, or a Markdown course written to the template
 * (docs/modele-cours.md). The file is the raw request body, not multipart -
 * see admin_chapters.py. `replace` re-imports an existing chapter. A .md
 * course carries its own title, so `title` is only needed for a PDF.
 */
export function uploadChapterSource({ id, title, file, replace = false }) {
  const url = new URL(
    replace
      ? `${API_URL}/admin/chapters/${encodeURIComponent(id)}/source`
      : `${API_URL}/admin/chapters`
  );
  if (!replace) {
    url.searchParams.set("id", id);
    if (title) url.searchParams.set("title", title);
  }
  url.searchParams.set("filename", file.name);
  const type = isMarkdown(file) ? "text/markdown" : "application/pdf";
  return sendFile(url, replace ? "PUT" : "POST", file, type);
}

/** The PDF students open on the chapter page (no re-import). */
export function uploadChapterDocument(id, file) {
  const url = new URL(`${API_URL}/admin/chapters/${encodeURIComponent(id)}/document`);
  return sendFile(url, "PUT", file, "application/pdf");
}

export { isMarkdown };

export const CHAPTER_STATUS = {
  processing: { label: "Extraction…", tone: "busy" },
  failed: { label: "Échec", tone: "danger" },
  draft: { label: "Brouillon", tone: "dim" },
  publishing: { label: "Publication…", tone: "busy" },
  published: { label: "Publié", tone: "ok" },
};

export const FLAG_LABELS = {
  lost_arrow: "Flèche ← perdue ?",
  garbled: "Caractères illisibles",
  short: "Très court",
  ascii_arrow: "Flèche écrite <- (mettre ←)",
  merged_columns: "Colonnes Algo/Python mélangées",
};
