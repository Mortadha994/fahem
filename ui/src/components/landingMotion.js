import { animate, hover, inView, press, scroll, springValue } from "motion";

/*
 * Everything on the landing page that needs more than CSS: springs, effects
 * bound to scroll, counters, the cursor-following cards and buttons.
 *
 * This file is only ever reached through a dynamic import() in Landing.jsx, so
 * Motion lands in its own chunk: the student app and the admin console never
 * download it, and a visitor who asked for reduced motion does not either
 * (Landing.jsx skips the import entirely in that mode).
 *
 * The page is complete without this module. Nothing is hidden by CSS waiting
 * for a script: an element is only hidden here, by this code, right before
 * this code registers the animation that brings it back. If the chunk fails to
 * load, the visitor gets a static page, never an empty one.
 *
 * enhanceLanding() returns a cleanup that stops every animation, listener and
 * spring it started, and clears the inline styles it wrote.
 */

// Springs are described by feel (visualDuration + bounce) for one-shot
// entrances, and by physics for values that follow the pointer - the Motion
// docs recommend stiffness/damping there, since those carry the velocity of
// the previous movement into the next one.
const ENTRANCE = { type: "spring", visualDuration: 0.6, bounce: 0.28 };
const FOLLOW = { stiffness: 220, damping: 20, mass: 0.6 };
const PRESS = { stiffness: 600, damping: 30 };

const RISE_PX = 28;

const finePointer = () =>
  typeof window.matchMedia === "function" &&
  window.matchMedia("(hover: hover) and (pointer: fine)").matches;

/** Below the fold at the moment we run? Only those are hidden for a reveal:
 *  hiding something the visitor is already looking at would read as a flicker. */
const belowFold = (el) => el.getBoundingClientRect().top > window.innerHeight;

const staggerIndex = (el) => Number(el.style.getPropertyValue("--i")) || 0;

/*
 * Reveal on scroll, with a spring.
 *
 * The rise is written to the `translate` and `opacity` properties rather than
 * through a Motion transform: the feature cards own `transform` for their tilt
 * and the chapter cards have a resting opacity below 1, and neither should be
 * clobbered by an entrance. So the spring drives one 0 -> 1 progress value and
 * onUpdate maps it - which also lets the overshoot show as a small upward
 * bounce while opacity simply clamps at the element's own resting value.
 */
function setupReveals(root, cleanups) {
  for (const el of root.querySelectorAll("[data-reveal]")) {
    if (!belowFold(el)) continue;

    const rest = parseFloat(getComputedStyle(el).opacity) || 1;
    const transition = el.style.transition;
    // A CSS transition on translate (the cards' hover lift) would smooth each
    // spring frame into a lag; it is put back once the entrance is over.
    el.style.transition = "none";
    el.style.opacity = "0";
    el.style.translate = `0 ${RISE_PX}px`;

    const restore = () => {
      el.style.opacity = "";
      el.style.translate = "";
      el.style.transition = transition;
    };

    let running;
    const stop = inView(
      el,
      () => {
        running = animate(0, 1, {
          ...ENTRANCE,
          delay: staggerIndex(el) * 0.08,
          onUpdate: (v) => {
            el.style.opacity = String(Math.min(rest, Math.max(0, v * rest)));
            el.style.translate = `0 ${((1 - v) * RISE_PX).toFixed(2)}px`;
          },
        });
        running.then(restore);
        // The step numbers land a beat after their step, with more bounce:
        // the eye follows the numbers down the page.
        const badge = el.querySelector(".lp-step-n");
        if (badge) {
          animate(
            badge,
            { scale: [0.4, 1], rotate: [-25, 0] },
            {
              type: "spring",
              visualDuration: 0.5,
              bounce: 0.5,
              delay: 0.15 + staggerIndex(el) * 0.08,
            }
          );
        }
      },
      // Slightly inside the bottom edge: the entrance should be finishing as
      // the element arrives, not starting once it is already centred.
      { margin: "0px 0px -10% 0px" }
    );

    cleanups.push(() => {
      stop();
      running?.stop();
      restore();
    });
  }
}

/*
 * The three numbers count up from zero when they arrive. The visible digits
 * are aria-hidden in Landing.jsx and the real value sits beside them for
 * screen readers, so nobody is read "43 extraits" halfway through.
 */
function setupCounters(root, cleanups) {
  for (const el of root.querySelectorAll("[data-count]")) {
    const target = Number(el.dataset.count);
    if (!Number.isFinite(target) || !belowFold(el)) continue;
    el.textContent = "0";

    let running;
    const stop = inView(el, () => {
      running = animate(0, target, {
        // Longer for bigger numbers, so 2 does not blink past and 117 does
        // not drag.
        duration: 0.5 + Math.min(target, 120) / 120,
        ease: "easeOut",
        onUpdate: (v) => {
          el.textContent = String(Math.round(v));
        },
      });
    });
    cleanups.push(() => {
      stop();
      running?.stop();
      el.textContent = String(target);
    });
  }
}

