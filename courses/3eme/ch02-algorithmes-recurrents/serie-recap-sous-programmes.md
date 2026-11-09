---
niveau: 3eme
chapitre: 2
titre: Série Récap : Les sous-programmes
type: serie
notions: fonctions et procédures, passage de paramètres par valeur et par adresse, transformation procédure en fonction, fonctions prédéfinies sur les chaînes, chaînes de caractères, tableaux, analyse modulaire, suites
source: Classroom — 3em info - série Récap - les sous programmes (série Récap - les sous programme.pdf)
---

# Série Récap : Les sous-programmes

<!-- TODO vérifier: PDF de 8 pages (« Série Récap – Les sous-programmes », 20 exercices, numérotation d'origine conservée). Dans les algorithmes le PDF mélange « debut / début », « FinSi / Fin_Si / fin_si » et « Pour…Fin Pour / pour…fin_pour » : unifiés ici en « Début », « Fin Si », « Fin Pour ». Les flèches « <-- » et « <- » du PDF sont notées ←. Les cases à cocher sont notées ☐. Les logos / pieds de page TuTo Academy sont supprimés -->

## Série d'exercices

### Exercice 1

Ecrire une fonction intitulée **occurrence** qui permet de donner le nombre d'occurrences d'un caractère C dans une chaine CH.

Écrire une fonction qui permet de compter le nombre d'occurrence d'un mot dans une phrase.

### Exercice 2

Soient les deux algorithmes suivants :

```algorithme
Algorithme Programme_Principal
Début
    Ecrire ("Donner un entier"), lire(x)
    Ecrire ("Donner un deuxième entier"),
    lire(y)
    z ← 0
    Somcar(x, y, z)
    Ecrire (x, y, z)
Fin
```

```algorithme
Procedure Somcar(a, b, c : entier)
Début
    a ← a * a
    b ← b * b
    c ← a + b
Fin
```

1) Trouver les résultats fournis dans les cas suivants :

| | | Valeurs initiales | Valeurs finales |
|---|---|---|---|
| 1er exemple | x | 3 | |
| | y | 4 | |
| | z | 0 | |
| 2ème exemple | x | 5 | |
| | y | 6 | |
| | z | 0 | |

2) Que faut-il ajouter à la procédure **SomCar** pour avoir un résultat correct ?

<!-- grille de réponse supprimée -->

### Exercice 3

Soit la procédure suivante :

```algorithme
PROCEDURE P1(c : caractère ; ch : chaîne ; @ p : entier)
Début
    p ← -1
    i ← -1
    Répéter
        i ← i + 1
        Si (ch[i] = c) alors
            p ← i
        Fin Si
    Jusqu'à ((p ≠ -1) OU (i = long(ch)-1)
Fin
```

<!-- TODO vérifier: la parenthèse de « Jusqu'à ((p ≠ -1) OU (i = long(ch)-1) » est déséquilibrée dans le PDF (transcrit tel quel) -->

T.D.O.L

| Objet | Type / Nature |
|---|---|
| i | entier |

1) Transformer cette procédure en une fonction (qui porte le nom F1) :

<!-- grille de réponse supprimée -->

2) Trouver le résultat retourné par la fonction F1 dans les cas suivants :

- c = "g" et ch = "algorithme" : <!-- grille de réponse supprimée -->
- c = "e" et ch = "exemple" : <!-- grille de réponse supprimée -->
- c = "i" et ch = "section Info" : <!-- grille de réponse supprimée -->

3) En déduire la fonction prédéfinie qui fournit le même résultat ?

<!-- grille de réponse supprimée -->

### Exercice 4

```python
def inconnu (...................;................):
    tr = False
    i = 0
    while((i<len(ch)) and (not tr):
        tr = (ch[i] == c)
        i =i+1
    return ................................
```

<!-- TODO vérifier: la parenthèse de « while((i<len(ch)) and (not tr): » est déséquilibrée dans le PDF ; les pointillés de l'en-tête et du return sont à compléter par l'élève (question 1) -->

1. Compléter les pointillés par les données marquantes.
2. Déterminer le résultat retourné par la fonction pour chacun des cas suivants :
    - inconnu ('algorithme','g') ..........................
    - inconnu ('python','H') ..........................
    - inconnu ('1H5','5') ..........................
3. Donner le rôle de la fonction inconnue
4. Convertir la fonction **inconnu** en une procédure (Algo)
5. Recopier et compléter le tableau suivant sachant que l'appel se fait en utilisant une variable **X** :

| Appel de la fonction inconnu | Appel de la procédure inconnu |
|---|---|
| | |

### Exercice 5

Soit la fonction **INCONNUE** suivante :

```algorithme
Fonction INCONNUE(T : tab ; p1, p2 : entier) : entier
Début
    Si (p1 > p2) alors
        aux ← p1
        p1 ← p2
        p2 ← aux
    Fin Si
    s ← 0
    Pour i de p1 à p2 faire
        s ← s + T[i]
    Fin Pour
    retourner s
Fin
```

N.B. Tab = Tableau de 20 entier

1) Nous proposons le tableau **T** suivant :

