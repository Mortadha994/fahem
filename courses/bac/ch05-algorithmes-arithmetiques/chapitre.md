---
niveau: bac
chapitre: 5
titre: Les algorithmes arithmétiques
type: cours
notions: calcul du PGCD, calcul du PPCM, test de primalité, facteurs premiers, factorielle, arrangement et combinaison, règles de divisibilité, conversion entre bases de numération
source: Classroom — Chap 5 : Les algorithmes arithmétiques
---

# Chapitre 5 : Les algorithmes arithmétiques

<!-- TODO vérifier: le PDF (9 pages, « chap 5 - arithmetique.pdf ») s'intitule « Chapitre V : Les algorithmes Arithmétiques » ; numéro 5 conforme au post Classroom. Le PDF contient des algorithmes (versions itératives et récursives) puis, à la fin (page 9), une « Traduction en python » ; il ne contient aucun exercice. Le second document joint au post (« Fichier Drive ») renvoie une erreur 404 et n'a pas pu être lu -->

<!-- TODO vérifier: mots-clés normalisés dans tout le fichier (le PDF écrit « alors/Alors », « faire/Faire », « sinon/Sinon », « Fin si/FinSi/Finsi/Fin Si », « Fin pour/FinPour/Fin Pour », « Fin Tant Que/Fin TantQue/FinTantque/Fin Tant que », « Repeter/Répéter », « Ecrire/Écrire », « pas/Pas ») en Si / Alors / Sinon / Fin Si / Tant que / Faire / Fin Tant que / Pour / Fin Pour / Répéter / Jusqu'à / Ecrire / Pas ; la casse des noms de variables et de fonctions du PDF est conservée -->

<!-- TODO vérifier: les titres des sous-parties (« Méthode de différence », « Solution efficace », « Solution avec Tableau », « Solution 1 »...) sont les en-têtes des tableaux à deux colonnes du PDF ; les colonnes ont été séparées en blocs successifs. Les en-têtes répétés « Solution récursive » et « S.R » (abréviation conservée) ont été complétés par la méthode concernée entre parenthèses (ajout pour distinguer les titres) -->

## Introduction

Dans ce chapitre, on présentera les algorithmes arithmétiques les plus connus : calculs du PGCD et du PPCM, recherche des nombres premiers et décomposition en produits des facteurs premiers, la conversion d'un nombre en base 10 vers le binaire, octal et en hexadécimal et inversement. A la fin, on développera le problème qui convertit un nombre en base b1 en son équivalent en base b2.

### 📌 Rappel : type tableau et T.D.N.T

Un type autre que Entier, Réel, Booléen, Caractère et Chaîne de caractères (un tableau, une matrice, un enregistrement, un fichier) se définit d'abord dans le **T.D.N.T**. Les objets de ce type se déclarent ensuite dans le **T.D.O** (ou le **T.D.O.L** d'un sous-programme) avec le nom du type.

T.D.N.T

| Type |
|---|
| Tab = Tableau de 100 entiers |

T.D.O

| Objet | Nature/type |
|---|---|
| T | Tab |

<!-- TODO vérifier: ajout (notion T.D.N.T absente du PDF de ce chapitre, dont les procédures utilisent le type « tab ») ; forme reprise du cours « Les algorithmes de tris et de recherches » -->

## I. Calcul du PGCD

### Méthode de différence

```algorithme
Fonction PGCD (a, b : entier) : entier
Début
    Tant que a ≠ b Faire
        Si a > b Alors
            a ← a – b
        Sinon
            b ← b - a
        Fin Si
    Fin Tant que
    Retourner a
Fin
```

### 📌 Méthode d'Euclide

```algorithme
Fonction PGCD (a, b : entier) : entier
Début
    Tant que (a mod b ≠ 0) Faire
        r ← a mod b
        a ← b
        b ← r
    Fin Tant que
    Retourner B
Fin
```

