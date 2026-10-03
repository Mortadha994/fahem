---
niveau: bac
chapitre: 6
titre: Les algorithmes d'approximation et d'optimisation
type: cours
notions: algorithmes d'approximation, problèmes d'optimisation (maximisation et minimisation), recherche de zéros d'une fonction (dichotomie), point fixe d'une fonction, valeurs approchées de constantes (π et e), valeur approchée de sin(x), calcul d'aires (méthode des rectangles et des trapèzes)
source: Classroom — Chap 6 : Les algorithmes d'approximation et d'optimisation
---

# Chapitre VI : Les algorithmes d'approximation et d'optimisation

<!-- Le PDF (8 pages) ne contient que des algorithmes ; aucun bloc Python n'est présent et aucun n'a été ajouté (seul l'énoncé de la partie VI demande « un programme Python ») -->

<!-- TODO vérifier: mots-clés harmonisés en Répéter, Jusqu'à, Si, Alors, Sinon, Fin Si (l'original écrit alors / sinon / fin si / FinSi), Pour, Faire, Fin Pour (l'original écrit Faire / faire, Fin pour / Fin Pour), Ecrire (l'original écrit Écrire / Ecrire / ecrire), Lire, ou, Mod, Début, Fin -->

<!-- Le sous-titre « 1. Algorithme de dichotomie » (épinglé) n'existe pas dans le PDF : c'est le libellé « Algorithme : » de la partie III, transformé en titre pour respecter la règle des sections épinglées -->

## I. Introduction

**Q :** qu'est-ce qu'un algorithme d'approximation ?

**R :** les algorithmes d'approximation sont utilisés pour retrouver des valeurs approchées de la solution de certains problèmes.

**D'après le dictionnaire :**

*Approximation, nom féminin :*

- Sens 1 = Évaluation, estimation d'un résultat, d'une valeur ou d'une grandeur
- Sens 2 = Valeur imprécise, valeur approchée.

**Q :** qu'est-ce qu'un algorithme d'optimisation ?

**R :** un algorithme d'optimisation est un algorithme qui trouve une solution optimale à un problème de minimisation ou de maximisation.

**Q :** est-ce qu'un algorithme d'approximation est un algorithme optimal ?

**R :** un algorithme d'approximation ne peut pas trouver une solution optimale.

## II. Problèmes d'optimisation

### Exemple de maximisation

On veut réaliser une pièce métallique ayant la forme de la figure ci-dessous, composée d'un rectangle et de deux triangles équilatéraux (**x** et **y** sont exprimés en mètres)

En déterminant le périmètre **P** de la pièce en fonction de **x** et **y** et en choisissant P=2m, nous aurons **y=1-2\*x** ce qui donne **0<x<1/2**.

On peut conclure donc que l'aire **S** de la pièce est égale à **S = ((√3-4)/2) \* x² + x**.

**Question :**

On se propose de calculer une valeur approchée de x pour laquelle **S** est **maximal**, pour cela écrire un algorithme puis la traduction en python d'un programme en python qui permet de déterminer une valeur approchée de **x** à **10⁻²** près.

![Pièce métallique : un rectangle central de largeur y et de côté x, flanqué à gauche et à droite de deux triangles équilatéraux de côté x](figures/piece-metallique.png)
<!-- TODO figure: à recréer -->

```algorithme
Procédure calculer ()
Début
    x ← 0
    S ← 0
    Répéter
        Sp ← S
        x ← x + 0.01
        S ← Surface(x)
    Jusqu'à ((S-Sp ≤ 0) ou (x = 1/2))
    Ecrire ("la valeur approchée de x est : ", x- 0.01, " donne la surface maximal ", Sp)
Fin
```

```algorithme
Fonction Surface (x : réel) : réel
Début
    Retourner ((Racine_carré (3)-4)/2)*x*x + x
Fin
```

