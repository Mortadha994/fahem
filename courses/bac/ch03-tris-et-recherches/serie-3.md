---
niveau: bac
chapitre: 3
titre: Série N° 3 : Tri & recherche
type: serie
notions: tournage à la main, identification d'un algorithme de tri, tri Shell, tri par comptage, recherche dichotomique, recherche trichotomique
source: Classroom — Série N°1+2+3 - Les Tris et les recherches (série 3 - les tris(Bac).pdf)
---

# Série N° 3 : Tri & recherche

<!-- TODO vérifier: le PDF (3 pages) est intitulé « Série 3 : (Tri & recherche) » ; la numérotation des exercices (21-A à 30) est conservée telle quelle -->

## Série d'exercices

### Exercice 21-A

Voici le début de la trace d'exécution d'un algorithme de tri :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 98 | 56 | 4 | 78 | 7 | 10 | 5 |
| Répétition 2 | 98 | 78 | 4 | 56 | 7 | 10 | 5 |
| ... |  |  |  |  |  |  |  |

Q1) De quel algorithme de tri s'agit-il ? Donner le principe de fonctionnement de cet algorithme

Q2) Compléter le tournage à la main de cet algorithme :

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: la grille de réponse du PDF reprend les lignes « Etat initial », « Répétition1 » et « Répétition 2 » ci-dessus, suivies de quatre lignes vides ; elle n'est pas reproduite -->

Q3) proposer un algorithme de ce tri :

### Exercice 21-B

Voici le début de la trace d'exécution d'un algorithme de tri :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 10 | 4 | 56 | 7 | 78 | 5 | 98 |
| Répétition 2 | 4 | 10 | 7 | 56 | 5 | 78 | 98 |
| ... |  |  |  |  |  |  |  |

Q1) De quel algorithme de tri s'agit-il ? Donner le principe de fonctionnement de cet algorithme

Q2) Compléter le tournage à la main de cet algorithme :

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: la grille de réponse du PDF reprend les trois premières lignes de la trace, suivies de quatre lignes vides ; elle n'est pas reproduite -->

Q3) proposer un algorithme de ce tri :

### Exercice 21-C

Voici le début de la trace d'exécution d'un algorithme de tri :

| Etat initial : T | 10 | 56 | 78 | 4 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 56 | 10 | 78 | 4 | 7 | 98 | 5 |
| Répétition 2 | 78 | 56 | 10 | 4 | 7 | 98 | 5 |

Q1) De quel algorithme de tri s'agit-il ? Donner le principe de fonctionnement de cet algorithme

Q2) Compléter le tournage à la main de cet algorithme :

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: la grille de réponse du PDF reprend les trois premières lignes de la trace, suivies de quatre lignes vides ; elle n'est pas reproduite ; contrairement aux exercices 21-A et 21-B, la trace de 21-C n'a pas de ligne « ... » -->

Q3) proposer un algorithme de ce tri :

### Exercice 21-D

Voici le début de la trace d'exécution d'un algorithme de tri :

| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T | 10 | 56 | 4 | 78 | 7 | 98 | 5 | 1 | 12 | 3 | -5 | 2 | -9 |

Q1) Donner le principe de fonctionnement du tri Shell.

Q2) proposer un algorithme de ce tri.

Q3) Compléter le tournage à la main de cet algorithme.

### Exercice 22

Ecrire une procédure « **Ranger(ch)** » qui permet pour une chaine de caractère non vide **ch** formé par des mots séparés par un seul espace d'ordonner ses mots dans l'ordre décroissant **de** leurs longueurs.

<u>Exemple</u> :

Pour la chaîne ch : à force de forger on devient forgeron

Elle devient : forgeron devient forger force de on à

### Exercice 23

Ecrire l'algorithme d'une fonction « **plus_grand(n)** » qui permet pour un entier positif non nul N de retourner l'entier le plus grand formé par les chiffres de N.

Exemple si N=12178, le résultat sera 87211

### Exercice 24

Ecrire l'algorithme d'une fonction «**verif_tri(T,n)** » qui teste l'état d'un tableau T de n éléments et retourne l'un de ces trois valeurs : «  trié par ordre croissant » ou « trié par ordre décroissant » ou « non trié »

### Exercice 25

- Ecrire l'algorithme d'une fonction «**recherche_pos_insert(x,t,n)** » qui permet de chercher la bonne position de l'insertion de l'entier x dans un tableau **trié** T de n entiers.
- Ecrire l'algorithme d'une procédure qui permet de remplir et trier (par ordre décroissant) au fur et à mesure (remplissage par insertion à la bonne position) un tableau T par des valeurs aléatoires compris entre 0 et 50.

