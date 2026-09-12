import { useState } from "react";
import Button from "./ui/Button.jsx";

/**
 * A password input with a show/hide toggle.
 *
 * With a 12-character minimum, students typing on a phone mistype a lot and
 * cannot see where; the toggle is how they check. It is a plain Button, not a
 * new control: its visible word ("Afficher") is contained in its accessible
 * name ("Afficher le mot de passe"), so voice users can say what they see
 * (WCAG 2.5.3), and the name changes with the state so a screen reader hears
 * what pressing it will do next.
 *
 * type="button" (Button's default) matters: inside a form, a bare <button>
 * would submit it.
 */
export default function PasswordField({
  id,
  label,
  value,
  onChange,
  autoComplete,
  hint,
  labelAction,
}) {
  const [visible, setVisible] = useState(false);
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <div className="field">
      {/* labelAction (the login form's "Mot de passe oublié ?") sits on the
          label row, where people look for it, rather than under the button. */}
      <div className="field-label-row">
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
        {labelAction}
      </div>
      <div className="password-field">
        <input
          id={id}
          className="field-input"
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          aria-describedby={hintId}
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          required
        />
        <Button
          variant="ghost"
          size="sm"
          className="password-toggle"
          aria-controls={id}
          aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
          onClick={() => setVisible((v) => !v)}
        >
          {visible ? "Masquer" : "Afficher"}
        </Button>
      </div>
      {hint && (
        <p id={hintId} className="field-hint">
          {hint}
        </p>
      )}
    </div>
  );
}
