import { useState } from "react";
import AuthShell from "./AuthShell.jsx";
import Alert from "./ui/Alert.jsx";
import {
  NIVEAUX,
  SECTIONS,
  SECTIONS_BY_NIVEAU,
  updateProfile,
} from "../lib/profile.js";

/**
 * "Ton niveau et ta section": asked once, right after the first sign-in or
 * account creation, before the app opens - and reopened from the sidebar to
 * change it.
 *
 * Two groups of radio buttons drawn as tiles. Real radios, so arrow keys move
 * within a group and a screen reader hears "3 sur 6". Choosing a niveau that
 * does not have the current section (2ème has no Math or Technique) clears
 * the section rather than keeping a pair the server would refuse.
 *
 * `onCancel` is only passed when editing an existing profile; a student who
 * has never answered has nowhere to go back to, but can still sign out.
 */
export default function ProfileSetup({
  user,
  onSaved,
  onCancel,
  onLogout,
  onUnauthorized,
}) {
  const [niveau, setNiveau] = useState(user?.niveau ?? "");
  const [section, setSection] = useState(user?.section ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const allowed = niveau ? SECTIONS_BY_NIVEAU[niveau] : [];
  const canSave = Boolean(niveau && section && allowed.includes(section)) && !busy;

  function chooseNiveau(id) {
    setNiveau(id);
    if (section && !SECTIONS_BY_NIVEAU[id].includes(section)) setSection("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSave) return;
    setBusy(true);
    setError("");
    const result = await updateProfile(niveau, section);
    setBusy(false);
    if (result.unauthorized) return onUnauthorized?.();
    if (result.error) return setError(result.error);
    onSaved(result.user);
  }

  const firstName = user?.display_name?.trim().split(/\s+/)[0];

  return (
    <AuthShell
      title={
        onCancel
          ? "Ton niveau et ta section"
          : `Bienvenue${firstName ? `, ${firstName}` : ""} !`
      }
      subtitle={
        onCancel
          ? "Fahem adapte ses réponses et ses chapitres à ta classe."
          : "Dis-nous en quelle classe tu es : Fahem adaptera ses réponses et ses chapitres à ton programme."
      }
    >
      <form className="profile-form" onSubmit={handleSubmit}>
        <fieldset className="profile-group">
          <legend className="profile-legend">Ton niveau</legend>
          <div className="profile-options profile-options-niveau">
            {NIVEAUX.map((n) => (
              <label key={n.id} className="profile-option">
                <input
                  type="radio"
                  name="niveau"
                  value={n.id}
                  checked={niveau === n.id}
                  onChange={() => chooseNiveau(n.id)}
                />
                <span>{n.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="profile-group" disabled={!niveau}>
          <legend className="profile-legend">
            Ta section
            {!niveau && (
              <span className="profile-hint"> — choisis d'abord ton niveau</span>
            )}
          </legend>
          <div className="profile-options profile-options-section">
            {SECTIONS.filter((s) => !niveau || allowed.includes(s.id)).map((s) => (
              <label key={s.id} className="profile-option">
                <input
                  type="radio"
                  name="section"
                  value={s.id}
                  checked={section === s.id}
                  onChange={() => setSection(s.id)}
                />
                <span>{s.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        {error && <Alert>{error}</Alert>}

        <button
          type="submit"
          className="btn btn-md btn-primary profile-submit"
          disabled={!canSave}
        >
          {busy ? "Enregistrement…" : onCancel ? "Enregistrer" : "Continuer"}
        </button>

        <div className="profile-foot">
          {onCancel ? (
            <button type="button" className="btn btn-sm btn-ghost" onClick={onCancel}>
              Annuler
            </button>
          ) : (
            <button type="button" className="btn btn-sm btn-ghost" onClick={onLogout}>
              Ce n'est pas toi ? Se déconnecter
            </button>
          )}
        </div>
      </form>
    </AuthShell>
  );
}
