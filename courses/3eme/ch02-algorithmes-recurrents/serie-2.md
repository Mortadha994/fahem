---
niveau: 3eme
chapitre: 2
titre: Série N° 2 : Les matrices
type: serie
notions: inversion d'une matrice, symétrie d'une matrice, remplissage d'une matrice en motifs, produit matriciel, conversion binaire, conversion hexadécimale, entiers Harshad, carré magique
source: Classroom — Série N° 2 - Les matrices
---

# Série N° 2 : Les matrices

<!-- TODO vérifier: la numérotation des exercices continue celle de la série 1 (exercices 15 à 25, puis Problèmes 1 à 3), comme dans le PDF -->

## Série d'exercices

### Exercice 15

Ecrire un algorithme qui permet de remplir une Matrice M Taille N*N entiers aléatoires ∈ [1..99] et d'inverser la matrice verticalement.

**Exemple :**

| 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| 6 | 7 | 8 | 9 | 10 |
| 11 | 12 | 13 | 14 | 15 |
| 16 | 17 | 18 | 19 | 20 |
| 21 | 22 | 23 | 24 | 25 |

devient

| 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| 10 | 9 | 8 | 7 | 6 |
| 15 | 14 | 13 | 12 | 11 |
| 20 | 19 | 18 | 17 | 16 |
| 25 | 24 | 23 | 22 | 21 |

![deux matrices 5x5 : à gauche 1 à 25 ligne par ligne, à droite la même matrice dont les colonnes sont inversées ; des flèches relient la colonne 1 (resp. 2) à la colonne 5 (resp. 4) et la colonne 2 de la matrice de gauche à la colonne 4 de la matrice de droite](figures/serie2-ex15-inversion-verticale.png)
<!-- TODO figure: à recréer -->

### Exercice 16

Ecrire un algorithme qui permet de remplir une Matrice M Taille N*N entiers aléatoires ∈ [1..99] et d'inverser la matrice horizontalement.

**Exemple :**

| 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| 6 | 7 | 8 | 9 | 10 |
| 11 | 12 | 13 | 14 | 15 |
| 16 | 17 | 18 | 19 | 20 |
| 21 | 22 | 23 | 24 | 25 |

devient

| 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|
| 16 | 17 | 18 | 19 | 20 |
| 11 | 12 | 13 | 14 | 15 |
| 6 | 7 | 8 | 9 | 10 |
| 1 | 2 | 3 | 4 | 5 |

![deux matrices 5x5 : à gauche 1 à 25 ligne par ligne, à droite la même matrice dont les lignes sont inversées ; des flèches relient la ligne 1 à la ligne 5 et la ligne 4 à la ligne 2](figures/serie2-ex16-inversion-horizontale.png)
<!-- TODO figure: à recréer -->

### Exercice 17

Ecrire un algorithme qui permet de remplir une Matrice M Taille N*N entiers aléatoires ∈ [10..99] et d'inverser toute les cases de la matrice.

| 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| 6 | 7 | 8 | 9 | 10 |
| 11 | 12 | 13 | 14 | 15 |
| 16 | 17 | 18 | 19 | 20 |
| 21 | 22 | 23 | 24 | 25 |

devient

| 25 | 24 | 23 | 22 | 21 |
|---|---|---|---|---|
| 20 | 19 | 18 | 17 | 16 |
| 15 | 14 | 13 | 12 | 11 |
| 10 | 9 | 8 | 7 | 6 |
| 5 | 4 | 3 | 2 | 1 |

![deux matrices 5x5 : à gauche 1 à 25 ligne par ligne, à droite toutes les cases inversées (25 à 1) ; des flèches relient la case 25 de la matrice de gauche à la case 25 de la matrice de droite en haut à gauche, et la case 7 de la matrice de gauche à la case 7 de la matrice de droite](figures/serie2-ex17-inversion-totale.png)
<!-- TODO figure: à recréer -->

### Exercice 18

