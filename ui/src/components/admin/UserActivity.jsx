import { useEffect, useState } from "react";
import * as m from "motion/react-m";
import { errorMessage, fetchUserActivity } from "../../lib/admin.js";
import { SPRING_ENTER, stagger } from "../../lib/motion.js";
import CountUp from "../CountUp.jsx";

/**
 * One student's last twelve weeks, on their own page in the console.
 *
 * The question this is built to answer is "does this person need more room,
 * or an offer" - which is a question about a trend, not a total. So the shape
 * is a weekly series with the empty weeks left in: a student who asked 40
 * questions in July and none since looks identical to a steady one in a
 * headline number, and completely different here.
 *
 * Two charts, never one. Questions and tokens are different scales, and
 * putting them on two y-axes in a single frame is the classic way to invent
 * a correlation that is not there.
 *
 * Colour carries which mode a question was asked in, so it is doing identity
 * work: four fixed slots, assigned in order and never cycled. Light mode's
 * aqua and yellow sit under 3:1 against the surface, so identity never rests
 * on colour alone - the legend carries each mode's total in text, and the
 * table underneath holds every number the bars encode.
 */

const MODES = [
  { key: "guided", label: "Mode guidé", varName: "--viz-1" },
  { key: "full", label: "Solution complète", varName: "--viz-2" },
  { key: "check", label: "Vérifier ma réponse", varName: "--viz-3" },
  { key: "practice", label: "Exercice similaire", varName: "--viz-4" },
];

const nf = new Intl.NumberFormat("fr-FR");

const HALF = 4; // weeks per half when comparing recent activity to before it

/**
 * The numbers, read out loud.
 *
 * The charts below answer "what happened"; this answers "so what", which is
 * the question the console is actually opened with. It is arithmetic on the
 * series and nothing more - no model, no score - so it says what it measured
 * and stops there. Three separate readings rather than one verdict, because
 * they are independent: a student can be busy and still only ever take
 * solutions, and that is exactly the case worth spotting.
 *
 * `tone` only ever marks something as worth a look, never as good or bad:
 * a quiet student may have finished the chapter.
 */
function read(weeks, totals) {
  const sum = (list, key = "questions") => list.reduce((n, w) => n + w[key], 0);
  const now = sum(weeks.slice(-HALF));
  const asked = sum(weeks);
  // The direction is taken across the whole period, not from the last four
  // weeks against the four before them. A student who climbed from three
  // questions a week to twenty-five did so gradually, and block-against-block
  // that reads as flat - it was 71 against 64 on the first account this ran
  // on, while the two halves were 109 against 45. The tile's delta still
  // compares the recent blocks, which is a different and shorter question:
  // momentum now, rather than where the term went.
  const half = Math.floor(weeks.length / 2);
  const early = sum(weeks.slice(0, half));
  const late = sum(weeks.slice(-half));

  if (!asked) {
    return [{ tone: "cold", text: "Aucune question sur les douze semaines." }];
  }

  const out = [];

  // How long since the last question, counted from the end of the series.
  let silent = 0;
  for (let i = weeks.length - 1; i >= 0 && weeks[i].questions === 0; i -= 1) silent += 1;

  if (silent >= 3) {
    out.push({
      tone: "cold",
      text: `Silencieux depuis ${silent} semaines.`,
    });
  } else if (early > 0 && late >= early * 1.4) {
    out.push({
      tone: "up",
      text: `En progression : ${nf.format(late)} questions sur les 6 dernières semaines contre ${nf.format(early)} les 6 premières.`,
    });
  } else if (early > 0 && late <= early * 0.6) {
    out.push({
      tone: "down",
      text: `En retrait : ${nf.format(late)} questions sur les 6 dernières semaines contre ${nf.format(early)} les 6 premières.`,
    });
  } else {
    out.push({
      tone: "flat",
      text: `Rythme régulier : ${nf.format(now)} questions ces 4 semaines.`,
    });
  }

  // What they do with Fahem, which is a different question from how much.
  const full = sum(weeks, "full");
  const guided = sum(weeks, "guided");
  if (full / asked >= 0.6) {
    out.push({
      tone: "watch",
      text: `Demande surtout la solution complète (${Math.round((full / asked) * 100)} % de ses questions).`,
    });
  } else if (guided / asked >= 0.5) {
    out.push({
      tone: "good",
      text: `Travaille surtout en mode guidé (${Math.round((guided / asked) * 100)} % de ses questions).`,
    });
  }

  // Volume, said as a fact rather than as a recommendation - what counts as
  // "a lot" depends on limits only you know.
  if (now >= 40) {
    out.push({
      tone: "watch",
      text: `Usage soutenu : ${nf.format(Math.round(now / HALF))} questions par semaine en moyenne sur le dernier mois.`,
    });
  }

  if (totals.active_days >= 1 && asked / totals.active_days >= 15) {
    out.push({
      tone: "watch",
      text: `Sessions denses : environ ${Math.round(asked / totals.active_days)} questions par jour actif.`,
    });
  }

  return out;
}

