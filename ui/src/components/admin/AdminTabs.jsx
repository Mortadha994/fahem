import { useId, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import * as m from "motion/react-m";

/**
 * Tabs for a console page, kept in the URL (?onglet=...) so a tab survives a
 * reload and can be linked to (the sidebar's AI status card opens
 * /admin/ia?onglet=controles).
 *
 * WAI-ARIA tabs: arrow keys, Home and End move between tabs. The selected
 * tab's background slides to the new one (Motion layoutId, the shared-layout
 * pattern) and the panel content cross-fades (AnimatePresence mode="wait").
 *
 *   <AdminTabs tabs={[{ id, label, Icon, badge }]} param="onglet">
 *     {(tabId) => ...panel for that tab...}
 *   </AdminTabs>
 */
const PANEL = {
  hidden: { opacity: 0, y: 6 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.18, ease: "easeOut", staggerChildren: 0.05 },
  },
  exit: { opacity: 0, y: -4, transition: { duration: 0.12 } },
};

export default function AdminTabs({ tabs, param = "onglet", label, children }) {
  const [params, setParams] = useSearchParams();
  const group = useId();
  const refs = useRef({});
  const wanted = params.get(param);
  const current = tabs.some((t) => t.id === wanted) ? wanted : tabs[0].id;

  function select(id) {
    const next = new URLSearchParams(params);
    if (id === tabs[0].id) next.delete(param);
    else next.set(param, id);
    setParams(next, { replace: true });
  }

  function onKeyDown(event) {
    const index = tabs.findIndex((t) => t.id === current);
    const moves = {
      ArrowRight: index + 1,
      ArrowLeft: index - 1,
      Home: 0,
      End: tabs.length - 1,
    };
    if (!(event.key in moves)) return;
    event.preventDefault();
    const target = tabs[(moves[event.key] + tabs.length) % tabs.length];
    select(target.id);
    refs.current[target.id]?.focus();
  }

  return (
    <div className="adm-tabs">
      <div
        className="adm-tablist"
        role="tablist"
        aria-label={label}
        onKeyDown={onKeyDown}
      >
        {tabs.map(({ id, label: text, Icon, badge }) => {
          const selected = id === current;
          return (
            <button
              key={id}
              ref={(el) => (refs.current[id] = el)}
              id={`${group}-tab-${id}`}
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`${group}-panel-${id}`}
              tabIndex={selected ? 0 : -1}
              className={`adm-tab${selected ? " is-on" : ""}`}
              onClick={() => select(id)}
            >
              {selected && (
                <m.span
                  layoutId={`${group}-tab-bg`}
                  className="adm-tab-bg"
                  transition={{ type: "spring", visualDuration: 0.3, bounce: 0.15 }}
                />
              )}
              {Icon && <Icon size={16} />}
              <span>{text}</span>
              {badge}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <m.div
          key={current}
          id={`${group}-panel-${current}`}
          role="tabpanel"
          aria-labelledby={`${group}-tab-${current}`}
          className="adm-tabpanel"
          // Variant names, not a plain animate object: panel content uses the
          // console's `rise` variants, which only play if the "show" label
          // reaches them through this element.
          variants={PANEL}
          initial="hidden"
          animate="show"
          exit="exit"
        >
          {children(current)}
        </m.div>
      </AnimatePresence>
    </div>
  );
}
