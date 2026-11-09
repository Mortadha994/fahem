---
niveau: bac
chapitre: 3
titre: Les algorithmes de tris et de recherches
type: cours
notions: tri par sélection, tri à bulles, tri par insertion, tri Shell, méthode itérative, méthode récursive, recherche séquentielle, recherche dichotomique
source: Classroom — Chap 3 - Les tris et les recherches (chap 3 - les tris et les recherches.pdf)
---

# Chapitre 3 : Les algorithmes de Tris et de Recherches

<!-- TODO vérifier: le PDF (6 pages) ne contient aucun code Python, seulement des algorithmes ; aucun bloc python n'a été ajouté -->
<!-- TODO vérifier: normalisation des mots-clés : « alors », « sinon », « faire », « Fin pour » du PDF sont écrits « Alors », « Sinon », « Faire », « Fin Pour » ; « Finsi » est écrit « Fin Si » ; « a » dans « Pour i de 1 a N-1 » est écrit « à » -->
<!-- TODO vérifier: les lignes « 1er Appel : ... » du PDF sont transcrites en texte avec le code en ligne (hors bloc algorithme) -->

## I. Le tri d'un tableau

### Introduction

- Le tri est une opération qui consiste à répartir ou organiser une collection d'objets selon un ordre déterminé. Dans le domaine de l'informatique, il existe plusieurs méthodes de tri (algorithmes).
- Dans ce chapitre nous allons découvrir trois méthodes de tri :
  - Tri par sélection
  - Tri à bulles
  - Tri par insertion
  - Tri Shell

<!-- TODO vérifier: le PDF annonce « trois méthodes de tri » mais en liste quatre (sélection, bulles, insertion, Shell) -->

### 📌 1. Tri par sélection

**Principe :**

Cette méthode de tri consiste à :

1. Se pointer à la 1ère case du tableau T et de parcourir la totalité du tableau pour repérer l'indice de la première position du minimum,
2. Comparer ce minimum avec T [0]. S'ils sont différents on les permute,
3. Le sous tableau de T allant de 1 à n-1 est à priori non trié, on applique l'étape 1 et 2 et ainsi de suite jusqu'à l'avant dernier élément (n-2).

**Remarque :**

- On est arrivé à l'élément numéro n-2, alors arrêt du traitement.
- Nous n'avons pas besoin de traiter le dernier élément, puisque si les neuf premiers éléments sont triés alors automatiquement le dernier sera le plus grand et par conséquent il se trouve à la bonne position.

**Méthode itérative :**

Algorithme de la procédure Tri :

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Pour i de 0 à N-2 Faire
        Pm ← i
        Pour j de i+1 à N-1 Faire
            Si (T [j] < T [Pm]) Alors
                Pm ← j
            Fin Si
        Fin Pour
        Si (i ≠ Pm) Alors
            Aux ← T[i]
            T[i] ← T[Pm]
            T[Pm] ← Aux
        Fin Si
    Fin Pour
Fin
```

T.D.N.T

| Type |
|---|
| TAB = Tableau de 100 entiers |

T.D.O.L

| Objet | Nature/type |
|---|---|
| i, j, Pm, Aux | Entier |

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, Pm, j, N : Entier)
Début
    Si (i ≤ N-2) Alors
        Si (j ≤ N-1) Alors
            Si (T [j] < T [Pm]) Alors
                Pm ← j
            Fin Si
            Tri (T, i, Pm, j+1, N)
        Sinon
            Si (i ≠ Pm) Alors
                Aux ← T[i]
                T[i] ← T[Pm]
                T[Pm] ← Aux
            Fin Si
            Tri (T, i+1, i+1, i+2, N-1)
        Fin Si
    Fin Si
Fin
```

**1er Appel :** `Tri (T, 0, 0, 1, N)`

### 📌 2. Tri à bulles

**Principe :**

Cette méthode de tri consiste à :

1. Comparer les éléments du tableau T deux à deux,
2. Permuter les contenus lorsque l'ordre n'est pas respecté,
3. Refaire les actions 1 et 2 et ainsi de suite jusqu'à avoir finalement un tableau trié.

Puisqu'on a atteint la fin du tableau et le contenu de la variable test est Faux, alors on doit recommencer un nouveau passage et ainsi de suite jusqu'à ce qu'on fasse un passage complet du tableau sans modifier le contenu de test (Vrai).

