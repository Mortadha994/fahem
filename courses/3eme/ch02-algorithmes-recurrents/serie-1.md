---
niveau: 3eme
chapitre: 2
titre: Série N° 1 : Les matrices
type: serie
notions: matrices, remplissage et affichage d'une matrice, somme des cases, lignes et colonnes, diagonales, addition de matrices, triangle de Pascal, PGCD
source: Classroom — Série N°1 - Les matrices
---

# Série N° 1 : Les matrices

## Rappel

(L : le nombre des lignes et C : le nombre de colonnes)

N : pour les lignes et les colonnes

Déclaration : MAT = Tableau de NBlignes * NbColonnes Type

![deux matrices 5x5 numérotées de 1 à 25 ; à gauche la ligne N° 1 (1 à 5) et la colonne N° 2 (2, 7, 12, 17, 22) sont colorées, la case commune étant la case 2 ; à droite la diagonale N° 1 (diagonale à gauche : 1, 7, 13, 19, 25) et la diagonale N° 2 (diagonale à droite : 5, 9, 13, 17, 21) sont colorées, la case commune étant 13](figures/serie1-rappel-matrices.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: le PDF place les légendes « Ligne N° 1 », « Colonne N° 2 », « Diag N° 1 : diagonale à gauche », « Diag N° 2 : diagonale à droite » et « Case commune » autour de ces deux matrices ; la description ci-dessus est faite d'après le rendu à l'écran, couleurs exactes à contrôler -->

## Série d'exercices

### Exercice 1

Ecrire un algorithme qui permet de remplir et d'afficher une Matrice M de taille N*N entiers

### Exercice 2

Ecrire un algorithme qui permet de remplir et d'afficher une Matrice M de taille N*N entiers de 3 chiffres. (5≤N≤20)

### Exercice 3

Ecrire un algorithme qui permet de remplir une Matrice M de taille L*C lettres majuscules aléatoire. (5 ≤ L ≤ 20 et 3 < C < 13) et d'afficher que les voyelles tout en remplaçant les consonnes par « * » dans l'affichage.

### Exercice 4

Ecrire un module qui permet de calculer la somme des cases d'une matrice M de taille L*C entiers.

### Exercice 5

Ecrire un module qui permet de calculer et d'afficher la somme des cases de chaque ligne d'une matrice M de taille L*C entiers.

### Exercice 6

Ecrire un module qui permet de calculer et d'afficher la somme des cases de chaque colonne d'une matrice M de taille L*C entiers.

### Exercice 7

Ecrire un module qui affiche la diagonale à gauche ainsi que la somme d'une matrice M de taille N*N entiers.

### Exercice 8

Ecrire un module qui affiche la diagonale à droite ainsi que la somme d'une matrice M de taille N*N entiers.

### Exercice 9

Ecrire un algorithme qui permet de remplir une Matrice M Taille N*N entiers et de calculer et d'afficher la somme des deux diagonales.

### Exercice 10

Ecrire un algorithme qui permet de remplir deux Matrice M1 et M2 Taille L*C entiers (L : le nombre des lignes et C : le nombre de colonnes) et de calculer et d'afficher l'addition de 2 matrices

M1 =

| 1 | 3 | 5 |
|---|---|---|
| 2 | 6 | 8 |
| 4 | 5 | 1 |
| 8 | 4 | 6 |

M2 =

| 5 | 1 | 4 |
|---|---|---|
| 2 | 8 | 12 |
| 6 | 4 | 8 |
| 7 | 9 | 3 |

M =

| 6 | 4 | 9 |
|---|---|---|
| 4 | 14 | 20 |
| 10 | 9 | 9 |
| 15 | 13 | 9 |

### Exercice 11

Ecrire un programme qui permet de remplir et afficher le triangle de PASCAL pour un degré N de l'équation (a+b)ⁿ donné par l'utilisateur.

si N = 4

| 1 | | | | |
|---|---|---|---|---|
| 1 | 1 | | | |
| 1 | 2 | 1 | | |
| 1 | 3 | 3 | 1 | |
| 1 | 4 | 6 | 4 | 1 |

### Exercice 12

Écrire un programme qui permet de :

remplir une matrice M par L*C lettres majuscules sachant que 4≤L≤20 et pair et 3≤C<19 et impair. Calculer et afficher le poids de la matrice

**N.B** : le poids de la matrice est la somme de l'ordre de l'ordre d'une voyelle dans l'alphabet (par exemple A=1, E=5 ....) multiplié par l'indice de la ligne et l'indice de la colonne

<!-- TODO vérifier: « l'ordre de l'ordre d'une voyelle » (répétition) transcrit tel quel d'après le PDF -->

### Exercice 13

Ecrire un programme intitulé "Devoir" qui permet de remplir une matrice T par n*m entiers positifs formés de 3 chiffres calculer puis afficher le nombre d'occurrences d'un chiffre c donné dans la matrice T.

Avec n c'est le nombre de lignes, m c'est le nombre de colonnes, 2<n ≤50 et 2<m≤50

**Exemple :**

Soit une matrice T de 4 lignes et 5 colonnes

| 124 | 809 | 509 | 423 | 237 |
|---|---|---|---|---|
| 587 | 250 | 102 | 586 | 999 |
| 506 | 100 | 390 | 145 | 155 |
| 589 | 608 | 940 | 358 | 680 |

Si c=5 le programme affichera le nombre d'occurrences de 5 est 10

### Exercice 14

1) Ecrire un algorithme d'une procédure qui permet de remplir une matrice carré d'ordre n de la façon suivante :

- Remplir la première ligne au hasard par des entiers de deux chiffres supérieurs à 15.
- A partir de la de ligne 2 : M [i, j] = PGCD (M[i-1,j] et M[i-1,j+1])

<!-- TODO vérifier: « A partir de la de ligne 2 » (faute de frappe) transcrit tel quel d'après le PDF -->

**Exemple :** n=4,

M=

| 15 | 20 | 30 | 99 |
|---|---|---|---|
| 5 | 10 | 3 | |
| 5 | 1 | | |
| 1 | | | |

2) Que représente la dernière case M [n, 1] ?
