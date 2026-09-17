import { useCallback, useEffect, useRef, useState } from "react";
import * as m from "motion/react-m";
import { fetchMonitoring, relativeTime, UnauthorizedError } from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { SPRING_ENTER, rise, stagger } from "../../lib/motion.js";
import CountUp from "../../components/CountUp.jsx";
import AiControls from "../../components/admin/AiControls.jsx";
import AdminTabs from "../../components/admin/AdminTabs.jsx";
import { IconActivity, IconClock, IconSliders } from "../../components/admin/icons.jsx";

/**
 * Surveillance IA: how hard Fahem is leaning on Groq, right now and over 24h.
 *
 * Everything comes from GET /admin/monitoring, polled every REFRESH_MS while
 * the tab is visible (a hidden tab stops asking). The "temperature" is the
 * server's: the most loaded of tokens per minute, tokens per day and the
 * queue - or saturated outright when Groq refused a call in the last five
 * minutes. The page draws it; it does not re-derive it.
 *
 * Layout borrowed from dashboard patterns (radial progress card, usage meters
 * against a plan limit, KPI cards over a small bar chart), rebuilt in the
 * console's own CSS - the console has no Tailwind. Motion draws the gauge's
 * ring with pathLength and grows the bars with springs; reduced motion is
 * handled by the MotionProvider.
 */

const REFRESH_MS = 10_000;

/* Three tabs instead of one long page: what is happening now, what can be
   changed, and what happened over the day. The tab is in the URL
   (?onglet=), so the sidebar's AI status card opens the controls directly. */
const TABS = [
  { id: "direct", label: "En direct", Icon: IconActivity },
  { id: "controles", label: "Contrôles", Icon: IconSliders },
  { id: "historique", label: "24 heures", Icon: IconClock },
];

const STATES = {
  cool: { label: "Froid", hint: "Large marge" },
  warm: { label: "Tiède", hint: "Charge modérée" },
  hot: { label: "Chaud", hint: "Proche des limites" },
  saturated: { label: "Saturé", hint: "Groq refuse des appels" },
};

const KINDS = {
  gatekeeper: "Tri des messages",
  solve: "Résolutions",
  transcription: "Lecture photo / PDF",
  default: "Autres",
};

const STATUS = {
  rate_limited: "Limite Groq (429)",
  queue_timeout: "File trop longue",
  error: "Erreur",
};