<!-- TODO vérifier: le texte parle de la « variable test », mais l'algorithme utilise la variable « permute » -->

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Répéter
        permute ← Faux
        Pour i de 0 à N-2 Faire
            Si (T[i] > T[i+1]) Alors
                Aux ← T[i]
                T[i] ← T[i+1]
                T[i+1] ← Aux
                permute ← Vrai
            Fin Si
        Fin Pour
    Jusqu'à (permute = Faux)
Fin
```

<!-- TODO vérifier: le PDF écrit « permute = faux » (transcrit « Faux ») -->

T.D.O.L

| Objet | Nature/type |
|---|---|
| I, Aux | Entier |
| permute | Booléen |

<!-- TODO vérifier: la T.D.O.L du PDF écrit « I » (majuscule) alors que l'algorithme utilise « i » ; le texte du PDF contient aussi une seconde T.D.O.L « Aux : Entier » non visible à l'écran, non transcrite -->

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, N : Entier)
Début
    Si (N ≠ 1) Alors
        Si (i ≤ N-2) Alors
            Si (T[i] > T [i+1]) Alors
                Aux ← T[i]
                T[i] ← T [i+1]
                T [i+1] ← Aux
            Fin Si
            Tri (T, i+1, N)
        Sinon
            Tri (T, 0, N-1)
        Fin Si
    Fin Si
Fin
```

**1er Appel :** `Tri (T, 0, N)`

### 3. Tri par insertion

**Principe :**

Cette méthode de tri consiste à :

1. Considérer que les i-1 premiers éléments du tableau T sont triés et insérer l'élément N°i dans sa position parmi les i-1 déjà triés,
2. Répéter cette action jusqu'à le dernier élément du tableau T.

**N.B :** L'insertion se traduit par la sauvegarde de l'élément N° i dans une variable intermédiaire (Tmp), puis le décalage d'un cran à droite des éléments i-1, i-2, ... jusqu'à avoir un élément inférieur à Int et finalement affecter le contenu de Int dans l'élément libre.

<!-- TODO vérifier: le texte parle de « Int » alors que la variable intermédiaire s'appelle « Tmp » (transcrit tel quel) -->

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Pour i de 1 à N-1 Faire
        Si (T[i-1] > T[i]) Alors
            Tmp ← T[i]
            j ← i
            Tant que ((j > 0) ET (T[j-1] > Tmp)) Faire
                T[j] ← T[j-1]
                j ← j – 1
            Fin Tant que
            T[j] ← Tmp
        Fin Si
    Fin Pour
Fin
```

T.D.O.L

| Objet | Nature/type |
|---|---|
| i, Tmp, j | Entier |

<!-- TODO vérifier: le texte du PDF contient une seconde T.D.O.L « Aux : Entier » non visible à l'écran, non transcrite -->

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, Tmp, j, N : Entier)
Début
    Si (i ≤ N-1) Alors
        Si ((j ≥ 1) ET (T [j-1] > Tmp)) Alors
            T [j] ← T [j-1]
            Tri (T, i, Tmp, j-1, N)
        Sinon
            T [j] ← Tmp
            Tri (T, i+1, T [i+1], i+1, N)
        Fin Si
    Fin Si
Fin
```

**1er Appel :** `Tri (T, 1, T [1], 1, N)`

### 4. Tri Shell

**Principe :**

C'est une variante du tri par insertion.

Shell propose une suite définie par : U0=0 et Un+1= 3 * Un +1 pour déterminer la valeur du pas.

Trie chaque liste d'éléments séparés par p positions chacun avec un tri par insertion.

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : Tab ; N : Entier)
Début
    p ← 0
    Tant que (p < N-1) Faire
        p ← 3*p + 1
    Fin Tant que
    Tant que (p ≠ 1) Faire
        p ← p Div 3
        Pour i de p à N-1 Faire
            Tmp ← T[i]
            j ← i
            Tant que ((j ≥ p) ET (T [j-p] > Tmp)) Faire
                T[j] ← T [j-p]
                j ← j-p
            Fin Tant que
            T[j] ← Tmp
        Fin Pour
    Fin Tant que
Fin
```

T.D.O.L

| Objet | Nature/type |
|---|---|
| i, Tmp, j, p | Entier |

<!-- TODO vérifier: dans le PDF, la T.D.O.L du tri Shell est placée à côté de l'algorithme itératif, sur la page 4 -->

**Méthode récursive :**

```algorithme
Fonction Pas (P, N : Entier) : Entier
Début
    Si (P < N-1) Alors
        Retourner Pas (3*P+1, N)
    Sinon
        Retourner P
    Fin Si
