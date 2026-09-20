import { useEffect, useState } from "react";
import { errorMessage, fetchUserActivity } from "../../lib/admin.js";

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

/** "8 sept." - short enough to sit under a narrow bar. */
function weekLabel(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  return d.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

function Tiles({ totals, exercises }) {
  const items = [
    ["Questions posées", nf.format(totals.questions)],
    ["Jours actifs", nf.format(totals.active_days)],
    ["Discussions", nf.format(totals.discussions)],
    ["Exercices réussis", nf.format(exercises.done)],
  ];
  return (
    <dl className="ua-tiles">
      {items.map(([label, value]) => (
        <div className="ua-tile" key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
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
function Bars({ weeks }) {
  const peak = Math.max(1, ...weeks.map((w) => w.questions));
  return (
    <div className="ua-chart" role="img" aria-label="Questions par semaine, par mode">
      {weeks.map((w) => (
        <div className="ua-col" key={w.start}>
          <div className="ua-stack" style={{ height: `${(w.questions / peak) * 100}%` }}>
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
          </div>
          {/* The whole column is the hit target, not the bar: an empty week
              has no bar to point at and still has something to say. */}
          <span className="ua-hit" tabIndex={0}>
            <span className="ua-tip" role="tooltip">
              <b>Semaine du {weekLabel(w.start)}</b>
              {w.questions === 0 ? (
                <i>aucune question</i>
              ) : (
                MODES.filter((m) => w[m.key] > 0).map((m) => (
                  <i key={m.key}>
                    {m.label} : {nf.format(w[m.key])}
                  </i>
                ))
              )}
              {w.tokens > 0 && <i>{nf.format(w.tokens)} jetons</i>}
            </span>
          </span>
        </div>
      ))}
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
    <section className="ua" aria-label="Activité de ce compte">
      <Tiles totals={totals} exercises={exercises} />

      <h3 className="ua-h">Questions par semaine</h3>
      {asked ? (
        <>
          <Bars weeks={weeks} />
          <div className="ua-axis" aria-hidden="true">
            <span>{weekLabel(weeks[0].start)}</span>
            <span>{weekLabel(weeks[weeks.length - 1].start)}</span>
          </div>
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

      <h3 className="ua-h">Jetons consommés</h3>
      {spend.since ? (
        <p className="ua-spend">
          <b>{nf.format(spend.tokens)}</b> jetons sur {nf.format(spend.calls)} appels,
          depuis le {new Date(spend.since).toLocaleDateString("fr-FR")}.
        </p>
      ) : (
        // Said plainly rather than drawn as an empty chart: nothing has been
        // measured yet, and a flat line at zero would read as "this student
        // costs nothing", which is a different claim.
        <p className="adm-muted">
          Le compteur par élève vient d'être mis en place : rien n'est encore
          attribué à ce compte. Les chiffres se rempliront à partir de ses
          prochaines questions.
        </p>
      )}
    </section>
  );
}