const nf = new Intl.NumberFormat("fr-FR");
const compact = new Intl.NumberFormat("fr-FR", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const pct = (r) => `${Math.round((r ?? 0) * 100)} %`;
const seconds = (ms) =>
  ms >= 10_000 ? `${Math.round(ms / 1000)} s` : `${(ms / 1000).toFixed(1)} s`;
const clamp01 = (r) => Math.max(0, Math.min(1, r ?? 0));

export default function AdminMonitoring() {
  const { onUnauthorized } = useAuth();
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);
  const [paused, setPaused] = useState(false);
  const [, tick] = useState(0);
  const inFlight = useRef(false);

  const load = useCallback(() => {
    if (inFlight.current) return;
    inFlight.current = true;
    fetchMonitoring()
      .then((d) => {
        setData(d);
        setFailed(false);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
      })
      .finally(() => {
        inFlight.current = false;
      });
  }, [onUnauthorized]);

  useEffect(() => {
    load();
    if (paused) return undefined;
    const id = setInterval(() => {
      if (!document.hidden) load();
      tick((n) => n + 1); // keeps "mis à jour il y a…" honest
    }, REFRESH_MS);
    const onVisible = () => !document.hidden && load();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [load, paused]);

  const saturated = data?.models.filter((mdl) => mdl.state === "saturated") ?? [];

  return (
    <m.div
      className="adm-page"
      variants={stagger(0.06)}
      initial="hidden"
      animate="show"
    >
      <m.header className="adm-head" variants={rise}>
        <div>
          <h1 className="adm-h1">Surveillance IA</h1>
          <p className="adm-sub">
            Charge de Groq, consommation, activité du chat — et les commandes pour agir.
          </p>
        </div>
        <div className="mon-live">
          <span
            className={`mon-pulse${paused ? " is-paused" : ""}`}
            aria-hidden="true"
          />
          <span className="adm-muted adm-small" aria-live="polite">
            {paused
              ? "Actualisation figée"
              : data
                ? `Mis à jour ${relativeTime(data.generated_at)}`
                : "Chargement…"}
          </span>
          {/* Freezes this page's figures only - the AI itself is paused
              from the Contrôles tab. */}
          <button className="adm-btn" onClick={() => setPaused((p) => !p)}>
            {paused ? "Reprendre l'actualisation" : "Figer les chiffres"}
          </button>
        </div>
      </m.header>

      {failed && (
        <p className="adm-alert">
          Impossible de charger la surveillance
          {data ? " — dernières valeurs affichées" : ""}.
        </p>
      )}

      {saturated.map((mdl) => (
        <m.p
          className="adm-callout is-danger mon-banner"
          key={mdl.model}
          variants={rise}
          role="alert"
        >
          {mdl.label} ({mdl.model}) est saturé
          {mdl.day_ratio >= 1
            ? " : la limite de tokens par jour est atteinte, les élèves reçoivent « service très sollicité » jusqu'à ce qu'elle se libère."
            : " : Groq a refusé des appels ces 5 dernières minutes."}
        </m.p>
      ))}

      <AdminTabs label="Sections de la surveillance" tabs={TABS}>
        {(tab) =>
          tab === "controles" ? (
            // See and act in the same place: every control refreshes the
            // figures as soon as it is applied.
            <AiControls onChanged={load} />
          ) : !data ? (
            <div className="mon-skeleton">
              <div className="adm-skel adm-skel-block" aria-hidden="true" />
              <div className="adm-skel adm-skel-block" aria-hidden="true" />
            </div>
          ) : tab === "direct" ? (
            <div className="adm-stack">
              <m.section
                className="mon-models"
                aria-label="Charge des modèles"
                variants={stagger(0.08)}
              >
                {data.models.map((mdl) => (
                  <ModelCard key={mdl.model} model={mdl} />
                ))}
              </m.section>

              <div className="adm-grid-2">
                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Tokens par minute — dernière heure</h2>
                    <span className="adm-muted adm-small">
                      limite {nf.format(data.models[0]?.tpm_limit ?? 0)} / min
                    </span>
                  </header>
                  <MinuteChart
                    minutes={data.minutes}
                    limit={data.models[0]?.tpm_limit ?? 0}
                  />
                </m.section>

                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Activité du chat (24 h)</h2>
                  </header>
                  <dl className="adm-kpis mon-kpis-2">
                    <div className="adm-kpi is-busy">
                      <dt>Élèves actifs</dt>
                      <dd>{data.chat.active_students_24h}</dd>
                    </div>
                    <div className="adm-kpi">
                      <dt>Discussions actives</dt>
                      <dd>{data.chat.active_discussions_24h}</dd>
                    </div>
                    <div className="adm-kpi">
                      <dt>Nouvelles discussions</dt>
                      <dd>{data.chat.new_discussions_24h}</dd>
                    </div>
                    <div className="adm-kpi">
                      <dt>Questions posées</dt>
                      <dd>{data.chat.questions_in_active}</dd>
                    </div>
                  </dl>
                  <p className="adm-muted adm-small">
                    Questions comptées dans les discussions actives ces 24 h.
                  </p>
                </m.section>
              </div>
            </div>
          ) : (
            <div className="adm-stack">
              <KpiRow kpis={data.kpis} />

              <m.section className="adm-panel" variants={rise}>
                <header className="adm-panel-head">
                  <h2 className="adm-h2">Appels Groq — dernières 24 h</h2>
                  <span className="mon-legend adm-small">
                    <i className="mon-dot" /> réussis <i className="mon-dot is-fail" />{" "}
                    échecs
                  </span>
                </header>
                <HourChart hours={data.timeline} />
              </m.section>

              <div className="adm-grid-2">
                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Par type de requête</h2>
                  </header>
                  <KindTable kinds={data.by_kind} />
                </m.section>

                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Échecs récents</h2>
                  </header>
                  <Failures failures={data.failures} />
                </m.section>
              </div>

              <div className="adm-grid-2">
                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Réponses par consigne</h2>
                  </header>
                  <RouteTable routes={data.routes ?? []} />
                </m.section>

                <m.section className="adm-panel" variants={rise}>
                  <header className="adm-panel-head">
                    <h2 className="adm-h2">Avis des élèves — 7 jours</h2>
                  </header>
                  <FeedbackPanel feedback={data.feedback} />
                </m.section>
              </div>

              <m.section className="adm-panel" variants={rise}>
                <header className="adm-panel-head">
                  <h2 className="adm-h2">Apprentissage — 7 jours</h2>
                </header>
                <LearningPanel learning={data.learning} />
              </m.section>
            </div>
          )
        }
      </AdminTabs>
    </m.div>
  );
}

/** One model: the temperature gauge, then the three loads it is made of. */
function ModelCard({ model }) {
  const state = STATES[model.state] ?? STATES.cool;
  const load = clamp01(model.load);
  const q = model.queue;
  const dayUsed =
    model.reported_tpd_used != null
      ? Math.max(model.tokens_24h, model.reported_tpd_used)
      : model.tokens_24h;

  return (
    <m.article className={`adm-panel mon-model is-${model.state}`} variants={rise}>
      <div className="mon-gauge-wrap">
        <Gauge value={load} label={`${state.label}, charge ${pct(model.load)}`} />
        <div className="mon-gauge-center" aria-hidden="true">
          <span className="mon-gauge-pct">{Math.round(model.load * 100)}%</span>
          <span className="mon-gauge-state">{state.label}</span>
        </div>
      </div>

      <div className="mon-model-body">
        <header>
          <h2 className="adm-h2">{model.label}</h2>
          <code className="adm-muted adm-small">{model.model}</code>
          <p className="mon-state-hint">{state.hint}</p>
        </header>

        <Meter
          label="Tokens / minute"
          ratio={model.minute_ratio}
          value={`${nf.format(model.tokens_last_minute)} / ${nf.format(model.tpm_limit)}`}
        />
        {model.tpd_limit > 0 ? (
          <Meter
            label="Tokens / jour"
            ratio={model.day_ratio}
            value={`${compact.format(dayUsed)} / ${compact.format(model.tpd_limit)}`}
            note={
              model.reported_tpd_used != null
                ? `Groq a compté ${nf.format(model.reported_tpd_used)} ${relativeTime(model.reported_at)}`
                : null
            }
          />
        ) : (
          <p className="adm-muted adm-small">
            {compact.format(model.tokens_24h)} tokens sur 24 h (limite journalière
            inconnue)
          </p>
        )}
        {q && (
          <Meter
            label="File d'attente"
            ratio={model.queue_ratio}
            value={`${q.active}/${q.max_concurrent} en cours · ${q.waiting} en attente`}
          />
        )}
      </div>
    </m.article>
  );
}

/** A 270° ring drawn with Motion's pathLength. */
function Gauge({ value, label }) {
  const r = 52;
  const arc = "M 23.2 96.8 A 52 52 0 1 1 96.8 96.8"; // 270°, gap at the bottom
  return (
    <svg className="mon-gauge" viewBox="0 0 120 120" role="img" aria-label={label}>
      <path d={arc} className="mon-gauge-track" pathLength={1} />
      <m.path
        d={arc}
        className="mon-gauge-fill"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: Math.max(value, 0.001) }}
        transition={{ ...SPRING_ENTER, visualDuration: 0.9 }}
      />
      <circle cx="60" cy="60" r={r - 14} className="mon-gauge-core" />
    </svg>
  );
}

