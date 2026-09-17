import { useState } from "react";
import { AnimatePresence, useReducedMotion } from "motion/react";
import * as m from "motion/react-m";
import Markdown from "../Markdown.jsx";
import { SPRING_ENTER, SPRING_HOVER } from "../../lib/motion.js";
import {
  GUIDED_STEPS,
  PRACTICE_LEVELS,
  VERDICTS,
  practiceStatement,
  splitCorrection,
  withoutVerdictLine,
} from "../../lib/learning.js";

/*
 * The learning features' visuals in the chat: Mode guidé's step rail and
 * buttons, a checked solution's verdict, the similar-exercise card and menu.
 *
 * Built only on transforms, opacity, height and SVG strokes - the student app
 * loads Motion's domAnimation features (MotionProvider.jsx), without layout
 * animations. `fresh` is true only for the answer that just finished in front
 * of the student (Chat.jsx): the celebrations play then, never when an old
 * discussion is reopened. Under reduced motion, Motion drops the transforms
 * and the confetti is not drawn at all.
 */

const STEP_ICONS = { 1: "🔍", 2: "💡", 3: "🧩", 4: "🏁" };
const LEVEL_ICONS = { easier: "🌱", same: "⚖️", harder: "🔥" };
const PRESS = { scale: 0.96 };
const LIFT = { y: -2, transition: SPRING_HOVER };

/* --- confetti --------------------------------------------------------------------------------- */

const COLORS = ["#6b26d9", "#22c55e", "#f59e0b", "#ec4899", "#3b82f6", "#14b8a6"];

// Deterministic "random" per particle: the same burst every render.
const noise = (i, salt) => {
  const x = Math.sin(i * 12.9898 + salt * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

/** A one-shot burst of confetti from the centre of its parent. */
export function Burst({ count = 32, spread = 170 }) {
  const reduce = useReducedMotion();
  if (reduce) return null;
  return (
    <span className="fx-burst" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => {
        const angle = (i / count) * Math.PI * 2 + noise(i, 1) * 0.6;
        const distance = spread * (0.55 + noise(i, 2) * 0.6);
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance - 20;
        return (
          <m.span
            key={i}
            className={`fx-piece${i % 3 === 0 ? " is-round" : ""}`}
            style={{ background: COLORS[i % COLORS.length] }}
            initial={{ x: 0, y: 0, scale: 0.4, rotate: 0, opacity: 1 }}
            animate={{
              x,
              y: [0, y, y + 40],
              scale: [0.4, 1, 0.8],
              rotate: noise(i, 3) * 540 - 270,
              opacity: [1, 1, 0],
            }}
            transition={{
              duration: 1.6 + noise(i, 4) * 0.6,
              ease: "easeOut",
              opacity: { times: [0, 0.75, 1], duration: 1.6 + noise(i, 4) * 0.6 },
            }}
          />
        );
      })}
    </span>
  );
}

/* --- Mode guidé ---------------------------------------------------------------------------------- */

