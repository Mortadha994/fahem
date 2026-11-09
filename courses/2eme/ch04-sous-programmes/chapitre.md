---
niveau: 2eme
chapitre: 4
titre: Les sous programmes
type: cours
notions: analyse modulaire, types de modules, fonction, procédure, paramètres formels et effectifs, passage par valeur ou par adresse, variables globales et locales
source: Classroom — Chapitre 4 - Les sous-programmes
---

# Chapitre : Les sous programmes

<!-- TODO vérifier: le PDF (« chap 4 les sous programmes - V Remplie.pdf », 8 pages) écrit les mots-clés de façon variable (FONCTION / Fonction, Fin pour / Fin Pour, Si ... alors / Alors, SI / Si, Fin SI / Fin Si, faire / Faire, Procédure / procédure, Début, Fin) ; harmonisés en Fonction, Procédure, Début, Fin, Retourner, Répéter, Jusqu'à, Pour, Faire, Fin Pour, Si, Alors, Sinon, Fin Si, Lire, Ecrire. L'original termine chaque sous-programme par « Fin » seul (pas « Fin Fonction » / « Fin Procédure ») : conservé tel quel. Le symbole « є » de l'original (appartenance) est écrit ∈ -->

<!-- Le PDF contient du Python dans les exemples et les applications ; rien n'a été ajouté -->

## I. Introductions :

### 1. Définition :

En programmation, il est préférable de décomposer le programme en sous programmes indépendants et de difficultés moindres appelés modules.

Un sous-programme est une **partie** du programme destinée à effectuer une tache précise.

**Exemple :**

- **long**(ch) est destinée à calculer la longueur d'une chaîne.
- **Racine_Carré**(x) calcule la racine carrée de x.
- Pour calculer xʸ, en algorithme, il n'y a pas de fonction prédéfinie puissance (on pourra la programmer).

**Rappels Fonction prédéfinies en algorithme - python :**

- Arrondi(x) – round(ch)
- racinecarre(x) - sqrt(x)
- alèa(vi,vf) - randint(vi,vf)
- ent(x) - int(x)
- Abs(x) – abs(x)
- ord(c), chr(d)
- long(ch) - len(ch)
- pos(ch1,ch2) - ch2.find(ch1)
- convch(x) – str(x)
- estnum(ch) - ch.isdigit()
- valeur(ch) – int(ch) ou float(ch)
- Sous_chaine(ch,d,f) - ch[d:f]
- effacer(ch,d,f) – ch[:d] + ch[f:]
- majus(ch) - ch.upper()

<!-- TODO vérifier: l'original écrit « Arrondi(x) – round(ch) » (round(ch) au lieu de round(x)) ; transcrit tel quel -->

### 2. L'analyse modulaire :

C'est décomposer le problème en des parties appelées modules ou sous programmes.

L'analyse modulaire a plusieurs objectifs tels que :

- Décomposer un problème en des sous-problèmes pour le mieux résoudre, car ce ci réduit le degré de difficulté.
- Eviter les redondances (répétition du même travail).
- Localiser l'erreur facilement.
- Utiliser quelques modules dans plusieurs programmes (réutiliser des parties programmés).
- Etc.

### 3. Les types des modules :

Il existe deux types de sous-programmes :

- Les fonctions qui sont destinées à effectuer des calculs et qui retournent un résultat unique et simple.
- Les procédures qui effectuent tous types de traitement (remplir, saisie, affichage, ...)

## II. Problème d'initiation :

On appelle **p** un point d'équilibre dans un tableau T contenant uniquement des chiffres, lorsque p sépare ce tableau en deux parties ayant la même somme (S1=S2).

Avec **S1** est la somme des éléments indicés de **0** à **p-1** et **S2** est la somme des éléments indicés de **p+1** jusqu'à la fin du tableau T.

**Exemple 1 :** pour **n= 9** et pour le tableau T ci-dessous, l'ordinateur a choisi au Hazard p = 2

| T | 5 | 6 | 4 | 1 | 1 | 3 | 1 | 0 | 5 |
|---|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 (p) | 3 | 4 | 5 | 6 | 7 | 8 |