/*
 * Scroll-linked effects. scroll(animate(...)) is the documented pairing: where
 * the browser has ScrollTimeline, Motion hands these to it and they run off
 * the main thread.
 */
function setupScroll(root, cleanups) {
  const progress = root.querySelector(".lp-progress");
  if (progress) {
    cleanups.push(scroll(animate(progress, { scaleX: [0, 1] }, { ease: "linear" })));
  }

  // The syntax glyphs drift up slower than the page: depth, without moving
  // the blurred blobs (their own keyframes own their transform).
  const glyphs = root.querySelector(".aurora-glyphs");
  if (glyphs) {
    cleanups.push(scroll(animate(glyphs, { y: [0, -220] }, { ease: "linear" })));
  }

  // The hero's two columns leave at different speeds as the page moves on.
  const hero = root.querySelector(".lp-hero");
  const copy = root.querySelector(".lp-hero-copy");
  const visual = root.querySelector(".lp-hero-visual");
  if (hero && copy && visual) {
    const offset = ["start start", "end start"];
    cleanups.push(
      scroll(animate(copy, { y: [0, 40] }, { ease: "linear" }), {
        target: hero,
        offset,
      }),
      scroll(animate(visual, { y: [0, 110], scale: [1, 0.94] }, { ease: "linear" }), {
        target: hero,
        offset,
      })
    );
  }

  // The line between the three steps fills as the steps pass the middle of
  // the screen.
  const steps = root.querySelector(".lp-steps-wrap");
  const fill = root.querySelector(".lp-steps-fill");
  if (steps && fill) {
    cleanups.push(
      scroll(animate(fill, { scaleX: [0, 1] }, { ease: "linear" }), {
        target: steps,
        offset: ["start 80%", "end 55%"],
      })
    );
  }
}

/*
 * The nav shows where you are: a soft pill slides under the link of the
 * section currently crossing the upper middle of the screen.
 */
function setupNavSpy(root, cleanups) {
  const nav = root.querySelector(".lp-nav");
  const pill = nav?.querySelector(".lp-nav-pill");
  if (!nav || !pill) return;

  const links = new Map(
    [...nav.querySelectorAll('a[href^="#"]')].map((a) => [
      a.getAttribute("href").slice(1),
      a,
    ])
  );
  let active = null;

  const place = (instant) => {
    const link = active && links.get(active);
    for (const [id, a] of links) a.toggleAttribute("data-active", id === active);
    if (!link) {
      animate(pill, { opacity: 0 }, { duration: 0.2 });
      return;
    }
    const pad = 12;
    animate(
      pill,
      { x: link.offsetLeft - pad, width: link.offsetWidth + pad * 2, opacity: 1 },
      instant ? { duration: 0 } : { type: "spring", visualDuration: 0.35, bounce: 0.2 }
    );
  };

  for (const id of links.keys()) {
    const section = root.querySelector(`#${id}`);
    if (!section) continue;
    cleanups.push(
      inView(
        section,
        () => {
          const wasHidden = active === null;
          active = id;
          place(wasHidden);
          return () => {
            if (active !== id) return;
            active = null;
            place(false);
          };
        },
        // A thin band across the upper middle: one section at a time.
        { margin: "-40% 0px -55% 0px" }
      )
    );
  }

  const onResize = () => place(true);
  window.addEventListener("resize", onResize);
  cleanups.push(() => {
    window.removeEventListener("resize", onResize);
    for (const a of links.values()) a.removeAttribute("data-active");
  });
}

/*
 * Feature cards lean toward the cursor on a spring. The tilt owns
 * `transform`; the hover lift in CSS uses `translate`, so the two compose.
 * Mouse only - on touch there is no hover to lean toward.
 */
function setupTilt(root, cleanups) {
  if (!finePointer()) return;
  for (const card of root.querySelectorAll(".lp-card")) {
    const rx = springValue(0, FOLLOW);
    const ry = springValue(0, FOLLOW);
    const render = () => {
      card.style.transform = `perspective(900px) rotateX(${rx.get().toFixed(2)}deg) rotateY(${ry.get().toFixed(2)}deg)`;
    };
    const offX = rx.on("change", render);
    const offY = ry.on("change", render);

    const move = (event) => {
      if (event.pointerType !== "mouse") return;
      const r = card.getBoundingClientRect();
      const nx = ((event.clientX - r.left) / r.width) * 2 - 1;
      const ny = ((event.clientY - r.top) / r.height) * 2 - 1;
      rx.set(-ny * 5);
      ry.set(nx * 6);
    };
    const leave = () => {
      rx.set(0);
      ry.set(0);
    };
    card.addEventListener("pointermove", move);
    card.addEventListener("pointerleave", leave);

    cleanups.push(() => {
      card.removeEventListener("pointermove", move);
      card.removeEventListener("pointerleave", leave);
      offX();
      offY();
      rx.destroy();
      ry.destroy();
      card.style.transform = "";
    });
  }
}

