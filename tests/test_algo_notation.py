"""Tests for app/grading/algo_notation.py: Python operators never reach the Algorithme
column, and nothing else is touched. Pure functions - no services.

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_algo_notation
"""

from __future__ import annotations

from app.grading import checker
from app.grading.algo_notation import normalize_answer, to_algo_notation

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def line(text: str) -> str:
    return to_algo_notation(text)[0]


def main() -> None:
    # --- the operators ------------------------------------------------------------
    cases = [
        ("Res ← X // Y", "Res ← X div Y"),
        ("Res ← X//Y", "Res ← X div Y"),
        ("R ← A % B", "R ← A mod B"),
        ("Q ← (A + B) // 2", "Q ← (A + B) div 2"),
        ("Si A == B Alors", "Si A = B Alors"),
        ("Si A != 0 Alors", "Si A ≠ 0 Alors"),
        ("Si moy >= 10 Alors", "Si moy ≥ 10 Alors"),
        ("Si moy <= 9 Alors", "Si moy ≤ 9 Alors"),
        ("x <- 5", "x ← 5"),
        ("Si (a > b) and (a > c) Alors", "Si (a > b) ET (a > c) Alors"),
        ("Si a < 0 or b < 0 Alors", "Si a < 0 OU b < 0 Alors"),
        ("trouve ← not fini", "trouve ← NON fini"),
        ("ok ← True", "ok ← Vrai"),
        ("ok ← False", "ok ← Faux"),
    ]
    for raw, expected in cases:
        got = line(raw)
        check(f"operator: {raw!r} -> {expected!r}", got == expected, got)

    # --- what must not change -------------------------------------------------------
    untouched = [
        "Res ← X div Y",
        "R ← A mod B",
        'Ecrire ("Remise de 5 %")',
        'Ecrire ("a // b donne le quotient")',
        'Ecrire ("Vrai ou False ?", x)',
        "note ← 12",  # "not" inside a word
        "ordre ← 3",  # "or" inside a word
        "Si x < y Alors",
        "Lire (A)",
        "Fin",
    ]
    for raw in untouched:
        got, n = to_algo_notation(raw)
        check(f"unchanged: {raw!r}", got == raw and n == 0, got)
    check(
        "strings kept, code around them fixed",
        line('Ecrire ("Reste :", A % B, " sur 100 %")')
        == 'Ecrire ("Reste :", A mod B, " sur 100 %")',
        line('Ecrire ("Reste :", A % B, " sur 100 %")'),
    )

    # --- in an answer: only the Algorithme column ----------------------------------
    answer = "\n".join(
        [
            "Le quotient s'obtient avec // en Python et div en algorithme.",
            "",
            "| Algorithme | Python |",
            "|---|---|",
            "| Début | |",
            "| Lire (X) | X = int(input()) |",
            "| Res ← X // Y | Res = X // Y |",
            "| R ← X % Y | R = X % Y |",
            '| Ecrire ("Reste :", R) | print("Reste :", R) |',
            "| Fin | |",
            "",
            "| Objet | Nature/type |",
            "|---|---|",
            "| X // Y | test |",
        ]
    )
    fixed, n = normalize_answer(answer)
    rows = fixed.split("\n")
    check("answer: two operators rewritten", n == 2, n)
    check(
        "answer: Algorithme cell uses div, Python cell keeps //",
        "| Res ← X div Y | Res = X // Y |" in rows,
        [r for r in rows if "Res" in r],
    )
    check(
        "answer: Algorithme cell uses mod, Python cell keeps %",
        "| R ← X mod Y | R = X % Y |" in rows,
        [r for r in rows if "R ←" in r],
    )
    check("answer: prose outside the table untouched", rows[0] == answer.split("\n")[0])
    check("answer: other tables untouched", rows[-1] == "| X // Y | test |", rows[-1])
    check("answer: a clean answer is returned as is", normalize_answer(fixed) == (fixed, 0))

    python_first = "| Python | Algorithme |\n|---|---|\n| q = a // b | q ← a // b |"
    fixed, n = normalize_answer(python_first)
    check(
        "answer: column order is read from the header",
        fixed.endswith("| q = a // b | q ← a div b |") and n == 1,
        fixed,
    )

    # --- the checker sees the corrected answer --------------------------------------
    raw_violations = checker.check_algorithme_column(answer)
    fixed_violations = checker.check_algorithme_column(normalize_answer(answer)[0])
    check(
        "checker: flags the raw answer, not the corrected one",
        any("//" in v for v in raw_violations)
        and not any("//" in v or "%" in v for v in fixed_violations),
        (raw_violations, fixed_violations),
    )

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
