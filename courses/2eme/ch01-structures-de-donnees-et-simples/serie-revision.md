---
niveau: 2eme
chapitre: 1
titre: Série de révision Chap 1
type: serie
notions: expressions et opérateurs, chaînes de caractères, fonctions prédéfinies, entrée/sortie, affectation, tableaux, structures conditionnelles
source: Classroom — Série de révision Chap 1
---

# Série de révision N° 1

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes ; accents rétablis par déduction (aperçus à l'écran pour les pages 4, 5, 6, 8, 9, 10, 11, 12) ; mots-clés d'algorithme harmonisés (ALGORITHME/DEBUT/FIN → Algorithme/Début/Fin, « faire », « Fin pour », « Fin si » → Faire, Fin Pour, Fin Si) -->

## Série d'exercices

### Exercice 1

Soient A = 4, B = 6, C = 3 et D = 2.5

Remplir le tableau suivant :

```algorithme
S ← A = B
S ← (A ≤ B) et (D ≠ B)
S ← A + B * C Mod A
S ← A + B / C * 5
S ← ((A+B)*C) + Ord ("A")
```

<!-- grille de réponse supprimée -->

### Exercice 2

Ecrire en Python chacune des expressions suivantes, puis donner la valeur et le type de chaque variable résultat.

1. `A ← Non (10 = 10.5) Ou ((7 ≠ 7) Et Non ((2*2) < 3))`
2. `B ← "BONJoUR" < "BONJOUR Mr"`
3. `C ← (Vrai Ou Faux) Ou Non (Vrai Et Faux Ou Vrai Et Faux)`

<!-- TODO vérifier: « BONJoUR » avec un « o » minuscule dans l'original (aussi visible à l'écran) ; transcrit tel quel -->

<!-- grille de réponse supprimée -->

### Exercice 3

Donner le résultat de chacune des instructions du programme Python suivant :

```python
s1 = "Salut mes collègues"
s2 = "La vie "
s3 = "est "
s4 = "belle"
s5 = s2 + s3 + s4
s6 = s2 * 3
print(s5)
print(s6)
print(len(s1))
print(len(s2))
print(s1.lower())
print(s1.upper())
print(s3.find("u"))
print(s1.find("mes"))
print("?" in s3)
```

<!-- grille de réponse supprimée -->

### Exercice 4

Soit l'algorithme suivant :

```algorithme
Début
    Ch ← "Bac"
    An ← "2024"
    Ph ← "Je calcule pour trouver le résultat"
    P ← Sous_Chaîne (Ph, 0, Long (Ph)-8)
    P ← Effacer (P , Long (P) – 12 , Long (P) – 4)
    P ← Effacer (P , 3 , 11)
    Ecrire (P)
Fin
```

<!-- grille de réponse supprimée -->

1. Donner le résultat de l'exécution des actions ci-dessus.
2. Compléter l'algorithme ci-dessus en utilisant P, An et Ch pour que la chaîne P aura la valeur : "Je prépare pour le Bac 2024".
3. Traduire cet algorithme en Python.

### Exercice 5

1. Ecrire l'algorithme du programme Python ci-dessous.
2. Donner le résultat de chacune des instructions de cet algorithme.

```python
C1="le disque dur, La RAM, la ROM"
C2="win98 et winnt"
C3="le microprocesseur Pentium se trouve sur la carte mère"
C1=C1[15:]
C2=C2[5:9]
X=C3.find("Pentium")
C3=C3[:X-1]+C3[X+7:]
C3=C1+C2+C3
P=C3.find("trouve")+len("trouve")
C3=C3[:P]+"nt"+C3[P:]
C3=C3+"."
print(C3)
```

<!-- TODO vérifier: la chaîne C3 est coupée sur deux lignes dans le PDF (après « se trouve ») ; recollée sur une seule ligne -->

<!-- grille de réponse supprimée -->

### Exercice 6

Ecrire l'algorithme ci-dessous en un programme Python et déduire son rôle.

