import Button from "./Button.jsx";

/**
 * One block for "something went wrong" (and, rarely, "note this").
 *
 * Replaces three implementations of the same red-on-pink box - .error in the
 * chat, .page-error on the routes, .signin-error on the sign-in card - each
 * with its own padding, radius and type size (audit P2-4).
 *
 * `action` is an optional { label, onClick } rendered as a small button after
 * the message - the hook for "Réessayer" (audit P2-10). No call site passes one
 * yet: wiring a retry means re-running a route's fetch, which is behaviour,
 * and belongs with the states work rather than this refactor.
 *
 * role defaults from the tone: an error interrupts (alert), anything softer
 * waits its turn (status). A caller can still override it.
 */
export default function Alert({
  tone = "danger",
  action,
  className = "",
  children,
  ...rest
}) {
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={`alert alert-${tone}${className ? ` ${className}` : ""}`}
      {...rest}
    >
      <p className="alert-body">{children}</p>
      {action && (
        <Button variant="secondary" size="sm" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
