---
niveau: 3eme
chapitre: 2
titre: Série N° 4 : Les suites
type: serie
notions: suite de Fibonacci, ordre de récurrence, suite de Syracuse, fonction récursive, suite de Héron, formule de Viète, calcul de racine carrée, suite de Robinson
source: Classroom — Série N°4 - Les suites
---

# Série N° 4 : Les suites

<!-- TODO vérifier: le PDF s'intitule « Les algorithmes récurrents — Série N°1 : les suites » (fichier « Série Suite N°1.pdf ») ; il est publié dans Classroom sous « Série N°4 - Les suites » -->

## Série d'exercices

### Exercice N°1 : (la suite de Fibonacci)

La suite de Fibonacci est définie par :

- Fn = 1 si n=0 ou n=1
- Fn = Fn-1 + Fn-2 pour n ≥2

**Question :**

1) Déterminer l'ordre de récurrence.
2) Proposer une solution au problème de Fibonacci. (Calculer Fn)

### Exercice N°2

La Suite de **SYRACUSE** est définie par :

- U0=a, a un entier positif non nul donné.
- Un= Un-1/2 si Un-1 est pair (/ : division entière)
- Un=3*Un-1 + 1 si Un-1est impair

**a)** Quel est l'ordre de récurrence de la suite U.

**b)** Écrire un algorithme d'une fonction itérative permettant de calculer le nième terme de la suite U.

**c)** Écrire un algorithme d'une fonction récursive permettant de calculer Un.

### Exercice N°3

```algorithme
Fonction Inconnue (N : entier) : entier
Début
    X ← 0
    Pour i de 1 à n Faire
        X ← 2*i + X
    Fin Pour
    Retourner X
Fin
```

1. Cette fonction est-elle récurrente ? quel est l'ordre de récurrence.
2. Exécuter la fonction Inconnue pour N=0, N=4 et N=9.
3. Quel est le rôle de cette fonction ?

### Exercice N°4

Soit la suite (U) définie par :

- U0=2
- U1=3
- Un=Un-1+2*Un-2 pour tout n >=2

En supposant que cette suite est croissante, écrire un programme permettant de lire un entier x (x>2), de vérifier et d'afficher s'il est un terme de la suite U ou non. Dans l'affirmative afficher son rang

### Exercice N°5 : (calcul de la suite de Heron)

- U0=**a**
- Un+1 = (Un/2)+(**B**/2*Un)

Où **a** et **B** sont deux réels positifs..

Calculer Un ??

### Exercice N°6 : (formule de viéte)

Soient deux suites récurrentes U et V :

- U0 = 2
- Un+1 = Un/Vn+1
- V0 = 0
- Vn+1 = √((1 + Vn)/2)

Écrire un programme permettant de tester la convergence de la suite U près à 10⁻³.

<!-- TODO vérifier: les formules sont sur deux colonnes dans le PDF (U à gauche, V à droite) ; « Un+1 = Un/Vn+1 » transcrit tel quel -->

### Exercice N°7

Écrire un programme qui permet de calculer puis d'afficher la racine carrée d'un réel positif X en utilisant la suite suivante :

- U0 = (1+X)/2
- Un+1 = (Un+X/Un)/2

Il s'agit de calculer les premiers termes de cette jusqu'à ce que la différence entre deux termes successifs devient inférieur ou égale à 10⁻⁴.

Le dernier terme calculé est une valeur approché de √X près

### Exercice N°8

Soit la suite (Pi), i impaire définie par :

- P1 = 2
- Pi = Pi – 2 * (i-1)/i * (i+1)/i   i impair et i > 1

Écrire un programme qui permet de calculer et d'afficher les termes de la suite P jusqu'à ce que la différence entre deux termes consécutifs devienne inférieure ou égale à 10⁻⁴.

<!-- TODO vérifier: la formule « Pi = Pi – 2 * (i-1)/i * (i+1)/i » est transcrite telle quelle d'après le PDF (le terme de droite semble devoir être P(i-2), à confirmer) -->

### Exercice N°9

On considère la suite U définie par : U1=1, U2=2, Un+1=Un+p*Un-1 ∀ n≥2 avec p un entier positif donnée.

**a)** Quel est l'ordre de récurrence de la suite U ?

**b)** Écrire un algorithme d'une fonction qui vérifie si un entier k donnée est un terme de la suite U ou non. Si k un terme de la suite, la fonction retourne le rang de k si non retourne 0.

### Exercice N°10

Soit la suite de ROBINSON Définie par:

Ui = a ( a est un chiffre) alors Ui+1 = apparition de chaque chiffre dans Ui

Chaque terme de la suite se construit ensuite en comptant le nombre d'apparitions des différents chiffres de 9 à 0 (dans cet ordre) dans le terme précédent. Si un chiffre n'apparaît pas, il n'est pas pris en compte.

**Exemple :**

Si U0=0 alors

- U1 = 10 « 0 se répète 1 fois dans U0 »
- U2 = 1110 « 1 se répète 1 fois dans U1 , 0 se répète 1 fois dans U1 »
- U3 = 3110 « 1 se répète 3 fois et 0 se répète 1 fois dans U2 »
- U4= 132110
- U5 = 13123110
- U6 = 23124110
- U7 = 1413223110
- U8 = 1423224110
- U9 = 2413323110...

**Écrire un programme qui permet de calculer et d'afficher Un, en enregistrant les Ui dans un fichier texte (un terme par ligne)**
