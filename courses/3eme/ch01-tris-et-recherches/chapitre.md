---
niveau: 3eme
chapitre: 1
titre: Les algorithmes de tris et de recherches
type: cours
notions: tri d'un tableau, tri par sélection, tri à bulles, recherche d'un élément, recherche séquentielle, recherche dichotomique
source: Classroom — Chapitre 1 - Les algorithmes de tris et de recherches
---

# Chapitre 1 : Les algorithmes de tris et de recherches

<!-- TODO vérifier: le PDF (3 pages) ne contient aucun code Python, seulement des algorithmes ; aucun bloc python n'a été ajouté -->

## I. Le tri d'un tableau

### Introduction

- Le tri est une opération qui consiste à répartir ou organiser une collection d'objets selon un ordre déterminé. Dans le domaine de l'informatique, il existe plusieurs méthodes de tri (algorithmes).
- Dans ce chapitre nous allons découvrir deux méthodes de tri :
  - Tri par sélection
  - Tri à bulles
- Et les deux méthodes de recherche :
  - Recherche séquentiel
  - Recherche dichotomique

### 📌 1. Tri par sélection

**Principe :**

Cette méthode de tri consiste à :

1. Se pointer à la 1ère case du tableau T et de parcourir la totalité du tableau pour repérer l'indice de la première position du minimum,
2. Comparer ce minimum avec T [0]. S'ils sont différents on les permute,
3. Le sous tableau de T allant de 1 à n-1 est à priori non trié, on applique l'étape 1 et 2 et ainsi de suite jusqu'à l'avant dernier élément (n-2).

**Remarque :**

- On est arrivé à l'élément numéro n-2, alors arrêt du traitement.
- Nous n'avons pas besoin de traiter le dernier élément, puisque si les neuf premiers éléments sont triés alors automatiquement le dernier sera le plus grand et par conséquent il se trouve à la bonne position.

**Méthode itérative :**

Algorithme de la procédure Tri :

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Pour i de 0 à N-2 Faire
        Pm ← i
        Pour j de i+1 à N-1 Faire
            Si (T [j] < T [Pm]) Alors
                Pm ← j
            Fin Si
        Fin Pour
        Si (i ≠ Pm) Alors
            Aux ← T[i]
            T[i] ← T[Pm]
            T[Pm] ← Aux
        Fin Si
    Fin Pour
Fin
```

T.D.N.T

| Type |
|---|
| TAB = Tableau de 100 entiers |

T.D.O.L

| Objet | Nature/type |
|---|---|
| i, j, Pm, Aux | Entier |

### 📌 2. Tri à bulles

**Principe :**

Cette méthode de tri consiste à :

1. Comparer les éléments du tableau T deux à deux,
2. Permuter les contenus lorsque l'ordre n'est pas respecté,
3. Refaire les actions 1 et 2 et ainsi de suite jusqu'à avoir finalement un tableau trié.

Puisqu'on a atteint la fin du tableau et le contenu de la variable test est Faux, alors on doit recommencer un nouveau passage et ainsi de suite jusqu'à ce qu'on fasse un passage complet du tableau sans modifier le contenu de test (Vrai).

<!-- TODO vérifier: le texte parle de la « variable test », mais l'algorithme utilise la variable « permute » -->

**Méthode itérative :**

Algorithme de la procédure Tri :

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Répéter
        permute ← Faux
        Pour i de 0 à N-2 Faire
            Si (T[i] > T[i+1]) Alors
                Aux ← T[i]
                T[i] ← T[i+1]
                T[i+1] ← Aux
                permute ← Vrai
            Fin Si
        Fin Pour
    Jusqu'à (permute = Faux)
Fin
    Fin Pour
Fin
```

<!-- TODO vérifier: dans le PDF, l'algorithme du tri à bulles se termine par un « Fin » suivi d'un « Fin Pour » et d'un second « Fin » superflus (transcrits tels quels) ; le PDF écrit « permute = faux » (transcrit « Faux ») -->

T.D.O.L

| Objet | Nature/type |
|---|---|
| I, Aux | Entier |
| permute | Booléen |

<!-- TODO vérifier: la T.D.O.L du PDF écrit « I » (majuscule) alors que l'algorithme utilise « i » -->

## II. La recherche d'un élément dans un tableau

### Introduction

- La recherche d'un élément dans un tableau ou dans une liste de valeur est un traitement très utile en informatique.
- Parmi les méthodes de recherches, on cite :
  - La recherche séquentielle,
  - La recherche dichotomique.

### 1. La recherche séquentielle

**Principe :**

Cette méthode de recherche consiste à parcourir les éléments du tableau un par un jusqu'à trouver la valeur cherchée ou arriver à la fin du tableau.

**Exemple :**

Soit un tableau T contenant les dix éléments suivants :

| T | 12 | 10 | 0 | -5 | 8 | 12 | -2 | 2 | 40 | -1 |
|---|---|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

Pour X = -2 le programme affichera "-2 existe dans le tableau"

Pour X = 5 le programme affichera "5 n'existe pas dans le tableau"

Algorithme de la fonction Recherche :

```algorithme
Fonction recherche (T : TAB ; N, X : Entier) : Booléen
Début
    i ← 0
    Répéter
        Trouve ← T[i] = X
        i ← i+1
    Jusqu'à ((Trouve = Vrai) OU (i = N))
    Retourner Trouve
Fin
```

T.D.O.L

| Objet | Nature/type |
|---|---|
| i | Entier |
| Trouve | Booléen |

### 📌 2. La recherche dichotomique

**Principe :**

Cette méthode de recherche consiste à :

1. Fixer le début (Deb) et la fin (Fin) du tableau,
2. Fixer le milieu du tableau (Mil = (Fin + Deb) Div 2),
3. Comparer X et T[Mil], Si (X > T[Mil]) alors rechercher X dans le sous tableau [Mil + 1 ... Fin] sinon si (X < T[Mil]) alors dans le tableau [Deb ... Mil - 1],
4. Répéter les étapes 1, 2 et 3 jusqu'à (X = T[Mil]) ou (Deb > Fin)

Algorithme de la fonction Recherche :

```algorithme
Fonction recherche (T : TAB ; N, X : Entier) : Booléen
Début
    Trouve ← Faux
    Deb ← 0
    Fin ← N - 1
    Répéter
        Mil ← (Deb + Fin) Div 2
        Si (T[Mil] > X) Alors
            Fin ← Mil - 1
        Sinon
            Si (T[Mil] < X) Alors
                Deb ← Mil + 1
            Sinon
                Trouve ← Vrai
            Fin Si
        Fin Si
    Jusqu'à ((Trouve = Vrai) OU (Deb > Fin))
    Retourner Trouve
Fin
```

<!-- TODO vérifier: le PDF écrit « Finsi » (en un mot) pour la seconde fermeture ; normalisé en « Fin Si » -->

T.D.O.L

| Objet | Nature/type |
|---|---|
| Deb, Fin, Mil | Entier |
| Trouve | Booléen |