function Meter({ label, ratio, value, note }) {
  const r = clamp01(ratio);
  const level = r >= 1 ? "is-full" : r >= 0.8 ? "is-hot" : r >= 0.5 ? "is-warm" : "";
  return (
    <div className={`mon-meter ${level}`}>
      <div className="mon-meter-top">
        <span>{label}</span>
        <span className="mon-meter-value">{value}</span>
      </div>
      <span
        className="mon-meter-track"
        role="img"
        aria-label={`${label} : ${pct(ratio)}`}
      >
        <m.span
          className="mon-meter-fill"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: r }}
          transition={{ ...SPRING_ENTER, visualDuration: 0.7 }}
        />
      </span>
      {note && <span className="adm-muted mon-meter-note">{note}</span>}
    </div>
  );
}

function KpiRow({ kpis }) {
  const failures = kpis.rate_limited + kpis.queue_timeouts + kpis.errors;
  const cards = [
    {
      label: "Appels (24 h)",
      icon: "⇄",
      value: kpis.calls,
      hint: kpis.cancelled
        ? `dont ${kpis.cancelled} abandonnés par l'élève`
        : "tous modèles confondus",
    },
    {
      label: "Tokens (24 h)",
      icon: "◇",
      value: kpis.tokens,
      hint: kpis.calls
        ? `${nf.format(Math.round(kpis.tokens / kpis.calls))} par appel en moyenne`
        : "—",
    },
    {
      label: "Taux de succès",
      icon: "✓",
      value: kpis.success_rate == null ? null : Math.round(kpis.success_rate * 100),
      suffix: " %",
      hint: failures ? `${failures} échec${failures > 1 ? "s" : ""}` : "aucun échec",
      tone: kpis.success_rate != null && kpis.success_rate < 0.95 ? "is-warn" : "",
    },
    {
      label: "Refus Groq (429)",
      icon: "⚠",
      value: kpis.rate_limit_hits,
      hint: `${kpis.rate_limited} arrivé${kpis.rate_limited > 1 ? "s" : ""} jusqu'à l'élève`,
      tone: kpis.rate_limited ? "is-warn" : "",
    },
  ];
  return (
    <m.section
      className="adm-stats"
      aria-label="Indicateurs 24 h"
      variants={stagger(0.06)}
    >
      {cards.map((c, i) => (
        <m.div className={`adm-stat ${c.tone ?? ""}`} key={c.label} variants={rise}>
          <span className="adm-stat-top">
            <span className="adm-stat-label">{c.label}</span>
            <span className="adm-stat-ico" aria-hidden="true">
              {c.icon}
            </span>
          </span>
          <span className="adm-stat-value">
            {c.value == null ? (
              "—"
            ) : (
              <>
                <CountUp value={c.value} delay={0.15 + i * 0.05} aria-hidden="true" />
                {c.suffix}
                <span className="sr-only">
                  {c.value}
                  {c.suffix}
                </span>
              </>
            )}
          </span>
          <span className="adm-stat-hint">{c.hint}</span>
        </m.div>
      ))}
    </m.section>
  );
}