### Exercice 26

On considère un tableau T de N entier distinct, rangés par ordre croissant, et un entier E.

Ecrire une procédure **Affiche (T,N,E)** qui :

- Si E existe dans T, affiche l'indice exprimant le rang de E . . pour ce faire écrire la fonction **Rech_Dicho (T,N,E)**
- Si E ne figure pas dans T, affiche le nombre appartenant au tableau T qui est le plus proche de E. pour ce faire écrire la fonction **plus_proche(T,N,E)**

### Exercice 27

Le tri à bulle après la première répétition il compare deux à deux et il place la grande valeur à la fin du tableau en ordre croissant, on souhaite modifier ce tri pour qu'à chaque répétition il place la grande valeur à la fin et la petite valeur au début et il refaire le même traitement avec les autres cases.

### Exercice 28

On se propose de chercher un entier X donné dans un tableau T de n entiers (le tableau est trié en ordre croissant) en utilisant la méthode de recherche **Trichotomique**.

Le principe de cette méthode est décrit comme suit :

- On compare l'entier à chercher X avec T[p1] et T[p2]
  - Si X est égale à l'un de deux, la recherche est terminée,
  - sinon s'il est inférieur à T[p1] on refait la recherche dans la partie gauche du tableau qui réside avant t[p1],
  - sinon s'il est inférieur à T[p2] on refait la recherche dans la partie du milieu du tableau qui réside entre p1 et p2,
  - sinon on refait la recherche dans la partie droite du tableau qui réside après T[p2].

Sachant que **P1=(2\*D+F) Div 3** et **P2=(D+2\*F) Div 3** où **D** et **F** sont respectivement les indices du début et de la fin de la partie du tableau dans laquelle on va continuer la recherche.

<u>Travail à réaliser</u> :

Établir l'algorithme du module recherche « **Trichotomique** » en une méthode **itérative**.

### Exercice 29

Le tri par comptage dans l'ordre croissant d'un tableau **T1** d'éléments distincts consiste à déterminer pour chaque élément de **T1** sa position dans un tableau trié **T2** qui égale au nombre d'éléments de **T1** qui lui sont strictement inférieures.

| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| T1 | 15 | 2 | 14 | 7 | 9 | 17 | 11 |
| T2 | 2 | 7 | 9 | 11 | 14 | 15 | 17 |

La valeur **15** qui est le premier élément du tableau **T1** possède **5** éléments qui lui sont strictement inférieurs, donc sa position dans le tableau **T2** est égale à **5**.

**Travail demandé :**

1. Soit **F** un fichier d'au maximum **100** entiers. Ecrire un algorithme d'une fonction nommée **Comptage(F,a)** permettant de retourner le nombre d'éléments dans le fichier **F** qui sont strictement inférieurs à un entier **a**.
2. En se basant sur le principe de tri par comptage décrit précédemment et en utilisant la fonction **Comptage**, écrire un module nommé **Tri_Comptage** qui permet de trier dans un ordre croissant les éléments du fichier **F** dans un deuxième fichier d'entiers **F2**.

N.B : On pourra placer les éléments triés dans un tableau puis les transférer dans le fichier **F2**.

<!-- TODO vérifier: dans le PDF, T1 et T2 sont deux grilles séparées, chacune avec sa ligne d'indices 0 à 6 ; elles sont regroupées ici dans un seul tableau -->

### Exercice 30

On donne ci-dessous, l'algorithme d'une procédure tri dont le rôle est de trier par ordre croissant les éléments d'un tableau T de type W, vecteur de réels.

```algorithme
Procédure Tri (pas, n : entier ; @ t : w)
Début
    Pour i de pas à n-1 Faire
        Aux ← t[i]
        Pos ← i
        DECALER (pas, pos, t)
        T[pos] ← aux
    Fin Pour
Fin
```

1. Pour une valeur de **pas = 1**. A quoi rassemble telle cette méthode de tri ?
2. Donner un algorithme de la procédure **DECALER** et préciser le type de transfert des paramètres utilisés.
3. Utiliser cette procédure de Tri pour déduire une solution d'un algorithme de tri **Shell**.

<!-- TODO vérifier: le PDF écrit « faire » (minuscule) et « Fin Pour » ; normalisé en « Faire » ; « rassemble telle » est transcrit tel quel -->
