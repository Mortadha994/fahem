---
niveau: 3eme
chapitre: 2
titre: Série N° 3 : Les matrices
type: serie
notions: simulation d'un jeu de dés, matrice et tableaux associés, triangle de Pascal, symétrie d'une matrice, spirale concentrique, sommes cumulées, dessins avec et sans matrice
source: Classroom — Série N° 3 - Les matrices
---

# Série N° 3 : Les matrices

<!-- TODO vérifier: la numérotation continue celle de la série 2 (Problème N°4, puis exercices N°26 à N°35), comme dans le PDF -->

## Série d'exercices

### Problème N°4

Le jeu **Max_Rep_joueurs** se joue à **N** joueurs : chacun lance **à tour de rôle** un dé, ceci est répéter **10 fois**.

Le(s) gagnant(s) est celui (sont ceux) qui a (ont) le plus grand nombre de répétition d'un numéro de dé.

**N.B :** si deux ou plusieurs joueurs ont le même plus grand nombre de répétition d'un numéro de dé, celui qui a le numéro le plus élevé sera déclaré gagnant.

Ecrire l'algorithme d'un programme qui simule le jeu avec **N** joueurs (**2<=N<=20**) en affichera le(s) **numéro** du joueur(s) gagnant, le **numéro le plus répété** dans les 10 lancés ainsi que son **nombre de répétition**.

**Exemple : N=5**

| 2 | 3 | 2 | 5 | 6 | 1 | 2 | 4 | 5 | 4 | → le 1er joueur 2 est le numéro le plus répéter 3 fois |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 4 | 5 | 1 | 5 | 4 | 3 | 1 | 4 | → le 2ème joueur 4 est le numéro le plus répéter 4 fois |
| 5 | 3 | 1 | 2 | 1 | 5 | 4 | 5 | 1 | 5 | → le 3ème joueur 5 est le numéro le plus répéter 4 fois |
| 1 | 6 | 4 | 5 | 2 | 1 | 6 | 3 | 4 | 2 | → le 4ème joueur 6 est le numéro le plus répéter 2 fois |
| 6 | 2 | 4 | 5 | 5 | 2 | 1 | 5 | 1 | 5 | → le 5ème joueur 5 est le numéro le plus répéter 4 fois |

Les gagnants sont :

- le joueur numéro 3 : la face 5 du dé est répéter 4 fois
- le joueur numéro 5 : la face 5 du dé est répéter 4 fois

Deux exemples d'exécution (affichage dans la console Python, programme `MaxRep final.py`) :

> tapez le nombre de joueurs de 2 à 20 5
> 3 2 5 5 6 5 5 3 3 3
> 4 3 2 4 6 3 2 2 4 6
> 5 6 6 6 3 4 1 1 3 2
> 6 6 4 1 5 6 2 5 1 3
> 3 2 5 1 5 2 4 5 5 1
> Les gagnants sont :
> le joueur numéro 1 : la face 5 du dé est répéter 4 fois
> le joueur numéro 5 : la face 5 du dé est répéter 4 fois

> tapez le nombre de joueurs de 2 à 20 5
> 2 2 3 6 5 3 1 1 4 5
> 6 4 1 2 5 1 6 4 2 6
> 6 2 6 1 5 4 6 5 4 2
> 1 1 3 5 6 6 2 3 3 6
> 2 3 2 5 2 3 5 3 1 1
> Les gagnants sont :
> le joueur numéro 2 : la face 6 du dé est répéter 3 fois
> le joueur numéro 3 : la face 6 du dé est répéter 3 fois
> le joueur numéro 4 : la face 6 du dé est répéter 3 fois

<!-- TODO vérifier: dans le PDF, les chiffres les plus répétés sont en gras dans le tableau d'exemple (mise en forme non reproduite) et la ligne « >>> %Run 'MaxRep final.py' » précède chaque exécution (capture d'écran de Thonny) -->

**Travail à faire :**

1. Préciser les structures de données à utilisées pour résoudre le problème.
2. Ecrire un algorithme d'un programme qui simule le jeu.
3. Ecrire les algorithmes des modules envisagés

**Solution :**

Les résultats des lancements seront rangés dans une Matrice M de 20 lignes 10 colonnes d'entier.

| M | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2 | 3 | 2 | 5 | 6 | 1 | 2 | 4 | 5 | 4 |
| 1 | 2 | 4 | 4 | 5 | 1 | 5 | 4 | 3 | 1 | 4 |
| 2 | 5 | 3 | 1 | 2 | 1 | 5 | 4 | 5 | 1 | 5 |
| 3 | 1 | 6 | 4 | 5 | 2 | 1 | 6 | 3 | 4 | 2 |
| 4 | 6 | 2 | 4 | 5 | 5 | 2 | 1 | 5 | 1 | 5 |