| T | -2 | 19 | -8 | 14 | 4 | 5 | -4 | 3 | -8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|

a) Remplir le tableau ci-dessous par la valeur de la variable H obtenue suite à l'exécution de l'instruction d'appel de la fonction **INCONNUE**.

| Instruction d'appel | Valeur de la variable H |
|---|---|
| H ← INCONNUE(T,3,8) | |
| H ← INCONNUE(T,6,2) | |
| H ← INCONNUE(T,4,4) | |

a) Déduire le rôle de la fonction INCONNUE

<!-- grille de réponse supprimée -->

<!-- TODO vérifier: la dernière question est numérotée « a) » comme la précédente dans le PDF -->

### Exercice N° 6

Soit la procédure suivante :

```algorithme
PROCEDURE P1(d, f : entier ; ch : chaîne ; @ ch2 : chaine)
Début
    ch2 ← ""
    Pour i de 0 à long(ch)-1 faire
        Si (non (i € [d..f-1])) alors
            ch2 ← ch2 + ch[i]
        Fin Si
    Fin Pour
Fin
```

<!-- TODO vérifier: le PDF écrit « i € [d..f-1] » (symbole €, probablement ∈ voulu), transcrit tel quel -->

T.D.O.L

| Objet | Type / Nature |
|---|---|
| i | entier |

1) Transformer cette procédure en une fonction (qui porte le nom F1).
2) Trouver le résultat retourné par la fonction F1 dans les cas suivants :
    - d = 4, f = 10 et ch = "algorithme" : <!-- grille de réponse supprimée -->
    - d = 0, f = 8 et ch = "Info en TuTo" : <!-- grille de réponse supprimée -->
3) En déduire la fonction prédéfinie qui fournit le même résultat ?

<!-- grille de réponse supprimée -->

### Exercice N° 7

Soit le script python de la fonction suivante :

```python
def quoi(n):
    a=0
    k=1
    while n!=0:
        if n % 2==0:
            a=a+n%10*k
            k=k*10
        n=n//10
    return a
```

<!-- TODO vérifier: l'indentation du script n'est pas lisible avec certitude sur le PDF (n=n//10 est ici placé dans le while, hors du if ; k=k*10 dans le if) -->

**Questions**

1) Pour chacune des propositions suivantes, répondre par la lettre (V) si elle est juste ou la lettre (F) si elle est fausse.

a) L'appel de la fonction **quoi**, dans le programme principal peut être de la forme :

- ☐ quoi(12346)
- ☐ print (quoi(12346))
- ☐ x= quoi ("12346")

b) Le passage de paramètre utilisé dans la fonction quoi est :

- ☐ par valeur
- ☐ par adresse
- ☐ par valeur et adresse

c) L'objet n déclaré dans l'entête de la fonction **quoi** est :

- ☐ un paramètre effectif
- ☐ un paramètre formel
- ☐ une entrée de la fonction

d) a et k utilisés dans le corps de la fonction **quoi** sont des variables :

- ☐ Visibles uniquement par la fonction **quoi**
- ☐ Visibles par **quoi** et **le programme principal**
- ☐ Visibles uniquement par le **programme principal**

2) Exécuter manuellement quoi(**12346**) en donnant les valeurs successives de **a**, **n** et **k** :

| n | | | | | | |
|---|---|---|---|---|---|---|
| a | | | | | | |
| k | | | | | | |

<!-- grille de réponse supprimée -->

3) Déduire le rôle de cette fonction

<!-- grille de réponse supprimée -->

4) Réécrire la fonction **quoi** en remplaçant la structure itérative à condition d'arrêt par une structure itérative complète

### Exercice N°8

Soit U0 un entier naturel de quatre chiffres. A l'aide de ses quatre chiffres, on compose le plus grand entier et le plus petit entier formés par ces chiffres.

