---
niveau: 2eme
chapitre: 3
titre: Série N° 3 : Les tableaux
type: serie
notions: remplissage d'un tableau, somme, minimum et maximum, occurrences, tableaux de chaînes, tableaux parallèles, programmation modulaire
source: Classroom — Série N° 3 - Les Tableaux
---

# Série N° 3 : Les tableaux

## Série d'exercices

<!-- TODO vérifier: la numérotation des exercices continue celle des séries 1 et 2 (31 à 44), comme dans le PDF ; le titre du PDF est « Série N° : 3-Les Tableaux » -->

### Exercice 31

Ecrire un programme qui permet de remplir un tableau T de n entiers, puis calculer leur somme et afficher le résultat.

### Exercice 32

Ecrire un programme qui permet de remplir un tableau T de n entiers, puis calculer et afficher le minimum et le maximum des éléments du tableau T.

### Exercice 33

Ecrire un programme qui permet de remplir un tableau T de n entiers, puis calculer et afficher le le maximum des éléments du tableau T en précisant quelle position elle occupe dans le tableau.

### Exercice 34

Ecrire un algorithme permettant de trouver et d'afficher le nombre d'occurrence d'un réel R dans un tableau T de N réels (N est au maximum 50)

### Exercice 35

Ecrire un programme qui permet de remplir un tableau T de n entiers, puis calculer et afficher le nombre des valeurs négatives et le nombre des valeurs positives.

### Exercice 36

Ecrire un programme qui permet de remplir un tableau T de n réel désigne les notes des élèves d'une classe

Le programme, une fois la saisie terminée, renvoie le nombre de ces notes supérieures à la **moyenne** de la classe.

### Exercice 37

Soit à saisir n caractères dans un tableau **T** de taille **Max=100**, puis de créer à partir de **T**, 3 tableaux (**TL** : tableau de lettres, **TS** : tableau de symboles, **TC** : tableau de chiffres) et enfin afficher le contenu de ces 3 tableaux.

### Exercice 38

Ecrire un programme qui permet de remplir deux tableaux **T1 et T2** avec **n** entiers

Le nouveau tableau **T** sera la somme des éléments des deux tableaux de départ **T1 et T2**.

| T1 : | 4 | 8 | 7 | 9 | 1 | 5 | 4 | 6 |
|---|---|---|---|---|---|---|---|---|
| **T2 :** | 7 | 6 | 5 | 2 | 1 | 3 | 7 | 4 |
| **T :** | 11 | 14 | 12 | 11 | 2 | 8 | 11 | 10 |

### Exercice 39

Ecrire un programme qui permet de remplir deux tableaux **T1 et T2** avec **n** entiers et qui calcule le **schtroumpf** des deux tableaux.

Pour calculer le **schtroumpf**, il faut multiplier chaque élément du tableau 1 par chaque élément du tableau 2, et additionner le tout. Par exemple si l'on a :

| T1 : | 4 | 8 | 7 | 12 |
|---|---|---|---|---|
| **T2 :** | 3 | 6 | | |

Le Schtroumpf sera :

3 * 4 + 3 * 8 + 3 * 7 + 3 * 12 + 6 * 4 + 6 * 8 + 6 * 7 + 6 * 12 = 279

<!-- TODO vérifier: dans le PDF, T2 est dessiné à part, plus étroit que T1 (deux cases 3 et 6) ; ici la deuxième ligne du tableau est complétée par des cases vides -->

### Exercice 40

On désire écrire l'application **tab_chaine** qui permet de remplir un tableau **T** par **N** chaînes de caractères avec (5<=N<=50), sachant que la taille des chaînes de caractères ne doit pas dépasser les 10 caractères, puis remplir un deuxième tableau **TR** par les mêmes chaînes renversées et enfin afficher **T** et **TR**.

**Exemple :**

| T | analyse | année | info | devoir | elle |
|---|---|---|---|---|---|
| **TR** | esylana | eénna | ofni | rioved | elle |

### Exercice 41

On propose de saisie 2 tableaux d'entiers et un tableau d'opérateur dont la taille des 3 tableaux est N, (5≤N≤30), ainsi qu'on remplit un tableau T par le résultat de l'équation.

| T1 : | 5 | 1 | -6 | 9 | 13 |
|---|---|---|---|---|---|
| **TOp :** | "+" | "-" | "*" | "+" | "/" |
| **T2 :** | 7 | 16 | -5 | 11 | 2 |
| **T :** | 12 | -15 | 30 | 20 | 6,5 |

<!-- TODO vérifier: dans le PDF, les étiquettes « T2 : » et « Résultat : » sont superposées à gauche de la ligne 7, 16, -5, 11, 2 (étiquetée ici T2) ; la dernière ligne (étiquetée T) est 12, -15, 30, 20, 6,5 -->

### Exercice 42

Faire l'algorithme modulaire d'un programme qui permet de :

- Saisir la taille N (2 ≤ N ≤ 50) d'un tableau T de chaînes de caractères ;
- Remplir le tableau T par N mots composés au maximum de 10 caractères.
- Remplir un deuxième tableau V par des entiers qui correspondent aux nombres de caractères non alphabétiques dans chaque mot.
- Calculer et afficher le nombre total des caractères non alphabétiques.

### Exercice 43

Soient A un tableau de n entiers de 4 chiffres chacun et b un tableau de n chiffres décimaux (5≤n≤20). On veut former le nombre X de la manière suivant :

Si le chiffre B[i] est l'un des chiffres de A[i] alors on l'ajoute à X à droite.

Décomposer le problème en modules, analPayser le problème principal ainsi que chaque module puis écrire les algorithmes.

**Exemple :**

| A | 3014 | 1633 | 5049 | 2567 | 9120 | 4871 |
|---|---|---|---|---|---|---|
| **B** | 4 | 9 | 1 | 2 | 0 | 3 |

X est 420

<!-- TODO vérifier: « analPayser » (au lieu de « analyser ») et « b » minuscule pour le tableau B dans l'énoncé ; transcrits tels quels -->

### Exercice 44

Écrire un programme modulaire en **Python** qui permet de :

- Remplir un tableau **NOMS** par **N** chaine de caractères désignent les noms des élèves d'une classe, **(4 ≤ N < 20),** sachant que chaque nom commence obligatoirement par une lettre majuscule et ne dépasse pas les 10 caractères.
- Remplir un deuxième tableau **NOTES** par **N** Réels désignent les notes des élèves d'une classe, sachant que chaque note est comprise entre 0 et 20.
- Calculer **la meilleure note** et afficher les noms qui ont cette note.
- Calcules **la moyenne générale** de classe et afficher les noms qui une note supérieure ou égale à cette moyenne.

**Exemple :**

Pour N = 5

| NOMS | "Ahmed" | "ONS" | "KARIM" | "Ali" | "Mohamed" |
|---|---|---|---|---|---|
| **NOTES** | 17,75 | 8 | 17,75 | 1 | 13,5 |

Le programme affiche :

> La meilleure note est : 17 ,75 les noms qui ont cette note sont :  
> Ahmed  
> KARIM  
> La moyenne générale de classe est : 11,6 les noms qui ont une note >= sont :  
> Ahmed  
> KARIM  
> Mohamed
