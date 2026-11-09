---
niveau: 3eme
chapitre: 1
titre: Série N° 1 : Tri & Recherche
type: serie
notions: tri par sélection, tri à bulles, recherche séquentielle, recherche dichotomique, algorithme modulaire, matrices
source: Classroom — Série N°1 - Les Tris et les recherches
---

# Série N° 1 : Tri & Recherche

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes (« Sé rié N° », « tabléau ») ; accents rétablis d'après le rendu à l'écran (contrôlé sur tout le PDF). Le titre du PDF est « Série N° : 1 (Tri & Recherche) » -->

## Série d'exercices

### Exercice 1

Trier une partie d'un tableau de N éléments de type chaînes de caractères en ordre croissant.

Écrire un algorithme modulaire intitulé TRI.

Vous pouvez suivre les étapes ci-dessous :

- Faire une procédure SAISIE( N ) qui permet de saisir un entier naturel non nul inférieur à 111.
- Faire une procédure BORNES ( N, BI, BS ) qui permet de saisir la borne inférieure BI et la borne supérieure BS sachant que 0 ≤ BI < BS < N.
- Faire une procédure REMPLIR ( N, T ) qui permet de saisir les éléments d'un tableau T.
- Faire une procédure TRIER ( BI, BS, T) qui permet de trier une partie du tableau T en ordre croissant.
- Faire une procédure Affiche ( BI, BS , T ) qui permet d'afficher les éléments triés.

### Exercice 2

Écrire un programme modulaire qui saisit de remplir un tableau T par N entiers positifs multiples de 3 avec (4≤N<15) puis trier ce tableau en ordre décroissant en utilisant la méthode de tri par sélection. Afficher les éléments de T après le tri.

Décomposer le problème en modules, écrire l'algorithme du problème principal ainsi que chaque module.

### Exercice 3

Écrire un programme qui permet de saisir un tableau de N chaînes de caractères de longueur maximale =60 et composée que par des lettres alphabétiques, avec 3≤n≤10 et d'afficher ce tableau trié suivant les longueurs des chaînes en utilisant la méthode Tri par sélection en ordre décroissant.

### Exercice 4

Écrire un programme qui saisir un tableau de n lettres majuscules (10≤n<40) et d'afficher ce tableau trié en utilisant la méthode de Tri à Bulle en ordre croissant.

### Exercice 5

Écrire un programme permettant de trier chaque ligne de la matrice et d'afficher les éléments entiers d'une matrice carrée M comportant N lignes et N colonnes (5≤N<30)) lus au hasard (de 1 à 1000) en utilisant la méthode de Tri à bulle.

1. Décomposer ce problème en modules et l'algorithme des modules proposés.
2. Traduisez la solution en un programme python.

### Exercice 6

Écrire un programme permettant de trier chaque colonne de la matrice et d'afficher les éléments entiers d'une matrice carrée M comportant N lignes et N colonnes (5≤N<30) lus au hasard (de 1 à 1000) en utilisant la méthode de Tri par sélection dans l'ordre décroissant.

1. Décomposer ce problème en modules et l'algorithme des modules proposés.
2. Traduisez la solution en un programme python.

### Exercice 7

Écrire un programme Python qui permet de :

1. Saisir un tableau T d'entiers et N dans 10...20
2. Afficher le tableau T
3. Rechercher un élément X en utilisant la recherche séquentielle
4. Trier le tableau dans l'ordre croissant (Tri à votre choix)
5. Afficher le tableau après le tri
6. Rechercher X en utilisant la recherche dichotomique

### Exercice 8

Écrire un programme Python permettant de remplir aléatoirement un tableau T par n (n dans [5..50]) entiers supérieurs à 100, puis former à partir de ce tableau un autre tableau T1 de la manière suivante : T1[i] comportera un entier formée par une suite croissante des chiffres de T[i] ensuite trié le tableau T dans l'ordre décroissant.

**Exemple :** soit le tableau T

| 5478 | 125 | 386 | 1584 | 1654 | 254 | 157 |
|---|---|---|---|---|---|---|

Le tableau T1 Devient :

| 4578 | 125 | 368 | 1458 | 1456 | 245 | 157 |
|---|---|---|---|---|---|---|

Ensuite le tableau T1 :

| 4578 | 1458 | 1456 | 368 | 245 | 157 | 125 |
|---|---|---|---|---|---|---|

<!-- TODO vérifier: l'énoncé dit « ensuite trié le tableau T dans l'ordre décroissant » alors que l'exemple trie le tableau T1 ; transcrit tel quel -->

### Exercice 9

« Un nombre est dit croissant s'il est constitué de chiffres triés dans l'ordre croissant lorsqu'il est lu de gauche à droite Exemple : 134 et 226 sont deux entiers croissants »

On vous demande de :

1. Remplir aléatoirement un tableau T1 par n entiers distincts formé de trois chiffres chacun (6 < n <16).
2. Transférer dans un autre tableau T2 les entiers croissants de T1.
3. Trier le tableau T2 et l'afficher.
4. Afficher les entiers de T2 dont la somme de leurs chiffres donne un entier formé d'un seul chiffre.

**Exemple :**

| T1 | 510 | 900 | 234 | 822 | 131 | 388 | 203 | 952 | 134 | 368 |
|---|---|---|---|---|---|---|---|---|---|---|
| i | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |

| T2 | 234 | 388 | 134 | 368 |
|---|---|---|---|---|
| i | 1 | 2 | 3 | 4 |

| T2 après le Tri | 134 | 234 | 368 | 388 |
|---|---|---|---|---|
| i | 1 | 2 | 3 | 4 |

Les entiers qui seront affichés sont 134 et 234 car 134 : 1 + 3 + 4 = 8 et 234 : 2 + 3 + 4 = 9

### Exercice 10

Écrire un programme qui saisit les noms des élèves dans tableau nom (sachant que les noms sont des chaines alphabétiques de longueur max 25 lettres) et les notes des élèves (réels) entre 0 et 20 dans un tableau notes.

- Trier le Tableaux dans l'ordre décroissant (Tri par sélection).
- Afficher pour chaque élève son nom et sa moyenne
- Afficher les noms des élèves dont la note est une donnée.

<!-- TODO vérifier: dernière puce « dont la note est une donnée » (note donnée en entrée ?) transcrite telle quelle -->