<!-- TODO vérifier: dans la méthode d'Euclide du PDF, la valeur retournée est écrite « B » (majuscule) alors que la variable est « b » ; transcrit tel quel -->

### Solution récursive (méthode de différence)

```algorithme
Fonction PGCD (a, b : entier) : entier
Début
    Si a = b Alors
        Retourner a
    Sinon
        Si a > b Alors
            Retourner PGCD (a-b, b)
        Sinon
            Retourner PGCD (a, b-a)
        Fin Si
    Fin Si
Fin
```

### Solution récursive (méthode d'Euclide)

```algorithme
Fonction PGCD (a, b : entier) : entier
Début
    Si a mod b = 0 Alors
        Retourner b
    Sinon
        Retourner PGCD (b, a mod b)
    Fin Si
Fin
```

## II. Calcul du PPCM

### 📌 Solution efficace (PPCM)

```algorithme
Fonction PPCM (a, b : entier) : entier
Début
    max ← a, min ← b
    Si (b > a) Alors
        Max ← b, Min ← a
    Fin Si
    Tant que (max mod min ≠ 0) Faire
        Max ← Max + A + B - Min
    Fin Tant que
    Retourner Max
Fin
```

<!-- TODO vérifier: la casse varie dans l'original (max/Max, min/Min, a/A, b/B) et est conservée -->

### Solution pareille (PPCM)

```algorithme
Fonction PPCM (a, b : entier) : entier
Début
    x ← a
    Tant que (a mod b ≠ 0) Faire
        a ← a+x
    Fin Tant que
    Retourner a
Fin
```

### Solution récursive (PPCM)

**1er Appel :** `P ← PPCM (a, b, a)`

```algorithme
Fonction PPCM (a, b, x : entier) : entier
Début
    Si (a < b) Alors
        Retourner PPCM (b, a, b)
    Sinon
        Si a mod b = 0 Alors
            Retourner a
        Sinon
            Retourner PPCM (a+x, b, x)
        Fin Si
    Fin Si
Fin
```

## III. Tester si un entier premier ou non :

### 📌 Solution efficace (nombre premier)

```algorithme
Fonction Premier (n : entier) : booléen
Début
    i ← 2
    Tant que ((i ≤ n div 2) et (n mod i ≠ 0)) Faire
        i ← i+1
    Fin Tant que
    Retourner (i > n div 2) et (n ≠ 1)
Fin
```

<!-- TODO vérifier: le PDF contient un caractère parasite (accent grave) après « Fin TantQue » dans cet algorithme ; supprimé -->

### Solution efficace (S.R)

**1er Appel :** `B ← Premier (n, 2)`

```algorithme
Fonction Premier (n, i : entier) : booléen
Début
    Si ((i ≤ n div 2) et (n mod i ≠ 0)) Alors
        Retourner Premier(n, i+1)
    Sinon
        Retourner (i > n div 2) et (n ≠ 1)
    Fin Si
Fin
```

### Solution pareille (nombre premier)

```algorithme
Fonction Premier (n : entier) : booléen
Début
    nb ← 0
    Pour i de 1 à N Faire
        Si (N mod i = 0) Alors
            nb ← nb+1
        Fin Si
    Fin Pour
    Retourner (nb = 2)
Fin
```

<!-- TODO vérifier: la fonction « Premier » de la solution pareille a le paramètre « n » mais utilise « N » dans le corps ; transcrit tel quel -->

### Solution pareille (S.R)

**1er Appel :** `B ← Premier (n, 2, 0)`

```algorithme
Fonction Premier (n, i, nb : entier) : booléen
Début
    Si (i > n) Alors
        Retourner (nb = 2)
    Sinon
        Si (N mod i = 0) Alors
            Retourner Premier (n, i+1, nb+1)
        Sinon
            Retourner Premier (n, i+1, nb)
        Fin Si
    Fin Si
Fin
```

## IV. Calcul des facteurs premier :

### Solution avec Tableau

