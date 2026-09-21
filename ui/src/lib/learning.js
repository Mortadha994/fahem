/**
 * Mode guidé and Vérifier ma réponse, on the chat's side.
 *
 * The server decides the prompt (app/main.py learning_route); the chat keeps where
 * a discussion is: the step of the guided exercise under way and the student
 * message it started from - read back from the answers themselves, so a
 * reloaded discussion resumes at the right step.
 */

export const GUIDED_STEPS = [
  { step: 1, label: "Comprendre" },
  { step: 2, label: "Indice" },
  { step: 3, label: "Squelette" },
  { step: 4, label: "Solution" },
];

export const ACTION_LABELS = {
  next_step: "Indice suivant",
  show_solution: "Voir la solution",
};

// Must match prompts.CHECK_CORRECTION_HEADING.
export const CORRECTION_HEADING = "### Correction complète";

export const VERDICTS = {
  correct: { label: "Correct", tone: "success", icon: "✓" },
  presque: { label: "Presque", tone: "warning", icon: "≈" },
  a_revoir: { label: "À revoir", tone: "danger", icon: "✗" },
};

/**
 * The guided exercise under way in these messages: { step, exerciseId,
 * exercise } from the latest guided answer, or null. A checked solution in
 * between does not end it (the student proposed a solution mid-exercise);
 * any other answer does.
 */
export function guidedState(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const msg = messages[i];
    if (msg.role !== "assistant") continue;
    if (msg.check || msg.route === "CHECK") continue;
    if (!msg.guided?.step) return null;
    const start = messages.find((m) => m.id === msg.guided.exerciseId);
    return {
      step: msg.guided.step,
      exerciseId: msg.guided.exerciseId,
      exercise: start?.content || "",
    };
  }
  return null;
}

// Must match prompts.PRACTICE_HEADING.
export const PRACTICE_HEADING = "### Exercice similaire";

export const PRACTICE_LEVELS = [
  { value: "easier", label: "Plus facile" },
  { value: "same", label: "Même niveau" },
  { value: "harder", label: "Plus difficile" },
];

const BUTTON_TEXTS = new Set(["Indice suivant", "Voir la solution"]);

/**
 * The exercise the discussion is about, for "Exercice similaire": the guided
 * exercise under way, else the latest generated exercise, else the latest
 * student message that was answered as a new statement.
 */
export function currentExercise(messages) {
  const guided = guidedState(messages);
  if (guided?.exercise) return guided.exercise;
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const msg = messages[i];
    if (msg.role !== "assistant" || !msg.content) continue;
    if (msg.practice) return practiceStatement(msg.content);
    if (msg.route === "PROBLEM" || msg.route === "GUIDED") {
      const asked = messages[i - 1];
      if (asked?.role === "user" && asked.content && !BUTTON_TEXTS.has(asked.content))
        return asked.content;
    }
  }
  const first = messages.find(
    (m) => m.role === "user" && m.content && m.mode !== "check"
  );
  return first?.content ?? "";
}

/** The statement of a generated exercise, without its heading line. */
export function practiceStatement(content) {
  const at = content.indexOf(PRACTICE_HEADING);
  const body = at < 0 ? content : content.slice(at).split("\n").slice(1).join("\n");
  return body.trim();
}

/** A CHECK answer as { review, correction } - the correction is folded away. */
export function splitCorrection(content) {
  const at = content.indexOf(CORRECTION_HEADING);
  if (at < 0) return { review: content, correction: "" };
  return {
    review: content.slice(0, at).trimEnd(),
    correction: content.slice(at + CORRECTION_HEADING.length).trim(),
  };
}

/** The verdict line is shown as a badge; drop it from the text below it. */
export function withoutVerdictLine(text) {
  return text.replace(/^\s*\**\s*verdict\s*[:：][^\n]*\n+/i, "");
}
