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
//
// localhost, NOT 127.0.0.1, and that is load-bearing since Phase 1: same-site
// is scheme + registrable domain (ports are irrelevant), so localhost:5173 ->
// localhost:8000 is same-site and the SameSite=Lax session cookie is sent,
// while localhost:5173 -> 127.0.0.1:8000 is cross-site and the browser
// withholds it. With the cookie withheld every request 401s and the app is
// stuck on the sign-in screen with no error explaining why.
export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Google OAuth client id. Not a secret - it ships in this bundle by design,
// and identifies the app to Google rather than authenticating it. Must be the
// same value as the backend's GOOGLE_CLIENT_ID: the backend checks the ID
// token's `aud` claim against its own copy, so a mismatch fails every
// sign-in. docker-compose.yml interpolates both from the same .env entry so
// they cannot drift.
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

// The corpus holds exactly one niveau/chapitre, so these are fixed labels
// rather than a selector. Add a picker when a second chapter is ingested.
export const NIVEAU = "2eme";
export const CHAPITRE = "1";
export const SCOPE_LABEL =
  "2ème — Chapitre 1 : Les structures de données et les structures simples";
