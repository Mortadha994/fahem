---
niveau: 2eme
chapitre: 1
titre: Série N° 1 : Les structures de données
type: serie
notions: expressions logiques, opérateurs div et mod, fonctions prédéfinies, chaînes de caractères, conversion des types
source: Classroom — Série N° 1 - Les structures de données
---

# Série N° 1 : Les structures de données

<!-- TODO vérifier: la couche texte du PDF remplace « e » par « é » dans plusieurs paragraphes (« lés différéntés valéurs ») ; accents rétablis d'après le rendu à l'écran (contrôlé sur les exercices 3 et 5), les autres paragraphes corrigés par déduction -->

## Série d'exercices

### Exercice 1

Pour chacun des cas suivants évaluée les expressions logiques suivantes :

- i. `(a<b) ET (c>d)`
- ii. `NON (a<b) ET (c>d)`
- iii. `(a>b) OU (c≠a)`
- iv. `(a+b<c) OU (a+d>c)`

1. Pour (a,b,c,d)=(-1,3,2,7)
2. Pour (a,b,c,d)=(1,3,2,7)
3. Pour (a,b,c,d)=(3,11,7,2)

### Exercice 2

Compléter le tableau suivant :

```algorithme
X1 ← 10 MOD 5
X2 ← 10 DIV 13
X3 ← (5>= 2)
X4 ← (9 MOD 4 = 1)
X5 ← Ent (4.235)
X6 ← arrondi (15.49)
X7 ← CHR (ORD ("A") + 4)
X8 ← "chat"<"CHAMEAU"
X9 ← "100"+"27"
X10 ← ORD (CHR(127))
```

<!-- grille de réponse supprimée -->

### Exercice 3

Pour les différentes valeurs du couple (x,y), mettre dans la case correspondante V si l'expression est vrai et F si l'expression est fausse.

Couples (X, Y) : (1, 5) ; (-1, 0) ; (-5, -3) ; (1, 1)

- `((X<Y) ou (X<=2)) et (X>=0)`
- `(X<Y) ou ((X<=2) et (X>=0))`

<!-- grille de réponse supprimée -->

### Exercice 4

Evaluer les expressions suivantes (avec détails)

```algorithme
E1 ← (10 DIV 3) MOD 2 – 8 + (6 + 7 MOD 3 * 2) DIV 2 + 5
E2 ← (racineCarré (16) = 3) OU (3 > 0) ET (ARRONDI (4.4) < 3)
E3 ← NON ((CHR(ORD('B') -1) = "A") ET (ORD ("A") = 97))
```

### Exercice 5

Soient les entiers w, x, y et z : `w = 2`, `x = 7`, `y = -6`, `z = 3`

Soit les deux chaînes de caractères CH1, CH2 :

```algorithme
CH1 ← 'harrathi'
CH2 ← 'rhimi'
Ch3 ← 'examen'
```

Evaluer les expressions suivantes :

- `sqrt(w-x+z*z)*(x Div w+1)`
- `w + (x % z * y / 3) + abs ( y – z)`
- `round (1.5* (w + (x % z * y / 3) + abs ( y – z)))/2`
- `((y>0) and (y=w*(-z) )) or (sqrt(w+x)=3)`
- `( len (CH2+ CH1)) = w+x +y) OR ( ch3[3:7]='men')`

<!-- TODO vérifier: l'original écrit « CH1:= », « CH2:= », « Ch3:= » (converti en ← selon la règle des affectations) ; expressions mêlant syntaxe algorithme et Python ; parenthèses non équilibrées dans la dernière expression ; 'men' déduit de « mén » (accents corrompus dans la couche texte) -->

<!-- grille de réponse supprimée -->

### Exercice 6

On se propose d'écrire les instructions permettant de réaliser les actions suivantes :

- Lire deux mots mot1 et mot2.
- Afficher la longueur du mot1.
- Afficher la longueur du mot 2.
- Afficher les deux premiers caractères du mot1.
- Insérer la chaîne de caractères 'AB' dans mot2 à la troisième position.
- Afficher mot2 après suppression de deux derniers caractères.
- Afficher le cinquième caractère du mot2.
- Concaténer les deux chaînes de caractères mot1 et mot2 dans mot3.
- Afficher mot3.
- Afficher la première occurrence de la chaîne "CD" dans mot3.

### Exercice 7

a) Écrivez les formules suivantes en python :

- `F ← x⁴ - 3x² + 1`
- `G ← |x³| - sin(x)`
- `X ← Arrondi (Ent(y)-1)`
- `Y ← RacineCarré (Abs ((Sin(x) – 4) * Ent(y)))`

<!-- TODO vérifier: exposants (x⁴, x², x³) perdus dans l'extraction texte et rétablis -->

<!-- grille de réponse supprimée -->

### Exercice 8