S1=11 (indices 0 et 1) ; S2=11 (indices 3 à 8) ; p est entouré d'un cercle.

S1=S2 Alors le programme affichera **L'indice 2 est un point d'équilibre**

**Exemple 2 :** pour **n= 12** et pour le tableau T ci-dessous

L'ordinateur a choisi au Hazard p=5

| T | 6 | 1 | 3 | 8 | 2 | 9 | 4 | 1 | 1 | 5 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 | 3 | 4 | 5 (p) | 6 | 7 | 8 | 9 | 10 | 11 |

S1=20 (indices 0 à 4) ; S2=18 (indices 6 à 11) ; p est entouré d'un cercle.

S1 ≠ S2 Alors le programme affichera : **L'indice 5 n'est pas un point d'équilibre**

<!-- TODO vérifier: les deux tableaux sont dessinés avec des accolades sous les indices (S1 à gauche de p, S2 à droite) ; transcrits ici sous forme de tableaux avec une ligne d'indices et une phrase pour S1 et S2 -->

**Travail demandé :** Ecrire un algorithme intitulé « **Equilibre** » et les tableaux de déclaration (T.D.N.T et T.D.O) correspondants au programme qui permet de :

- Saisir un entier n, la taille du tableau T avec (4 ≤ n ≤ 12 )
- Remplir un tableau T par n chiffres. (de 0 à 9)
- L'ordinateur va choisir un entier « **p** », au hasard, compris entre 1 et n-2
- Calculer « S1 » puis « S2 »
- Afficher si l'indice p est un point d'équilibre du tableau T ou non.

```algorithme
Algorithme Equilibre
Début
    Répéter
        Ecrire ("Saisir un entier entre 4 et 12 : ")
        Lire(n)
    Jusqu'à ( n ∈ [4..12] )
    Pour i de 0 à n-1 Faire
        Répéter
            Ecrire("T[", i, "]= ")
            Lire( T[i] )
        Jusqu'à ( 0 ≤ T[i] ≤ 9 )
    Fin Pour
    P ← Aléa (1, n-2)
    S1 ← 0
    Pour i de 0 à p-1 Faire
        S1 ← S1 + T[i]
    Fin Pour
    S2 ← 0
    Pour i de p+1 à n-1 Faire
        S2 ← S2 + T[i]
    Fin Pour
    Si (S1=S2) Alors
        Ecrire ("L'indice", p, " est un point d'équilibre")
    Sinon
        Ecrire ("L'indice", p, " n'est pas un point d'équilibre")
    Fin Si
Fin
```

<!-- TODO vérifier: l'original écrit « P←Aléa (1, n-2) » avec P majuscule puis utilise « p » ; transcrit tel quel -->

Dans le PDF, le programme est découpé par des cadres en pointillés avec ces légendes :

1. Bloc d'instructions pour saisir n (les lignes Répéter ... Jusqu'à ( n ∈ [4..12] )).
2. Bloc d'instructions pour remplir le tableau T par n chiffres (la boucle Pour i de 0 à n-1 ... Fin Pour).
3 et 4. Bloc d'instructions pour calculer la somme S1 puis S2 (les deux boucles Pour de S1 et de S2).
5. Tester et afficher si le tableau est équilibré ou non (le Si ... Fin Si final).

<!-- TODO vérifier: les cadres en pointillés ne sont pas reproduits, seulement leurs légendes -->

**Décomposition du Programme Principal (PP) en modules :**

![Schéma de décomposition du programme principal PP en quatre modules : Saisie, Remplir, Somme, Afficher](figures/decomposition-pp.png)
<!-- TODO figure: à recréer -->

Le PDF présente ensuite, côte à côte, l'algorithme (colonne gauche) et le Python (colonne droite), séparés ici.

**Algorithme :**