/** "8 sept." - short enough to sit under a narrow bar. */
function weekLabel(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  return d.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

/**
 * The twelve weekly counts as one line, drawn on arrival.
 *
 * A shape, not a chart: no axis, no labels, nothing to read a value off. It
 * is there so the headline number carries its own recent history instead of
 * being a figure with no past. The real numbers are in the chart below and in
 * its table, so this is decorative in the strict sense and hidden from
 * assistive tech.
 *
 * Drawn with Motion's pathLength (SVG animation docs) rather than by hand
 * with stroke-dasharray: it is one 0-1 value, and MotionConfig's
 * reducedMotion="user" in AdminLayout turns it off with everything else.
 */
function Spark({ points }) {
  const W = 96;
  const H = 28;
  const peak = Math.max(1, ...points);
  const step = W / Math.max(1, points.length - 1);
  // A cubic through the midpoints: smooth without overshooting past a value,
  // which a spline through the points themselves would do.
  const xy = points.map((p, i) => [i * step, H - (p / peak) * (H - 3) - 1.5]);
  let d = `M ${xy[0][0]} ${xy[0][1]}`;
  for (let i = 0; i < xy.length - 1; i += 1) {
    const [x1, y1] = xy[i];
    const [x2, y2] = xy[i + 1];
    const mid = (x1 + x2) / 2;
    d += ` C ${mid},${y1} ${mid},${y2} ${x2},${y2}`;
  }

  return (
    <svg className="ua-spark" viewBox={`0 0 ${W} ${H}`} aria-hidden="true" focusable="false">
      <m.path
        d={d}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.9, ease: "easeOut", delay: 0.15 }}
      />
    </svg>
  );
}

/**
 * ↑ 62 % — the arrow carries the direction, so colour never has to.
 *
 * Nothing under 10 % is shown. Week-to-week counts wobble, and an arrow on a
 * 3 % move claims a direction the data has not got - it would also sit
 * directly under a reading that calls the same student regular, and the two
 * must not contradict each other.
 */
const NOISE = 10;

function Delta({ now, before }) {
  if (!before) return null;
  const pct = Math.round(((now - before) / before) * 100);
  if (Math.abs(pct) < NOISE) return null;
  const up = pct > 0;
  return (
    <span className={`ua-delta${up ? " is-up" : " is-down"}`}>
      <span aria-hidden="true">{up ? "↑" : "↓"}</span>
      {Math.abs(pct)} %
      <span className="sr-only">
        {up ? "en hausse" : "en baisse"} par rapport aux 4 semaines précédentes
      </span>
    </span>
  );
}

