---
niveau: bac
chapitre: 1
titre: Série N° 3 : Les fichiers
type: serie
notions: fichiers texte, fichiers d'enregistrements, programme modulaire, tableau d'enregistrements, tri, sujets du bac
source: Classroom — Série 1+2+3 Normal - Les fichiers (série 3 les fichiers.pdf)
---

# Série N° 3 : Les fichiers

<!-- TODO vérifier: le PDF (8 pages) est intitulé « Les fichiers Série N°3 » ; la numérotation des exercices (13 à 22) est conservée telle quelle. Les mentions des titres d'exercices (« Algo + Python », « Bac 2020C », « Bac 2022P », « Bac 2015C », « Bac 2014P », « Bac 2012P ») sont reprises en première ligne de l'énoncé. Les exercices 18 à 22 sont des captures d'images de sujets du bac dans le PDF, transcrites depuis le rendu -->

## Série d'exercices

### Exercice 13

(Algo + Python)

Soit à remplir un Fichier texte **Fe** par des lignes, la saisie se termine en répondant par « **N** » à la question "**continuer O/N?**".

Une fois on a rempli le fichier le programme doit copier le contenu du fichier **fe** vers un deuxième fichier **fs** de telle sorte qu'il convertit tous les lettres se trouvant après un point "**.**" **en majuscule.**

Contenu de **fe** :

> On a bac Sc.info, bac Sc.exp.
> Fichier texte.fichier des enregistrements.
> Algo.pascal.

Contenu de **fs** :

> On a bac Sc.Info, bac Sc.Exp.
> Fichier texte.Fichier des enregistrements.
> Algo.Pascal.

<!-- TODO vérifier: les deux cadres de l'exemple sont présentés côte à côte sans légende ; légendes déduites de l'énoncé (la lettre qui suit chaque point passe en majuscule dans le cadre de droite) -->

### Exercice 14

(Algo + Python)

On dispose d'un fichier texte, intitulé **source.txt**.

Un tautogramme est texte dont les mots commencent par la même lettre (sans distinction entre majuscule ou minuscule). **Exemple :** le lion lape le lait lentement.

On se propose de sauvegarder toutes les lignes tautogrammes de ce fichier, dans un dans un 2ème fichier intitulé **tauto.txt**

### Exercice 15

(Algo + Python)

Soit **F** un fichier texte contenant un certain nombre des lignes, écrire l'algorithme du module intitulé **Former** qui permet de former un nouveau fichier texte **F2**, contenant dans chaque ligne la concaténation des voyelles (minuscules et majuscules) figurants dans chaque ligne de **F**.

### Exercice 16

(Algo + Python)

Une agence bancaire utilise pour le suivi des mouvements de ses clients les fichiers "**compte.fch**" et "**Mvt.fch**"