<!-- TODO vérifier: dans l'original, la fonction Surface est dans un encadré à droite de la procédure calculer ; la phrase « la traduction en python d'un programme en python » est transcrite telle quelle ; « surface maximal » (sans e) transcrit tel quel -->

### Exemple de minimisation

Chaque page d'un livre à imprimer comporte un rectangle d'aire 300cm² pour le texte, des marges mesurant 2 cm sur les bords horizontaux et 1.5 cm sur les bords verticaux.

![Page d'un livre : rectangle de texte de 300 cm² et de largeur x, avec une marge de 2 cm en haut et une marge de 1.5 cm sur le côté](figures/page-livre.png)
<!-- TODO figure: à recréer -->

On se propose de déterminer les dimensions des pages pour que la consommation du papier soit minimale.

**Méthode**

- Stext = x\* longtext = 300 → longtext = 300/x
- Longpap = longtext + 2\*2 = 300/x + 4
- Largpap = x + 2\*1,5 = x + 3
- Spap = longpap \* largpap → S=(x+3)\*(300/x+4) → S=4x+900/x+312
- 0<x<√300

```algorithme
Procédure calculer (pas : réel)
Début
    x ← pas
    S ← Surface(x)
    Répéter
        Sp ← S
        x ← x + pas
        S ← Surface(x)
    Jusqu'à ((S-Sp ≥ 0) ou (x ≥ Racine_carré (300)))
    x ← x-pas
    Ecrire ("la valeur approchée de x est : ", x, " les dimensions du papier :  Largeur = ", (x+3) ," et longueur =",(300/x+4))
Fin
```

```algorithme
Procédure saisir (@pas : réel)
Début
    Répéter
        Ecrire ("Pas = "), Lire(pas)
    Jusqu'à pas>0
Fin
Fonction Surface (x : réel) : réel
Début
    Retourner 4*x + 900/x + 312
Fin
```

<!-- TODO vérifier: dans l'original, les procédures/fonctions saisir et Surface sont dans un encadré à droite de la procédure calculer ; « Longpap » / « longpap » et « Largpap » / « largpap » transcrits tels quels ; « Ecrire ("Pas = "), lire(pas) » transcrit tel quel (sur une seule ligne) -->

## III. Recherche de zéros d'une fonction

**Q :** donnez-moi des exemples ?

**R :** Recherche de zéros de f c'est-à-dire chercher les valeurs approchées des x lorsque **F(x)=0** dans **[a, b]**

**Q :** Expliquer le principe de la méthode de **f(x)=0** dans l'intervalle **[a, b]** ?

**R :** la méthode consiste à répéter la division de l'intervalle en deux parties égaux (la dichotomie) en calculant **c= (a+b)/2**. Il y a maintenant deux possibilités :

- ou **f (a)** et **f(c)** sont de signe opposés donc les zéros de f existe dans le sous intervalle **[a, c]** ici on va continuer la division de l'intervalle.
- ou **f(c)** et **f (b)** sont de signe opposés donc les zéros de f existe dans le sous intervalle **[c, b]** ici on va continuer la division de l'intervalle.

### 📌 1. Algorithme de dichotomie

```algorithme
Procédure calculer (a,b,eps : réel)
Début
    N ← 0
    Répéter
        C ← (a + b) /2
        Si (F(a) * F(c) < 0) Alors
            b ← c
        Sinon
            a ← c
        Fin Si
        N ← N +1
    Jusqu'à (b-a ≤ eps)
    Ecrire ("la valeur approchée est : ", a, "trouvée après ", N, " itérations")
Fin
```

## IV. Recherche d'un point fixe d'une fonction

**Présentation :**

En mathématiques, pour une application f d'un ensemble **E**, un élément **x** de **E** est un point fixe de **f** si **f(x) = x**.

**Exemples :**

- Dans le plan, la symétrie par rapport a un point **A** admet un unique point fixe : **A**
- L'application inverse (définie sur l'ensemble des réels non nuls) admet 2 points fixes : **-1** et **1**