Pour ranger le **numéro le plus répéter** et son **nombre de répétition** des 10 lancés de chaque joueur on utilisera un tableau T1 à 2 lignes 20 colonnes d'entier :

- la ligne 1 pour les **numéros les plus répéter**
- la ligne 2 pour les **nombres de répétition**

| T1 | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| 0 | 2 | 4 | 5 | 6 | 5 |
| 1 | 3 | 4 | 4 | 2 | 4 |

<!-- TODO vérifier: le PDF contient, après « Solution : », ces indications de structures de données (elles font partie de la page) ; elles sont conservées telles quelles. Les en-têtes de lignes/colonnes 0..4 de T1 et de M sont ceux du PDF -->

### Exercice N°26

Ecrire l'algorithme d'un module intitulé **Symétrie** permettant de remplir une matrice **M** de **(2*N-1)** lignes et **N** colonnes, comme le montre l'exemple ci-contre sachant que :

- La partie inférieure de la matrice **M** (de la ligne **0** à la ligne **N-1**) représente les valeurs du **triangle de pascal**.
- La partie supérieure de la matrice M (de la ligne **1-N** à la ligne **0**) représente la **symétrie** de la partie inférieure par rapport à la ligne **0**.

**Exemple :** pour N=5 (les lignes sont numérotées de -4 à 4, les colonnes de 1 à 5)

| | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| -4 | 1 | 4 | 6 | 4 | 1 |
| -3 | 1 | 3 | 3 | 1 | |
| -2 | 1 | 2 | 1 | | |
| -1 | 1 | 1 | | | |
| 0 | 1 | | | | |
| 1 | 1 | 1 | | | |
| 2 | 1 | 2 | 1 | | |
| 3 | 1 | 3 | 3 | 1 | |
| 4 | 1 | 4 | 6 | 4 | 1 |

<!-- TODO vérifier: dans le PDF, les lignes 0 à 4 (partie inférieure) sont colorées en bleu -->

### Exercice N°27

Écrire un programme python qui permet d'afficher le triangle de ana de la façon suivante : pour N = 4

<!-- TODO vérifier: « le triangle de ana » transcrit tel quel d'après le PDF (peut-être « triangle de Pascal ») -->

| | -4 | -3 | -2 | -1 | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|---|
| -4 | 1 | 4 | 6 | 4 | 1 | 4 | 6 | 4 | 1 |
| -3 | | 1 | 3 | 3 | 1 | 3 | 3 | 1 | |
| -2 | | | 1 | 2 | 1 | 2 | 1 | | |
| -1 | | | | 1 | 1 | 1 | | | |
| 0 | | | | | 1 | | | | |
| 1 | | | | 1 | 1 | 1 | | | |
| 2 | | | 1 | 2 | 1 | 2 | 1 | | |
| 3 | | 1 | 3 | 3 | 1 | 3 | 3 | 1 | |
| 4 | 1 | 4 | 6 | 4 | 1 | 4 | 6 | 4 | 1 |

<!-- TODO vérifier: tableau lu sur une capture ; dans le PDF la partie colonnes 0 à 4, lignes 0 à 4 est colorée en bleu -->

### Exercice N°28

On se propose d'écrire un programme qui permet de remplir une matrice carré M d'ordre N en spiral concentrique dans le sens des aiguilles d'une montre (2≤N≤100, N pair).

**Exemple :** pour N=4 l'affichage sera de la sorte :

| 1 | 2 | 3 | 4 |
|---|---|---|---|
| 12 | 13 | 14 | 5 |
| 11 | 16 | 15 | 6 |
| 10 | 9 | 8 | 7 |

1) Afficher la matrice M.
2) Analyser le problème en le décomposant en modules.
3) Ecrire l'algorithme de chaque module envisagé.

### Exercice N°29

Ecrire un algorithme qui permet de remplir une Matrice **M** Taille **N*N** (**N** est impair) entiers aléatoires ∈ [1..99] et d'inverser la matrice de la façon suivante.

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
| 6 | 9 | 8 | 7 | 10 |
| 11 | 12 | 13 | 14 | 15 |
| 16 | 19 | 18 | 17 | 20 |
| 25 | 24 | 23 | 22 | 21 |

![deux matrices 5x5 ; des flèches relient les cases symétriques par rapport à la colonne centrale dans la première, la deuxième, la quatrième et la cinquième ligne, les cases des lignes 2 et 4 situées aux colonnes extrêmes (6, 10, 16, 20) restent en place](figures/serie3-ex29-inversion.png)
<!-- TODO figure: à recréer -->

