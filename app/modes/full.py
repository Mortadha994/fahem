"""« La solution »: the exercise solved outright, in one answer.

The default mode, and the one every other mode falls back to: a request in a
mode that is switched off, or that the mode does not claim, is answered here.
The prompt route is the gatekeeper's own (PROBLEM, QUESTION or CODE), or
FOLLOW_UP for a short message continuing the discussion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core import models

if TYPE_CHECKING:
    from app.main import SolveRequest

MODE = "full"
# The route a cached full solution is saved and reported under.
ROUTE = "PROBLEM"


def requested(payload: SolveRequest) -> bool:
    """The student asked for the solution itself."""
    return payload.mode == MODE


def prompt_route(route: str, follow: bool) -> str:
    """The prompt for a request no other mode took: FOLLOW_UP for a short
    message continuing the discussion, otherwise the classifier's route."""
    return "FOLLOW_UP" if follow else route


def cache_target(payload: SolveRequest) -> tuple[str, int] | None:
    """(mode, step) of the stored answer that can stand in for this request:
    the full solution, whose whole input is the statement."""
    if requested(payload):
        return (models.ANSWER_MODE_FULL, 0)
    return None
