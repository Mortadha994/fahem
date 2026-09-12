/**
 * State for the "confirme ton adresse" reminder and the email-link outcome.
 *
 * Dismissal is per browser session and per user: it survives a reload (so
 * closing it is not immediately undone), but every sign-in and sign-out clears
 * it, so an account that is still unverified sees it again at the next login.
 * sessionStorage rather than localStorage for exactly that reason - it is
 * meant to go away.
 *
 * Every storage call is guarded: private windows and locked-down browsers can
 * throw on access, and a reminder banner is not worth crashing the app over.
 */

const PREFIX = "fahem.verifyBannerDismissed.";

export function isVerifyBannerDismissed(userId) {
  try {
    return sessionStorage.getItem(PREFIX + userId) === "1";
  } catch {
    return false;
  }
}

export function dismissVerifyBanner(userId) {
  try {
    sessionStorage.setItem(PREFIX + userId, "1");
  } catch {
    // Not persisted; the banner still hides for this render.
  }
}

export function clearVerifyBannerDismissals() {
  try {
    for (const key of Object.keys(sessionStorage)) {
      if (key.startsWith(PREFIX)) sessionStorage.removeItem(key);
    }
  } catch {
    // Nothing to clear.
  }
}

/**
 * `?email_verifie=1|0` is where the API's verify-email redirect lands.
 * Read once, at load; App strips it from the URL right after.
 */
export function readVerifyOutcome() {
  const value = new URLSearchParams(window.location.search).get("email_verifie");
  if (value === "1") return "ok";
  if (value === "0") return "failed";
  return null;
}

/** The sentence for an outcome, worded for whether the student is signed in. */
export function verifyOutcomeMessage(outcome, signedIn) {
  if (outcome === "ok") {
    return signedIn
      ? "Ton adresse e-mail est confirmée."
      : "Ton adresse e-mail est confirmée. Connecte-toi pour continuer.";
  }
  return signedIn
    ? "Ce lien de confirmation est invalide ou a déjà servi."
    : "Ce lien de confirmation est invalide ou a déjà servi. Connecte-toi pour en demander un nouveau.";
}