/** 60 one-minute bars, with the per-minute limit as a line. */
function MinuteChart({ minutes, limit }) {
  const peak = Math.max(limit, ...minutes.map((b) => b.tokens), 1);
  const total = minutes.reduce((n, b) => n + b.tokens, 0);
  return (
    <figure
      className="mon-chart"
      aria-label={`${nf.format(total)} tokens sur la dernière heure`}
    >
      <div className="mon-bars">
        {limit > 0 && (
          <span className="mon-limit" style={{ bottom: `${(limit / peak) * 100}%` }}>
            <span>limite</span>
          </span>
        )}
        {minutes.map((b, i) => (
          <m.span
            key={b.at}
            className={`mon-bar${b.tokens > limit && limit ? " is-over" : ""}`}
            title={`${new Date(b.at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })} · ${nf.format(b.tokens)} tokens · ${b.calls} appel${b.calls > 1 ? "s" : ""}`}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: b.tokens / peak }}
            transition={{ ...SPRING_ENTER, delay: i * 0.004 }}
          />
        ))}
      </div>
      <figcaption className="mon-axis">
        <span>−60 min</span>
        <span>−30 min</span>
        <span>maintenant</span>
      </figcaption>
    </figure>
  );
}

/** 24 hourly bars, successes stacked under failures. */
function HourChart({ hours }) {
  const peak = Math.max(...hours.map((h) => h.calls), 1);
  const hourLabel = (iso) =>
    new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit" });
  return (
    <figure className="mon-chart" aria-label="Appels par heure sur 24 heures">
      <div className="mon-bars mon-bars-hours">
        {hours.map((h, i) => (
          <span
            key={h.at}
            className="mon-stack"
            title={`${hourLabel(h.at)} · ${h.calls} appels · ${nf.format(h.tokens)} tokens · ${h.failures} échec${h.failures > 1 ? "s" : ""}`}
          >
            <m.span
              className="mon-stack-fill"
              style={{ height: `${(h.calls / peak) * 100}%` }}
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ ...SPRING_ENTER, delay: i * 0.015 }}
            >
              {h.failures > 0 && (
                <span
                  className="mon-stack-fail"
                  style={{ height: `${(h.failures / h.calls) * 100}%` }}
                />
              )}
            </m.span>
          </span>
        ))}
      </div>
      <figcaption className="mon-axis">
        <span>{hourLabel(hours[0].at)}</span>
        <span>{hourLabel(hours[12].at)}</span>
        <span>{hourLabel(hours[23].at)}</span>
      </figcaption>
    </figure>
  );
}

