---
niveau: 3eme
chapitre: 1
titre: Série N° 2 : Tri & Recherche
type: serie
notions: tri par comptage, tri par sélection, insertion dans un tableau trié, fusion de tableaux, algorithme modulaire, matrices
source: Classroom — Série N°2 - Les Tris et les recherches
---

# Série N° 2 : Tri & Recherche

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes (« Sé rié N° ») ; accents rétablis d'après le rendu à l'écran. La numérotation des exercices continue celle de la série 1 (exercices 11 à 20), comme dans le PDF -->

## Série d'exercices

### Exercice 11

Écrire un programme intitulé Tri_vecteur permettant de trier et d'afficher un tableau T de N entiers distincts (5<N<20) selon le principe suivant :

Trouver NB le nombre de case inférieur à T[i] et placer T[i] dans le tableau R à la position NB.

Pour chaque élément de T :

**Exemple :**

| T | 6 | 2 | 0 | 5 | 12 | 25 |
|---|---|---|---|---|---|---|

Trois valeurs sont inférieures au premier élément de T. cet élément sera placé à la position quatre du tableau R

| R | | | | 6 | | |
|---|---|---|---|---|---|---|

Une seule valeur est inférieure au deuxième élément de T. cet élément sera placé à la position deux du tableau R

| R | | 2 | | 6 | | |
|---|---|---|---|---|---|---|

Le résultat affiché est R qui sera un tableau trié dans l'ordre croissant.

<!-- TODO vérifier: les tableaux R du PDF sont partiellement remplis (cases vides) ; transcrits avec cases vides. Le texte « position quatre » / « position deux » correspond à la 4e et à la 2e case -->

### Exercice 12

Soit un tableau T1 contenant N lettres majuscule (de A à Z), N étant un entier compris entre 5 et 20. On désire triés en ordre croissant les éléments de T1 et les ranges dans un tableau T2 en utilisant le principe suivant :

1. Cherche la lettre qui a le plus petit code ASCII dans T1.
2. a) ranger cette lettre dans T2.
   b) remplacer cette lettre par '*' dans T1.
3. Répéter n fois les étapes 1 et 2.

Écrire un programme qui permet de :

- Saisir les éléments de T1
- Trier les éléments de T1 et les ranger dans T2
- Afficher les éléments de T2

### Exercice 13

Écrire l'algorithme modulaire d'un programme nommé TRI_TAB qui permet de trier par ordre décroissant les éléments d'un tableau A de N entiers positifs (5<N<20) dans un tableau B de même dimension.

1. Chercher le maximum de A.
2. Placer le maximum dans B.
3. Placer ce maximum par -1 dans A
4. Refaire les étapes 1, 2 et 3 jusqu'à ce que le tableau A soit entièrement composé par des -1

N.B : prévoir l'affichage des éléments du Tableau B.

### Exercice 14

Écrire un programme qui saisit deux tableaux d'entiers triés par ordre croissant et les fusionnent dans un nouveau tableau en respectant l'ordre croissant des entiers.

**Exemple :**

| | 1 | 5 | 7 | 9 |
|---|---|---|---|---|
| | -8 | 0 | 3 | |

Résultat de la fusion :

| -8 | 0 | 1 | 3 | 5 | 7 | 9 |
|---|---|---|---|---|---|---|

<!-- TODO vérifier: dans le PDF, les deux tableaux de départ sont reliés par une accolade au tableau résultat ; mise en forme en tableaux reconstituée -->

### Exercice 15

Soit un tableau T contenant N lettres majuscules (de A à Z). N étant un entier compris entre 5 et 20. On désire trier en ordre croissant les éléments de T en utilisant la méthode de tri comptage (Tri casier).

**Principe**

1. Compter le nombre d'apparition de chaque élément du tableau T dans un tableau TC.
2. Reconstruire T en tenant compte du nombre d'apparition de chaque élément du tableau T

Si T contient les 10 lettres majuscules suivantes :

| T | G | D | M | A | G | Z | G | A | U | M |
|---|---|---|---|---|---|---|---|---|---|---|

Alors TC (Tableau de comptage) contient les valeurs suivantes :

| TC | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T | U | V | W | X | Y | Z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | 2 | 0 | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |

En fin, en tenant compte du contenu de TC, en reconstruit le tableau T, en insérant chaque indice du tableau autant de fois dans le tableau T.

| T | A | A | D | G | G | G | M | M | U | Z |
|---|---|---|---|---|---|---|---|---|---|---|

Écrire un programme Python qui permet de :