```algorithme
{Algorithme du programme principal (PP) }
Algorithme Equilibre
Début
    Saisie(n)          # correspond au 1er Bloc
    Remplir (n, t)     # correspond au 2ème Bloc
    P ← Aléa (1, n-2)
    S1 ← Somme (0, t, p)     # correspond au 3ème Bloc
    S2 ← Somme (p+1, t, n)   # correspond au 4ème Bloc
    Afficher(S1,S2)
Fin

# On commence à développer chaque sous-programme #

{Algorithme de la procédure saisie}
Procédure saisie (@n : entier)
Début
    Répéter
        Ecrire("N=")
        Lire(n)
    Jusqu'à ( n ∈ [3..20])
Fin

{Algorithme de la procédure Remplir}
Procédure remplir (x : entier, @v : tab)
Début
    Pour i de 0 à x-1 Faire
        Répéter
            Ecrire("T[", i, "]="), Lire(v[i])
        Jusqu'à ( v[i] ∈ [0..9])
    Fin Pour
Fin

{Algorithme de la fonction somme }
Fonction somme (x : entier, v : tab, p : entier) : entier
Début
    S ← 0
    Pour i de x à p-1 Faire
        S ← S + V[i]
    Fin Pour
    Retourner S
Fin

Procédure Afficher(x,y : entier)
Début
    Si (x=y) Alors
        Ecrire("L'indice", P, " est un point d'équilibre")
    Sinon
        Ecrire("L'indice", P, " n'est pas un point 'équilibre")
    Fin Si
Fin
```

Une flèche « ( Appel du sous-prog) » du PDF pointe vers les appels Saisie, Remplir, Somme du programme principal.

Tableaux de déclaration des objets locaux (T.D.O.L) indiqués dans le PDF :

| Sous-programme | Objet | Nature / Type |
|---|---|---|
| Procédure remplir | i | entier |
| Fonction somme | i, S | entier |

**Python :**

```python
from numpy import *
from random import*
def saisie():
    global n
    test=False
    while test==False:
        n=int(input('N= '))
        test= (3<=n<=20)
#Remplir T-----------------
def remplir(x,v):
    for i in range(x):
        ok=False
        while ok==False:
            v[i]=int(input('T['+str(i)+']='))
            ok=(0<=v[i]<=9)
# calcul de la somme des éléments de T
def somme (x,v,p):
    s=0
    for i in range(x,p):
        s+=v[i]
    return s
#afficher les éléments de T-------
def afficher(x,y):
    if x==y:
        print('Le tableau est équilibré ')
    else:
        print("Le tableau n'est pas équilibré")
#prog principal------------------
saisie()
t=array([int]*n)
remplir(n,t)
affiche(n,t)
p=randint(1,n-2)
s1=somme(0,t,p)
s2=somme(p+1,t,n)
afficher(s1,s2)
```

<!-- TODO vérifier: incohérences de l'original, transcrites telles quelles : (1) l'énoncé demande 4 ≤ n ≤ 12 mais les sous-programmes saisie testent n ∈ [3..20] ; (2) la procédure Afficher utilise P sans le recevoir en paramètre, et son message contient « point 'équilibre » (d' manquant) ; (3) le Python appelle affiche(n,t) qui n'est pas définie (seule afficher(x,y) existe) ; (4) les messages du Python d'afficher diffèrent de ceux de l'algorithme ; (5) Remplir écrit « Ecrire(...), Lire(v[i]) » sur une seule ligne ; (6) « Aléa » / « alèa » : deux orthographes dans le PDF, laissées telles quelles -->

## III. Les fonctions :

**Activité 1 :** Quelles seront les valeurs des variables **x1**, **ch3**, **ch4** après l'exécution de la séquence d'instructions :

```algorithme
ch1 ← "info"
ch2 ← "informatique"
x1 ← pos (ch1,ch2)
ch3 ← majus (ch1)
ch4 ← sous-chaîne (ch2, 5, 8)
```

Résultat indiqué dans le PDF :

> x1 = 0  
> ch3 = INFO  
> ch4 = mat

**NB :** pos, majus et souschaine sont des fonctions algorithmiques prédéfinies qu'on peut les utiliser facilement pour avoir des résultats bien déterminés.

### 1. Définition :

Une fonction est un sous-programme (une portion de code) que l'on peut appeler au besoin dont elle fournit un **seul résultat** de type **simple**.

L'utilisation des fonctions évite les redondances de code : on obtient ainsi des programmes plus courts et plus lisibles.