Fin
```

```algorithme
Procédure Tri (@ T : Tab ; P, i, Tmp, j, N : Entier)
Début
    Si (P ≠ 0) Alors
        Si (i ≤ N-1) Alors
            Si ((j ≥ P) ET (T [j-P] > Tmp)) Alors
                T [j] ← T [j-P]
                Tri (T, P, i, Tmp, j-P, N)
            Sinon
                T [j] ← Tmp
                Tri (T, P, i+1, T [i+1], i+1, N)
            Fin Si
        Sinon
            p ← p Div 3
            Tri (T, P, P, T [P], P, N)
        Fin Si
    Fin Si
Fin
```

<!-- TODO vérifier: dans le PDF, la procédure récursive du tri Shell utilise « P » (paramètre) et « p » (dans « p ← p Div 3 ») ; transcrit tel quel -->

**1er Appel :** `P ← Pas (0, N) div 3` puis `Tri (T, P, P, T [P], P, N)`

## II. La recherche d'un élément dans un tableau

### Introduction

- La recherche d'un élément dans un tableau ou dans une liste de valeur est un traitement très utile en informatique, parmi les méthodes de recherches, on cite :
  - La recherche séquentielle,
  - La recherche dichotomique.

### 1. La recherche séquentielle

**Principe :**

Cette méthode de recherche consiste à parcourir les éléments du tableau un par un jusqu'à trouver la valeur cherchée ou arriver à la fin du tableau.

**Exemple :**

Soit un tableau T contenant les dix éléments suivants :

| T | 12 | 10 | 0 | -5 | 8 | 12 | -2 | 2 | 40 | -1 |
|---|---|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

Pour X = -2 le programme affichera "-2 existe dans le tableau"

Pour X = 5 le programme affichera "5 n'existe pas dans le tableau"

**Méthode itérative :**

```algorithme
Fonction recherche (T : TAB ; N, X : Entier) : Booléen
Début
    i ← 0
    Répéter
        Trouve ← T[i] = X
        i ← i+1
    Jusqu'à ((Trouve = Vrai) OU (i = N))
    Retourner Trouve
Fin
```

<!-- TODO vérifier: le PDF n'a pas de T.D.O.L pour la recherche séquentielle ; le PDF écrit « Trouve » (et non « Trouvé ») -->

**Méthode récursive :**

```algorithme
Fonction Recherche (T : TAB ; N, X : Entier) : Booléen
Début
    Si (N = -1) Alors
        Retourner Faux
    Sinon
        Si (T [N] = X) Alors
            Retourner Vrai
        Sinon
            Recherche (T, N-1, X)
        Fin Si
    Fin Si
Fin
```

<!-- TODO vérifier: dans le PDF, l'appel récursif « Recherche (T, N-1, X) » n'est pas précédé de « Retourner » (transcrit tel quel) -->

**1er Appel :** `B ← Recherche (T, N-1, X)`

### 📌 2. La recherche dichotomique

**Principe :**

Cette méthode de recherche consiste à :

1. Fixer le début (Deb) et la fin (Fin) du tableau,
2. Fixer le milieu du tableau (Mil = (Fin + Deb) Div 2),
3. Comparer X et T[Mil], Si (X > T[Mil]) alors rechercher X dans le sous tableau [Mil + 1 ... Fin] sinon si (X < T[Mil]) alors dans le tableau [Deb ... Mil - 1],
4. Répéter les étapes 1, 2 et 3 jusqu'à (X = T[Mil]) ou (Deb > Fin)

**Méthode itérative :**

```algorithme
Fonction recherche (T : TAB ; N, X : Entier) : Booléen
Début
    Trouve ← Faux
    d ← 0
    f ← N - 1
    Répéter
        Mil ← (d + f) Div 2
        Si (T[Mil] > X) Alors
            f ← Mil - 1
        Sinon
            Si (T[Mil] < X) Alors
                d ← Mil + 1
            Sinon
                Trouve ← Vrai
            Fin Si
        Fin Si
    Jusqu'à ((Trouve = Vrai) OU (Deb > Fin))
    Retourner Trouve
