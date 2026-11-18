"""Tests for app/modes: how « La solution » and « Mode guidé » route a request,
which cached answer they accept, and how a guided answer is judged. Offline:
no database, Redis or Groq - the admin switches are patched in.

    python -m tests.test_modes
"""

from __future__ import annotations

from types import SimpleNamespace

from app.core import models, runtime_settings
from app.modes import full, guided

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(("[PASS] " if ok else "[FAIL] ") + name + (f"  -> {detail!r}" if not ok else ""))


def payload(**kw) -> SimpleNamespace:
    base = dict(
        mode="full",
        problem="Ecrire un algorithme qui lit un entier N et affiche son double.",
        step=None,
        action=None,
        exercise=None,
        exercise_trusted=False,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def with_guided(on: bool):
    real = runtime_settings.get
    runtime_settings.get = lambda key: on if key == "guided_mode_enabled" else real(key)
    return real


def main() -> None:
    real = with_guided(True)
    try:
        g = payload(mode="guided")
        under_way = payload(mode="guided", step=2, exercise="Lire N", exercise_trusted=True)

        check("full: claims mode full", full.requested(payload()))
        check("full: FOLLOW_UP for a follow-up", full.prompt_route("PROBLEM", True) == "FOLLOW_UP")
        check("full: classifier route otherwise", full.prompt_route("CODE", False) == "CODE")
        check(
            "full: caches the full solution",
            full.cache_target(payload()) == (models.ANSWER_MODE_FULL, 0),
        )
        check("full: not a guided request", full.cache_target(g) is None)

        check(
            "guided: new statement starts at 1",
            guided.route(g, "PROBLEM", False, True) == ("GUIDED", 1, True),
        )
        check(
            "guided: next_step moves on",
            guided.route(
                payload(**{**vars(under_way), "action": "next_step"}), "PROBLEM", True, True
            )
            == ("GUIDED", 3, False),
        )
        check(
            "guided: show_solution jumps to 4",
            guided.route(
                payload(**{**vars(under_way), "action": "show_solution"}), "PROBLEM", True, True
            )
            == ("GUIDED", 4, False),
        )
        check(
            "guided: next_step never passes 4",
            guided.route(
                payload(**{**vars(under_way), "step": 4, "action": "next_step"}),
                "PROBLEM",
                True,
                True,
            )
            == ("GUIDED", 4, False),
        )
        check(
            "guided: a reply stays at its step",
            guided.route(under_way, "QUESTION", True, True) == ("GUIDED", 2, False),
        )
        check(
            "guided: pasted code is checked",
            guided.route(under_way, "CODE", True, True) == ("CHECK", None, False),
        )
        check(
            "guided: ...unless check is off",
            guided.route(under_way, "CODE", True, False) == ("GUIDED", 2, False),
        )
        check(
            "guided: an untrusted exercise's button is not obeyed",
            guided.route(
                payload(
                    **{**vars(under_way), "exercise_trusted": False, "action": "show_solution"}
                ),
                "QUESTION",
                True,
                True,
            )
            is None,
        )
        check(
            "guided: a question outside an exercise falls back",
            guided.route(g, "QUESTION", False, True) is None,
        )
        check(
            "guided: full mode is never claimed",
            guided.route(payload(), "PROBLEM", False, True) is None,
        )

        check(
            "guided: first step is cached", guided.cache_target(g) == (models.ANSWER_MODE_GUIDED, 1)
        )
        check(
            "guided: a button is not cached",
            guided.cache_target(payload(mode="guided", action="next_step")) is None,
        )

        check(
            "guided: a button skips the classifier",
            guided.skips_classifier(
                payload(**{**vars(under_way), "action": "next_step"}), [], None
            ),
        )
        check("guided: a new statement does not", not guided.skips_classifier(g, [], None))

        state = guided.state(2, "ex-1")
        check("guided: a hint vouches for nothing", guided.review(state, False) == (state, False))
        check(
            "guided: a hint with a solution table is a leak",
            guided.review(state, True) == ({**state, "leak": True}, False),
        )
        last = guided.state(4, "ex-1")
        check("guided: step 4 is a solution", guided.review(last, True) == (last, True))
        check("guided: is_reply - an answer to the tutor", guided.is_reply(under_way, False))
        check(
            "guided: is_reply - not a button",
            not guided.is_reply(payload(action="next_step"), False),
        )

        with_guided(False)
        check(
            "switched off: guided claims nothing", guided.route(g, "PROBLEM", False, True) is None
        )
        check("switched off: no guided cache", guided.cache_target(g) is None)
        check(
            "switched off: buttons go through the classifier",
            not guided.skips_classifier(
                payload(**{**vars(under_way), "action": "next_step"}), [], None
            ),
        )
    finally:
        runtime_settings.get = real


if __name__ == "__main__":
    main()
    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")
    raise SystemExit(0 if all(results) else 1)
