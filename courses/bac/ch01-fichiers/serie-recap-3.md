---
niveau: bac
chapitre: 1
titre: Série Récap N° 3 : Les fichiers
type: serie
notions: fichiers typés, fichiers texte, fichiers d'enregistrements, création et remplissage, recherche dans un fichier, ajout suppression et modification, menu
source: Classroom — Série 1+2+3 Récap- Les fichiers (série Récap 3 les fichiers (série 1+2+3).pdf)
---

# Série Récap N° 3 : Les fichiers

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Les fichiers — Série de Récap N°3 » ; c'est un document scanné (sujets de bac), sans couche de texte : tout est transcrit depuis des captures. La numérotation des exercices (17 à 20) est conservée telle quelle. Les mentions « (Bac 2022P) », « (Bac 2015C - Algo) », « (Bac 2014P) (Python) », « (Bac 2012P - Algo) » des titres sont reprises en première ligne de l'énoncé -->

## Série d'exercices

### Exercice 17

(Bac 2022P) (Algo + Python)

**Problème (10,5 points)**

Afin d'analyser les données concernant **Coronavirus** (**Covid19**) dans plusieurs pays, on dispose d'un fichier texte nommé "**Corona.txt**" sauvegardé dans la racine du lecteur D et contenant des informations sur l'infection par ce virus dans quelques pays.

Chaque ligne du fichier contient le **nom du pays** suivi du **nombre de personnes infectées**, le **nombre de personnes guéries** et le **nombre de personnes décédées**. Chaque deux informations sont séparées par un espace.

On se propose d'organiser les données du fichier par ordre décroissant selon le nombre de personnes infectées par le virus et de déterminer, pour chaque pays, le pourcentage des personnes décédées par rapports à celles infectées comme suit :

- Transférer les informations contenues dans le fichier "**Corona.txt**" vers un tableau d'enregistrements **T**. Chaque enregistrement est formé de quatre champs représentants les informations sur les infections par coronavirus dans chaque pays.
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

Le contenu du tableau **T** sera (une colonne par enregistrement, numérotée de 1 à 4) :

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Pays | USA | Chine | Italie | Tunisie |
| Infectées | 80770604 | 109964 | 12867918 | 999441 |
| Guéries | 53945789 | 102234 | 11651094 | 953587 |
| Décédées | 579725 | 4636 | 155214 | 27824 |

Après tri, le tableau **T** devient :

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Pays | USA | Italie | Tunisie | Chine |
| Infectées | 80770604 | 12867918 | 999441 | 109964 |
| Guéries | 53945789 | 11651094 | 953587 | 102234 |
| Décédées | 579725 | 155214 | 27824 | 4636 |

Le contenu du fichier "**Resultat.txt**" sera :

> USA 80770604 53945789 579725 0,71%
> Italie 12867918 11651094 155214 1,20%
> Tunisie 999441 953587 27824 2,78%
> Chine 109964 102234 4636 4,21%

<!-- TODO vérifier: les en-têtes de lignes du tableau T (Pays, Infectées, Guéries, Décédées) sont ajoutés d'après l'énoncé ; dans le PDF les cases ne sont pas étiquetées (la première ligne porte le nom du pays). Les chiffres des tableaux, très petits sur le scan, sont alignés sur ceux du fichier Corona.txt -->

**Travail demandé :**

1. Analyser le problème en le décomposant en modules tout en prévoyant un module qui affiche les noms des **Nb** pays les moins infectés dans le monde (prévoir la saisie de **Nb** qui doit être inférieur ou égal au nombre total des pays contenus dans le fichier "**Corona.txt**").

   **N.B. :** Le candidat n'est pas appelé à remplir le fichier "**Corona.txt**".

<!-- TODO vérifier: le « Travail demandé » du sujet n'a qu'une question (n° 1) sur le scan ; le reste du sujet original (questions suivantes) n'apparaît pas dans le PDF -->

### Exercice 18

(Bac 2015C - Algo)

**Problème (9,5 points)**

En utilisant un ordinateur, même ayant un seul processeur, nous remarquons qu'on peut lancer plusieurs programmes en même temps. Or, nous savons qu'un seul processeur ne peut exécuter qu'un seul programme à la fois. Cette notion de "multitâche" est obtenue grâce au système d'exploitation.

