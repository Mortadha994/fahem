---
niveau: 2eme
chapitre: 2
titre: Les structures de contrôle conditionnelles
type: cours
notions: structure conditionnelle Si, simple choix, double choix, conditions imbriquées, opérateurs de comparaison, opérateurs logiques, structure conditionnelle Selon
source: Classroom — Chapitre 2 - Les structures de contrôles conditionnelles
---

# Chapitre II : Les structures de contrôle conditionnelles

<!-- TODO vérifier: les mots-clés sont écrits SI / Si, SINON / Sinon, FINSI / Fin SI / Fin si, SELON / FIN SELON selon les endroits du PDF ; harmonisés en Si, Alors, Sinon, Fin Si, Selon, Fin Selon -->

## I. Introduction

Souvent les problèmes nécessitent l'étude de plusieurs situations qui ne peuvent pas être traitées par les séquences d'actions simples. Puisqu'on a plusieurs situations, et qu'avant l'exécution, on ne sait pas à quel cas de figure on aura à exécuter, dans l'algorithme on doit prévoir tous les cas possibles. Ce sont les structures conditionnelles qui le permettent, en se basant sur ce qu'on appelle prédicat ou condition.

## II. Définition

Une instruction conditionnelle est une instruction qui permet l'exécution d'une ou plusieurs autres instructions spécifiées selon le résultat d'une condition établie. Il faut remarquer qu'une instruction conditionnelle peut englober une autre et sont alors appelées des instructions conditionnelles imbriquées.

Les actions à effectuer peuvent être des actions simples ou composées (affectation, appel de procédures, instruction tant que, suite d'instructions,...).

## III. La structure conditionnelle Si

### 📌 1. Simple choix

**Syntaxe :**

```algorithme
Si <condition> Alors
    <Traitement>
Fin Si
```

```python
if (<condition>) :
    <Traitement>
```

- `<Condition>` : Expression logique qui donnera un résultat logique (Vrai ou Faux).
- `<Traitement>` : Une ou plusieurs instructions ou actions pouvant être de toute nature (Simple, Conditionnelle ou itérative).

### 📌 2. Double choix

**Syntaxe :**

```algorithme
Si <condition> Alors
    <Traitement 1>
Sinon
    <Traitement 2>
Fin Si
```

```python
if (<condition>) :
    <Traitement 1>
else :
    <Traitement 2>
```

La `<condition>` est un prédicat, qui peut être vrai ou faux, selon les valeurs des paramètres la constituant.

Si la condition est vérifiée (sa valeur est vrai), c'est le `<Traitement 1>` qui sera exécutée. Ensuite, le système passe à l'exécution juste après le Fin Si.

Dans le cas contraire, lorsque la condition n'est pas vérifiée (valeur de la condition est faux), c'est le `<Traitement 2>` qui s'exécute, en cas où celui-ci existe (facultative). S'il n'existe pas, le système passe directement à l'instruction qui suit le Fin Si.

Les traitements 1 et 2, peuvent être des actions simples ou même des structures conditionnelles.

**Exemple :**

Une remise de 5 % est accordée si la somme des achats dépasse 100 Euros.

```algorithme
Si Montant>100 Alors
    Rem ← Montant*0,05
Sinon
    Rem ← 0
Fin Si
```

Python :

**Version 1**

```python
if (Montant>100) :
    Rem =Montant*0,05
else :
    Rem =0
```

**Version 2**

```python
Rem =0
if (Montant>100) :
    Rem =Montant*0,05
```

<!-- TODO vérifier: « 0,05 » avec une virgule décimale dans le code Python (Python attend 0.05) ; transcrit tel quel -->

**Remarque :**

- L'expression logique peut effectuer une comparaison entre plusieurs grandeurs. Elle utilise alors les opérateurs de comparaison : `>`, `>=`, `<`, `<=`, `<>`.
- L'expression logique peut être complexe et peut faire intervenir les opérateurs logiques : ET, OU.

**Exemple :** `(a>b) ET (a>c)`.

### 3. Structures imbriquées

**Généralement :**

```algorithme
Si <condition1> Alors
    Si <condition2> Alors
        <Traitement 1>
    Sinon
        <Traitement 2>
    Fin Si
Sinon
    Si <condition3> Alors
        <Traitement 3>
    Sinon
        <Traitement 4>
    Fin Si
    <Traitement 5>
Fin Si
```

```python
if (<condition1>) :
    if (<condition2>) :
        <Traitement 1>
    else :
        <Traitement 2>
else:
    if (<condition3>) :
        <Traitement 3>
    else :
        <Traitement 4>
    <Traitement 5>
```

**Exemple :**

```algorithme
Si moy ≥ 10 Alors
    Si moy ≥ 15 Alors
        Ecrire ("Excellent")
    Sinon
        Ecrire ("Admis")
    Fin Si
Sinon
    Si moy ≥ 9 Alors
        Ecrire ("Admis avec rachat")
    Sinon
        Ecrire ("Redouble")
    Fin Si
Fin Si
```

```python
if (moy >=10):
    if (moy >=15) :
        print("Excellent")
    else :
        print("Admin")
elif (moy >=9) :
    print("Admis avec rachat")
else :
    print("Redouble")
```

<!-- TODO vérifier: « Admin » (au lieu de « Admis ») dans le code Python de l'original ; les deux programmes ne sont pas équivalents (le Python utilise elif au niveau du premier if, sans la condition moy < 10 de l'algorithme) ; transcrits tels quels -->

