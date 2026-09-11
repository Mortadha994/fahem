import GoogleSignIn from "./GoogleSignIn.jsx";
import Alert from "./ui/Alert.jsx";
import { SCOPE_LABEL } from "../config.js";

/**
 * What an unauthenticated visitor sees instead of the chat.
 *
 * Deliberately says what Fahem is before asking for a sign-in - a bare Google
 * button on an unexplained page is the kind of thing students are told not to
 * click.
 */
export default function SignInScreen({ onCredential, busy, error }) {
  return (
    <div className="signin">
      <div className="signin-card surface">
        <span className="brand signin-brand">Fahem</span>

        <h1 className="signin-title">Ton tuteur d'algorithmique</h1>
        <p className="signin-lead">
          Colle l'énoncé d'un exercice. Fahem le résout avec la syntaxe de ton chapitre
          — et te montre exactement sur quelles parties du cours il s'appuie.
        </p>

        <div className="signin-action">
          <GoogleSignIn onCredential={onCredential} disabled={busy} />
          {busy && <p className="signin-busy">Connexion en cours…</p>}
          {error && <Alert>{error}</Alert>}
        </div>

        <p className="signin-foot">{SCOPE_LABEL}</p>
      </div>
    </div>
  );
}
