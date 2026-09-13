/**
 * An account's initial on a colour of its own.
 *
 * Every avatar used to be the same violet circle, so a list of accounts was a
 * column of identical dots and "which one was that" came down to reading every
 * email. The colour is derived from the account id - stable across reloads and
 * pages, and the same account always looks the same - and picked from a fixed
 * set that each carries white text above 4.5:1, rather than a computed hue that
 * could land on a pale yellow.
 *
 * Decoration: the name beside it is what a screen reader gets.
 */

const PALETTE = [
  "#4f46e5", // indigo
  "#6a4fe0", // brand violet
  "#3f6fb5", // brand blue
  "#0f766e", // teal
  "#047857", // green
  "#b45309", // amber
  "#be185d", // pink
  "#7c3aed", // purple
];

function colourFor(seed = "") {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

export default function AdminAvatar({ seed, label, size = "md" }) {
  const initial = (label || "?").trim().charAt(0).toUpperCase() || "?";
  return (
    <span
      className={`adm-avatar${size === "md" ? "" : ` adm-avatar-${size}`}`}
      style={{ background: colourFor(seed || label) }}
      aria-hidden="true"
    >
      {initial}
    </span>
  );
}
