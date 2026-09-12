import { useId, useState } from "react";
import PasswordField from "./PasswordField.jsx";
import PasswordStrength from "./PasswordStrength.jsx";
import Alert from "./ui/Alert.jsx";
import Button from "./ui/Button.jsx";
import { forgotPassword, logIn, PASSWORD_MIN_LENGTH, signUp } from "../lib/auth.js";

const TITLES = {
  login: "Connexion avec ton adresse e-mail",
  signup: "Créer un compte",
  forgot: "Mot de passe oublié",
};
const SUBMIT = {
  login: "Se connecter",
  signup: "Créer mon compte",
  forgot: "Envoyer le lien",
};
const BUSY = {
  login: "Connexion…",
  signup: "Création…",
  forgot: "Envoi…",
};

function TextField({
  id,
  label,
  type = "text",
  value,
  onChange,
  autoComplete,
  inputMode,
}) {
  return (
    <div className="field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className="field-input"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        inputMode={inputMode}
        autoCapitalize={type === "email" ? "none" : undefined}
        spellCheck={type === "email" ? false : undefined}
        required
      />
    </div>
  );
}

/**
 * Email + password: sign in, create an account, or ask for a reset link.
 *
 * One form in three modes rather than three forms, so the address a student
 * already typed survives switching between them. The mode itself lives with
 * the parent (SignInScreen hides the Google button in "forgot").
 *
 * noValidate: the browser's own validation bubbles are in the browser's
 * language and look different on every device. The backend is the authority,
 * and its messages are already written for students.
 */
export default function PasswordAuthForm({ mode, onModeChange, onSignedIn }) {
  const id = useId();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [sentNotice, setSentNotice] = useState(null);
  // A short shake on a failed attempt: the Alert says what went wrong, the
  // motion says *that* something did, for anyone not reading the alert yet.
  const [shaking, setShaking] = useState(false);

  function switchTo(next) {
    setError(null);
    setSentNotice(null);
    setPassword("");
    onModeChange(next);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;
    setError(null);

    // Counted the way the backend counts (NFKC, code points), so the form
    // and the server never disagree about a borderline password.
    if (
      mode === "signup" &&
      [...password.normalize("NFKC")].length < PASSWORD_MIN_LENGTH
    ) {
      setError(
        `Le mot de passe doit contenir au moins ${PASSWORD_MIN_LENGTH} caractères.`
      );
      return;
    }

    setBusy(true);
    try {
      if (mode === "forgot") {
        const ack = await forgotPassword(email.trim());
        setSentNotice(ack.detail);
      } else if (mode === "signup") {
        onSignedIn(await signUp({ email: email.trim(), password, displayName }));
      } else {
        onSignedIn(await logIn({ email: email.trim(), password }));
      }
    } catch (err) {
      setError(err.message);
      setShaking(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-block">
      {mode !== "forgot" && (
        <div
          className="auth-toggle"
          role="group"
          aria-label="Choisir entre connexion et création de compte"
          data-active={mode}
        >
          {/* One highlight that slides between the two, instead of two
              buttons swapping fills: it shows the switch as one control. */}
          <span className="auth-toggle-indicator" aria-hidden="true" />
          <Button
            variant="ghost"
            className={mode === "login" ? "is-active" : ""}
            aria-pressed={mode === "login"}
            onClick={() => mode !== "login" && switchTo("login")}
          >
            Connexion
          </Button>
          <Button
            variant="ghost"
            className={mode === "signup" ? "is-active" : ""}
            aria-pressed={mode === "signup"}
            onClick={() => mode !== "signup" && switchTo("signup")}
          >
            Créer un compte
          </Button>
        </div>
      )}

      <form
        className={`auth-form${shaking ? " is-shaking" : ""}`}
        onSubmit={handleSubmit}
        onAnimationEnd={(e) => e.target === e.currentTarget && setShaking(false)}
        noValidate
        aria-labelledby={`${id}-title`}
      >
        {/* Names the form for screen readers. Hidden on screen: the page's
            visible <h1> (SignInScreen) already says the same thing, per mode. */}
        <h2 id={`${id}-title`} className="auth-form-title sr-only">
          {TITLES[mode]}
        </h2>

        {sentNotice ? (
          <Alert tone="info">{sentNotice}</Alert>
        ) : (
          <>
            {mode === "signup" && (
              <TextField
                id={`${id}-name`}
                label="Ton prénom (ou ton nom)"
                value={displayName}
                onChange={setDisplayName}
                autoComplete="name"
              />
            )}
            <TextField
              id={`${id}-email`}
              label="Adresse e-mail"
              type="email"
              inputMode="email"
              value={email}
              onChange={setEmail}
              autoComplete="email"
            />
            {mode !== "forgot" && (
              <PasswordField
                id={`${id}-password`}
                label="Mot de passe"
                value={password}
                onChange={setPassword}
                autoComplete={mode === "signup" ? "new-password" : "current-password"}
                hint={
                  mode === "signup"
                    ? `${PASSWORD_MIN_LENGTH} caractères minimum.`
                    : undefined
                }
                labelAction={
                  mode === "login" ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="field-label-action"
                      onClick={() => switchTo("forgot")}
                    >
                      Mot de passe oublié ?
                    </Button>
                  ) : undefined
                }
              />
            )}
            {mode === "signup" && <PasswordStrength value={password} />}

            {error && <Alert>{error}</Alert>}

            <Button
              type="submit"
              variant="primary"
              className="auth-submit"
              disabled={busy}
            >
              {busy ? BUSY[mode] : SUBMIT[mode]}
            </Button>
          </>
        )}
      </form>

      {mode === "forgot" && (
        <Button
          variant="ghost"
          size="sm"
          className="auth-link"
          onClick={() => switchTo("login")}
        >
          ← Retour à la connexion
        </Button>
      )}
    </div>
  );
}
