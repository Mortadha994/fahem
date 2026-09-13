import { setTheme, useTheme } from "../lib/theme.js";

/**
 * The light / dark switch.
 *
 * One button, not a menu: it shows the theme you would switch *to* (a moon
 * in light mode, a sun in dark mode), which is what people expect from this
 * control. Its accessible name says the action ("Passer au thème sombre"),
 * and aria-pressed is deliberately not used - a pressed state would have to
 * mean "dark is on", which reads backwards to half of the people using it.
 *
 * Styled with currentColor so it sits in any bar - the student sidebar, the
 * public pages' glass bar, the console's dark command bar - and takes that
 * bar's text colour. `className` places it.
 */
export default function ThemeToggle({ className = "" }) {
  const theme = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  const label = next === "dark" ? "Passer au thème sombre" : "Passer au thème clair";

  return (
    <button
      type="button"
      className={`theme-toggle${className ? ` ${className}` : ""}`}
      data-theme-current={theme}
      onClick={() => setTheme(next)}
      aria-label={label}
      title={label}
    >
      {/* Both icons are always drawn; CSS turns and fades between them. */}
      <svg
        className="theme-toggle-icon theme-toggle-sun"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="4.2" />
        <path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6" />
      </svg>
      <svg
        className="theme-toggle-icon theme-toggle-moon"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6Z" />
      </svg>
    </button>
  );
}
