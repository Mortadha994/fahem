---
niveau: 2eme
chapitre: 1
titre: Les structures de données et les structures simples
type: cours
notions: algorithme, constantes, variables, type entier, type réel, type booléen, type chaîne de caractères, conversion des types, tableaux, entrée/sortie, affectation, fonctions prédéfinies
source: Classroom — Chapitre 1 - Les structures des données et les structures simples
---

# Chapitre I : Les structures de données et les structures simples

## I. Notion

### 1. Notion d'Algorithme

- Un algorithme est une suite de raisonnement ou de calcule qui fournit la solution à un problème présenté sous forme de succession des étapes.
- C'est un ensemble d'instruction logique organisé (ordonné) pour résoudre un problème.
- A la base de tout programme, il existe donc un algorithme.
- En fait, un programme n'est rien d'autre qu'une traduction d'un algorithme en un langage de programmation.

### 📌 2. Forme générale d'un Algorithme

```algorithme
Algorithme Nom_De_L_Algorithme
Début
    Etape 1
    Etape 2
    ...
    ...
    ....
    Etape n
Fin
```

### 3. Exemple

Si on prend l'exemple suivant :

- Données : fournies 2 entiers.
- Traitement : Faire la somme de ces deux entiers.
- Résultat : afficher la somme.

Comment écrire un algorithme qui résout cet exemple ?

On peut donc dire que tout problème (généralement) se décompose en 3 parties :

- La partie lecture : dans laquelle les données fournies sont "lues"
- La partie traitement : dans laquelle un ou plusieurs opérations sont effectuées pour atteindre les résultats voulus.
- La partie écriture : dans laquelle les résultats sont affichés

En appliquant ceci à notre exemple on trouve qu'on doit écrire cela :

1. La lecture de deux entiers
2. Calculer la somme
3. Afficher cette somme

Si on essaye d'écrire cela convenablement, en langage de description, on doit écrire

```algorithme
Algorithme Calcul_Somme
Début
    Lire (entier1)
    Lire (entier2)
    somme ← entier1 + entier2
    Ecrire (somme)
Fin
```

```python
entier1 = int (input())
entier2 = int (input())
somme = entier1 + entier2
print(somme)
```

- **entier1**, **entier2** et **somme** sont dits *variables*
- Il est conseillé d'utiliser des noms de variables significatifs
- On peut distinguer deux verbes dans l'exemple :
  - **lire** : Introduire une valeur dans une variable
  - **écrire** : Afficher le contenu de cette variable
- Il est également conseillé d'ajouter quelques messages pour faciliter la compréhension de l'algorithme d'abord, et du programme par l'utilisateur ensuite, notre algorithme deviendra donc

<!-- TODO vérifier: l'original écrit « Debut » (sans accent) dans cet exemple et « Début » ailleurs ; harmonisé en « Début » -->

```algorithme
Algorithme Calcul_Somme
Début
    Ecrire ("Donner le premier entier")
    Lire (entier1)
    Ecrire ("Donner le deuxième entier")
    Lire (entier2)
    somme ← entier1 + entier2
    Ecrire ("la somme est : ", somme)
Fin
```

```python
entier1 = int (input("Donner le premier entier"))
entier2 = int (input("Donner le deuxième entier"))
somme = entier1 + entier2
print("la somme est : " , somme)
```

## II. Les constantes et les Variables

### 1. Les constantes

**a) Définition :**

Une constante est une case mémoire dont la valeur reste inchangée tout le long de l'exécution du programme.

Exemples :

- E = 2.718281
- Pi = 3.14
- Trouve = faux
- Val = 20

**b) Caractéristiques :**

Une constante est caractérisée par :

- Son nom : un identificateur unique
- Sa valeur inchangeable.

**c) Déclarations :**

**Déclaration en Algorithme**

| Objet | Nature/type |
|---|---|
| Nom de la constante | Constante = Valeur |

**d) Remarque :**

- La valeur de la constante nous renseigne sur son type : réel, entier, booléen, …
- On utilise les constantes pour rendre le programme plus lisible et plus facilement modifiable