Toutes les fonctions n'ont pas nécessairement de point fixe.

Par exemple, la fonction **f** telle que **f(x) = x + 1** n'en possède pas, car il n'existe aucun nombre réel **x** égal a **x+1**.

Dans la suite de ce paragraphe, nous allons établir des algorithmes permettant de calculer une valeur approchée du point fixe d'une fonction.

Soit la suite réelle (**Uₙ**) récurrente et définie par sa valeur initiale **U₀** et par la relation de Récurrence **Uₙ₊₁ = f(Uₙ)**. Dans le cas ou (**Uₙ**) converge, elle le fait nécessairement vers un point fixe de f.

**Activité :**

Point fixe de f avec une précision epsilon (**10⁻⁵** prés). Soit la fonction f définie par : **F(x)= 1/(1 + x)³**

**Algorithme :**

```algorithme
Procédure pt_fixe (eps : réel)
Début
    xact ← 1
    i ← 1
    Répéter
        xpre ← xact
        i ← i+1
        xact ← F(xact)
    Jusqu'à (abs(xact-xpre) ≤ eps)
    Ecrire ("la valeur approchée du point fixe est : ", xact, " trouvée après ", i, " itérations")
Fin
```

**Algorithme de la fonction F**

```algorithme
Fonction F (x : réel) : réel
Début
    Retourner 1/((x+1) * (x+1) * (x+1))
Fin
```

## V. Calcul de valeurs approchées des constantes connues

### 1. Valeur approchée de π

On se propose de calculer une approximation de π en utilisant la formule d'Euler.

**π² = 6 \* (1 + 1/2² + 1/3² + 1/4² + 1/5² ……)**

**Algorithme du programme Pi_Euler**

```algorithme
Procédure Pi_Euler (eps : réel)
Début
    s ← 1
    i ← 2
    Répéter
        sp ← s
        s ← s+1/(i*i)
        i ← i+1
    Jusqu'à ((RacineCarre(6*s)-RacineCarre(6*sp)) ≤ eps)
    V ← RacineCarre(6*s)
    Ecrire ("la valeur approchée de PI est : ", v)
Fin
```

<!-- TODO vérifier: l'original écrit « V ← RacineCarre(6*s) » puis « Ecrire (..., v) » (V majuscule puis v minuscule) ; transcrit tel quel -->

**Valeur approchée par la formule de Wallis**

On se propose de calculer une approximation de π en utilisant la formule de Wallis.

**π = 2 \* (2/1 \* 2/3 \* 4/3 \* 4/5 \* 6/5 \* 6/7 \* …)**

**Algorithme du programme Pi_Wallis**

```algorithme
Procédure Pi_Wallis (eps : réel)
Début
    p2 ← 2
    i ← 2
    num ← 2
    den ← 3
    Répéter
        p1 ← p2
        p2 ← p1*(num/den)
        Si (i Mod 2 = 0) Alors
            num ← num+2
        Sinon
            den ← den+2
        Fin Si
        i ← i+1
    Jusqu'à (abs(2*p2-2*p1) ≤ eps)
    Ecrire ("la valeur approchée de PI est : ", 2*p2)
Fin
```

<!-- TODO vérifier: dans l'original, « p2←2, i←2 » et « num←2, den←3 » sont écrits chacun sur une seule ligne (séparés par une virgule) ; séparés ici en une affectation par ligne -->

### 2. Valeur approchée par la formule des factorielles

On se propose de calculer une approximation de e à **10⁻⁴** en utilisant la formule suivante :

**e = 1 + (1/1!) + (1/2!) + (1/3!) + (1/4!) + (1/5!) + (1/6!) + …**

**Algorithme du programme e_Fact**

```algorithme
Procédure e_Fact (eps : réel)
Début
    S ← 1
    i ← 0
    Répéter
        sp ← s
        i ← i+1
        s ← s+1/ Fact(i)
    Jusqu'à (abs (s-sp) ≤ eps)
    Ecrire ("la valeur approchée de e est : ", s, " trouvée après ", i, " itérations")
Fin
```

