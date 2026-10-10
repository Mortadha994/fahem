---
niveau: 2eme
chapitre: 1
titre: Série N° 2 : Les structures simples
type: serie
notions: types et expressions, affectation, lecture et écriture, calculs arithmétiques, chiffres d'un entier, chaînes de caractères
source: Classroom — Série N° 2 - Les structures simples
---

# Série N° 2 : Les structures simples

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes (« lés éxpréssions suivantés ») ; accents rétablis par déduction, sans contrôle visuel de cette série -->

## Série d'exercices

### Exercice 1

a) Les variable N, P et Q sont entiers et contiennent respectivement les valeurs 5, 7 et 3. Les expressions suivantes sont-elles correctes. Si oui, donnez-leur type et leur valeur.

- `N mod P *Q`
- `N mod P div Q`
- `N = P oi N ≤ Q`
- `"N" + "P"`

<!-- TODO vérifier: « oi » dans la 3e expression (probablement « ou ») ; transcrit tel quel -->

b) La variable C est de type caractère et contient la valeur '[?]'. Les expressions suivantes sont-elles correctes. Si oui, donnez-leur type et leur valeur.

- `CHR(ord(C) – 1)+ "e"`
- `ORD(C) + 2.5`
- `CHR( ORD( C )-32)`
- `CHR(ORD( C ))`

<!-- TODO vérifier: la valeur de C est « é » dans l'extraction (paragraphe à accents corrompus) ; probablement « e » -->

c) Si N est une variable entière et X une variable réelle, quelles sont les affectations possibles :

- `X = N`
- `N = X+1`
- `N = int(x)+1`
- `X = int(X)+1.5`
- `N = round (X)+1.5`
- `N = round (X+1.5)`

d) Pour chaque opération de lecture ou d'écriture, mettre V si l'opération est possible et F dans le cas contraire.

- `Lire(A)`
- `Lire("A")`
- `Ecrire("A = ",A)`
- `Ecrire(5 mod 7 div 2)`
- `Lire (45)`
- `Lire("A = ",A)`
- `Ecrire(A," ",B)`
- `Ecrire("Saisir un réel")`
- `Lire(A+B)`
- `Ecrire(X + 2*Y)`
- `Ecrire(A)`
- `Ecrire(45)`

<!-- grille de réponse supprimée -->

### Exercice 2

Ecrire un algorithme puis la traduction python d'un programme intitulé Sortie_inverse, qui saisit trois nombres dans un ordre donné et les affiche dans l'ordre opposé à l'entrée.

### Exercice 3

Ecrire un programme qui demande à l'utilisateur les valeurs de 2 entiers x,y, qui permute leurs valeurs et qui les affiches. Modifier ce programme pour qu'il avoir permuté 3 entiers x, y et z

### Exercice 4

Ecrire un programme qui demande à l'utilisateur les coordonnées de 2 points distincts du plan et qui affiche les coordonnées du point milieu.

### Exercice 5

Ecrire un programme qui demande un nombre à l'utilisateur, puis qui calcule et affiche le carré de ce nombre.

### Exercice 6

Ecrire un algorithme et un programme python que permet de saisir un réel, calculer et afficher son arrondi et le carré de sa partie entière et le cosinus de son carré.

### Exercice 7

Ecrire un programme python que permet de saisir un caractère C, afficher son code ASCII puis saisir un entier X, afficher le caractère dont le code ASCII est X puis afficher son successeur et son prédécesseur.

### Exercice 8

Ecrire un programme python qui permet de saisir une chaîne de caractères CH puis afficher le code ASCII de son premier caractère et le code ASCII de son dernier caractère puis effacer son caractère milieu.

### Exercice 9

En se proposant de calculer l'allongement L d'un ressort de raideur K au quel est accrocher par une masse M.

Sachant que M*G=K*L et G=9,8.

Ecrire l'algorithme d'un programme qui permet de calculer l'allongement ?

Traduire la solution en Python et l'exécuter pour M=150 et K=10 ?

### Exercice 10

Ecrire un programme python permettant de saisir le nom et prénom d'un élève et 3 matières de base leurs moyennes et leurs coefficients. Puis de calculer et d'afficher la moyenne arithmétique prévoir des messages et des formats d'affichage.

### Exercice 11

Ecrire un programme qui demande à l'utilisateur la valeur d'une durée exprimée en secondes et qui affiche sa correspondance en heures minutes secondes.

Exemple : 3800 s → 1 heure 3 minutes 20 secondes.

### Exercice 12

Ecrire un programme qui lit le prix HT d'un article, le nombre d'articles et le taux de TVA, et qui fournit le prix total TTC Correspondant.

Faire en sorte que des libellés apparaissent clairement.

### Exercice 13

Ecrire l'algorithme et le programme python de l'application « Substitution » qui permet de lire 3 entiers positifs A,B et n , de remplacer les n derniers chiffres de A par les n premiers chiffres de B et d'afficher le résultat C.

Exemple :

- A= 1000
- B= 1987
- n= 3 → C = 1198.
- n=2 → C = 1019
- n= 1 → C= 1001

### Exercice 14

Etablir l'algorithme et le python du programme INSERTION qui pour deux entier N1 et N2 (N1 formé de trois chiffres et N2 formé de deux chiffres) insère N2 dans N1 comme suit : le premier chiffre de N2 sera entre le premier et le deuxième chiffre de N1 et le deuxième chiffre de N2 sera entre le deuxième et le troisième chiffre de N1.

Exemple : si N1=125 et N2=87 alors le résultat sera 18275

### Exercice 15

Ecrire l'algorithme et le python du programme SOMME_CARRE qui calcule puis affiche la somme des carrés des chiffres d'un entier N formé de trois chiffres.

Exemple : si N= 123, le résultat sera égal à 1²+2²+3² = 14

### Exercice 16

Ecrire un algorithme et sa traduction en Python intitulé Permutation qui permet la lecture d'un entier A composé de trois chiffres, puis afficher la valeur de B telle que :

- Le 1er chiffre de B est le 3ème chiffre de A
- Le 2ème chiffre de B est le 1er chiffre de A
- Le 3ème chiffre de B est le 2ème chiffre de A

Exemple : Si on donne A=598 alors la valeur de B sera 859

### Exercice 17

Ecrire un programme Python CONVERT qui convertit une distance mesurée en Km, en sa mesure équivalente en milles marins.

(1 mille marins = 1.852 Km)

### Exercice 18

Ecrire un algorithme puis la traduction python d'un programme intitulé Cylindre, qui calcule et affiche le volume d'un cylindre après saisie son rayon R et sa hauteur H

Sachant que V = π * R²*H

### Exercice 19

Ecrire un algorithme puis la traduction python d'un programme intitulé Surface_rectangle, qui calcule la surface d'un rectangle de dimensions données et affiche le résultat sous la forme suivante : « La surface du rectangle dont la longueur ..... M et la largeur ...... m, a une surface égale à .... Mètres carrés »

### Exercice 20

Ecrire un algorithme puis la traduction python d'un programme intitulé Piscine, qui lit les dimensions d'une piscine, et affiche son volume et la quantité d'eau nécessaire pour la remplir.

Sachant que le volume = longueur*largeur* profondeur moyenne

Et profondeur moyenne= (profondeur maxi+ profondeur mini)/2