```algorithme
Procédure facteur (@ t : tab ; @ n : entier ; x : entier)
Début
    N ← 0 , i ← 2
    Répéter
        Si (x mod i = 0) Alors
            x ← x div i
            T[n] ← i
            n ← n+1
        Sinon
            i ← i+1
        Fin Si
    Jusqu'à (x = 1)
Fin
```

<!-- TODO vérifier: la procédure du PDF déclare « t » et « n » mais initialise « N ← 0 » et utilise « T[n] » ; casse transcrite telle quelle -->

### Solution avec chaine

```algorithme
Fonction facteur (x : entier) : chaine
Début
    ch ← "" , i ← 2
    Répéter
        Si (x mod i = 0) Alors
            ch ← ch+"*"+convch(i)
            x ← x div i
        Sinon
            i ← i+1
        Fin Si
    Jusqu'à (x = 1)
    Retourner Effacer (ch, 0, 1)
Fin
```

### Solution avec Tableau (S.R)

**1er Appel :**

```algorithme
n ← 0
facteur (t, n, x, 2)
```

```algorithme
Procédure facteur (@ t : tab ; @ n : entier ; x, i : entier)
Début
    Si (x > 1) Alors
        Si (x mod i = 0) Alors
            x ← x div i
            T[n] ← i
            n ← n+1
            facteur (t, n, x, i)
        Sinon
            facteur (t, n, x, i+1)
        Fin Si
    Fin Si
Fin
```

### Solution avec chaine (S.R)

**1er Appel :**

```algorithme
ch ← facteur (x, 2)
Ecrire (X, "=", Effacer (ch, 0, 1))
```

```algorithme
Fonction facteur (x, i : entier) : chaine
Début
    Si (x = 1) Alors
        Retourner ""
    Sinon
        Si (x mod i = 0) Alors
            Retourner "*"+convch(i)+ facteur (x div i, i)
        Sinon
            Retourner facteur (x, i+1)
        Fin Si
    Fin Si
Fin
```

## V. Calcul du Factorielle :

### Solution itérative

```algorithme
Fonction Fact (n : entier) : entier
Début
    F ← 1
    Pour i de 1 à n Faire
        F ← F*i
    Fin Pour
    Retourner f
Fin
```

<!-- TODO vérifier: le PDF écrit « Pour i de 1 a n » (sans accent, normalisé en « à ») et « Retourner f » (minuscule) alors que la variable est « F » ; transcrit tel quel -->

### Solution récursive

```algorithme
Fonction Fact (n : entier) : entier
Début
    Si (n = 0) Alors
        Retourner 1
    Sinon
        Retourner n * Fact(n-1)
    Fin Si
Fin
```

## VI. Calcul d'arrangement et combinaison :

### Arrangement

C'est le nombre de permutations ordonnées possibles de P éléments parmi N.

**Exemple** avec {a, b, c} : A (2,3) = 6

- {a, b}, {b, a}, {a, c}, {c, a}, {b, c}, {c, b}

### Solution 1 (arrangement)

```algorithme
Fonction arrange (p, n : entier) : entier
Début
    a ← 1
    Pour i de n à n-p+1 (Pas=-1) Faire
        a ← a*i
    Fin Pour
    Retourner a
Fin
```

### Solution 2 (arrangement)

```algorithme
Fonction arrange (p, n : entier) : entier
Début
    Retourner fact(n)/ fact(n-p)
Fin
```

Formule : Aₙᵖ = n! / (n−p)!

### Solution 1 récursive (arrangement)

**1er Appel :** `a ← arrange (n, n-p+1)`

```algorithme
Fonction arrange (g, p : entier) : entier
Début
    Si (g < p) Alors
        Retourner 1
    Sinon
        Retourner g * arrange (g-1, p)
    Fin Si
Fin
```

### Combinaison

C'est le nombre de permutations sans ordre possibles de P éléments parmi N.

**Exemple** avec {a, b, c} : C(2,3) = 3