La différence de ces deux nombres donne U1, qui sera soumis au même traitement pour donner U2, etc. Jusqu'à ce que la suite U devienne stationnaire, c'est-à-dire, à un certain terme elle devient constante (ne change plus de valeur).

Soit l'algorithme suivant nommé Suite et permettant de déterminer les termes d'une suite U ayant comme premier terme U0, de les ranger dans un tableau T et de l'afficher (avec Max et Min sont deux modules qui déterminent respectivement le plus grand entier et le plus petit entier formés à partir des chiffres de Ui avec i >0).

```algorithme
Algorithme Exo
Début
    répéter
        lire(U0)
    jusqu'à (U0>=1000) et (U0<=9999)
    i ← 0
    T[0] ← U0
    Répéter
        i ← i+1
        T[i] ← Max(U0) - Min(U0)
        U0 ← T[i]
    jusqu'à (T[i]=T[i-1])
    Afficher(i,T)
fin
```

N.B. Tab = Tableau de 100 entier

<!-- TODO vérifier: dans le PDF l'algorithme est en couleurs : « séquence 1 (vert) » = le premier répéter…jusqu'à (lecture de U0) ; « séquence en violet » = le second Répéter…jusqu'à ; Afficher(i,T) en rouge. Les couleurs ne sont pas reproduites -->

**Travail demandé :** Pour chacune des questions suivantes, cocher la ou les bonnes réponses.

1. Par quel appel peut-on remplacer la séquence 1 (vert) de l'algorithme Suite ?
    - ☐ Saisir (N)
    - ☐ Saisir (U0)
    - ☐ Procédure Saisir(@n : entier)
    - ☐ U0 ← Saisir(N)
2. Quels sont les en-têtes qui correspondent à la déclaration de la procédure Afficher ?
    - ☐ Procédure Afficher(T[i] : entier)
    - ☐ Procédure Afficher(i : entier ; T : Tab)
    - ☐ Procédure Afficher(@T : Tab ; n : entier)
    - ☐ Procédure Afficher(n : entier ; T : Tab)
3. L'en-tête suivant de la fonction Max est erroné : DEF FN Max (X : entier). Quel est l'origine de l'erreur ?
    - ☐ Le mode de passage des paramètres est erroné.
    - ☐ Le nom du paramètre effectif est différent du nom du paramètre formel.
    - ☐ Le type du résultat est manquant.
    - ☐ Le type du paramètre effectif est incompatible avec celui du paramètre formel.
4. Si On veut remplacer la séquence en violet par l'appel d'un module :
    - a. Quelle sera sa nature ?
        - ☐ Une procédure
        - ☐ Une fonction
    - b. Quels seront les paramètres effectifs à utiliser ?
        - ☐ T,i et U0
        - ☐ T[i] et U0
        - ☐ T et U0
        - ☐ T et i
5. Pour U0 égale à 5843, quel sera le résultat de l'affichage de l'algorithme Suite ?
    - ☐ Tableau A :

    | 5843 | 5085 | 7992 | 7173 | 6354 | 3087 | 8352 | 6147 | 6174 |
    |---|---|---|---|---|---|---|---|---|

    - ☐ Tableau B :

    | 5843 | 5085 | 2970 | 6930 | 5940 | 4950 | 4950 |
    |---|---|---|---|---|---|---|

### Exercice N°9

Ecrire une fonction **Remplace_index(ch,index,car)** qui reçoit en argument :

- **ch** : une chaine de caractère
- **index** : l'indice de caractère à changer
- **car** : le nouveau caractère à mettre à l'indice **index**

*Exemple :*

| ch | Appel | la fonction renvoie |
|---|---|---|
| ch = "informatique" | Remplace_index(ch,0,"2") | "2nformatique" |
| ch = "Ali" | Remplace_index(ch,5,"a") | "Alia" |
| ch = "python" | Remplace_index(ch,4,"a") | "pythan" |

### Exercice N°10

On appelle **Poids d'un mot** la somme des produits de la position de chaque voyelle contenue dans le mot par son rang dans l'alphabet français. Une lettre a le même rang qu'elle écrite en majuscule ou en minuscule.

**Exemple :** le mot « **Epreuve** » a pour poids 165 car (1\*5) +(4\*5) +(5\*21) +(7\*5) =165.

Ecrire une fonction « **Poids(ch)** » qui calcul le poids d'un mot.

### Exercice N°11

**220** et **284** sont deux nombres amis. En effet :

- **D284** = {1,2,4,71,142,284}
- **D220** = {1,2,4,5,10,11,20,22,44,55,110,220}