**Activité 2 :** Soit la fonction mathématique définie par : f (x) = 2x-2 (soit y=2x-2)

Écrire un algorithme qui permet de saisir un entier « x » non nul et d'afficher sa valeur correspondante « y » en fonction de la fonction f.

```algorithme
Algorithme Act1
Début
    Répéter
        Ecrire ("Donner X : ")
        Lire (x)
    Jusqu'à x ≠ 0
    Y ← F(x)     # appeler la fonction f.
    Ecrire ("F(", x, ")=", Y)     # afficher le résultat de la fonction f
Fin
```

```algorithme
Fonction F(x : entier) : entier
Début
    Retourner 2*x-2
Fin
```

<!-- TODO vérifier: dans le PDF, l'algorithme Act1 est dans un grand cadre et la fonction F dans un petit cadre à sa droite ; séparés ici en deux blocs. L'énoncé définit f(x) = 2x-2 mais la fonction écrite s'appelle F et le programme dit « fonction f » -->

### 📌 2. Déclaration d'une fonction en algorithme et en Python :

```algorithme
Fonction NomF (pf1 : type1, pf2 : type2, ...) : TypeR
Début
    Instructions
    .
    .
    Retourner Valeur
Fin
```

```python
def NomF (pf1, pf2, ...) :
    Instructions
    .
    .
    return Valeur
```

<!-- TODO vérifier: l'original écrit « return :Valeur » (deux-points avant Valeur) ; écrit ici « return Valeur ». Le PDF désigne pf1, pf2, ... par « Paramètres formels » (deux flèches) -->

### 📌 3. Appel d'une fonction en algorithme et en Python :

L'appel d'une fonction, au niveau Algorithme, comme en python, peut se faire de deux méthodes :

```algorithme
Objet ← Nom_fonction (pe1, pe2, ..., pen)
```

Ou bien

```algorithme
Ecrire (Nom_fonction (pe1, pe2, ...) )
```

```python
Objet = Nom_fonction (pe1, pe2, ..., pen)
```

Ou bien

```python
print (Nom_fonction (pe1, pe2, ...) )
```

<!-- TODO vérifier: le PDF présente un tableau « Appel algorithmique » | « Appel en Python » avec « Ou bien » au centre de chaque colonne, et un cadre « Paramètres effectifs » pointant vers pe1, pe2, ... -->

**NB :**

- *pf* : est un paramètre formel qui est défini au niveau de la définition de la fonction.
- *pe* : est un paramètre effectif utilisé lors de l'appel de la fonction.
- L'instruction **retourner/return**, qui vient toujours en *dernière ligne* de la fonction, définit ce que doit renvoyer la fonction (c'est le résultat de la fonction).
- La valeur (ou l'objet) renvoyée pourra, par exemple, être stockée dans une variable et ré-exploitée par le programme.

**Application 1 :** écrire un code, en algorithme et en Python, d'une fonction **carreX(x)** qui permet de calculer le carre d'un entier « x » :

```algorithme
Fonction carreX(x : entier) : entier
Début
    Retourner x*x
Fin
```

```python
def carreX(x) :
    return x*x
```

**Application 2 :** écrire un code, en algorithme et en Python, d'une fonction **Nbvoy( ch)** qui permet de retourner le nombre de voyelles dans une chaine de caractères. Exp : ch= "Salut amis"   nb= 4

```algorithme
Fonction Nbvoy( ch : chaine) : entier
Début
    Nb ← 0
    Pour i de 0 à long(ch) – 1 Faire
        Si Pos ( Majus(ch[i]), "AEIOUY") ≠ -1 Alors
            Nb ← Nb + 1
        Fin Si
    Fin Pour
    Retourner Nb
Fin
```

```python
def Nbvoy (ch) :
    nb=0
    for i in range(len(ch)) :
        if "AEIOUY".find(ch[i].upper()) != -1 :
            nb+=1
    return nb
```

| Objet | Nature / Type |
|---|---|
| i, Nb | entier |

<!-- TODO vérifier: le tableau ci-dessus est le T.D.O.L de la fonction Nbvoy, placé dans le PDF à droite de l'algorithme ; « Salut amis » est écrit avec des guillemets typographiques doubles ouvrants des deux côtés -->

**Application 3 :** écrire un code, en algorithme et en Python, d'une fonction **Nbchiff( ch)** qui permet de retourner le nombre de chiffres dans une chaine de caractères. Exp : ch= "Bac2022"   nb = 4

```algorithme
Fonction Nbchiff( ch : chaine) : entier
Début
    Nb ← 0
    Pour i de 0 à long(ch) – 1 Faire
        Si estNum (ch[i]) Alors
            Nb ← Nb + 1
        Fin Si
    Fin Pour
    Retourner Nb
Fin
```

```python
def Nbchiff (ch) :
    nb=0
    for i in range(len(ch)) :
        if ch[i].isdigit() :
            nb+=1
            return nb
```

| Objet | Nature / Type |
|---|---|
| i, Nb | entier |

<!-- TODO vérifier: dans le Python de l'original, « return nb » est décalé encore plus à droite que « nb+=1 » ; transcrit au même niveau que « nb+=1 » (donc à l'intérieur du if, ce qui est faux : la fonction retournerait dès le premier chiffre) ; indentation réelle illisible. Le T.D.O.L est placé à droite de l'algorithme dans le PDF -->

