---
niveau: 3eme
chapitre: 3
titre: Les algorithmes arithmétiques
type: cours
notions: calcul du PGCD, méthode de différence, méthode d'Euclide, calcul du PPCM, test de primalité, facteurs premiers, factorielle
source: Classroom — Chapitre 4 - Les algorithmes arithmétiques
---

# Chapitre 3 : Les algorithmes arithmétiques

<!-- TODO vérifier: le PDF (2 pages) s'intitule « Chapitre V : Les algorithmes Arithmétiques » (post Classroom : « Chapitre 4 ») ; numéro 3 retenu selon l'ordre du programme. Le PDF ne contient aucun code Python, seulement des algorithmes ; aucun bloc python n'a été ajouté -->

<!-- TODO vérifier: mots-clés normalisés dans tout le fichier (le PDF écrit « Fin Tant Que », « FinTantQue », « FinSi », « Finsi », « Fin pour », « si/alors/sinon », « faire » sous plusieurs graphies) en Si / Alors / Sinon / Fin Si / Tant que / Faire / Fin Tant que / Pour / Fin Pour ; la casse des noms de variables du PDF est conservée -->

## I. Introduction

Dans ce chapitre, on présentera les algorithmes arithmétiques les plus connus : calculs du PGCD et du PPCM, recherche des nombres premiers et décomposition en produits des facteurs premiers, la conversion d'un nombre en base 10 vers le binaire et en hexadécimal. A la fin, on développera le problème qui convertit un nombre en base b1 en son équivalent en base b2.

## II. Calcul du PGCD

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
        R ← a mod b
        A ← b
        B ← R
    Fin Tant que
    Retourner B
Fin
```

<!-- TODO vérifier: dans la méthode d'Euclide du PDF, la condition utilise « a » et « b » (minuscules) alors que les affectations utilisent « A » et « B » (majuscules) ; transcrit tel quel -->

## III. Calcul du PPCM

### 📌 Solution efficace (PPCM)

```algorithme
Fonction PPCM (a, b : entier) : entier
Début
    max ← a
    min ← b
    Si (b > a) Alors
        Max ← b
        Min ← a
    Fin Si
    Tant que (max mod min ≠ 0) Faire
        Max ← Max + A + B - Min
    Fin Tant que
    Retourner Max
Fin
```

<!-- TODO vérifier: le PDF écrit « Fontion PPCM » (faute de frappe, transcrite « Fonction ») ; la casse varie (max/Max, min/Min, a/A, b/B) dans l'original et est conservée -->

### Solution pareille

```algorithme
Fonction PPCM (a, b : entier) : entier
Début
    x ← a
    Tant que (a mod b ≠ 0) Faire
        a ← a + x
    Fin Tant que
    Retourner a
Fin
```

## IV. Tester si un entier premier ou non

### 📌 Solution efficace (nombre premier)

```algorithme
Fonction Premier (n : entier) : booléen
Début
    i ← 2
    Tant que ((i ≤ n div 2) et (n mod i ≠ 0)) Faire
        i ← i + 1
    Fin Tant que
    Retourner (i > n div 2) et (n ≠ 1)
Fin
```

### Solution pareille

```algorithme
Fonction Premier (n : entier) : booléen
Début
    nb ← 0
    Pour i de 1 à N Faire
        Si (N mod i = 0) Alors
            nb ← nb + 1
        Fin Si
    Fin Pour
    Retourner (nb = 2)
Fin
```

<!-- TODO vérifier: la fonction « Premier » de la solution pareille a le paramètre « n » mais utilise « N » dans le corps ; transcrit tel quel -->

## V. Calcul des facteurs premiers

### Solution avec tableau

```algorithme
Procédure facteur (@ t : tab ; @ n : entier ; x : entier)
Début
    N ← 0
    i ← 2
    Répéter
        Si (x mod i = 0) Alors
            x ← x div i
            T[n] ← i
            n ← n + 1
        Sinon
            i ← i + 1
        Fin Si
    Jusqu'à (x = 1)
Fin
```

<!-- TODO vérifier: la procédure du PDF déclare « t » et « n » mais initialise « N ← 0 » et utilise « T[n] » ; casse transcrite telle quelle -->

### Solution avec chaîne

```algorithme
Fonction facteur (x : entier) : chaine
Début
    ch ← ""
    i ← 2
    Répéter
        Si (x mod i = 0) Alors
            ch ← ch + "*" + convch(i)
            x ← x div i
        Sinon
            i ← i + 1
        Fin Si
    Jusqu'à (x = 1)
    Retourner ch
Fin
```

## VI. Calcul du Factorielle

```algorithme
Fonction Fact (n : entier) : entier
Début
    F ← 1
    Pour i de 1 à n Faire
        F ← F * i
    Fin Pour
    Retourner f
Fin
```

<!-- TODO vérifier: le PDF écrit « Pour i de 1 a n » (sans accent, normalisé en « à ») et « Retourner f » (minuscule) alors que la variable est « F » ; transcrit tel quel -->
