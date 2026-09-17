import { createContext, useContext } from "react";

/**
 * The AI's state as the whole console shows it (sidebar card, top bar pill,
 * command palette): "on" | "paused" | "blocked" (daily budget guard reached),
 * or null while unknown. AdminLayout polls it; anything that changes it (the
 * controls panel, the palette) calls refresh() so every copy updates at once.
 */
export const AdminStatusContext = createContext({
  status: null,
  controls: null,
  refresh: () => {},
});

export const useAdminStatus = () => useContext(AdminStatusContext);

export function statusFrom(controls) {
  if (!controls) return null;
  if (controls.settings.ai_paused.value) return "paused";
  if (controls.budget.blocking) return "blocked";
  return "on";
}

export const STATUS_LABELS = {
  on: "IA active",
  paused: "IA en pause",
  blocked: "Garde-fou atteint",
};