- {a, b}, {a, c}, {b, c}

### Solution itérative (combinaison)

```algorithme
Fonction comb (p, n : entier) : réel
Début
    Retourner fact(n)/(fact(p)* fact(n-p))
Fin
```

Formule : Cₙᵖ = n! / (p! (n−p)!)

### Solution récursive (combinaison)

```algorithme
Fonction Comb_1 (n, p : entier) : réel
Début
    Si (p = n) Alors
        Retourner 1
    Sinon
        Si (p = 1) Alors
            Retourner n
        Sinon
            Retourner (n/p) *Comb_1(n-1, p-1)
        Fin Si
    Fin Si
Fin
```

**2ème méthode :**

```algorithme
Fonction Comb_2 (n, p : entier) : réel
Début
    Si ((p = 0) ou (p = n)) Alors
        Retourner 1
    Sinon
        Retourner Comb_2(n-1, p)+Comb_2(n-1, p-1)
    Fin Si
Fin
```

<!-- TODO vérifier: dans le PDF, la 2ème méthode (Comb_2, séparée par une ligne d'astérisques « 2ème méthode ») figure dans la colonne « Solution récursive » sous Comb_1 ; transcrite à la suite -->

## VII. Quelques règles de divisibilité :

### Définition

Un entier n est divisible par un entier m, si le reste de la division euclidienne de n par m est nul.

Une règle de divisibilité est une séquence d'opérations simples qui permet de reconnaître rapidement si un entier est divisible par un autre sans qu'il soit nécessaire d'effectuer des divisions. Ces règles sont généralement appliquées à des grands nombres.

### Divisible par 3

Un entier est divisible par 3 si la somme des chiffres qui le composent est divisible par 3.

**Algorithme de la fonction Div_3 :**

```algorithme
Fonction Div_3 (Ch : chaine) : Booléen
Début
    Répéter
        S ← 0
        Pour i de 0 à long (ch)-1 Faire
            S ← S + Valeur (ch[i])
        Fin Pour
        Ch ← Convch(s)
    Jusqu'à (long (ch) = 1)
    Retourner S ∈ [3, 6, 9]
Fin
```

<!-- TODO vérifier: dans le PDF, la flèche de l'affectation « Ch ← Convch(s) » et le symbole d'appartenance « ∈ » ont été lus sur la capture d'écran (le texte extrait les perdait) ; l'algorithme réaffecte « Ch » mais sa boucle recalcule « S » à partir de « ch » (casse différente) ; transcrit tel quel -->

### Divisible par 4

Un entier est divisible par 4 si le nombre composé des **deux derniers** chiffres est divisible par 4.

**Exemple :** 5243 n'est pas divisible par 4 car 43 n'est pas divisible par 4 ; 7224 est divisible par 4 car 24 est divisible par 4.

**Algorithme de la fonction Div_4 :**

```algorithme
Fonction Div_4 (ch : Chaine) : Booléen
Début
    ch ← sous_chaine (ch, long (ch)-2, long(ch))
    Retourner Valeur (ch) mod 4 = 0
Fin
```

### Divisibilité par 5

Un entier est divisible par 5 si son chiffre des unités est égal à 0 ou à 5.

**Exemple :** 5243 n'est pas divisible par 5 car 3 ∉ {0,5} ; 72240 est divisible par 5 car 0 ∈ {0,5}

**Algorithme de la fonction Div_5 :**

```algorithme
Fonction Div_5 (ch : Chaine) : Booléen
Début
    Retourner ch[ long(ch)-1 ] ∈ ["0","5"]
Fin
```

### Autre règles de divisibilité

- Un entier est divisible par 2 si son chiffre des unités est divisible par 2.
- Un entier est divisible par 6 s'il est divisible par 2 et 3 au même temps.
- Un entier est divisible par 9 si la somme de ses chiffres est divisible par 9.
- Un entier est divisible par 10 si son chiffre des unités est égal à 0.
- Un entier est divisible par 25 si le nombre composé des deux derniers chiffres est divisible par 25.

## VIII. Conversion entre bases de numération :

### 1. Définition

Un système de numération est une méthode de comptage fondé sur une base de numération qui est un entier supérieur ou égal à deux. Soit N une base de numération, le système sera doté de N chiffres allant de [0 à N-1].

### 2. Exemples de bases de Numération

- Base 2 : Alphabet de la base 2 : {0,1}
- Base 8 : Alphabet de la base 8 : {0, 1, 3, 4, 5, 6, 7}
- Base 10 : Alphabet de la base 10 : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
- Base 16 : Alphabet de la base 16 : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F}

