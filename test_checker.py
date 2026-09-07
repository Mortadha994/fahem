"""Unit-test check_constraints against the four new checks (A/B/C/D),
plus regression cases to confirm nothing that used to pass now fails.

Run inside the backend container (needs torch via context.py -> rag_store.py):
    docker compose exec -T backend python test_checker_cases.py
"""
from generate import check_constraints

# A realistic-enough context stub: the real pinned operators table (for the
# %/// exemption checks) plus enough of the common builtins that RULE1_NAMES
# tracks (print/input/float/range) so those PRE-EXISTING, unrelated checks
# don't fire and cloud the results of the new checks under test.
CONTEXT = (
    "Division entière | // | div | 21 // 4 donne 5\n"
    "Reste de Division entière | % | mod | 21 % 4 donne 1\n"
    "Aléa(Binf,Bsup) | randint (Binf,Bsup) | entier | entier\n"
    'Ecrire ("msg") | print("msg")\n'
    "Lire (x) | x = float(input())\n"
    "Pour i de 1 a n | for i in range(n)\n"  # never actually pinned like this;
    # just present so RULE1_NAMES's range()/print()/input()/float() checks
    # aren't the thing tripping these tests.
)

# Every answer fixture includes a declaration table so the pre-existing,
# unrelated "no Objet | Nature/type table" check (line ~260) never fires and
# clouds a test that isn't about it.
DECL = "Objet | Nature/type\nx | entier\n"

cases = [
    # --- A: min/max ---
    (
        "A: min/max leak (the real confirmed case)",
        "| alea ← Aléa(min(a,b), max(a,b)) | alea = random.randint(min(a,b), max(a,b)) |\n" + DECL,
        True,
    ),
    # --- B: % / // / ** column leak ---
    (
        "B: % leak in Algorithme column (the real confirmed case)",
        "| reste ← alea % 2 | reste = alea % 2 |\n" + DECL,
        True,
    ),
    (
        "B: // leak in Algorithme column",
        "| q ← x // 3 | q = x // 3 |\n" + DECL,
        True,
    ),
    (
        "B: ** leak in Algorithme column",
        "| p ← x ** 2 | p = x ** 2 |\n" + DECL,
        True,
    ),
    (
        "B: %/// legitimate in PYTHON column only - must NOT false-positive",
        "| reste ← alea mod 2 | reste = alea % 2 |\n| q ← x div 3 | q = x // 3 |\n" + DECL,
        False,
    ),
    (
        "B: decorative *** must NOT false-positive",
        '| resultat ← truc | print("***", S, "***", X, "***") |\n' + DECL,
        False,
    ),
    (
        "B: mod/div correctly used in Algorithme column - clean",
        "| reste ← alea mod 2 | reste = alea % 2 |\n" + DECL,
        False,
    ),
    # --- C: f-strings / comprehensions ---
    (
        "C: f-string leak",
        '| Ecrire (resultat) | print(f"Le resultat est {x}") |\n' + DECL,
        True,
    ),
    (
        "C: list comprehension leak",
        "| Ecrire (carres) | carres = [i*i for i in range(10)] |\n" + DECL,
        True,
    ),
    (
        "C: literal single-char string must NOT false-positive as f-string",
        '| Ecrire (ch) | ch [2] = "f" |\n' + DECL,
        False,
    ),
    # --- D: écrire_nl / lire_ligne ---
    (
        "D: écrire_nl used in ch.1 context (not yet ingested) - flagged",
        "| Ecrire_nl (x) | print(x, end='') |\n" + DECL,
        True,
    ),
    (
        "D: lire_ligne used in ch.1 context (not yet ingested) - flagged",
        "| Lire_ligne (f) | line = f.readline() |\n" + DECL,
        True,
    ),
    (
        "D: écrire_nl allowed once context actually supplies it",
        "| Ecrire_nl (x) | print(x, end='') |\n" + DECL,
        False,
        CONTEXT + "Ecrire_nl(x) | print(x, end='')\n",
    ),
    # --- NEGATION_RE: paragraph-scoped, not line-scoped ---
    (
        "NEGATION_RE: soft-wrapped negation (the real confirmed false positive)",
        "*Remarque : le cours du chapitre 1 ne comporte pas de structure\n"
        "conditionnelle ( Si…Alors… ).*\n" + DECL,
        False,
    ),
    (
        "NEGATION_RE: a real Si...Alors in a LATER paragraph must still be flagged "
        "(paragraph-scoping must not become whole-document-scoping)",
        "*Remarque : le cours du chapitre 1 ne comporte pas de structure\n"
        "conditionnelle.*\n"
        "\n"
        "Si le nombre est pair alors on l'affiche.\n" + DECL,
        True,
    ),
    # --- Regression: previously-clean real answer must stay clean ---
    (
        "Regression: known-good answer (carre example) stays clean",
        '| Ecrire ("Entrez un nombre") | print("Entrez un nombre") |\n'
        "| Lire (nombre) | nombre = float(input()) |\n"
        "| carre ← nombre * nombre | carre = nombre * nombre |\n"
        "| Ecrire (carre) | print(carre) |\n"
        "Objet | Nature/type\nnombre | réel\ncarre | réel\n",
        False,
    ),
]

failures = 0
for case in cases:
    label, answer, expect_violation = case[0], case[1], case[2]
    context = case[3] if len(case) > 3 else CONTEXT
    violations, notes = check_constraints(answer, context)
    got_violation = len(violations) > 0
    status = "PASS" if got_violation == expect_violation else "FAIL"
    if status == "FAIL":
        failures += 1
    print(f"[{status}] {label}")
    if violations:
        for v in violations:
            print(f"         ! {v}")
    elif expect_violation:
        print("         (expected a violation, got none)")

print()
print("ALL PASSED" if failures == 0 else f"{failures} CASE(S) FAILED")
