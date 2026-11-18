"""« Mode guidé »: the exercise solved with the student, one step at a time.

Steps 1-3 lead towards the solution without giving it (understand, hint,
skeleton with blanks); step 4 is the full solution. The step is decided here,
from the chat's buttons ("Indice suivant" / "Voir la solution") and the step
the discussion is at - never by the model, so it cannot skip ahead because a
student insists. The prompts themselves are prompts.GUIDED_*.

The admin switch `guided_mode_enabled` turns the mode off: a guided request
is then answered as a full solution (app/modes/full.py).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core import models, runtime_settings
from app.grading import session_memory

if TYPE_CHECKING:
    from app.main import SolveRequest

log = logging.getLogger("fahem.api")

MODE = "guided"
ROUTE = "GUIDED"
LAST_STEP = 4


def enabled() -> bool:
    return bool(runtime_settings.get("guided_mode_enabled"))


def requested(payload: SolveRequest) -> bool:
    """The request is in guided mode and the mode is switched on."""
    return payload.mode == MODE and enabled()


def skips_classifier(payload: SolveRequest, memory: list, note: str | None) -> bool:
    """Whether the gatekeeper's call can be skipped: a guided exercise's
    buttons ("Indice suivant" is not an exercise), or a short reply in the
    middle of one ("deux entiers ?"), which the classifier could decline as
    off topic. Only for an exercise the discussion vouches for."""
    if not requested(payload) or not payload.exercise_trusted:
        return False
    return bool(payload.action) or bool(
        payload.step
        and session_memory.is_follow_up(payload.problem, memory, note)
        and not session_memory.looks_like_statement(payload.problem)
    )


def route(
    payload: SolveRequest, route: str, follow: bool, check_on: bool
) -> tuple[str, int | None, bool] | None:
    """(prompt route, step, whether a guided exercise starts here), or None
    when guided mode does not claim the request and it is answered normally.

    A new statement starts at step 1; a button moves the step on; anything
    else in an exercise under way stays at its step - except pasted code,
    which is checked when "Vérifier ma réponse" is on."""
    if not requested(payload):
        return None
    in_exercise = bool(payload.step and payload.exercise) and payload.exercise_trusted
    if in_exercise and payload.action == "show_solution":
        return ROUTE, LAST_STEP, False
    if in_exercise and payload.action == "next_step":
        return ROUTE, min(LAST_STEP, payload.step + 1), False
    if route == "PROBLEM" and not follow:
        return ROUTE, 1, True
    if in_exercise:
        if route == "CODE" and check_on:
            return "CHECK", None, False
        return ROUTE, payload.step, False
    return None


def cache_target(payload: SolveRequest) -> tuple[str, int] | None:
    """(mode, step) of the stored answer that can stand in for this request:
    only the first step of a new statement, not a button (step/action unset).
    Steps 2-4 depend on the discussion and are never cached."""
    if requested(payload) and not payload.step and not payload.action:
        return (models.ANSWER_MODE_GUIDED, 1)
    return None


def state(step: int, exercise_id: str | None) -> dict:
    """The guided fields an answer carries (meta / done frames, saved message)."""
    return {"step": step, "exerciseId": exercise_id}


def is_reply(payload: SolveRequest, starts_exercise: bool) -> bool:
    """Neither a new exercise nor a button: the student answering the tutor's
    question at this step."""
    return not starts_exercise and not payload.action


def review(guided: dict, has_solution: bool) -> tuple[dict, bool]:
    """(guided fields to save, whether the answer counts as a solution).

    A hint (steps 1-3) is not a solution to vouch for. One that holds a full
    solution table broke the step rules: flagged `leak`, kept visible in the
    logs and the console."""
    if guided["step"] >= LAST_STEP:
        return guided, has_solution
    if has_solution:
        log.warning("guided step %d answered with a full solution table", guided["step"])
        return {**guided, "leak": True}, False
    return guided, False
