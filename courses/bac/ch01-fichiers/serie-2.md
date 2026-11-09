---
niveau: bac
chapitre: 1
titre: Série N° 2 : Les fichiers
type: serie
notions: fichiers typés, fichiers texte, fichiers d'enregistrements, tri d'un fichier, statistiques, programme modulaire, génération aléatoire
source: Classroom — Série 1+2+3 Normal - Les fichiers (série 2 les fichiers.pdf)
---

# Série N° 2 : Les fichiers

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Les fichiers Série N°2 » ; la numérotation des exercices (7 à 12) est conservée telle quelle. Les mentions « (Algo + Python) » des titres d'exercices sont reprises en première ligne de l'énoncé ; les exercices 10, 11 et 12 n'en ont pas -->

## Série d'exercices

### Exercice 7

(Algo + Python)

- Remplir un fichier **caractère.dat** par N **caractères majuscules** d'une manière aléatoire **(2<N<30)**
- Trié le fichier par ordre croissant
- Déterminer l'apparence de chaque caractère et l'enregistrer dans un fichier texte **stat.txt** ainsi que le caractère correspondant
- Afficher le fichier texte

**Exemple**

Contenu de caractère.dat :

> E
> D
> E
> A
> F
> D
> E

Contenu de caractère.dat après le tri :

> A
> D
> D
> E
> E
> E
> F

Contenu de stat.txt :

> A est apparu 1 fois
> D est apparu 2 fois
> E est apparu 3 fois
> F est apparu 1 fois

<!-- TODO vérifier: l'exemple est présenté dans le PDF sous la forme de trois cadres côte à côte sans légende ; les légendes ci-dessus sont déduites de l'énoncé -->

### Exercice 8

(Algo + Python)

Soit "**chaines.txt**" un fichier de **N** chaînes de caractères non vides et dont la taille maximale est 5 caractères.

On se propose d'écrire un programme Python qui permet de :

1. Remplir le fichier "**chaines.txt**" par **N** chaînes ( 2<= **N** <=30)
2. A partir de fichier "**chaines.txt**", créer un fichier d'enregistrements dont le nom physique est "**chiffres.dat**" **Chaque** enregistrement comporte deux champs :
    - **N** (nombre extrait de chaîne existant dans chaque ligne de fichier texte)
    - **S** (Somme des chiffres du nombre **N**)
3. Afficher la somme des valeurs du champ **N** des enregistrements de fichier "*chiffres.dat* : Somme = 42 + 125 + 0 + 6574 = 6741.

<!-- TODO vérifier: la parenthèse et le guillemet fermants manquent après « chiffres.dat » à la question 3 dans l'original ; transcrit tel quel -->

**Exemple :**

Contenu du fichier "*chaines.txt*" :