### Exercice N°30

Ecrire un algorithme qui permet de modifier une Matrice **M** Taille **N*N** entiers de la façon suivante : Chaque case **M[i,j]** contient la somme des cases précédentes + la case **M[i,j]**.

**Exemple :**

| 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| 6 | 7 | 8 | 9 | 10 |
| 11 | 12 | 13 | 14 | 15 |
| 16 | 17 | 18 | 19 | 20 |
| 21 | 22 | 23 | 24 | 25 |

devient

| 1 | 3 | 6 | 10 | 15 |
|---|---|---|---|---|
| 21 | 28 | 36 | 45 | 55 |
| 66 | 78 | 91 | 105 | 130 |
| 146 | 163 | 181 | 200 | 220 |
| 241 | 263 | 286 | 310 | 335 |

Annotations du PDF :

- 1+2+3+4+5 = 15 (case en première ligne, dernière colonne)
- 1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17= 163 (case en quatrième ligne, deuxième colonne)

<!-- TODO vérifier: la case de la 3e ligne, 5e colonne vaut 130 dans le PDF (la somme cumulée attendue serait 120) ; transcrit tel quel -->

### Exercice N°31

Ecrire un programme qui affiche le carré ci-dessous de côté **N** (**N** est un entier positif) qui contient **Affiche 1** avec l'utilisation d'une matrice et **Affiche 2** sans l'utilisation d'une matrice.

**Exemple :** N =8

![carré de côté 8 formé de croix X : la première et la dernière ligne contiennent 8 croix, les lignes 2 à 7 contiennent une croix en première colonne et une croix en dernière colonne ; les lignes sont numérotées de 1 à 8 à gauche](figures/serie3-ex31-carre.png)
<!-- TODO figure: à recréer -->

### Exercice N°32

Réutiliser le code du carré pour afficher les formes suivantes **avec et sans matrice** (pour chaque forme le N est indépendant)

![deux formes de 9 lignes de croix X ; à gauche, un quadrillage en croix : lignes 1, 5 et 9 pleines (9 croix) et croix aux colonnes 1, 5 et 9 sur les autres lignes ; à droite, lignes 1, 5 et 9 pleines, croix en colonne 1 et en colonne 9 sur les autres lignes, et sur les lignes 2 à 4 des croix aux colonnes 2 à 5, sur les lignes 6 à 8 des croix aux colonnes 5 à 8](figures/serie3-ex32-formes.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: description des deux formes d'après le rendu à l'écran, détails des colonnes à contrôler sur l'original -->

### Exercice N°33

Réutiliser le code du carré pour afficher les formes suivantes **avec et sans matrice** (pour chaque forme le N est indépendant)

![quatre formes de 9 lignes de croix X, chacune bordée par un cadre (lignes 1 et 9 pleines, colonnes 1 et 9) : en haut à gauche le cadre avec une diagonale descendante, en haut à droite le cadre avec une diagonale montante, en bas à gauche le cadre avec un triangle plein au-dessus de la diagonale, en bas à droite le cadre avec un triangle plein en dessous de la diagonale](figures/serie3-ex33-formes.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: description des quatre formes d'après le rendu à l'écran, à contrôler sur l'original -->

### Exercice N°34

<!-- TODO vérifier: l'exercice N°34 n'a pas d'énoncé écrit dans le PDF, seulement quatre dessins -->

![quatre formes en croix X sur 6 lignes : en haut à gauche un triangle creux de sommet en haut (sommet en ligne 1, base pleine de 11 croix en ligne 6) ; en haut à droite un triangle creux inversé à base en ligne 1 de 11 croix et sommet creux vers le bas, dernière ligne pleine de 11 croix ; en bas à gauche un triangle plein de 1, 3, 5, 7, 9, 11 croix du haut vers le bas ; en bas à droite un triangle plein d'étoiles « * » de 10 lignes dont chaque ligne k contient 2k-1 étoiles](figures/serie3-ex34-formes.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: description des quatre formes d'après le rendu à l'écran, à contrôler sur l'original -->

### Exercice N°35

Créer un programme qui permet de dessiner les triangles suivants :

![deux triangles d'étoiles « * » sur 9 lignes numérotées de 1 à 9 ; à gauche la ligne k contient k étoiles (de 1 à 9) ; à droite la ligne k contient 10-k étoiles (de 9 à 1)](figures/serie3-ex35-triangles.png)
<!-- TODO figure: à recréer -->