<!-- TODO vérifier: dans l'original, cet algorithme est coupé par un changement de page et disposé en deux colonnes séparées par un trait vertical (colonne de gauche : S ← 1, i ← 0, Répéter, sp ← s, i ← i+1 ; colonne de droite : s ← s+1/ Fact(i), Jusqu'à, Ecrire, Fin.) ; recomposé ici dans l'ordre de lecture. La fonction Fact est donnée dans la partie VI -->

### 3. Avec appel à une fonction suite

**Algorithme du programme e_2**

```algorithme
Procédure e_2 (eps : réel)
Début
    i ← 0
    Répéter
        s ← Suite(i)
        i ← i+1
    Jusqu'à ((Suite(i) -s) ≤ eps)
    Ecrire ("la valeur approchée de e est : ", s, " trouvée après ", i, " itérations")
Fin
```

**Algorithme de la fonction suite**

```algorithme
Fonction Suite (n : entier) : réel
Début
    s ← 1
    Pour i de 1 à n Faire
        s ← s+1/Fact(i)
    Fin Pour
    Retourner S
Fin
```

## VI. Calcul de valeurs approchées des variables connues

**Valeur approchée de sin(x) :**

Sachant que **sin (x) = x - (x³/3!) + (x⁵/5!) - (x⁷/7!) + …**

Pour x très proche de zéro, écrire un programme Python qui permet d'afficher **sin(x)** en utilisant la formule ci-dessus.

Le calcul s'arrête quand la différence entre deux termes consécutifs devient Inférieure ou égale à **10⁻⁴**. La dernière somme calculée est une valeur approchée de **sin(x)**.

Le candidat pourra utiliser la fonction **FACT(n)** suivante qui permet de calculer la Factorielle de n **(n !)**.

**Algorithme de la fonction SinX(x) :**

```algorithme
Fonction SinX (x : réel) : entier
Début
    Terme ← X
    S ← X
    i ← 3
    sg ← -1
    Répéter
        TermeP ← Terme
        Terme ← Puiss(x,i)/Fact(i)
        S ← S + Terme*sg
        i ← i + 2
        sg ← -sg
    Jusqu'à (abs(Terme-TermeP) ≤ 0.0001)
    Retourner S
Fin
```

<!-- TODO vérifier: la fonction SinX est déclarée « : entier » dans l'original alors qu'elle retourne un réel ; transcrit tel quel -->

```algorithme
Fonction Fact (n : entier) : entier
Début
    F ← 1
    Pour i de 1 à n Faire
        F ← F * i
    Fin Pour
    Retourner F
Fin
Fonction Puiss (x : réel ; n : entier) : réel
Début
    P ← 1
    Pour i de 1 à n Faire
        P ← P * x
    Fin Pour
    Retourner P
Fin
```

<!-- TODO vérifier: dans l'original, les fonctions Fact et Puiss sont dans un encadré à droite de la fonction SinX -->

## VII. Calcul d'aires

### 1) Rappel

Soit une fonction f continue et croissante dans l'intervalle **[a,b]**.

Si nous ne connaissons pas de primitive de la fonction f, nous ne pouvons pas calculer ∫ₐᵇ f(x)dt. Nous chercherons alors, à en déterminer une valeur approchée.

![Courbe d'une fonction f avec la valeur f(a) sur l'axe vertical, l'abscisse a sur l'axe horizontal, l'aire sous la courbe hachurée et l'intégrale de 0 à a de f(x) dx](figures/integrale-representation.png)
<!-- TODO figure: à recréer -->

**Représentation graphique d'une intégrale**

### 2) Méthode des rectangles

**a) Principe :**

Sur chaque intervalle [aᵢ, aᵢ₊₁] représente un rectangle de largeur aᵢ₊₁ – aᵢ et de hauteur :

