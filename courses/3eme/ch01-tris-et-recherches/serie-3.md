---
niveau: 3eme
chapitre: 1
titre: Série N° 3 : Tri & recherche
type: serie
notions: trace d'exécution, tri par sélection, tri à bulles, recherche dichotomique, recherche trichotomique, insertion dans un tableau trié, matrices
source: Classroom — Série N°3 - Les Tris et les recherches
---

# Série N° 3 : Tri & recherche

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes (« Sé rié 3 », « Voici lé début dé la tracé ») ; accents rétablis d'après le rendu à l'écran. La numérotation des exercices continue celle de la série 2 (exercices 21 à 35), comme dans le PDF -->

## Série d'exercices

### Exercice 21

Voici le début de la trace d'exécution d'un algorithme de tri :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 98 | 56 | 4 | 78 | 7 | 10 | 5 |
| Répétition 2 | 98 | 78 | 4 | 56 | 7 | 10 | 5 |
| ... | | | | | | | |

Q1) De quel algorithme de tri s'agit-il ? Donner le principe de fonctionnement de cet algorithme

Q2) Compléter le tournage à la main de cet algorithme :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 98 | 56 | 4 | 78 | 7 | 10 | 5 |
| Répétition 2 | 98 | 78 | 4 | 56 | 7 | 10 | 5 |

<!-- grille de réponse supprimée -->

Q3) proposer un algorithme de ce tri :

### Exercice 22

Voici le début de la trace d'exécution d'un algorithme de tri :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 10 | 4 | 56 | 7 | 78 | 5 | 98 |
| Répétition 2 | 4 | 10 | 7 | 56 | 5 | 78 | 98 |
| ... | | | | | | | |

Q1) De quel algorithme de tri s'agit-il ? Donner le principe de fonctionnement de cet algorithme

Q2) Compléter le tournage à la main de cet algorithme :

| Etat initial : T | 10 | 56 | 4 | 78 | 7 | 98 | 5 |
|---|---|---|---|---|---|---|---|
| Répétition1 | 10 | 4 | 56 | 7 | 78 | 5 | 98 |
| Répétition 2 | 4 | 10 | 7 | 56 | 5 | 78 | 98 |

<!-- grille de réponse supprimée -->

Q3) proposer un algorithme de ce tri :

### Exercice 23

Ecrire une procédure « Ranger(ch) » qui permet pour une chaine de caractère non vide ch formé par des mots séparés par un seul espace d'ordonner ses mots dans l'ordre décroissant de leurs longueurs.

**Exemple :**

Pour la chaîne ch : à force de forger on devient forgeron

Elle devient : forgeron devient forger force de on à

### Exercice 24

Ecrire l'algorithme d'une fonction « plus_grand(n) » qui permet pour un entier positif non nul N de retourner l'entier le plus grand formé par les chiffres de N.

Exemple si N=12178, le résultat sera 87211

### Exercice 25

Ecrire l'algorithme d'une fonction « verif_tri(T,n) » qui teste l'état d'un tableau T de n éléments et retourne l'un de ces trois valeurs : « trié par ordre croissant » ou « trié par ordre décroissant » ou « non trié »

### Exercice 26

Ecrire l'algorithme d'une fonction « recherche_pos_insert(x,t,n) » qui permet de chercher la bonne position de l'insertion de l'entier x dans un tableau trié T de n entiers.

### Exercice 27

Ecrire l'algorithme d'une procédure qui permet de remplir et trier (par ordre décroissant) au fur et à mesure (remplissage par insertion à la bonne position) un tableau T par des valeurs aléatoires compris entre 0 et 50.

### Exercice 28

On considère un tableau T de N entier distinct, rangés par ordre croissant, et un entier E.

Ecrire une procédure Affiche (T,N,E) qui :

- Si E existe dans T , affiche l'indice exprimant le rang de E . . pour ce faire écrire la fonction Rech_Dicho (T,N,E)
- Si E ne figure pas dans T, affiche le nombre appartenant au tableau T qui est le plus proche de E. pour ce faire écrire la fonction plus_proche(T,N,E)

