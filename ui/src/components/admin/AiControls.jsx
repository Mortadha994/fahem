import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";
import {
  errorMessage,
  fetchControls,
  relativeTime,
  resetQueue,
  revertAudit,
  UnauthorizedError,
  updateControls,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { useAdminStatus } from "../../lib/adminStatus.js";
import { useToast } from "../../lib/toast.js";
import { formatValue } from "../../lib/auditFormat.js";
import { SPRING_ENTER, rise, stagger } from "../../lib/motion.js";
import "./controls.css";

/**
 * "Contrôles": what the Surveillance IA page shows, the admin can act on.
 *
 * Everything writes to GET/PUT /admin/controls (app/routes/admin/admin_controls.py) and takes
 * effect for students within seconds, without a restart. The page reads top
 * to bottom as the questions an admin asks:
 *
 *   1. Is the AI on?            the status card: pause / relaunch, and the
 *                               daily budget with its guard;
 *   2. What can students use?   one switch per feature (photos, Mode guidé,
 *                               Vérifier ma réponse, exercices similaires);
 *   3. How much can they ask?   steppers for the limits;
 *   4. Is anything stuck?       the queues.
 *
 * Pause, relaunch, the guard and a queue reset apply at once (each asks first
 * when it matters). Switches and limits are edited together and saved from
 * the bar that slides up as soon as something differs from what is live - it
 * counts the changes and can undo them. The history of every change lives in
 * its own tab, Journal (AuditLog.jsx).
 *
 * Refreshed every REFRESH_MS for the budget and the queues; the form is only
 * refreshed while it has no unsaved change, so a poll never erases an edit.
 */

const REFRESH_MS = 15_000;
const GUARD_OPTIONS = [0, 70, 80, 90, 95];
const LIMIT_RE = /^\s*(\d+)\s*\/\s*minute\s*;\s*(\d+)\s*\/\s*hour\s*$/i;
const nf = new Intl.NumberFormat("fr-FR");

const SPRING_SWITCH = { type: "spring", visualDuration: 0.25, bounce: 0.25 };

// The form's fields and the setting each one writes.
const FORM_KEYS = [
  "solve_rate_limit",
  "queue_timeout_seconds",
  "retry_max",
  "attachments_enabled",
  "guided_mode_enabled",
  "check_answer_enabled",
  "default_chat_mode",
  "practice_enabled",
  "practice_daily_limit",
];

function splitLimit(text) {
  const match = LIMIT_RE.exec(text ?? "");
  return match ? { perMinute: match[1], perHour: match[2] } : null;
}

function formFrom(settings, which = "value") {
  const limit = splitLimit(settings.solve_rate_limit[which]);
  return {
    pauseMessage: settings.ai_pause_message.value,
    perMinute: limit?.perMinute ?? "",
    perHour: limit?.perHour ?? "",
    rawLimit: limit ? null : settings.solve_rate_limit[which],
    queueTimeout: String(settings.queue_timeout_seconds[which]),
    retryMax: String(settings.retry_max[which]),
    attachments: settings.attachments_enabled[which],
    guided: settings.guided_mode_enabled[which],
    check: settings.check_answer_enabled[which],
    defaultMode: settings.default_chat_mode[which],
    practice: settings.practice_enabled[which],
    practiceLimit: String(settings.practice_daily_limit[which]),
  };
}

function formValues(form) {
  return {
    solve_rate_limit:
      form.rawLimit ?? `${Number(form.perMinute)}/minute;${Number(form.perHour)}/hour`,
    queue_timeout_seconds: Number(form.queueTimeout),
    retry_max: Number(form.retryMax),
    attachments_enabled: form.attachments,
    guided_mode_enabled: form.guided,
    check_answer_enabled: form.check,
    default_chat_mode: form.guided ? form.defaultMode : "full",
    practice_enabled: form.practice,
    practice_daily_limit: Number(form.practiceLimit),
  };
}

/** The settings keys whose form value differs from the live one. */
function changedKeys(form, settings) {
  const values = formValues(form);
  return FORM_KEYS.filter((key) => {
    const live = settings[key].value;
    if (key === "default_chat_mode" && !values.guided_mode_enabled) return false;
    return String(values[key]) !== String(live);
  });
}

export default function AiControls({ onChanged }) {
  const { onUnauthorized } = useAuth();
  const { refresh: refreshStatus } = useAdminStatus();
  const [, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(null); // pause | guard | save | reset:<model>
  const [confirming, setConfirming] = useState(null); // pause | reset:<model>
  const [error, setError] = useState(null);
  const toast = useToast();

  const changes = useMemo(
    () => (data && form ? changedKeys(form, data.settings) : []),
    [data, form]
  );
  const dirty = changes.length > 0;

  const fail = useCallback(
    (err) => {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
    },
    [onUnauthorized]
  );

  useEffect(() => {
    let cancelled = false;
    const load = (first) =>
      fetchControls()
        .then((next) => {
          if (cancelled) return;
          // A form without an edit follows what is live (another admin may
          // have changed it); one with an edit is left alone.
          setData((previous) => {
            setForm((f) =>
              first || !f || !previous
                ? formFrom(next.settings)
                : changedKeys(f, previous.settings).length === 0
                  ? { ...formFrom(next.settings), pauseMessage: f.pauseMessage }
                  : f
            );
            return next;
          });
        })
        .catch((err) => !cancelled && fail(err));
    load(true);
    const id = setInterval(() => !document.hidden && load(false), REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [fail]);

  function applied(next, resetForm) {
    setData(next);
    if (resetForm) setForm(formFrom(next.settings));
    onChanged?.();
    refreshStatus();
  }

  async function run(kind, action, success) {
    setBusy(kind);
    setError(null);
    try {
      const next = await action();
      applied(next, kind === "save" || !dirty);
      setConfirming(null);
      const entry = next.audit?.[0];
      const undo =
        entry?.revertible && entry.action === "settings.update"
          ? {
              label: "Annuler",
              run: async () => {
                try {
                  applied(await revertAudit(entry.id), true);
                  toast.info("Changement annulé.");
                } catch (err) {
                  if (err instanceof UnauthorizedError) onUnauthorized();
                  else toast.error(errorMessage(err));
                }
              },
            }
          : undefined;
      toast.success(success, { action: undo });
    } catch (err) {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else toast.error(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  if (!data || !form) {
    return (
      <section className="cx" aria-label="Contrôles de l'IA">
        {error ? (
          <p className="adm-alert">{error}</p>
        ) : (
          <div className="cx-skeleton" aria-hidden="true">
            <div className="adm-skel adm-skel-block" />
            <div className="adm-skel adm-skel-block" />
          </div>
        )}
      </section>
    );
  }

  const { settings, budget, queues } = data;
  const paused = settings.ai_paused.value;
  const guard = settings.daily_budget_guard_pct.value;
  const status = paused ? "paused" : budget.blocking ? "blocked" : "on";
  const update = (patch) => setForm((f) => ({ ...f, ...patch }));
  const limitInvalid =
    form.rawLimit === null &&
    (!(Number(form.perMinute) >= 1) || !(Number(form.perHour) >= 1));
  const changed = (key) => changes.includes(key);

  const save = () =>
    run("save", () => updateControls(formValues(form)), "Réglages enregistrés.");

  return (
    <m.div className="cx" variants={stagger(0.07)} initial="hidden" animate="show">
      {error && (
        <p className="adm-alert" role="alert">
          {error}
        </p>
      )}

      {/* --- 1. is the AI on? ------------------------------------------------------ */}
      <m.section
        className={`cx-hero is-${status}`}
        variants={rise}
        aria-label="État de l'IA"
      >
        <div className="cx-hero-main">
          <span className="cx-orb" aria-hidden="true">
            <m.span
              className="cx-orb-ring"
              animate={
                status === "on"
                  ? { scale: [1, 1.9], opacity: [0.5, 0] }
                  : { scale: 1, opacity: 0 }
              }
              transition={
                status === "on"
                  ? { duration: 1.8, repeat: Infinity, ease: "easeOut" }
                  : { duration: 0.2 }
              }
            />
            <span className="cx-orb-core" />
          </span>
          <div className="cx-hero-text">
            <p className="cx-eyebrow">État de l'IA</p>
            <h2 className="cx-hero-title">
              {status === "paused"
                ? "En pause"
                : status === "blocked"
                  ? "Garde-fou atteint"
                  : "Active"}
            </h2>
            {/* The heading is read when the panel opens; a change of state is
                announced separately, which a heading alone would not do. */}
            <span className="sr-only" role="status">
              {status === "paused"
                ? "L'IA est en pause."
                : status === "blocked"
                  ? "Le garde-fou du budget est atteint."
                  : "L'IA est active."}
            </span>
            <p className="cx-hero-sub">
              {status === "paused"
                ? "Aucune requête n'atteint l'IA : les élèves lisent ton message."
                : status === "blocked"
                  ? "Le budget du jour a atteint le garde-fou : les nouvelles demandes sont refusées."
                  : "Les élèves peuvent poser leurs questions. Chaque réglage s'applique en quelques secondes."}
            </p>
            <SettingMeta settings={settings} keys={["ai_paused", "ai_pause_message"]} />
          </div>
          <div className="cx-hero-action">
            {paused ? (
              <m.button
                type="button"
                className="cx-big-btn is-go"
                disabled={busy === "pause"}
                whileTap={{ scale: 0.96 }}
                onClick={() =>
                  run(
                    "pause",
                    () => updateControls({ ai_paused: false }),
                    "L'IA est relancée."
                  )
                }
              >
                <PlayIcon /> {busy === "pause" ? "Relance…" : "Relancer l'IA"}
              </m.button>
            ) : (
              <m.button
                type="button"
                className="cx-big-btn is-stop"
                aria-expanded={confirming === "pause"}
                whileTap={{ scale: 0.96 }}
                onClick={() => setConfirming(confirming === "pause" ? null : "pause")}
              >
                <PauseIcon /> Mettre en pause
              </m.button>
            )}
          </div>
        </div>

        {/* The message students read: shown while paused, and before pausing. */}
        <AnimatePresence initial={false}>
          {(paused || confirming === "pause") && (
            <m.div
              key="pause"
              className="cx-reveal"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1, transition: SPRING_ENTER }}
              exit={{ height: 0, opacity: 0, transition: { duration: 0.18 } }}
            >
              <div className="cx-pause-box">
                <label className="cx-label" htmlFor="cx-pause-message">
                  Message affiché aux élèves pendant la pause
                </label>
                <textarea
                  id="cx-pause-message"
                  className="adm-input cx-textarea"
                  rows={2}
                  maxLength={300}
                  value={form.pauseMessage}
                  onChange={(e) => update({ pauseMessage: e.target.value })}
                />
                <div className="cx-row-end">
                  <span className="cx-count">{form.pauseMessage.length} / 300</span>
                  {paused ? (
                    <button
                      type="button"
                      className="adm-btn"
                      disabled={
                        busy === "pause-message" ||
                        form.pauseMessage === settings.ai_pause_message.value ||
                        !form.pauseMessage.trim()
                      }
                      onClick={() =>
                        run(
                          "pause-message",
                          () => updateControls({ ai_pause_message: form.pauseMessage }),
                          "Message mis à jour."
                        )
                      }
                    >
                      Mettre à jour le message
                    </button>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="adm-btn"
                        onClick={() => setConfirming(null)}
                      >
                        Annuler
                      </button>
                      <button
                        type="button"
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
                    </>
                  )}
                </div>
              </div>
            </m.div>
          )}
        </AnimatePresence>

        <BudgetCard
          budget={budget}
          guard={guard}
          busy={busy === "guard"}
          settings={settings}
          onGuard={(pct) =>
            guard !== pct &&
            run(
              "guard",
              () => updateControls({ daily_budget_guard_pct: pct }),
              pct ? `Garde-fou réglé à ${pct} %.` : "Garde-fou désactivé."
            )
          }
        />
      </m.section>

      <div className="cx-columns">
        {/* --- 2. what can students use? ----------------------------------------------- */}
        <m.section className="cx-card" variants={rise} aria-labelledby="cx-features">
          <CardHead
            id="cx-features"
            icon={<SparkIcon />}
            title="Fonctionnalités des élèves"
            sub="Ce que les élèves voient dans le chat."
          />
          <div className="cx-rows">
            <SwitchRow
              icon={<CameraIcon />}
              title="Photos et PDF"
              description="L'élève envoie une photo ou un PDF de son exercice."
              checked={form.attachments}
              changed={changed("attachments_enabled")}
              onChange={(v) => update({ attachments: v })}
            />
            <SwitchRow
              icon={<CompassIcon />}
              title="Mode guidé"
              description="Indices étape par étape avant la solution."
              checked={form.guided}
              changed={changed("guided_mode_enabled")}
              onChange={(v) => update({ guided: v })}
            >
              <div className="cx-sub">
                <span className="cx-sub-label">Mode d'une nouvelle discussion</span>
                <Segmented
                  name="cx-default-mode"
                  value={form.defaultMode}
                  onChange={(v) => update({ defaultMode: v })}
                  options={[
                    { value: "full", label: "Solution complète" },
                    { value: "guided", label: "Mode guidé" },
                  ]}
                  changed={changed("default_chat_mode")}
                />
              </div>
            </SwitchRow>
            <SwitchRow
              icon={<CheckIcon />}
              title="Vérifier ma réponse"
              description="Correction ligne par ligne des solutions des élèves."
              checked={form.check}
              changed={changed("check_answer_enabled")}
              onChange={(v) => update({ check: v })}
            />
            <SwitchRow
              icon={<DiceIcon />}
              title="Exercices similaires"
              description="Nouveaux énoncés générés, plus faciles ou plus difficiles."
              checked={form.practice}
              changed={changed("practice_enabled")}
              onChange={(v) => update({ practice: v })}
            >
              <div className="cx-sub">
                <span className="cx-sub-label">Par élève et par jour</span>
                <Stepper
                  label="Exercices similaires par élève et par jour"
                  value={form.practiceLimit}
                  min={1}
                  max={100}
                  suffix="/ jour"
                  changed={changed("practice_daily_limit")}
                  onChange={(v) => update({ practiceLimit: v })}
                />
              </div>
            </SwitchRow>
          </div>
          <SettingMeta
            settings={settings}
            keys={[
              "attachments_enabled",
              "guided_mode_enabled",
              "check_answer_enabled",
              "default_chat_mode",
              "practice_enabled",
              "practice_daily_limit",
            ]}
          />
        </m.section>

        <div className="cx-stack">
          {/* --- 3. how much can they ask? ----------------------------------------------- */}
          <m.section className="cx-card" variants={rise} aria-labelledby="cx-limits">
            <CardHead
              id="cx-limits"
              icon={<GaugeIcon />}
              title="Limites d'utilisation"
              sub="Protègent le budget Groq quand beaucoup d'élèves sont connectés."
            />
            <div className="cx-limits">
              {form.rawLimit !== null ? (
                <label className="cx-limit is-wide">
                  <span className="cx-limit-title">Limite par élève</span>
                  <input
                    className="adm-input"
                    value={form.rawLimit}
                    onChange={(e) => update({ rawLimit: e.target.value })}
                  />
                </label>
              ) : (
                <>
                  <LimitField
                    title="Questions par minute"
                    hint="par élève"
                    setting={settings.solve_rate_limit}
                    settingKey="solve_rate_limit"
                    changed={changed("solve_rate_limit")}
                  >
                    <Stepper
                      label="Questions par minute"
                      value={form.perMinute}
                      min={1}
                      max={1000}
                      onChange={(v) => update({ perMinute: v })}
                    />
                  </LimitField>
                  <LimitField
                    title="Questions par heure"
                    hint="par élève"
                    changed={changed("solve_rate_limit")}
                  >
                    <Stepper
                      label="Questions par heure"
                      value={form.perHour}
                      min={1}
                      max={10000}
                      step={10}
                      onChange={(v) => update({ perHour: v })}
                    />
                  </LimitField>
                </>
              )}
              <LimitField
                title="Attente max"
                hint="dans la file, en secondes"
                setting={settings.queue_timeout_seconds}
                settingKey="queue_timeout_seconds"
                current={form.queueTimeout}
                changed={changed("queue_timeout_seconds")}
              >
                <Stepper
                  label="Attente max dans la file, en secondes"
                  value={form.queueTimeout}
                  min={15}
                  max={600}
                  step={15}
                  suffix="s"
                  onChange={(v) => update({ queueTimeout: v })}
                />
              </LimitField>
              <LimitField
                title="Réessais"
                hint="après un refus Groq (429)"
                setting={settings.retry_max}
                settingKey="retry_max"
                current={form.retryMax}
                changed={changed("retry_max")}
              >
                <Stepper
                  label="Réessais après un refus Groq"
                  value={form.retryMax}
                  min={0}
                  max={5}
                  onChange={(v) => update({ retryMax: v })}
                />
              </LimitField>
            </div>
            <SettingMeta
              settings={settings}
              keys={["solve_rate_limit", "queue_timeout_seconds", "retry_max"]}
            />
          </m.section>

          {/* --- 4. is anything stuck? ----------------------------------------------------- */}
          <m.section className="cx-card" variants={rise} aria-labelledby="cx-queues">
            <CardHead
              id="cx-queues"
              icon={<LayersIcon />}
              title="Files d'attente"
              sub="À vider seulement si une file semble bloquée."
            />
            <ul className="cx-queues">
              {queues.map((q) => {
                const key = `reset:${q.model}`;
                const load = q.max_concurrent
                  ? Math.min(1, (q.active ?? 0) / q.max_concurrent)
                  : 0;
                return (
                  <li key={q.model} className="cx-queue">
                    <div className="cx-queue-top">
                      <span className="cx-queue-name">{q.label}</span>
                      <span className="cx-queue-stats">
                        {q.waiting === null ? (
                          "indisponible"
                        ) : (
                          <>
                            <b>{q.active}</b>/{q.max_concurrent} en cours ·{" "}
                            <b>{q.waiting}</b> en attente
                          </>
                        )}
                      </span>
                    </div>
                    <span className="cx-queue-bar" aria-hidden="true">
                      <m.span
                        className="cx-queue-fill"
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: load }}
                        transition={SPRING_ENTER}
                      />
                    </span>
                    <AnimatePresence mode="wait" initial={false}>
                      {confirming === key ? (
                        <m.span
                          key="confirm"
                          className="cx-row-end"
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                        >
                          <span className="cx-count">
                            Les demandes en attente seront relancées.
                          </span>
                          <button
                            type="button"
                            className="adm-btn"
                            onClick={() => setConfirming(null)}
                          >
                            Annuler
                          </button>
                          <button
                            type="button"
                            className="adm-btn adm-btn-warn"
                            disabled={busy === key}
                            onClick={() =>
                              run(
                                key,
                                () => resetQueue(q.model),
                                `File ${q.label} vidée.`
                              )
                            }
                          >
                            Vider
                          </button>
                        </m.span>
                      ) : (
                        <m.span
                          key="idle"
                          className="cx-row-end"
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                        >
                          <button
                            type="button"
                            className="adm-btn"
                            onClick={() => setConfirming(key)}
                          >
                            Vider la file
                          </button>
                        </m.span>
                      )}
                    </AnimatePresence>
                  </li>
                );
              })}
            </ul>
          </m.section>
        </div>
      </div>

      <m.p className="cx-journal-link" variants={rise}>
        Chaque changement est enregistré avec son auteur.{" "}
        <button
          type="button"
          className="cx-link"
          onClick={() => setParams({ onglet: "journal" }, { replace: true })}
        >
          Ouvrir le journal des actions →
        </button>
      </m.p>

      {/* --- the unsaved changes bar ------------------------------------------------------------ */}
      <AnimatePresence>
        {dirty && (
          <m.div
            className="cx-savebar"
            role="region"
            aria-label="Changements non enregistrés"
            initial={{ y: 80, opacity: 0 }}
            animate={{
              y: 0,
              opacity: 1,
              transition: { type: "spring", visualDuration: 0.35, bounce: 0.2 },
            }}
            exit={{ y: 80, opacity: 0, transition: { duration: 0.18 } }}
          >
            <span className="cx-savebar-text">
              <m.span
                key={changes.length}
                className="cx-savebar-count"
                initial={{ scale: 0.6 }}
                animate={{ scale: 1, transition: SPRING_SWITCH }}
              >
                {changes.length}
              </m.span>
              changement{changes.length > 1 ? "s" : ""} non enregistré
              {changes.length > 1 ? "s" : ""}
            </span>
            <span className="cx-savebar-actions">
              <button
                type="button"
                className="adm-btn cx-savebar-ghost"
                onClick={() => setForm(formFrom(settings))}
              >
                Annuler
              </button>
              <button
                type="button"
                className="adm-btn adm-btn-primary"
                disabled={busy === "save" || limitInvalid}
                onClick={save}
              >
                {busy === "save" ? "Enregistrement…" : "Enregistrer"}
              </button>
            </span>
          </m.div>
        )}
      </AnimatePresence>
      <DefaultsButton
        onReset={() =>
          setForm((f) => ({
            ...formFrom(settings, "default"),
            pauseMessage: f.pauseMessage,
          }))
        }
      />
    </m.div>
  );
}

/* --- the budget ------------------------------------------------------------------------------ */

function BudgetCard({ budget, guard, onGuard, busy, settings }) {
  const used = budget.limit ? Math.min(1, budget.used / budget.limit) : 0;
  const threshold =
    budget.threshold && budget.limit ? budget.threshold / budget.limit : null;
  const r = 34;
  const circumference = 2 * Math.PI * r;
  return (
    <div className="cx-budget">
      <div
        className="cx-ring"
        role="img"
        aria-label={`${Math.round(used * 100)} % du budget du jour utilisé`}
      >
        <svg viewBox="0 0 80 80">
          <circle className="cx-ring-track" cx="40" cy="40" r={r} />
          <m.circle
            className={`cx-ring-fill${budget.blocking ? " is-blocking" : used > 0.8 ? " is-hot" : ""}`}
            cx="40"
            cy="40"
            r={r}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - used) }}
            transition={{ ...SPRING_ENTER, visualDuration: 0.9 }}
          />
          {threshold !== null && (
            <line
              className="cx-ring-mark"
              x1="40"
              y1="2"
              x2="40"
              y2="12"
              transform={`rotate(${threshold * 360} 40 40)`}
            />
          )}
        </svg>
        <span className="cx-ring-text">{Math.round(used * 100)}%</span>
      </div>
      <div className="cx-budget-body">
        <p className="cx-budget-title">Budget du jour</p>
        <p className="cx-budget-sub">
          <b>{nf.format(budget.used)}</b> / {nf.format(budget.limit)} tokens sur 24 h
          {budget.threshold !== null && (
            <>
              {" "}
              · arrêt à <b>{nf.format(budget.threshold)}</b>
            </>
          )}
        </p>
        <span className="cx-sub-label">
          Garde-fou : arrêter les nouvelles demandes à
        </span>
        <Segmented
          name="cx-guard"
          value={guard}
          disabled={busy}
          onChange={onGuard}
          options={GUARD_OPTIONS.map((pct) => ({
            value: pct,
            label: pct ? `${pct} %` : "Jamais",
          }))}
        />
        <SettingMeta settings={settings} keys={["daily_budget_guard_pct"]} />
      </div>
    </div>
  );
}

