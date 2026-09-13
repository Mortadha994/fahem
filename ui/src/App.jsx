import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import AppLayout from "./components/AppLayout.jsx";
import Landing from "./components/Landing.jsx";
import SignInScreen from "./components/SignInScreen.jsx";
import Home from "./routes/Home.jsx";
import ChapterPage from "./routes/ChapterPage.jsx";
import AdminLayout from "./components/admin/AdminLayout.jsx";
import AdminDashboard from "./routes/admin/AdminDashboard.jsx";
import AdminUserCreate from "./routes/admin/AdminUserCreate.jsx";
import AdminUserDetail from "./routes/admin/AdminUserDetail.jsx";
import AdminUsers from "./routes/admin/AdminUsers.jsx";
import AdminChapters from "./routes/admin/AdminChapters.jsx";
import AdminChapterDetail from "./routes/admin/AdminChapterDetail.jsx";
import Chat from "./routes/Chat.jsx";
import ResetPassword from "./routes/ResetPassword.jsx";
import {
  fetchMe,
  signInWithGoogle,
  logout,
  isAdmin,
  RESET_PASSWORD_PATH,
  SIGNIN_PATH,
} from "./lib/auth.js";
import { AuthContext } from "./lib/authContext.js";
import { clearVerifyBannerDismissals, readVerifyOutcome } from "./lib/verifyBanner.js";
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
 *
 * Phase 5 adds exactly one exception, the password-reset page, and it is
 * matched before the gate rather than inside <Routes> for the same reason:
 * the exception is a single visible line here, not a route that could be
 * copied into a more permissive pattern. See the comment at the match.
 */
