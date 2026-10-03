---
niveau: bac
chapitre: 6
titre: Série N° 1 : Approximation et optimisation
type: serie
notions: valeur approchée d'une aire entre deux courbes, approximation de π, point fixe d'une fonction, développements limités, méthode des rectangles, méthode des trapèzes, subdivision aléatoire
source: Classroom — Série Approximation et Optimisation (série 1 - approximation.pdf)
---

# Série N° 1 : Approximation et optimisation

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Série Approximation et Optimisation » ; la numérotation des exercices (1 à 13) est conservée. Les formules sont transcrites en texte linéaire (intégrales, fractions, exposants) ; le texte de l'exercice 13 est une image dans le PDF, transcrit à la lecture -->

## Série d'exercices

### Exercice 1

Les courbes **Cf** et **Cg** représentées ci-dessous sont respectivement les courbes représentatives des fonctions **f** et **g** définies sur l'intervalle **]0, +∞ [** par **f(x)=ln(x)** et **g(x)=ln(x)²**

![Repère orthogonal avec les courbes Cf (courbe de ln x) et Cg (courbe de ln(x)²) ; elles se coupent aux points d'abscisses 1 et e ; pointillés horizontaux en y = 1 et verticaux en x = e ; abscisses graduées de -4 à 4, ordonnées de -3 à 2](figures/serie1-ex1-courbes.png)
<!-- TODO figure: à recréer -->

**Travail demandée :**

Écrire un algorithme puis la traduction en python d'un programme qui permet de calculer une valeur approchée de l'aire qui se trouve entre les deux courbes représentatives dans l'intervalle **[1..e]** avec e une valeur approchée à **10⁻⁴** près de l'exponentiel décrite par la formule suivante :

e = 1/0! + 1/1! + 1/2! + 1/3! + 1/4! + ….

### Exercice 2

On peut définir **π** grâce à l'expression suivante :

π/4 = ∫₀¹ √(1 − x²) dx

Écrire un algorithme puis la traduction en python d'un programme qui permet de calculer une valeur approchée de **π** tout en utilisant l'expression décrite ci-dessus.

**N.B :** Utiliser la méthode des rectangles pour calculer l'intégrale

### Exercice 3

Soit la fonction **f(x) = x³ + x² -1**

Écrire un algorithme puis la traduction en python d'un programme qui permet de permet de trouver le point fixe de cette fonction à **10⁻⁵** près et d'indiquer à quelle itération il est trouvé.

![Courbe de f(x) = x³ + x² - 1 et droite y = x tracées dans un même repère](figures/serie1-ex3-point-fixe.png)
<!-- TODO figure: à recréer -->

### Exercice 4

Soit la fonction **f(x) = sin(x) + π/6 − x**

Écrire un algorithme puis la traduction en python d'un programme qui permet de permet de trouver le point fixe de cette fonction à 10⁻⁵ près et d'indiquer à quelle itération il est trouvé.

![Courbe de f(x) = sin(x) + π/6 - x (décroissante) et droite y = x tracées dans un même repère](figures/serie1-ex4-point-fixe.png)
<!-- TODO figure: à recréer -->

### Exercice 5

Cherchez le point fixe de la fonction **f(x) =√(1 + x)**

Traduisez et testez la solution obtenue.

Enregistrez votre programme sous le nom **Pt_fixe2**

### Exercice 6

Écrire un programme en python intitulé « **Somme** » qui permet de calculer pour un ordre n donnée (n>=0), la somme approchée de la série définie par :

S = 1 + 1 / (5¹ \* 1 !) + 1 / (5² \* 2 !) + ….. + 1 / (5ⁿ \* n !)

### Exercice 7

**Soit les développements limités des fonctions suivantes :**

- **Exp(x)** = 1 + (x/1!) + (x²/2!) + (x³/3!) + …….
- **Sin(x)** = x – (x³/3!) + (x⁵/5!) - (x⁷/7!) + ……
- **Cos(x)** = 1 – (x²/2!) + (x⁴/4!) - (x⁶/6!) + ……
- **1/(1-x)** = 1 + x + x² + x³ + x⁴ + x⁵ + ….

**Questions :**

**a)** Pour chacune des fonctions suivantes, écrire un algorithme d'un module qui permet de calculer une valeur approchée pour une valeur donnée de réel **x** (**x** dans **] -1,1[** ) à **10⁻⁶** près.

**b)** Déduire les algorithmes de chacun des modules

<!-- TODO vérifier: l'intervalle « ] -1,1[ » est transcrit tel que lu (espace avant la parenthèse) -->

### Exercice 8

(Bac 2009 Session contrôle)

On veut réaliser une pièce métallique ayant la forme de la figure ci-dessous, composée d'un rectangle et de deux triangles équilatéraux (x et y sont exprimés en mètres)

En déterminant le périmètre P de la pièce en fonction de x et y et en choisissant P=2m, nous aurons y=1-2\*x ce qui donne 0<x<1/2.

On peut conclure donc que l'aire S de la pièce est égale à S = ((√3-4)/2) \* x² + x.

**Question :**