**D284** et **D220** sont respectivement les ensembles de tous les diviseurs de 284 et de 220.

- **284** = 1+2+4+5+10+11+20+22+44+55+110.
- **220** = 1+2+4+71+142.

Ecrire un programme python qui permet de déterminer puis d'afficher si deux entiers positifs donnés M et N sont amis ou non.

<!-- TODO vérifier: les deux égalités « 284 = 1+2+4+5+10+11+20+22+44+55+110 » et « 220 = 1+2+4+71+142 » sont inversées dans le PDF (les diviseurs de 220 somment à 284 et inversement) ; transcrit tel quel -->

### Exercice N°12

Ecrire un programme qui permet de saisir un entier n (n>0), puis de vérifier et d'afficher si cet entier est distinct ou non.

**NB :** Un nombre est dit distinct s'il est composé par des chiffres différents.

### Exercice N°13

Deux entiers **N1** et **N2** sont dits **frères** si chaque chiffre de N1 apparaît au moins une fois dans N2 et inversement.

Ecrire une fonction Python qui vérifie si deux entiers N1 et N2 sont frères ou non.

**Exemples :**

- Si N1 = 1164 et N2 = 614 -> N1 et N2 sont frères
- Si N1 = 905 et N2 = 9059 -> N1 et N2 sont frères
- Si N1 = 405 et N2 = 554 -> N1 et N2 ne sont pas frères

### Exercice N°14

On veut écrire un programme permettant de lire deux mots ch1 et ch2 et d'afficher tous les caractères qui apparaissent dans les deux chaînes sans redondance. Décomposer le problème en module.

**Exemple :** Soit ch1= "**Bonjour**" et ch2="**Bonbon**". Résultat : **B, O, N**.

### Exercice N°15

Faire l'analyse modulaire d'un programme qui permet de :

- Saisir la taille N (2 ≤ N ≤ 50) d'un tableau T de chaînes de caractères ;
- Remplir le tableau T par N mots composés au maximum de 10 caractères.
- Remplir un deuxième tableau V par des entiers qui correspondent aux nombres de caractères non alphabétiques dans chaque mot.
- Calculer et afficher le nombre total de caractères non alphabétiques.

### Exercice N°16

On désire écrire l'application **tab_chaine** qui permet de remplir un tableau **T** par **N** chaînes de caractères avec **(5<=N<=50),** sachant que la taille des chaînes de caractères ne doit pas dépasser les 10 caractères, puis remplir un deuxième tableau **TR** par les mêmes chaînes renversées et enfin afficher **T** et **TR**.

*Exemple :*

| T | analyse | année | info | devoir | elle |
|---|---|---|---|---|---|
| TR | esylana | eénna | ofni | rioved | elle |

### Exercice N°17

Un message textuel est une phrase qui contient un ensemble de caractères pouvant être des alphabets, des numéros ou des symboles. Lors de l'envoi d'un message à travers un réseau de télécommunication, il sera converti à sa forme numérique (signal numérique).

Un signal numérique est une chaîne de caractères formée que par des « 0 » et des « 1 ».

Le signal numérique relatif à un message textuel sera trouvé de la manière suivante :

![image décorative : chiffres 0 et 1 verts sur fond sombre (signal numérique)](figures/recap-sp-ex17-signal.png)
<!-- TODO figure: à recréer -->

- Chaque caractère alphabétique majuscule sera remplacé par « 10 ».
- Chaque caractère alphabétique minuscule sera remplacé par « 01 ».
- Chaque caractère numérique sera remplacé par « 11 ».
- Chaque symbole sera remplacé par « 00 ».

Le poids du message sera calculé en additionnant le nombre de « 1 » multiplié par 2 avec le nombre de « 0 ».

**Exemple :** Message textuel : "Elle a 2 Filles et 1 garçon."

- Signal numérique : "1001010100010011001001010101010001010011000101010001010100"
- Poids du signal : 22 \* 2 + 34 = 78

<!-- TODO vérifier: le signal numérique « 1001010100010011001001010101010001010011000101010001010100 » est recopié depuis une capture à résolution moyenne ; à comparer au PDF -->

**Travail demandé :**

On veut écrire un algorithme nommé « **Message** » qui permet de saisir un message textuel non vide et de taille inférieure à 50 caractères, trouver puis afficher le signal numérique et son poids.

- a. Décomposer le problème en modules, et déduire l'algorithme principal + T.D.O.G
- b. Ecrire l'algorithme de chaque module envisagé + T.D.O.L

