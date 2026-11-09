---
niveau: bac
chapitre: 1
titre: Série Récap N° 2 : Les fichiers
type: serie
notions: fichiers typés, fichiers texte, fichiers d'enregistrements, création et remplissage, recherche dans un fichier, ajout suppression et modification, menu
source: Classroom — Série 1+2+3 Récap- Les fichiers (série Récap 2 les fichiers (série 1+2+3).pdf)
---

# Série Récap N° 2 : Les fichiers

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Les fichiers — Série de Récap N°2 » ; la numérotation des exercices (9 à 16) est conservée telle quelle (elle continue celle de la série Récap N°1). Les mentions « (Algo + Python) », « (Algo) » et « (Bac 2020C) » des titres sont reprises en première ligne de l'énoncé -->

## Série d'exercices

### Exercice 9

(Algo + Python)

Un article est représenté par une fiche qui contient les informations suivantes :

- **Nom** : désigne le nom de l'article commandé
- **Qte** : désigne la quantité commandé
- **Prix** : désigne le prix unitaire
- **Etat** : booléen tel que vrai signifie payé et faux signifie pas encore

"Commande.dat" est un fichier qui contient les informations des articles commandés.

"Facture.txt" est un fichier texte

On veut écrire un programme qui permet de :

- Remplir "*commande.dat*" par des informations des articles, le remplissage se termine lorsque la réponse à la question "Continuer O/N" est "**N**"
- Remplir "*facture.txt*" par les informations des articles non payés telque chaque ligne contient les informations d'un seul article de la manière suivante : **nom qte\*prix**. La dernière ligne contient le total à payer : **total valeur**
- Afficher le contenu de fichier "facture.txt"

**Exemple :**

Contenu de "*commande.dat*" (chaque colonne est un article : nom, quantité, prix, état)

| Souris | Clavier | Imprimante | Scanner | Micro-casque | Webcam |
|---|---|---|---|---|---|
| 12 | 6 | 2 | 3 | 15 | 10 |
| 14 | 10 | 60 | 45 | 9 | 13 |
| vrai | faux | faux | vrai | faux | faux |

<!-- TODO vérifier: dans le PDF, le tableau est présenté en deux lignes de nombres puis une ligne d'états sous la ligne des noms ; la disposition « une colonne par article » est reprise telle quelle -->

Contenu "*facture.txt*"

> Clavier 60
> Imprimante 120
> Micro-casque 135
> Webcam 130
> **Total 445**

**Travail demandé :**

- Donner les structures de données à utiliser
- Donner l'algorithme du programme principal (Modulaire)
- Donner l'algorithme de chaque module prévu

**N.B** les fichiers sont enregistrés sous le lecteur C:\

### Exercice 10

(Algo + Python)

On se propose de remplir un fichier texte « **Nombre.txt** » par N lignes (3≤N≤10)

Chaque ligne contient un nombre compris entre 97 et 122 généré automatiquement par l'ordinateur.

La fonction Aléa(x,y) renvoie automatiquement un entier entre x et y.

On désire ensuite remplir un autre fichier « **caract_Nombre.dat** » contenant autant d'enregistrements que de lignes du fichier « **Nombre.txt** ».

Chaque enregistrement contient les informations suivantes :

- **Num** : contient le nombre du fichier « Nombre.txt »
- **Caract_min** : contient la lettre qui correspond au code Ascii du premier champ Num.
- **Caract_maj** : contient la conversion de Caract_min en Majuscule.
- **Nature** : contient la chaine « voyelle » ou bien la chaine « consonne » selon la nature de la lettre.

On désire finalement ajouter à la fin du fichier « **nombre.txt** » une ligne contenant la concaténation des lettres du fichier « **Caract_Nombre.dat** » (Les consonnes en majuscules et les voyelles en minuscules)

Pour visualiser la modification apportée au fichier « **Nombre.txt** », on vous demande de l'afficher

### Exercice 11

(Algo + Python)

Le conseil scientifique d'une institution est formé de m membres avec (6 ≤ m ≤ 20). Pour décider de l'achat de micro-ordinateurs, les membres du conseil effectuent un vote. Cette opération est informatisée. Chacun des membres exprime son avis par la saisie d'un seul caractère qui peut être :

- **F** ou **f** pour Favorable
- **D** ou **d** pour Défavorable
- **N** ou **n** pour Neutre

Les votes des membres seront sauvegardés dans un fichier « **Vote.dat** »

