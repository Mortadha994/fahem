import { useSyncExternalStore } from "react";

// Light / dark theme.
//
// The resolved theme lives on <html data-theme="light|dark">, and every theme
// rule in the CSS keys off that attribute instead of a prefers-color-scheme
// media query - a media query cannot be overridden by a button, an attribute
// can. index.html sets it before the first paint (same logic as below), so
// the page never flashes the wrong theme.
//
// Until the student picks, the theme follows the device and keeps following
// it live. Once they press the button, their choice is remembered in this
// browser and wins over the device.

const KEY = "fahem.theme";
const EVENT = "fahem-theme-change";
const media = () => window.matchMedia?.("(prefers-color-scheme: dark)");

/** The saved choice, or null when the student has not picked one. */
export function storedTheme() {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function systemTheme() {
  return media()?.matches ? "dark" : "light";
}

function apply(theme) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  // Native controls, scrollbars and autofill follow too.
  root.style.colorScheme = theme;
  window.dispatchEvent(new Event(EVENT));
}

/** Remembers and applies an explicit choice. */
export function setTheme(theme) {
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    // Blocked storage: the choice still applies for this page view.
  }
  apply(theme);
}

/**
 * Keeps an unset theme in step with the device while the page is open.
 * Called once from main.jsx; index.html has already applied the first value.
 */
export function initTheme() {
  if (!document.documentElement.dataset.theme) apply(storedTheme() ?? systemTheme());
  media()?.addEventListener("change", () => {
    if (!storedTheme()) apply(systemTheme());
  });
}

function subscribe(callback) {
  window.addEventListener(EVENT, callback);
  return () => window.removeEventListener(EVENT, callback);
}

/** The theme currently on the page, re-rendering when it changes. */
export function useTheme() {
  return useSyncExternalStore(
    subscribe,
    () => document.documentElement.dataset.theme ?? "light",
    () => "light"
  );
}