<!-- TODO vérifier: l'alphabet de la base 8 du PDF est {0, 1, 3, 4, 5, 6, 7} : le chiffre 2 est absent (erreur de l'original) ; transcrit tel quel -->

### 3. Conversion d'un nombre décimal en base binaire / Octal : (B10 → B2 / B8)

<!-- TODO vérifier: dans les deux algorithmes ci-dessous, les « (8) » surlignés en jaune dans le PDF indiquent la valeur à utiliser pour la conversion en octal (remplacer 2 par 8) ; transcrits tels quels. La procédure Conv_10_2 est donnée avec un tableau « T » (@ T : tab) -->

**Solution avec Tableau**

```algorithme
Procédure Conv_10_2 (N : entier ; @ T : tab ; @ i : entier)
Début
    i ← 0
    Répéter
        T[i] ← N mod 2 (8)
        N ← N div 2 (8)
        i ← i+1
    Jusqu'à (N = 0)
Fin
```

**Solution avec Chaine**

```algorithme
Fonction Conv_10_2 (N : entier) : chaine
Début
    Ch ← ""
    Répéter
        R ← N mod 2 (8)
        Ch ← Convch (R) + Ch
        N ← N div 2 (8)
    Jusqu'à (N = 0)
    Retourner ch
Fin
```

### 4. Conversion d'un nombre octal/binaire en décimal : (B8 / B2 → B10)

**Solution avec Fn Puissance**

**Algorithme de la Fonction Décimal**

```algorithme
Fonction Décimal (ch : chaine) : entier
Début
    s ← 0
    Pour i de 0 à long (ch)-1 Faire
        NB ← valeur (ch[i])
        S ← S + NB * puissance (8 (2), long(ch)-1-i)
    Fin Pour
    Retourner S
Fin
```

**Algorithme de la Fonction Puissance Xn**

```algorithme
Fonction puissance (x, n : entier) : entier
Début
    p ← 1
    Pour i de 1 à n Faire
        p ← p*x
    Fin Pour
    Retourner p
Fin
```

**Solution sans Fn Puissance**

```algorithme
Fonction Décimal (ch : chaine) : entier
Début
    s ← 0 , P ← 1
    Pour i de long (ch)-1 à 0 (Pas=-1) Faire
        NB ← valeur (ch[i])
        S ← S + NB * P
        P ← P * 8 (2)
    Fin Pour
    Retourner S
Fin
```

<!-- TODO vérifier: les « 8 (2) » du PDF (surlignés) indiquent la base 8, ou 2 pour le binaire ; transcrits tels quels -->

### 5. Conversion d'un nombre décimal en hexadécimal :

**Base10 → Base16**

```algorithme
Fonction Conv_10_16 (N : entier) : chaine
Début
    Ch ← ""
    Répéter
        R ← N mod 16
        Si (R ∈ [0..9]) Alors
            Ch1 ← Convch (R)
        Sinon
            Ch1 ← CHR(R+55)
        Fin Si
        Ch ← Ch1 + Ch
        N ← N div 16
    Jusqu'à (N = 0)
    Retourner ch
Fin
```

**Base16 → Base10**

