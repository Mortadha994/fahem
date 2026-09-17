/**
 * How the admin action log (admin_audit) reads in French: a title per action,
 * a label per changed field, and each value as a person would say it
 * ("10/min · 100/h", "désactivé", "Payante") rather than as it is stored.
 */

const NIVEAUX = { "2eme": "2ème année", "3eme": "3ème année", bac: "Bac" };
const SECTIONS = {
  informatique: "Informatique",
  math: "Mathématiques",
  sciences: "Sciences expérimentales",
  lettres: "Lettres",
  technique: "Sciences techniques",
  eco: "Économie et gestion",
};

export const CATEGORY_OF = (action) =>
  action.startsWith("settings.")
    ? "ia"
    : action.startsWith("user.")
      ? "comptes"
      : action.startsWith("queue.")
        ? "files"
        : "autre";

export const FIELD_LABELS = {
  // AI settings
  ai_paused: "IA",
  ai_pause_message: "Message de pause",
  daily_budget_guard_pct: "Garde-fou",
  solve_rate_limit: "Limite par élève",
  queue_timeout_seconds: "Attente max",
  retry_max: "Réessais (429)",
  attachments_enabled: "Photos et PDF",
  guided_mode_enabled: "Mode guidé",
  check_answer_enabled: "Vérifier ma réponse",
  default_chat_mode: "Mode par défaut",
  // account fields
  display_name: "Nom",
  email_verified: "E-mail confirmé",
  niveau: "Niveau",
  section: "Section",
  plan: "Offre",
};

/** "10/minute;100/hour" -> "10/min · 100/h". */
export function formatLimit(text) {
  if (!text) return "globale";
  return String(text)
    .split(";")
    .map((part) =>
      part
        .trim()
        .replace(/\/\s*second(s)?$/i, "/s")
        .replace(/\/\s*minute(s)?$/i, "/min")
        .replace(/\/\s*hour(s)?$/i, "/h")
        .replace(/\/\s*day(s)?$/i, "/jour")
    )
    .join(" · ");
}

export function formatValue(key, value, action = "") {
  if (value === null || value === undefined || value === "") {
    return key === "solve_rate_limit" && action.startsWith("user.") ? "globale" : "—";
  }
  switch (key) {
    case "ai_paused":
      return value ? "en pause" : "active";
    case "attachments_enabled":
      return value ? "activées" : "désactivées";
    case "guided_mode_enabled":
    case "check_answer_enabled":
      return value ? "activé" : "désactivé";
    case "default_chat_mode":
      return value === "guided" ? "guidé" : "solution complète";
    case "email_verified":
      return value ? "oui" : "non";
    case "daily_budget_guard_pct":
      return value ? `${value} %` : "désactivé";
    case "queue_timeout_seconds":
      return `${value} s`;
    case "solve_rate_limit":
      return formatLimit(value);
    case "plan":
      return value === "paid" ? "Payante" : "Gratuite";
    case "niveau":
      return NIVEAUX[value] ?? value;
    case "section":
      return SECTIONS[value] ?? value;
    case "ai_pause_message": {
      const text = String(value);
      return `« ${text.length > 60 ? `${text.slice(0, 57)}…` : text} »`;
    }
    default:
      return typeof value === "boolean" ? (value ? "oui" : "non") : String(value);
  }
}

/** The fields a log entry changed, as {key, label, old, new} (for chips). */
export function changesOf(entry) {
  if (
    !entry.detail ||
    !["settings.update", "settings.revert", "user.update"].includes(entry.action)
  )
    return [];
  return Object.entries(entry.detail)
    .filter(
      ([key, change]) => FIELD_LABELS[key] && change && typeof change === "object"
    )
    .map(([key, change]) => {
      let old = formatValue(key, change.old, entry.action);
      let next = formatValue(key, change.new, entry.action);
      // Two long texts cut at the same place read as identical: show the
      // part where they differ instead.
      if (
        old === next &&
        typeof change.old === "string" &&
        typeof change.new === "string"
      ) {
        [old, next] = differingExcerpts(change.old, change.new);
      }
      return { key, label: FIELD_LABELS[key], old, new: next };
    });
}

/** « …the part around the first difference… » for two long strings. */
export function differingExcerpts(a, b, width = 44) {
  let start = 0;
  while (start < a.length && start < b.length && a[start] === b[start]) start++;
  // Start a few words before the difference, on a word boundary.
  const space = a.lastIndexOf(" ", Math.max(0, start - 16));
  const from = space > 0 ? space + 1 : 0;
  const cut = (text) => {
    const piece = text.slice(from, from + width);
    return `« ${from > 0 ? "…" : ""}${piece}${from + width < text.length ? "…" : ""} »`;
  };
  return [a.length ? cut(a) : "« »", b.length ? cut(b) : "« »"];
}

/** One line saying what happened. */
export function titleOf(entry, queueLabel = (m) => m) {
  const keys = Object.keys(entry.detail ?? {});
  switch (entry.action) {
    case "settings.update":
      if (keys.length === 1 && keys[0] === "ai_paused")
        return entry.detail.ai_paused.new ? "IA mise en pause" : "IA relancée";
      if (keys.length === 1 && keys[0] === "daily_budget_guard_pct")
        return entry.detail.daily_budget_guard_pct.new
          ? "Garde-fou du budget réglé"
          : "Garde-fou du budget désactivé";
      return keys.length === 1
        ? `${FIELD_LABELS[keys[0]] ?? "Réglage"} modifié`
        : "Réglages de l'IA modifiés";
    case "settings.revert":
      return "Réglages rétablis";
    case "queue.reset":
      return `File d'attente vidée — ${queueLabel(entry.target)}`;
    case "user.update":
      return "Compte modifié";
    case "user.suspend":
      return "Compte suspendu";
    case "user.reactivate":
      return "Compte réactivé";
    default:
      return entry.action;
  }
}

/** "Aujourd'hui", "Hier", or "lundi 14 septembre". */
export function dayLabel(iso, now = new Date()) {
  const date = new Date(iso);
  const startOf = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((startOf(now) - startOf(date)) / 86_400_000);
  if (days === 0) return "Aujourd'hui";
  if (days === 1) return "Hier";
  return date.toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    ...(date.getFullYear() !== now.getFullYear() ? { year: "numeric" } : {}),
  });
}

export const timeOf = (iso) =>
  new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