export default function App() {
  const location = useLocation();
  const navigate = useNavigate();

  // Three states, not a boolean: "checking" has to be distinguishable from
  // "signed out", otherwise the sign-in screen flashes on every reload before
  // /auth/me answers, and a logged-in student sees a login form for a moment.
  const [authState, setAuthState] = useState("checking"); // checking|out|in
  const [user, setUser] = useState(null);
  const [signinBusy, setSigninBusy] = useState(false);
  const [signinError, setSigninError] = useState(null);

  // Something happened that the visitor has to read on the form itself, rather
  // than on the landing page: a session that expired mid-chapter, or a
  // sign-in that failed. Distinct from signinError because the boot-time
  // "server unreachable" also sets that, and a cold visitor whose /auth/me
  // timed out should still get the public page - the landing page needs no
  // backend, and the error still reaches them when they open the form.
  const [formRequired, setFormRequired] = useState(false);

  // Where a confirmation link landed us (?email_verifie=1|0), read once.
  const [verifyOutcome, setVerifyOutcome] = useState(readVerifyOutcome);

  // ...and then removed from the URL, so a reload or a bookmark does not
  // replay "ton adresse est confirmée" forever.
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (!params.has("email_verifie")) return;
    params.delete("email_verifie");
    const search = params.toString();
    navigate(
      { pathname: location.pathname, search: search ? `?${search}` : "" },
      { replace: true, state: location.state }
    );
  }, [location.pathname, location.search, location.state, navigate]);

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

  /** Any successful sign-in - Google, password, or a completed reset. */
  const handleSignedIn = useCallback((me) => {
    // A fresh login is a fresh chance to show the "confirme ton adresse"
    // reminder, and a link outcome shown on the sign-in screen has done its job.
    clearVerifyBannerDismissals();
    setVerifyOutcome(null);
    setSigninError(null);
    setFormRequired(false);
    setUser(me);
    setAuthState("in");
  }, []);

  const handleCredential = useCallback(
    async (idToken) => {
      setSigninBusy(true);
      setSigninError(null);
      try {
        handleSignedIn(await signInWithGoogle(idToken));
      } catch {
        setSigninError(SIGNIN_FAILED);
        setFormRequired(true);
      } finally {
        setSigninBusy(false);
      }
    },
    [handleSignedIn]
  );

  const handleLogout = useCallback(async () => {
    // Signed-out state first, network call second, and the order matters.
    //
    // Dropping the session here stops <Routes> rendering, which unmounts the
    // chat screen, which fires its cleanup and aborts any stream still in
    // flight - so an in-progress generation is cancelled *before* the request
    // to /auth/logout goes out, rather than continuing to bill Groq for the
    // length of that round trip. Before Phase 3b, App.jsx aborted here
    // directly; the controller now lives in the chat route, and this is what
    // reaches it.
    //
    // Resetting before awaiting is also the more honest failure mode: if the
    // logout request fails the cookie may survive server-side, but leaving
    // the UI signed in with a session it cannot rely on is worse than showing
    // the sign-in screen.
    //
    // localStorage chat history is deliberately NOT cleared - it is
    // browser-scoped, not identity-scoped, in this phase.
    clearVerifyBannerDismissals();
    setUser(null);
    setAuthState("out");
    // Deliberately signing out lands on the landing page, not on a login form:
    // nothing went wrong, and there is no message to read.
    setSigninError(null);
    setFormRequired(false);
    try {
      await logout();
    } catch {
      // Nothing useful to do: the UI is already signed out, and the cookie
      // expires on its own. Swallowed rather than surfaced on a screen the
      // student has just left.
    }
  }, []);

  /** The session went away mid-use (expired, or logged out in another tab). */
  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setAuthState("out");
    setSigninError("Ta session a expiré. Reconnecte-toi pour continuer.");
    // Straight to the form: the student was mid-chapter, and a landing page
    // pitching the app they were already using would bury the explanation.
    setFormRequired(true);
  }, []);

  const clearVerifyOutcome = useCallback(() => setVerifyOutcome(null), []);

  const auth = useMemo(
    () => ({
      user,
      logout: handleLogout,
      onUnauthorized: handleUnauthorized,
      verifyOutcome,
      clearVerifyOutcome,
    }),
    [user, handleLogout, handleUnauthorized, verifyOutcome, clearVerifyOutcome]
  );

  // THE ONE ROUTE REACHABLE WITHOUT A SESSION.
  //
  // The reset email's link has to work for a student who is signed out -
  // that is the whole point of a reset. It is matched here, above the gate,
  // by exact pathname: not a prefix, not a pattern, and not a <Route> inside
  // the authenticated tree. Everything else still falls through to the gate
  // below unchanged, so "/", "/chapitre/:id" and "/chat" are exactly as
  // private as before. Do not widen this into a list of "public" routes;
  // add a second exception the same explicit way, or not at all.
  //
  // ResetPassword renders no authenticated component and calls no
  // authenticated endpoint; it only posts the emailed token.
  if (location.pathname === RESET_PASSWORD_PATH) {
    return (
      <ResetPassword
        onSignedIn={(me) => {
          handleSignedIn(me);
          navigate("/", { replace: true });
        }}
      />
    );
  }

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

  // Note there is still no <Routes> in this branch: a signed-out visitor gets
  // one of exactly two public screens for every path, including one typed
  // straight into the bar, and no authenticated route is ever mounted to flash
  // its content first. The gate is unchanged - what a signed-out visitor sees
  // instead of the app got a second screen, not a hole.
  if (authState === "out") {
    // The landing page is the default: a visitor who has never heard of Fahem
    // is shown what it is before being asked for an e-mail address. The form
    // is one click away, and three things send a visitor straight to it:
    //
    //   - /connexion, the path the landing page's buttons navigate to;
    //   - a router state carrying an authMode - a dead reset link asking for
    //     "forgot", or "Créer un compte" asking for the signup tab;
    //   - formRequired, i.e. an action of the student's own failed and the
    //     explanation lives on the form: an expired session (the pathname is
    //     an app route, not /connexion, so only this catches it) or a rejected
    //     sign-in. A marketing page in place of either would drop the one
    //     sentence saying what just happened.
    const wantsForm =
      location.pathname === SIGNIN_PATH || location.state?.authMode || formRequired;
    if (!wantsForm) return <Landing />;

    return (
      <SignInScreen
        onCredential={handleCredential}
        onSignedIn={handleSignedIn}
        busy={signinBusy}
        error={signinError}
        verifyOutcome={verifyOutcome}
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

        {/* The admin console (Phase 8): a sibling of AppLayout, not a child,
            so it gets its own shell and none of the student sidebar.

            Registered only for an admin, not registered-and-guarded: for
            anyone else every /admin/* path is simply unknown and the
            catch-all above sends it to "/", so no console component mounts
            for a student at all. AdminLayout then re-checks with the server,
            and every API call behind it is checked again - those are the
            checks that actually hold. */}
        {isAdmin(user) && (
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="utilisateurs" element={<AdminUsers />} />
            <Route path="utilisateurs/nouveau" element={<AdminUserCreate />} />
            <Route path="utilisateurs/:id" element={<AdminUserDetail />} />
            <Route path="chapitres" element={<AdminChapters />} />
            <Route path="chapitres/:id" element={<AdminChapterDetail />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Route>
        )}
      </Routes>
    </AuthContext.Provider>
  );
}
