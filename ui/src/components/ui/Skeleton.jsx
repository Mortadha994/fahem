/**
 * A placeholder shape that holds a layout while its content loads.
 *
 * Replaces bare "Chargement…" lines (audit P2-9), which gave the page nothing
 * to stand on: the real content arrived and everything below it jumped.
 *
 * Always aria-hidden. A grey rectangle means nothing read aloud, so the call
 * site keeps its own role="status" and a visually-hidden "Chargement…" - the
 * skeleton is for sighted users, the status text for everyone else.
 *
 * Size it with width/height (any CSS length) or with a className; `radius`
 * picks a step from the radius scale. The 1em default height lives in the
 * CSS, not here: a default inline style would outrank any sizing class the
 * caller passes, so className sizing could never win.
 */
export default function Skeleton({
  width,
  height,
  radius = "sm",
  className = "",
  style,
}) {
  return (
    <span
      aria-hidden="true"
      className={`skeleton skeleton-r-${radius}${className ? ` ${className}` : ""}`}
      style={{ width, height, ...style }}
    />
  );
}
