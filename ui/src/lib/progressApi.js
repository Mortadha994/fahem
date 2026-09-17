import { API_URL } from "../config.js";
import { ChapterError, UnauthorizedError } from "./chapters.js";

/**
 * The student's progress (GET /progress, see progress.py): per chapter each
 * exercise's status, the counts and the next exercise; the latest checked
 * solutions; the recurring notation mistakes. Same errors as lib/chapters.js.
 */
export async function fetchProgress() {
  let response;
  try {
    response = await fetch(`${API_URL}/progress`, { credentials: "include" });
  } catch (err) {
    throw new ChapterError(`network failure on /progress: ${err.message}`);
  }
  if (response.status === 401) throw new UnauthorizedError("/progress");
  if (!response.ok) throw new ChapterError(`/progress returned ${response.status}`);
  return response.json();
}

/** How an exercise's status reads to a student. */
export const EXERCISE_STATUS = {
  done: { label: "Réussi", short: "✓ Réussi", tone: "success" },
  solution_seen: { label: "Solution vue", short: "Solution vue", tone: "warning" },
  started: { label: "Commencé", short: "Commencé", tone: "neutral" },
};

export const VERDICT_LABELS = {
  correct: { label: "Correct", icon: "✓", tone: "success" },
  presque: { label: "Presque", icon: "≈", tone: "warning" },
  a_revoir: { label: "À revoir", icon: "✗", tone: "danger" },
};

/** answer_check.py's finding kinds, in words - and what to remember. */
export const MISTAKES = {
  operator: {
    label: "Opérateur Python dans l'algorithme",
    tip: "En algorithme : div, mod, ≠, ≤, ≥, ET, OU, NON - jamais //, %, !=, <=, and, or.",
  },
  assignment: {
    label: "Affectation écrite avec =",
    tip: "En algorithme, on affecte avec ← : somme ← a + b.",
  },
  lire: {
    label: "Type écrit dans Lire",
    tip: "Lire (x) seulement : le type va dans le tableau de déclaration.",
  },
  declaration: {
    label: "Tableau de déclaration oublié",
    tip: "Avant l'algorithme : le tableau Objet | Nature/type avec chaque variable.",
  },
};