**e) Exemple :**

Déclarer un constant message de valeur "Bonne chance".

| Objet | Nature/type |
|---|---|
| Message | Constante = "Bonne chance" |

**Activité :**

Ecrire un code en Python qui permet :

- D'afficher la constante pi,
- D'additionner pi avec 1, et de l'affecter à pi
- D'afficher pi encore une autre fois.
- Exécuter ce code, que constatez-vous ?
- Fermer l'éditeur IDLE et ouvrir de nouveau et afficher la constante pi. Que constatez-vous ?

**Solution :**

```python
>>> from math import *
>>> pi
>>> pi=pi+1
>>> pi
```

- On constate que la constante pi peut être changée au cours du programme
- On remarque que la valeur pi est toujours initialisée à 3.14

### 2. Les Variables

**a) Définition :**

Une variable est un objet dont la valeur est susceptible d'être modifiée dans le temps.

Elle est caractérisée par :

1. Son nom : un identificateur unique
2. Son type
3. Son contenu

**b) Déclarations :**

**Déclaration en Algorithme**

| Objet | Nature/type |
|---|---|
| Nom de la variable | Type de la variable |

Python :

```python
Nom_Variable = Valeur_Variable
```

`=` correspond à une affectation

**c) Remarque :**

- Un identificateur est un mot que le programmeur choisit librement et qui lui permet de nommer son programme, ses données (constante, variables, …)
- Les caractères autorisés pour construire un identificateur sont :
  1. Les lettres majuscules et minuscules non accentuées.
  2. Les chiffres
  3. Le caractère de soulignement « _ » (tiré bas)
- Un identificateur ne peut commencer que par une lettre
- Il est conseillé de choisir des noms d'identificateurs évocateurs

Exemples :

- Les identificateurs suivants sont corrects : Classe, ELEVE1 ; nombre_d_eleves ;
- Par contre ceux-ci sont incorrects :
  - Elève 1 (lettre accentuée non admise et l'espace aussi)
  - Nombre_d'eleves (l'apostrophe est interdite)
  - 1ereclasse (on ne peut pas commencer par un chiffre)
