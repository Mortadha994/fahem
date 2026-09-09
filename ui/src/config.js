/**
 * Single place for frontend configuration.
 *
 * Values only - no logic, no imports from the rest of the app, so this can
 * be imported anywhere without a cycle. The modules that use these keep
 * their logic where it was; only the constants moved here.
 */

// Vite inlines import.meta.env at BUILD time, so changing the backend URL
// means rebuilding the frontend image - see ui/Dockerfile's VITE_API_URL
// build arg. It is the browser that calls the backend, so this must be
// reachable from the host, not from inside the compose network.
export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// The corpus holds exactly one niveau/chapitre, so these are fixed labels
// rather than a selector. Add a picker when a second chapter is ingested.
export const NIVEAU = "2eme";
export const CHAPITRE = "1";
export const SCOPE_LABEL =
  "2ème — Chapitre 1 : Les structures de données et les structures simples";