```algorithme
Fonction Conv_16_10 (ch : chaine) : entier
Début
    s ← 0, P ← 1
    Pour i de long (ch)-1 à 0 (Pas=-1) Faire
        Si (ch[i] ∈ ["0".."9"]) Alors
            NB ← valeur (ch[i])
        Sinon
            NB ← ORD(ch[i])-55
        Fin Si
        S ← S+NB*P
        P ← P*16
    Fin Pour
    Retourner S
Fin
```

### 6. Conversion d'un nombre Hexadécimal en Binaire :

**Base16 → Base2**

```algorithme
Fonction Conv_16_2 (ch : chaine) : chaine
Début
    chb ← ""
    Pour i de 0 à long (ch) - 1 Faire
        Si (ch[i] ∈ ["0".."9"]) Alors
            N ← valeur (ch[i])
        Sinon
            N ← ord(ch[i])-55
        Fin Si
        ch2 ← ""
        Répéter
            ch2 ← Convch(N mod 2) + ch2
            N ← N div 2
        Jusqu'à (n = 0)
        Tant que (long (ch2) mod 4 ≠ 0) Faire
            ch2 ← "0"+ch2
        Fin Tant que
        chb ← chb + ch2
    Fin Pour
    Retourner chb
Fin
```

**Base2 → Base16**

```algorithme
Fonction Conv_2_16 (ch : chaine) : chaine
Début
    Tant que (long (ch) mod 4 ≠ 0) Faire
        ch ← "0"+ch
    Fin Tant que
    ch2 ← ""
    Répéter
        ch1 ← sous_chaine(ch, 0, 4)
        ch ← Effacer (ch, 0, 4)
        s ← 0 , P ← 1
        Pour i de long(ch1)-1 à 0 (Pas=-1) Faire
            S ← S+ valeur (ch[i]) * P
            P ← P * 2
        Fin Pour
        Si (S ∈ [0..9]) Alors
            Ch1 ← Convch (S)
        Sinon
            Ch1 ← CHR(S+55)
        Fin Si
        ch2 ← ch2+ Ch1
    Jusqu'à (long (ch) = 0)
    Retourner ch2
Fin
```

