import { useCallback, useEffect, useState } from "react";
import * as m from "motion/react-m";
import {
  errorMessage,
  fetchControls,
  relativeTime,
  resetQueue,
  UnauthorizedError,
  updateControls,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { SPRING_ENTER, rise } from "../../lib/motion.js";

/**
 * "Contrôle de l'IA": what the Surveillance IA page shows, the admin can act on.
 *
 * Everything here writes to GET/PUT /admin/controls (admin_controls.py) and
 * takes effect for students within seconds, without a restart:
 *   - pause the AI, with the sentence students read meanwhile;
 *   - a daily budget guard that stops new requests at N % of Groq's daily
 *     token limit, so a reserve is always left;
 *   - the per-student limit, the maximum wait, the 429 retries, photo reading;
 *   - emptying a model's queue;
 * and every change lands in the log at the bottom, with who made it.
 *
 * Refreshed every REFRESH_MS for the budget and the queues; the settings form
 * is only refreshed while it has no unsaved edit, so a poll never erases what
 * the admin is typing.
 */

const REFRESH_MS = 15_000;
const GUARD_OPTIONS = [0, 70, 80, 90, 95];
const LIMIT_RE = /^\s*(\d+)\s*\/\s*minute\s*;\s*(\d+)\s*\/\s*hour\s*$/i;

const ACTIONS = {
  "settings.update": "Réglages de l'IA",
  "queue.reset": "File vidée",
  "user.update": "Compte modifié",
  "user.suspend": "Compte suspendu",
  "user.reactivate": "Compte réactivé",
};

const SETTING_LABELS = {
  ai_paused: "Pause",
  ai_pause_message: "Message de pause",
  daily_budget_guard_pct: "Garde-fou",
  solve_rate_limit: "Limite par élève",
  queue_timeout_seconds: "Attente max",
  retry_max: "Réessais",
  attachments_enabled: "Photos / PDF",
};

const nf = new Intl.NumberFormat("fr-FR");

/** "10/minute;100/hour" -> {perMinute: "10", perHour: "100"}; null if another shape. */
function splitLimit(text) {
  const match = LIMIT_RE.exec(text ?? "");
  return match ? { perMinute: match[1], perHour: match[2] } : null;
}

function formFrom(settings) {
  const limit = splitLimit(settings.solve_rate_limit.value);
  return {
    pauseMessage: settings.ai_pause_message.value,
    perMinute: limit?.perMinute ?? "",
    perHour: limit?.perHour ?? "",
    rawLimit: limit ? null : settings.solve_rate_limit.value,
    queueTimeout: String(settings.queue_timeout_seconds.value),
    retryMax: String(settings.retry_max.value),
    attachments: settings.attachments_enabled.value,
  };
}

function formValues(form) {
  return {
    ai_pause_message: form.pauseMessage,
    solve_rate_limit:
      form.rawLimit ?? `${Number(form.perMinute)}/minute;${Number(form.perHour)}/hour`,
    queue_timeout_seconds: Number(form.queueTimeout),
    retry_max: Number(form.retryMax),
    attachments_enabled: form.attachments,
  };
}

function describe(entry) {
  if (entry.action === "settings.update" && entry.detail) {
    return Object.entries(entry.detail)
      .map(([key, { new: value }]) => {
        const label = SETTING_LABELS[key] ?? key;
        if (typeof value === "boolean") {
          if (key === "ai_paused") return value ? "IA mise en pause" : "IA relancée";
          return `${label} : ${value ? "activé" : "désactivé"}`;
        }
        if (key === "daily_budget_guard_pct")
          return value ? `${label} : ${value} %` : `${label} : désactivé`;
        if (key === "queue_timeout_seconds") return `${label} : ${value} s`;
        if (key === "ai_pause_message") return `${label} modifié`;
        return `${label} : ${value}`;
      })
      .join(" · ");
  }
  if (entry.action === "user.update" && entry.detail) {
    return `${entry.target} — ${Object.keys(entry.detail).join(", ")}`;
  }
  return entry.target ?? "";
}

export default function AiControls({ onChanged }) {
  const { onUnauthorized } = useAuth();
  const [data, setData] = useState(null);
  const [form, setForm] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(null); // pause | guard | save | reset:<model>
  const [confirming, setConfirming] = useState(null); // pause | reset:<model>
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);

  const fail = useCallback(
    (err) => {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
    },
    [onUnauthorized]
  );

  const apply = useCallback((next, { resetForm }) => {
    setData(next);
    if (resetForm) {
      setForm(formFrom(next.settings));
      setDirty(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = (first) =>
      fetchControls()
        .then((next) => {
          if (cancelled) return;
          setData(next);
          if (first) setForm(formFrom(next.settings));
        })
        .catch((err) => !cancelled && fail(err));
    load(true);
    const id = setInterval(() => !document.hidden && load(false), REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [fail]);

  async function run(kind, action, success) {
    setBusy(kind);
    setError(null);
    setNotice(null);
    try {
      const next = await action();
      apply(next, { resetForm: kind === "save" || !dirty });
      setNotice(success);
      setConfirming(null);
      onChanged?.();
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  if (!data || !form) {
    return (
      <section className="adm-panel ctl" aria-label="Contrôle de l'IA">
        {error ? (
          <p className="adm-alert">{error}</p>
        ) : (
          <div className="adm-skel adm-skel-block" aria-hidden="true" />
        )}
      </section>
    );
  }

  const { settings, budget, queues, audit } = data;
  const paused = settings.ai_paused.value;
  const guard = settings.daily_budget_guard_pct.value;
  const status = paused ? "paused" : budget.blocking ? "blocked" : "on";
  const usedRatio = budget.limit ? Math.min(1, budget.used / budget.limit) : 0;
  const thresholdRatio =
    budget.threshold && budget.limit ? budget.threshold / budget.limit : null;

  const update = (patch) => {
    setForm((f) => ({ ...f, ...patch }));
    setDirty(true);
  };
  const limitInvalid =
    form.rawLimit === null &&
    (!(Number(form.perMinute) >= 1) || !(Number(form.perHour) >= 1));

  return (
    <m.section
      className={`adm-panel ctl is-${status}`}
      variants={rise}
      aria-label="Contrôle de l'IA"
    >
      <header className="adm-panel-head ctl-head">
        <div>
          <h2 className="adm-h2">Contrôle de l'IA</h2>
          <p className="adm-muted adm-small">
            Chaque réglage s'applique aux élèves en quelques secondes, sans redémarrer.
          </p>
        </div>
        <span className={`ctl-status is-${status}`} role="status">
          <i aria-hidden="true" />
          {status === "paused"
            ? "IA en pause"
            : status === "blocked"
              ? "Garde-fou atteint"
              : "IA active"}
        </span>
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

      <div className="ctl-grid">
        {/* --- pause ------------------------------------------------------ */}
        <div className="ctl-card ctl-pause">
          <p className="adm-strong">Pause / maintenance</p>
          <p className="adm-muted adm-small">
            {paused
              ? "Aucune requête n'atteint l'IA. Les élèves lisent ce message :"
              : "Coupe toutes les requêtes à l'IA. Les élèves liront ce message :"}
          </p>
          <textarea
            className="adm-input ctl-message"
            rows={2}
            maxLength={300}
            value={form.pauseMessage}
            onChange={(e) => update({ pauseMessage: e.target.value })}
            aria-label="Message affiché aux élèves pendant la pause"
          />
          {paused ? (
            <button
              className="adm-btn adm-btn-primary"
              disabled={busy === "pause"}
              onClick={() =>
                run(
                  "pause",
                  () => updateControls({ ai_paused: false }),
                  "L'IA est relancée."
                )
              }
            >
              {busy === "pause" ? "Relance…" : "Relancer l'IA"}
            </button>
          ) : confirming === "pause" ? (
            <span className="adm-confirm">
              <button className="adm-btn" onClick={() => setConfirming(null)}>
                Annuler
              </button>
              <button
                className="adm-btn adm-btn-danger"
                disabled={busy === "pause" || !form.pauseMessage.trim()}
                onClick={() =>
                  run(
                    "pause",
                    () =>
                      updateControls({
                        ai_paused: true,
                        ai_pause_message: form.pauseMessage,
                      }),
                    "L'IA est en pause."
                  )
                }
              >
                Confirmer la pause
              </button>
            </span>
          ) : (
            <button
              className="adm-btn adm-btn-warn"
              onClick={() => setConfirming("pause")}
            >
              Mettre l'IA en pause
            </button>
          )}
        </div>

        {/* --- daily budget guard -------------------------------------------- */}
        <div className="ctl-card">
          <p className="adm-strong">Garde-fou du budget journalier</p>
          <p className="adm-muted adm-small">
            Arrête les nouvelles requêtes à ce pourcentage de la limite de tokens par
            jour de Groq, pour garder une réserve.
          </p>
          <div className="adm-seg" role="radiogroup" aria-label="Seuil du garde-fou">
            {GUARD_OPTIONS.map((pct) => (
              <button
                key={pct}
                type="button"
                role="radio"
                aria-checked={guard === pct}
                className={`adm-seg-btn${guard === pct ? " is-on" : ""}`}
                disabled={busy === "guard"}
                onClick={() =>
                  guard !== pct &&
                  run(
                    "guard",
                    () => updateControls({ daily_budget_guard_pct: pct }),
                    pct ? `Garde-fou réglé à ${pct} %.` : "Garde-fou désactivé."
                  )
                }
              >
                {pct ? `${pct} %` : "Désactivé"}
              </button>
            ))}
          </div>
          <div
            className={`ctl-budget${budget.blocking ? " is-blocking" : ""}`}
            role="img"
            aria-label={`${nf.format(budget.used)} tokens utilisés sur ${nf.format(budget.limit)} aujourd'hui`}
          >
            <m.span
              className="ctl-budget-fill"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: usedRatio }}
              transition={{ ...SPRING_ENTER, visualDuration: 0.7 }}
            />
            {thresholdRatio !== null && (
              <span
                className="ctl-budget-mark"
                style={{ left: `${thresholdRatio * 100}%` }}
              />
            )}
          </div>
          <p className="adm-small ctl-budget-text">
            <span className="adm-strong">{nf.format(budget.used)}</span> /{" "}
            {nf.format(budget.limit)} tokens (24 h)
            {budget.threshold !== null && (
              <>
                {" "}
                · arrêt à{" "}
                <span className="adm-strong">{nf.format(budget.threshold)}</span>
              </>
            )}
          </p>
        </div>

        {/* --- limits ----------------------------------------------------------- */}
        <form
          className="ctl-card ctl-limits"
          onSubmit={(e) => {
            e.preventDefault();
            run(
              "save",
              () => updateControls(formValues(form)),
              "Réglages enregistrés."
            );
          }}
        >
          <p className="adm-strong">Limites et réglages</p>
          <div className="ctl-fields">
            <fieldset className="ctl-field">
              <legend>Limite par élève</legend>
              {form.rawLimit !== null ? (
                <input
                  className="adm-input"
                  value={form.rawLimit}
                  onChange={(e) => update({ rawLimit: e.target.value })}
                  aria-label="Limite par élève"
                />
              ) : (
                <span className="ctl-inline">
                  <input
                    className="adm-input ctl-num"
                    type="number"
                    min={1}
                    max={1000}
                    value={form.perMinute}
                    onChange={(e) => update({ perMinute: e.target.value })}
                    aria-label="Requêtes par minute"
                  />
                  / min
                  <input
                    className="adm-input ctl-num"
                    type="number"
                    min={1}
                    max={10000}
                    value={form.perHour}
                    onChange={(e) => update({ perHour: e.target.value })}
                    aria-label="Requêtes par heure"
                  />
                  / heure
                </span>
              )}
            </fieldset>
            <label className="ctl-field">
              <span>Attente max dans la file</span>
              <span className="ctl-inline">
                <input
                  className="adm-input ctl-num"
                  type="number"
                  min={15}
                  max={600}
                  value={form.queueTimeout}
                  onChange={(e) => update({ queueTimeout: e.target.value })}
                />
                secondes
              </span>
            </label>
            <label className="ctl-field">
              <span>Réessais après un refus Groq (429)</span>
              <span className="ctl-inline">
                <input
                  className="adm-input ctl-num"
                  type="number"
                  min={0}
                  max={5}
                  value={form.retryMax}
                  onChange={(e) => update({ retryMax: e.target.value })}
                />
                fois
              </span>
            </label>
            <label className="adm-check ctl-field">
              <input
                type="checkbox"
                checked={form.attachments}
                onChange={(e) => update({ attachments: e.target.checked })}
              />
              <span>Lecture des photos et PDF</span>
            </label>
          </div>
          <div className="adm-form-actions">
            {dirty && (
              <button
                type="button"
                className="adm-btn"
                onClick={() => {
                  setForm(formFrom(settings));
                  setDirty(false);
                }}
              >
                Annuler
              </button>
            )}
            <button
              className="adm-btn adm-btn-primary"
              disabled={!dirty || busy === "save" || limitInvalid}
            >
              {busy === "save" ? "Enregistrement…" : "Enregistrer"}
            </button>
          </div>
        </form>

        {/* --- queues -------------------------------------------------------------- */}
        <div className="ctl-card">
          <p className="adm-strong">Files d'attente</p>
          <p className="adm-muted adm-small">
            À vider seulement si une file semble bloquée : les demandes en attente se
            replacent d'elles-mêmes.
          </p>
          <ul className="ctl-queues">
            {queues.map((q) => {
              const key = `reset:${q.model}`;
              return (
                <li key={q.model}>
                  <span>
                    <span className="adm-strong">{q.label}</span>{" "}
                    <span className="adm-muted adm-small">
                      {q.waiting === null
                        ? "indisponible"
                        : `${q.active}/${q.max_concurrent} en cours · ${q.waiting} en attente`}
                    </span>
                  </span>
                  {confirming === key ? (
                    <span className="adm-confirm">
                      <button className="adm-btn" onClick={() => setConfirming(null)}>
                        Annuler
                      </button>
                      <button
                        className="adm-btn adm-btn-warn"
                        disabled={busy === key}
                        onClick={() =>
                          run(key, () => resetQueue(q.model), `File ${q.label} vidée.`)
                        }
                      >
                        Vider
                      </button>
                    </span>
                  ) : (
                    <button className="adm-btn" onClick={() => setConfirming(key)}>
                      Vider la file
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {/* --- log ------------------------------------------------------------------ */}
      <details className="ctl-log">
        <summary>
          Historique des actions admin{" "}
          <span className="adm-muted">({audit.length})</span>
        </summary>
        {audit.length === 0 ? (
          <p className="adm-muted adm-small">Aucune action pour l'instant.</p>
        ) : (
          <ul>
            {audit.map((entry, i) => (
              <li key={`${entry.at}-${i}`}>
                <span className="adm-strong">
                  {ACTIONS[entry.action] ?? entry.action}
                </span>
                <span className="ctl-log-detail">{describe(entry)}</span>
                <span className="adm-muted adm-small">
                  {entry.admin_email} · {relativeTime(entry.at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </details>
    </m.section>
  );
}