- Saisir la taille du tableau.
- Saisir les éléments de T.
- Trier les éléments de T en utilisant la méthode de tri comptage.
- Afficher les éléments de T.

### Exercice 16

Écrire un programme qui permet de saisir un entier composé de 4 chiffres :

- Calculer le min et le max obtenus par la combinaison des chiffres.
- Calculer la différence entre le min et le max
- Répéter le traitement jusqu'à la différence devienne constante ou égale à 0.

**Exemple :**

```
N=1211
Min =1112 Max=2111
Différence =N=999
Min =999 Max=999
Différence = N=0
```

### Exercice 17

Écrire un programme qui permet de saisir un tableau de N chaînes de caractères de longueur maximale =30 et composée que par des lettres alphabétiques, avec 5≤n≤25 et d'afficher ce tableau trié suivant le nombre des voyelles des chaînes en utilisant la méthode Tri par sélection en ordre décroissant.

| T | "Asma" | "Ons" | "Ahmed" | "Mohamed" | "Baccalauréat" | "Youssef" |
|---|---|---|---|---|---|---|

| T Après le Tri : | "Baccalauréat" | "Mohamed" | "Youssef" | "Asma" | "Ahmed" | "Ons" |
|---|---|---|---|---|---|---|

### Exercice 18

- de remplir un tableau T par n entiers saisis dans un ordre croissant (4 ≤ n≤ 10)
- de saisir un entier E et de l'insérer dans le tableau T à la bonne place de sorte que les entiers restent triés dans ce tableau.
- d'afficher les éléments du tableau T après insertion de E.

<!-- TODO vérifier: dans le PDF, l'exercice 18 n'a pas de phrase d'introduction (« Écrire un programme qui permet : » semble manquer) ; la page est une image scannée, transcrite d'après le rendu à l'écran -->

**Exemple :** pour n= 7 et pour le tableau T suivant :

| T | 6 | 8 | 12 | 14 | 28 | 37 | 43 | | | | |
|---|---|---|---|---|---|---|---|---|---|---|---|
| indice | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |

Si on saisit E = 21, il sera inséré à la position 5 dans le tableau qui devient :

| T | 6 | 8 | 12 | 14 | 21 | 28 | 37 | 43 | | | |
|---|---|---|---|---|---|---|---|---|---|---|---|
| indice | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |

### Exercice 19

Soit un tableau T contenant N Entiers (de 0 à 99). N étant un entier compris entre 5 et 20. On désire trier en ordre croissant les éléments de T en utilisant la méthode de tri comptage (Tri casier).

**Principe**

1. Compter le nombre d'apparition de chaque élément du tableau T dans un tableau TC.
2. Reconstruire T en tenant compte du nombre d'apparition de chaque élément du tableau T

Si T contient les 10 entiers suivants :

| T | 6 | 12 | 0 | 4 | 6 | 0 | 98 | 5 | 0 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|

Alors TC (Tableau de comptage) contient les valeurs suivantes :

| TC | 4 | 0 | 0 | 0 | 1 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | .. | .. | 0 | 0 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | .. | .. | 96 | 97 | 98 | 99 |

<!-- TODO vérifier: le tableau TC du PDF est abrégé (points de suspension « .... ») et l'image est peu lisible ; les valeurs ci-dessus sont celles qui correspondent à T (compte de chaque valeur : 0 → 4, 4 → 1, 5 → 1, 6 → 2, 12 → 1, 98 → 1), l'alignement exact des cases du PDF est à contrôler -->
<!-- TODO figure: à recréer -->
![tableau de comptage TC de l'exercice 19 (indices 0 à 99, avec points de suspension)](figures/serie2-ex19-tc.png)

En fin, en tenant compte du contenu de TC, en reconstruit le tableau T, en insérant chaque indice du tableau autant de fois dans le tableau T.

| T | 0 | 0 | 0 | 0 | 4 | 5 | 6 | 6 | 12 | 98 |
|---|---|---|---|---|---|---|---|---|---|---|

Écrire un programme qui permet de :

- Saisir la taille du tableau.
- Saisir les éléments de T.
- Trier les éléments de T en utilisant la méthode de tri comptage.
- Afficher les éléments de T.

### Exercice 20

Écrire un programme qui permet de :

- Remplir une matrice M par L*C lettres majuscules sachant que 4≤L≤20 et pair et 3≤C<19 et impair
- Trier toute la matrice M
- Calculer et afficher le poids de la matrice

N.B : le poids de la matrice est la somme de l'ordre d'une voyelle dans l'alphabet (par exemple A=1, E=5 ....) multiplié par l'indice de la ligne et l'indice de la colonne
