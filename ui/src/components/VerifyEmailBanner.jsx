import { useState } from "react";
import Alert from "./ui/Alert.jsx";
import Button from "./ui/Button.jsx";
import { useAuth } from "../lib/authContext.js";
import { resendVerification } from "../lib/auth.js";
import {
  dismissVerifyBanner,
  isVerifyBannerDismissed,
  verifyOutcomeMessage,
} from "../lib/verifyBanner.js";

/**
 * Two things under the app bar, both about the email address:
 *
 * 1. The outcome of a confirmation link just opened (?email_verifie=1|0),
 *    shown once and closable.
 * 2. A reminder for password accounts that have not confirmed yet, with a
 *    "Renvoyer l'e-mail" action. Never shown to Google accounts - Fahem has
 *    nothing for them to confirm. Nothing in the app is gated on it.
 *
 * Built from the Alert and Button primitives as they are: the close control
 * sits beside the Alert rather than inside it, so the primitive did not need
 * a new prop.
 */
export default function VerifyEmailBanner() {
  const { user, verifyOutcome, clearVerifyOutcome } = useAuth();
  const [dismissed, setDismissed] = useState(() => isVerifyBannerDismissed(user?.id));
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null); // { tone, text } after a resend

  const needsReminder =
    user?.auth_method === "password" && !user.email_verified && !dismissed;
  if (!verifyOutcome && !needsReminder) return null;

  async function resend() {
    if (sending) return;
    setSending(true);
    try {
      const ack = await resendVerification();
      setResult({ tone: "info", text: ack.detail });
    } catch (err) {
      setResult({ tone: "danger", text: err.message });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="verify-banner" role="region" aria-label="Adresse e-mail">
      {verifyOutcome && (
        <div className="verify-banner-row">
          <Alert tone={verifyOutcome === "ok" ? "info" : "warning"}>
            {verifyOutcomeMessage(verifyOutcome, true)}
          </Alert>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Fermer ce message"
            onClick={clearVerifyOutcome}
          >
            ×
          </Button>
        </div>
      )}
      {needsReminder && (
        <div className="verify-banner-row">
          <Alert
            tone={result?.tone ?? "warning"}
            action={
              result
                ? undefined
                : { label: sending ? "Envoi…" : "Renvoyer l'e-mail", onClick: resend }
            }
          >
            {result?.text ??
              `Confirme ton adresse e-mail : on t'a envoyé un lien à ${user.email}.`}
          </Alert>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Masquer ce rappel"
            onClick={() => {
              dismissVerifyBanner(user.id);
              setDismissed(true);
            }}
          >
            ×
          </Button>
        </div>
      )}
    </div>
  );
}
