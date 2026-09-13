import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  deleteUser,
  errorMessage,
  fetchUser,
  fullDate,
  revokeSessions,
  UnauthorizedError,
  updateUser,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import AdminAvatar from "../../components/admin/AdminAvatar.jsx";

/**
 * One account: what it is, what can be edited, and the two consequential
 * actions (end every session, delete). Both of those ask for confirmation
 * inline rather than through window.confirm, so the question sits next to the
 * button it is about and names the account.
 */
export default function AdminUserDetail() {
  const { id } = useParams();
  const { user: me, onUnauthorized } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [account, setAccount] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [form, setForm] = useState(null);
  const [notice, setNotice] = useState(location.state?.created ? "Compte créé." : null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null); // save | revoke | delete
  const [confirming, setConfirming] = useState(null); // revoke | delete

  function fail(err) {
    if (err instanceof UnauthorizedError) onUnauthorized();
    else setError(errorMessage(err));
  }

  useEffect(() => {
    let cancelled = false;
    fetchUser(id)
      .then((u) => {
        if (cancelled) return;
        setAccount(u);
        setForm({
          display_name: u.display_name ?? "",
          email_verified: u.email_verified,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setLoadError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [id, onUnauthorized]);

  if (loadError) {
    return (
      <div className="adm-page adm-page-narrow">
        <Link to="/admin/utilisateurs" className="adm-back">
          ← Utilisateurs
        </Link>
        <p className="adm-alert">{loadError}</p>
      </div>
    );
  }
  if (!account) {
    return (
      <div className="adm-page adm-page-narrow">
        <div className="adm-skel adm-skel-block" aria-hidden="true" />
      </div>
    );
  }

  const isSelf = me?.id === account.id;
  const isAdminAccount = account.role === "admin";
  const dirty =
    form.display_name.trim() !== (account.display_name ?? "") ||
    form.email_verified !== account.email_verified;

  async function save(e) {
    e.preventDefault();
    setBusy("save");
    setError(null);
    setNotice(null);
    try {
      const updated = await updateUser(account.id, {
        display_name: form.display_name,
        email_verified: form.email_verified,
      });
      setAccount(updated);
      setForm({
        display_name: updated.display_name ?? "",
        email_verified: updated.email_verified,
      });
      setNotice("Modifications enregistrées.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doRevoke() {
    setBusy("revoke");
    setError(null);
    setNotice(null);
    try {
      setAccount(await revokeSessions(account.id));
      setConfirming(null);
      // Revoking your own sessions includes this one; the next call 401s and
      // App.jsx sends you to sign in, which is the honest outcome.
      setNotice("Toutes les sessions de ce compte ont été fermées.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doDelete() {
    setBusy("delete");
    setError(null);
    try {
      await deleteUser(account.id);
      navigate("/admin/utilisateurs", { replace: true });
    } catch (err) {
      fail(err);
      setBusy(null);
      setConfirming(null);
    }
  }

  const name = account.display_name || account.email;

  return (
    <div className="adm-page adm-page-narrow">
      <Link to="/admin/utilisateurs" className="adm-back">
        ← Utilisateurs
      </Link>

      <header className="adm-profile">
        <AdminAvatar seed={account.id} label={name} size="lg" />
        <div>
          <h1 className="adm-h1">{account.display_name || "Sans nom"}</h1>
          <p className="adm-sub">
            {account.email}
            <span className={`adm-tag adm-tag-${account.role}`}>
              {isAdminAccount ? "Admin" : "Élève"}
            </span>
            {isSelf && <span className="adm-tag adm-tag-dim">Toi</span>}
          </p>
        </div>
      </header>

      {notice && (
        <p className="adm-notice" role="status">
          {notice}
        </p>
      )}
      {error && (
        <p className="adm-alert" role="alert">
          {error}
        </p>
      )}

      <section className="adm-panel">
        <h2 className="adm-h2">Informations</h2>
        <dl className="adm-facts">
          <div>
            <dt>Identifiant</dt>
            <dd>
              <code>{account.id}</code>
            </dd>
          </div>
          <div>
            <dt>Connexion</dt>
            <dd>
              {account.auth_method === "google" ? "Google" : "E-mail + mot de passe"}
            </dd>
          </div>
          <div>
            <dt>Inscrit le</dt>
            <dd>{fullDate(account.created_at)}</dd>
          </div>
          <div>
            <dt>Dernière connexion</dt>
            <dd>{fullDate(account.last_login_at)}</dd>
          </div>
          <div>
            <dt>Sessions fermées le</dt>
            <dd>{fullDate(account.sessions_valid_after)}</dd>
          </div>
        </dl>
      </section>

      <form className="adm-panel adm-form" onSubmit={save}>
        <h2 className="adm-h2">Modifier</h2>
        <label className="adm-field">
          <span>Nom affiché</span>
          <input
            className="adm-input"
            required
            maxLength={80}
            value={form.display_name}
            onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
          />
        </label>
        <label className="adm-check">
          <input
            type="checkbox"
            checked={form.email_verified}
            onChange={(e) =>
              setForm((f) => ({ ...f, email_verified: e.target.checked }))
            }
          />
          <span>Adresse e-mail confirmée</span>
        </label>
        <p className="adm-muted adm-small">
          L'adresse e-mail et le rôle ne se modifient pas depuis la console.
        </p>
        <div className="adm-form-actions">
          <button
            className="adm-btn adm-btn-primary"
            disabled={!dirty || busy === "save"}
          >
            {busy === "save" ? "Enregistrement…" : "Enregistrer"}
          </button>
        </div>
      </form>

      <section className="adm-panel adm-danger">
        <h2 className="adm-h2">Actions sensibles</h2>

        <div className="adm-danger-row">
          <div>
            <p className="adm-strong">Fermer toutes les sessions</p>
            <p className="adm-muted adm-small">
              Déconnecte ce compte sur tous ses appareils. Il pourra se reconnecter.
            </p>
          </div>
          {confirming === "revoke" ? (
            <span className="adm-confirm">
              <button className="adm-btn" onClick={() => setConfirming(null)}>
                Annuler
              </button>
              <button
                className="adm-btn adm-btn-warn"
                disabled={busy === "revoke"}
                onClick={doRevoke}
              >
                Confirmer
              </button>
            </span>
          ) : (
            <button className="adm-btn" onClick={() => setConfirming("revoke")}>
              Déconnecter
            </button>
          )}
        </div>

        <div className="adm-danger-row">
          <div>
            <p className="adm-strong">Supprimer le compte</p>
            <p className="adm-muted adm-small">
              {isSelf
                ? "Tu ne peux pas supprimer ton propre compte."
                : isAdminAccount
                  ? "Un compte admin doit d'abord perdre son rôle via promote_admin.py."
                  : "Définitif : le compte et ses données sont effacés."}
            </p>
          </div>
          {confirming === "delete" ? (
            <span className="adm-confirm">
              <button className="adm-btn" onClick={() => setConfirming(null)}>
                Annuler
              </button>
              <button
                className="adm-btn adm-btn-danger"
                disabled={busy === "delete"}
                onClick={doDelete}
              >
                Supprimer {name}
              </button>
            </span>
          ) : (
            <button
              className="adm-btn adm-btn-danger-ghost"
              disabled={isSelf || isAdminAccount}
              onClick={() => setConfirming("delete")}
            >
              Supprimer
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