## IV. La structure conditionnelle Selon

Cette structure conditionnelle est appelée aussi à choix multiple ou sélectif car elle sélectionne entre plusieurs choix à la fois, et non entre deux choix alternatifs (le cas de la structure Si).

### 📌 Syntaxe : Selon

```algorithme
Selon (sélecteur)
    Valeur1: <Suite d'action(s)1>
    Valeur2_1 . . Valeur2_2 : <Suite d'action(s)2>
    Valeur3_1, Valeur3_2, Valeur3_3: <Suite d'action(s)3>
    .
    .
    <liste de valeurs n-1> : <Suite d'action(s)n-1>
    [Sinon <Suite d'action(s)n>] (Facultative)
Fin Selon
```

**Python :** à partir de la version python 3.10

```python
match (sélecteur) :
    case Valeur 1 :
        <Suite d'action(s)1>
    case sélecteur if Valeur2_1 <= sélecteur <= Valeur2_2 :
        <Suite d'action(s)2>
    case Valeur3_1 | Valeur3_2 | Valeur3_3 :
        <Suite d'action(s)3>
    .
    .
    case Valeurs n-1 :
        <Suite d'action(s)n-1>
    case _:
        <Suite d'action(s)n> ;(Facultative)
```

<!-- TODO vérifier: dans le PDF le bloc Python du Selon est placé après les remarques ci-dessous, et la ligne « <Suite d'action(s)3> » n'y est pas indentée ; ici le Python est regroupé avec la syntaxe de l'algorithme et indenté -->

### Remarque

- Le sélecteur peut être une variable de type scalaire ou une expression arithmétique ou logique.
- La structure Selon évalue le "Sélecteur", passe à comparer celui-ci respectivement avec les valeurs dans les listes. En cas d'égalité avec une valeur, les actions correspondantes, qui sont devant cette valeur seront exécutées.
- Devant "Cas", il peut y avoir une seule valeur, une suite de valeurs séparées par des virgules ou / ou un intervalle de valeurs.
- Après avoir traité la suite d'actions correspondante, l'exécution se poursuit après le Fin Selon.
- Le sélecteur doit avoir le même type que les valeurs devant les cas.

### Exemple 1 : Afficher le nom d'un mois donné

```algorithme
Selon mois
    1 : Ecrire ("Janvier")
    2 : Ecrire ("Février")
    .
    .
    12 : Ecrire ("décembre")
Sinon
    Ecrire ("Mois incorrecte")
Fin Selon
```

```python
match mois :
    case 1 :
        print ("Janvier")
    case 2 :
        print ("Février")
    .
    .
    case12 :
        print ("Décembre")
    case _ :
        print ("Mois incorrecte")
```

<!-- TODO vérifier: « décembre » (minuscule) en algorithme et « Décembre » en Python ; « case12 » sans espace ; transcrits tels quels -->

### Exemple 2 : Afficher le nombre de jours d'un mois donné

```algorithme
Selon mois
    1,3,5,7,8,10,12 :
        Ecrire ("31 jours")
    4,6,9,11 :
        Ecrire ("30 jours")
    2 :
        Ecrire ("Donner l'année :")
        Lire(A)
        Si (a mod 4 = 0) Alors
            Ecrire ("29 jours")
        Sinon
            Ecrire ("28 jours")
        Fin Si
Sinon
    Ecrire ("Mois incorrecte")
Fin Selon
```

```python
match mois :
    case 1 | 3 | 5 | 7 | 8 | 10 | 12 :
        print ("31 jours")
    case 4 | 6 | 9 | 11 :
        print ("30 jours")
    case2 :
        a=int(input("Donner l'année :"))
        if( a % 4 ==0) :
            print ("29 jours")
        else :
            print("28 jours")
    case _ :
        print ("Mois incorrecte")
```

<!-- TODO vérifier: « Lire(A) » puis « a mod 4 » (casse différente) ; « case2 » sans espace ; transcrits tels quels -->

### Exemple 3 : Afficher la catégorie d'un élève selon l'âge donné

```algorithme
Selon age
    3,4,5 : Ecrire ("Jardin d'enfant")
    6 . . 12 : Ecrire ("école primaire")
    13 . . 15 : Ecrire ("Collège")
    16 .. 19 : Ecrire ("Lycée")
Sinon
    Ecrire ("n'est pas un élève")
Fin Selon
```

```python
match age :
    case 3 | 4 | 5 | :
        print ("Jardin d'enfant")
    case age if 6 <= age <= 12 :
        print ("école primaire")
    case age if 13 <= age <= 15 :
        print ("Collège")
    case age if 16 <= age <= 19 :
        print ("lycée")
    case _ :
        print ("n'est pas un élève ")
```

<!-- TODO vérifier: « case 3 | 4 | 5 | : » avec un « | » final superflu ; titre original « Afficher a catégorie » (corrigé en « la ») ; transcrits tels quels -->
