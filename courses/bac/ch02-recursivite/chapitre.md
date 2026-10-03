---
niveau: bac
chapitre: 2
titre: La récursivité
type: cours
notions: notion de récursivité, point d'arrêt et appel récursif, module récursif (procédure et fonction), récursivité directe croisée et indirecte, mécanisme de fonctionnement et pile d'exécution
source: Classroom — Chap 2 : La récursivité
---

# Chapitre II : La récursivité

<!-- TODO vérifier: mots-clés harmonisés en Si, Alors, Sinon, Fin Si (l'original écrit alors / FinSi), Ecrire, Retourner, Procédure, Fonction, Début, Fin, Pour, Faire, Fin Pour ; les mots-clés `Procédure` et `Fonction` n'ont pas de fin explicite autre que `Fin` -->

<!-- Les sous-titres « 1. Schéma d'un module récursif » (épinglé), « 1. Afficher « TuTo » 5 fois » / « 2. Calculer la somme… » (titres des colonnes du tableau) et « 1. Version itérative » / « 2. Version récursive » ne sont pas des titres numérotés du PDF : ils ont été ajoutés ou numérotés pour structurer le texte (et respecter la règle des sections épinglées) -->

## I. Notion de récursivité

![Cinq poupées russes (matriochkas) de tailles décroissantes, rangées de la plus grande à la plus petite](figures/poupees-russes.png)
<!-- TODO figure: à recréer -->

La récursivité est une méthode algorithmique qui consiste à appeler un sous-programme dans son propre corps.

Un sous-programme **récursif** est un module qui fait appelle à lui-même (jusqu'à ce qu'une **condition d'arrêt** soit vérifiée), à chaque appel, il y aura une mémorisation d'une nouvelle valeur d'un même paramètre formel.

Un programme récursif doit avoir :

- Un (ou plusieurs) point d'arrêt (condition(s) de sortie).
- Un (ou plusieurs) appel récursif.

### 📌 1. Schéma d'un module récursif

**Exemple d'appel :**

Procédure :

```algorithme
Procédure NomP (paramètres)
Début
    Si (condition de travail) Alors
        #Traitements
        NomP (valeurs)
        #Traitements
    Fin Si
Fin
Appel : NomP(param)
```

```python
def NomP (paramètres) :
    if (condition de travail) :
        #Traitements
        NomP (Valeurs)
        #Traitements
#PP
NomP(parm)
```

Fonction :

```algorithme
Fonction NomFN (paramètres) : Type_Retour
Début
    Si (condition d'arrêt) Alors
        Retourner Valeur
    Sinon
        #Traitements
        Retourner NomFN (valeurs)
    Fin Si
Fin
Appel : X ← NomFN(param)
```

```python
def NomFn(paramètres) :
    if (condition d'arrêt) :
        return valeur
    else:
        #Traitements
        return NomFn (Valeurs)
#PP
X = NomFn(parm)
```

<!-- TODO vérifier: l'original écrit « NomP(parm) » et « NomFn(parm) » (« parm » au lieu de « param ») dans les appels Python, et « NomFN » / « NomFn » selon les endroits ; transcrit tel quel -->

**Remarques :**

- La **condition de travail** est l'inverse de la **condition d'arrêt**.
- Une **procédure** s'arrête lorsqu'elle **ne fait pas** l'appel à elle-même.
- Une fonction s'arrête lorsqu'elle **reçoit** une valeur.
- Dans un module récursif, il faut s'assurer que la condition d'arrêt soit **atteinte** après un nombre fini d'appels. Cette condition d'arrêt **ne peut** en aucun cas être un appel récursif.

## II. Exemples des modules récursifs

### 1. Afficher « TuTo » 5 fois

```algorithme
Procédure Afficher (N : entier)
Début
    Si (N ≠ 0) Alors
        Ecrire ("TuTo")
        Afficher (N-1)
    Fin Si
Fin
```

L'appel se fait par : `Afficher (5)`

```python
def Afficher (N) :
    if (N != 0) :
        print ("TuTo")
        Afficher(N-1)
#PP
Afficher (5)
```

### 2. Calculer la somme d'un tableau T rempli par N entiers

```algorithme
Fonction SomTab (T : Tab, N : entier) : entier
Début
    Si (n=-1) Alors
        Retourner 0
    Sinon
        Retourner T[N] + SomTab (T, N-1)
    Fin Si
Fin
```

L'appel se fait par : `S ← SomTab(T,N-1)`

Ou bien : `Ecrire ("la somme est :",SomTab(T,N-1))`

```python
def NomFn(T,N):
    if (N ==-1):
        return 0
    else:
        return T[N] + SomTab (T, N-1)
#PP
S=SomTab(T,N-1)
#ou bien
print("la somme est :", SomTab(T,N-1))
```

<!-- TODO vérifier: l'original écrit « Si (n=-1) » en minuscule alors que le paramètre est N ; la fonction Python est nommée « def NomFn(T,N): » alors que l'appel récursif et l'appel principal utilisent « SomTab » ; transcrit tel quel -->

**Remarques :**

- Dans l'appel des modules l'argument **N-1** transmis pour que le module **converge** et **arrive** à la condition d'arrêt.
- La fonction **SomTab** s'arrête lorsque N atteint la valeur **-1**, puis-ce que si le N=0 (tableau vide) l'appel se fait par **SomTab (T, -1)** d'où la fonction renvoie **0**.
- La procédure **Afficher** s'arrête lorsque **N** attient la valeur **0**.

**Attention !** L'existence d'une condition d'arrêt ne signifie pas que l'appel récursif s'arrête grâce à celle-ci.

Prenons l'exemple de l'exécution de `Afficher(-1)`

- `Afficher(-1)` conduit par appel récursif à l'exécution de `Afficher(-2)`,
- `Afficher(-2)` conduit par appel récursif à l'exécution de `Afficher(-3)`,
- `Afficher(-3)` conduit par appel récursif à l'exécution de `Afficher(-4)`,
- …

La condition d'arrêt **N=0** n'est jamais atteinte et on obtient une suite infinie d'appels. Ainsi, il est important d'ajouter une **précondition** pour imposer que **N** soit un entier naturel.

## III. La récursivité directe, croisée et indirecte

- **Récursivité directe :** un sous-programme **A**, appelle directement **A**.
- **Récursivité croisée** un sous-programme **A**, appelle un sous-programme **B** qui appelle **A**.
- **Récursivité indirecte** un sous-programme **A**, appelle un sous-programme **B** qui appelle un sous-programme **C** … qui appelle **A**.

## IV. Mécanisme de fonctionnement de la récursivité

La factorielle d'un entier positif N notée N! =1\*2\*…\*N (d'où 0 ! =1)

**Exemple :**

- Factorielle (1) = 1
- Factorielle (2) = 1\*2 = 2 (obtenu en multipliant le résultat précédent par 2)
- Factorielle (3) = 1 \* 2 \* 3 = 6 (obtenu en multipliant le résultat précédent par 3)
- Factorielle (4) = 1 \* 2 \* 3 \* 4 = 24 (obtenu en multipliant le résultat précédent par 4)
- …

<!-- TODO vérifier: dans l'original, des flèches relient chaque résultat au « *2 », « *3 », « *4 » suivant ; rendu ici entre parenthèses -->

**Formule d'hérédité :** Factorielle (N) = Factorielle (N-1) \* N

Pour calculer la factorielle d'un nombre N on peut utiliser une méthode itérative ou récursive. Soit la fonction suivante :

### 1. Version itérative

```algorithme
Fonction Fact (N : entier) : entier
Début
    F ← 1
    Pour i de 2 à N Faire
        F ← F * i
    Fin Pour
    Retourner F
Fin
```

```python
def Fact (N) :
    F=1
    for i in range(2,N+1):
        F = F * i
    return F
```

### 2. Version récursive

```algorithme
Fonction Fact (N : entier) : entier
Début
    Si (N = 0) Alors
        Retourner 1
    Sinon
        Retourner N * Fact (N – 1)
    Fin Si
Fin
```

```python
def Fact (N):
    if (N==0):
        return 1
    else:
        return N * Fact (N-1)
```

<!-- TODO vérifier: dans l'original, les deux versions sont présentées côte à côte dans un tableau à deux colonnes « Itératif » / « Récursif » ; les sous-titres « 1. Version itérative » et « 2. Version récursive » sont ajoutés (absents du PDF) -->

**Exemple :**

Calcul de **4!** (N = 4) par la fonction récursive Factorielle :

| Appel | Résultat |
|---|---|
| Fact (4) | = **24** |
| 4 \* Fact (3) | = 4 \* **6** = 24 |
| 3 \* Fact (2) | = 3 \* **2** = 6 |
| 2 \* Fact (1) | = 2 \* **1** = 2 |
| 1 \* Fact (0) | = 1 \* **1** = 1 |
| 1 (arrêt de la récursivité) | |

<!-- TODO vérifier: dans l'original, ce calcul est dessiné en escalier avec des flèches montantes (descente jusqu'à Fact (0), puis remontée des résultats) ; mis en tableau -->