```algorithme
Début
    C1 ← Chr (65 + Aléa(0,25))
    C2 ← Chr (65 + Aléa (0,25))
    C3 ← Chr (65 + Aléa (0,25))
    Ecrire ("Avant traitement :", C1, C2, C3)
    A ← Ord (C1)
    B ← Ord (C2)
    C ← Ord (C3)
    A ← A + B + C
    B ← A – B – C
    C ← A – B – C
    A ← A – B – C
    C1 ← Chr (A)
    C2 ← Chr (B)
    C3 ← Chr (C)
    Ecrire ("Après traitement :", C1, C2, C3)
Fin
```

<!-- grille de réponse supprimée -->

### Exercice 7

Un élève veut créer un programme pour aider ses camarades à calculer leur IMC (indice de masse corporelle)

Sachant que : IMC = Poids / Taille²

Exemple :

Nadine pèse 56 Kg et mesure 1,65cm

Le programme affiche :

> Votre IMC = 20.56

<!-- TODO vérifier: « Taille² » (exposant perdu dans l'extraction texte, rétabli) ; « 1,65cm » écrit ainsi dans l'original (probablement 1,65 m) -->

### Exercice 8

Compléter le tableau suivant :

- Déclarer une constante de valeur "2Info".
- Un entier aléatoire dans l'intervalle [-8,100].
- Afficher la taille d'une chaîne ch.
- Saisir le contenu d'un réel x.
- Insérer la chaîne ch2 au milieu de la chaîne ch1.
- Convertir une chaîne ch en majuscule.
- Convertir la chaîne CH contenant "1254" en entier.
- Arrondir la valeur 12.36 dans une variable Y.
- Modifier le troisième caractère d'une chaîne ch par le caractère "m".
- Retourner un caractère C aléatoire, C est une lettre majuscule.
- Supprimer les deux derniers caractères d'une chaîne S.
- Afficher le caractère correspondant au code ASCII 150.
- Afficher la partie entière de la racine carré de 12 à la puissance 5.

<!-- grille de réponse supprimée -->

### Exercice 9

Soit l'algorithme suivant :

```algorithme
Algorithme exercice_1
Début
    A ← 10.6
    B ← "A"
    C ← 65+2*4DIV3
    D ← (-3+5<10)ET(2<10)
    E ← NON(B<"B")OU(CHR(C)> "C")
    F ← Arrondi(A)>Ent(A)
    G ← Chr(aléa(65,90)) Dans ["A".."Z"]
    Ecrire(A, "-" , B , "-" , C , "-" , D , "-" , E , "-" , F , "-" , G)
Fin
```

1. Après l'exécution de l'algorithme, donne la valeur et le type de chaque variable.

<!-- grille de réponse supprimée -->

2. Donne la démarche suivie pour chaque valeur trouvée.

<!-- grille de réponse supprimée -->

3. Qu'affiche-t-il cet algorithme à l'écran.

<!-- grille de réponse supprimée -->

### Exercice 10

Complète les codes python suivants :

- Afficher la somme de deux entiers x et y :

```python
x = ........(input("donner le premier entier : " ))
y = ........(input("donner le deuxième entier : " ))
p = ......+......
print("la somme est ", ......)
```

- Afficher la racine carrée d'un réel :

```python
from .................. import *
x=float(input("donner un réel: "))
if ..............:
    r=................
    print("la racine carrée est ", r)
else :
    print("svp donnez un réel positif")
```

- Afficher le minimum de deux réels a et b :

```python
a = ..........(input("donner le premier réel : " ))
b = ..........(input("donner le deuxième réel : " ))
if ............... :
    print(a)
else :
    print(.........)
```

### Exercice 11

1. Complète par ce qui convient.

```python
ch = "devoir de synthèse n°1 en informatique"
p = ch.find("n")
```

Après exécution p = .....

find() est une méthode (fonction) qui permet de retrouver la ................... d'une sous-chaîne dans une chaîne de caractères.

2. En utilisant la méthode find(), écris un code python qui permet de :
   - demander à l'utilisateur d'entrer une chaîne de caractères ch.
   - Demander à l'utilisateur d'entrer un caractère c.
   - Rechercher et afficher la position de la première occurrence de c dans ch.

Code python

<!-- grille de réponse supprimée -->

### Exercice 12

Tarek souhaite résoudre une liste d'équations de 1er degré pour cela il décide d'écrire un programme qui lui demande la valeur de a et celle de b, affiche l'équation puis la solution.

Exemple :

a = 2, b=4

Le programme affiche :

> L'équation est : 2x + 4 = 0
> x = -2

### Exercice 13

Ali veut calculer sa moyenne annuelle et la moyenne de ces camarades pour cela il écrit un programme qui demande à son exécution la moyenne des trois trimestres de l'élève puis le programme affiche la moyenne générale de l'élève.

Sachant que :

La moyenne générale = (moyenne tri1 + moyenne tri2 * 2 + moyenne tri3 *2)/5

Exemple :

- Moyenne trimestre 1 = 11,5
- Moyenne trimestre 2 = 12,7
- Moyenne trimestre 3 = 11,75

Le programme affiche :

> Moyenne générale = 12,08

### Exercice 14

Ecrire un programme Python qui permet de lire un entier positif N formé de 3 chiffres et insère le chiffre zéro (0) entre les chiffres de l'entier N.

Exemple : N=125 → Le résultat est N=10205

### Exercice 15

Ecrire un programme Python qui permet de lire une adresse Email de la forme Nom.Prénom@Serveur.Suffixe (Ex : BenAmmar.Tarek@TuToAcademy.tn) puis afficher le nom, le prénom, le serveur et le suffixe.

### Exercice 16

Soit le programme python suivant :

```python
N=int(input("Donner un entier de deux chiffres: "))
D=N // 10
U=N % 10
P=U*10 + D
print("Le resultat = ",P)
```

<!-- TODO figure: dans le PDF ce code est une capture d'écran d'un éditeur (lignes numérotées 1 à 5) ; transcrit ci-dessus d'après l'image, à vérifier et à recréer -->

1. Donner l'affichage final du programme lorsque N=23 :

<!-- grille de réponse supprimée -->

2. Donner le rôle de ce programme :

<!-- grille de réponse supprimée -->

### Exercice 17

Pour des raisons de sécurité et de confidentialité les administrateurs du site éducatif du lycée proposent de générer pour chaque élève son mot de passe.

Ecrire l'algorithme du programme MOT_DE_PASSE qui permet de :

1. Lire le nom, le prénom et l'âge de l'élève
2. Former un mot de passe composé du nombre de caractères de nom suivi par la première lettre du prénom et l'âge multiplié par deux
3. Afficher le mot de passe à l'utilisateur

Exemple :

> Donner votre nom : Ben Mahmoud
> Donner votre prénom : Fatma
> Donner votre âge : 17
> Votre mot de passe est : 11F34

### Exercice 18

En appliquant les étapes de résolution d'un problème informatique, écris un algorithme qui permet de :

- Demander à l'utilisateur d'entrer un entier M de trois chiffres.
- Calculer et afficher la somme et le produit des trois chiffres qui composent M.

Exemple : Si M=725 Alors S=7+2+5=14 et P=7*2*5=70.

N.B : Extraire les unités, les dizaines et les centaines en utilisant div et mod.

### Exercice 19

Ecrire l'algorithme d'un programme qui permet de calculer la surface H sachant que les cotes c1 et c2 seront saisis au clavier.

![Figure : un carré clair contenant un carré bleu plus petit ; la cote c2 est indiquée par une double flèche au-dessus, une flèche est tracée sur le côté droit (libellé c1 non lisible)](figures/revision-ex19-surface-h.png)

<!-- TODO figure: à recréer -->

### Exercice 20

Pour Chacune des questions données ci-dessous, mettre dans chaque case, la lettre V si la réponse est correcte, ou la lettre F dans le cas contraire.

Soit le script python :

```python
if round(x) >= 6 :
    k = ent (x)
else :
    k = x+2
```

Quelle sera la valeur de k sachant que x = 6.5 ?

- 5
- 6
- 7
- 8

Soit CH une variable contenant le prénom d'une personne.

Quelle assignation doit-on utiliser pour déterminer au hasard dans une variable C un caractère de ce prénom ?

- `C = randint (1, len (CH))`
- `C = chr (randint (1, len (CH)))`
- `C = CH [randint (1, len (CH))]`
- `C = CH [randint (0, len (CH) - 1)]`

Soit le script python :

```python
ch="Info 2022"
ch2=ch[ :len(ch)-1] + chr(ord(ch[-1])+1)
```

Après exécution du script ci-dessus le contenu de ch2 devient :

- "Info 2021"
- "Info 2022"
- "Info 2023"
- "Info 20223"

La (les) quelle(s) des conditions suivantes retournera True ?

(on donne le code ascii de "A" = 65)

- `"1025".isnumeric()`
- `"17" == "0"+"1"+"7"`
- `"17" != "0"+"1"+"7"`
- `( ord("B") > 67 ) or ( "Z" > "a".upper())`

<!-- grille de réponse supprimée -->

### Exercice 21

Compléter le tableau suivant :

```python
a = (40 // 5 % 3 >=2) and ("A"=="a")
b = (57/3==17) or (4+10% 3<5)
c = (12 // 5 > 32%4) or (68%3+8-6>7)
d = 5 != 7 and "a">"c" or 45%3==1
```

<!-- grille de réponse supprimée -->

### Exercice 22

Soit T et V deux tableaux et soit la séquence algorithmique suivante :

NB : Le code ASCII de 'A' = 65, Le code ASCII de 'T' = 84, Le code ASCII de 'Y' = 89, le code de 'N'=78

```algorithme
CH ← "Nouvel"
T[0] ← CH
CH ← Effacer (CH, 2, len(CH))
T[1] ← CH
T[2] ← CH + "rmal"
T[3] ← Sous_Chaine (T[2], 0, 3)
T[4] ← CHR (84) + CHR (79) + CHR (78) + CHR (89)
V[0] ← ORD (CH[0])
V[1] ← V[0] mod 2 * 5
V[2] ← V[1] div 3 + 8
V[3] ← ORD ("Y")
V[4] ← POS ("a", "bananes") + ORD ("A")
```

<!-- TODO vérifier: les 12 lignes sont numérotées 1) à 12) dans l'original (numéros retirés du bloc) ; flèches (←) absentes de l'extraction texte, rétablies -->