- le fichier "**compte.fch**" contient les fiches des comptes des clients. Chaque fiche contient les informations suivantes :
    - *Num_cpt* : numéro du compte, chaîne [20]
    - *NP* : nom et prénom du client, chaîne[15]
    - *Adr* : adresse du client, chaîne[40]
    - *Prem_Mvt* : entier désignant le numéro du bloc dans le fichier "**Mvt.fch**" portant la première opération du compte (-1 si pas d'opération)
- le fichier "**Mvt.fch**" contient les informations sur chaque mouvement du compte figurant dans "**compte.fch**". Ces informations sont :
    - *Num_cpt* : numéro du compte client
    - *Dat_op* : date de l'opération effectuée, chaîne [10] sous la forme jj/mm/aaaa
    - *Mont* : réel
    - *Nat_op* : un caractère ( D : pour débit, C : pour crédit)
    - *Mvt_suiv* : entier désignant le numéro du bloc dans ce fichier correspondant à l'opération suivante pour le même compte (-1 si pas de suivant)

*On veut réaliser le menu suivant :*

1. **Ajouter_Cpt** : saisir la nouvelle fiche compte client et l'ajouter à la fin du fichier "**compte.fch**". Le champ Prem_Mvt prend la valeur -1
2. **Ajouter_Mvt** : saisir les informations d'un nouveau mouvement et l'ajouter à la fin du fichier "**Mvt.fch**" et effectuer le test suivant, s'il s'agit d'un premier mouvement du client correspondant, changer la valeur du champ **Prem_Mvt** par le numéro du bloc déjà ajouté dans le fichier "**Mvt.fch**", sinon changer la valeur du champ **Mvt_suiv** du dernier mouvement effectué par le même client par le numéro du bloc déjà ajouté dans le fichier "**Mvt.fch**"
3. **Tri** : former à partir des fichiers "**compte.fch**" et "**Mvt.fch**" un fichier texte nommé "**résultat.txt**" contenant dans chaque ligne le numéro du compte (**Num_cpt**) suivi du caractère espace suivi par le solde final (solde final = somme des crédits – somme des débits). Le fichier "**résultat.txt**" doit être **trié dans l'ordre croissant** selon le **solde final**, utilisez un tableau d'enregistrements (Num_cpt, solde) pour effectuer l'opération de tri.
4. **Quitter**

<u>Travail demandé :</u>

Ecrire l'algorithme du programme principal qui permet de réaliser le menu décrit auparavant (la décomposition en modules est obligatoire) ainsi que l'algorithme de chaque module utilisé.

<u>*Exemple :*</u>

Soient les fichiers "**compte.fch**" et "**Mvt.fch**" suivant :

Fichier « compte.fch » :

| | Bloc 0 | Bloc 1 | Bloc 2 |
|---|---|---|---|
| **Num_cpt** | c1 | c2 | c3 |
| **NP** | Np1 | Np2 | Np3 |
| **Adr** | Adr1 | Adr2 | Adr3 |
| **Prem_mvt** | 0 | **<u>1</u>** | -1 |

> La valeur **1** (en gras et souligné) du champ **Prem_mvt** désigne le bloc numéro 1 dans le fichier **Mvt.fch**

Fichier « Mvt.fch » :

| | Bloc 0 | Bloc 1 | Bloc 2 | Bloc 3 | Bloc 4 |
|---|---|---|---|---|---|
| **Num_cpt** | c1 | c2 | c1 | c2 | c2 |
| **Dat_op** | Date1 | Date2 | Date3 | Date4 | Date5 |
| **Nat_op** | C | D | D | C | C |
| **Mont** | 2000 | 1000 | 1000 | 250 | 250 |
| **Mvt_suiv** | 2 | **<u>3</u>** | -1 | 4 | -1 |

> La valeur **3** (en gras et souligné) du champ Mvt_suiv désigne le bloc numéro **3** dans le fichier **Mvt.fch**

- ***Choix=1*** \* si on va ajouter un nouveau compte ayant la fiche (c4, Np4, Adr4), on aura la modification suivante dans le fichier "**compte.fch**" :

| | Bloc 0 | Bloc 1 | Bloc 2 | Bloc 3 |
|---|---|---|---|---|
| **Num_cpt** | c1 | c2 | c3 | **c4** |
| **NP** | Np1 | Np2 | Np3 | **Np4** |
| **Adr** | Adr1 | Adr2 | Adr3 | **Adr4** |
| **Prem_mvt** | 0 | 1 | -1 | **-1** |

> La valeur **5** (en gras et souligné) du champ **Prem_mvt** désigne le bloc numéro **5** dans le fichier **Mvt.fch**

<!-- TODO vérifier: la note « La valeur 5 ... du champ Prem_mvt » figure à côté du tableau du choix 1 dans le PDF alors qu'elle se rapporte au tableau du choix 2 ci-dessous (c3) ; transcrite telle quelle -->

- ***Choix =2*** \* si on va ajouter un mouvement effectué par le client c3 on aura une modification dans les 2 fichiers :

Fichier « compte.fch » :

| | Bloc 0 | Bloc 1 | Bloc 2 |
|---|---|---|---|
| **Num_cpt** | c1 | c2 | c3 |
| **NP** | Np1 | Np2 | Np3 |
| **Adr** | Adr1 | Adr2 | Adr3 |
| **Prem_mvt** | 0 | 1 | **<u>5</u>** |

Fichier « Mvt.fch » :

| | Bloc 0 | Bloc 1 | Bloc 2 | Bloc 3 | Bloc 4 | Bloc 5 |
|---|---|---|---|---|---|---|
| **Num_cpt** | c1 | c2 | c1 | c2 | c2 | **c3** |
| **Dat_op** | Date1 | Date2 | Date3 | Date4 | Date5 | **Date6** |
| **Nat_op** | C | D | D | C | C | **C** |
| **Mont** | 2000 | 1000 | 1000 | 250 | 250 | **1500** |
| **Mvt_suiv** | 2 | 3 | -1 | 4 | -1 | **-1** |

![Flèche reliant la valeur 5 du champ Prem_mvt du bloc 2 de compte.fch au bloc 5 de Mvt.fch](figures/serie3-ex16-fleche-bloc5.png)

<!-- TODO figure: à recréer -->

- ***Choix =2*** \* si on va ajouter un mouvement effectué par le client c2 on aura une modification dans le fichier "**Mvt.fch**" :

| | Bloc 0 | Bloc 1 | Bloc 2 | Bloc 3 | Bloc 4 | Bloc 5 |
|---|---|---|---|---|---|---|
| **Num_cpt** | c1 | c2 | c1 | c2 | c2 | **c2** |
| **Dat_op** | Date1 | Date2 | Date3 | Date4 | Date5 | **Date6** |
| **Nat_op** | C | D | D | C | C | **C** |
| **Mont** | 2000 | 1000 | 1000 | 250 | 250 | **3000** |
| **Mvt_suiv** | 2 | 3 | -1 | 4 | **<u>5</u>** | **-1** |

![Flèche reliant la valeur 5 du champ Mvt_suiv du bloc 4 au bloc 5](figures/serie3-ex16-fleche-mvt-suiv.png)

<!-- TODO figure: à recréer -->

- ***Choix =3*** \* le fichier "**résultat.txt**" sera le suivant :

> c2 **<u>-500</u>**
> c3 0
> c1 1000

> La valeur **-500** (en gras et souligné) est égale à (250 + 250) -1000

### Exercice 17

(Bac 2020C) (Algo + Python)

On se propose de nettoyer un fichier text "Source.txt" pour générer un fichier "Resultat.txt", en respectant les règles suivantes :

- Le texte ne doit pas comporter des espaces succesifs
- Si une ligne de texte commence par une lettre, cette dernière doit être en majuscule
- Avant un point ou une virgule il n'y a pas d'espace
- Après un point, il doit y avoir un espace et s'il est suivi d'une lettre ell doit être en majuscule, à l'exception du point qui peut se trouver à la fin d'une ligne

**N.B** : Chaque ligne du fichier est composée d'au maximum 255 caractères.

**Exemple :**

Pour le fichier "Source.txt" suivant :

![Capture du Bloc-notes affichant Source.txt : « Fichier Edition Format Affichage ? » ; « un fichier     est un    ensemble de   données .ces données sont stockées sur un support d'enregistrement . » ; « l'accés à un    fichier    peut   se faire de deux façons , séquentiel ou direct. » ; « le    contenu   d'un fichier texte   représente   une    suite de caractères »](figures/serie3-ex17-source-txt.png)

<!-- TODO figure: à recréer -->

Après nettoyage des lignes du fichier "Source.txt", le fichier "Resultat.txt" sera :

![Capture du Bloc-notes affichant Resultat.txt : « Fichier Edition Format Affichage ? » ; « Un fichier est un ensemble de données. Ces données sont stockées sur un support d'enregistrement. » ; « L'accés à un fichier peut se faire de deux façons , séquentiel ou direct. » ; « Le contenu d'un fichier texte représente une suite de caractères »](figures/serie3-ex17-resultat-txt.png)

<!-- TODO figure: à recréer -->

<!-- TODO vérifier: la virgule dans « deux façons , séquentiel » est suivie d'un espace précédé d'un espace dans les deux captures (y compris Resultat.txt) alors que la règle demande de supprimer l'espace avant une virgule ; transcrit tel quel -->

**Travail demandé :**

1. Donner une instruction d'association pour chacun de deux fichiers "Source.txt" et "Resultat.txt" respectivement aux variables logiques **S** et **R**, sachant que les deux fichiers sont enregistrés sur la racine du disque **D**.
2. Ecrire un module nommé **Nettoi_F** que permet à partir d'un fichier "Source.txt" déjà saisi dans le programme appelant, de créer et de générer un deuxième fichier "Resultat.txt" en respectant les règles décrites précédemment.

### Exercice 18

(Bac 2022P) (Algo + Python)

**Problème (10,5 points)**

Afin d'analyser les données concernant **Coronavirus** (Covid19) dans plusieurs pays, on dispose d'un fichier texte nommé "**Corona.txt**" sauvegardé dans la racine du lecteur **D** et contenant des informations sur l'infection par ce virus dans quelques pays.

Chaque ligne du fichier contient le **nom du pays** suivi du **nombre de personnes infectées**, le **nombre de personnes guéries** et le **nombre de personnes décédées**. Chaque deux informations sont séparées par un espace.

On se propose d'organiser les données du fichier par ordre décroissant selon le nombre de personnes infectées par le virus et de déterminer, pour chaque pays, le pourcentage des personnes décédées par rapports à celles infectées comme suit :

- Transférer les informations contenues dans le fichier "**Corona.txt**" vers un tableau d'enregistrements **T**. Chaque enregistrement est formé de quatre champs représentant les informations sur les infections par coronavirus dans chaque pays.
- Trier le tableau **T** par ordre décroissant du nombre des personnes infectées par coronavirus.
- Transférer le contenu du tableau **T** vers un fichier "**Resultat.txt**", sauvegardé dans la racine du lecteur D, tout en ajoutant à la fin de chaque ligne du fichier le pourcentage des personnes décédées à cause de coronavirus par rapports aux personnes infectées de chaque pays suivi du caractère "**%**", sachant qu'il est égal à :

  **(Nombre de personnes décédées du pays / Nombre de personnes infectées du pays) \* 100**

**N.B. :** Chaque deux informations d'une même ligne du fichier "**Resultat.txt**" doivent être séparées par un espace.

**Exemple :**

Pour le contenu du fichier "**Corona.txt**" suivant :

> USA 80770604 53945789 579725
> Chine 109964 102234 4636
> Italie 12867918 11651094 155214
> Tunisie 999441 953587 27824

Le contenu du tableau **T** sera :

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| | USA | Chine | Italie | Tunisie |
| | 80770604 | 109964 | 12867918 | 999441 |
| | 53945789 | 102234 | 11651094 | 953587 |
| | 579725 | 4636 | 155214 | 27824 |

Après tri, le tableau **T** devient :

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| | USA | Italie | Tunisie | Chine |
| | 80770604 | 12867918 | 999441 | 109964 |
| | 53945789 | 11651094 | 953587 | 102234 |
| | 579725 | 155214 | 27824 | 4636 |

<!-- TODO vérifier: dans le PDF, chaque case du tableau T est un petit tableau vertical à 4 lignes (pays, infectés, guéris, décédés), les numéros 1 à 4 sont au-dessus ; reformaté en tableau 4 colonnes. Texte des petits tableaux lu sur une image de faible résolution -->

Le contenu du fichier "**Resultat.txt**" sera :

> **USA 80770604 53945789 579725 0,71%**
> **Italie 12867918 11651094 155214 1,20%**
> **Tunisie 999441 953587 27824 2,78%**
> **Chine 109964 102234 4636 4,21%**

**Travail demandé :**

1. Analyser le problème en le décomposant en modules tout en prévoyant un module qui affiche les noms des **Nb** pays les moins infectés dans le monde (prévoir la saisie de **Nb** qui doit être inférieur ou égal au nombre total des pays contenus dans le fichier "**Corona.txt**").

   **N.B. :** Le candidat n'est pas appelé à remplir le fichier "**Corona.txt**".
2. Ecrire les algorithmes des modules envisagés.

### Exercice 19

(Bac 2022P) (Algo + Python)

**Exercice 5 (7 points)**

Un nombre décimal *n* est dit brésilien s'il possède, dans une base *B* (avec 2 ≤ *B* ≤ *n* − 2), une représentation qui s'écrit sous la forme de *p* chiffres égaux, c'est-à-dire : *n* = (*kkk…kkk*)_B (*p* chiffres)

**Exemples :**

- 7 est un nombre brésilien car 7 = (111)₂
- 3124 est un nombre brésilien car 3124 = (44444)₅
- 1170 est un nombre brésilien car 1170 = (2222)₈
- 20 est un nombre brésilien car 20 = (22)₉
- 204 est un nombre brésilien car 204 = (CC)₁₆
- 9 n'est pas un nombre brésilien car 9 = (1001)₂ = (100)₃ = (21)₄ = (14)₅ = (13)₆ = (12)₇ et aucune de ces écritures n'est brésilienne.

On se propose d'écrire un algorithme d'une procédure **Gen_Bres** qui permet de créer et de remplir un fichier d'enregistrements nommé "**F_Brésilien.dat**" par les nombres brésiliens contenus dans un fichier texte existant nommé "**Nombres.txt**", sachant que chaque ligne du fichier "**Nombres.txt**" contient un nombre décimal et chaque enregistrement du fichier "**F_Brésilien.dat**" comportera les champs suivants :

- **N** : Le nombre décimal.
- **B** : Une base dans laquelle le nombre **N** s'écrit sous la forme de *p* chiffres égaux avec 2 ≤ *B* ≤ 16.
- **Rep** : La représentation du nombre décimal N dans la base B.

**Travail demandé :**

1. Donner une déclaration d'un type pour le fichier d'enregistrement "**F_Brésilien.dat**" ainsi que celles des types nécessaires à sa déclaration.
2. Donner en algorithmique les instructions d'ouverture des deux fichiers "**Nombres.txt**" et "**F_Brésilien.dat**", sachant que le fichier à créer et à remplir "**F_Brésilien.dat**" et le fichier source "**Nombres.txt**" se trouvent sur la racine du disque **D**.
3. Ecrire un algorithme de la procédure **Gen_Bres**, sachant que le fichier "**Nombres.txt**" est déjà rempli dans le programme appelant.

### Exercice 20

(Bac 2015C)

**Problème (9,5 points)**

En utilisant un ordinateur, même ayant un seul processeur, nous remarquons qu'on peut lancer plusieurs programmes en même temps. Or, nous savons qu'un seul processeur ne peut exécuter qu'un seul programme à la fois. Cette notion de "multitâche" est obtenue grâce au système d'exploitation.

Pour ce faire, le système d'exploitation utilise une technique appelée ordonnancement des processus, qui consiste à gérer l'allocation des différents processus au processeur.

Il existe plusieurs algorithmes d'ordonnancement des processus, tels que :

- FIFO (First In First Out) : Le processus qui arrive le premier sera le premier à être exécuté.
- LIFO (Last In First Out) : Le processus qui arrive le dernier sera le premier à être exécuté.
- SJF (Shortest Job First) : Le processus qui a une durée d'exécution minimale sera le premier à être exécuté.

On se propose d'élaborer un nouvel ordonnancement basé sur les deux méthodes : FIFO et SJF, comme expliqué ci-dessous :

1. Remplir un fichier d'enregistrements intitulé "Processus.dat", situé sur la racine du disque C, par N processus prêts à être exécutés (avec 3 ≤ N ≤ 200), sachant qu'un processus est caractérisé par :
    - un code, qui est une chaîne de caractères formée par la lettre "P" suivie d'un nombre qui commence de 1 et s'incrémente automatiquement de 1 pour chaque nouveau processus (P1, P2, …, P100,….).
    - une durée d'exécution exprimée en millisecondes.

   NB : L'ordre de remplissage des processus dans le fichier "Processus.dat" représente l'ordre d'ordonnancement FIFO.
2. A partir du fichier "Processus.dat", appliquer l'algorithme d'ordonnancement SJF pour classer les processus dans un nouveau fichier d'enregistrements intitulé "Ord_SJF.dat".
3. A partir des fichiers "Processus.dat" et "Ord_SJF.dat", générer un fichier texte intitulé "Ord_Nouv.txt", contenant les codes des processus, chacun sur une ligne, et ce de la manière suivante :
    1. Commencer par placer chaque processus ayant le même rang dans les deux fichiers "Processus.dat" et "Ord_SJF.dat".
    2. Ensuite, placer le reste des processus selon leur ordre d'apparition dans le fichier "Ord_SJF.dat".

Exemple :

- Pour le fichier "Processus.dat" suivant :

| Code | Durée |
|---|---|
| P1 | 3 |
| P2 | 1 |
| P3 | 2 |
| P4 | 3 |
| P5 | 1 |
| P6 | 5 |

- En appliquant l'algorithme d'ordonnancement SJF, on obtient le fichier "Ord_SJF.dat" suivant :

| Code | Durée |
|---|---|
| P2 | 1 |
| P5 | 1 |
| P3 | 2 |
| P1 | 3 |
| P4 | 3 |
| P6 | 5 |

- le fichier "Ord_Nouv.txt" généré sera le suivant :

> P3
> P6
> P2
> P5
> P1
> P4

### Exercice 21

(Bac 2014P)

Une molécule est un regroupement d'au moins deux atomes qui sont unis par des liens chimiques et elle est représentée par une formule chimique. Exemple : H₂O.

Une formule chimique est une succession de symboles d'atomes, suivi chacun par un entier représentant le nombre d'apparitions (**nbr**) de l'atome dans la molécule.

Chaque atome est symbolisé par la première lettre de son nom en majuscule, suivie éventuellement d'une deuxième lettre en minuscule pour distinguer des atomes ayant des initiales identiques. Ainsi, le **Fluor (F)** se distingue du **Fer (Fe)**, du **Fermium (Fm)** et du **Francium (Fr)**,

Le calcul de la masse molaire moléculaire d'une molécule, notée **M(Molécule)**, sera comme suit :

- pour chaque atome de la molécule, calculer le produit (**nbr** x **A(atome)**) où **A(atome)** est un réel représentant la masse atomique de l'atome,
- calculer la somme des produits obtenus.

*Exemple :*

*Pour la molécule dichromate de potassium (K₂Cr₂O₇) qui est constituée de **2** atomes de **potassium (K)**, **2** atomes de **chrome (Cr)** et **7** atomes d'**oxygène (O)**, sa masse molaire moléculaire **M(K₂Cr₂O₇)** est égale à 2\***A**(K) + 2\***A**(Cr) + 7\***A**(O).*

*Puisque **A**(K) = 39,1 g/mol, **A**(Cr) = 52 g/mol et **A**(O) = 16 g/mol, alors **M**(K₂Cr₂O₇) sera égale à 2 \* 39,1 + 2\*52 + 7 \* 16 = **294,2 g/mol***

En disposant d'un fichier texte "**Molecules.txt**" dont chaque ligne contient le ***nom*** d'une molécule suivi de sa ***formule chimique***, séparés par le caractère astérisque "\*", écrire un programme permettant de :

- remplir un fichier "**Atomes.dat**" par les données relatives à **N** atomes (N≤50), où chacun est représenté par son **symbole** et sa **masse atomique**,
- stocker dans un fichier "**Resultats.dat**" le ***nom*** et la ***masse molaire moléculaire*** de chaque molécule figurant dans le fichier "**Molecules.txt**".

### Exercice 22

(Bac 2012P)

**Louis Braille**, est l'inventeur du système d'écriture tactile à points saillants, à l'usage des personnes aveugles ou fortement malvoyantes.

En Braille standard :

- Un caractère est représenté par six points numérotés de 1 à 6 et disposés comme le montre la **Figure 1**.
- Un point peut être saillant (en relief) ou non, comme le montre la **Figure 2**.
- Le nombre et la disposition des points en relief définissent un caractère.

![Figure 1 : cellule Braille de six points numérotés, colonne de gauche 1, 2, 3 et colonne de droite 4, 5, 6](figures/serie3-ex22-figure1.png)

<!-- TODO figure: à recréer -->

![Figure 2 : photographie d'un point en relief sur une surface Braille](figures/serie3-ex22-figure2.png)

<!-- TODO figure: à recréer -->

Dans la suite, on s'intéressera à la représentation des 26 lettres majuscules de l'alphabet français. Le tableau suivant, donne cette représentation.

![Tableau des 26 lettres majuscules de A à Z, chacune accompagnée de sa cellule Braille à six points (points noirs = points saillants)](figures/serie3-ex22-alphabet-braille.png)

<!-- TODO figure: à recréer -->

*N.B* Chaque point noir représente un point saillant.

Etant donné un fichier d'enregistrements intitulé "**Codes_Braille.dat**", où chaque enregistrement est composé de deux champs :

- un champ **Lettre** contenant une lettre majuscule de l'alphabet français,
- un champ **Codage** contenant une chaîne de 6 caractères représentant l'équivalent en braille de la lettre.

En utilisant le fichier "**Codes_Braille.dat**", on se propose de convertir le fichier texte intitulé "**Braille.txt**" contenant une représentation Braille d'un texte en son équivalent en alphabet français puis d'afficher le résultat obtenu.

Sachant que :

- Chaque ligne du fichier "**Braille.txt**" contient la représentation d'un seul mot.
- La représentation d'un mot est une concaténation de blocs de six caractères.
- Chaque bloc de six caractères représente une lettre du mot.
- Un caractère peut être un astérisque ("\*") représentant un point saillant, ou un trait d'union ("-") représenté un point non saillant.
- Les caractères "\*" et "-" sont disposés selon l'ordre des numéros des points qu'ils représentent. Par exemple, la lettre "H" sera représentée par le bloc de six caractères suivant : `*  *  -  -  *  -` (points 1 à 6)

**Exemple :**

Etant donné le contenu du fichier "**Codes_Braille.dat**" dont une partie est représentée comme suit :

| Lettre | Codage |
|---|---|
| A | `*-----` |
| B | `**----` |
| C | `*--*--` |
| D | `*--**-` |
| … | |

Si le contenu du fichier "**Braille.txt**" est le suivant :

> `*---*-*-**-**-----*-**--*---*-*-***-`
> `*--**-*-*--*`
> `**----*-----*--*--`

Le programme affichera la chaîne : "**EXAMEN DU BAC**"

En effet :

- "**EXAMEN**" est l'équivalent en alphabet français de la première ligne du fichier "**Braille.txt**".

  | E | X | A | M | E | N |
  |---|---|---|---|---|---|
  | `*---*-` | `*-**-*` | `*-----` | `*-**--` | `*---*-` | `*-***-` |

- "**DU**" est l'équivalent en alphabet français de la deuxième ligne du fichier "**Braille.txt**".
- "**BAC**" est l'équivalent en alphabet français de la troisième ligne du fichier "**Braille.txt**".

**N.B** *Le candidat n'est pas appelé à remplir les deux fichiers "**Codes_Braille.dat**" et "**Braille.txt**".*

<!-- TODO vérifier: les codages de l'exemple (traits d'union rendus comme des tirets bas dans l'image) ont été lus sur une image ; le bloc de la lettre H est montré avec les numéros 1 à 6 sous les caractères -->
