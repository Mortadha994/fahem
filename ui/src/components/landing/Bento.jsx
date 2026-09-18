import * as m from "motion/react-m";

/**
 * What Fahem does, shown rather than described: every tile carries a small,
 * working piece of the interface (the step rail, the verdict, the generated
 * exercise, the terminal, the progress ring), so a visitor reads the product
 * instead of a feature list.
 *
 * Sizes are deliberate - two wide tiles carry the two ideas that matter most
 * (guided first, then correcting the student's own work).
 */

const reveal = {
  hidden: { opacity: 0, y: 26 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", visualDuration: 0.6, bounce: 0.2 },
  },
};

function Tile({ className = "", kicker, title, body, children }) {
  return (
    <m.article className={`fx-tile ${className}`} variants={reveal}>
      <div className="fx-tile-text">
        <p className="fx-tile-kicker">{kicker}</p>
        <h3 className="fx-tile-title">{title}</h3>
        <p className="fx-tile-body">{body}</p>
      </div>
      {children && <div className="fx-tile-visual">{children}</div>}
    </m.article>
  );
}

export default function Bento({ photos }) {
  return (
    <m.div
      className="fx-bento"
      variants={{ show: { transition: { staggerChildren: 0.07 } } }}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.15 }}
    >
      <Tile
        className="fx-tile-wide fx-tile-accent"
        kicker="Mode guidé"
        title="Il t'aide à trouver, pas seulement à copier"
        body="Comprendre l'énoncé, un indice, un squelette à compléter — et la solution seulement quand tu la demandes."
      >
        <ol className="fx-mini-rail fx-mini-rail-lg">
          {["Comprendre", "Indice", "Squelette", "Solution"].map((label, i) => (
            <li
              key={label}
              className={i < 2 ? (i === 1 ? "is-current" : "is-done") : ""}
            >
              <span aria-hidden="true">{i === 0 ? "✓" : i + 1}</span>
              {label}
            </li>
          ))}
        </ol>
        <p className="fx-mini-hint">
          « Pense à <b>div</b> et <b>mod</b> pour séparer les chiffres. Quelle
          instruction écrirais-tu ? »
        </p>
      </Tile>

      <Tile
        className="fx-tile-wide"
        kicker="Vérifier ma réponse"
        title="Tu écris ta solution, il la corrige"
        body="Ligne par ligne : ce qui est juste, ce qui coûte des points, et la règle derrière chaque correction."
      >
        <div className="fx-mini-verdict">
          <span aria-hidden="true">💪</span>
          <div>
            <b>Presque !</b>
            <span>
              <code>S = A + B</code> → en algorithme, l'affectation s'écrit{" "}
              <code>←</code>
            </span>
          </div>
        </div>
        <ul className="fx-mini-checks">
          <li>
            <span aria-hidden="true">✓</span> La lecture des deux entiers est juste
          </li>
          <li>
            <span aria-hidden="true">✓</span> Test sur un exemple : 7 et 5 → 12
          </li>
          <li>
            <span aria-hidden="true">!</span> Il manque le tableau de déclaration
          </li>
        </ul>
      </Tile>

      <Tile
        kicker="Exécuter le Python"
        title="Lance le programme, vois le résultat"
        body="Le Python de la solution tourne dans ton navigateur."
      >
        <div className="fx-mini-term">
          <div className="fx-term-bar" aria-hidden="true">
            <i />
            <i />
            <i />
            <span>Terminé ✓</span>
          </div>
          <pre>{"Donner A : 7\nDonner B : 5\nLa somme est 12"}</pre>
        </div>
      </Tile>

      <Tile
        kicker="Exercice similaire"
        title="Un autre, à ta difficulté"
        body="Plus facile, pareil ou plus dur — sur la même leçon."
      >
        <div className="fx-mini-levels">
          <span className="is-easy">🌱 Plus facile</span>
          <span className="is-same">⚖️ Même niveau</span>
          <span className="is-hard">🔥 Plus difficile</span>
        </div>
      </Tile>

      <Tile
        kicker="Ma progression"
        title="Tu vois ce qui te reste"
        body="Un exercice réussi seul est compté. Le prochain t'attend."
      >
        <div
          className="fx-mini-ring"
          role="img"
          aria-label="7 exercices réussis sur 19"
        >
          <svg viewBox="0 0 100 100" aria-hidden="true">
            <circle className="fx-ring-track" cx="50" cy="50" r="42" />
            <m.circle
              className="fx-ring-fill"
              cx="50"
              cy="50"
              r="42"
              strokeDasharray={264}
              initial={{ strokeDashoffset: 264 }}
              whileInView={{ strokeDashoffset: 264 * (1 - 7 / 19) }}
              viewport={{ once: true }}
              transition={{ duration: 1, delay: 0.2 }}
            />
          </svg>
          <b>
            7<span>/19</span>
          </b>
        </div>
      </Tile>

      {photos && (
        <Tile
          kicker="Photo ou PDF"
          title="Prends ton cahier en photo"
          body="Il lit l'énoncé et le résout comme si tu l'avais tapé."
        >
          <div className="fx-mini-photo" aria-hidden="true">
            <span className="fx-mini-photo-frame">
              <span className="fx-mini-photo-line" />
              <span className="fx-mini-photo-line" />
              <span className="fx-mini-photo-line is-short" />
            </span>
            <span className="fx-mini-photo-go">→</span>
            <span className="fx-mini-photo-chip">Énoncé lu ✓</span>
          </div>
        </Tile>
      )}
    </m.div>
  );
}
