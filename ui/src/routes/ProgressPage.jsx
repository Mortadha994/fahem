import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as m from "motion/react-m";
import { SPRING_ENTER, rise, stagger } from "../lib/motion.js";
import { UnauthorizedError } from "../lib/chapters.js";
import { MISTAKES, VERDICT_LABELS, fetchProgress } from "../lib/progressApi.js";
import { exerciseTitle } from "../lib/exercises.js";
import { useAuth } from "../lib/authContext.js";
import { useChatSessions } from "../lib/chatSessionsContext.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import Skeleton from "../components/ui/Skeleton.jsx";
import CountUp from "../components/CountUp.jsx";
import { Burst } from "../components/learning/Learning.jsx";

/**
 * Ma progression: where the student is in each chapter (réussis by themselves,
 * solution vue, commencés), what to do next, the solutions they had checked,
 * and the notation mistakes that keep coming back - with the rule to remember.
 * Everything comes from GET /progress, which derives it from their discussions.
 */
export default function ProgressPage() {
  const { onUnauthorized } = useAuth();
  const { setActiveId } = useChatSessions();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchProgress()
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  const openDiscussion = (sessionId) => {
    setActiveId(sessionId);
    navigate("/chat");
  };
  const startExercise = (chapterId, question) =>
    navigate("/chat", { state: { problem: question, chapitre: chapterId } });

  return (
    <main className="page">
      <header className="page-head">
        <h1>Ma progression</h1>
        <p className="page-muted">
          Un exercice est <strong>réussi</strong> quand « Vérifier ma réponse » dit
          Correct : tu l'as résolu toi-même.
        </p>
      </header>

      {failed && (
        <Alert className="page-alert">
          Impossible de charger ta progression. Recharge la page pour réessayer.
        </Alert>
      )}
      {!data && !failed && (
        <div className="prog-grid" aria-hidden="true">
          <Skeleton height="12rem" radius="lg" />
          <Skeleton height="12rem" radius="lg" />
        </div>
      )}

      {data && (
        <m.div
          className="prog"
          variants={stagger(0.08)}
          initial="hidden"
          animate="show"
        >
          <Summary chapters={data.chapters} />

          <section className="prog-chapters" aria-label="Chapitres">
            {data.chapters.length === 0 && (
              <EmptyState size="sm">
                Aucun chapitre disponible pour l'instant.
              </EmptyState>
            )}
            {data.chapters.map((c) => (
              <m.article
                key={c.id}
                className="prog-card surface"
                variants={rise}
                whileHover={{ y: -3 }}
              >
                <header className="prog-card-head">
                  <div>
                    <p className="prog-card-meta">Chapitre {c.id}</p>
                    <h2 className="prog-card-title">
                      <Link to={`/chapitre/${c.id}`}>{c.title}</Link>
                    </h2>
                  </div>
                  <p className="prog-score">
                    <CountUp className="prog-score-num" value={c.done} />
                    <span className="prog-score-total"> / {c.total} réussis</span>
                  </p>
                </header>

                <StackedBar chapter={c} />
                <p className="prog-legend">
                  <span className="prog-dot is-done" /> Réussis {c.done}
                  <span className="prog-dot is-seen" /> Solution vue {c.solution_seen}
                  <span className="prog-dot is-started" /> Commencés{" "}
                  {c.started - c.done - c.solution_seen}
                </p>

                {c.next_exercise ? (
                  <div className="prog-next">
                    <p className="prog-next-label">
                      {c.next_exercise.status ? "À terminer" : "Prochain exercice"}
                    </p>
                    <p className="prog-next-title">
                      {exerciseTitle(c.next_exercise.question)}
                    </p>
                    <div className="prog-next-actions">
                      {c.next_exercise.session_id ? (
                        <button
                          type="button"
                          className="guided-btn is-primary"
                          onClick={() => openDiscussion(c.next_exercise.session_id)}
                        >
                          Reprendre →
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="guided-btn is-primary"
                          onClick={() => startExercise(c.id, c.next_exercise.question)}
                        >
                          Commencer →
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  c.total > 0 && (
                    <p className="prog-all-done">
                      <span className="prog-trophy">
                        🏆
                        <Burst count={16} spread={80} />
                      </span>
                      Tous les exercices de ce chapitre sont réussis !
                    </p>
                  )
                )}
              </m.article>
            ))}
          </section>

          <div className="prog-side">
            <m.section
              className="prog-card surface"
              variants={rise}
              aria-labelledby="checks-title"
            >
              <h2 id="checks-title" className="prog-card-title">
                Mes solutions vérifiées
              </h2>
              {data.recent_checks.length === 0 ? (
                <p className="page-muted">
                  Écris ta propre solution et appuie sur « Vérifier ma réponse » : Fahem
                  la corrige ligne par ligne.
                </p>
              ) : (
                <ul className="prog-checks">
                  {data.recent_checks.map((r) => {
                    const v = VERDICT_LABELS[r.verdict];
                    return (
                      <li key={r.session_id}>
                        <button
                          type="button"
                          className="prog-check"
                          onClick={() => openDiscussion(r.session_id)}
                        >
                          <span className="prog-check-title">{r.title}</span>
                          <span className="prog-check-meta">
                            Chapitre {r.chapitre}
                            {r.checks > 1 ? ` · ${r.checks} essais` : ""}
                          </span>
                          {v ? (
                            <Badge tone={v.tone}>
                              {v.icon} {v.label}
                            </Badge>
                          ) : (
                            <Badge tone="neutral">Vérifié</Badge>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </m.section>

            <m.section
              className="prog-card surface"
              variants={rise}
              aria-labelledby="mistakes-title"
            >
              <h2 id="mistakes-title" className="prog-card-title">
                Mes erreurs fréquentes
              </h2>
              {data.mistakes.length === 0 ? (
                <p className="page-muted">
                  Aucune erreur de notation relevée dans tes solutions. Continue !
                </p>
              ) : (
                <ul className="prog-mistakes">
                  {data.mistakes.map((mk) => {
                    const info = MISTAKES[mk.kind];
                    return (
                      <li key={mk.kind} className="prog-mistake">
                        <span className="prog-mistake-head">
                          <span className="prog-mistake-label">
                            {info?.label ?? mk.kind}
                          </span>
                          <span className="prog-mistake-count">×{mk.count}</span>
                        </span>
                        {info && <span className="prog-mistake-tip">{info.tip}</span>}
                      </li>
                    );
                  })}
                </ul>
              )}
            </m.section>
          </div>
        </m.div>
      )}
    </main>
  );
}

const MOODS = [
  {
    upTo: 0,
    emoji: "🚀",
    title: "C'est parti !",
    sub: "Choisis un exercice et vérifie ta solution : ta première réussite t'attend.",
  },
  {
    upTo: 0.25,
    emoji: "🌱",
    title: "Beau début !",
    sub: "Chaque exercice réussi seul compte. Continue sur ta lancée.",
  },
  {
    upTo: 0.5,
    emoji: "⚡",
    title: "Tu avances bien !",
    sub: "Tu as déjà fait une belle partie du programme.",
  },
  {
    upTo: 0.99,
    emoji: "🔥",
    title: "Plus que quelques-uns !",
    sub: "La ligne d'arrivée est en vue.",
  },
  {
    upTo: 1,
    emoji: "🏆",
    title: "Champion !",
    sub: "Tous les exercices sont réussis. Essaie les exercices similaires plus difficiles !",
  },
];

/** All chapters at once: a ring for the exercises solved alone, and a word of encouragement. */
function Summary({ chapters }) {
  const total = chapters.reduce((n, c) => n + c.total, 0);
  const done = chapters.reduce((n, c) => n + c.done, 0);
  const seen = chapters.reduce((n, c) => n + c.solution_seen, 0);
  const ratio = total ? done / total : 0;
  const mood = MOODS.find((x) => ratio <= x.upTo) ?? MOODS[MOODS.length - 1];
  const r = 44;
  const circumference = 2 * Math.PI * r;
  return (
    <m.section className="prog-hero surface" variants={rise} aria-label="Résumé">
      <div
        className="prog-ring"
        role="img"
        aria-label={`${done} exercices réussis sur ${total}`}
      >
        <svg viewBox="0 0 100 100">
          <defs>
            <linearGradient id="prog-ring-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="100%" stopColor="#6b26d9" />
            </linearGradient>
          </defs>
          <circle className="prog-ring-track" cx="50" cy="50" r={r} />
          <m.circle
            className="prog-ring-fill"
            cx="50"
            cy="50"
            r={r}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - ratio) }}
            transition={{ ...SPRING_ENTER, visualDuration: 1.1, delay: 0.3 }}
          />
        </svg>
        <span className="prog-ring-text">
          <CountUp className="prog-ring-num" value={done} />
          <span className="prog-ring-total">/ {total}</span>
        </span>
      </div>
      <div className="prog-hero-text">
        <p className="prog-hero-title">
          <m.span
            className="prog-hero-emoji"
            aria-hidden="true"
            initial={{ scale: 0, rotate: -40 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{
              type: "spring",
              visualDuration: 0.5,
              bounce: 0.5,
              delay: 0.5,
            }}
          >
            {mood.emoji}
          </m.span>
          {mood.title}
        </p>
        <p className="prog-hero-sub">{mood.sub}</p>
        <p className="prog-hero-stats">
          <span className="prog-stat is-done">
            <b>{done}</b> réussis seul
          </span>
          <span className="prog-stat is-seen">
            <b>{seen}</b> avec la solution
          </span>
          <span className="prog-stat">
            <b>{total}</b> exercices au programme
          </span>
        </p>
      </div>
    </m.section>
  );
}

/** Réussis, solution vue and commencés as one bar, out of all the exercises. */
function StackedBar({ chapter }) {
  const total = Math.max(1, chapter.total);
  const parts = [
    ["is-done", chapter.done],
    ["is-seen", chapter.solution_seen],
    ["is-started", chapter.started - chapter.done - chapter.solution_seen],
  ];
  return (
    <div
      className="prog-bar"
      role="img"
      aria-label={`${chapter.done} réussis, ${chapter.solution_seen} avec la solution vue, ${
        chapter.started - chapter.done - chapter.solution_seen
      } commencés, sur ${chapter.total} exercices`}
    >
      {parts.map(([cls, n]) =>
        n > 0 ? (
          <m.span
            key={cls}
            className={`prog-bar-part ${cls}`}
            initial={{ width: 0 }}
            animate={{
              width: `${(n / total) * 100}%`,
              transition: { ...SPRING_ENTER, delay: 0.2 },
            }}
          />
        ) : null
      )}
    </div>
  );
}