Pour ce faire, le système d'exploitation utilise une technique appelée ordonnancement des processus, qui consiste à gérer l'allocation des différents processus au processeur.

Il existe plusieurs algorithmes d'ordonnancement des processus, tels que :

- FIFO (First In First Out) : Le processus qui arrive le premier sera le premier à être exécuté.
- LIFO (Last In First Out) : Le processus qui arrive le dernier sera le premier à être exécuté.
- SJF (Shortest Job First) : Le processus qui a une durée d'exécution minimale sera le premier à être exécuté.

On se propose d'élaborer un nouvel ordonnancement basé sur les deux méthodes : FIFO et SJF, comme expliqué ci-dessous :

1. Remplir un fichier d'enregistrements intitulé "**Processus.dat**", situé sur la racine du disque C, par N processus prêts à être exécutés (avec 3 ≤ N ≤ 200), sachant qu'un processus est caractérisé par :
   - un code, qui est une chaîne de caractères formée par la lettre "P" suivie d'un nombre qui commence de 1 et s'incrémente automatiquement de 1 pour chaque nouveau processus (P1, P2, …, P100,….).
   - une durée d'exécution exprimée en millisecondes.

   **NB :** L'ordre de remplissage des processus dans le fichier "Processus.dat" représente l'ordre d'ordonnancement FIFO.
2. A partir du fichier "**Processus.dat**", appliquer l'algorithme d'ordonnancement SJF pour classer les processus dans un nouveau fichier d'enregistrements intitulé "**Ord_SJF.dat**".
3. A partir des fichiers "**Processus.dat**" et "**Ord_SJF.dat**", générer un fichier texte intitulé "**Ord_Nouv.txt**", contenant les codes des processus, chacun sur une ligne, et ce de la manière suivante :
   1. Commencer par placer chaque processus ayant le même rang dans les deux fichiers "Processus.dat" et "Ord_SJF.dat".

Exemple de contenu du fichier "Ord_Nouv.txt" tel qu'il apparaît à la fin du sujet scanné :

> P3
> P6
> P2
> P5
> P1
> P4

<!-- TODO vérifier: le scan s'arrête à l'étape 3.a ; les étapes suivantes (b, c…) et l'explication de l'exemple n'apparaissent pas dans le PDF, et on ne voit pas à quoi se rapporte exactement la liste P3 P6 P2 P5 P1 P4 (probablement le contenu de Ord_Nouv.txt) -->

### Exercice 19

(Bac 2014P) (Python)

Une molécule est un regroupement d'au moins deux atomes qui sont unis par des liens chimiques et elle est représentée par une formule chimique. Exemple : H₂O.

Une formule chimique est une succession de symboles d'atomes, suivi chacun par un entier représentant le nombre d'apparitions (**nbr**) de l'atome dans la molécule.

Chaque atome est symbolisé par la première lettre de son nom en majuscule, suivie éventuellement d'une deuxième lettre en minuscule pour distinguer des atomes ayant des initiales identiques. Ainsi, le **Fluor (F)** se distingue du **Fer (Fe)**, du **Fermium (Fm)** et du **Francium (Fr)**,

Le calcul de la masse molaire moléculaire d'une molécule, notée **M(Molécule)**, sera comme suit :

- pour chaque atome de la molécule, calculer le produit (**nbr x A(atome)**) où **A(atome)** est un réel représentant la masse atomique de l'atome,
- calculer la somme des produits obtenus.

*Exemple :*

*Pour la molécule dichromate de potassium (K₂Cr₂O₇) qui est constituée de 2 atomes de potassium (K), 2 atomes de chrome (Cr) et 7 atomes d'oxygène (O), sa masse molaire moléculaire M(K₂Cr₂O₇) est égale à 2\*A(K) + 2\*A(Cr) + 7\*A(O).*

*Puisque A(K) = 39,1 g/mol, A(Cr) = 52 g/mol et A(O) = 16 g/mol, alors M(K₂Cr₂O₇) sera égale à 2 \* 39,1 + 2\*52 + 7 \* 16 = 294,2 g/mol*

