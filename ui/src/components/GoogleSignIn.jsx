import { useEffect, useRef, useState } from "react";
import { GOOGLE_CLIENT_ID } from "../config.js";
import Alert from "./ui/Alert.jsx";

const GIS_SRC = "https://accounts.google.com/gsi/client";

/**
 * Google's Identity Services button, loaded directly rather than through a
 * wrapper library.
 *
 * Why no @react-oauth/google: its last release was 2023, and putting a stale
 * dependency on the authentication path is the same risk the backend avoided
 * by choosing PyJWT over python-jose. The FedCM migration people cite as a
 * reason to use a wrapper actually argues the other way here - FedCM changes
 * One Tap (google.accounts.id.prompt()), which this does not use.
 * renderButton is the stable surface, and a wrapper would sit between us and
 * GIS without insulating us from its changes.
 *
 * `onCredential` receives the raw ID token. It is only ever handed to the
 * backend, which verifies it against Google's public keys - the frontend
 * never treats it as proof of anything on its own.
 */
export default function GoogleSignIn({ onCredential, disabled }) {
  const holder = useRef(null);
  const callbackRef = useRef(onCredential);

  // Only the script-load failure is state; a missing client id is knowable
  // during render, so deriving it avoids a setState inside the effect (and
  // the extra render pass that comes with it).
  const [loadFailed, setLoadFailed] = useState(false);
  const misconfigured = !GOOGLE_CLIENT_ID;
  const failed = misconfigured || loadFailed;

  // Keep the latest callback without re-running the effect: re-initialising
  // GIS on every render would tear the rendered button down mid-click.
  useEffect(() => {
    callbackRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (misconfigured) return;

    let cancelled = false;

    function render() {
      if (cancelled || !holder.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => callbackRef.current?.(response.credential),
      });
      window.google.accounts.id.renderButton(holder.current, {
        theme: "outline",
        size: "large",
        shape: "pill",
        text: "signin_with",
        logo_alignment: "left",
        width: 280,
      });
    }

    if (window.google?.accounts?.id) {
      render();
      return () => {
        cancelled = true;
      };
    }

    // Reuse the tag if it is already in flight - StrictMode mounts effects
    // twice in dev, and two <script> tags for GIS race each other.
    let script = document.querySelector(`script[src="${GIS_SRC}"]`);
    if (!script) {
      script = document.createElement("script");
      script.src = GIS_SRC;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", render);
    script.addEventListener("error", () => !cancelled && setLoadFailed(true));

    return () => {
      cancelled = true;
      script.removeEventListener("load", render);
    };
  }, [misconfigured]);

  if (failed) {
    return (
      <Alert>
        {misconfigured
          ? "La connexion Google n'est pas configurée sur ce serveur."
          : "Impossible de charger la connexion Google. Vérifie ta connexion internet et recharge la page."}
      </Alert>
    );
  }

  return (
    <div
      className="google-btn"
      ref={holder}
      // Google renders into this node, so React must not manage its children.
      aria-busy={disabled ? "true" : "false"}
      style={disabled ? { opacity: 0.5, pointerEvents: "none" } : undefined}
    />
  );
}
