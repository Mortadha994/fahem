import { createContext, useContext } from "react";

/**
 * The chat's session list, shared between the chat screen and the app
 * sidebar.
 *
 * It used to live inside Chat.jsx, which was fine while the session history
 * had its own sidebar rendered by that route. Phase 6 moves the history into
 * the one app sidebar (AppLayout), so two very different parts of the tree now
 * read and write the same list - which is what a context is for. Same shape as
 * authContext.js: the context and its hook here, the stateful provider in a
 * component file.
 */
export const ChatSessionsContext = createContext(null);

export function useChatSessions() {
  const value = useContext(ChatSessionsContext);
  if (!value) {
    // A clearer failure than "cannot read property of null" three frames deep.
    throw new Error("useChatSessions must be used inside <ChatSessionsProvider>");
  }
  return value;
}