On se propose de calculer une valeur approchée de x pour laquelle S est maximal, pour cela écrire un algorithme puis la traduction en python d'un programme en python qui permet de déterminer une valeur approchée de x à 10⁻² près.

![Pièce métallique : un rectangle central de largeur y et de côté x, flanqué à gauche et à droite de deux triangles équilatéraux de côté x](figures/piece-metallique.png)
<!-- TODO figure: à recréer -->

### Exercice 9

Une des méthodes d'approximation de π consiste à remplir au hasard un carrée Q de côté **2R** par n points. Parmi ces n point, il y'aura P points qui seront à l'intérieur du cercle inscrit dans le carrée Q comme illustré par la figure ci-contre.

<!-- TODO vérifier: l'énoncé renvoie à « la figure ci-contre » ; aucune figure n'apparaît à cet endroit dans le PDF (aucun texte ni image entre l'énoncé et l'exercice suivant) -->

En déterminant P, on aura calculé une valeur approchée de π vu que le rapport entre le nombre de points P à l'intérieur du cercle inscrit et le nombre total n de points du carrée est une estimation du rapport entre la surface du cercle est la surface du carrée Q. nous avons donc **P/n ≈ πR2/4R2 = π /4** ce qui donne **π≈4p/n**.

<!-- TODO vérifier: « πR2/4R2 » (sans exposants) et « π≈4p/n » (p minuscule) transcrits tels quels -->

On rappelle qu'un point M(x,y) est à l'intérieur du cercle si **√(x² + y²) ≤ R**

En se basant sur le principe décrit précédemment on se propose d'écrire un programme en python qui permet de saisir un rayon R (10<=R<=100) et un nombre de point n (1000<=n<=20000) de coordonnées aléatoires x et y puis calculer et afficher une valeur approchée de π

### Exercice 10

La valeur de **π/4** peut être approchée comme la somme des n premiers termes de la suite suivante :

- **Un = (-1)ⁿ / (2n + 1)**
- **U0 = 1**

1/ Proposez un algorithme de la fonction **Un** qui renvoie le **nème** terme de la suite.

2/ Proposez un algorithme de la fonction **app_pi (epsilon)** qui renvoie l'approximation de **π** calculée à partir des **n** premiers termes de la suite.

### Exercice 11

Soit l'expression mathématique suivante :

**π/4 = 1-1/3+1/5-1/7+1/9-………**

Écrire un programme Python qui utilise l'expression ci-dessus pour déterminer et afficher une valeur approchée de **π** a **10⁻⁴** prés.

- Le calcul s'arrête quand la différence entre deux sommes consécutives de cette Expression devient strictement inférieure à **10⁻⁴**.

### Exercice 12

Calculez une valeur approchée de : ∫₁⁵ **x + 3 \* sin(x) dx** en utilisant la methode des trapèzes. Traduisez et testez la solution obtenue.

### Exercice 13

(bac 2009 Session contrôle)

**Problème (12 points)**

Le but du problème est de déterminer une valeur approchée de l'intégrale I = ∫₁² e^(−x²) dx

On se propose d'utiliser deux méthodes et d'en dégager la différence entre les deux valeurs approchées trouvées.

On choisit dans les deux cas, un entier n tel que 100 < n < 1000. n sera le nombre de subdivisions qu'on va utiliser dans les deux méthodes.

1. <u>Méthode des trapèzes</u>.

   On utilise la méthode des trapèzes pour déterminer une première valeur approchée I₁ de I.

2. <u>Méthode d'une subdivision aléatoire</u>.

   On remplit un tableau V par n-1 réels distincts générés au hasard de l'intervalle [1,2]. On utilisera la fonction prédéfinie RANDOM qui génère au hasard un réel entre 0 et 1 au sens strict. Ensuite, on trie le tableau V par ordre croissant en utilisant le tri par insertion. On aura formé ainsi une suite (xᵢ)₀≤ᵢ≤ₙ où x₀ = 1, xᵢ = V[i] et xₙ = 2.

   On définit les sommes S₁ et S₂ par :

   S₁ = Σ (xᵢ₊₁ – xᵢ).f(xᵢ) ; S₂ = Σ (xᵢ₊₁ – xᵢ).f(xᵢ₊₁) avec f(x) = e^(−x²)

   (les deux sommes portent sur i de 0 à n-1)

   Une valeur approchée de I = ∫₁² e^(−x²) dx est :

   I₂ = (S₁+S₂)/2

On se propose d'écrire un programme qui calcule ∫₁² e^(−x²) dx par les deux méthodes et affiche les deux valeurs approchées ainsi que la valeur absolue de leur différence.

**Questions :**

1. Analyser le problème en le décomposant en modules et déduire l'algorithme du programme principal qui permet de réaliser le traitement décrit précédemment.
2. Analyser chacun des modules envisagés précédemment et en déduire les algorithmes correspondants.

<!-- TODO vérifier: les bornes des sommes S₁ et S₂ (i = 0 à n-1) sont lues sur une image du PDF de petite taille ; « <u>…</u> » reproduit le soulignement des titres « Méthode des trapèzes » et « Méthode d'une subdivision aléatoire » -->