/*
 * Buttons: the big calls to action are pulled a few pixels toward the cursor,
 * and every primary button gives under a press. Written to `translate` and
 * `scale` so the CSS hover lift (transform) still applies on top.
 */
function setupButtons(root, cleanups) {
  const magnetic = finePointer();
  for (const btn of root.querySelectorAll(".btn-primary")) {
    const x = springValue(0, FOLLOW);
    const y = springValue(0, FOLLOW);
    const s = springValue(1, PRESS);
    const render = () => {
      btn.style.translate = `${x.get().toFixed(2)}px ${y.get().toFixed(2)}px`;
      btn.style.scale = s.get().toFixed(3);
    };
    const offs = [
      x.on("change", render),
      y.on("change", render),
      s.on("change", render),
    ];

    const clamp = (v, max) => Math.max(-max, Math.min(max, v));
    const move = (event) => {
      if (event.pointerType !== "mouse") return;
      const r = btn.getBoundingClientRect();
      x.set(clamp((event.clientX - (r.left + r.width / 2)) * 0.25, 8));
      y.set(clamp((event.clientY - (r.top + r.height / 2)) * 0.35, 5));
    };
    const leave = () => {
      x.set(0);
      y.set(0);
    };
    const pull = magnetic && btn.classList.contains("lp-btn-lg");
    if (pull) {
      btn.addEventListener("pointermove", move);
      btn.addEventListener("pointerleave", leave);
    }

    const stopPress = press(btn, () => {
      s.set(0.95);
      return () => s.set(1);
    });

    cleanups.push(() => {
      if (pull) {
        btn.removeEventListener("pointermove", move);
        btn.removeEventListener("pointerleave", leave);
      }
      stopPress();
      offs.forEach((off) => off());
      [x, y, s].forEach((v) => v.destroy());
      btn.style.translate = "";
      btn.style.scale = "";
    });
  }
}

/*
 * The notation correction (SyntaxFix in Landing.jsx): `=` is struck out, the
 * course's `←` springs in, the check lands. The markup's resting state is the
 * finished correction, so without this nothing is missing. It plays once when
 * it is well in view, and again when the mouse comes back over it.
 */
function setupFixes(root, cleanups) {
  for (const fix of root.querySelectorAll(".lp-fix")) {
    const strike = fix.querySelector(".lp-fix-strike");
    const arrow = fix.querySelector(".lp-fix-arrow");
    const check = fix.querySelector(".lp-fix-check");
    const right = fix.querySelector(".lp-fix-right");
    if (!strike || !arrow || !check || !right) continue;

    let running = null;
    const play = () => {
      if (running) return;
      running = animate([
        [strike, { scaleX: [0, 1] }, { duration: 0.4, ease: "easeOut", at: 0.25 }],
        [right, { opacity: [0.4, 1] }, { duration: 0.3, at: "<" }],
        [
          arrow,
          { scale: [0, 1], rotate: [-140, 0] },
          { type: "spring", visualDuration: 0.5, bounce: 0.45, at: "+0.05" },
        ],
        [
          check,
          { scale: [0, 1] },
          { type: "spring", visualDuration: 0.4, bounce: 0.55, at: "-0.2" },
        ],
      ]);
      running.then(() => {
        running = null;
      });
    };

    // Below the fold, start from the uncorrected line so the first play does
    // not jump backwards from the finished state as it scrolls in.
    if (belowFold(fix)) {
      animate(strike, { scaleX: 0 }, { duration: 0 });
      animate([arrow, check], { scale: 0 }, { duration: 0 });
      animate(right, { opacity: 0.4 }, { duration: 0 });
    }

    const stopView = inView(fix, play, { amount: 0.6 });
    const stopHover = hover(fix, play);
    cleanups.push(() => {
      stopView();
      stopHover();
      running?.stop();
    });
  }
}

export function enhanceLanding(root) {
  const cleanups = [];
  setupReveals(root, cleanups);
  setupCounters(root, cleanups);
  setupScroll(root, cleanups);
  setupNavSpy(root, cleanups);
  setupTilt(root, cleanups);
  setupButtons(root, cleanups);
  setupFixes(root, cleanups);
  return () => cleanups.forEach((fn) => fn());
}
