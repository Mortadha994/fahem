import { API_URL } from "../config.js";
import { GENERIC_ERROR } from "./api.js";

/**
 * The student profile: niveau and section, asked once after the first
 * sign-in (ProfileSetup.jsx) and kept on the account.
 *
 * Mirrors models.NIVEAUX / SECTIONS / SECTIONS_BY_NIVEAU on the backend,
 * which stays the authority - PUT /auth/me/profile rejects any pair not in
 * its own lists. The 2ème année has no Math or Technique section; those open
 * in 3ème.
 */
export const NIVEAUX = [
  { id: "2eme", label: "2ème année" },
  { id: "3eme", label: "3ème année" },
  { id: "bac", label: "Bac" },
];

export const SECTIONS = [
  { id: "informatique", label: "Informatique", short: "Info" },
  { id: "math", label: "Mathématiques", short: "Math" },
  { id: "sciences", label: "Sciences expérimentales", short: "Sciences" },
  { id: "technique", label: "Sciences techniques", short: "Technique" },
  { id: "eco", label: "Économie et gestion", short: "Éco" },
  { id: "lettres", label: "Lettres", short: "Lettres" },
];

export const SECTIONS_BY_NIVEAU = {
  "2eme": ["informatique", "sciences", "lettres", "eco"],
  "3eme": SECTIONS.map((s) => s.id),
  bac: SECTIONS.map((s) => s.id),
};

/** Whether the one-time question still has to be asked. Admins are not
 *  students, so they are never stopped by it. */
export function needsProfile(user) {
  return Boolean(user) && user.role !== "admin" && (!user.niveau || !user.section);
}

/** "3ème année · Informatique", or "" before the student has answered. */
export function profileLabel(user) {
  const niveau = NIVEAUX.find((n) => n.id === user?.niveau)?.label;
  const section = SECTIONS.find((s) => s.id === user?.section)?.label;
  return niveau && section ? `${niveau} · ${section}` : "";
}

/**
 * PUT /auth/me/profile. Resolves to the updated user, or
 * { unauthorized: true } / { error } on failure.
 */
export async function updateProfile(niveau, section) {
  let response;
  try {
    response = await fetch(`${API_URL}/auth/me/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ niveau, section }),
    });
  } catch {
    return { error: GENERIC_ERROR };
  }
  if (response.status === 401) return { unauthorized: true };
  if (!response.ok) return { error: GENERIC_ERROR };
  return { user: await response.json() };
}
