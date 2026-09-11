import Button from "./Button.jsx";

/**
 * What a screen shows when it has nothing to show.
 *
 * Three places did this three ways - the chat's centred prompt, the
 * sidebar's "Aucune discussion" line and the chapter's "Aucun exercice" line
 * (audit P2-10, P3-1). One primitive, two sizes:
 *
 *   md - a screen-level prompt: a title, a line of explanation, maybe an action
 *   sm - a one-line "nothing here" inside a panel or list
 *
 * `titleAs` exists because the chat's title is a real <h2> in the page
 * outline (Step 2) and must stay one; elsewhere the title is just text.
 *
 * `icon` is accepted and rendered aria-hidden, but nothing passes one yet: the
 * app's glyph icons are their own open question (audit P3-2), and picking an
 * icon set is not something to do in passing inside a component refactor.
 */
export default function EmptyState({
  icon,
  title,
  titleAs: Title = "p",
  action,
  size = "md",
  className = "",
  children,
}) {
  return (
    <div
      className={`empty-state empty-state-${size}${className ? ` ${className}` : ""}`}
    >
      {icon && (
        <span className="empty-state-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      {title && <Title className="empty-state-title">{title}</Title>}
      {children && <p className="empty-state-body">{children}</p>}
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