function KindTable({ kinds }) {
  if (!kinds.length)
    return <p className="adm-empty">Aucun appel ces dernières 24 h.</p>;
  return (
    <div className="adm-table-wrap">
      <table className="adm-table mon-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Appels</th>
            <th>Échecs</th>
            <th>Tokens moy.</th>
            <th>Durée p50 / p95</th>
            <th>Attente p50 / p95</th>
          </tr>
        </thead>
        <tbody>
          {kinds.map((k) => (
            <tr key={k.kind}>
              <td className="adm-strong">{KINDS[k.kind] ?? k.kind}</td>
              <td>{nf.format(k.calls)}</td>
              <td>
                {k.failures ? (
                  <span className="adm-tag adm-tag-danger">{k.failures}</span>
                ) : (
                  "0"
                )}
              </td>
              <td>{nf.format(k.avg_tokens)}</td>
              <td>
                {seconds(k.latency_p50_ms)} / {seconds(k.latency_p95_ms)}
              </td>
              <td>
                {seconds(k.wait_p50_ms)} / {seconds(k.wait_p95_ms)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const ROUTES = {
  PROBLEM: "Énoncé complet",
  QUESTION: "Question de cours",
  CODE: "Code à corriger",
  FOLLOW_UP: "Suite d'échange",
  GUIDED: "Mode guidé",
  CHECK: "Vérifier ma réponse",
  PRACTICE: "Exercice similaire",
};

const FINDINGS = {
  operator: "Opérateur Python en algorithme (//, %, !=…)",
  assignment: "Affectation écrite avec =",
  lire: "Type dans Lire",
  declaration: "Tableau de déclaration absent",
};

/** Mode guidé and Vérifier ma réponse over 7 days. */
function LearningPanel({ learning }) {
  if (!learning || learning.guided_answers + learning.checks === 0)
    return (
      <p className="adm-empty">Ni mode guidé ni vérification ces 7 derniers jours.</p>
    );
  const verdictTotal =
    learning.verdicts.correct + learning.verdicts.presque + learning.verdicts.a_revoir;
  return (
    <div className="adm-stack">
      <div className="mon-learning-row">
        <div>
          <p className="adm-strong">
            Mode guidé : {nf.format(learning.guided_answers)} réponses
          </p>
          <p className="adm-muted adm-small">
            Compréhension {learning.guided_by_step["1"]} · Indice{" "}
            {learning.guided_by_step["2"]} · Squelette {learning.guided_by_step["3"]} ·
            Solution {learning.guided_by_step["4"]}
          </p>
        </div>
        {learning.guided_leaks > 0 ? (
          <span className="adm-tag adm-tag-warn">
            {learning.guided_leaks} solution{learning.guided_leaks > 1 ? "s" : ""}{" "}
            donnée
            {learning.guided_leaks > 1 ? "s" : ""} trop tôt
          </span>
        ) : (
          <span className="adm-tag">aucune fuite</span>
        )}
      </div>
      <div className="mon-learning-row">
        <div>
          <p className="adm-strong">Vérifications : {nf.format(learning.checks)}</p>
          <p className="adm-muted adm-small">
            ✓ Correct {learning.verdicts.correct} · ≈ Presque{" "}
            {learning.verdicts.presque} · ✗ À revoir {learning.verdicts.a_revoir}
            {learning.verdicts.unknown
              ? ` · sans verdict ${learning.verdicts.unknown}`
              : ""}
          </p>
        </div>
      </div>
      {verdictTotal > 0 && (
        <Meter
          label="Solutions à revoir"
          ratio={learning.verdicts.a_revoir / verdictTotal}
          value={`${Math.round((learning.verdicts.a_revoir / verdictTotal) * 100)} %`}
        />
      )}
      {learning.top_findings.length > 0 && (
        <div>
          <p className="adm-strong adm-small">
            Erreurs de notation les plus fréquentes
          </p>
          <ul className="adm-list">
            {learning.top_findings.map((f) => (
              <li key={f.kind} className="mon-failure">
                <span className="mon-failure-main">{FINDINGS[f.kind] ?? f.kind}</span>
                <span className="adm-tag">{f.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/** Which prompt answered, and how much of it was the discussion's memory. */
function RouteTable({ routes }) {
  if (!routes.length)
    return <p className="adm-empty">Aucune réponse ces dernières 24 h.</p>;
  return (
    <div className="adm-table-wrap">
      <table className="adm-table mon-table">
        <thead>
          <tr>
            <th>Consigne</th>
            <th>Réponses</th>
            <th>Avec mémoire</th>
            <th>Tokens envoyés moy.</th>
            <th>Mémoire moy.</th>
          </tr>
        </thead>
        <tbody>
          {routes.map((r) => (
            <tr key={r.route}>
              <td className="adm-strong">{ROUTES[r.route] ?? r.route}</td>
              <td>{nf.format(r.calls)}</td>
              <td>
                {nf.format(r.with_memory)}
                {r.calls ? (
                  <span className="adm-muted adm-small">
                    {" "}
                    ({Math.round((r.with_memory / r.calls) * 100)} %)
                  </span>
                ) : null}
              </td>
              <td>{nf.format(r.avg_prompt_tokens)}</td>
              <td>
                {r.avg_memory_chars ? `${nf.format(r.avg_memory_chars)} car.` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** 👍 / 👎 over 7 days, and the answers students marked as wrong or unclear. */
function FeedbackPanel({ feedback }) {
  if (!feedback || feedback.up + feedback.down === 0)
    return <p className="adm-empty">Aucun avis ces 7 derniers jours.</p>;
  const total = feedback.up + feedback.down;
  // The bar warms up as 👎 grow, like the other loads on this page.
  const share = Math.round((feedback.down / total) * 100);
  return (
    <div className="adm-stack">
      <Meter
        label="Réponses jugées fausses ou pas claires"
        ratio={feedback.down / total}
        value={`${share} %`}
        note={`${nf.format(feedback.up)} 👍 · ${nf.format(feedback.down)} 👎`}
      />
      {feedback.recent_down.length > 0 ? (
        <m.ul className="adm-list mon-failures" variants={stagger(0.04)}>
          {feedback.recent_down.map((d, i) => (
            <m.li key={`${d.at}-${i}`} className="mon-failure" variants={rise}>
              <span className="adm-tag adm-tag-warn">👎</span>
              <span className="mon-failure-main">
                <span className="adm-strong">{d.title || "Discussion sans titre"}</span>
                <span className="adm-muted adm-small">
                  {d.chapitre ? `Chapitre ${d.chapitre}` : ""}
                  {d.comment ? ` · « ${d.comment} »` : ""}
                </span>
              </span>
              <span className="adm-muted adm-list-when">{relativeTime(d.at)}</span>
            </m.li>
          ))}
        </m.ul>
      ) : (
        <p className="adm-callout is-ok">Aucune réponse jugée fausse.</p>
      )}
    </div>
  );
}

function Failures({ failures }) {
  if (!failures.length)
    return <p className="adm-callout is-ok">Aucun échec ces dernières 24 h.</p>;
  return (
    <m.ul className="adm-list mon-failures" variants={stagger(0.04)}>
      {failures.map((f, i) => (
        <m.li key={`${f.at}-${i}`} className="mon-failure" variants={rise}>
          <span
            className={`adm-tag ${f.status === "error" ? "adm-tag-danger" : "adm-tag-warn"}`}
          >
            {STATUS[f.status] ?? f.status}
          </span>
          <span className="mon-failure-main">
            <span className="adm-strong">{KINDS[f.kind] ?? f.kind}</span>
            <span className="adm-muted adm-small">
              {f.detail ?? "—"}
              {f.rate_limit_hits > 1 ? ` · ${f.rate_limit_hits} refus` : ""}
              {f.queue_wait_ms ? ` · ${seconds(f.queue_wait_ms)} en file` : ""}
            </span>
          </span>
          <span className="adm-muted adm-list-when">{relativeTime(f.at)}</span>
        </m.li>
      ))}
    </m.ul>
  );
}