/** Comprendre → Indice → Squelette → Solution, the rail filling up to the step. */
export function GuidedSteps({ step, fresh, live }) {
  const current = GUIDED_STEPS.find((s) => s.step === step);
  const to = (step - 1) / 3;
  const from = fresh ? Math.max(0, (step - 2) / 3) : to;
  return (
    <div className="gs">
      <p className="gs-chip">
        <m.span
          className="gs-chip-icon"
          aria-hidden="true"
          initial={fresh ? { scale: 0, rotate: -30 } : false}
          animate={{
            scale: 1,
            rotate: 0,
            transition: { ...SPRING_HOVER, delay: 0.25 },
          }}
        >
          {STEP_ICONS[step]}
        </m.span>
        Étape {step} sur 4 · <b>{current?.label}</b>
      </p>
      <div className="gs-rail-wrap">
        <span className="gs-track" aria-hidden="true">
          <m.span
            className="gs-fill"
            initial={{ scaleX: from }}
            animate={{ scaleX: to }}
            transition={{ ...SPRING_ENTER, visualDuration: 0.7, delay: 0.1 }}
          />
        </span>
        <ol
          className="gs-rail"
          aria-label={`Mode guidé, étape ${step} sur 4 : ${current?.label ?? ""}`}
        >
          {GUIDED_STEPS.map((s) => {
            const done = s.step < step;
            const now = s.step === step;
            return (
              <li
                key={s.step}
                className={`gs-step${done ? " is-done" : ""}${now ? " is-current" : ""}`}
                aria-current={now ? "step" : undefined}
              >
                <span className="gs-dot" aria-hidden="true">
                  {now && live && (
                    <m.span
                      className="gs-ping"
                      animate={{ scale: [1, 1.8], opacity: [0.45, 0] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
                    />
                  )}
                  {done ? (
                    <svg viewBox="0 0 24 24" className="gs-check">
                      <m.path
                        d="M6 12.5 10.5 17 18 8"
                        initial={
                          fresh && s.step === step - 1 ? { pathLength: 0 } : false
                        }
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 0.35, delay: 0.45 }}
                      />
                    </svg>
                  ) : (
                    <m.span
                      initial={fresh && now ? { scale: 0.3 } : false}
                      animate={{
                        scale: 1,
                        transition: { ...SPRING_HOVER, delay: 0.5 },
                      }}
                    >
                      {s.step}
                    </m.span>
                  )}
                </span>
                <span className="gs-label">{s.label}</span>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}

/** Buttons that arrive one after the other, lift on hover and press on tap. */
export function ActionRow({ children, fresh }) {
  return (
    <m.div
      className="guided-actions"
      initial={fresh ? "hidden" : false}
      animate="show"
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: 0.07, delayChildren: 0.15 } },
      }}
    >
      {children}
    </m.div>
  );
}

export function ActionButton({ tone = "", onClick, children }) {
  return (
    <m.button
      type="button"
      className={`guided-btn${tone ? ` is-${tone}` : ""}`}
      onClick={onClick}
      variants={{
        hidden: { opacity: 0, y: 8, scale: 0.96 },
        show: { opacity: 1, y: 0, scale: 1, transition: SPRING_HOVER },
      }}
      whileHover={LIFT}
      whileTap={PRESS}
    >
      {children}
    </m.button>
  );
}

/* --- Vérifier ma réponse ----------------------------------------------------------------------- */

const VERDICT_TEXT = {
  correct: {
    emoji: "🎉",
    title: "Bravo, ta solution est correcte !",
    sub: "Tu as résolu cet exercice toi-même. Il compte dans ta progression.",
  },
  presque: {
    emoji: "💪",
    title: "Presque ! Il reste quelques détails.",
    sub: "Regarde ce qu'il faut corriger, puis vérifie à nouveau.",
  },
  a_revoir: {
    emoji: "🔁",
    title: "À revoir : on corrige ensemble.",
    sub: "Commence par la correction la plus importante, en bas.",
  },
};

const VERDICT_MOTION = {
  correct: { scale: [0.6, 1.08, 1], rotate: [0, -3, 0] },
  presque: { rotate: [0, -4, 4, -2, 0], scale: [0.9, 1] },
  a_revoir: { x: [0, -8, 8, -5, 5, 0], scale: [0.95, 1] },
};

/** A checked solution: the verdict card, the review, the correction folded away. */
export function CheckedAnswer({ content, verdict, fresh }) {
  const [open, setOpen] = useState(false);
  const { review, correction } = splitCorrection(content);
  const shown = VERDICTS[verdict];
  const text = VERDICT_TEXT[verdict];
  return (
    <>
      {shown && text && (
        <m.div
          className={`vc is-${verdict}`}
          initial={fresh ? { opacity: 0, y: 10 } : false}
          animate={{ opacity: 1, y: 0, transition: SPRING_ENTER }}
          role="status"
        >
          <span className="vc-emoji-wrap">
            <m.span
              className="vc-emoji"
              aria-hidden="true"
              initial={false}
              animate={fresh ? VERDICT_MOTION[verdict] : {}}
              transition={{ duration: 0.7, delay: 0.15 }}
            >
              {text.emoji}
            </m.span>
            {fresh && verdict === "correct" && <Burst />}
          </span>
          <span className="vc-text">
            <span className="vc-label">
              {shown.icon} Verdict : {shown.label}
            </span>
            <span className="vc-title">{text.title}</span>
            <span className="vc-sub">{text.sub}</span>
          </span>
        </m.div>
      )}
      <Markdown>{shown ? withoutVerdictLine(review) : review}</Markdown>
      {correction && (
        <div className="check-correction">
          <m.button
            type="button"
            className={`guided-btn${open ? "" : " is-primary"}`}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            whileHover={LIFT}
            whileTap={PRESS}
          >
            {open ? "Masquer la correction complète" : "Voir la correction complète"}
            <m.span
              aria-hidden="true"
              className="check-chevron"
              animate={{ rotate: open ? 180 : 0 }}
              transition={SPRING_HOVER}
            >
              ▾
            </m.span>
          </m.button>
          <AnimatePresence initial={false}>
            {open && (
              <m.div
                key="correction"
                className="check-correction-body"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1, transition: SPRING_ENTER }}
                exit={{ height: 0, opacity: 0, transition: { duration: 0.2 } }}
              >
                <div className="check-correction-inner">
                  <Markdown>{correction}</Markdown>
                </div>
              </m.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </>
  );
}

/* --- Exercice similaire ------------------------------------------------------------------------ */

/** A generated exercise, as a challenge card. */
export function PracticeCard({ content, difficulty, fresh }) {
  const level =
    PRACTICE_LEVELS.find((l) => l.value === difficulty) ?? PRACTICE_LEVELS[1];
  return (
    <m.div
      className={`pc is-${level.value}`}
      initial={fresh ? { opacity: 0, scale: 0.97, y: 8 } : false}
      animate={{ opacity: 1, scale: 1, y: 0, transition: SPRING_ENTER }}
    >
      <div className="pc-head">
        <m.span
          className="pc-dice"
          aria-hidden="true"
          initial={fresh ? { rotate: -200, scale: 0.4 } : false}
          animate={{
            rotate: 0,
            scale: 1,
            transition: { type: "spring", visualDuration: 0.6, bounce: 0.45 },
          }}
        >
          🎲
        </m.span>
        <span className="pc-title">Nouveau défi</span>
        <span className="pc-level">
          <span aria-hidden="true">{LEVEL_ICONS[level.value]}</span> {level.label}
        </span>
      </div>
      <div className="pc-body">
        <Markdown>{practiceStatement(content)}</Markdown>
      </div>
    </m.div>
  );
}

/** "Exercice similaire", then how hard: three levels pop out of the button. */
export function PracticeMenu({ onPick }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="practice-menu">
      <m.button
        type="button"
        className={`msg-action practice-trigger${open ? " is-open" : ""}`}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        whileTap={PRESS}
      >
        <m.span
          aria-hidden="true"
          animate={{ rotate: open ? 45 : 0 }}
          transition={SPRING_HOVER}
          className="practice-plus"
        >
          +
        </m.span>
        Exercice similaire
      </m.button>
      <AnimatePresence>
        {open && (
          <m.span
            className="practice-levels"
            role="group"
            aria-label="Difficulté"
            initial="hidden"
            animate="show"
            exit="hidden"
            variants={{
              hidden: { transition: { staggerChildren: 0.03, staggerDirection: -1 } },
              show: { transition: { staggerChildren: 0.06 } },
            }}
          >
            {PRACTICE_LEVELS.map((level) => (
              <m.button
                key={level.value}
                type="button"
                className={`practice-level is-${level.value}`}
                variants={{
                  hidden: { opacity: 0, x: -8, scale: 0.9 },
                  show: { opacity: 1, x: 0, scale: 1, transition: SPRING_HOVER },
                }}
                whileHover={LIFT}
                whileTap={PRESS}
                onClick={() => {
                  setOpen(false);
                  onPick(level.value);
                }}
              >
                <span aria-hidden="true">{LEVEL_ICONS[level.value]}</span> {level.label}
              </m.button>
            ))}
          </m.span>
        )}
      </AnimatePresence>
    </span>
  );
}
