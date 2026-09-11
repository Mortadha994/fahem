/**
 * A small status pill.
 *
 * One primitive for what used to be two systems doing the same job - the
 * checker's .badge-* in Message and the chapter card's .chapter-tag-* - with
 * different padding, size and radius each (audit P2-3). Tones name meaning,
 * not colour:
 *
 *   neutral - informational, or not available yet ("À venir")
 *   success - a check passed or a thing is ready ("Disponible")
 *   warning - look at this, nothing is broken ("Syntaxe à vérifier")
 *   danger  - something failed
 *
 * Not interactive, so there is no size or focus state. `className` is for
 * placement (margin, alignment inside a card) only.
 */
export default function Badge({ tone = "neutral", className = "", ...rest }) {
  return (
    <span
      className={`badge badge-${tone}${className ? ` ${className}` : ""}`}
      {...rest}
    />
  );
}
