import { useEffect } from "react";
import { animate, useMotionValue, useReducedMotion, useTransform } from "motion/react";
import * as m from "motion/react-m";
import { SPRING_ENTER } from "../lib/motion.js";

/**
 * A whole number that counts up to `value` when it appears, and springs to a
 * new value when it changes.
 *
 * Built on a motion value rather than state, so the count renders straight
 * into the DOM without re-rendering React on every frame (Motion docs,
 * "Motion values overview"). The number shown is always a real count - this
 * only animates the way it arrives.
 *
 * MotionConfig's reducedMotion covers `m` components, not an imperative
 * animate() call, so reduced motion is checked here and the value is set
 * directly instead.
 */
export default function CountUp({ value, delay = 0.3, className, ...rest }) {
  const reduce = useReducedMotion();
  const count = useMotionValue(reduce ? value : 0);
  const shown = useTransform(() => Math.round(count.get()));

  useEffect(() => {
    if (reduce) {
      count.jump(value);
      return undefined;
    }
    const controls = animate(count, value, {
      ...SPRING_ENTER,
      visualDuration: 0.8,
      bounce: 0,
      delay,
    });
    return () => controls.stop();
  }, [count, value, delay, reduce]);

  return (
    <m.span className={className} {...rest}>
      {shown}
    </m.span>
  );
}
