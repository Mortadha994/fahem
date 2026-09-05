"""Isolation test: current 7-pin context, OLD rule 3bis wording.

Changes exactly one variable against the current baseline - the coefficient
clause - to see whether that wording drives the int/float choice at all, or
whether something else does. prompts.py is left untouched; the swap is done
in memory.
"""
import argparse, json, re, sys
import prompts
from context import build_context
from generate import generate, check_constraints
from prompts import USER_PROMPT

NEW = """durée, une mesure physique comme un rayon ou une hauteur, un coefficient)
   doit être lue comme réel. Une grandeur qui est un compte ou
   intrinsèquement entière (un nombre d'éléments, un indice, une position)
   reste entier. En cas de doute sur une grandeur mesurable, privilégie
   réel."""

OLD = """durée, une mesure physique comme un rayon ou une hauteur) doit être lue
   comme réel. Une grandeur qui est un compte ou intrinsèquement entière
   (un nombre d'éléments, un coefficient donné comme un entier dans
   l'énoncé, un indice, une position) reste entier. En cas de doute sur une
   grandeur mesurable, privilégie réel."""

ap = argparse.ArgumentParser()
ap.add_argument("--wording", choices=["old", "new"], default="old")
ap.add_argument("--temperature", type=float, default=0.2)
ap.add_argument("--out")
args = ap.parse_args()

system = prompts.SYSTEM_PROMPT
if args.wording == "old":
    if NEW not in system:
        sys.exit("FAIL: current 3bis wording not found - prompts.py changed, update this script")
    system = system.replace(NEW, OLD)
    assert "coefficient donné comme un entier" in system
    assert "une hauteur, un coefficient)" not in system

p = [x for x in json.load(open("sample_problems.json", encoding="utf-8"))
     if x["id"] == "ex21_moyenne"][0]
ctx = build_context(p["question"], p["niveau"], p["chapitre"], k=5).render()
msgs = [
    {"role": "system", "content": system.format(niveau="2ème", chapitre="1")},
    {"role": "user", "content": USER_PROMPT.format(context=ctx, query=p["question"])},
]
print(f"wording={args.wording} temp={args.temperature} pins-context={len(ctx)} chars")
ans = generate(msgs, "groq", args.temperature)
v, _ = check_constraints(ans, ctx)
print("  moyennes:", re.findall(r"moyenne\d?\s*=\s*(int|float)\s*\(", ans, re.I))
print("  coefs   :", re.findall(r"coef\w*\d?\s*=\s*(int|float)\s*\(", ans, re.I))
print("  violations:", v or "clean")
if args.out:
    json.dump({"wording": args.wording, "answer": ans}, open(args.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