Chaque membre est caractérisé par :

- Numéro de CIN qui doit être composé seulement de 8 chiffres.
- Nom du membre (chaîne de 30 caractères)
- Avis (caractère).

On vous demande d'écrire un programme qui saisit les votes des membres et affichera la décision à prendre par le conseil sachant qu'elle est :

« **Reportée** » si le pourcentage des neutres est strictement supérieur à 50 %, sinon elle est « **Acceptée** » si le pourcentage des favorables est strictement supérieur à celui des défavorables et « **Refusée** » dans le cas contraire.

Le récup de cette opération est enregistré dans un fichier texte intitulé « **Resultat.txt** » de la façon suivante :

- La première ligne contient : le mot « **\*\* Le résultat de vote \*\*** »
- La 2 éme : le mot « **Favorable :** » suivi d'un espace puis le nombre de vote favorable.
- La 3 éme : le mot « **Défavorable :** » suivi d'un espace puis le nombre de vote défavorable.
- La 4 éme : le mot « **Neutre :** » suivi d'un espace puis le nombre de vote neutre.
- La 5 éme : la décision prise par le conseil.

**N.B :** on suppose que tous les fichiers seront mis à la racine du lecteur **C :**

**Exemple :** Pour m = 7 nous saisissons les votes suivants, on obtient un fichier résultat comme suit

Fichier *Avis.dat* :

| NCIN | Nom | Vote |
|---|---|---|
| 11111111 | Ahlem | D |
| 22222222 | Ahmed | f |
| 33333333 | Karim | D |
| 55555555 | wahid | F |
| 88888888 | sami | N |
| 99999999 | mariem | F |
| 11112222 | siwar | N |

Fichier *Résultat.txt* :

> \*\* le résultat de vote \*\*
> Favorable : 3
> Défavorable : 2
> Neutre : 2
> **Décision : acceptée**

<!-- TODO vérifier: l'énoncé parle de « Vote.dat » et de « Avis.dat » (légende de l'exemple) pour le même fichier ; transcrit tel quel -->

### Exercice 12

(Algo)

On se propose de créer un programme qui sera utilisé par un instituteur de l'enseignement primaire pour évaluer ses élèves dans le calcul d'une opération arithmétique et avoir des statistiques sur l'évolution du niveau de ses élèves.

Pour chaque élève, on détient les informations suivantes :

- **Nom** (chaine de 15 caractères au maximum), c'est le nom de l'élève.
- **Num** (entier de 1 à 10), c'est le numéro de l'opération à calculer.
- **Op** (chaine de 50 caractères au maximum), c'est l'opération que l'élève doit évaluer. Cette opération sera prise à partir du fichier « calcul.dat » et correspond au numéro de l'opération.
- **Rep** (entier), c'est la réponse de l'élève à l'opération correspondante.

**N.B :** Vous n'êtes pas appelé à remplir le fichier « **calcul.dat** ».

Le fichier « **calcul.dat** » contient 10 enregistrements dont chacun est composée de deux champs

- **Num** (entier), c'est le numéro de l'opération
- **Op** (chaine de 50 caractères au maximum), c'est l'opération à calculer

On vous demande d'écrire un programme permettant de :

1. Remplir le fichier « **evaluer.dat** » par des élèves, la fin de la saisie est possible si nous répondons "O" (OUI) à la question "**Avez-vous terminé (O/N) ?**".
2. Remplir un fichier texte nommé « **stat.txt** » comportant au début les noms des élèves ayant répondu correctement à l'opération proposée (un par ligne) et à sa fin le pourcentage de ces élèves.

   **N.B :** Pour savoir si un élève a répondu correctement il faut calculer l'opération qu'il a choisi puis la comparer avec sa réponse.
3. Afficher le fichier « **Stat.txt** ».

**Exemple :**

« Calcul.dat »

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

« evaluer.dat »

| Nom | Num | Op | Rep |
|---|---|---|---|
| Manel | 8 | 853+246+985 | 2084 |
| Salma | 3 | 87+3948+94 | 10 |
| Amine | 6 | 2+20+3+4+786 | 815 |
| Mohamed | 10 | 2332+34+678 | 3044 |
| nesrine | 4 | 1+2+3+5904 | 200 |
| Mourad | 5 | 97+346 | 350 |

« Stat.txt »

> Manel
> Amine
> Mohamed
> Pourcentage=50%

