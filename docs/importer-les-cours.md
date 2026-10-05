# Importer les cours Markdown dans Fahem

Les cours sont écrits à partir des documents Classroom, un fichier par document :

```
courses/<niveau>/chNN-<slug>/chapitre.md      le cours      (type: cours)
courses/<niveau>/chNN-<slug>/serie-*.md       une série par fichier (type: serie)
```

`<niveau>` vaut `2eme`, `3eme` ou `bac`. `NN` est le numéro du chapitre **dans son niveau** (le
même que `chapitre:` dans l'en-tête). Ces fichiers sont la source de vérité.

## Ce que Fahem importe

Fahem importe **un fichier par chapitre** (`app/rag/course_markdown.py`) : du texte de cours, au moins
une section 📌 (la fiche de syntaxe, injectée dans chaque réponse du chapitre) et les exercices sous
`## Série d'exercices`. Un fichier de série seul est donc refusé.
`scripts/import_courses.py` assemble le fichier de chapitre : le cours, puis les exercices de toutes
les séries, renumérotés à la suite (`Exercice 1`… `Exercice 75`), chacun précédé de la série dont il vient.

## Numéros de chapitre dans Fahem

L'identifiant d'un chapitre est unique pour toute la plateforme. Chaque niveau a son bloc
(`app/core/chapter_ids.py`, et `ui/src/lib/chapterNumber.js` pour l'affichage) :

| niveau | identifiants | id = |
|---|---|---|
| 2eme | 1 à 29 | numéro |
| 3eme | 31 à 59 | 30 + numéro |
| bac | 61 à 89 | 60 + numéro |

L'élève lit « Chapitre 1 », jamais « Chapitre 31 ». Le chapitre 1 de 2ème (id 1) est intégré à Fahem
et n'est jamais remplacé ; un dossier sans `chapitre.md` (séries seules) n'est pas importé.

## Commandes

Vérifier sans rien changer (Python seul, aucune dépendance) :

```
.venv\Scripts\python -m scripts.import_courses
.venv\Scripts\python -m scripts.import_courses --niveau 3eme --write-merged build\merged
```

Écrire dans la base (brouillons), puis publier. Il faut la base, Qdrant et le modèle d'embeddings,
donc dans le conteneur du backend :

```
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml run --rm \
  -v "<dossier>/courses:/app/courses:ro" -v "<dossier>/scripts:/app/scripts:ro" \
  -v "<dossier>/app:/app/app:ro" backend python -m scripts.import_courses --root /app/courses --apply --publish
```

Relancer la commande réimporte les chapitres que ce script a créés : ils repartent à zéro depuis leurs
fichiers (même chemin que « envoyer un fichier corrigé » dans la console). Un chapitre qui existe déjà
avec une autre source (envoyé ou relu à la main dans la console) est ignoré ; `--force` le remplace. La publication ne lance pas le calcul des
réponses préparées ; il se fait depuis la console, chapitre par chapitre.

## Envoi à la main

Le fichier assemblé (`--write-merged`) peut aussi être envoyé depuis la console admin : l'identifiant
demandé doit être celui du tableau ci-dessus, et le niveau est lu dans l'en-tête du fichier.

## Le PDF du cours

La page d'un chapitre montre un PDF ; sans PDF elle affiche le texte du cours (`/chapters/{id}/course`).
`scripts/build_pdf.py` fabrique le PDF de chaque chapitre à partir des fichiers de `courses/`
(le cours seulement, comme l'élève le lit : sans notes d'auteur ni exercices). Il utilise Edge ou
Chrome en mode sans fenêtre ; aucune dépendance de plus.

```
.venv\Scripts\python -m scripts.build_pdf                      # build\pdf\<id>.pdf pour chaque chapitre
.venv\Scripts\python -m scripts.build_pdf --niveau bac --chapter 4
docker cp build\pdf\31.pdf fahem-backend-1:/app/uploads/chapters/31.pdf
```

Le fichier porte l'identifiant Fahem du chapitre. Ne copie pas un PDF sur un chapitre dont le PDF a
été envoyé à la main (par exemple le chapitre 2 de 2ème) : il serait remplacé.