Questions :

1. Compléter les tableaux ci-dessous après exécution des séquences ci-dessus.
2. Déclarer les tableaux T et V.

<!-- grille de réponse supprimée -->

### Exercice 23

Evaluer chacune des propositions suivantes par « vrai » si elle est valide ou « faux » sinon.

- Le contenu d'une variable peut être changé à tout moment dans un programme.
- L'identificateur d'une variable peut contenir des espaces.
- A et a sont deux variables différentes.
- `"Info" [?] chaine` est une affectation correcte.
- Pour saisir une donnée dans l'étape d'algorithme, on utilise l'action lire.
- L'action `print("4ième",sciences)` permet d'afficher le message "4ième sciences"
- Les indices d'une chaine de caractères peuvent être des entiers négatifs.
- Le type float est un type entier.
- `N = 1 - ent(17.8) % 2 + floor(6.5) //10` permet d'affecter à N la valeur 0.
- `C ← chr ( ord ("B") + 32 )` permet d'affecter à C la valeur "b".

<!-- TODO vérifier: « "Info"chaine » dans l'extraction texte, symbole d'affectation perdu entre les deux -->

<!-- grille de réponse supprimée -->

### Exercice 24

Ecrire en python les instructions suivantes :

- Affecter à X la valeur 5.
- Saisir un réel Y.
- Afficher le dernier caractère d'une chaine CH.
- Supprimer les trois derniers caractères d'une chaine CH.
- Afficher un réel R à trois chiffres après la virgule.