<!-- TODO vérifier: les en-têtes de colonnes du tableau « evaluer.dat » (Nom, Num, Op, Rep) sont ajoutés d'après l'énoncé ; le PDF n'en affiche pas. Dans « Calcul.dat », la ligne 4 est « 1+2+3+5987 » alors que « evaluer.dat » contient « 1+2+3+5904 » pour l'opération 4 : transcrit tel quel -->

**Questions :**

1. Ecrire l'algorithme du programme principal et les algorithmes des modules envisagés.

**N .B :** les fichiers sont enregistrés dans "**C :\Bac2024**"

### Exercice 13

(Algo + Python)

Soit à remplir un Fichier texte Fe par des lignes, la saisie se termine en répondant par « N » à la question "continuer O/N?".

Une fois on a rempli le fichier le programme doit copier le contenue du fichier fe vers un deuxième fichier fs de telle sorte qu'il convertit tous les lettres se trouvant après un point "." en majuscule.

Exemple (contenu de Fe, puis contenu de Fs) :

| Fe | Fs |
|---|---|
| On a bac Sc.info, bac Sc.exp. | On a bac Sc.Info, bac Sc.Exp. |
| Fichier texte.fichier des enregistrements. | Fichier texte.Fichier des enregistrements. |
| Algo.pascal. | Algo.Pascal. |

<!-- TODO vérifier: les en-têtes « Fe » et « Fs » du tableau sont ajoutés ; le PDF présente deux blocs côte à côte sans titre -->

### Exercice 14

(Algo + Python)

On dispose d'un fichier texte, intitulé **source.txt**.

Un tautogramme est texte dont les mots commencent par la même lettre (sans distinction entre majuscule ou minuscule). **Exemple :** le lion lape le lait lentement.

On se propose de sauvegarder toutes les lignes tautogrammes de ce fichier, dans un dans un 2ème fichier intitulé **tauto.txt**

### Exercice 15

(Algo + Python)

Soit **F** un fichier texte contenant un certain nombre des lignes, écrire l'algorithme du module intitulé **Former** qui permet de former un nouveau fichier texte **F2**, contenant dans chaque ligne la concaténation des voyelles (minuscules et majuscules) figurants dans chaque ligne de **F**.

### Exercice 16

(Bac 2020C) (Algo + Python)

On se propose de nettoyer un fichier texte ''**Source.txt**'' pour générer un fichier ''**Resultat.txt**'', en respectant les règles suivantes :

- Le texte ne doit pas comporter des espaces successifs
- Si une ligne de texte commence par une lettre, cette dernière doit être en majuscule
- Avant un point ou une virgule il n'y a pas d'espace
- Après un point, il doit y avoir un espace et s'il est suivi d'une lettre elle doit être en majuscule, à l'exception du point qui peut se trouver à la fin d'une ligne

**Exemple :**

Pour le fichier ''**Source.txt**'' suivant :

![Capture du Bloc-notes montrant le fichier Source.txt : 4 lignes de texte avec des espaces multiples et des espaces avant les points et virgules](figures/serie-recap-2-source-txt.png)
<!-- TODO figure: à recréer -->

Après nettoyage des lignes du fichier ''**Source.txt**'', le fichier ''**Resultat.txt**'' sera :

![Capture du Bloc-notes montrant le fichier Resultat.txt : 4 lignes nettoyées (« Fichier Edition Format Affichage ? », « Un fichier est un ensemble de données. Ces données sont stockées sur un support d'enregistrement. », « L'accès à un fichier peut se faire de deux façons , séquentiel ou direct. », « Le contenu d'un fichier texte représente une suite de caractères »)](figures/serie-recap-2-resultat-txt.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: contenu des captures lu sur une image de faible résolution ; les espaces exacts du fichier Source.txt (illisibles) et la ligne « Fichier Edition Format Affichage ? » (barre de menu du Bloc-notes copiée dans le texte) sont à contrôler -->

**Travail demandé :**

1. Donner une instruction d'association pour chacun de deux fichiers ''**Source.txt**'' et ''**Resultat.txt**'' respectivement aux variables logiques **S** et **R**, sachant que les deux fichiers sont enregistrés sur la racine du disque **D**.
2. Ecrire un module nommé **Nettoi_F** que permet à partir d'un fichier ''**Source.txt**'' déjà saisi dans le programme appelant, de créer et de générer un deuxième fichier ''**Resultat.txt**'' en respectant les règles décrites précédemment.