function Tiles({ totals, exercises, weeks }) {
  const sum = (list) => list.reduce((n, w) => n + w.questions, 0);
  const items = [
    {
      label: "Questions posées",
      value: totals.questions,
      // Only this one has a series behind it, so only this one gets a shape
      // and a delta. Putting a sparkline on a number with no history would
      // be decoration pretending to be information.
      spark: weeks.map((w) => w.questions),
      now: sum(weeks.slice(-HALF)),
      before: sum(weeks.slice(-HALF * 2, -HALF)),
    },
    { label: "Jours actifs", value: totals.active_days },
    { label: "Discussions", value: totals.discussions },
    { label: "Exercices réussis", value: exercises.done },
  ];
  return (
    <dl className="ua-tiles">
      {items.map((it) => (
        <div className="ua-tile" key={it.label}>
          <dt>{it.label}</dt>
          <dd>
            <CountUp value={it.value} />
            {it.before !== undefined && <Delta now={it.now} before={it.before} />}
          </dd>
          {it.spark && it.value > 0 && <Spark points={it.spark} />}
        </div>
      ))}
    </dl>
  );
}

/**
 * The weekly bars. One stacked column per week, each segment a mode.
 *
 * Heights are percentages of the busiest week, so the shape is comparable
 * across the row without an axis competing with it; the exact numbers live in
 * the tooltip and the table.
 */
/**
 * A scale whose ticks are numbers a person would say out loud: the smallest
 * step from 1 / 2 / 5 / 10 / … that covers the peak in four bands or fewer.
 * 25 becomes 0-10-20-30, 7 becomes 0-2-4-6-8.
 */
function scaleFor(peak) {
  const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000];
  const step = steps.find((s) => Math.ceil(peak / s) <= 4) ?? steps[steps.length - 1];
  const max = Math.max(step, Math.ceil(peak / step) * step);
  const ticks = [];
  for (let v = 0; v <= max; v += step) ticks.push(v);
  return { max, ticks };
}

function Bars({ weeks }) {
  const peak = Math.max(1, ...weeks.map((w) => w.questions));
  const { max, ticks } = scaleFor(peak);
  return (
    <div className="ua-plot">
      {/* Hairline, solid, one step off the surface, and behind the data.
          Without them every value had to be hovered for to be read at all. */}
      <div className="ua-grid" aria-hidden="true">
        {ticks.map((t) => (
          <span key={t} className="ua-gridline" style={{ bottom: `${(t / max) * 100}%` }}>
            <b>{nf.format(t)}</b>
          </span>
        ))}
      </div>
      <m.div
        className="ua-chart"
        role="img"
        aria-label="Questions par semaine, par mode"
        variants={stagger(0.035)}
        initial="hidden"
        animate="show"
      >
      {weeks.map((w) => (
        <div className="ua-col" key={w.start}>
          {/* Each column grows from the baseline in turn. scaleY rather than
              height so it is a compositor transform, and the origin is the
              axis, so they rise out of it instead of unfolding in place.
              MotionConfig reducedMotion="user" in AdminLayout drops it. */}
          <m.div
            className="ua-stack"
            style={{ height: `${(w.questions / max) * 100}%`, originY: 1 }}
            variants={{
              hidden: { scaleY: 0, opacity: 0 },
              show: { scaleY: 1, opacity: 1, transition: SPRING_ENTER },
            }}
          >
            {MODES.map(({ key, varName }) =>
              w[key] > 0 ? (
                <span
                  key={key}
                  className="ua-seg"
                  style={{
                    flexGrow: w[key],
                    background: `var(${varName})`,
                  }}
                />
              ) : null
            )}
          </m.div>
          {/* The whole column is the hit target, not the bar: an empty week
              has no bar to point at and still has something to say. */}
          <span className="ua-hit" tabIndex={0}>
            <span className="ua-tip" role="tooltip">
              <b>Semaine du {weekLabel(w.start)}</b>
              {w.questions === 0 ? (
                <i>aucune question</i>
              ) : (
                // Not `m`: that is the Motion namespace in this file.
                MODES.filter((mode) => w[mode.key] > 0).map((mode) => (
                  <i key={mode.key}>
                    {mode.label} : {nf.format(w[mode.key])}
                  </i>
                ))
              )}
              {w.tokens > 0 && <i>{nf.format(w.tokens)} jetons</i>}
            </span>
          </span>
        </div>
        ))}
      </m.div>
      {/* Every other week, so the row reads without the labels colliding. */}
      <div className="ua-xaxis" aria-hidden="true">
        {weeks.map((w, i) => (
          <span key={w.start}>{i % 2 === 0 ? weekLabel(w.start) : ""}</span>
        ))}
      </div>
    </div>
  );
}