**Remarques :**

1. Pour exécuter une fonction, il faut **l'appeler**.
2. Toutes les instructions qui suivent l'instruction **return** constitue un code mort c'est-à-dire non exécutable par la fonction.
3. Une fonction peut ne pas avoir de paramètres au moment de la définition, dans ce cas il ne faut pas oublier les deux parenthèses ().

## IV. Les procédures :

### 1. Définition d'une procédure :

Une procédure est un ensemble d'instructions, appliqué sur des arguments passés en paramètres (appelés paramètres formels), qui renvoie zéros ou plusieurs résultats au programme appelant.

### 📌 2. Déclaration d'une procédure en algorithme et en Python :

```algorithme
Procédure Nom-procédure (pf1 : type1, pf2 : type2, ...)
Début
    Traitement
Fin
```

```python
def Nom-procédure (pf1, pf2,...) :
    Traitement
```

**Exemple** d'une procédure qui permet de saisir un entier ( 4 ≤ n ≤ 25 ) .

Procédure en algorithme :

```algorithme
Procédure saisie (@ x : entier)
Début
    Répéter
        Ecrire ("N =")
        Lire(x)
    Jusqu'à (4 ≤ x ≤ 25)
Fin
```

Procédure en Python :

```python
def saisie ( ) :
    global n
    ok= False
    while ok== False:
        n =int(input("N ="))
        ok = 4 <= n <= 25
```

Procédure (fonction) en Python avec return :

```python
def saisie ( ) :
    ok = False
    while not ok:
        x =int(input("N ="))
        ok = 4 <= x <= 25
    return x
```

<!-- TODO vérifier: dans le PDF, « @ x » est entouré d'un cercle et une flèche le relie à « global n » du Python ; le tableau de l'original comporte trois colonnes (Procédure en algorithme | Procédure en Python | Procédure (fonction) en Python avec return) ; « Nom-procédure » est écrit avec un tiret dans l'original (invalide en Python), transcrit tel quel -->

**NB :** Si le mode de passage est par adresse (par référence), on ajoutera le symbole **@** avant le nom du paramètre formel. On dit qu'on est devant un *changement d'état*

c-à-d. d'un état initial *vide* vers un état final *avec une valeur* (une opération de saisie) ou bien *une modification* de valeurs ( exp : *permutation de valeurs*)

**Mode de passage des paramètres :** C'est la substitution des paramètres effectifs par les paramètres formels. Il correspond à un transfert de données entre le programme appelant (PP) et le sous-programme appelé.

- *Par adresse (par variable /par référence) :* Toute modification du PF entraîne la modification du PE. Donc le transfert de données sera effectué dans les deux sens : du programme appelant vers la procédure appelée et inversement.
  **NB :** le **PF** doit être précédé par le symbole **@** au niveau de l'entête de la procédure.
- *Par valeur :* Toute modification du PF n'entraîne pas la modification du PE. Donc le transfert de données sera effectué dans un seul sens : du programme appelant vers la procédure appelée.