<!-- TODO vérifier: dans Conv_2_16 du PDF, la boucle utilise « valeur (ch[i]) » alors que la chaîne parcourue est « ch1 » (dans Conv_2_8 l'original écrit « Valeur (ch1[i]) ») ; transcrit tel quel -->

### 7. Conversion d'un nombre Octal en Binaire :

**Base8 → Base2**

```algorithme
Fonction Conv_8_2 (ch : chaine) : chaine
Début
    chb ← ""
    Pour i de 0 à long (ch)-1 Faire
        N ← valeur (ch[i])
        ch2 ← ""
        Répéter
            ch2 ← Convch(N mod 2) + ch2
            N ← N div 2
        Jusqu'à (n = 0)
        Tant que (long (ch2) mod 3 ≠ 0) Faire
            ch2 ← "0"+ch2
        Fin Tant que
        chb ← chb+ch2
    Fin Pour
    Retourner chb
Fin
```

**Base2 → Base8**

```algorithme
Fonction Conv_2_8 (ch : chaine) : chaine
Début
    Tant que (long (ch) mod 3 ≠ 0) Faire
        ch ← "0"+ch
    Fin Tant que
    ch2 ← ""
    Répéter
        ch1 ← sous_chaine(ch, 0, 3)
        ch ← Effacer (ch, 0, 3)
        s ← 0 , P ← 1
        Pour i de long(ch1)-1 à 0 (Pas=-1) Faire
            S ← S+ Valeur (ch1[i]) * P
            P ← P * 2
        Fin Pour
        ch2 ← ch2+ Convch (S)
    Jusqu'à (long (ch) = 0)
    Retourner ch2
Fin
```

### 8. Conversion d'un nombre de la base B1 vers la Base B2 (en passant par la Base10) :

**Algorithme CONVERT**

```algorithme
Algorithme CONVERT
Début
    saisieBase(B1)
    saisieBase(B2)
    saisie (NB1, B1)
    NB2 ← B10_BX( BX_B10(NB1, B1) , B2)
    Ecrire ("(", NB1 ,")", B1, "=(", NB2 ,")", B2)
Fin
```

**Algorithme de la procédure saisieBase**

```algorithme
Procédure saisieBase (@ B : entier)
Début
    Répéter
        Ecrire ("Donner une base : ")
        Lire (B)
    Jusqu'à (B ∈ [2, 8, 10, 16])
Fin
```

**Algorithme de la procédure saisie**

```algorithme
Procédure saisie (@ ch : chaine ; B : entier)
Début
    Ens ← "0123456789ABCDEF"
    Alpha ← sous_chaine(Ens, 0, B)
    Répéter
        Ecrire ("Donner un nombre dans la base ", B ,": ")
        Lire (ch)
        i ← 0
        Répéter
            Test ← Pos (ch[i], Alpha) >= 0
            i ← i+1
        Jusqu'à (Test = Faux) ou (i = long (ch))
    Jusqu'à (Test)
Fin
```

**Algorithme de la fonction B10_BX**

```algorithme
Fonction B10_BX (N, X : entier) : chaine
Début
    Ch ← ""
    Répéter
        R ← N mod X
        Si (R ∈ [0..9]) Alors
            Ch1 ← Convch (R)
        Sinon
            Ch1 ← CHR(R+55)
        Fin Si
        Ch ← Ch1 + Ch
        N ← N div X
    Jusqu'à (N = 0)
    Retourner ch
Fin
```

**Algorithme de la fonction BX_B10**

```algorithme
Fonction BX_B10 (ch : chaine ; X : entier) : entier
Début
    s ← 0, P ← 1
    Pour i de long (ch)-1 à 0 (Pas=-1) Faire
        Si (ch[i] ∈ ["0".."9"]) Alors
            NB ← valeur (ch[i])
        Sinon
            NB ← ORD(ch[i])-55
        Fin Si
        S ← S+NB*P
        P ← P* X
    Fin Pour
    Retourner S
Fin
```

### Traduction en python

```python
def saisieBase():
    b=int(input("Donner une base : "))
    while(not (b in [2,8,10,16])):
        b=int(input("Donner une base : "))
    return b

def saisie(B):
    Ens="0123456789ABCDEF"
    Alpha=Ens[:B]
    Test=False
    while not Test:
        ch=input("Donner un nombre dans la base "+ str(B) +": ")
        i=0
        Test = True
        while (Test and (i<len(ch))):
            Test=Alpha.find(ch[i]) >= 0
            i+=1
    return ch

def B10_BX(N,X):
    Ch=""
    while N != 0 :
        R=N % X
        if(0<=R<=9):
            Ch1=str(R)
        else:
            Ch1=chr(R+55)
        Ch=Ch1+Ch
        N=N//X
    return Ch

def BX_B10 (ch,X):
    S=0
    P=1
    for i in range(len(ch)-1,-1,-1):
        if ("0"<=ch[i]<="9"):
            NB=int(ch[i])
        else:
            NB=ord(ch[i])-55
        S+=NB*P
        P*=X
    return S

#PP
B1=saisieBase()
B2=saisieBase()
NB1=saisie(B1)
NB2=B10_BX(BX_B10(NB1,B1),B2)
print("(", NB1 ,")",B1,"=(", NB2 ,")", B2)
```

<!-- TODO vérifier: le code Python est présenté sur deux colonnes dans le PDF (la colonne de gauche s'arrête à « S=0 / P=1 » dans BX_B10, la colonne de droite reprend à « for i in range... ») ; les deux colonnes ont été rassemblées dans l'ordre de lecture. L'indentation est relue sur la capture d'écran. Le Python n'est pas identique à l'algorithme (par exemple la fonction « saisie » du Python) ; transcrit tel quel -->