Une **pile d'exécution** permet de mémoriser des informations sur les fonctions en cours d'exécution dans un programme.

Le principe est le suivant :

- L'instruction située en haut de la pile d'exécution est en cours d'exécution,
- Les instructions en dessous sont mises en pause dans l'attente de se retrouver au sommet de la pile d'exécution.

**Empilage :**

![Six états successifs de la pile d'exécution pour Fact(4) : Fact(4) ; Fact(3) sur 4*Fact(3) ; Fact(2) sur 3*Fact(2) sur 4*Fact(3) ; Fact(1) sur 2*Fact(1) sur 3*Fact(2) sur 4*Fact(3) ; Fact(0) sur 1*Fact(0) sur 2*Fact(1) sur 3*Fact(2) sur 4*Fact(3) ; 1 sur 1*Fact(0) sur 2*Fact(1) sur 3*Fact(2) sur 4*Fact(3)](figures/pile-empilage.png)
<!-- TODO figure: à recréer -->

**Dépilage :**

![Six états successifs de la pile pendant le dépilage : 1 sur 1*Fact(0), 2*Fact(1), 3*Fact(2), 4*Fact(3) ; puis 1*1 = 1 ; 2*1 = 2 ; 3*2 = 6 ; 4*6 = 24 ; Fact(4) = 24](figures/pile-depilage.png)
<!-- TODO figure: à recréer -->

## Série d'exercices

<!-- TODO vérifier: ces deux exercices sont intitulés « Application de cours : Application N°1 » et « Application N°2 » dans le PDF ; numérotés Exercice 1 et 2 ici -->

### Exercice 1

(Application N°1)

Mettez la lettre V (Vrai) dans la case qui correspond à chaque proposition si vous jugez qu'elle est vraie sinon mettez la lettre F (Faux).

**a.** Une procédure :

- est obligatoirement récursive
- n'est jamais récursive
- peut être récursive

**b.** Dans un module récursif, nous utilisons obligatoirement une structure :

- conditionnelle
- itérative à condition d'arrêt
- itérative complète

**c.** Pour appliquer la récursivité, un ordinateur utilise :

- une pile
- un fichier
- un tableau

**d.** Parmi les dessins suivants, lesquels pouvant être réalisés grâce à un module récursif :

![Trois dessins : des carrés emboîtés dans un coin, un arbre dont les branches se divisent, des cercles concentriques](figures/dessins-recursifs.png)
<!-- TODO figure: à recréer -->

<!-- grille de réponse supprimée -->

### Exercice 2

(Application N°2)

```python
def Inc1(n):
    if n == 0:
        return True
    else:
        return Inc2(n-1)
def Inc2(n):
    if n == 0:
        return False
    else:
        return Inc1(n-1)
```

- Donner le traçage de l'exécution de : **Inc1 (4)**, **Inc1(5)**, **Inc2**(4) et **Inc2 (5)**
- Donner le rôle des fonctions **Inc1** et **Inc2**.
