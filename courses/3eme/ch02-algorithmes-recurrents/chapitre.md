---
niveau: 3eme
chapitre: 2
titre: Les algorithmes récurrents
type: cours
notions: matrices, déclaration d'une matrice, programmes modulaires, suites
source: Classroom — Chapitre 2 - les algorithmes récurrents (texte du post « Série N°1 - Les matrices »)
---

# Chapitre 2 : Les algorithmes récurrents

<!-- TODO vérifier: le post Classroom « Chapitre 2 - les algorithmes récurrents » n'a ni texte ni PDF. Ce cours se limite au texte écrit dans le post « Série N°1 - Les matrices » (déclaration d'une matrice) ; les séries du chapitre (matrices 1 à 3, suites) sont les exercices. À compléter avec le vrai cours si vous le retrouvez. -->

## I. Les matrices

Les séries de ce chapitre demandent d'écrire des algorithmes et leur correspondance en Python, sous forme de programmes modulaires, en utilisant les matrices.

### 📌 1. Déclaration d'une matrice

En algorithme :

```algorithme
MAT = Tableau de nombre de lignes "NBL" * nombre de colonnes "NBC" Type
```

En Python :

```python
from numpy import array
M = array([[Type] * NBC] * NBL)
```

<!-- TODO vérifier: le post écrit « from nupmy import array » (corrigé en numpy) ; la ligne algorithme est reprise telle quelle du post -->

Une matrice est un type autre que Entier, Réel, Booléen, Caractère et Chaîne de caractères : elle se définit dans le **T.D.N.T**, puis l'objet se déclare dans le **T.D.O** avec le nom du type.

T.D.N.T

| Type |
|---|
| Mat = Tableau de NBL * NBC Type |

T.D.O

| Objet | Nature/type |
|---|---|
| M | Mat |

<!-- TODO vérifier: ajout (notion T.D.N.T) : le post ne donne que la ligne « MAT = Tableau de … » ; forme du T.D.N.T / T.D.O reprise du cours « Les structures de données et les structures simples » -->

### 2. Exemple

Matrice de 15 lignes et 8 colonnes d'entiers :

```algorithme
MAT = Tableau de 15 * 8 Entier
```

```python
M = array([[int] * 8] * 15)
```

T.D.N.T

| Type |
|---|
| Mat = Tableau de 15 * 8 Entiers |

T.D.O

| Objet | Nature/type |
|---|---|
| M | Mat |