| Soit f(aᵢ) : Rectangles a gauche | Soit f(aᵢ₊₁) : Rectangles à droite | Soit f ((aᵢ + aᵢ₊₁)/2) : Rectangles du point milieu |
|---|---|---|
| ![Rectangles à gauche sous une courbe](figures/rectangles-gauche.png) | ![Rectangles à droite sous une courbe](figures/rectangles-droite.png) | ![Rectangles du point milieu sous une courbe](figures/rectangles-milieu.png) |

<!-- TODO figure: à recréer -->

**b) Application :**

Nous proposons de calculer, en utilisant la méthode des rectangles, l'aire résultante de la courbe de la fonction **f : x → 1/(1+x²)** sur un intervalle **[a, b]**

- a) Proposez un algorithme modulaire au problème,
- b) Déduisez les algorithmes correspondants des modules,
- c) Traduisez et testez la solution obtenue. Enregistrez votre programme sous le nom **Meth_Rec**

**Algorithme de la fonction Rectangles :**

```algorithme
Fonction Rectangles (a, b : Réel ; n : Entier) : Réel
Début
    S ← 0
    h ← (b-a)/n
    # à gauche : x ← a
    # point milieu : x ← a + h/2
    # à droit : x ← a + h
    Pour k de 1 à n Faire
        S ← S + f(x)
        x ← x + h
    Fin Pour
    Retourner S * h
Fin
```

<!-- TODO vérifier: dans l'original, les trois lignes « # à gauche », « # point milieu », « # à droit » sont surlignées en jaune (trois variantes de l'initialisation de x selon la méthode choisie) ; la fraction h ← (b-a)/n est écrite en notation fractionnaire dans l'original -->

### 3) Méthode des trapèzes

**a) Principe :**

Dans cette méthode, nous subdivisons l'intervalle **[a,b]** en n sous-intervalles, de même largeur **h = (b-a)/n**. Nous notons **aᵢ = a + i \* h**.

Par linéarité de l'intégrale, nous savons que l'intégrale globale correspond a la somme des intégrales de f sur chaque sous-intervalle de **[a,b]**. Soit **[a₀, a₁]** un de ces sous intervalles, nous approchons l'intégrale de f sur cet intervalle par l'aire du trapèze reliant les points **(a₀, 0)**, **(a₀,f(a₀))**, **(a₁, f(a₁))** et **(a₁,0)**.

Cette aire vaut **h \* ((f(a₀) + f(a₁)) / 2)**

L'intégrale globale s'obtient donc en additionnant ces n aires, c'est à dire la somme des **h \* ((f(aᵢ) + f(aᵢ₊₁)) / 2)**.

![Courbe approchée par une suite de trapèzes verticaux hachurés de même largeur sous la courbe](figures/trapezes.png)
<!-- TODO figure: à recréer -->

**b) Application :**

Utilisez la méthode des trapèzes, pour calculer l'aire résultante de la courbe de la fonction :

**f : x → 1/(1+x²)**

- a) Proposez un algorithme modulaire au problème,
- b) Déduisez les algorithmes correspondants,
- c) Traduisez et testez la solution obtenue. Enregistrez votre programme sous le nom **Meth_Tra**

**Algorithme de la fonction Trapèzes :**

```algorithme
Fonction Trapèzes (a, b : Réel ; n : Entier non signé) : Réel
Début
    h ← (b-a)/n
    S ← 0
    x ← a
    Pour k de 1 à n Faire
        S ← S + (F(x)+ F(x+h))/2
        x ← x + h
    Fin Pour
    Retourner S*h
Fin
```

<!-- La dernière page du PDF se termine par la citation : « Bien que cela puisse paraître Paradoxal, toute science exacte est dominée par la notion d'approximation » (Bertrand Russel, 1872 - 1970), accompagnée d'une illustration de professeur au tableau : non transcrite -->
