---
niveau: 3eme
chapitre: 3
titre: Série N° 1 : Les algorithmes arithmétiques
type: serie
notions: nombre parfait, PPCM, nombres amis, nombres frères, facteurs premiers, nombres jumeaux, nombre super premier, nombre heureux, divisibilité par 11, nombre Harshad, combinaisons, divisibilité par 7, nombre valable, divisibilité par 9, division égyptienne, nombre semi-premier
source: Classroom — Série N°1 - les algorithmes arithmétiques
---

# Série N° 1 : Les algorithmes arithmétiques

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans certains mots (« Sé rié », « arithmé tiqués ») ; accents rétablis d'après le rendu à l'écran. Le PDF compte 4 pages, toutes lues -->

## Série d'exercices

### Exercice 1

Un nombre parfait est un entier positif caractérisé par le fait qu'il est égal à la somme de tous ses diviseurs sauf lui-même. Le premier nombre parfait est 6 égal à 1 + 2 + 3 qui sont les diviseurs de 6.

1. Ecrire un algorithme PARFAIT, qui lit un entier et vérifie s'il est parfait ou non.
2. Modifier cet algorithme pour qu'il détermine et affiche tous les nombres parfaits inférieurs à 200.

### Exercice 2

Ecrire un programme qui permet de calculer et d'afficher le PPCM de trois entiers positifs

1. décomposer ce problème en module et déduire l'algorithme des modules proposés.
2. traduisez la solution en un programme python.

### Exercice 3

220 et 284 sont deux nombres amis. En effet :

- D284 = {1, 2, 4, 71, 142, 284}
- D220 = {1, 2, 4, 5, 10, 11, 20, 22, 44, 55, 110, 220}

D284 et D220 sont respectivement les ensembles de tous les diviseurs de 284 et de 220.

- 284 = 1+2+4+5+10+11+20+22+44+55+110.
- 220 = 1+2+4+71+142.

Ecrire un programme python qui permet de déterminer puis d'afficher si deux entiers naturels donnés M et N sont amis ou non.

<!-- TODO vérifier: dans le PDF, les sommes sont inversées par rapport aux diviseurs (284 = 1+2+4+5+10+11+20+22+44+55+110 correspond aux diviseurs de 220, et 220 = 1+2+4+71+142 à ceux de 284) ; et la liste D284 contient 284 alors que la somme l'exclut ; transcrit tel quel -->

### Exercice 4

Deux entiers N1 et N2 sont dits frères si chaque chiffre de N1 apparaît au moins une fois dans N2 et inversement.

Ecrire une fonction python qui vérifie si deux entiers N1 et N2 sont frères ou non.

Exemples :

- Si N1 = 1164 et N2 = 614 -> N1 et N2 sont frères
- Si N1 = 905 et N2 = 9059 -> N1 et N2 sont frères
- Si N1 = 405 et N2 = 554 -> N1 et N2 ne sont pas frères

### Exercice 5

Ecrire un algorithme et un programme python permettant de décomposer un nombre N de type entier en ses produits de facteurs premiers.

### Exercice 6

Écrire un programme intitulé jumeaux qui permet de déterminer et d'afficher tous les entiers jumeaux compris entre 1 et N (N est un entier supérieur ou égal à 2)

Deux nombres A et B sont dits jumeaux si A et B sont premiers et A=B+2

Exemple : 5 et 3 sont des jumeaux : 5 et 3 sont premiers et 5=3+2

### Exercice 7

Un nombre est dit super premier et si en supprimant des chiffres a partir de sa droite, le nombre restant est aussi premier

Exemple :

Le nombre 59399 est super premier car 59399, 5939, 593, 59 et 5 sont tous premiers

Ecrire un programme qui affiche tous les entiers super premier de 1 à n (1000≤n≤32000)

### Exercice 8

Un nombre heureux est un nombre entier qui, lorsqu'on ajoute les carrés de chacun de ses chiffres, puis les carrés des chiffres de ce résultat et ainsi de suite jusqu'à l'obtention d'un nombre à un seul chiffre = 1. (Si le chiffre trouvé comme résultat final est égal à 1 alors le nombre est heureux)

Ainsi, 70 est heureux, puisque :

