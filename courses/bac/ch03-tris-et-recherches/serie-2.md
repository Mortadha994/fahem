---
niveau: bac
chapitre: 3
titre: Série N° 2 : Tri & Recherche
type: serie
notions: tri par rang, tri par comptage, tri casier, fusion de tableaux, insertion dans un tableau trié, matrices
source: Classroom — Série N°1+2+3 - Les Tris et les recherches (série 2 les tris (Bac).pdf)
---

# Série N° 2 : Tri & Recherche

<!-- TODO vérifier: le PDF (3 pages) est intitulé « Série N° : 2 (Tri & Recherche) » ; la numérotation des exercices (11 à 20) est conservée telle quelle -->

## Série d'exercices

### Exercice 11

Écrire un programme intitulé **Tri_vecteur** permettant de trier et d'afficher un tableau **T** de **N** entiers <u>**distincts**</u> (5<**N**<20) selon le principe suivant :

Trouver **NB** le nombre de case inférieur à T[i] et placer T[i] dans le tableau **R** à la position **NB+1**. Pour chaque élément de T :

**Exemple :**

| T | 6 | 2 | 0 | 5 | 12 | 25 |
|---|---|---|---|---|---|---|

Trois valeurs sont inférieures au premier élément de T. cet élément sera placé à la position quatre du tableau R

| R |  |  |  | 6 |  |  |
|---|---|---|---|---|---|---|

Une seule valeur est inférieure au deuxième élément de T. cet élément sera placé à la position deux du tableau R

| R |  | 2 |  | 6 |  |  |
|---|---|---|---|---|---|---|

Le résultat affiché est **R** qui sera un tableau trié dans l'ordre croissant.

<!-- TODO vérifier: dans le PDF, « Pour chaque élément de T : » est placé à la fin du paragraphe, avant « Exemple » (transcrit tel quel) ; les tableaux R ont des cases vides (ce sont des cases de l'énoncé, pas des grilles de réponse) -->

### Exercice 12

Soit un tableau **T1** contenant **N** lettres majuscule (de A à Z), **N** étant un entier compris entre **5** et **20**. On désire triés en ordre croissant les éléments de **T1** et les ranger dans un tableau **T2** en utilisant le principe suivant :

1. Cherche la lettre **qui a le plus petit code ASCII** dans **T1**.
2. a) ranger cette lettre dans **T2**.  
   b) remplacer cette lettre par '\*' dans **T1**.
3. Répéter n fois les étapes 1 et 2.

Écrire un programme qui permet de :

- Saisir les éléments de **T1**
- Trier les éléments de **T1** et les ranger dans **T2**
- Afficher les éléments de **T2**

### Exercice 13

Écrire l'algorithme modulaire d'un programme nommé **TRI_TAB** qui permet de trier par ordre décroissant les éléments d'un tableau **A** de **N** entiers positifs (5<**N**<20) dans un tableau **B** de même dimension.

1. Chercher le maximum de **A**.
2. Placer le maximum dans **B**.
3. Placer ce maximum par -1 dans **A**
4. Refaire les étapes 1, 2 et 3 jusqu'à ce que le tableau **A** soit entièrement composé par des -1

N.B : prévoir l'affichage des éléments du Tableau **B**.

### Exercice 14

Écrire un programme qui saisit deux tableaux d'entiers triés par ordre croissant et les fusionnent dans un nouveau tableau en respectant l'ordre croissant des entiers.

**Exemple :**

| Tableau 1 | 1 | 5 | 7 | 9 |
|---|---|---|---|---|
| Tableau 2 | -8 | 0 | 3 |  |

Résultat :

| -8 | 0 | 1 | 3 | 5 | 7 | 9 |
|---|---|---|---|---|---|---|

<!-- TODO vérifier: dans le PDF, l'exemple montre deux tableaux (1 5 7 9 et -8 0 3) réunis par une accolade vers le tableau résultat ; les étiquettes « Tableau 1 », « Tableau 2 » et « Résultat » sont ajoutées -->

### Exercice 15

Soit un tableau **T** contenant **N** lettres majuscules (de A à Z). **N** étant un entier compris entre 5 et 20. On désire trier en ordre croissant les éléments de **T** en utilisant la méthode de tri comptage **(Tri casier)**.

<u>Principe</u>

1. Compter le nombre d'apparition de chaque élément du tableau T dans un tableau TC.
2. Reconstruire T en tenant compte du nombre d'apparition de chaque élément du tableau T

Si T contient les 10 lettres majuscules suivantes :

| T | G | D | M | A | G | Z | G | A | U | M |
|---|---|---|---|---|---|---|---|---|---|---|

Alors TC (Tableau de comptage) contient les valeurs suivantes :

| TC | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T | U | V | W | X | Y | Z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | 2 | 0 | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |

