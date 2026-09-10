import { createContext, useContext } from "react";

/**
 * The signed-in user and the two things any authenticated screen may need to
 * do about the session.
 *
 * Context rather than prop-drilling: the auth check lives at the router's
 * root (App.jsx) while the pages that need it - the layout's logout button,
 * the chat's expired-session handling, the chapter fetches' 401 branch - are
 * several levels down and on different routes. Threading three props through
 * every route element would be noise, and would make it easy for a new route
 * to quietly not handle 401 at all.
 *
 * onUnauthorized is deliberately part of the same contract as `user`: a
 * screen that can read the identity is a screen that can discover the session
 * is gone, and both belong in one place so every route handles it the same
 * way rather than inventing its own error path.
 */
export const AuthContext = createContext({
  user: null,
  logout: () => {},
  onUnauthorized: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}