### Exercice N°18

Ecrire un algorithme qui permet de remplir un tableau **T** par **N** chaines de caractères non vides (avec 2≤**N**≤20) puis remplir un tableau **TPoids** par le poids de chaque chaine de caractères contenu dans le tableau **T**.

**NB :** Le poids d'une chaine de caractères est égal à la somme des codes ASCII des caractères qui la forment.

Afficher le tableau TPoids et la chaine de caractère ayant le plus grand poids.

*Exemple :*

| T | "php" | "Tic" | "info" | "math" | "mcth" |
|---|---|---|---|---|---|
| TPoids | 328 | 288 | 428 | 426 | 428 |

Le programme affiche :

> TPoids[0]=328
> TPoids[1]=288
> TPoids[2]=428
> TPoids[3]=426
> TPoids[4]=428
> Les chaines ayant le plus grand poids sont :
> **info**
> **mcth**

### Exercice N°19

Dans le but de sécuriser les messages envoyés, on désire les **crypter** en suivant cette démarche :

- Remplir un tableau **T** par n (1≤**n**≤10) *messages* composés au minimum de 3 caractères et commençant obligatoirement par une lettre alphabétique majuscule.
- Construire un tableau **TC** qui contient les messages cryptés en remplaçant chaque lettre de message à crypter par celle obtenu en ajoutant une clé de cryptage (la clé **clc** est un entier donné par l'utilisateur et elle est strictement positif) à son code **ASCII** correspondant.
- Afficher le tableau **TC** contenant les messages cryptés.

*Exemple :*

| T | "Concours" | "Help" | "Info" |
|---|---|---|---|
| TC (pour clc=1) | "Dpodpvst" | "Ifmq" | "Jogp" |

Le programme affiche : les messages cryptées sont :

> Dpodpvst
> Ifmq
> Jogp

### Exercice N°20

On désire savoir si un nombre contenant un grand nombre de chiffres est divisible par 7 ou non.

On applique la méthode suivante :

On découpe le nombre par tranche de 2 chiffres en commençant par la droite et chercher les restes de la division de chaque tranche par 7.

**Exemple :** Si une case contient « **abs55df2757dd9818992** », Nb_dec = **5527579818992**, et il est **divisible par 7** car :

![schéma du calcul : 5 | 52 | 75 | 79 | 81 | 89 | 92 découpé en tranches de 2 chiffres depuis la droite, restes de la division par 7 : 5 3 5 2 4 5 1 ; le nombre obtenu est 5352451 ; on recommence : 5 | 35 | 24 | 51 donne 5 0 3 2, le nombre obtenu est 5032 ; 50 | 32 donne 1 4, le nombre obtenu est 14 (tranche de 2 chiffres)](figures/recap-sp-ex20-schema.png)
<!-- TODO figure: à recréer -->

**14** est divisible par 7 donc le nombre **5527579818992** est divisible par 7.

**NB1 :** On s'arrête quand la dernière tranche obtenue est composée de 2 chiffres

**Travail demandé**

Ecrire un algorithme modulaire qui permet de :

1. Remplir le tableau T par N chaînes (5 ≤ N < 60) chacune de longueur minimale 30 et maximale 50.
2. Remplir à partir du tableau T, un tableau D compotera le nombre décimal.
3. Remplir à partir du tableau D, un tableau V comportera le message « **divisible par 7** » ou le message « **non divisible par 7** »
4. Afficher chaque valeur de D et la mention du tableau V

**NB2 :** Si une chaîne du tableau T ne contient pas des caractères chiffres dans ce cas pas de nombre à traiter

*Exemple :* pour N = 5 :

| T | "abs55df2757dd9818992" | "#Bac-Info" | "Bac2024" | "Info2022-23" | "St1245B3" |
|---|---|---|---|---|---|
| D | "5527579818992" | "" | "2024" | "202223" | "12453" |
| V | "divisible par 7" | "" | "non divisible par 7" | "divisible par 7" | "divisible par 7" |

Le programme affiche :

> 5527579818992 est divisible par 7
> 2024 est non divisible par 7
> 202223 est divisible par 7
> 12453 est divisible par 7

<!-- TODO vérifier: les indices 0 à 4 sont indiqués sous les lignes T, D, V dans le PDF (non reproduits) ; l'exemple dit N = 5 mais ne précise pas que « abs55df… » (20 caractères) est plus court que la longueur minimale 30 de la question 1 -->
