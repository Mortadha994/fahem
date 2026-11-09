---
niveau: 2eme
chapitre: 3
titre: Les structures algorithmiques de contrôle itératives
type: cours
notions: schéma itératif Pour, fonction range, schéma itératif Tant que, schéma itératif Répéter Jusqu'à, nombre d'itérations connu ou inconnu
source: Classroom — Chapitre 3 - Les Structures itératives
---

# Chapitre III : Les structures algorithmiques de contrôle itératives

<!-- TODO vérifier: les mots-clés sont écrits Pour / pour, faire / Faire, Fin pour / FINPOUR, Tant que / TANT QUE, Fin tant que, sinon / Sinon, fin si, Répéter / REPETER selon les endroits du PDF ; harmonisés en Pour, Faire, Fin Pour, Tant que, Fin Tant que, Répéter, Jusqu'à, Si, Alors, Sinon, Fin Si. Les mots-clés Python For / While / Range de l'original sont écrits en minuscules (for, while, range) -->

<!-- Le PDF ne contient du Python que dans les syntaxes et les exemples ; rien n'a été ajouté -->

## I. Introduction

- Dans les problèmes quotidiens, on ne traite pas uniquement des séquences d'actions, sous ou sans conditions, mais il peut être fréquent d'être obligé d'exécuter un traitement (séquence d'actions), plusieurs fois. En effet, pour saisir les N notes d'un étudiant et calculer sa moyenne, on est amené à saisir N variables, puis faire la somme et ensuite diviser la somme par N.
- Cette solution nécessite la réservation de l'espace par la déclaration des variables, et une série de séquence d'écriture/lecture.
- Ce problème est résolu à l'aide des structures répétitives. Celles-ci permettent de donner un ordre de répétition d'une action ou d'une séquence d'actions une ou plusieurs fois.

## II. Le schéma Itératif Pour

### 1. Rôle

