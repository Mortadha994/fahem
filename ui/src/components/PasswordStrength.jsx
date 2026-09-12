import { PASSWORD_MIN_LENGTH } from "../lib/auth.js";

/*
 * Judged on length alone, on purpose - the same rule the backend enforces
 * (NIST 800-63B / OWASP: length, no composition rules). A meter that rewarded
 * "P@ssw0rd!" for its symbols would teach the opposite of the rule, and would
 * disagree with the server about what counts as acceptable.
 */
const LEVELS = [
  { label: `Trop court — ${PASSWORD_MIN_LENGTH} caractères minimum`, tone: "short" },
  { label: "Correct — quelques mots de plus le renforceraient", tone: "fair" },
  { label: "Solide", tone: "good" },
  { label: "Excellent", tone: "great" },
];

function levelFor(length) {
  if (length < PASSWORD_MIN_LENGTH) return 0;
  if (length < PASSWORD_MIN_LENGTH + 4) return 1;
  if (length < PASSWORD_MIN_LENGTH + 8) return 2;
  return 3;
}

/**
 * Four-segment strength bar under a new-password field. Counted the way the
 * backend counts (NFKC, code points). The label is a polite live region: it
 * only changes when the level changes, so a screen reader hears "Solide" once,
 * not a word per keystroke.
 */
export default function PasswordStrength({ value }) {
  const length = [...value.normalize("NFKC")].length;
  if (length === 0) return null;
  const level = levelFor(length);
  const { label, tone } = LEVELS[level];

  return (
    <div className={`pw-meter pw-${tone}`}>
      <div className="pw-bars" aria-hidden="true">
        {LEVELS.map((l, i) => (
          <span key={l.tone} className={i <= level ? "is-on" : ""} />
        ))}
      </div>
      <p className="pw-label" aria-live="polite">
        {label}
      </p>
    </div>
  );
}