En fin, en tenant compte du contenu de TC, en reconstruit le tableau T, en insérant chaque indice du tableau autant de fois dans le tableau T.

| T | A | A | D | G | G | G | M | M | U | Z |
|---|---|---|---|---|---|---|---|---|---|---|

Écrire un programme Python qui permet de :

- Saisir la taille du tableau.
- Saisir les éléments de T.
- Trier les éléments de T en utilisant la méthode de tri comptage.
- Afficher les éléments de T.

<!-- TODO vérifier: dans le PDF, les lettres A à Z sont écrites au-dessus de la grille TC (indices) et les valeurs dans la grille ; elles sont regroupées ici dans un seul tableau (valeurs relues sur la capture d'écran) -->

### Exercice 16

Écrire un programme qui permet de saisir un entier composé de 4 chiffres :

- Calculer le min et le max obtenus par la combinaison des chiffres.
- Calculer la différence entre le min et le max
- Répéter le traitement jusqu'à la différence devienne constante ou égale à 0.

<u>Exemple :</u>

> N=1211
> Min =1112   Max=2111
> Différence =N=999
> Min =999   Max=999
> Différence = N=0

### Exercice 17

Écrire un programme qui permet de saisir un tableau de N chaînes de caractères de longueur maximale =30 et composée que par des lettres alphabétiques, avec 5≤n≤25 et d'afficher ce tableau trié **suivant le nombre des voyelles des chaînes** en utilisant la méthode **Tri par sélection** en ordre décroissant.

| T | "Asma" | "Ons" | "Ahmed" | "Mohamed" | "Baccalauréat" | "Youssef" |
|---|---|---|---|---|---|---|

| T Après le Tri | "Baccalauréat" | "Mohamed" | "Youssef" | "Asma" | "Ahmed" | "Ons" |
|---|---|---|---|---|---|---|

### Exercice 18

<!-- TODO vérifier: dans le PDF, l'énoncé de l'exercice 18 est une image (page 3, scan) ; il n'a pas de phrase d'introduction, les trois puces suivent directement le titre « Exercice N°18 » -->

- de remplir un tableau **T** par **n** entiers saisis dans un ordre croissant (**4 ≤ n ≤ 10**)
- de saisir un entier **E** et de l'insérer dans le tableau **T** à la bonne place de sorte que les entiers restent triés dans ce tableau.
- d'afficher les éléments du tableau **T** après insertion de **E**.

**Exemple :** pour **n= 7** et pour le tableau **T** suivant :

| i | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T | 6 | 8 | 12 | 14 | 28 | 37 | 43 |  |  |  |  |

Si on saisit **E = 21**, il sera inséré à la position **5** dans le tableau qui devient :

| i | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T | 6 | 8 | 12 | 14 | 21 | 28 | 37 | 43 |  |  |  |

### Exercice 19

Soit un tableau **T** contenant **N** Entiers (de 0 à 99). **N** étant un entier compris entre 5 et 20. On désire trier en ordre croissant les éléments de **T** en utilisant la méthode de tri comptage **(Tri casier)**.

<u>Principe</u>

1. Compter le nombre d'apparition de chaque élément du tableau T dans un tableau TC.
2. Reconstruire T en tenant compte du nombre d'apparition de chaque élément du tableau T

Si T contient les 10 entiers suivants :

| T | 6 | 12 | 0 | 4 | 6 | 0 | 98 | 5 | 0 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|

Alors TC (Tableau de comptage) contient les valeurs suivantes :

| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | .. | 97 | 98 | 99 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC | 4 | 0 | 0 | 0 | 1 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | .... | 0 | 1 | 0 |

En fin, en tenant compte du contenu de TC, en reconstruit le tableau T, en insérant chaque indice du tableau autant de fois dans le tableau T.

| T | 0 | 0 | 0 | 0 | 4 | 5 | 6 | 6 | 12 | 98 |
|---|---|---|---|---|---|---|---|---|---|---|

Écrire un programme qui permet de :

- Saisir la taille du tableau.
- Saisir les éléments de T.
- Trier les éléments de T en utilisant la méthode de tri comptage.
- Afficher les éléments de T.

<!-- TODO vérifier: dans le PDF, la grille TC de l'exercice 19 compte plusieurs cases de points de suspension (« .. » sous les indices, « .... » dans les valeurs) entre les indices 15 et 97 ; elles sont regroupées en une seule colonne « .. » -->

### Exercice 20

Écrire un programme qui permet de :

- Remplir une matrice M par L\*C lettres majuscules sachant que 4≤L≤20 et pair et 3≤C<19 et impair
- Trier toute la matrice M
- Calculer et afficher le poids de la matrice

<u>N.B</u> : le poids de la matrice est la somme de l'ordre d'une voyelle dans l'alphabet (par exemple A=1, E=5 ....) multiplié par l'indice de la ligne et l'indice de la colonne
