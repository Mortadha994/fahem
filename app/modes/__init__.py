"""The chat's answer modes, one module each.

  full     « La solution »: the exercise solved outright (the default).
  guided   « Mode guidé »: the exercise led step by step, the solution last.

Each module owns what is specific to its mode: when a request is in it, which
prompt route and step it gets, whether its first answer can come from the
precomputed cache, and how its answer is judged once written. app/main.py's
/solve/stream only dispatches to them, so changing one mode does not mean
reading through the other.

"Vérifier ma réponse" (check) and "Exercice similaire" (practice) are still
handled in app/main.py.
"""
