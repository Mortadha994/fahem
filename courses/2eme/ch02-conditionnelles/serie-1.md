---
niveau: 2eme
chapitre: 2
titre: Série N° 1 : Les structures de contrôle conditionnelles
type: serie
notions: structure conditionnelle Si, conditions imbriquées, structure conditionnelle Selon, opérateurs logiques, équation du second degré
source: Classroom — Série N° 1 - Les structures Conditionnelles
---

# Série N° 1 : Les structures de contrôle conditionnelles

## Série d'exercices

### Exercice 1

Ecrivez un algorithme intitulé **Affich_op** permettant d'afficher en toutes lettres les quatre opérateurs arithmétique somme, Différence, Produit, Quotient.

### Exercice 2

Ecrivez un algorithme intitulé **Signe** permettant d'afficher le signe en toutes lettres d'un entier saisi au clavier.

Le signe est soit « Plus » soit « Moins ».

### Exercice 3

Ecrire un algorithme qui consiste à demander un nombre à l'utilisateur, et l'informer ensuite si ce nombre est positif ou négatif ou nul.

### Exercice 4

Ecrire un programme python qui demande un nombre à l'utilisateur et l'informe ensuite si ce nombre est pair ou impair.

### Exercice 5

Ecrire un programme python qui permet de calculer y= (-1)ⁿ +n.

### Exercice 6

Ecrire un algorithme qui demande l'âge d'un enfant à l'utilisateur. Ensuite, il l'informe de sa catégorie :

- "Poussin" de 6 à 7 ans
- "Pupille" de 8 à 9 ans
- "Minime" de 10 à 11 ans
- "Cadet" après 12 ans

Peut-on concevoir plusieurs algorithmes équivalents menant à ce résultat ?

### Exercice 7

Ecrire un algorithme qui calcule les solutions réelles d'une équation de second degré ax² + bx + c =0.

- Utiliser des variables de type entier pour a, b et c.
- Utiliser une variable d'aide d pour la valeur discriminant **b²-4\*a\*c** et décider à l'aide de d, si l'équation a une, deux ou aucune solution réelle.
- Afficher les résultats et les messages nécessaires.

### Exercice 8

On veut calculer le montant des impôts d'un salarié. La grille à utiliser est la suivante :

| Salaire Brut (sb) | Taux D'impot |
|---|---|
| Sb<150 DT | 5% |
| 150 DT<=sb<300 DT | 10% |
| 300 DT<=sb<600 DT | 20% |
| 600 DT et + | 25% |

Écrire un programme qui saisit le salaire et affiche **le montant des impôts** et le **salaire net**.

### Exercice 9

Écrire un programme qui permet de lire une lettre puis affiche s'il s'agit d'une voyelle ou d'une consonne.

**Exemple :**

- Entrée : c="y".
- Sortie : y est une voyelle.

### Exercice 10

Soit un programme permettant la réalisation d'une opération arithmétique de la forme **X** op **Y**.

Mettant en jeu 2 opérandes **X** et **Y**, sachant que :

a. **X** est un entier multiple de 3.
b. **Y** est réel compris entre -5 et 55.

Sachant que l'opérateur arithmétique, noté op, est saisi sous forme d'un caractère qui est soit « + », « -», « * », « / », « % ».

<!-- TODO vérifier: l'énoncé ne dit pas ce qu'il faut faire du programme (pas de verbe « écrire » ni de résultat demandé) ; transcrit tel quel -->

### Exercice 11

Écrire un programme qui affiche le type d'un caractère saisi tel que :

- 0,9 : chiffre.
- a, A : alphabet.
- +,-,*,/ : opération.
- $, ", &, } : autres caractères spéciaux.

<!-- TODO vérifier: les caractères spéciaux listés sont lus « $, '', &, } » sur le rendu (le 2e symbole est une paire de guillemets) -->

### Exercice 12

Soit à saisir une série de **trois nombres** séparés par le caractère « * ». Les nombres sont dits parentés si la somme du premier et du dernier chiffre de chacun des nombres est un diviseur du nombre suivant dans la saisie

**Exemple :**

814564*1212*66 les nombres sont parentés car (**8+4=12**) est un diviseur de **1212** et (**1+2=3**) est un diviseur de **66**.

Ecrire un programme qui permet de vérifier si les nombres saisis sont parentés ou non (Aucun contrôle de saisie n'est demandé).

### Exercice 13

Quel est la valeur de **A** et B après exécution de ces algorithmes

```algorithme
A ← 2
B ← 1
Si ((A>2) et (B≤1)) alors
    B ← 3
Sinon
    B ← 2
Fin si
```

```algorithme
A ← 2
A ← 0
Si A=2 alors
    B ← 3
Sinon si A=0 alors
    B ← 2
Sinon
    B ← 1
Fin si
```

```algorithme
A ← 2
Si (Non (A<2) ou (A=2)) alors
    B ← 3
Sinon
    B ← 1
Fin si
```

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: les trois algorithmes sont dans trois cadres côte à côte ; le deuxième ne montre qu'un seul « Fin si » à l'écran (« Sinon si » sans « Fin si » supplémentaire) alors que la couche texte en donne deux ; mots-clés laissés en minuscules (« alors », « Fin si ») comme dans l'original ; sous chaque cadre figurent deux cases A et B à compléter -->
