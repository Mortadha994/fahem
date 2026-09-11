/**
 * The one button.
 *
 * Replaces five independent .btn-* rules that each restated their own padding,
 * radius and colour (audit P2-2). Variants carry intent, not appearance:
 *
 *   primary   - the one action a screen is for (Envoyer)
 *   secondary - a real action that is not the main one (Nouvelle discussion)
 *   ghost     - chrome: no fill, no border until hovered (the burger)
 *   danger    - an action that destroys something (confirming a delete)
 *
 * Both sizes keep the 44px hit area from Step 3. `sm` is smaller type and
 * tighter padding, not a smaller target - a small-looking control on a phone
 * still has to be hittable, so the floor is a property of every button rather
 * than something each call site has to remember.
 *
 * `className` is for placement only (width, margin, show/hide at a
 * breakpoint). Anything that changes how the button looks belongs in a variant.
 */
export default function Button({
  variant = "secondary",
  size = "md",
  className = "",
  type = "button",
  ...rest
}) {
  const classes = `btn btn-${variant} btn-${size}${className ? ` ${className}` : ""}`;
  return <button type={type} className={classes} {...rest} />;
}
