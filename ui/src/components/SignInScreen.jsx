import { useState } from "react";
import { useLocation } from "react-router-dom";
import AuthShell from "./AuthShell.jsx";
import GoogleSignIn from "./GoogleSignIn.jsx";
import PasswordAuthForm from "./PasswordAuthForm.jsx";
import Alert from "./ui/Alert.jsx";
import { verifyOutcomeMessage } from "../lib/verifyBanner.js";

const HEADINGS = {
  login: {
    title: "Bon retour sur Fahem",
    subtitle: "Connecte-toi pour continuer tes exercices.",
  },
  signup: {
    title: "Crée ton compte",
    subtitle:
      "Une adresse e-mail et un mot de passe, et tu peux poser ta première question.",
  },
  forgot: {
    title: "Mot de passe oublié",
    subtitle:
      "Indique ton adresse : si un compte Fahem l'utilise, on t'envoie un lien pour choisir un nouveau mot de passe.",
  },
};

/**
 * What an unauthenticated visitor sees instead of the app.
 *
 * The panel (AuthShell) says what Fahem is before anything is asked of the
 * student - a bare login form on an unexplained page is the kind of thing
 * students are told not to fill in.
 *
 * Google first, then email + password (Phase 5): Google is still the one-tap
 * path for students who have an account, and the form is the way in for those
 * who do not. In "forgot" mode the Google button steps aside so the one thing
 * on screen is the thing being asked for.
 *
 * `verifyOutcome` is the result of a confirmation link opened while signed
 * out - often on a phone, while the session lives on another device - so it
 * has to be shown here and not only inside the app.
 */
export default function SignInScreen({
  onCredential,
  onSignedIn,
  busy,
  error,
  verifyOutcome,
}) {
  const location = useLocation();
  // A dead reset link sends the student back here already in "forgot" mode.
  const [mode, setMode] = useState(() =>
    location.state?.authMode === "forgot" ? "forgot" : "login"
  );
  const { title, subtitle } = HEADINGS[mode];

  return (
    <AuthShell title={title} subtitle={subtitle}>
      {verifyOutcome && (
        <Alert
          tone={verifyOutcome === "ok" ? "info" : "warning"}
          className="signin-notice"
        >
          {verifyOutcomeMessage(verifyOutcome, false)}
        </Alert>
      )}

      {mode !== "forgot" && (
        <>
          <div className="signin-action">
            <GoogleSignIn onCredential={onCredential} disabled={busy} />
            {busy && <p className="signin-busy">Connexion en cours…</p>}
            {error && <Alert>{error}</Alert>}
          </div>
          <div className="auth-divider" aria-hidden="true">
            ou
          </div>
        </>
      )}

      <PasswordAuthForm mode={mode} onModeChange={setMode} onSignedIn={onSignedIn} />
    </AuthShell>
  );
}