Fin
```

<!-- TODO vérifier: dans le PDF, l'algorithme initialise « d » et « f » mais la condition d'arrêt utilise « Deb » et « Fin » (transcrit tel quel) ; le PDF écrit « Finsi » en un mot pour la seconde fermeture (normalisé en « Fin Si ») -->

T.D.O.L

| Objet | Nature/type |
|---|---|
| d, f, Mil | Entier |
| Trouve | Booléen |

**Méthode récursive :**

```algorithme
Fonction Recherche (T : TAB ; D, F, X : Entier) : Booléen
Début
    Si (D > F) Alors
        Retourner Faux
    Sinon
        M ← (D + F) Div 2
        Si (T [M] > X) Alors
            Recherche (T, D, M-1, X)
        Sinon
            Si (T [M] < X) Alors
                Recherche (T, M+1, F, X)
            Sinon
                Retourner Vrai
            Fin Si
        Fin Si
    Fin Si
Fin
```

<!-- TODO vérifier: dans le PDF, les appels récursifs « Recherche (T, D, M-1, X) » et « Recherche (T, M+1, F, X) » ne sont pas précédés de « Retourner » (transcrit tel quel) -->

**1er Appel :** `B ← Recherche (T, 0, N-1, X)`

## III. Résumé : les tris et les recherches (méthodes itératives et récursives)

<!-- TODO vérifier: résumé « Tris et recherches (itérative + récursive).pdf » du sujet « Les documents importants », rattaché à ce chapitre ; niveau bac déduit du contenu -->


<!-- TODO vérifier: PDF de 3 pages (titre « Les tris et les recherches — Méthodes récursives »), uniquement des algorithmes (aucun code Python, aucun texte explicatif) ; présenté dans le PDF en tableau « Nom | Itérative | Récursive », chaque méthode sur une ligne ; ici chaque méthode donne une section avec sa version itérative puis sa version récursive. Niveau « bac » déduit du contenu (tri par insertion, tri Shell, versions récursives) : à confirmer. Mots-clés unifiés (Alors, Sinon, Fin Si, Fin Pour, ET, OU, Faux, Vrai) ; les flèches « ⃪ » du PDF sont notées ← -->


### Résumé — 1. Tri à bulles

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Répéter
        permute ← Faux
        Pour i de 0 à N-2 Faire
            Si (T[i] > T [i+1]) Alors
                Aux ← T [i]
                T [i] ← T [i+1]
                T [i+1] ← Aux
                permute ← Vrai
            Fin Si
        Fin Pour
        N ← N-1
    Jusqu'à ((permute = Faux) OU (N=1))
Fin
```

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, N : Entier)
Début
    Si (N ≠ 1) Alors
        Si (i ≤ N-2) Alors
            Si (T[i] > T [i+1]) Alors
                Aux ← T[i]
                T[i] ← T [i+1]
                T [i+1] ← Aux
            Fin Si
            Tri (T, i+1, N)
        Sinon
            Tri (T, 0, N-1)
        Fin Si
    Fin Si
Fin
```

1er Appel : `Tri (T, 0, N)`

### Résumé — 2. Tri par sélection

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Pour i de 0 à N-2 Faire
        Pm ← i
        Pour j de i+1 à N-1 Faire
            Si (T [j] < T [Pm]) Alors
                Pm ← j
            Fin Si
        Fin Pour
        Si (i ≠ Pm) Alors
            Aux ← T[i]
            T[i] ← T[Pm]
            T[Pm] ← Aux
        Fin Si
    Fin Pour
Fin
```

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, Pm, j, N : Entier)
Début
    Si (i ≤ N-2) Alors
        Si (j ≤ N-1) Alors
            Si (T [j] < T [Pm]) Alors
                Pm ← j
            Fin Si
            Tri (T, i, Pm, j+1, N)
        Sinon
            Si (i ≠ Pm) Alors
                Aux ← T[i]
                T[i] ← T[Pm]
                T[Pm] ← Aux
            Fin Si
            Tri (T, i+1, i+1, i+2, N-1)
        Fin Si
    Fin Si
Fin
```

1er Appel : `Tri (T, 0, 0, 1, N)`

### Résumé — 3. Tri par insertion

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : TAB ; N : Entier)
Début
    Pour i de 1 à N-1 Faire
        Tmp ← T[i]
        j ← i
        Tant que ((j ≥ 1) ET (T [j-1] > Tmp)) Faire
            T [j] ← T [j-1]
            j ← j – 1
        Fin Tant que
        T [j] ← Tmp
    Fin Pour
Fin
```

**Méthode récursive :**

```algorithme
Procédure Tri (@ T : TAB ; i, Tmp, j, N : Entier)
Début
    Si (i ≤ N-1) Alors
        Si ((j ≥ 1) ET (T [j-1] > Tmp)) Alors
            T [j] ← T [j-1]
            Tri (T, i, Tmp, j-1, N)
        Sinon
            T [j] ← Tmp
            Tri (T, i+1, T [i+1], i+1, N)
        Fin Si
    Fin Si
Fin
```

