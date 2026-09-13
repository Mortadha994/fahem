# Prompt pour convertir un cours au modèle Fahem

Copie tout le bloc ci-dessous dans ton IA, puis colle ton cours (PDF, texte ou Word) à la place de `[COURS]`. Joins aussi le fichier `modele-cours.md` si ton IA accepte les fichiers.

---

```text
Tu convertis un cours d'algorithmique (lycée tunisien, 2ème année) au format
Markdown EXACT décrit ci-dessous. Le fichier sera lu par un programme : le
moindre écart de format le fait refuser. Tu ne réécris pas le cours, tu le
remets en forme. Tu n'inventes aucun contenu.

FORMAT OBLIGATOIRE

1. Le fichier commence par cet en-tête, sans rien avant :
---
niveau: 2eme
chapitre: <numéro seul, ex. 2>
titre: <titre du chapitre>
notions: <liste des notions du chapitre, séparées par des virgules>
---

2. Titres :
   - "# Chapitre N : titre" une seule fois, juste après l'en-tête.
   - "## I. ..." pour chaque grande partie, "### 1. ..." pour les sous-parties.
   - Pour chaque SYNTAXE GÉNÉRALE (pas les exemples), un titre
     "### 📌 Syntaxe : <nom>". Garde dans cette section uniquement la syntaxe
     et, au plus, une courte liste expliquant ses éléments.

3. Code :
   - Chaque algorithme dans un bloc ```algorithme, chaque programme dans un
     bloc ```python. Jamais de bloc ``` sans langage.
   - Jamais l'algorithme et le Python côte à côte ou mélangés sur une ligne :
     d'abord le bloc algorithme, puis le bloc python.
   - Chaque bloc ouvert par ``` est fermé par ```.

4. Notation (à corriger si le cours source se trompe) :
   - Affectation : toujours ← dans les algorithmes (jamais <- ni -).
   - Une seule orthographe par mot-clé dans TOUT le fichier :
     Si, Alors, Sinon, Fin Si, Selon, Fin Selon, Pour, Faire, Fin Pour,
     Tant que, Fin Tant que, Lire, Ecrire.
   - Opérateurs : =, ≠, <, ≤, >, ≥, ET, OU, NON, mod, div.
   - Le même nom de variable dans l'algorithme et dans le Python.

5. Exercices : à la fin, "## Série d'exercices", puis pour chacun
   "### Exercice N" suivi de l'énoncé complet. Pas de correction.

6. Avant de répondre, vérifie : chaque Si a son Fin Si, chaque Selon son
   Fin Selon, chaque bloc de code est fermé, aucun "<-" ne reste. Si le cours
   source contient une erreur (bloc non fermé, opérateur manquant), corrige-la
   et signale-la après le fichier dans une liste "Corrections effectuées".

Réponds uniquement avec le fichier Markdown, puis la liste des corrections.

COURS :
[COURS]
```
