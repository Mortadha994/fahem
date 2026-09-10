import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout.jsx";
import SignInScreen from "./components/SignInScreen.jsx";
import Home from "./routes/Home.jsx";
import ChapterPage from "./routes/ChapterPage.jsx";
import Chat from "./routes/Chat.jsx";
import { fetchMe, signInWithGoogle, logout } from "./lib/auth.js";
import { AuthContext } from "./lib/authContext.js";
import "./App.css";

const SIGNIN_FAILED =
  "La connexion a échoué. Réessaie, ou vérifie que tu utilises un compte Google valide.";
const SIGNIN_UNREACHABLE =
  "Impossible de joindre le serveur. Vérifie ta connexion et réessaie.";

/**
 * The auth shell. Everything below it is already signed in.
 *
 * The three-state check moved out of the chat screen in Phase 3b and now
 * wraps the whole router, so the gate covers every route rather than one of
 * them. That is a structural guarantee, not a rule to remember: an
 * unauthenticated visitor never reaches <Routes> at all, so a route added
 * later cannot be accidentally public - there is no per-route check to forget.
 */
export default function App() {
  // Three states, not a boolean: "checking" has to be distinguishable from
  // "signed out", otherwise the sign-in screen flashes on every reload before
  // /auth/me answers, and a logged-in student sees a login form for a moment.
  const [authState, setAuthState] = useState("checking"); // checking|out|in
  const [user, setUser] = useState(null);
  const [signinBusy, setSigninBusy] = useState(false);
  const [signinError, setSigninError] = useState(null);

  // One /auth/me on load. The cookie is httpOnly, so asking the server is the
  // only way to know whether there is a session - there is nothing readable
  // in the browser to check first.
  useEffect(() => {
    let cancelled = false;
    fetchMe()
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setAuthState(me ? "in" : "out");
      })
      .catch(() => {
        // A backend outage is not a logged-out user, but there is nothing
        // useful to render either - the sign-in screen at least offers an
        // action, and the error explains why it may not work yet.
        if (cancelled) return;
        setAuthState("out");
        setSigninError(SIGNIN_UNREACHABLE);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCredential = useCallback(async (idToken) => {
    setSigninBusy(true);
    setSigninError(null);
    try {
      const me = await signInWithGoogle(idToken);
      setUser(me);
      setAuthState("in");
    } catch {
      setSigninError(SIGNIN_FAILED);
    } finally {
      setSigninBusy(false);
    }
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await logout();
    } finally {
      // Local state resets either way: if the network call failed the cookie
      // may survive, but leaving the UI in a signed-in state it cannot use is
      // worse than showing the sign-in screen.
      //
      // localStorage chat history is deliberately NOT cleared - it is
      // browser-scoped, not identity-scoped, in this phase.
      setUser(null);
      setAuthState("out");
    }
  }, []);

  /** The session went away mid-use (expired, or logged out in another tab). */
  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setAuthState("out");
    setSigninError("Ta session a expiré. Reconnecte-toi pour continuer.");
  }, []);

  const auth = useMemo(
    () => ({ user, logout: handleLogout, onUnauthorized: handleUnauthorized }),
    [user, handleLogout, handleUnauthorized]
  );

  // Neither the app nor the sign-in screen, until /auth/me has answered -
  // rendering either one early means a visible flash of the wrong app.
  if (authState === "checking") {
    return (
      <div className="boot" role="status" aria-live="polite">
        <span className="brand">Fahem</span>
        <span className="boot-dots" aria-hidden="true" />
        <span className="sr-only">Chargement…</span>
      </div>
    );
  }

  // Note there is no <Routes> in this branch: a signed-out visitor gets the
  // sign-in screen for every path, including one typed straight into the bar,
  // and no authenticated route is ever mounted to flash its content first.
  if (authState === "out") {
    return (
      <SignInScreen
        onCredential={handleCredential}
        busy={signinBusy}
        error={signinError}
      />
    );
  }

  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route element={<AppLayout />}>
          {/* Sign-in lands here, not in the chat: the chapters are the
              starting point, and the freeform chat is one option from the
              header rather than the only thing the app does. */}
          <Route path="/" element={<Home />} />
          <Route path="/chapitre/:id" element={<ChapterPage />} />
          <Route path="/chat" element={<Chat />} />
          {/* An unknown path is a mistyped URL or a stale bookmark, not an
              error worth a screen of its own at this size. */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AuthContext.Provider>
  );
}