Soit la séquence algorithmique suivante :

```algorithme
x ← Chr(Ord("C")-1)
y ← Chr (Ord ("R"))
z ← Majus(Chr(Ord(x)-1))
c ← Chr (Ord ("U"))
w ← Chr(Ord(c)+1)
u ← Chr (Ord (c) - 6)
Ecrire(x , y , z , w, u)
```

<!-- grille de réponse supprimée -->

1. Déclarer les variables utilisées dans la séquence ci-dessus.
2. Exécuter manuellement cet algorithme.
3. Traduire cet algorithme en un programme Python.

### Exercice 9

Soit l'algorithme suivant :

```algorithme
Début
    C1 ← "Les"
    C2 ← "Banques"
    C3 ← "je cherche des documents"
    C4 ← Sous-chaîne (C3 , 0 , 10)
    C3 ← Effacer (C3, 0, Pos ("des" , C3) +3)
    C3 ← C1 + C3
Fin
```

<!-- grille de réponse supprimée -->

1. Donner le résultat de l'exécution des actions ci-dessus.
2. Compléter les actions de cet algorithme en utilisant les chaînes C2, C3 et C4 pour que la chaîne C3 aura la valeur "Les documents que je cherche".
3. Traduire cet algorithme en Python.

### Exercice 10

Soit l'algorithme suivant :

```algorithme
Début
    Ch1 ← "programmation"
    Ch2 ← "cadeau"
    Ch3 ← "nouvelle"
    Ch2 ← Effacer (Ch2, 0, 4)
    Ch3 ← Ch3 + Ch2
    Ch3 ← Effacer (Ch3, 5, 8)
    Ch1 ← Effacer (Ch1, 8, 13)
    S ← Ch3 + " " + Ch1 + "e"
    X ← Pos ("e", S)
    Ecrire ("***", S , "***", X, " Scientifiques***")
Fin
```

<!-- grille de réponse supprimée -->

1. Exécuter manuellement (tournage à la main) cet algorithme ?
2. Traduire cet algorithme en Python.

### Exercice 11

Soit le tableau suivant contenant une suite des instructions d'affectation, compléter les parties manquantes par le code équivalent en python, le résultat en python et le type de résultat.

```algorithme
ch ← "je suis en 2 éme année"
X ← RacineCarré (long(ch))
N ← arrondi(X)
C ← ch[N]
P ← pos("sui",ch)
A ← valeur(ch[11])*2
R ← pos("An",ch)>0
```

<!-- grille de réponse supprimée -->

### Exercice 12

Soit les trois chaînes suivantes : `A="programmation'`, `B= "turbo"`, `C= "langage"`

Compléter le tableau suivant : (Respecter l'ordre des instructions)

```python
D = ord(C[2])
E = 'A' + 'B' + 'C'
F = 'A' + B + 'C'
G = B.upper()
H = str(len(C))
I = A.find('ma')
C = C[:3] + C[5:]
J = chr(120)
K = C.isdigit()
L = A[0:4] == 'Prog'
```

<!-- TODO vérifier: guillemet fermant de A écrit « ' » au lieu de « " » dans l'original ; transcrit tel quel -->

<!-- grille de réponse supprimée -->

### Exercice 13

Soit les variables suivantes : a=9 ; b=12 ; c=1 ; d=2 ; ch = "jeux" ; msg = "game"

Evaluer les expressions logiques suivantes :

1. `not (b>(a-c))`
2. `(a<b) and (c>=d)`
3. `(a!=b) or (c<d)`
4. `not(c>d) and (not(b==a))`
5. `ch>msg`
6. `(len(ch)>a) or (not(len(msg)>c))`
7. `ch[:c]>=ch[:b-a]`

### Exercice 14

Soit le programme suivant :

```python
x = int(input("Saisir un entier de trois chiffres : "))
c = x // 100
d = (x % 100) // 10
u = (x % 100) % 10
s = u*u*u + d*d*d +c*c*c
print ("La somme cubique = ",s)
```

1. Pour x = 125, donner le contenu de chaque variable.

<!-- grille de réponse supprimée -->

2. En déduire le rôle de ce programme.

<!-- grille de réponse supprimée -->

3. Ecrire un algorithme qui effectue le même traitement, mais, en utilisant les fonctions Valeur et Convch.
4. Traduire ce nouvel algorithme en Python et le tester.

### Exercice 15

Donner les valeurs et les types des expressions arithmétiques suivantes.

```algorithme
A ← 20 div(3)/2+3*Arrondi(9.5)-Racine Carré(25) +1
B ← 13 div(3)/Ent(2.25)*Arrondi(11.49)+3*3/3*2
C ← 26+11 mod(3)+Racine Carré(49)/Ent(7.5)-(2*2+Racine Carré(16))/Ent(4.99)
```

<!-- grille de réponse supprimée -->
