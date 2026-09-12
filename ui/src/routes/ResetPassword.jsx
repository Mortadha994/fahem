import { useEffect, useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell.jsx";
import PasswordField from "../components/PasswordField.jsx";
import PasswordStrength from "../components/PasswordStrength.jsx";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import { PASSWORD_MIN_LENGTH, resetPassword } from "../lib/auth.js";

/** The token rides in the URL fragment (#token=...), which no server - not
 * nginx, not the API - ever receives. Read it once, at mount. */
function readToken() {
  return new URLSearchParams(window.location.hash.slice(1)).get("token") ?? "";
}

/**
 * The page the reset email links to. The only route App lets through without
 * a session - see App.jsx for how narrowly.
 *
 * On success the backend has already set a session cookie (and ended every
 * other session for the account); onSignedIn hands the user to App, which
 * moves the student into the app.
 */
export default function ResetPassword({ onSignedIn }) {
  const id = useId();
  const navigate = useNavigate();
  const [token] = useState(readToken);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [linkDead, setLinkDead] = useState(false);

  // Take the token out of the address bar and the history entry as soon as it
  // has been read, so it is not left on screen, in a screenshot, or one Back
  // press away. replaceState rather than navigate(): the router's copy of the
  // location is not the concern, the browser's is.
  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(
        window.history.state,
        "",
        window.location.pathname + window.location.search
      );
    }
  }, []);

  const requestNewLink = () =>
    navigate("/", { replace: true, state: { authMode: "forgot" } });

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;
    setError(null);
    if ([...password.normalize("NFKC")].length < PASSWORD_MIN_LENGTH) {
      setError(
        `Le mot de passe doit contenir au moins ${PASSWORD_MIN_LENGTH} caractères.`
      );
      return;
    }
    if (password !== confirm) {
      setError("Les deux mots de passe ne sont pas identiques.");
      return;
    }
    setBusy(true);
    try {
      onSignedIn(await resetPassword(token, password));
    } catch (err) {
      setError(err.message);
      // 400 is the backend's "invalid or expired link": retrying cannot help.
      if (err.status === 400) setLinkDead(true);
    } finally {
      setBusy(false);
    }
  }

  let body;
  if (!token) {
    body = (
      <>
        <Alert>
          Ce lien est incomplet. Ouvre à nouveau le lien reçu par e-mail, ou demande-en
          un nouveau.
        </Alert>
        <Button variant="secondary" className="auth-submit" onClick={requestNewLink}>
          Demander un nouveau lien
        </Button>
      </>
    );
  } else if (linkDead) {
    body = (
      <>
        <Alert>{error}</Alert>
        <Button variant="secondary" className="auth-submit" onClick={requestNewLink}>
          Demander un nouveau lien
        </Button>
      </>
    );
  } else {
    body = (
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <PasswordField
          id={`${id}-new`}
          label="Nouveau mot de passe"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          hint={`${PASSWORD_MIN_LENGTH} caractères minimum.`}
        />
        <PasswordStrength value={password} />
        <PasswordField
          id={`${id}-confirm`}
          label="Confirme le mot de passe"
          value={confirm}
          onChange={setConfirm}
          autoComplete="new-password"
        />
        {error && <Alert>{error}</Alert>}
        <Button type="submit" variant="primary" className="auth-submit" disabled={busy}>
          {busy ? "Enregistrement…" : "Enregistrer et me connecter"}
        </Button>
      </form>
    );
  }

  return (
    <AuthShell
      title="Choisis un nouveau mot de passe"
      subtitle="Une fois enregistré, tu es connecté ici et déconnecté de tous tes autres appareils."
    >
      {body}
    </AuthShell>
  );
}
