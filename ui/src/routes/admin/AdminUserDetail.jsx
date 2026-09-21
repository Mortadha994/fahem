import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  deleteUser,
  errorMessage,
  fetchUser,
  fullDate,
  reactivateUser,
  revokeSessions,
  suspendUser,
  UnauthorizedError,
  updateUser,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { useToast } from "../../lib/toast.js";
import AdminAvatar from "../../components/admin/AdminAvatar.jsx";
import AdminTabs from "../../components/admin/AdminTabs.jsx";
import { IconActivity, IconShield, IconUser } from "../../components/admin/icons.jsx";
import UserActivity from "../../components/admin/UserActivity.jsx";

/* The school system, as the student's own profile question offers it
   (app/core/models.py NIVEAUX / SECTIONS / SECTIONS_BY_NIVEAU). */
const NIVEAUX = [
  ["2eme", "2ème année"],
  ["3eme", "3ème année"],
  ["bac", "Bac"],
];
const SECTIONS = {
  informatique: "Informatique",
  math: "Mathématiques",
  sciences: "Sciences expérimentales",
  lettres: "Lettres",
  technique: "Sciences techniques",
  eco: "Économie et gestion",
};
const SECTIONS_BY_NIVEAU = {
  "2eme": ["informatique", "sciences", "lettres", "eco"],
  "3eme": Object.keys(SECTIONS),
  bac: Object.keys(SECTIONS),
};
const LIMIT_RE = /^\s*(\d+)\s*\/\s*minute\s*;\s*(\d+)\s*\/\s*hour\s*$/i;

/**
 * The subscription in words.
 *
 * `plan` is what is stored, `current_plan` what applies today; they differ
 * once the end date has passed. Saying only "Payante" for a lapsed account
 * would explain neither why the student is being throttled nor what to do
 * about it, so the lapsed case names its date.
 */
function planLabel(u) {
  const day = u.plan_until
    ? new Date(u.plan_until).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : null;
  if (u.plan !== "paid") return "Gratuite";
  if (u.current_plan !== "paid") return day ? `Expirée le ${day}` : "Expirée";
  return day ? `Payante jusqu'au ${day}` : "Payante (sans date de fin)";
}