/* --- building blocks -------------------------------------------------------------------------- */

function CardHead({ id, icon, title, sub }) {
  return (
    <header className="cx-card-head">
      <span className="cx-card-icon" aria-hidden="true">
        {icon}
      </span>
      <div>
        <h3 id={id} className="cx-card-title">
          {title}
        </h3>
        <p className="cx-card-sub">{sub}</p>
      </div>
    </header>
  );
}

/** A feature: icon, what it does, its switch; its own settings unfold when on. */
function SwitchRow({ icon, title, description, checked, onChange, changed, children }) {
  return (
    <div className={`cx-row${checked ? " is-on" : ""}${changed ? " is-changed" : ""}`}>
      <div className="cx-row-main">
        <span className="cx-row-icon" aria-hidden="true">
          {icon}
        </span>
        <span className="cx-row-text">
          <span className="cx-row-title">
            {title}
            {changed && (
              <span className="cx-dot" title="Modifié, pas encore enregistré" />
            )}
          </span>
          <span className="cx-row-desc">{description}</span>
        </span>
        <Switch checked={checked} onChange={onChange} label={title} />
      </div>
      {children && (
        <AnimatePresence initial={false}>
          {checked && (
            <m.div
              className="cx-reveal"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1, transition: SPRING_ENTER }}
              exit={{ height: 0, opacity: 0, transition: { duration: 0.16 } }}
            >
              {children}
            </m.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}

/** role="switch": the thumb springs across with a layout animation. */
function Switch({ checked, onChange, label, disabled }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      className={`cx-switch${checked ? " is-on" : ""}`}
      onClick={() => onChange(!checked)}
    >
      <m.span className="cx-switch-thumb" layout transition={SPRING_SWITCH} />
    </button>
  );
}

/** Choices side by side; the highlight slides to the chosen one (layoutId). */
function Segmented({ name, value, onChange, options, disabled, changed }) {
  return (
    <div className={`cx-seg${changed ? " is-changed" : ""}`} role="radiogroup">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={String(o.value)}
            type="button"
            role="radio"
            aria-checked={on}
            disabled={disabled}
            className={`cx-seg-btn${on ? " is-on" : ""}`}
            onClick={() => onChange(o.value)}
          >
            {on && (
              <m.span
                className="cx-seg-pill"
                layoutId={`${name}-pill`}
                transition={SPRING_SWITCH}
              />
            )}
            <span className="cx-seg-label">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}

/** − value + : big targets for a number, still typeable. */
function Stepper({ label, value, onChange, min, max, step = 1, suffix, changed }) {
  const n = Number(value);
  const set = (next) => onChange(String(Math.min(max, Math.max(min, next))));
  return (
    <span className={`cx-stepper${changed ? " is-changed" : ""}`}>
      <m.button
        type="button"
        className="cx-step-btn"
        aria-label={`${label} : moins`}
        disabled={!(n > min)}
        whileTap={{ scale: 0.85 }}
        onClick={() => set((Number.isFinite(n) ? n : min) - step)}
      >
        −
      </m.button>
      <input
        className="cx-step-input"
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        value={value}
        aria-label={label}
        onChange={(e) => onChange(e.target.value)}
      />
      {suffix && <span className="cx-step-suffix">{suffix}</span>}
      <m.button
        type="button"
        className="cx-step-btn"
        aria-label={`${label} : plus`}
        disabled={!(n < max)}
        whileTap={{ scale: 0.85 }}
        onClick={() => set((Number.isFinite(n) ? n : min) + step)}
      >
        +
      </m.button>
    </span>
  );
}

function LimitField({ title, hint, setting, settingKey, current, changed, children }) {
  return (
    <div className={`cx-limit${changed ? " is-changed" : ""}`}>
      <span className="cx-limit-title">
        {title}
        {changed && <span className="cx-dot" title="Modifié, pas encore enregistré" />}
      </span>
      <span className="cx-limit-hint">{hint}</span>
      {children}
      {setting &&
        current !== undefined &&
        String(current) !== String(setting.default) && (
          <span className="cx-default">
            défaut : {formatValue(settingKey, setting.default)}
          </span>
        )}
    </div>
  );
}

function DefaultsButton({ onReset }) {
  return (
    <p className="cx-defaults">
      <button type="button" className="cx-link" onClick={onReset}>
        Remettre les fonctionnalités et les limites par défaut
      </button>
    </p>
  );
}

/** "Modifié par x · il y a 3 h", or the default when never changed. */
function SettingMeta({ settings, keys }) {
  const last = keys
    .map((key) => settings[key])
    .filter((s) => s?.updated_at)
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))[0];
  return (
    <p className="cx-meta">
      {last
        ? `Modifié par ${last.updated_by ?? "un admin"} · ${relativeTime(last.updated_at)}`
        : "Valeurs par défaut, jamais modifiées"}
    </p>
  );
}

/* --- icons (24px strokes, currentColor) -------------------------------------------------------- */

const Svg = ({ children }) => (
  <svg
    viewBox="0 0 24 24"
    width="20"
    height="20"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {children}
  </svg>
);
const PauseIcon = () => (
  <Svg>
    <path d="M9 5v14M15 5v14" />
  </Svg>
);
const PlayIcon = () => (
  <Svg>
    <path d="M7 4.5v15l12-7.5z" />
  </Svg>
);
const SparkIcon = () => (
  <Svg>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" />
  </Svg>
);
const CameraIcon = () => (
  <Svg>
    <path d="M4 8h3l2-3h6l2 3h3v11H4z" />
    <circle cx="12" cy="13" r="3.5" />
  </Svg>
);
const CompassIcon = () => (
  <Svg>
    <circle cx="12" cy="12" r="9" />
    <path d="m15.5 8.5-2 5-5 2 2-5z" />
  </Svg>
);
const CheckIcon = () => (
  <Svg>
    <circle cx="12" cy="12" r="9" />
    <path d="m8 12 3 3 5-6" />
  </Svg>
);
const DiceIcon = () => (
  <Svg>
    <rect x="4" y="4" width="16" height="16" rx="3" />
    <circle cx="9" cy="9" r="1" fill="currentColor" />
    <circle cx="15" cy="15" r="1" fill="currentColor" />
    <circle cx="15" cy="9" r="1" fill="currentColor" />
    <circle cx="9" cy="15" r="1" fill="currentColor" />
  </Svg>
);
const GaugeIcon = () => (
  <Svg>
    <path d="M4 17a8 8 0 1 1 16 0" />
    <path d="m12 17 4-5" />
  </Svg>
);
const LayersIcon = () => (
  <Svg>
    <path d="m12 3 9 5-9 5-9-5z" />
    <path d="m3 13 9 5 9-5" />
  </Svg>
);
