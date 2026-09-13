import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createUser, errorMessage, UnauthorizedError } from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { PASSWORD_MIN_LENGTH } from "../../lib/auth.js";

/**
 * Create a password account on a student's behalf. Always a student: roles
 * are not settable from the console. No email is sent - the student can use
 * "mot de passe oublié" to choose their own password.
 */
export default function AdminUserCreate() {
  const { onUnauthorized } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    display_name: "",
    email: "",
    password: "",
    email_verified: false,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const set = (key) => (e) =>
    setForm((f) => ({
      ...f,
      [key]: e.target.type === "checkbox" ? e.target.checked : e.target.value,
    }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await createUser(form);
      navigate(`/admin/utilisateurs/${user.id}`, {
        replace: true,
        state: { created: true },
      });
    } catch (err) {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="adm-page adm-page-narrow">
      <Link to="/admin/utilisateurs" className="adm-back">
        ← Utilisateurs
      </Link>
      <header className="adm-head">
        <div>
          <h1 className="adm-h1">Nouvel utilisateur</h1>
          <p className="adm-sub">Crée un compte élève avec e-mail et mot de passe.</p>
        </div>
      </header>

      <form className="adm-panel adm-form" onSubmit={submit}>
        {error && (
          <p className="adm-alert" role="alert">
            {error}
          </p>
        )}
        <label className="adm-field">
          <span>Nom affiché</span>
          <input
            className="adm-input"
            required
            maxLength={80}
            value={form.display_name}
            onChange={set("display_name")}
            autoComplete="off"
          />
        </label>
        <label className="adm-field">
          <span>Adresse e-mail</span>
          <input
            className="adm-input"
            type="email"
            required
            value={form.email}
            onChange={set("email")}
            autoComplete="off"
          />
        </label>
        <label className="adm-field">
          <span>Mot de passe initial</span>
          <input
            className="adm-input"
            type="password"
            required
            minLength={PASSWORD_MIN_LENGTH}
            value={form.password}
            onChange={set("password")}
            autoComplete="new-password"
          />
          <small className="adm-muted">
            {PASSWORD_MIN_LENGTH} caractères minimum. Transmets-le à l'élève par un
            canal sûr.
          </small>
        </label>
        <label className="adm-check">
          <input
            type="checkbox"
            checked={form.email_verified}
            onChange={set("email_verified")}
          />
          <span>Marquer l'adresse comme confirmée</span>
        </label>
        <div className="adm-form-actions">
          <Link to="/admin/utilisateurs" className="adm-btn">
            Annuler
          </Link>
          <button className="adm-btn adm-btn-primary" disabled={busy}>
            {busy ? "Création…" : "Créer le compte"}
          </button>
        </div>
      </form>
    </div>
  );
}