/** The editable account fields, as the form holds them. */
function accountForm(u) {
  const limit = LIMIT_RE.exec(u.solve_rate_limit ?? "");
  return {
    niveau: u.niveau ?? "",
    section: u.section ?? "",
    plan: u.plan ?? "free",
    // <input type="date"> wants YYYY-MM-DD; the API sends an ISO instant.
    // Empty means "no end date", which is what the backend reads as null.
    planUntil: u.plan_until ? u.plan_until.slice(0, 10) : "",
    customLimit: Boolean(u.solve_rate_limit),
    perMinute: limit?.[1] ?? "5",
    perHour: limit?.[2] ?? "50",
  };
}

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
  const toast = useToast();
  const [busy, setBusy] = useState(null); // save | account | suspend | reactivate | revoke | delete
  const [confirming, setConfirming] = useState(null); // suspend | revoke | delete
  const [control, setControl] = useState(null); // accountForm()
  const [reason, setReason] = useState("");

  function fail(err) {
    if (err instanceof UnauthorizedError) onUnauthorized();
    else toast.error(errorMessage(err));
  }

  // Arriving from "Créer un compte": say so once (the ref survives StrictMode's
  // double effect in development).
  const announced = useRef(false);
  const created = Boolean(location.state?.created);
  useEffect(() => {
    if (created && !announced.current) {
      announced.current = true;
      toast.success("Compte créé.");
    }
  }, [created, toast]);

  useEffect(() => {
    let cancelled = false;
    fetchUser(id)
      .then((u) => {
        if (cancelled) return;
        setAccount(u);
        setControl(accountForm(u));
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
      toast.success("Modifications enregistrées.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  const controlDirty =
    control &&
    account &&
    (control.niveau !== (account.niveau ?? "") ||
      control.section !== (account.section ?? "") ||
      control.plan !== (account.plan ?? "free") ||
      control.planUntil !==
        (account.plan_until ? account.plan_until.slice(0, 10) : "") ||
      control.customLimit !== Boolean(account.solve_rate_limit) ||
      (control.customLimit &&
        `${Number(control.perMinute)}/minute;${Number(control.perHour)}/hour` !==
          account.solve_rate_limit));
  const sectionOk =
    !control?.niveau || SECTIONS_BY_NIVEAU[control.niveau]?.includes(control.section);
  const limitOk =
    !control?.customLimit ||
    (Number(control.perMinute) >= 1 && Number(control.perHour) >= 1);

  async function saveControl(e) {
    e.preventDefault();
    setBusy("account");
    const body = {
      plan: control.plan,
      solve_rate_limit: control.customLimit
        ? `${Number(control.perMinute)}/minute;${Number(control.perHour)}/hour`
        : null,
    };
    // plan_until is sent only when it actually changes, or when the plan goes
    // back to free (which clears it - an end date without a subscription
    // means nothing, and a kept one would resurrect itself the next time the
    // plan was set to paid). An expired account's form loads with the date it
    // lapsed on, and the backend refuses a past date; resending it unchanged
    // would make editing that account's class impossible.
    const savedUntil = account.plan_until ? account.plan_until.slice(0, 10) : "";
    if (control.plan !== "paid") {
      if (account.plan_until) body.plan_until = null;
    } else if (control.planUntil !== savedUntil) {
      // End of the chosen day, not its midnight: a subscription "until the
      // 3rd" that stopped working at 00:00 on the 3rd would read as a bug to
      // whoever set it.
      body.plan_until = control.planUntil
        ? new Date(`${control.planUntil}T23:59:59`).toISOString()
        : null;
    }
    if (
      control.niveau !== (account.niveau ?? "") ||
      control.section !== (account.section ?? "")
    ) {
      body.niveau = control.niveau || null;
      body.section = control.niveau ? control.section : null;
    }
    try {
      const updated = await updateUser(account.id, body);
      setAccount(updated);
      setControl(accountForm(updated));
      toast.success("Classe, offre et limite enregistrées.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doSuspend() {
    setBusy("suspend");
    try {
      const updated = await suspendUser(account.id, reason);
      setAccount(updated);
      setConfirming(null);
      setReason("");
      toast.success(
        "Compte suspendu : ses sessions sont fermées et il ne peut plus se connecter."
      );
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doReactivate() {
    setBusy("reactivate");
    try {
      setAccount(await reactivateUser(account.id));
      toast.success("Compte réactivé : l'élève peut se reconnecter.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doRevoke() {
    setBusy("revoke");
    try {
      setAccount(await revokeSessions(account.id));
      setConfirming(null);
      // Revoking your own sessions includes this one; the next call 401s and
      // App.jsx sends you to sign in, which is the honest outcome.
      toast.success("Toutes les sessions de ce compte ont été fermées.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  async function doDelete() {
    setBusy("delete");
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

  const niveauLabel = NIVEAUX.find(([key]) => key === account.niveau)?.[1];
  const tabs = [
    { id: "profil", label: "Profil", Icon: IconUser },
    { id: "activite", label: "Activité", Icon: IconActivity },
    {
      id: "securite",
      label: "Sécurité",
      Icon: IconShield,
      badge: account.suspended_at ? <span className="adm-dot is-paused" /> : null,
    },
  ];

  return (
    <div className="adm-page">
      <Link to="/admin/utilisateurs" className="adm-back">
        ← Utilisateurs
      </Link>

      <div className="adm-user-layout">
        {/* Who this is, always in view while editing. */}
        <aside className="adm-panel adm-id-card">
          <AdminAvatar seed={account.id} label={name} size="lg" />
          <h1 className="adm-h1">{account.display_name || "Sans nom"}</h1>
          <p className="adm-muted adm-id-mail">{account.email}</p>
          <p className="adm-id-tags">
            <span className={`adm-tag adm-tag-${account.role}`}>
              {isAdminAccount ? "Admin" : "Élève"}
            </span>
            {isSelf && <span className="adm-tag adm-tag-dim">Toi</span>}
            {account.suspended_at && (
              <span className="adm-tag adm-tag-danger">Suspendu</span>
            )}
            {account.current_plan === "paid" && (
              <span className="adm-tag adm-tag-ok">Payant</span>
            )}
            {account.plan === "paid" && account.current_plan !== "paid" && (
              <span className="adm-tag adm-tag-dim">Abonnement expiré</span>
            )}
          </p>

          {!isAdminAccount && (
            <dl className="adm-id-stats">
              <div>
                <dt>Classe</dt>
                <dd>
                  {niveauLabel
                    ? `${niveauLabel}${account.section ? ` · ${SECTIONS[account.section]}` : ""}`
                    : "Non renseignée"}
                </dd>
              </div>
              <div>
                <dt>Offre</dt>
                <dd>{planLabel(account)}</dd>
              </div>
              <div>
                <dt>Limite</dt>
                <dd>
                  {account.solve_rate_limit
                    ? account.solve_rate_limit.replace(";", " · ")
                    : "Globale"}
                </dd>
              </div>
            </dl>
          )}

          <dl className="adm-facts adm-facts-compact">
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
        </aside>

        <div className="adm-user-main">
          <AdminTabs label="Sections du compte" tabs={tabs}>
            {(tab) =>
              tab === "activite" ? (
                <div className="adm-panel">
                  <h2 className="adm-h2">Douze dernières semaines</h2>
                  <UserActivity userId={account.id} />
                </div>
              ) : tab === "profil" ? (
                <div className="adm-stack">
                  <form className="adm-panel adm-form" onSubmit={save}>
                    <h2 className="adm-h2">Modifier</h2>
                    <label className="adm-field">
                      <span>Nom affiché</span>
                      <input
                        className="adm-input"
                        required
                        maxLength={80}
                        value={form.display_name}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, display_name: e.target.value }))
                        }
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

                  {!isAdminAccount && control && (
                    <form className="adm-panel adm-form" onSubmit={saveControl}>
                      <h2 className="adm-h2">Classe, offre et limite</h2>
                      <div className="ctl-fields">
                        <label className="adm-field">
                          <span>Niveau</span>
                          <select
                            className="adm-input"
                            value={control.niveau}
                            onChange={(e) => {
                              const niveau = e.target.value;
                              setControl((c) => ({
                                ...c,
                                niveau,
                                section: SECTIONS_BY_NIVEAU[niveau]?.includes(c.section)
                                  ? c.section
                                  : (SECTIONS_BY_NIVEAU[niveau]?.[0] ?? ""),
                              }));
                            }}
                          >
                            <option value="">Non renseigné</option>
                            {NIVEAUX.map(([key, label]) => (
                              <option key={key} value={key}>
                                {label}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="adm-field">
                          <span>Section</span>
                          <select
                            className="adm-input"
                            value={control.section}
                            disabled={!control.niveau}
                            onChange={(e) =>
                              setControl((c) => ({ ...c, section: e.target.value }))
                            }
                          >
                            {!control.niveau && <option value="">—</option>}
                            {(SECTIONS_BY_NIVEAU[control.niveau] ?? []).map((key) => (
                              <option key={key} value={key}>
                                {SECTIONS[key]}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="adm-field">
                          <span>Offre</span>
                          <select
                            className="adm-input"
                            value={control.plan}
                            onChange={(e) =>
                              setControl((c) => ({ ...c, plan: e.target.value }))
                            }
                          >
                            {/* One word each. The select is a third of the
                                row, and a parenthesis explaining what the
                                paid tier gives was cut off mid-word
                                ("limites éla…"); it belongs in the hint
                                below, where there is room for it. */}
                            <option value="free">Gratuite</option>
                            <option value="paid">Payante</option>
                          </select>
                          {control.plan === "paid" && (
                            <small className="adm-hint">
                              Prioritaire dans la file, limites élargies.
                            </small>
                          )}
                        </label>
                        {control.plan === "paid" && (
                          <label className="adm-field">
                            <span>Fin de l'abonnement</span>
                            <input
                              type="date"
                              className="adm-input"
                              value={control.planUntil}
                              // Deliberately no `min`. A lapsed account's form
                              // loads with the date it lapsed on, and a `min`
                              // made the browser block the whole form - in
                              // English, on a French page - so an admin could
                              // not change the section of an expired account
                              // without first editing a date they had no
                              // business touching. The backend refuses a past
                              // date in French, and an unchanged one is never
                              // sent (see saveControl).
                              onChange={(e) =>
                                setControl((c) => ({ ...c, planUntil: e.target.value }))
                              }
                            />
                            <small className="adm-hint">
                              Laisser vide : sans date de fin.
                            </small>
                          </label>
                        )}
                      </div>

                      <fieldset className="ctl-field">
                        <legend>Limite de requêtes</legend>
                        <label className="adm-check">
                          <input
                            type="radio"
                            name="limit"
                            checked={!control.customLimit}
                            onChange={() =>
                              setControl((c) => ({ ...c, customLimit: false }))
                            }
                          />
                          <span>Limite globale (réglée dans Surveillance IA)</span>
                        </label>
                        <label className="adm-check">
                          <input
                            type="radio"
                            name="limit"
                            checked={control.customLimit}
                            onChange={() =>
                              setControl((c) => ({ ...c, customLimit: true }))
                            }
                          />
                          <span>Limite personnelle</span>
                        </label>
                        {control.customLimit && (
                          <span className="ctl-inline">
                            <input
                              className="adm-input ctl-num"
                              type="number"
                              min={1}
                              value={control.perMinute}
                              onChange={(e) =>
                                setControl((c) => ({ ...c, perMinute: e.target.value }))
                              }
                              aria-label="Requêtes par minute"
                            />
                            / min
                            <input
                              className="adm-input ctl-num"
                              type="number"
                              min={1}
                              value={control.perHour}
                              onChange={(e) =>
                                setControl((c) => ({ ...c, perHour: e.target.value }))
                              }
                              aria-label="Requêtes par heure"
                            />
                            / heure
                          </span>
                        )}
                      </fieldset>

                      <div className="adm-form-actions">
                        <button
                          className="adm-btn adm-btn-primary"
                          disabled={
                            !controlDirty ||
                            !sectionOk ||
                            !limitOk ||
                            busy === "account"
                          }
                        >
                          {busy === "account" ? "Enregistrement…" : "Enregistrer"}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              ) : (
                <div className="adm-stack">
                  <section className="adm-panel adm-danger">
                    <h2 className="adm-h2">Actions sensibles</h2>

                    <div className="adm-danger-row">
                      <div>
                        <p className="adm-strong">
                          {account.suspended_at
                            ? "Compte suspendu"
                            : "Suspendre le compte"}
                        </p>
                        <p className="adm-muted adm-small">
                          {isSelf
                            ? "Tu ne peux pas suspendre ton propre compte."
                            : isAdminAccount
                              ? "Un compte admin ne se suspend pas depuis la console."
                              : account.suspended_at
                                ? `Depuis le ${fullDate(account.suspended_at)}${
                                    account.suspended_reason
                                      ? ` — « ${account.suspended_reason} »`
                                      : ""
                                  }. L'élève ne peut plus se connecter.`
                                : "Ferme ses sessions et bloque la connexion, sans rien effacer. Réversible."}
                        </p>
                        {confirming === "suspend" && (
                          <input
                            className="adm-input ctl-reason"
                            placeholder="Raison (visible par les admins seulement)"
                            maxLength={300}
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            aria-label="Raison de la suspension"
                          />
                        )}
                      </div>
                      {account.suspended_at ? (
                        <button
                          className="adm-btn adm-btn-primary"
                          disabled={busy === "reactivate"}
                          onClick={doReactivate}
                        >
                          {busy === "reactivate" ? "Réactivation…" : "Réactiver"}
                        </button>
                      ) : confirming === "suspend" ? (
                        <span className="adm-confirm">
                          <button
                            className="adm-btn"
                            onClick={() => setConfirming(null)}
                          >
                            Annuler
                          </button>
                          <button
                            className="adm-btn adm-btn-danger"
                            disabled={busy === "suspend"}
                            onClick={doSuspend}
                          >
                            Suspendre {name}
                          </button>
                        </span>
                      ) : (
                        <button
                          className="adm-btn adm-btn-warn"
                          disabled={isSelf || isAdminAccount}
                          onClick={() => setConfirming("suspend")}
                        >
                          Suspendre
                        </button>
                      )}
                    </div>

                    <div className="adm-danger-row">
                      <div>
                        <p className="adm-strong">Fermer toutes les sessions</p>
                        <p className="adm-muted adm-small">
                          Déconnecte ce compte sur tous ses appareils. Il pourra se
                          reconnecter.
                        </p>
                      </div>
                      {confirming === "revoke" ? (
                        <span className="adm-confirm">
                          <button
                            className="adm-btn"
                            onClick={() => setConfirming(null)}
                          >
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
                        <button
                          className="adm-btn"
                          onClick={() => setConfirming("revoke")}
                        >
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
                              ? "Un compte admin doit d'abord perdre son rôle via scripts/promote_admin.py."
                              : "Définitif : le compte et ses données sont effacés."}
                        </p>
                      </div>
                      {confirming === "delete" ? (
                        <span className="adm-confirm">
                          <button
                            className="adm-btn"
                            onClick={() => setConfirming(null)}
                          >
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
              )
            }
          </AdminTabs>
        </div>
      </div>
    </div>
  );
}
