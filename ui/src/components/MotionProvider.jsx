import { LazyMotion, MotionConfig, domAnimation } from "motion/react";

/**
 * Motion for the signed-in app.
 *
 * - LazyMotion + domAnimation: animations, variants, exit animations and
 *   hover/tap/focus gestures, without the layout and drag features the app
 *   does not use (Motion docs, "Reduce bundle size"). `strict` makes any
 *   full `motion.*` component throw, so nobody reintroduces the heavy one.
 *
 *   The features are bundled rather than lazy-loaded on purpose. Entrances
 *   start from opacity 0; with a lazy chunk, a failed or slow download would
 *   leave the home screen blank until it arrived. The landing page holds the
 *   same line - nothing is hidden that the page cannot bring back itself.
 *
 * - reducedMotion="user": with the OS "reduce motion" setting on, Motion
 *   drops transform animations (rises, lifts, pops) and keeps opacity fades
 *   (Motion docs, "Accessibility"). CSS loops are stopped separately in
 *   App.css.
 */
export default function MotionProvider({ children }) {
  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">{children}</MotionConfig>
    </LazyMotion>
  );
}