> R4\*s2
> 12hj5
> G(y !
> 6574

Contenu du fichier "*chiffres.dat*" :

| Enregistrement | N | S |
|---|---|---|
| 0 | 42 | 6 |
| 1 | 125 | 8 |
| 2 | 0 | 0 |
| 3 | 6574 | 22 |

![Schéma reliant chaque ligne du fichier chaines.txt (R4*s2, 12hj5, G(y !, 6574) par une flèche à l'enregistrement correspondant du fichier chiffres.dat : 0- N=42 S=6, 1- N=125 S=8, 2- N=0 S=0, 3- N=6574 S=22](figures/serie2-ex8-chaines-chiffres.png)

<!-- TODO figure: à recréer -->

### Exercice 9

(Algo + Python)

- Un article est représenté par une fiche qui contient les informations suivantes :
    - **Nom** : désigne le nom de l'article commandé
    - **Qte** : désigne la quantité commandé
    - **Prix** : désigne le prix unitaire
    - **Etat** : booléen tel que vrai signifie payé et faux signifie pas encore
- "Commande.dat" est un fichier qui contient les informations des articles commandés.
- "Facture.txt" est un fichier texte

On veut écrire un programme qui permet de :

- Remplir "*commande.dat*" par des informations des articles, le remplissage se termine lorsque la réponse à la question "Continuer O/N" est **"N"**
- Remplir "*facture.txt*" par les informations des articles non payés telque chaque ligne contient les informations d'un seul article de la manière suivante : **nom   qte\*prix**

  La dernière ligne contient le total à payer : **total   valeur**

- Afficher le contenu de fichier "facture.txt"

**Exemple :**

Contenu de "*commande.dat*" :

| Nom | Qte | Prix | Etat |
|---|---|---|---|
| Souris | 12 | 14 | vrai |
| Clavier | 6 | 10 | faux |
| Imprimante | 2 | 60 | faux |
| Scanner | 3 | 45 | vrai |
| Micro-casque | 15 | 9 | faux |
| Webcam | 10 | 13 | faux |

<!-- TODO vérifier: dans le PDF, le contenu de commande.dat est un tableau de 6 colonnes (une par article) dont chaque colonne liste nom, quantité, prix, état sur quatre lignes ; reformaté en tableau d'une ligne par article (les intitulés de colonnes Nom/Qte/Prix/Etat sont déduits de l'énoncé) -->

Contenu "*facture.txt*" :

> Clavier 60
> Imprimante 120
> Micro-casque 135
> Webcam 130
> Total 445

**Travail demandé :**

- Donner les structures de données à utiliser
- Donner l'algorithme du programme principal (Modulaire)
- Donner l'algorithme de chaque module prévu

**N.B** les fichiers sont enregistrés sous le lecteur C:\

### Exercice 10

On se propose de créer un programme qui sera utilisé par un instituteur de l'enseignement primaire pour évaluer ses élèves dans le calcul d'une opération arithmétique et avoir des statistiques sur l'évolution du niveau de ses élèves.

Pour chaque élève, on détient les informations suivantes :

- **Nom** (chaine de 15 caractères au maximum), c'est le nom de l'élève.
- **Num** (entier de1 à 10), c'est le numéro de l'opération à calculer.
- **Op** (chaine de 50 caractères au maximum), c'est l'opération que l'élève doit évaluer. Cette opération sera prise à partir du fichier « **calcul.dat** » et correspond au numéro de l'opération.
- **Rep** (entier), c'est la réponse de l'élève à l'opération correspondante.

<u>N.B</u> : Vous n'êtes pas appelé à remplir le fichier « **calcul.dat** ».

Le fichier « **calcul.dat** » contient 10 enregistrements dont chacun est composée de deux champs

- Num (entier), c'est le numéro de l'opération
- Op (chaine de 50 caractères au maximum), c'est l'opération à calculer

On vous demande d'écrire un programme permettant de :

1. Remplir le fichier « **evaluer.dat** » par des élèves, la fin de la saisie est possible si nous répondons "O" (OUI) à la question "**Avez-vous terminé (O/N) ?**".
2. Remplir un fichier texte nommé « **stat.txt** » comportant au début les noms des élèves ayant répondu <u>correctement</u> à l'opération proposée (un par ligne) et à sa fin le pourcentage de ces élèves.

   <u>N.B</u> : Pour savoir si un élève a répondu correctement il faut calculer l'opération qu'il a choisi puis la comparer avec sa réponse.
3. Afficher le fichier « **Stat.txt** ».

**Exemple :**

Contenu de « Calcul.dat » :

| Num | Op |
|---|---|
| 1 | 9857+234+65 |
| 2 | 2376+7+333 |
| 3 | 87+3948+94 |
| 4 | 1+2+3+5987 |
| 5 | 97+346 |
| 6 | 2+20+3+4+786 |
| 7 | 75+974+852 |
| 8 | 853+246+985 |
| 9 | 147+268+379 |
| 10 | 2332+34+678 |

Contenu de « evaluer.dat » :

| Nom | Num | Op | Rep |
|---|---|---|---|
| Manel | 8 | 853+246+985 | 2084 |
| Salma | 3 | 87+3948+94 | 10 |
| Amine | 6 | 2+20+3+4+786 | 815 |
| Mohamed | 10 | 2332+34+678 | 3044 |
| nesrine | 4 | 1+2+3+5904 | 200 |
| Mourad | 5 | 97+346 | 350 |

Contenu de « Stat.txt » :

> Manel
> Amine
> Mohamed
> Pourcentage=50%

**Questions :**

1. Ecrire l'algorithme du programme principal et les algorithmes des modules envisagés.

**N.B** : les fichiers sont enregistrés dans "**C :\Bac2023**"

<!-- TODO vérifier: dans l'exemple, la ligne « nesrine 4 1+2+3+5904 200 » de evaluer.dat ne correspond pas à l'opération 4 de calcul.dat (1+2+3+5987) ; transcrit tel quel -->

### Exercice 11

Le conseil scientifique d'une institution est formé de m membres avec (10 ≤ **m** ≤ 20). Pour décider de l'achat de micro-ordinateurs, les membres du conseil effectuent un vote. Cette opération est informatisée. Chacun des membres exprime son avis par la saisie d'un seul caractère qui peut être :

- **F** ou **f** pour Favorable
- **D** ou **d** pour Défavorable
- **N** ou **n** pour Neutre

Les votes des membres seront sauvegardés dans un fichier « **Vote.dat** »

Chaque membre est caractérisé par :

- Numéro de **CIN** qui doit être composé seulement de 8 chiffres.
- **Nom** du membre (chaîne de 30 caractères)
- **Avis** (caractère).

On vous demande d'écrire un programme qui saisit les votes des membres et affichera la décision à prendre par le conseil sachant qu'elle est :

- « **Reportée** » si le pourcentage des neutres est strictement supérieur à 50 %, sinon elle est
- « **Acceptée** » si le pourcentage des favorables est strictement supérieur à celui des défavorables et
- « **Refusée** » dans le cas contraire.

Le récap de cette opération est enregistré dans un fichier texte intitulé « **Resultat.txt** » de la façon suivante :

- La première ligne contient : le mot « **\*\* Le résultat de vote \*\*** »
- La 2 éme : le mot « **Favorable** : » suivi d'un espace puis le nombre de vote favorable.
- La 3 éme : le mot « **Défavorable** : » suivi d'un espace puis le nombre de vote défavorable.
- La 4 éme : le mot « **Neutre** : » suivi d'un espace puis le nombre de vote neutre.
- La 5 éme : la décision prise par le conseil.

**N.B :** on suppose que tous les fichiers seront mis à la racine du lecteur **C :**

**Exemple :** Pour m = 7 nous saisissons les votes suivants, on obtient un fichier résultat comme suit

Contenu de Avis.dat :

| NCIN | Nom | Vote |
|---|---|---|
| 11111111 | Ahlem | D |
| 22222222 | Ahmed | f |
| 33333333 | Karim | D |
| 55555555 | wahid | F |
| 88888888 | sami | N |
| 99999999 | mariem | F |
| 11112222 | siwar | N |

Contenu de Résultat.txt :

> \*\* le résultat de vote \*\*
> Favorable : 3
> Défavorable : 2
> Neutre : 2
> **Décision : acceptée**

### Exercice 12

On se propose de remplir un fichier texte « **Nombre.txt** » par **N** lignes (3≤**N**≤10)

Chaque ligne contient un nombre compris entre **97** et **122** généré automatiquement par l'ordinateur.

La fonction **Aléa**(x,y) renvoie automatiquement un entier entre **x** et **y**.

On désire ensuite remplir un autre fichier « **caract_Nombre.dat** » contenant autant d'enregistrements que de lignes du fichier « **Nombre.txt** ».

Chaque enregistrement contient les informations suivantes :

- **Num** : contient le nombre du fichier « **Nombre.txt** »
- **Caract_min** : contient la lettre qui correspond au code Ascii du premier champ **Num**.
- **Caract_maj** : contient la conversion de **Caract_min** en Majuscule.
- **Nature** : contient la chaine « voyelle » ou bien la chaine « consonne » selon la nature de la lettre.

On désire finalement ajouter à la fin du fichier « **nombre.txt** » une ligne contenant la concaténation des lettres du fichier « **Caract_Nombre.dat** » (Les consonnes en majuscules et les voyelles en minuscules)

Pour visualiser la modification apportée au fichier « **Nombre.txt** », on vous demande de l'afficher