Ce schéma itératif permet l'exécution d'un traitement donné en un nombre de fois n donné. On peut donc l'utiliser chaque fois qu'on connaît le nombre d'exécutions souhaitées d'un même traitement (ensemble d'instructions formant le corps de la boucle).

### 📌 2. Syntaxe de la boucle Pour

<!-- TODO vérifier: le titre original est « 2. Syntaxe : » (identique pour les trois schémas) ; précisé ici pour que chaque section épinglée ait un titre distinct -->

```algorithme
[Initialisation(s)]
Pour compteur de Vi à Vf [PAS = <a>] Faire
    <instruction1>
    <instruction2>
    <instruction3>
    .
    .
    .
    <instructionN>
Fin Pour
```

```python
[initialisation(s)]
for compteur in range(Vi, Vf+1, Pas) :
    <instruction1>
    <instruction2>
    .
    .
    .
    <instructionN>
```

<!-- TODO vérifier: l'original écrit « For compteur in Range(Vi, VF+1,Pas) » ; transcrit en minuscules. Le « Vf+1 » ne convient qu'à un pas positif ; transcrit tel quel -->

- `Compteur` : nom de la variable représentant le compteur des itérations à effectuer.
- `Vi` : valeur initiale.
- `Vf` : valeur finale.
- `<a>` : la valeur du pas pour faire passer compteur d'une valeur à la suivante.

Compteur, Vi et Vf doit être de type entier (Algo/python) ou caractère (Algo).

### 3. Les étapes d'exécution de la boucle Pour

1. Initialisation de compteur par la boucle Vi.
2. Test si Vi dépasse Vf (du côté supérieur ou inférieur, selon la positivité ou la négativité du PAS).
   - Si oui, alors la boucle s'arrête et l'exécution se poursuit après le Fin Pour.
   - Sinon :
     - Exécution du traitement (les instructions).
     - Incrémentation ou décrémentation de compteur par la valeur du PAS.
     - Retour à l'étape 2.

**Remarque :**

- La boucle Pour est utilisée lorsqu'on connaît le nombre de répétition du traitement d'avance.
- Le nombre d'itérations de la boucle « Pour » est : |Vf-Vi| + 1
- La valeur du pas peut être positive ou négative et par conséquent, il faut au départ de la boucle que Vi <= Vf (parcours croissant) ou Vi >= Vf (parcours décroissant) selon la positivité ou la négativité de cette valeur.
- La valeur du PAS est égale à 1 par défaut.
- La fonction python « range » crée un compteur qui s'incrémente ou se décrémente automatiquement.

**Exemple :**

- `range(n)` renvoi un itérateur parcourant 0, 1, 2 ... , n − 1 ;
- `range(n,m)` renvoi un itérateur parcourant n, n+1, n+2, ..., m − 1 ;
- `range(n,m,p)` renvoi un itérateur parcourant n, n+p, n+2p , ..., m − 1.

### 4. Exemples

**Exemple 1 :**

```algorithme
Pour i de 1 à 5 Faire
    Ecrire("Ligne N° :", i)
Fin Pour
```

```python
for i in range(1,6) :
    print("Ligne N°:",i)
```

Affichage à l'écran :

> Ligne N° : 1  
> Ligne N° : 2  
> Ligne N° : 3  
> Ligne N° : 4  
> Ligne N° : 5

**Exemple 2 :**

```algorithme
Pour i de 5 à 1 (pas =-1) Faire
    Ecrire("Ligne N° :", i)
Fin Pour
```

```python
for i in range(5,0,-1) :
    print("Ligne N°:",i)
```

Affichage à l'écran :

> Ligne N° : 5  
> Ligne N° : 4  
> Ligne N° : 3  
> Ligne N° : 2  
> Ligne N° : 1

### 5. Activité

| Instruction en python | Valeur de i |
|---|---|
| `for i in range(5):` | 0,1,2,3,4 |
| `for i in range(1,5):` | 1,2,3,4,5 |
| `for i in range(0,4):` | 0,1,2,3,4 |
| `for i in range(2,5):` | 2,3,4 |
| `for i in range(5,2,-1):` | 5,4,3,2 |
| `for i in range(1,5,-1):` | 5,4,3,2 |
| `for i in range(2,11,3):` | 2,5,8 |
| `for i in range(10,-10,-5):` | 10,5,0,-5 |
| `for i in range(len("Python")):` | 0,1,2,3,4,5 |

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: le tableau original comporte trois colonnes à remplir (Vrai, Faux, Résultat correct si Faux), vides ; les valeurs de la colonne « Valeur de i » sont celles du PDF (certaines sont volontairement fausses : l'activité demande de les corriger) -->

## III. Le Schéma Itératif Tant que

### 1. Rôle

Ce type de schéma permet l'exécution d'un traitement donné, plusieurs fois tant qu'une condition spécifiée est vraie. La condition est une expression logique qui peut être simple ou composée mais qui donne toujours un résultat logique. Par conséquent, ce type de schéma est utilisé chaque fois que le nombre d'itérations qui seront exécutées n'est pas déterminé à priori.

### 📌 2. Syntaxe de la boucle Tant que

```algorithme
[Initialisation(s)]
Tant que (condition(s)) Faire
    Instruction 1
    Instruction 2
    Instruction 3
    .
    .
    .
    Instruction N
Fin Tant que
```

```python
[Initialisation(s)]
while (condition(s)) :
    Instruction 1
    Instruction 2
    Instruction 3
    .
    .
    Instruction N
```

- `Traitement` : un ou plusieurs blocs d'instructions.
- `Condition` : c'est une condition de travail sous forme d'expression logique qui donne un résultat logique vrai ou faux.

### 3. Les étapes d'exécution de la boucle Tant que

1. Test de la valeur de la `<condition d'exécution>`.
2. Si elle est vérifiée Alors :
   - Exécution du `<Traitement>`.
   - Retour à l'étape 1.

   Sinon : arrêt de la boucle.

**Remarque :**

- Dans cette boucle, le traitement peut ne pas être exécuté aucune fois, lorsque la condition d'exécution est à faux dès le départ.
- Les paramètres de la condition doivent être initialisés par lecture ou par affectation avant la boucle.
- Il doit y avoir une action dans le `<Traitement>` qui modifie la valeur de la condition.

### 4. Exemples

```algorithme
Tant que (a ≠ b) Faire
    Si (a > b) Alors
        a ← a - b
    Sinon
        b ← b - a
    Fin Si
Fin Tant que
```

```python
while (a != b) :
    if (a>b) :
        a=a-b
    else :
        b=b-a
```

## IV. Le Schéma Itératif Répéter Jusqu'à

### 1. Rôle

Ce type de schéma permettra l'exécution d'un traitement donné, plusieurs fois, jusqu'à ce qu'une condition spécifiée soit vraie. La condition est une expression logique qui peut être simple ou composée mais qui donne toujours un résultat logique. On peut utiliser ce schéma si on ne peut pas déterminer le nombre de répétitions à l'avance.

### 📌 2. Syntaxe de la boucle Répéter Jusqu'à

```algorithme
Initialisation(s)
Répéter
    Instruction 1
    Instruction 2
    .
    .
    Instruction N
Jusqu'à (condition(s) d'arrêt)
```

Python Version 1 :

```python
Initialisation(s)
while (not (condition(s) d'arrêt)) :
    Instruction 1
    instruction 2
    .
    .
    Instruction N
```

Python Version 2 :

```python
Initialisation(s)
B=False
while not B :
    Instruction 1
    instruction 2
    .
    .
    Instruction N
    B=(condition(s) d'arrêt)
```

- `Traitement` : un ou plusieurs blocs d'instructions.
- `<condition d'arrêt>` : c'est une condition d'arrêt sous forme d'expression logique (vrai ou faux).

### 3. Les étapes d'exécution de la boucle Répéter Jusqu'à

1. Exécution du `<Traitement>`.
2. Test de la valeur de la `<condition d'arrêt>`.
   - Si elle est vérifiée Alors la boucle s'arrête.
   - Sinon Retour à l'étape 1.

**Remarque :**

- Il doit y avoir une action dans le `<Traitement>` qui modifie la valeur de la condition.
- La différence entre le schéma itératif Répéter et le schéma Tant que est que le traitement spécifié est exécuté au moins une fois dans le premier cas et peut être 0 ou plusieurs fois dans le deuxième cas.

### 4. Exemples

```algorithme
Répéter
    Ecrire ("Donner un entier :")
    Lire(x)
Jusqu'à (x € [3..10])
```

Python v1 :

```python
x=int(input("Donner un entier :"))
while (not (3<=x<=10)) :
    x=int(input("Donner un entier :"))
```

Python v2 :

```python
B=False
while not B :
    x=int(input("Donner un entier :"))
    B=(3<=x<=10)
```

<!-- TODO vérifier: « x € [3..10] » (symbole € au lieu de ∈) dans l'algorithme de l'original ; transcrit tel quel -->