- Variable 1, variables 2, …, variable N sont les identificateur des variables intervenant dans le programme (ou l'algorithme) et type 1, type 2, …, et type N sont les identificateurs de leurs types respectifs.
- Lors de la déclaration d'une variable, le compilateur réserve dans la mémoire vive (RAM) un certain espace (appelé la taille de la variable) pour stocker la valeur future de cette variable. Suivant le type de celle-ci l'espace réservé ne sera pas de tout le même. Ainsi pour une variable de type entier, on réserve un espace de 2 octets alors qu'un réel occupe 8 octets.

<!-- TODO vérifier: « 2 octets » pour un entier ici, mais « codage sur 32 bits soit 4 octets » plus loin (III.1) ; transcrit tel quel -->

**Activité :**

Déclarer la variable age [?] 17 puis faire appel à l'aide du nom age, Age et AGE

Que Constatez-vous ?

<!-- TODO vérifier: symbole manquant entre « age » et « 17 », et séparateurs entre « age », « Age » et « AGE » -->

**Solution :**

```python
age=17
print ('age=', age)
print ('age=', Age) #Erreur
print ('age=', AGE) #Erreur
```

**N.B :**

- Les lettres majuscules et minuscules ne constituent la même variable (age ≠ Age ≠ AGE)
- Python est sensible à la casse, ce qui signifie les variables age, Age et AGE sont différentes.

<!-- TODO vérifier: première phrase du N.B sans « pas » dans l'original (« ne constituent la même variable ») et avec une parenthèse fermante en trop ; transcrite telle quelle -->

## III. Les types standards

### 1. Le type Entier : (int)

La mémoire vive de l'ordinateur n'étant pas infinie et par conséquent l'ensemble des entiers n'est pas égal à Z.

Si une variable est déclarée sous un type entier cela signifie que ses valeurs possibles sont les entiers appartenant à un certain intervalle [MinInt, MaxInt].

Entier compris entre -2 147 483 648 et 2 147 483 647 (codage sur 32 bits soit 4 octets)

**Remarque :**

1. Les opérateurs arithmétiques qu'on peut appliquer sur une variable de type entier sont : l'addition (+), la soustraction (-), la multiplication (*), la division entière (div), le reste de la division entière (mod) et le changement de signe (-).
2. Les opérateurs relationnels sont : <, >, ≤, ≥, ≠, =

<!-- TODO vérifier: trois symboles absents de l'extraction texte (« <, >, , , , = ») ; ≤ ≥ ≠ déduits de la ligne Python du type Réel -->

Exemples :

- `21 div 4 = 5`
- `21 mod 4 = 1`
- `21 / 4 = 5.25`

**Exemple de déclaration :**

| Objet | Nature/type |
|---|---|
| A | Entier |

### 2. Le type Réel : (float)

Comme pour les entiers, l'ensemble des nombres réels informatiques n'est pas, c'est un ensemble fini.

<!-- TODO vérifier: phrase incomplète dans l'original (« n'est pas, c'est un ensemble fini ») ; transcrite telle quelle -->

Les valeurs d'une variable de type réel sont donc délimitées par un intervalle de validité (correspondant cette fois à un espace de 8 octets).

Dans le langage python, tout réel est codifié par : un chiffre autre que 0 précédé du signe - si le nombre est négatif puis un point (qui correspond à notre virgule) suivi de dix chiffres et d'un exposant positif ou négatif à deux chiffres précédé de la lettre E.

Exemples :

- Le nombre 12,5 est mémorisé par python sous la forme : 1.2500000000E+01 (qu'il faut le comprendre 1,25.10¹). Cette écriture est appelée écriture scientifique des nombres (ou écriture à virgule flottante)
- Par contre le nombre 1/3 est mémorisé sous la forme 3.3333333333E-01 (qu'il faut comprendre 3, 3333333333.10⁻¹)

<!-- TODO vérifier: exposants (10¹ et 10⁻¹) perdus dans l'extraction texte, rétablis d'après la notation E+01 / E-01 -->

**Remarque :**

1. Nous ne sommes pas obligés d'adopter cette écriture dans la conception de nos programmes. A condition d'utiliser le point à la place de la virgule et la lettre E pour l'exposant.
2. Les opérateurs arithmétiques qu'on peut appliquer sur une variable de type réel sont : l'addition (+), la soustraction (-), la multiplication (*), la division (/) et le changement de signe (-).
3. Les opérateurs relationnels sont : <, >, ≤, ≥, =, ≠ (En Python : <, >, <=, >=, ==, !=)

<!-- TODO vérifier: ≤ ≥ ≠ absents de l'extraction texte ; déduits de la liste Python entre parenthèses -->

**Exemple de déclaration :**

| Objet | Nature/type |
|---|---|
| X | Réel |

**Application :** soient la déclaration suivante :

| Objet | Nature/type |
|---|---|
| Max | Constante = 1000 |
| X | Réel |
| Y | Réel |
| A | Entier |
| B | Entier |
| C | Entier |

Compléter le tableau ci-dessous, dans le cas d'invalidité, donner une justification.

- `C ← A mod B`
- `C ← (990 - max) div A`
- `C ← A mod y`
- `X ← A / B`
- `X ← A mod (A / B)`
- `C ← (max - 990) div A`
- `C ← A mod 0`
- `X ← A div B`

<!-- grille de réponse supprimée -->

| Opérateur | Python | algorithme | Exemple |
|---|---|---|---|
| Addition | `+` | `+` | 2 + 4 = 6 |
| Soustraction | `-` | `-` | 4 - 2 = 2 |
| Multiplication | `*` | `*` | 7 * 2 = 14 |
| Puissance | `**` | `**` | 2 ** 3 = 8 |
| Division | `/` | `/` | 21 / 4 donne 5.25 |
| Division entière | `//` | `div` | 21 // 4 donne 5 |
| Reste de Division entière | `%` | `mod` | 21 % 4 donne 1 |
| Addition, soustraction, multiplication, division… puis affectation |  | `+=` `-=` `*=` `/=` `**=` `//=` `%=` | X = 5 ; x += 3 (x vaut 8) ; x **=2 (x vaut 25) |
| Inférieur | `<` | `<` | 2 < 3 donne True |
| Inférieur ou égale | `<=` | `<=` | 2.75 <= 2 donne False |
| Supérieur | `>` | `>` | 3 > 2 donne True |
| Supérieur ou égale | `>=` | `>=` | 2.5 >= 2 donne True |
| Égale | `==` | `=` | 2.5 == 2.5 donne True |
| Différent de | `!=` | `≠` | 2 != 2 donne False |

<!-- TODO vérifier: ligne « puis affectation » : dans l'original les opérateurs +=, -=, … apparaissent dans la colonne « algorithme » et la colonne « Python » est vide -->

### Les fonctions mathématiques

Python fournit des fonctions mathématiques de base, regroupées dans le module math.

Elles peuvent être regroupées en trois ensembles :

- Des constantes.
- Des fonctions de conversion
- Des fonctions trigonométriques

Pour utiliser les fonctions mathématiques, il faut commencer par importer le module math, pour importer la bibliothèque mathématique on utilise :

```python
From math import *
```

(*pour utiliser toutes les fonctions usuelles de math)

<!-- TODO vérifier: « From » avec un F majuscule dans l'original (Python attend « from ») ; transcrit tel quel -->

On peut préciser la fonction du module math, pour cela on utilise

```python
from math import nom_fonction
```

par exemple

```python
from math import pi
```

N.B. : dir( ) retourne la liste des fonctions d'un module donné

```python
from math import *
print(dir()) #Lister l'ensemble des fonctionnalités du module math
print(e) #Constante mathématique e (constante d'Euler)
print(pi) #Constante mathématique π
print(sqrt(16)) #Renvoie la racine carrée de x
print(abs(-8)) #Renvoie la valeur absolue de x
print(fabs(-8)) #Renvoie la valeur absolue de x en float
print(trunc(5.25)) #Renvoie la partie entière de x
print(pow(3, 4)) #Renvoie x**y
print(cos(pi/4)) #Renvoie le cosinus de x en radians.
print(degrees(pi/4)) #Convertit en degrés un angle exprimé en radians.
```

### Les nombres aléatoires

Pour générer un nombre aléatoire avec python, on doit importer d'abord la bibliothèque random

- Pour générer un nombre aléatoire de type entier, on doit appeler la fonction randint

```python
from random import randint
randint(BINF,BSUP)
```

(BINF, BSUP) représente l'intervalle au quelle générée le nombre aléatoire de type entier

- Il est possible de générer un nombre aléatoire de type réel, on doit d'abord appeler la fonction uniform de la bibliothèque random

```python
from random import uniform
uniform(BINF,BSUP)
```

(BINF, BSUP) représente l'intervalle au quelle générée le nombre aléatoire de type réel

```python
from random import random
random()
```

Génère un réel aléatoire compris entre 0 et 1 exclu

```python
from random import randint
print(randint(0,5)) # génère un nombre aléatoire de type entier entre 0 et 5
from random import uniform
print(uniform(0,5)) # génère un nombre aléatoire de type réel entre 0 et 5
from random import random
print(random()) # génère un nombre aléatoire de type réel entre 0 et 1 exclu
```

### 3. Le type Booléen : (bool)

Une variable déclarée sous le type booléen est dite « booléenne ». Elle ne peut prendre que deux valeurs possibles : vrai (True) ou faux (False).

Les opérateurs possibles applicables sur les variables booléennes sont :

- La négation NON (NOT)
- La conjonction ET (AND)
- La disjonction OU (OR)

| A | B | NON(A) | NON(B) | A ET B | A OU B |
|---|---|---|---|---|---|
| Faux | Faux |  |  |  |  |
| Faux | Vrai |  |  |  |  |
| Vrai | Faux |  |  |  |  |
| Vrai | Vrai |  |  |  |  |

<!-- TODO vérifier: cellules de résultat vides dans l'original (table de vérité à compléter) -->

**Remarque :**

- Classement des opérateurs selon l'ordre de priorité décroissante :
  1. NOT
  2. `*`, `/`, div, mod, AND
  3. `+`, `-`, OR
  4. `<`, `<=`, `=`, `<>`, `>=`, `>`
- Les opérateurs se trouvant entre parenthèses ( ) sont prioritaires
- Si les opérateurs ont même priorité, on commence de gauche vers la droite

**Exemple de déclaration :**

| Objet | Nature/type |
|---|---|
| Ok | Booléen |

N.B : On utilise True et False

### 4. Le type Chaîne de caractère : (str)

Une variable de type caractère a comme valeur un des 256 caractères connus : lettres minuscules, lettres majuscules, lettres accentuées, chiffres, caractères spéciaux ($, %, …).

La valeur d'une variable de type caractère est donnée par le caractère lui-même encadré par deux guillemets en algorithme et par deux apostrophes ou deux guillemets en python.

Exemples :

"A", 'a', '2', "", …

```python
s1 = "Salut mes collègues"
s2 = 'Aujourd\'hui' # séquence d'échappement \
#La séquence d'échappement \n représente un saut ligne :
s3 = 'Première ligne\nDeuxièmeligne'
print(s1)
print(type(s1))
print(s2)
Print(s3)
```

<!-- TODO vérifier: « Print(s3) » avec P majuscule et « Deuxièmeligne » sans espace dans l'original ; transcrits tels quels -->

**Remarques :**

1. Chaque caractère possède un code appelé : Code ASCII (American Standard Code for Information Interchange)
2. Le caractère "" est un caractère (caractère vide)
3. Une variable de type caractère ne peut contenir qu'un seul caractère
4. Les caractères sont classés selon leurs codes ASCII. ("A"<"B"<"C"<"D"<"E"<…<"Z")
   Exemple : Code ("A") = 65, Code ("a") =97
5. Les opérateurs relationnels sur les caractères sont : <, >, ≤, ≥, =, ≠

<!-- TODO vérifier: ≤ ≥ ≠ absents de l'extraction texte (remarque 5) ; déduits comme au type Réel -->

| Ch = "BONJOUR" | B | O | N | J | O | U | R |
|---|---|---|---|---|---|---|---|
| Indice (positif) | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| Indice (négatif) | -7 | -6 | -5 | -4 | -3 | -2 | -1 |

Ch[0] donne 'B'

ch[5] donne 'U'

aussi ch[-7] donne 'B' et ch[-5] donne 'N'

Une chaîne de caractères est une suite de n caractères (0 ≤ n ≤ 255).

Si n = 0 alors la chaîne est dite vide.

Exemple : "informatique", "programme", … sont des chaînes de caractères.

<!-- TODO vérifier: « 0 ≤ n ≤ 255 » : les symboles ≤ sont absents de l'extraction texte -->

Remarques :

- Le caractère de position i dans une chaîne de caractère ch est noté, en algorithme et en python, par ch [i]
  Exemple : si ch = "informatique" alors ch [0] = "i" ; ch [2] = "f" ; …
- Le compilateur réserve 256 octets dans la RAM pour stocker les caractères de la chaîne CH même si la chaîne contient un nombre de caractères inférieur à 256.
- Au moment de la déclaration d'une chaîne CH, on peut fixer le nombre maximal des caractères qui constituent la chaîne CH
- Les indices commencent par 0 (zéro)

**Exemple de déclaration :**

| Objet | Nature/type |
|---|---|
| Ch | Chaine de caractères |
| Ch2 | Chaine de 30 caractères |

### Opérateurs applicables sur les chaînes

| opérateur | signification | exemple | Résultat |
|---|---|---|---|
| `+` | concaténation de chaînes de caractères | `t = "abc" + "def"`<br>`print(t)` | `t ="abcdef"` |
| `+=` | concaténation puis affectation | `t="123"`<br>`t += "abc"`<br>`print(t)` | `t ="123abc"` |
| `in`, `not in` | une chaîne en contient-elle une autre ? | `print("ed" in "med")` | True |
| `*` | répétition d'une chaîne de caractères | `t = "abc" * 4`<br>`print(t)` | `t= "abcabcabcabc"` |
| `[n]` | obtention du enième caractère, le premier caractère a pour indice 0 | `t = "abc";`<br>`print(t[0])` | a |
| `[i:j]` | obtention des caractères compris entre les indices i et j-1 inclus, le premier caractère a pour indice 0 | `t = "Informatique";`<br>`print(t [2:8])` | format |

### Formatage de chaîne

À chaque expression précédée d'un % appelé marqueur de formatage, doit correspondre une valeur de formatage

L'expression est de la forme % [P]c où c est un caractère qui détermine le type de valeur et P un éventuel paramètre supplémentaire, indiquant la précision à utiliser pour la valeur à formater

La précision est représentée par un entier préfixé par un point qui spécifie le nombre de chiffres significatifs après la virgule

Exemples de caractères de formatage :

- `%d` : entier ;
- `%f` ou `%F` : réel ;
- `%c` : un seul caractère (sous la forme d'un string ou d'un entier) ;
- `%s` : renvoie le résultat de la primitive str();
- `%o` : octal non signé ;
- `%u` : décimal non signé ;
- `%x` ou `%X` : valeur hexadécimale, préfixée respectivement par 0x ou 0X ;
- `%e` ou `%E` : valeur à virgule flottante, de la forme xe[?]v ou xE[?]v;

<!-- TODO vérifier: « xevou xEv » dans l'extraction texte, signes (probablement ±) perdus ; « %f ou F% » lu « %f ou %F » -->

```python
print('%.2f dinars' %2.394765) # 2.39 dinars
print('%E dinars' %2.394765) #2.394765E+00 dinars
print('%s dinars' %'2.394') #2.394 dinars
print('%d dinars' %2.394) #2 dinars
print("Mon Prénom est %s j'ai %d ans !" % ('Anis', 22)) #Mon Prénom est Anis j'ai 22 ans !
```

### Conversion des types

Il existe plusieurs fonctions qui permettent de forcer le type d'une variable en un autre type :

- `int()` : permet de modifier une variable en entier.
- `long()` : transforme une valeur en long.
- `float()` : permet la transformation en flottant.
- `str()` : permet de transformer la plupart des variables d'un autre type en chaînes de caractère.
- `repr()` : similaire à str.
- `eval()` : évalue le contenu de son argument comme si c'était du code Python.

Puis :

- `Nom_var = str(Nom_var)` : permet de transformer une variable de type entier ou réel en une chaîne
- `Nom_var=int(Nom_var)` : permet de convertir une variable de type chaîne ou réel en entier
- `Nom_var=float(Nom_var)` : permet de convertir une variable de type chaîne ou entier en réel

## IV. Les Tableaux

### 1. Définition

Un tableau unidimensionnel (ou vecteur) est une structure de données permettant de ranger (regrouper) un nombre fini d'éléments de même type.

Un vecteur est caractérisé par :

- Son nom (un identificateur unique. Exemple : T, V, U, …)
- Sa taille (nombre d'éléments. Exemple : 20, 30, 100, …)
- Son type (le type des éléments qu'il contient. Exemple : entier, réel, caractères, …)

### 2. Déclaration

**a) Déclaration en algorithme (première formulation) :**

| Objet | Nature/type |
|---|---|
| T | Tableau de 30 entiers |

**b) Déclaration (deuxième formulation) :**

T.D.N.T

| Type |
|---|
| Tab = tableau de 30 Entiers |

T.D.O

| Objet | Nature/type |
|---|---|
| T | Tab |

**b) Déclaration en Python :**

```python
from numpy import *
T= array ([int]*30)
```

### 3. Remarque

- Si T et U sont deux tableaux de même type alors l'instruction T←U transfère en bloc tout le tableau U dans le tableau T. Cette opération est appelée affectation de transfert.
- Les éléments d'un tableau n'ont pas de valeurs par défaut. Il faut penser à les initialiser avant de les utiliser.
- En dehors de l'affectation de transfert, aucune instruction n'est utilisable pour un tableau en bloc. Ainsi l'initialisation d'un tableau T à 0 ne peut pas se faire par l'instruction T ←0. De même, on ne peut pas utiliser les instructions écrire et lire pour afficher ou lire un tableau T en entier.
- L'affichage ou la lecture des éléments d'un tableau se fait un par un.

## V. Les opérations d'entrée / sortie

### 📌 1. L'opération d'entrée

```algorithme
Lire (Variable)
```

```python
variable= input()
```

```algorithme
Ecrire ("donner un entier")
Lire(x)
```

```python
X = input("donner un entier")
```

<!-- TODO vérifier: « x » en algorithme mais « X » en Python dans l'original ; transcrit tel quel -->

### 📌 2. L'opération de sortie

```algorithme
Ecrire ("Message")
Ecrire (Objet)
Ecrire ("Message", Objet)
Ecrire ("Message1", Objet1, "Message2", Objet2)
```

```python
print ('Message') ;
print (Objet) ;
print ('Message', Objet) ;
print ('Message1', Objet1,'Message2', Objet2) ;
```

Exemple :

```algorithme
X ← 474
Ecrire (X)
Ecrire ("X")
```

- `Ecrire (X)` affiche 474
- `Ecrire ("X")` affiche X

Remarques :

- On peut afficher le résultat d'une expression par : Ecrire (expression). Exemples : Ecrire (x/2-1), Ecrire (X>Y), …
- Afficher un mélange : Ecrire (a, "+", b, "+", c, "=", m)
- La procédure print("Message \n" ) \n permet d'effectuer un retour à la ligne après l'affichage d'un résultat.

## VI. L'affectation

### 📌 1. Définition

L'affectation est l'instruction qui permet d'attribuer (affecter) une valeur à une variable ou de modifier la valeur qu'elle a déjà. Sa syntaxe est :

```algorithme
Variable ← Valeur
```

```python
Variable =Valeur
```

### 2. Remarque

- Expression : est une expression arithmétique dont la valeur sera affectée à la variable.
- Il doit y avoir une comptabilité entre le type de la variable et celui de l'expression.

### 3. Exemple

| Exemples | Commentaires |
|---|---|
| `Note ← 12` | Affecte à Note la valeur 12 |
| `X ← Y` | Affecte à X la valeur de la variable Y |
| `X ← 3*Y+1` | Calcule la valeur de 3*Y+1 et l'attribue à X |
| `Z ← sin (y-1)` | Calcule la valeur y-1 puis son sinus et attribue sa valeur à Z |
| `K ← k+1` | Ajoute 1 à la valeur de K (incrémentation) |
| `K ← k-1` | Diminuer la valeur de K de 1 (décrémentation) |

<!-- TODO vérifier: « K » et « k » (casse différente) dans les deux dernières lignes de l'original ; transcrit tel quel -->

**Application :**

Soit la séquence d'affectation suivante :

1. `R ← 10`
2. `S ← pi * R * R`
3. `R ← 1`
4. `S ← Carré (ABS(R))`

Remplir le tableau d'exécution de cette séquence d'affectation ?

<!-- grille de réponse supprimée -->

## Les fonctions et les procédures prédéfinies

### Les fonctions prédéfinies sur les caractères

| Nom | Nom en Python | Rôle | Exemples |
|---|---|---|---|
| `ord (c)` | `ord (c)` | Renvoie le code ASCII du caractère c. Le résultat est un entier positif. | `ORD ("A")` vaut 65<br>`ORD ("a")` vaut 97 |
| `chr (x)` | `chr (x)` | Renvoie le caractère dont le code ASCII est x. | `CHR (65)` vaut "A"<br>`CHR (97)` vaut "a" |

### Les fonctions prédéfinies sur les entiers et les réels

| Nom | Python | Type de paramètre | Type de résultat | Rôle | Exemple |
|---|---|---|---|---|---|
| `arrondi (x)` | `round (x)` | Réel/entier | entier | Donner un entier qui est la valeur du réel x arrondie à la plus proche valeur. | Arrondi (9.499) vaut 9<br>Arrondi (2.5) vaut 3<br>Arrondi (8,99) vaut 9 |
| `abs (x)` | `abs (x)` | Réel/entier | Réel/entier | Donne la valeur absolue de x. | Abs (-20) vaut 20 |
| `RacineCarré (x)` | `sqrt(x)` | Réel/entier | Réel | Donne la racine carrée de x si x n'est pas négatif et provoque une erreur, sinon. | RacineCarré (2) vaut 1,4142 |
| `Ent(x)` | `int (x)` | Réel/entier | entier | Retourne la partie entière de x. | `X ← int (9.499)`<br>X vaut 9 |
| `Aléa()` | `random ()` | ---------- | Réel | Donne un réel compris entre 0 et 1 exclu. | `X ← Alea`<br>X vaut [0,0 . . 0,999999] |
| `Aléa(Binf,Bsup)` | `randint (Binf,Bsup)` | entier | entier | Donne un entier entre Binf et Bsup. | Alea (15,100)<br>donne un entier ∈ [15..100] |
| --------- | `Uniform(Binf,Bsup)` | Entier | Réel | Donne un rél entre Binf et Bsup | `uniform (15,100)`<br>donne un réel ∈ [15..100] |

<!-- TODO vérifier: flèches (←) absentes de l'extraction texte aux lignes « Ent(x) » et « Aléa() » (« X  int (9.499) », « XAlea ») ; rétablies ; « int » dans la colonne exemple de la fonction Ent -->

Remarque :

Pour utiliser ces fonctions il faut importer la bibliothèque math :

```python
from math import *
```

Et la bibliothèque random :

```python
from random import *
```

### Les fonctions prédéfinies sur les chaînes de caractères

| Syntaxe en Algorithme | Syntaxe en Python | Description | Exemple |
|---|---|---|---|
| `+` | `+` | Permet la concaténation de deux ou plusieurs chaines de caractères | `Ch1='micro-'`<br>`Ch2='ordinateur'`<br>`Ch3=ch1+ch2 ;`<br>Resultat: Ch3="micro-ordinateur" |
| `Long(ch)` | `Len(ch)` | Retourne le nombre de caractères d'une chaine | `L=len('Python')`<br>L=6 |
| `Majus(ch)` | `Ch.upper()` | Mettre tous les caractères d'une chaîne Ch en majuscules | `Ch1='python'`<br>`Ch2=Ch1.upper ()`<br>Résultat : ch2='PYTHON' |
| `Pos(ch2,ch1)` | `Ch1.find(ch2)` | Retourne la position d'une chaîne ch2 dans une chaine Ch1. Cette fonction retourne -1 si la recherche n'a pas abouti. | `Ch1='langage'`<br>`K=Ch1.find('ga')` ; k=3 |
| `Sous_chaine(ch,d,f)` | `Ch[d :f]` | Retourne une partie de la chaine ch à partir de la position d jusqu'à la position f (f exclue) | `Ch ← sous_chaine("baccalauréat",0,3)`<br>Ch = "bac" |
| `Effacer(ch,d,f)` | `Ch[ :d]+ch[f:]` | Efface des caractères de la chaine ch à partir de la position d jusqu'à la position f (f exclue) | `Ch ← Effacer("programmation",7,13)`<br>Ch = "program" |
| `Convch(x)` | `Str(x)` | Retourne la conversion d'un nombre x en une chaine de caractère | `Ch1 ← Convch (2002) ;`<br>CH1 = "2002"<br>`CH2 ← Convch(15.54)`<br>CH2 = "15.54" |
| `Estnum(ch)` | `Ch.isdigit()` ou `Ch.isnumeric ()` | Retourne vrai si la chaine ch est convertible en une valeur numérique, sinon elle retourne faux. | `B ← Estnum("bonjour")`<br>B = Faux<br>`B ← Estnum("4020")`<br>B = Vrai |
| `Valeur(ch)` | `int(ch)` ou `float(ch)` | Retourne la conversion d'une chaine ch en une valeur numérique, si c'est possible | `X1 ← valeur("1207")`<br>X1 = 1207<br>`X2 ← valeur("23.45")`<br>X2 = 23.45 |