1er Appel : `Tri (T, 1, T [1], 1, N)`

### Résumé — 4. Tri Shell

**Méthode itérative :**

```algorithme
Procédure Tri (@ T : Tab ; N : entier)
Début
    p ← 0
    Tant que (p < N-1) Faire
        p ← 3*p + 1
    Fin Tant que
    Tant que (p ≠ 1) Faire
        p ← p Div 3
        Pour i de p à N-1 Faire
            Tmp ← T[i]
            j ← i
            Tant que ((j ≥ p) ET (T [j-p] > Tmp)) Faire
                T[j] ← T [j-p]
                j ← j-p
            Fin Tant que
            T[j] ← Tmp
        Fin Pour
    Fin Tant que
Fin
```

**Méthode récursive :**

```algorithme
Fonction Pas (P, N : Entier) : Entier
Début
    Si (P < N-1) Alors
        Retourner Pas (3*P+1, N)
    Sinon
        Retourner P
    Fin Si
Fin
```

```algorithme
Procédure Tri (@ T : Tab ; P, i, Tmp, j, N : entier)
Début
    Si (P ≠ 0) Alors
        Si (i ≤ N-1) Alors
            Si ((j ≥ P) ET (T [j-P] > Tmp)) Alors
                T [j] ← T [j-P]
                Tri (T, P, i, Tmp, j-P, N)
            Sinon
                T [j] ← Tmp
                Tri (T, P, i+1, T [i+1], i+1, N)
            Fin Si
        Sinon
            p ← p Div 3
            Tri (T, P, P, T [P], P, N)
        Fin Si
    Fin Si
Fin
```

<!-- TODO vérifier: dans la version récursive du tri Shell, « p ← p Div 3 » est écrit avec un « p » minuscule alors que le paramètre est « P » (transcrit tel quel) -->

1er Appel :

```algorithme
P ← Pas (0, N) Div 3
Tri (T, P, P, T [P], P, N)
```


### Résumé — 5. Recherche séquentielle

**Méthode itérative :**

```algorithme
Fonction Recherche (T : TAB ; N, X : Entier) : Booléen
Début
    i ← 0
    Répéter
        B ← T[i] = X
        i ← i+1
    Jusqu'à ((B = Vrai) OU (i = N))
    Retourner B
Fin
```

**Méthode récursive :**

```algorithme
Fonction Recherche (T : TAB ; N, X : Entier) : Booléen
Début
    Si (N = -1) Alors
        Retourner Faux
    Sinon
        Si (T [N] = X) Alors
            Retourner Vrai
        Sinon
            Recherche (T, N-1, X)
        Fin Si
    Fin Si
Fin
```

1er Appel : `B ← Recherche (T, N-1, X)`

<!-- TODO vérifier: dans la version récursive, l'appel « Recherche(T, N-1, X) » n'est pas précédé de « Retourner » dans le PDF (transcrit tel quel) -->

### Résumé — 6. Recherche dichotomique

**Méthode itérative :**

```algorithme
Fonction Recherche (T : TAB ; N, X : Entier) : Booléen
Début
    B ← Faux
    D ← 0
    F ← N - 1
    Répéter
        M ← (D + F) Div 2
        Si (T [M] > X) Alors
            F ← M - 1
        Sinon
            Si (T [M] < X) Alors
                D ← M + 1
            Sinon
                B ← Vrai
            Fin Si
        Fin Si
    Jusqu'à ((B = Vrai) OU (D > F))
    Retourner B
Fin
```

**Méthode récursive :**

```algorithme
Fonction Recherche (T : TAB ; D, F, X : Entier) : Booléen
Début
    Si (D > F) Alors
        Retourner Faux
    Sinon
        M ← (D + F) Div 2
        Si (T [M] > X) Alors
            Recherche (T, D, M-1, X)
        Sinon
            Si (T [M] < X) Alors
                Recherche (T, M+1, F, X)
            Sinon
                Retourner Vrai
            Fin Si
        Fin Si
    Fin Si
Fin
```

1er Appel : `B ← Recherche (T, 0, N-1, X)`

<!-- TODO vérifier: comme pour la recherche séquentielle, les appels récursifs « Recherche(T, D, M-1, X) » et « Recherche(T, M+1, F, X) » ne sont pas précédés de « Retourner » dans le PDF (transcrit tel quel) -->