En disposant d'un fichier texte "**Molecules.txt**" dont chaque ligne contient le *nom* d'une molécule suivi de sa *formule chimique*, séparés par le caractère astérisque "\*", écrire un programme permettant de :

- remplir un fichier "**Atomes.dat**" par les données relatives à **N** atomes (N≤50), où chacun est représenté par son **symbole** et sa **masse atomique**,
- stocker dans un fichier "**Resultats.dat**" le *nom* et la *masse molaire moléculaire* de chaque molécule figurant dans le fichier "**Molecules.txt**".

### Exercice 20

(Bac 2012P - Algo)

**Louis Braille**, est l'inventeur du système d'écriture tactile à points saillants, à l'usage des personnes aveugles ou fortement malvoyantes.

En Braille standard :

- Un caractère est représenté par six points numérotés de 1 à 6 et disposés comme le montre la **Figure 1**.
- Un point peut être saillant (en relief) ou non, comme le montre la **Figure 2**.
- Le nombre et la disposition des points en relief définissent un caractère.

![Figure 1 : cellule Braille de six points numérotés, en deux colonnes de trois : points 1, 2, 3 à gauche et 4, 5, 6 à droite](figures/serie-recap-3-braille-figure-1.png)
<!-- TODO figure: à recréer -->

![Figure 2 : photographie d'un point en relief sur une surface (point saillant)](figures/serie-recap-3-braille-figure-2.png)
<!-- TODO figure: à recréer -->

Dans la suite, on s'intéressera à la représentation des 26 lettres majuscules de l'alphabet français. Le tableau suivant, donne cette représentation.

![Tableau de la représentation Braille des 26 lettres majuscules A à Z : pour chaque lettre, une cellule de six points (colonne 1-2-3 et colonne 4-5-6) où les points noirs sont saillants](figures/serie-recap-3-braille-alphabet.png)
<!-- TODO figure: à recréer -->

**N. B** *Chaque point noir représente un point saillant.*

Étant donné un fichier d'enregistrements intitulé "**Codes_Braille.dat**", où chaque enregistrement est composé de deux champs :

- un champ **Lettre** contenant une lettre majuscule de l'alphabet français,
- un champ **Codage** contenant une chaîne de 6 caractères représentant l'équivalent en braille de la lettre.

En utilisant le fichier "**Codes_Braille.dat**", on se propose de convertir le fichier texte intitulé "**Braille.txt**" contenant une représentation Braille d'un texte en son équivalent en alphabet français puis d'afficher le résultat obtenu.

Sachant que :

- Chaque ligne du fichier "**Braille.txt**" contient la représentation d'un seul mot.
- La représentation d'un mot est une concaténation de blocs de six caractères.
- Chaque bloc de six caractères représente une lettre du mot.
- Un caractère peut être un astérisque ("\*") représentant un point saillant, ou un trait d'union ("-") représentant un point non saillant.
- Les caractères "\*" et "-" sont disposés selon l'ordre des numéros des points qu'ils représentent. Par exemple, la lettre "**H**" sera représentée par le bloc de six caractères suivant : `*  *  -  -  *  -` (points numérotés 1 à 6 : `*` aux positions 1, 2 et 5, `-` aux positions 3, 4 et 6)

**Exemple :**

Étant donné le contenu du fichier "**Codes_Braille.dat**" dont une partie est représentée comme suit :

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

- "**EXAMEN**" est l'équivalent en alphabet français de la première ligne du fichier "**Braille.txt**" (blocs de six caractères correspondant respectivement à E, X, A, M, E, N).
- "**DU**" est l'équivalent en alphabet français de la deuxième ligne du fichier "**Braille.txt**".
- "**BAC**" est l'équivalent en alphabet français de la troisième ligne du fichier "**Braille.txt**".

**N. B** *Le candidat n'est pas appelé à remplir les deux fichiers "Codes_Braille.dat" et "Braille.txt".*

<!-- TODO vérifier: les séquences de * et - des lignes de Braille.txt sont lues sur un scan de faible résolution (longueurs des traits à contrôler : 36, 12 et 18 caractères) ; les codes des lettres A à D aussi. Le dessin Braille de la lettre H (ligne de * et - numérotés 1 à 6) est transcrit en texte -->
