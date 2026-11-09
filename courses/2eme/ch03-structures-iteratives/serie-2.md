---
niveau: 2eme
chapitre: 3
titre: Série N° 2 : Les chaînes de caractères
type: serie
notions: parcours d'une chaîne, comptage de voyelles, occurrences, palindrome, anagramme, tautogramme, fréquence des lettres
source: Classroom — Série N° 2 - Les chaines de caractères
---

# Série N° 2 : Les chaînes de caractères

## Série d'exercices

<!-- TODO vérifier: la numérotation des exercices continue celle de la série 1 (16 à 30), comme dans le PDF -->

### Exercice 16

Ecrire un algorithme qui permet de remplir une chaine ch et de compter le nombre de voyelle majuscule dans une chaîne de caractères Ch.

### Exercice 17

Ecrire un algorithme qui permet de remplir une chaine ch et de compter le nombre de voyelle dans une chaîne de caractères Ch.

### Exercice 18

Ecrire un algorithme qui permet de remplir une chaine ch et un caractère C et de donner le nombre d'occurrences d'un caractère C dans une chaine CH.

### Exercice 19

Ecrire un algorithme qui permet de remplir deux chaines ch et Mot et de donner le nombre d'occurrences d'une chaine Mot dans une chaine CH.

### Exercice 20

Ecrire un programme qui permet d'inverser une chaine de caractères et l'afficher.

### Exercice 21

Ecrire un programme qui permet de saisir une chaine de caractères et d'extraire les caractères non alphabétiques

### Exercice 22

Ecrire un algorithme qui permet de remplir une chaine ch et d'afficher si la chaine ch est palindrome ou non.

N.B : une chaine est dite palindrome si elle s'écrite de deux sens

Exemple : ELLE, RADAR, AZZA...

### Exercice 23

On se propose d'écrire un programme qui saisit un texte composé par des lettres et de caractères de ponctuation (la lecture : caractère par caractère) puis calcule et affiche la fréquence (nombre d'occurrence) de chaque lettre utilisée dans le texte.

**Remarque :** la fin du texte est signalée par le caractère #.

### Exercice 24

On appelle **Poids d'un mot** la somme des produits de la position de chaque voyelle contenue dans le mot par son range dans l'alphabet français. Une lettre a le même range qu'elle écrite en majuscule ou en minuscule.

**Exemple :** le mot « Epreuve » a pour poids 165 car (1*5)+(4*5)+(5*21)+(7*5)=165.

<!-- TODO vérifier: l'énoncé ne demande rien (pas de verbe ni de travail à faire après l'exemple) ; transcrit tel quel -->

### Exercice 25

Un "tautogramme" est une chaîne dont chacun de ses mots commence par la même lettre (sans distinction entre majuscule et minuscule).

**Exemple :** la chaîne "Le lion lape le lait lentement" est un "tautogramme"

Ecrire un programme, permettant de saisir une chaîne de caractères composée uniquement de lettres et d'espaces (on suppose que deux mots consécutifs sont séparés par un seul espace) Puis d'afficher un message indiquant si cette chaîne est "tautogramme" ou non.

### Exercice 26

On veut écrire un programme permettant de lire deux mots ch1 et ch2 et d'afficher tous les caractères qui apparaissent dans les deux chaînes sans redondance.

**Exemple :**

Soit ch1= "Bonjour" et ch2="Bonbon".

Résultat : B, O, N.

### Exercice 27

On veut écrire un programme permettant de lire deux mots ch1 et ch2 et d'afficher si les deux chaines sont anagramme ou non.

N.B : deux chaines sont anagrammes si les deux mots sont composés de mêmes lettres

**Exemple :**

ch1= "chien" et ch2="niche".

### Exercice 28

Pour chercher le chiffre de chance d'une personne, en procède comme suit : on additionne les chiffres composants la date de naissance de la personne concerné. Au nombre obtenu, on refait le même procédé jusqu'à obtenir un nombre composé d'un seul chiffre. Ce nombre est le chiffre de chance.

**Exemple :**

Soit la date de naissance suivante : 29/09/1999.

On additionne les chiffres de naissance : 2+9+0+9+1+9+9+9=48

48 est composé de 2 chiffres, on refait le même traitement : 4+8=12

12 est composé de 2 chiffres, on refait le même traitement : 1+2=3

3 est le chiffre de chance recherché.

### Exercice 29

Ecrire un algorithme qui permet de saisir une phrase Ph et de compter et d'afficher le nombre des lettres par mot.

### Exercice 30

Ecrire un algorithme qui permet de remplir une chaine ch et de calculer une équation sous la forme d'une chaine et retourne le résultat dans un entier.

**Exp :**

Ch ="314+9+16+128" la fonction retourne 467