- 7² + 0² = 49
- 4² + 9² = 97
- 9² + 7² = 130
- 1² + 3² + 0² = 10
- 1² + 0² = 1 (on est arrivé à un nombre d'un seul chiffre = 1, donc 70 est heureux)

Ecrire un programme Entier_Heureux.py qui permet de chercher tous les entiers heureux formés de trois chiffres, les afficher à raison d'un nombre par ligne en mentionnant devant chaque nombre heureux la note "Heureux"

### Exercice 9

Une méthode pour vérifier si un nombre N est divisible par 11 consiste à faire le travail suivant :

Soustraire de N amputé de son chiffre des unités le chiffre supprimé et recommencer éventuellement avec le nombre ainsi obtenu jusqu'au moment où l'on peut conclure à la divisibilité.

Exemple :

N = 12345674

- 1234567 - 4 = 1234563 → 4
- 123456 - 3 = 123453 → 3
- 12345 - 3 = 1234 → 3
- 1234 - 2 = 1232 → 2
- 123 - 2 = 121 → 2
- 12 - 1 = 11 → 1
- 1 - 1 = 0 → 1

Donc 12345674 est divisible par 11 et plus fort, 12345674 : 11 = 1122334

<!-- TODO vérifier: la ligne « 12345 - 3 = 1234 → 3 » du PDF est inexacte (12345 - 3 = 12342) ; transcrit tel quel -->

### Exercice 10

On se propose d'écrire un programme python permettant de déterminer et d'afficher si un entier N saisi (N>11) est divisible par 11 ou non, en appliquant la méthode suivante :

1. On calcule la somme SI des chiffres en position impaire,
2. On calcule la somme SP des chiffres en position paire,
3. On calcule la différence des deux sommes (SI - SP) ou (SP - SI).

N est divisible par 11 si et seulement si la différence (SI - SP) ou (SP - SI) est divisible par 11

Cela revient à effectuer la somme alternée de ses chiffres.

Exemple :

Pour N = 19382 le programme effectuera les opérations suivantes :

- SI = 1 + 3 + 2 = 6
- SP = 9 + 8 = 17
- SP - SI = 17 - 6 = 11

Nous trouvons un résultat divisible par 11, donc 19 382 est divisible par 11.

En effet, 19382 = 11*1762

### Exercice 11

Un nombre HARSHAD est un entier qui est divisible par la somme de ses chiffres.

Exemple : 198 est un nombre HARSHAD car il est divisible par la somme de ses chiffres qui est 18 (18=1+9+8)

Ecrire un programme qui affiche tous les nombres HARSHAD de l'intervalle [n..m] avec (100≤n<m≤999) et dont le prédécesseur de chacun est premier.

Exemple :

Pour n=100 et m=150 :

Le programme affiche les nombres HARSHAD suivants :

- 102 car 102 est un nombre HARSHAD et son prédécesseur 101 est un nombre premier.
- 108 car 108 est un nombre HARSHAD et son prédécesseur 107 est un nombre premier.
- 110 car 110 est un nombre HARSHAD et son prédécesseur 109 est un nombre premier.
- 114 car 114 est un nombre HARSHAD et son prédécesseur 113 est un nombre premier.
- 132 car 132 est un nombre HARSHAD et son prédécesseur 131 est un nombre premier.
- 140 car 140 est un nombre HARSHAD et son prédécesseur 139 est un nombre premier.
- 150 car 150 est un nombre HARSHAD et son prédécesseur 149 est un nombre premier.

### Exercice 12

Ecrire un programme qui permet de calculer et d'afficher le nombre de combinaisons de p objets parmi n.

NB : C(n, p) = n! / (p! (n−p)!), noté dans le PDF avec n en indice et p en exposant de C.

1. décomposer ce problème en module et déduire l'algorithme des modules proposés.
2. traduisez la solution en un programme python.

### Exercice 13

Écrivez un programme permettant de vérifier si un entier n donné est divisible par 7, en utilisant la règle de divisibilité suivante :

Nous nous appuyons sur le fait que si le nombre mcdu est divisible par 7 alors : (mcd-2*u) Est divisible par 7 et réciproquement.

Exemple 7241 :

Nous conservons tous les chiffres sauf le dernier, et nous lui retranchons deux fois le dernier : 724-2*1=277, nous procédons de même avec le résultat, soit 722 : 72-2*2 = 68, or 68 n'est pas divisible par 7, donc 7241 non plus.

<!-- TODO vérifier: dans le PDF, 724-2*1 donne 722 (et non 277) ; transcrit tel quel -->

### Exercice 14

Un entier est dit Valable si son premier chiffre à gauche est suivi par ses multiples.

Exemple : (2888, 3696 et 1541 sont valables)

- n = 2888 → 8 est un multiple de 2
- n = 3696 → 6 et 9 sont des multiples de 3
- n = 1541 → 5, 4 et 1 sont des multiples de 1

Questions :

1. Écrire l'algorithme d'un sous-programme qui permet de vérifier si un entier n donné en paramètre est valable.
2. Écrire un algorithme d'un sous-programme itératif qui permet d'afficher tous les entiers valables formés de quatre chiffres (un entier par ligne). La dernière ligne contient le nombre de ces entiers valables.

Exemple : La dernière ligne : "Le nombre d'entiers valables de quatre chiffres = 1256"

### Exercice 15

(Divisibilité par 9)

On veut déterminer si un nombre est divisible par 9 par la méthode suivante :

- On part du premier chiffre le plus à gauche, on ajoute (addition « + ») le deuxième chiffre (s'il y en a un), si le résultat est supérieur ou égal à 9, on lui soustrait 9 (" -") sinon on ne fait rien.
- On répète ensuite la même opération pour les chiffres suivants. Le nombre est divisible par 9 si et seulement si le résultat final est nul. (La condition d'arrêt est lorsqu'on atteint le dernier chiffre le plus à droite [long (ch)-1])

Écrire l'algorithme d'une fonction booléenne estDivisiblePar9 qui indique si le nombre entier positif passé en paramètre est divisible par 9 en mettant en œuvre la méthode décrite ci-dessus.

La fonction recevra le nombre entier sous la forme d'une chaîne de caractères contenant son écriture décimale.

Exemple :

Pour le nombre 78192 (passé en paramètre à la fonction sous la forme de la chaîne "78192")

La fonction effectuera donc les opérations suivantes :

- 7 + 8 = 15 → 15 est supérieur ou égal à 9 on lui soustrait 9 pour obtenir 6 (6 = 15 - 9)
- 6 + 1 = 7 → 7 est strictement inférieur à 9 (Ne rien faire)
- 7 + 9 = 16 → 16 est supérieur ou égal à 9 on lui soustrait 9 pour obtenir 7 (7 = 16 – 9)
- 7 + 2 = 9 → 9 est supérieur ou égal à 9 on lui soustrait 9 pour obtenir 0 (0 = 9 – 9)
- Le résultat est nul donc 78192 est divisible par 9 (78192 = 9 x 8688).

### Exercice 16

Les égyptiens utilisaient une technique particulière pour calculer la division euclidienne de deux nombres n et m (0 < m ≤ n). Ils procédaient par duplications du diviseur : celui-ci est écrit sous la forme d'une somme de puissances de 2 (2 ; 2*2 ; 2*2*2 ; 2*2*2*2…)

Exemple : 817 ÷ 45

On cherche à s'approcher du dividende sans le dépasser par duplication successives (si on continuait, on trouverait 32*45 = 1440, nombre qui dépasse le dividende 817).

- 45 → 1 → Comprendre : 1*45=45
- 90 → 2 → Comprendre : 2*45=90
- 180 → 4 → Comprendre : 4*45=180
- 360 → 8 → Comprendre : 8*45=360
- 720 → 16 → Comprendre : 16*45=720
- 1440 → 32 → Comprendre : 32*45=1440 (arrêt)

<!-- TODO vérifier: le PDF présente ces lignes dans un tableau de trois colonnes sans en-têtes (valeur, facteur, « Comprendre : ... ») ; mis en liste faute d'en-têtes ; le mot « Comprendre » est transcrit tel quel -->

Donc 817 = 720 + ? C'est-à-dire 817 = 16*45 + ? et ? = 817-720 = 97

Donc 817 = 16*45+97 Et 97 = 90+7 = 45*2+7

Donc 817 = 16*45+45*2+7= (16+2)*45+7 = 18*45+7

Le programme affiche à la fin : le quotient est égal 18 et le reste est égal 7.

### Exercice 17

(Le nombre semi-premier)

Un nombre N est dit semi-premier lorsqu'il est égal au produit de deux nombres premiers non nécessairement distincts. C'est-à-dire N = k*k avec k est un nombre premier ou N = k*j avec k et j sont deux nombres premiers.

Exemples :

- 6 est un nombre semi-premier car 6 = 2 × 3 avec 2 et 3 sont deux nombres premiers.
- 25 est un nombre semi-premier car 25 = 5 × 5 avec 5 est un nombre premier.
- 831 est un nombre semi-premier car 831= 3 × 277 avec 3 et 277 sont deux nombres premiers
- 8 n'est pas un nombre semi-premier, car 8 = 2 × 4 avec 4 n'est pas un nombre premier.

Travail demandé :

- Ecrire une fonction pour vérifier si un entier naturel N est un nombre premier ou non.
- Ecrire une fonction pour vérifier si un entier naturel N (N > 2) est un nombre semi-premier ou non.
- Ecrire un programme permettant d'afficher tous les nombres semi-premiers compris entre deux bornes p et q saisies avec 3 < p < q < 1000.