Ecrire un module qui permet de tester si une Matrice M Taille N*N entiers est symétrique verticalement ou non.

### Exercice 19

Ecrire un module qui permet de tester si une Matrice M Taille N*N entiers est symétrique horizontalement ou non.

### Exercice 20

Ecrire un algorithme d'un programme permettant de remplir une matrice de la façon suivante un triangle isocèle formé par des étoiles de n lignes. (2≤n≤30) et d'afficher la matrice

**Exemple :** n=4

> `*******`
> `  *****`
> `    ***`
> `      *`

<!-- TODO vérifier: dans le PDF les lignes d'étoiles sont centrées (7, 5, 3 puis 1 étoile) ; les espaces de décalage sont reconstitués d'après le rendu -->

### Exercice 21

On se propose de remplir une matrice M sous la forme d'une pyramide d'entiers de la manière suivante :

pour n=5 (3≤n≤30)

| 1 | | | | | | | | |
|---|---|---|---|---|---|---|---|---|
| 2 | 3 | 2 | | | | | | |
| 3 | 4 | 5 | 4 | 3 | | | | |
| 4 | 5 | 6 | 7 | 6 | 5 | 4 | | |
| 5 | 6 | 7 | 8 | 9 | 8 | 7 | 6 | 5 |

### Exercice 22

- Remplir une matrice carrée de n entiers de la façon suivante :

| 1 | 2 | 3 | 4 |
|---|---|---|---|
| 8 | 7 | 6 | 5 |
| 9 | 10 | 11 | 12 |
| 16 | 15 | 14 | 13 |

### Exercice 23

- Remplir une matrice carrée de n entiers (n impair) de la façon suivante :

| | | 1 | | |
|---|---|---|---|---|
| | 2 | 3 | 4 | |
| 5 | 6 | 7 | 8 | 9 |
| | 10 | 11 | 12 | |
| | | 13 | | |

### Exercice 24

- Remplir une matrice carrée de **N** caractères de la façon suivante :
  - La diagonale à gauche remplie par des étoiles « * »
  - Les restes des cases de la partie inférieure remplies par des lettres majuscules aléatoire
  - El la partie supérieure par la symétrie

| * | Z | B | Q | T |
|---|---|---|---|---|
| Z | * | X | A | N |
| B | X | * | W | E |
| Q | A | W | * | F |
| T | N | E | F | * |

<!-- TODO vérifier: « El la partie supérieure » (faute de frappe) transcrit tel quel d'après le PDF -->

### Exercice 25

Ecrire un algorithme qui permet de remplir deux Matrice M1 et M2 Taille N entiers et de calculer et d'afficher le produit matriciel de 2 matrices 1*5+3*2+5*6

M1 =

| 1 | 3 | 5 |
|---|---|---|
| 2 | 6 | 8 |
| 4 | 5 | 1 |

M2 =

| 5 | 1 | 4 |
|---|---|---|
| 2 | 8 | 12 |
| 6 | 4 | 8 |

M =

| 41 | 45 | 80 |
|---|---|---|
| 70 | 146 | 144 |
| 36 | 48 | 84 |

Les cases de M sont accompagnées dans le PDF des calculs suivants :

- 41=1*5+3*2+5*6
- 45=1*1+3*8+5*4
- 80=1*4+3*12+5*8
- 70=2*5+6*2+8*6

<!-- TODO vérifier: la phrase « produit matriciel de 2 matrices 1*5+3*2+5*6 » du PDF contient le calcul de la case 41 en fin de phrase ; transcrite telle quelle. Dans le PDF, les calculs sont placés sur la matrice M avec des flèches -->

### Problème 1

On se propose d'écrire un programme qui permet de :

- Remplir une matrice **M** de degré **N** par des entiers **binaires** (0 ou 1 seulement),
- Chaque ligne de la matrice **M** représente la conversion binaire d'un entier **X** de la base 10 ;
  - Trouver la valeur de **X** pour chaque ligne de **M**,
  - Associer les valeurs de **X** dans un tableau **T**,
