---
niveau: bac
chapitre: 2
titre: Séries N° 1 et 2 : La récursivité
type: serie
notions: modules récursifs, fonctions récursives sur les chaînes, fonctions récursives sur les tableaux, tris et recherches récursifs, suite de Fibonacci, matrices
source: Classroom — Série N°1 & 2 - La récursivité (série 1 + 2 récursivité.pdf)
---

# Série N° 1 & 2 : La récursivité

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Série N° : 1 & 2 (récursivité) » ; il contient une seule liste continue de 45 exercices, sans séparation entre la série 1 et la série 2 ; la numérotation d'origine (1 à 45) est conservée -->

<!-- TODO vérifier: mots-clés harmonisés dans les algorithmes en Si, Alors, Sinon, Fin Si (l'original écrit alors / sinon / Finsi / Fin si), Ecrire, Lire, Début, Fin -->

## Série d'exercices

### Exercice 1

Soit l'algorithme de la procédure « quefaire » suivante :

```algorithme
Procédure quefaire (@ x : Entier)
Début
    Ecrire ("saisir un entier >0")
    Lire (x)
    Si (x<0) Alors
        quefaire(x)
    Fin Si
Fin
```

1. Quel est le rôle de la procédure que faire ?
2. Traduire cette procédure en python

<!-- TODO vérifier: l'original écrit « Fin. » (avec un point) à la fin de la procédure et le message « saisir un entier >0 » alors que la condition de relance est « x<0 » ; transcrit tel quel -->

### Exercice 2

Ecrire une fonction récursive qui teste l'existence d'une lettre dans une chaîne de caractères donné.

### Exercice 3

Ecrire une fonction récursive qui détermine X\*n avec X un réel donné et N un entier donné.

<!-- TODO vérifier: « X*n » (n minuscule) dans l'énoncé original, transcrit tel quel -->

### Exercice 4

Ecrire une fonction récursive qui retourne le nombre des voyelles d'une chaine donnée.

![Cinq lettres A E I O U Y décorées (illustration à côté de l'énoncé de l'exercice 5)](figures/voyelles-illustration.png)
<!-- TODO figure: à recréer -->

### Exercice 5

Un mot palindrome s'il se lit de la même façon dans les deux sens (droit et gauche)

Exemple : radar, été

1. Proposez un algorithme itératif d'une fonction permettant de tester si une chaine CH est palindrome
2. Chercher une relation de récursivité et déduisez l'algorithme récursif de la fonction palindrome

### Exercice 6

Ecrire une fonction récursive qui permet d'inverser une chaîne de caractères donné (miroir)

### Exercice 7

Ecrire un programme contenant deux procédures récursives permettant la saisie et l'affichage d'un tableau de N entiers positifs.

### Exercice 8

Ecrire une fonction récursive nommée **Somme_chiffre** qui retourne la somme des chiffres d'un nombre donné

**Exemple :**

317 → 3 + 1 + 7 = 11

### Exercice 9

Convertir, en python, la procédure itérative ci-dessous en une procédure récursive

```python
def afficher ( ) :
    For i in range (1,11) :
        print ("Baccalauréat 2023")
```

<!-- TODO vérifier: l'original écrit « For » avec une majuscule (Python demande « for ») ; transcrit tel quel -->

### Exercice 10

On propose la procédure itérative suivante

```python
def Table_Multi ( ) :
    for i in range (1,11) :
        for j in range (1,11) :
            print (i*j, end="        ")
    print()
```

*Travail demandé*

Quel est le rôle de cette procédure ?

Convertir cette procédure itérative en une procédure récursive ?

<!-- TODO vérifier: la chaîne de end="…" contient plusieurs espaces dans l'original (nombre exact non lisible) ; l'indentation du dernier print() est celle du PDF (au niveau de la boucle for i) -->

### Exercice 11

Donner l'algorithme d'une fonction qui vérifie si une chaine est formée uniquement par des lettres alphabétiques ou non.

### Exercice 12

Ecrire une fonction permettant de calculer la somme suivante :

**Somme de cubes S(n) = 1³+2³+3³+…………..+n³**

### Exercice 13

Ecrire une fonction permettant de calculer le pgcd de 2 entiers a et b avec 2 méthodes (différence et Euclide)

### Exercice 14

Ecrire l'algorithme d'une fonction récursive qui permet de calculer la somme des éléments d'un tableau T de N entiers

### Exercice 15

Ecrire l'algorithme d'une fonction récursive qui étant donnée un entier M, détermine la valeur la plus proche de M dans un tableau T de N entiers

### Exercice 16

Ecrire l'algorithme d'une procédure récursive qui permet d'inverser un tableau

### Exercice 17

Ecrire l'algorithme d'une fonction récursive qui permet de faire une recherche séquentielle d'un élément X dans un tableau T.

### Exercice 18

Ecrire l'algorithme d'une fonction récursive qui permet de faire une recherche dichotomique d'un élément X dans un tableau T déjà trié

### Exercice 19

Ecrire l'algorithme d'une procédure récursive qui permet de faire un tri à bulle d'un tableau T de N entiers

### Exercice 20

Ecrire l'algorithme d'une procédure récursive qui permet de faire un tri par sélection d'un tableau T de N entiers

### Exercice 21

Ecrire l'algorithme d'une procédure récursive qui permet de faire un tri par insertion d'un tableau T de N entiers

### Exercice 22

Ecrire l'algorithme d'une procédure récursive qui permet de faire un tri shell d'un tableau T de N entiers

### Exercice 23

Ecrire l'algorithme d'une fonction récursive qui permet de rechercher la position de la première occurrence d'un entier A dans un tableau

### Exercice 24

Ecrire l'algorithme d'une fonction récursive qui permet de rechercher la position de la dernière occurrence d'un entier A dans un tableau

### Exercice 25

Ecrire l'algorithme d'une fonction récursive qui permet de calculer le nombre d'occurrence d'une chaine CH dans un tableau T de N chaines

### Exercice 26

Ecrire l'algorithme d'une fonction récursive qui permet de chercher la valeur maximale d'un tableau T de N entiers

### Exercice 27

Ecrire l'algorithme d'une fonction récursive qui permet de chercher la valeur minimale d'un tableau T de N entiers

### Exercice 28

Ecrire l'algorithme d'une fonction récursive qui permet de déterminer si un entier N saisie au clavier est premier ou non

### Exercice 29

Un nombre parfait est un nombre qui est égale à la somme de ses diviseurs sauf lui-même

**Exemple :** 6 est parfait car 6=1+2+3

Ecrire l'algorithme d'une fonction récursive qui vérifie si un entier N est parfait ou non

### Exercice 30

Ecrire l'algorithme d'une fonction récursive qui affiche si deux chaînes s1 et s2 sont anagrammes.

S1 et s2 sont anagrammes s'ils se composent de même lettres. Exemple : s1= « chien », s2= « niche »

### Exercice 31

Ecrire l'algorithme d'une fonction récursive qui permet d'évaluer une chaîne composée par des nombres et des signes +

**Exemple :** pour la chaîne ch= « 2+13+5+1 » le résultat est 21

### Exercice 32

Ecrire l'algorithme d'une fonction récursive qui permet d'évaluer une chaîne composée par des nombres et des signes + et des signes -

**Exemple :** pour la chaîne ch= « 20-3+6+1-5 » le résultat est 19

### Exercice 33

Ecrire l'algorithme d'une fonction récursive qui permet d'effacer tous les chiffres d'une chaîne alphanumérique donnée.

### Exercice 34

Ecrire l'algorithme d'une fonction récursive qui permet d'effacer superflus tous les espaces d'une phrase donnée.

### Exercice 35

Ecrire l'algorithme d'une fonction récursive qui permet de calculer le nombre d'occurrence d'un caractère donné dans une chaîne donnée.

### Exercice 36

Ecrire l'algorithme d'une fonction récursive qui permet de calculer la Nème valeur (n>0) de la suite Fibonacci f définie comme suit :

- F₀ = 0
- F₁ = 1
- Fₙ = Fₙ₋₂ + Fₙ₋₁ pour n ≥ 2.

Les premiers termes de la suite de Fibonacci :

| F₀ | F₁ | F₂ | F₃ | F₄ | F₅ | F₆ | F₇ | F₈ | F₉ | F₁₀ | F₁₁ | F₁₂ | F₁₃ | F₁₄ | F₁₅ | F₁₆ | … | Fₙ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 2 | 3 | 5 | 8 | 13 | 21 | 34 | 55 | 89 | 144 | 233 | 377 | 610 | 987 | … | Fₙ₋₁ + Fₙ₋₂ |

### Exercice 37

Ecrire l'algorithme d'un programme qui permet de décomposer un entier N donné (2<=N<=100) en produit des facteurs premiers et d'afficher N et le produit de ses facteurs trouvés

*Exemple :* Pour N=75, le résultat est : 75=3\*5\*5     Pour N=60, le résultat est : 60=2\*2\*3\*5

### Exercice 38

Ecrire l'algorithme d'un programme qui calcule la somme des puissances successives des chiffres (exposant égal à leur rang en partant de la gauche) d'un entier positif donnée

**Exemple :** Pour N=342 le résultat est 3¹+4²+2³=27

### Exercice 39

Ecrire l'algorithme d'un programme qui permet de saisir une phrase et l'affiche renversée

<u>N.B :</u> la phrase commence obligatoirement par une lettre et ses mots sont séparés par un seul espace

**Exemple :**

**Votre phrase :** "des exercices d'informatique"

**Résultat :** "d'informatique exercices des"

### Exercice 40

Ecrire l'algorithme d'une fonction récursive qui permet de calculer la somme suivante :

**S=1 + 2/2! + 3/3! + 4/4! + 5/5! + … + N/N!**

### Exercice 41

Ecrire l'algorithme d'une fonction récursive qui permet de mixer deux chaînes CH1 et CH2 saisies au clavier

**Exemple :**

- CH1= « INFO » et CH2= « MIXE » la chaîne résultat est : « IMNIFXOE »
- CH1= « ABC » et CH2= « DEFG » la chaîne résultat est : « ADBECFG »

### Exercice 42

1. Donner l'algorithme de la fonction récursive nommée « som_chif » qui prend en paramètre une chaine de caractères ch pour calculer et renvoyer la somme de ses chiffres.
2. Traduire votre fonction en python.

*Exemple :* Pour ch= « Bac2023 » , la fonction doit retourner la valeur 7

### Exercice 43

Donner le résultat de : **Guess (3, 1),** si la fonction *Guess* a la définition suivante :

```algorithme
Fonction Guess (x, y : entier) : entier
Début
    Si (x=y) Alors
        Retourner x
    Sinon
        Si (x>y) Alors
            Retourner Guess (x-1,y) + Guess(x,y+1)
        Sinon
            Retourner Guess(x+1,y) + Guess(x, y-1)
        Fin Si
    Fin Si
Fin
```

### Exercice 44

Ecrire l'algorithme d'une fonction récursive qui permet de vérifier si un entier N est pair ou impair

### Exercice 45

- Ecrire l'algorithme d'un module récursif qui permet de remplir une matrice **M** de **L\*C** entiers positifs
- Ecrire l'algorithme d'un module récursif qui permet de calculer la somme une matrice **M** de **L\*C** entiers.
- Ecrire l'algorithme d'un module récursif qui permet de d'inverser une matrice **M** de **L\*C** entiers positifs
