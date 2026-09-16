import { createContext, useContext } from "react";

/**
 * The console's notifications, shown at the bottom of the page (Toaster.jsx).
 *
 *   const toast = useToast();
 *   toast.success("Réglages enregistrés.");
 *   toast.error("Impossible d'enregistrer.");
 *   toast.success("IA mise en pause.", { action: { label: "Annuler", run } });
 *
 * Every call returns the toast's id; toast.dismiss(id) closes it early.
 * Outside a Toaster the calls do nothing, so a component can use them
 * unconditionally.
 */
const noop = () => null;

export const ToastContext = createContext({
  success: noop,
  error: noop,
  info: noop,
  dismiss: noop,
});

export const useToast = () => useContext(ToastContext);