- Trier puis afficher (en ordre décroissant) les éléments du tableau **T**,
- Enregistrer dans un fichier texte les résultats sous la forme **(X)₂ = (Y)₁₀**.

**Exemple :**

Si N = 4 et M=

| 1 | 0 | 1 | 0 |
|---|---|---|---|
| 0 | 1 | 1 | 1 |
| 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 1 |

T=

| 10 |
|---|
| 7 |
| 9 |
| 11 |

Le programme affichera : 11-10-9-7

(1010)₂ = (10)₁₀ comment ?

2³ 2² 2¹ 2⁰

1 0 1 0

1010 = 1*2³ + 0*2² + 1*2¹ + 0*2⁰ = 1*8 + 0*4 + 1*2 + 0*1 =10

**Questions :**

1. Analyser le problème en le décomposant en modules,
2. écrire l'algorithme du programme principal ainsi que les algorithmes des modules envisagés.

### Problème 2

Soit M une matrice carrée de dimension N (2 ≤ N ≤ 10). On veut écrire un programme qui remplit M par des entiers positifs. Puis transférer les entiers **Harshad** dans un tableau T et afficher la conversion en hexadécimale (base 16) de chaque élément de T.

**N.B :** un entier est dit **Harshad** s'il est divisible par la somme de ses chiffres.

Exemple : 102 est Harshad car 102 est divisible par la somme de ses chiffres qui est 3 (3 = 1+0+2)

**Exemple :** n= 3 et M=

| 102 | 203 | 15 |
|---|---|---|
| 12 | 113 | 26 |
| 150 | 42 | 77 |

T =

| 102 | 12 | 150 | 42 |
|---|---|---|---|

Le programme affichera :

| 66 | C | 96 | 2A |
|---|---|---|---|

### Problème 3 : (Carré magique)

Un carré magique est un arrangement de nombres avec n lignes et n colonnes tel que la somme des valeurs de chaque ligne = la somme des valeurs de chaque colonne = la somme des valeurs de chaque diagonale.

**Par exemple,** le carré suivant est magique

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 16 | 9 | 2 | 7 |
| 2 | 6 | 3 | 12 | 13 |
| 3 | 11 | 14 | 5 | 4 |
| 4 | 1 | 8 | 15 | 10 |

La somme des valeurs de chaque ligne = 34

La somme des valeurs de chaque colonne = 34

La somme des valeurs de chaque diagonale = 34

#### Partie I :

1) Ecrire un algorithme d'une fonction intitulée **Somme_ligne** qui permet de retourner la somme d'une ligne donnée.

2) Ecrire un algorithme d'une fonction intitulée **Somme_colonnne** qui permet de retourner la somme d'une colonne donnée.

3) Ecrire un algorithme d'une fonction intitulée **Somme_ diagonale1** qui permet de retourner la somme de la 1ere diagonale.

4) Ecrire un algorithme d'une fonction intitulée **Somme_diagonale2** qui permet de retourner la somme de la 2ème diagonale.

5) Ecrire un algorithme d'une fonction intitulée **Magic_1** qui permet de vérifier si un carré donné est magique.

<!-- TODO vérifier: noms « Somme_colonnne » (trois n) et « Somme_ diagonale1 » (espace) transcrits tels quels d'après le PDF -->

#### Partie II :

Une autre condition pour un arrangement de nombres avec n lignes et n colonnes d'être un vrai carré magique est qu'il doit contenir tous les entiers entre 1,2,......,**n²** .

Par exemple dans notre cas il faut que tous les entiers entre 1 et 16 doivent être comprises dans le carré (Matrice).

1) Ecrire un algorithme d'une fonction intitulée **Magic_2** qui permet de vérifier si un carré est un vrai carré magique.

2) Ecrire un algorithme du programme principal permettant de vérifier si un carré est magique, un vrai carré magique ou bien n'est pas magique.