La procédure saisie (), en Python, est sans paramètre puisque la valeur de n sera saisie pour la 1ère fois. C'est une variable *globale* du programme principal, donc on peut la faire déclarer par le mot clé **global** à l'intérieur du sous-programme.

### 3. Appel d'une procédure :

L'appel d'une procédure, au niveau Algorithme, comme en python se fait par son nom suivi par la liste de paramètres effectifs, comme suit :

| Algorithme | En Python : Procédure | En Python : Fonction |
|---|---|---|
| `saisie (n)` | `saisie ( )` | `n = saisie ( )` |

**Remarque :**

- Les paramètres effectifs transmis par variable ne peuvent pas être des constantes ou des expressions. Il ne peut s'agir que des variables.
- On interdit l'emploi de paramètres variables dans les fonctions ainsi que la modification des valeurs des variables globales.
- **Les variables globales :** Ce sont des variables déclarées dans le programme principal, **utilisable dans les instructions du programme principal** ainsi que dans **les procédures** et **les fonctions**.
- **Les variables locales :** Ce sont des variables déclarées dans la procédure ou la fonction, **utilisable uniquement à l'intérieur** de **la procédure** ou **la fonction**.

**Application 1 :** écrire un code, en algorithme et en Python, d'une procédure **lecture (ch)** qui permet de saisir une chaine de caractères non vide et de longueur maximale =20.

```algorithme
Procédure lecture (@ch : chaine)
Début
    Répéter
        Ecrire ("Donner une chaine : ")
        Lire(ch)
    Jusqu'à (long(ch) ∈ [1..20])
Fin
```

```python
def lecture() :
    b=False
    while not b :
        ch=input("Donner une chaine :")
        b = (1<=len(ch)<=20)
    return ch
```

**Application 2 :** écrire un code, en algorithme et en Python, d'une procédure **remplir (n, T)** qui permet de remplir un tableau T de N caractères alphabétiques.

```algorithme
Procédure remplir (n : entier ; @T : Tab)
Début
    Pour i de 0 à N-1 Faire
        Répéter
            Ecrire ("T[", i, "]= ")
            Lire(T[i])
        Jusqu'à (T [i] ∈ ["A".."Z"])
    Fin Pour
Fin
```

```python
def remplir(n ,T) :
    for i in range(n) :
        b=False
        while not b :
            T[i]=input("T["+str(i)+"]=")
            b = ("A"<=T[i]<="Z") and len(T[i])==1
```

| Objet | Nature / Type |
|---|---|
| i | entier |

<!-- TODO vérifier: le tableau ci-dessus est le T.D.O.L de la procédure remplir (placé dans le PDF à droite de l'algorithme) ; l'original écrit « n » dans l'en-tête et « N-1 » dans le Pour (casse différente) ; la procédure lecture du Python est sans paramètre et retourne ch alors que l'énoncé et l'algorithme l'appellent lecture (ch) avec @ch -->

## Série d'exercices

<!-- TODO vérifier: ce dernier texte du PDF est intitulé « Application 3 » (comme la fonction Nbchiff plus haut) ; placé ici comme Exercice 1 car c'est un énoncé sans correction à la fin du chapitre -->

### Exercice 1

Écrire un algorithme modulaire « **traitement** » qui permet de :

- Saisir un entier N avec (3<= N <= 30)
- Remplir un tableau par N caractères alphanumériques.
- Déterminer le nombre de lettres trouvant dans ce tableau T
- Déterminer la chaine formée par les chiffres existant dans le tableau.
- Afficher le tableau T ainsi le nombre de lettres et la chaine des chiffres.

**Exemple :**

Si N= 8 et T :

| T | 2 | M | 0 | A | 2 | T | 2 | H |
|---|---|---|---|---|---|---|---|---|
| indice | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |

Alors le programme affichera :

> 2   M   0   A   2   T   2   H  
> Le nombre de lettres = 4  
> La chaine des chiffres = 2022

- Schématiser votre programme en indiquant les données, les traitements et les résultats.
- Puis écrire l'algorithme correspondant.