export default function UserActivity({ userId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError("");
    fetchUserActivity(userId, 12)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(errorMessage(e)));
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (error) return <p className="adm-alert">{error}</p>;
  if (!data) return <div className="adm-skel adm-skel-block" aria-hidden="true" />;

  const { weeks, totals, exercises, spend } = data;
  const perMode = Object.fromEntries(
    MODES.map((m) => [m.key, weeks.reduce((n, w) => n + w[m.key], 0)])
  );
  const asked = weeks.some((w) => w.questions > 0);

  return (
    // A plain div, not a labelled <section>: that would be a landmark, and
    // the Activité tab already names this region. Two names for one thing is
    // just more to step through.
    <div className="ua">
      {/* The reading first, the evidence under it. Plain arithmetic on the
          series below, labelled as such - it points at what to look at, it
          does not decide anything. */}
      <ul className="ua-read">
        {read(weeks, totals).map((r) => (
          <li key={r.text} className={`ua-note is-${r.tone}`}>
            <span className="ua-note-dot" aria-hidden="true" />
            {r.text}
          </li>
        ))}
      </ul>

      <Tiles totals={totals} exercises={exercises} weeks={weeks} />

      <h3 className="ua-h">Questions par semaine</h3>
      {asked ? (
        <>
          <Bars weeks={weeks} />
          {/* The legend carries the totals as text: in light mode two of
              these four hues fall under 3:1 on this surface, so the numbers
              have to be readable without telling the colours apart. */}
          <ul className="ua-legend">
            {MODES.map(({ key, label, varName }) => (
              <li key={key}>
                <span className="ua-swatch" style={{ background: `var(${varName})` }} />
                {label} <b>{nf.format(perMode[key])}</b>
              </li>
            ))}
          </ul>
          <details className="ua-table">
            <summary>Voir les chiffres</summary>
            <table>
              <thead>
                <tr>
                  <th scope="col">Semaine</th>
                  {MODES.map((m) => (
                    <th scope="col" key={m.key}>
                      {m.label}
                    </th>
                  ))}
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((w) => (
                  <tr key={w.start}>
                    <th scope="row">{weekLabel(w.start)}</th>
                    {MODES.map((m) => (
                      <td key={m.key}>{nf.format(w[m.key])}</td>
                    ))}
                    <td>{nf.format(w.questions)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      ) : (
        <p className="adm-muted">
          Ce compte n'a posé aucune question ces douze dernières semaines.
        </p>
      )}

      {/* With spend to show this is a section; with none it is a footnote.
          A heading over "there is nothing yet" is an orphan, and drawing an
          empty chart instead would read as "this student costs nothing",
          which is a different claim from "not measured yet". */}
      {spend.since ? (
        <div>
          <h3 className="ua-h">Jetons consommés</h3>
          <p className="ua-spend">
            <b>{nf.format(spend.tokens)}</b> jetons sur {nf.format(spend.calls)}{" "}
            appels, depuis le {new Date(spend.since).toLocaleDateString("fr-FR")}.
          </p>
        </div>
      ) : (
        <p className="ua-footnote">
          Jetons : le compteur par élève vient d'être mis en place, rien n'est
          encore attribué à ce compte.
        </p>
      )}
    </div>
  );
}
