/**
 * The app's one icon set: 24px line icons, drawn with the text colour.
 *
 * It replaces the emoji that used to sit in buttons, chips and the sidebar
 * (📖 🧭 💡 ✍️ 🔍 …). Emoji render differently on every phone and never match
 * each other or the text beside them; one stroke set does both.
 *
 * Decorative by default (aria-hidden): the button or link around an icon
 * carries the words. Pass `label` only for an icon that stands alone.
 */
const PATHS = {
  // navigation
  home: "M3 10.5 12 3l9 7.5M5 9v11h5v-6h4v6h5V9",
  chapters:
    "M4 5.5A1.5 1.5 0 0 1 5.5 4H10l2 2h6.5A1.5 1.5 0 0 1 20 7.5v11a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5z",
  chat: "M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z",
  progress: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  admin: "M12 3 4.5 6v5.5c0 4.6 3.2 8.3 7.5 9.5 4.3-1.2 7.5-4.9 7.5-9.5V6z",
  // modes
  book: "M12 6.5C10.5 5 8 4.5 4 4.5v14c4 0 6.5.5 8 2 1.5-1.5 4-2 8-2v-14c-4 0-6.5.5-8 2zM12 6.5v14",
  compass: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM15.5 8.5l-2 5-5 2 2-5z",
  // actions
  plus: "M12 5v14M5 12h14",
  history: "M3 12a9 9 0 1 0 2.6-6.4L3 8M3 3v5h5M12 7.5V12l3 2",
  logout:
    "M9 20H5.5A1.5 1.5 0 0 1 4 18.5v-13A1.5 1.5 0 0 1 5.5 4H9M16 16l4-4-4-4M20 12H9",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6 6 18",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  arrowUp: "M12 19V5M5.5 11.5 12 5l6.5 6.5",
  swap: "M7 4 3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7",
  check: "M5 12.5 10 17.5 19 7",
  checkCircle: "M9 11.5 11.5 14 16 9.5M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18z",
  pencil: "M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16zM13.5 6.5l4 4",
  eye: "M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7zM12 14.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  edit: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z",
  // guided steps
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4",
  bulb: "M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.4 1 1.1 1 1.9V16h5v-.2c0-.8.4-1.5 1-1.9A6 6 0 0 0 12 3z",
  puzzle:
    "M10 4a2 2 0 1 1 4 0v2h4v4h-2a2 2 0 1 0 0 4h2v4h-4v-2a2 2 0 1 0-4 0v2H6v-4h2a2 2 0 1 0 0-4H6V6h4z",
  flag: "M5 21V4M5 4h11l-2 4 2 4H5",
  // practice levels and moods
  sprout: "M12 20v-8M12 12c0-4-3-6-7-6 0 4 3 6 7 6zM12 14c0-4 3-6 7-6 0 4-3 6-7 6z",
  scale: "M12 4v16M8 20h8M5 8h14M5 8l-2.5 6a3 3 0 0 0 5 0zM19 8l-2.5 6a3 3 0 0 0 5 0z",
  flame:
    "M12 21a6 6 0 0 0 6-6c0-4-3-6-4-10-1.5 2-2 3.5-2 5-1-1-2-1.5-2.5-3C8 9 6 11.5 6 15a6 6 0 0 0 6 6z",
  dice: "M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM8.5 8.5h.01M15.5 8.5h.01M12 12h.01M8.5 15.5h.01M15.5 15.5h.01",
  trophy:
    "M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3",
  rocket:
    "M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2M14 4c3-1 6-1 6-1s0 3-1 6l-7 7-5-5zM9 11l-3 0-2 3 4 1M13 15v3l-3 2-1-4",
  bolt: "M13 2 4 14h7l-1 8 9-12h-7z",
  sparkle:
    "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18",
  repeat: "M17 2l3 3-3 3M4 11V9a4 4 0 0 1 4-4h12M7 22l-3-3 3-3M20 13v2a4 4 0 0 1-4 4H4",
  muscle:
    "M7 15c0-5 2-10 5-10 1.5 0 2 1 2 2s-1 2-2 2c0 2 1 3 3 3 3 0 5 2 5 4s-2 4-6 4H10c-2 0-3-2-3-5z",
  paperclip:
    "M20.5 11.5 12.4 19.6a5 5 0 0 1-7.1-7.1l8.5-8.5a3.4 3.4 0 0 1 4.8 4.8l-8.5 8.5a1.7 1.7 0 0 1-2.4-2.4l7.8-7.8",
  code: "M8 7l-5 5 5 5M16 7l5 5-5 5",
  play: "M7 4.5v15L19.5 12z",
  alert:
    "M12 9v4M12 17h.01M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
};

export default function Icon({
  name,
  size = 18,
  className = "",
  label,
  strokeWidth = 1.8,
}) {
  const d = PATHS[name];
  if (!d) return null;
  return (
    <svg
      className={`icon${className ? ` ${className}` : ""}`}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : "true"}
      role={label ? "img" : undefined}
      aria-label={label}
      focusable="false"
    >
      <path d={d} />
    </svg>
  );
}

/**
 * Fahem's mark: a rounded tile in the accent with a white "f" whose bar is
 * the algorithm's assignment arrow (←). The ← alone, which the mark used to
 * be, read as a "go back" button.
 */
export function LogoMark({ size = 28, className = "" }) {
  return (
    <svg
      className={`logo-mark${className ? ` ${className}` : ""}`}
      viewBox="0 0 32 32"
      width={size}
      height={size}
      aria-hidden="true"
      focusable="false"
    >
      <rect width="32" height="32" rx="9" fill="var(--accent)" />
      <path
        d="M19.5 8.5c-.6-.3-1.3-.5-2.1-.5-2.3 0-3.9 1.5-3.9 4v11.5"
        fill="none"
        stroke="var(--accent-fg)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <path
        d="M20.5 15h-10M13 12.2 10.2 15l2.8 2.8"
        fill="none"
        stroke="var(--accent-fg)"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