<!-- grille de réponse supprimée -->

### Exercice 25 : (application d'opérateurs)

Compléter le tableau suivant :

```algorithme
x ← 15 + 3 * 2 + 5
x ← (18 mod 5) / 2
x ← (3 mod 5) div 2
x ← abs(-12.5)
x ← non("anis" ≥ "Anis")
x ← 1=2
x ← (10 ≠ (9+1)) ou (12 > -1)
```

<!-- grille de réponse supprimée -->

### Exercice 26 : (périmètre et surface d'un disque)

1. Écrire un programme Python qui, à partir de la saisie d'un rayon, calcule et affiche le périmètre d'un cercle.
2. Améliorer votre programme pour qu'il puisse afficher en plus du périmètre, l'aire (surface) du cercle en appliquant la formule suivante :

![Schéma d'un disque (rayon r) avec les indications « π = 3,14 » et « périmètre = 2π × r », et un encadré avec la formule « aire = π × r² »](figures/revision-ex26-disque.png)

<!-- TODO figure: à recréer ; texte de l'image lu sur une capture réduite, à vérifier -->

### Exercice 27

Ecrire un programme qui permet de calculer puis afficher la surface d'un cercle de rayon donné.

### Exercice 28

Rappelons que pour un rectangle :

- Le périmètre = (longueur + largeur) *2
- La surface = longueur * largeur

Donner l'algorithme nommé Rectangle qui permet de :

- Lire la longueur (X) et la largeur (Y) d'un rectangle,
- Calculer le périmètre (P) et la surface (S) du rectangle
- Afficher les valeurs (S) et (P) trouvés

Pour les valeurs X=2 et Y=3, quelles sont les valeurs trouvées de S et P

### Exercice 29

Soient x, y et z des entiers :

1. `(x==y) and (y==z)`
2. `(x==y) or (y==z) or (x==z)`
3. `(x!=y) or (y!=z) or (x!=z)`
4. `((x==y) and (x!=z)) or ((x==z) and (x!=y)) or ((y==z) and (x!=y))`
5. `(x % 2 == 0) or (y % 2 == 0) or (z % 2 == 0)`
6. `((x+y+z) % 2 == 0) and ((x% 2 != 0)or(y% 2 != 0)or(z% 2 != 0))`

| Lettre | Rôle |
|---|---|
| F | Parmi les valeurs de x, y et z deux valeurs et seulement deux sont identiques |
| D | Parmi les valeurs de x, y et z deux valeurs au plus sont identiques |
| E | Parmi les valeurs de x, y et z deux sur trois au plus sont impaires. |
| C | Parmi les valeurs de x, y et z deux valeurs au moins sont identiques |
| B | Les variables x, y et z sont identiques |
| A | Exactement deux sur les trois sont impaires. |

Compléter le tableau suivant en indiquant le rôle de chaque expression :

<!-- grille de réponse supprimée -->

### Exercice 30

Pour les segments de code ci-dessous : Quelle est la valeur finale de la variable b ? Cocher la réponse juste.

Segment 1 :

```python
a=7
b=12
if a>5 :
    b=b-4
if b>=10:
    b=b+1
```

Réponses : 8, 9, 12, 13

Segment 2 :

```python
a=3
b=6
if a>5 or b!=3:
    b=4
else:
    b=2
```

Réponses : 2, 4, 6

Segment 3 :

```python
a=10
b= 20
c=15
if b > a:
    if a > c :
        b=a
    else:
        b=c
else :
    b=a+c
```

Réponses : 25, 15, 10

<!-- grille de réponse supprimée -->

### Exercice 31

Une année bissextile est une année comportant 366 jours au lieu de 365 jours pour une année régulière.

L'année sera bissextile :

- Si elle est divisible par 4 et non divisible par 100, ou
- Si elle est divisible par 400.

Compléter le programme ci-dessous pour afficher si une année est bissextile ou non :

```python
annee = int(input("Entrer l'année à vérifier:"))
if .................................................................................................................................................:
    print("L'année est bissextile!")
else:
    print("L'année n'est pas bissextile!")
```

Compléter le programme ci-dessous pour afficher sans faire du calcul si le produit de deux nombres (a*b) est positif, négatif ou nul :

```python
a= float(input ("donner un nombre : "))
b= float(input ("donner un autre nombre : "))
if ......................................................................................... :
    print("produit positif")
elif .................................................................................. :
    print ("produit négatif")
else :
    print ("produit nul")
```

### Exercice 32 : (Admis / Redouble)

Pour savoir si un élève est admis ou redoublant il faut calculer sa moyenne générale de fin d'année en utilisant la formule suivante :

MG = (MT1 * 1 + MT2 * 2 + MT3 * 2) / 5

Avec : MG : Moyenne Générale, MT1 : Moyenne Trimestre 1, MT2 : Moyenne Trimestre 2, MT3 : Moyenne Trimestre 3

On désire faire un programme Python qui permet d'introduire les moyennes de 3 trimestres pour calculer et afficher la moyenne générale ainsi que la décision adéquate. Sachant que la décision est « admis » si l'élève aura une moyenne ≥ 10 et « redoublant » dans le cas contraire.

### Exercice 33

Un triangle équilatéral est un triangle dont les trois côtés ont la même longueur.

Un triangle isocèle est un triangle qui possède deux côtés de longueurs égales.

Un triangle quelconque est un triangle dont les trois côtés ont des longueurs différentes.

Soit A, B et C trois points de coordonnées respectives x1, y1, x2, y2, x3 et y3.

Ecrire un algorithme d'un programme qui permet de saisir les coordonnées de trois points d'un triangle et afficher :

- « Équilatérale » si le triangle est équilatéral.
- « Isocèle » si le triangle est isocèle.
- « Quelconque » sinon.

Remarque : Pour calculer la distance entre deux sommets d'un triangle on utilise la formule suivante : √((x2-x1)² + (y2-y1)²)

![Triangle ABC tracé dans un repère quadrillé : A à gauche, B en haut, C à droite](figures/revision-ex33-triangle.png)

<!-- TODO figure: à recréer -->

### Exercice 34

Soit l'algorithme suivant :

```algorithme
Algorithme inconnu
Début
    Ecrire ("donner a")
    Lire (a)
    Ecrire ("donner b")
    Lire (b)
    Si b=0 Alors
        R ← 1
    Sinon
        R ← 1
        Pour i de 1 à b Faire
            R ← R * a
        Fin Pour
    Fin Si
    Ecrire (R)
Fin
```

Déterminer la valeur de R à chaque fois :

- a = 2, b = 0
- a = 2, b = 3
- a = 4, b = 2
- a = 5, b = 3

<!-- grille de réponse supprimée -->

En déduire le rôle de cet algorithme.

### Exercice 35

Ecrire l'algorithme d'un programme qui permet de coder une chaîne de caractères CH Saisi au clavier de longueur L. Le procédé du codage consiste à échanger les valeurs du premier et l'avant dernier caractère si sa longueur L > 6 sinon on remplace le dernier caractère par le caractère '*'.

Exemple :

- Si CH = "bonjour" après le codage CH="uonjobr"
- Si CH = "bon" après le codage CH="bo*"

### Exercice 36

Ecrire un algorithme d'un programme qui lit une chaine CH non vide puis vérifie si elle contient une parenthèse ouvrante et une parenthèse fermante.

Dans l'affirmative on affiche trois parties de la chaine (voir exemple) sinon on affiche le message pas de parenthèses.

Exemple : CH="info(2sciences4)python"

Le programme affiche :

> Partie1 :info
> Partie 2 :2siences4
> Partie3 :python

<!-- TODO vérifier: « 2siences4 » (sans « c ») dans l'original, alors que CH contient « 2sciences4 » ; transcrit tel quel -->

### Exercice 37

Compléter le tableau suivant, sachant que le code ASCII de 'a' = 97, 'A'=65 et '0' = 48 :

```python
a = len ("Sciences de l'informatique") % 11 // 3
b = not (155 < 99) and (ord ("D") == 1) or (chr (97) == "c")
ch = "a"
c = ch.upper ( ) < chr (50)
d = ("F" < "B") and (round (1.85) > 0)
ch = "20"
e = ("c" > "C") or (ch.isdigit ())
f = str (32 % 4 + int ("658") // 4)
ch = "1245"
g = int (str (209) + "1") + ch.find ("4")
```

<!-- grille de réponse supprimée -->

### Exercice 38

Soit les affectations suivantes : ch1, ch2, ch3 = "DEVOIR", "PROGRAMMATION ", "PYTHON"

Écrire en Python et en Algorithme les instructions nécessaires pour réaliser les tâches suivantes :

- Déterminer la longueur L de la chaine ch1.
- Obtenir la chaine ch4 = "PROGRAMMATION PYTHON" à partir des chaines ch2 et ch3.
- Obtenir ch5 = "PROGRAM" à partir de la chaine ch2.
- Donner la position du mot "PYTHON" dans la chaine ch4.
- Soit x = 2023. Obtenir la chaine ch6 = "DEVOIR 2023", à partir de la chaine ch1 et l'entier x.
- Donner au hasard une lettre alphabétique majuscule M. sachant que les codes ASCII des lettres majuscule compris entre 65 et 90.

<!-- grille de réponse supprimée -->

### Exercice 39

Cocher la bonne réponse.

**1.**

```python
x = int(input("x= "))
if x<0 :
    A=-x
print( "|" + str(x)+ "| =" + str(A))
```

X=-3 , Le programme affiche :

- |3| =-3
- |-3| =-3
- |-3| =3

**2.**

```python
mot1= input("1er mot:")
mot2= input("2ème mot : ")
if (len(mot1) < len(mot2) ):
    print (mot1)
else:
    print (mot2)
```

1er mot : Tunis, 2ème mot : Tunisie. Le programme affiche :

- Tunis
- mot1
- Tunisie

**3.**

```python
x=int(input("donner un nombre "))
ch=chr(x)
print(ch)
```

X=65, Le programme affiche :

- A
- 65
- ch

**4.**

```python
x=int(input(" donner x "))
if (x %2 == 0) :
    msg="paire"
else :
    msg="impaire"
print(msg)
```

X= 15. Le programme affiche :

- paire
- nul
- impaire

**5.**

```python
x = int(input("x= "))
if( x%3==0):
    print(x, "divisible par 3")
else :
    print(x, "non divisible par 3")
```

X=33. Le programme affiche :

- 33 non divisible par 3
- 33 divisible par 3
- erreur

**6.**

```python
Ch=input("donner une chaine de 4 caractère "))
if(ch[0]==ch[3] and ch[1]==ch[2]):
    print(ch, "est palindrome")
else :
    print(ch, "est non palindrome")
```

Ch= 'RAAR'. Le programme affiche :

- "est palindrome"
- "RAAR est palindrome"
- "RAAR est non palindrome"

**7.**

```python
x = int(input("x= "))
y= int (input("y= "))
if(x>y) and (x%y==1)):
    x=x+3
    y=y-1
else:
    x=x-3
    y=y+4
print('x=',x,'y=',y)
```

X=3 et y= 5. Le programme affiche :

- x=6 y=4
- x=0 y=9
- x=3 y=5

**8.**

```python
ch1= "devoir"
ch2= "sciences"
if (ch1[2]!=ch2[2]) :
    ch1=ch1.upper()
else :
    ch2=ch2.upper()
print(ch1,' ',ch2)
```

Le programme affiche :

- devoir SCIENCES
- devoir sciences
- DEVOIR sciences

**9.**

```python
x=3
y=7
if((x<y)and not(y!=7)):
    print(x+10,y-5)
else :
    print(x-5,y)
```

Le programme affiche :

- 13 2
- 13 7
- -2 7

**10.**

```python
ch="TuTo2023"
if (len(ch) % 2 == 0) :
    msg=ch[0:4]
else :
    msg=ch[4:]
print(msg)
```

Le programme affiche :

- TuTo2023
- 2023
- TuTo

<!-- TODO vérifier: parenthèse fermante en trop (« input(...)) » au 6, « (x%y==1)) » au 7) dans l'original ; transcrit tel quel. Numérotation 1 à 10 reprise des puces ❶ à ❿ du PDF -->

<!-- grille de réponse supprimée -->

### Exercice 40

Pour chacune des propositions suivantes, Quelle est la valeur finale de B, mettre une croix devant le résultat exact :

Script 1 :

```python
A=7
B=12
if (A>5) :
    B=B-4
else :
    B=B+1
```

Script 2 :

```python
A=2
B=5
if (A>8) :
    B=10
else :
    B=3
```

Script 3 :

```python
A=2
B=0
if (A<0) :
    B=1
elif((A>0) and (A<5)) :
    B=2
else :
    B=3
```

<!-- TODO vérifier: aucune proposition de réponse (cases à cocher) dans l'extraction texte de cet exercice ; le bas de la page 12 n'a pas été contrôlé à l'écran -->
