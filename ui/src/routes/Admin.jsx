import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { fetchAdminWhoAmI, ForbiddenError, UnauthorizedError } from "../lib/admin.js";
import { useAuth } from "../lib/authContext.js";
import Alert from "../components/ui/Alert.jsx";

/**
 * The admin placeholder (Phase 7). No feature yet - this page exists to prove
 * the gate.
 *
 * Two locks, and the page is only drawn once both have opened:
 *
 *   1. App.jsx does not register /admin at all unless the /auth/me user is an
 *      admin, so a student typing the URL falls through to the catch-all and
 *      lands on "/". This component never even mounts for them.
 *   2. On mount it asks the server (/admin/whoami, behind get_current_admin).
 *      The role in the client came from /auth/me at sign-in and may be stale -
 *      an operator can demote an account whose tab is still open - so the
 *      welcome is shown only after the server says yes *now*.
 *
 * Nothing admin-looking is rendered while that request is in flight, so a
 * stale client never flashes the page before the 403 arrives.
 */
export default function Admin() {
  const { onUnauthorized } = useAuth();
  // checking | ok | forbidden | failed
  const [state, setState] = useState("checking");
  const [me, setMe] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchAdminWhoAmI()
      .then((data) => {
        if (cancelled) return;
        setMe(data);
        setState("ok");
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
        else if (err instanceof ForbiddenError) setState("forbidden");
        else setState("failed");
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  // The server said no: the client's role was stale. Out, silently, to the
  // same place a student typing /admin ends up.
  if (state === "forbidden") return <Navigate to="/" replace />;

  return (
    <main className="page">
      {state === "checking" && (
        <p className="sr-only" role="status">
          Vérification…
        </p>
      )}

      {state === "failed" && (
        <Alert className="page-alert">
          Impossible de vérifier l'accès administrateur. Recharge la page pour
          réessayer.
        </Alert>
      )}

      {state === "ok" && (
        <header className="page-head">
          <h1>Bienvenue, admin</h1>
          <p className="page-lead">
            Connecté en tant que {me.email}. Les outils d'administration arriveront ici.
          </p>
        </header>
      )}
    </main>
  );
}
