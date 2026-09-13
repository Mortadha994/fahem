// Shared motion vocabulary for the signed-in app (home + chat).
//
// Components animate with `m.*` from "motion/react-m" inside the
// MotionProvider (components/MotionProvider.jsx), never `motion.*`: the full
// component preloads every feature and would undo LazyMotion's saving - the
// provider is `strict`, so a stray `motion.div` throws in development.
//
// Springs are described by feel (visualDuration + bounce), as the landing
// page's are, so an entrance and a hover read as the same material.

export const SPRING_ENTER = { type: "spring", visualDuration: 0.5, bounce: 0.2 };
export const SPRING_HOVER = { type: "spring", visualDuration: 0.25, bounce: 0.3 };
export const SPRING_PRESS = { type: "spring", visualDuration: 0.15, bounce: 0 };

/** A container whose children rise in one after another. */
export const stagger = (gap = 0.07, delay = 0) => ({
  hidden: {},
  show: { transition: { staggerChildren: gap, delayChildren: delay } },
});

/** The child of `stagger`: fades up into place. */
export const rise = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: SPRING_ENTER },
};

/** A small element that pops into place (streak days, verdict badge). */
export const pop = {
  hidden: { opacity: 0, scale: 0.6 },
  show: { opacity: 1, scale: 1, transition: { ...SPRING_ENTER, bounce: 0.45 } },
};

export const HOVER_LIFT = { y: -4, transition: SPRING_HOVER };
export const PRESS = { scale: 0.98, transition: SPRING_PRESS };