### Exercice 29

(Algo)

On se propose de chercher un entier X donné dans un tableau T de n entiers (le tableau est trié en ordre croissant) en utilisant la méthode de recherche Trichotomique.

Le principe de cette méthode est décrit comme suit :

- On compare l'entier à chercher X avec T[p1] et T[p2]
- Si X est égale à l'un de deux, la recherche est terminée, sinon s'il est inférieur à T[p1] on refait la recherche dans la partie gauche du tableau qui réside avant t[p1], sinon s'il est inférieur à T[p2] on refait la recherche dans la partie du milieu du tableau qui réside entre p1 et p2, sinon on refait la recherche dans la partie droite du tableau qui réside après T[p2] .

Sachant que P1=(2*D+F) Div 3 et P2=(D+2*F) Div 3 où D et F sont respectivement les indices du début et de la fin de la partie du tableau dans laquelle on va continuer la recherche.

**Travail à réaliser :**

Établir l'algorithme du module recherche « Trichotomique » en une méthode itérative.

<!-- TODO vérifier: le PDF écrit « T[p1] » / « t[p1] » / « p1 » avec des casses différentes, et P1 = (2*D+F) Div 3 ; transcrit tel quel -->

### Exercice 30

Le tri à bulle après la première répétition il compare deux à deux et il place la grande valeur à la fin du tableau en ordre croissant, on souhaite modifier ce tri pour qu'à chaque répétition il place la grande valeur à la fin et la petite valeur au début et il refaire le même traitement avec les autres cases.

### Exercice 31

Tri du singe Un singe trie les cartes de la façon suivante : il prend les cartes, les jette en l'air, les ramasse puis regarde si elles sont triées. Si oui, il s'arrête, sinon il relance les cartes.

Implémenter et tester ce tri sur le tableau t=[3,1,9,4,4].

### Exercice 32

Soit le code Python suivant :

```python
def quoi(sh):
    echange=True
    while echange:
        echange=False
        for i in range(1,len(sh)):
            c1=sh[i-1]
            c2=sh[i]
            if (c2>c1):
                sh=sh[:i-1]+c2+c1+sh[i+1:]
                echange=True
    return sh
ch=input('saisir chaine')
ch=quoi(ch)
print(ch)
```

1) Compléter la trace d'exécution pour ch="info" puis pour ch="ALGO"

| ch | sh | i | echange |
|---|---|---|---|
| info | | | |

| ch | sh | i | echange |
|---|---|---|---|
| ALGO | | | |

<!-- grille de réponse supprimée -->

### Exercice 33

Écrire un programme permettant de trier chaque ligne de la matrice et d'afficher les éléments entiers d'une matrice carrée M comportant N lignes et N colonnes (5≤N<30)) lus au hasard (de 1 à 1000) en utilisant la méthode de Tri à bulle.

1. Décomposer ce problème en modules et l'algorithme des modules proposés.
2. Traduisez la solution en un programme python.

### Exercice 34

Écrire un programme permettant de trier chaque colonne de la matrice et d'afficher les éléments entiers d'une matrice carrée M comportant N lignes et N colonnes (5≤N<30) lus au hasard (de 1 à 1000) en utilisant la méthode de Tri par sélection dans l'ordre décroissant.

1. Décomposer ce problème en modules et l'algorithme des modules proposés.
2. Traduisez la solution en un programme python.

### Exercice 35

Écrire un programme qui permet de :

- Remplir une matrice M par L*C lettres majuscules sachant que 4≤L≤20 et pair et 3≤C<19 et impair
- Trier toute la matrice M
- Calculer et afficher le poids de la matrice

N.B : le poids de la matrice est la somme de l'ordre d'une voyelle dans l'alphabet (par exemple A=1, E=5 ....) multiplié par l'indice de la ligne +1 et l'indice de la colonne +1
