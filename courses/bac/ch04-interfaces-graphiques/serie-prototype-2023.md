---
niveau: bac
chapitre: 4
titre: Série N° 1 : Prototype Bac info 2023
type: serie
notions: interface graphique, PyQt5, fichiers typés, fichiers texte, Table Widget, List Widget, QMessageBox, chiffre de chance
source: Classroom — Prototype 2023 (prototype.pdf)
---

# Série N° 1 : Prototype Bac info 2023

<!-- TODO vérifier: le PDF (4 pages, « prototype.pdf », en-tête « Les Interfaces Graphiques ») contient deux énoncés : « Prototype Bac info 2023 » (pages 1 à 3) et « Application » (pages 3 et 4) ; ils sont rangés en Exercice 1 et Exercice 2, numérotation non présente dans le PDF. Le texte du PDF n'était pas extractible : transcrit à partir de captures d'écran -->

## Série d'exercices

### Exercice 1

**Prototype Bac info 2023 :**

Soit le fichier de données « **Clients.dat** » contenant des informations sur des clients. Chaque enregistrement de ce fichier se compose des champs suivants :

- **Identifiant** : une chaîne formée uniquement par des alphanumériques de longueur inférieure à 10 et qui désigne l'identifiant d'un client.
- **NTel** : une chaîne de 8 chiffres qui désigne le numéro de téléphone d'un client.
- **Ville** : une chaine qui désigne la ville d'un client.
- **Genre** : une chaîne qui désigne le genre d'un client "Masculin" ou "Féminin"
- **Etat** : une chaîne qui désigne l'état d'inscription d'un client "Inscrit" ou "Non Inscrit"

On se propose d'afficher les clients gagnants contenus dans le fichier « **Clients.dat** ». Un client est déclaré gagnant si le chiffre de chance **CC** de son numéro de téléphone existe dans un fichier « **Chance.txt** » déjà rempli par des chiffres.

Un chiffre de chance **CC** relatif à un numéro de téléphone est calculé en additionnant de façon répétitive tous les chiffres qui composent le numéro de téléphone jusqu'à obtenir un seul chiffre.

**Exemple :**

Pour les deux fichiers « Clients.dat » et « Chance.txt » suivants :

**Clients.dat**

| Identifiant | NTel | Ville | Genre | Etat |
|---|---|---|---|---|
| C01 | 65405003 | Tunis | Masculin | Non Inscrit |
| C02 | 49456241 | Béja | Féminin | Non Inscrit |
| Cf16 | 80617081 | Gafsa | Féminin | Inscrit |
| Cr09 | 09562444 | Tunis | Masculin | Inscrit |

**Chance.txt**

| Chiffre |
|---|
| 2 |
| 6 |
| 4 |
| 5 |
| 1 |
| 9 |

<!-- TODO vérifier: le tableau Chance.txt du PDF n'a pas d'en-tête de colonne (le fichier contient un chiffre par ligne) ; l'en-tête « Chiffre » est ajouté pour le tableau Markdown -->

Les clients gagnants sont :

- Identifiant : C01 – N° Téléphone : 65405003
- Identifiant : Cf16 – N° Téléphone : 80617081

En effet,

Le CC du client ayant l'identifiant **C01** a été obtenu en additionnant les chiffres de son numéro de téléphone jusqu'à obtenir un seul chiffre c'est à dire 6+5+4+0+5+0+0+3 = 23 → 2+3 =5. Le chiffre **5** figure dans le fichier « Chance.txt », donc c'est un client gagnant.

- Le CC du client ayant l'identifiant **C02** est 4+9+4+5+6+2+4+1=35 → 3+5=**8**. Le chiffre **8** ne figure pas dans le fichier « Chance.txt ».
- Le CC du client ayant l'identifiant **Cf16** est 8+0+6+1+7+0+8+1=31 → 3+1=**4**. Le chiffre **4** figure dans le fichier « Chance.txt », donc c'est un client gagnant.
- Le CC du client ayant l'identifiant **Cr09** est 0+9+5+6+2+4+4+4=34 → 3+4=**7**. Le chiffre **7** ne figure pas dans le fichier « Chance.txt ».

On se propose de concevoir une interface graphique contenant les éléments suivants :

- Un label contenant le texte : « *Identifiant* »
- Une zone de saisie permettant la saisie de l'identifiant d'un client
- Un label contenant le texte : « *Numéro de téléphone* »
- Une zone de saisie permettant la saisie de numéro de téléphone d'un client
- Un label contenant le texte : « *Genre* »
- Deux boutons Radios intitulés « *Masculin* » et « *Féminin* »
- Un label contenant le texte : « *Ville* »
- Une liste déroulante contenant les villes « *Tunis* », « *Béja* » et « *Gafsa* »
- Un label contenant le texte : « *Etat* »
- Une case à cocher intitulée « *Inscription* »
- Un bouton intitulé « *Ajouter* » permettant d'ajouter un client au fichier « *Client.dat* »
- Une List Widget pour afficher le contenu du fichier « *Chance.txt* »
- Un bouton intitulé « *Afficher Chance* »
- Une Table Widget contenant les colonnes « *Identifiant* », « *Numéro Tel* », « *Genre* », « *Ville* », « *Etat* » pour afficher le contenu du fichier « *Clients.dat* »
- Un bouton intitulé « *Afficher Clients* »
- Une List Widget pour afficher les clients gagnants
- Un bouton intitulé « *Afficher Gagnants* »

<!-- TODO vérifier: le PDF écrit « Client.dat » (au lieu de « Clients.dat ») dans la ligne du bouton « Ajouter » ; transcrit tel quel -->

**Travail demandé :**

1. Compléter l'interface graphique « **Interface_Prototype** » par les éléments présentés précédemment comme illustrée dans la figure suivante :

   ![Figure 1 : Interface Résultat. Fenêtre « Jeux de chance » avec les étiquettes Identifiant et Numéro de téléphone et leurs zones de saisie, Genre (boutons radio Masculin et Féminin), Ville (liste déroulante), Etat (case à cocher Inscription), deux listes vides à droite avec les boutons « Afficher Chance » et « Afficher Gagnants », les boutons « Ajouter » et « Afficher Clients » et un tableau aux colonnes Identifiant, N° Téléphone, Genre, Ville, Etat](figures/prototype-2023-figure-1.png)
   <!-- TODO figure: à recréer -->

2. Ouvrir le fichier nommé « **Prototype.py** » situé dans votre dossier de travail dans lequel vous apportez les modifications suivantes :
   - développer le module « ***ajouter*** », qui s'exécute suite à un clic sur le bouton « Ajouter », et permettant, lorsque toutes les contraintes sont respectées, d'ajouter un client au fichier « **Clients.dat** » sinon d'afficher, dans le cas contraire, un message d'alerte via « **QMessagebox** ».
   - développer le module « ***affchance*** », qui s'exécute suite à un clic sur le bouton « Afficher Chance », permettant d'afficher dans l'élément Liste Widget1, le contenu du fichier « Chance.txt »
   - développer le module « ***affclient*** », qui s'exécute suite à un clic sur le bouton « Afficher Clients », permettant d'afficher dans la table Widget, le contenu du fichier « **Clients.dat** »
   - développer le module « ***affgagnants*** », qui s'exécute suite à un clic sur le bouton « Afficher Gagnants », permettant d'afficher les clients gagnants dans l'élément List Widget 2
   - Compléter les instructions de la partie exploitation de l'interface graphique par les informations nécessaires à l'appel de l'interface « **Interface_Prototype** » et aux différents modules développés.

Ci-dessous quelques captures d'écran montrant des exemples d'exécutions :

![Figure 2 : Message d'erreur de champs vides. La fenêtre avec les champs Identifiant et Numéro de téléphone vides et une fenêtre d'erreur « Veuillez saisir toutes les informations » avec un bouton OK](figures/prototype-2023-figure-2.png)
<!-- TODO figure: à recréer -->

![Figure 3 : Message d'erreur d'un identifiant invalide. Identifiant « C7015 », numéro de téléphone « 12345678 » et une fenêtre d'erreur « Identifiant invalide » avec un bouton OK](figures/prototype-2023-figure-3.png)
<!-- TODO figure: à recréer -->

![Figure 4 : Message d'erreur d'un numéro de téléphone invalide. Identifiant « C015 », numéro de téléphone « 12345 » et une fenêtre d'erreur « N° de téléphone invalide » avec un bouton OK](figures/prototype-2023-figure-4.png)
<!-- TODO figure: à recréer -->

![Figure 5 : Affichage des clients. La fenêtre « Jeux de chance » avec le tableau rempli des quatre clients du fichier Clients.dat, listes de droite vides](figures/prototype-2023-figure-5.png)
<!-- TODO figure: à recréer -->

![Figure 6 : Affichage du contenu du fichier « Chance.txt » et des clients gagnants. La fenêtre « Jeux de chance » avec la liste des chiffres de Chance.txt, la liste des clients gagnants (C01 – 65405003 et Cf16 – 80617081) et le tableau des clients](figures/prototype-2023-figure-6.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: le texte dans les captures d'écran (figures 2 à 6) est très petit ; seuls les messages d'erreur et les valeurs de saisie lisibles ont été décrits -->

### Exercice 2

**Application :**

Pour chercher le chiffre de chance d'une personne, en procède comme suit : on additionne les chiffres composants la date de naissance de la personne concerné. Au nombre obtenu, on refait le même procédé jusqu'à obtenir un nombre composé d'un seul chiffre.

**Travail demandé :**

On se propose de concevoir une interface graphique contenant les éléments suivants :

- Un label contenant le texte : « **Chiffre de chance** »
- Un label demandant la saisie d'un nom « **Donner votre nom :** »
- Un label demandant la saisie d'un prénom « **Donner votre prénom :** »
- Un label demandant la saisie d'une date de naissance « **Donner votre date de naissance :** »
- Une zone de saisie permettant la saisie du nom. « **nom** »
- Une zone de saisie permettant la saisie du prénom. « **prenom** »
- Une zone de saisie permettant la saisie de la date. « **date** »
- Un label pour afficher le chiffre de la chance. « **res** »
- Un bouton intitulé « **Quitter** ».
- Un bouton intitulé « **Effacer** ». : permet de vider les champs
- Un bouton intitulé « **Calculer** ». « **b1** » : permet de calculer le chiffre de la chance et remplir le fichier « **chance.dat** » par les informations du formulaire.
- Un bouton intitulé « **Afficher** ». « **b2** » permet d'afficher le contenu du fichier dans une table widget « **table** » trié en ordre croissant selon le chiffre de la chance.

**N.B :**

- Le **nom** et le **prénom** doit être des chaines non vides, alphabétiques, contient un seul espace au maximum et ne dépassent pas les 30 caractères.
- Le champ **date** doit être de la forme "jj/mm/aaaa" où **jj** ∈ [01..31], **mm** ∈ [01..12] et **aaaa** ∈ [1900..2023]
- Pour chaque opération d'affichage, la table se rétablir avant l'affichage.

![Fenêtre « Chiffre de chance » (titre TuTo Academy) avec les champs Donner votre nom, Donner votre prénom, Donner votre date de naissance, l'étiquette Chiffre de chance, les boutons Calculer, Afficher, Effacer, Quitter et un tableau aux colonnes Nom, Prenom, Date, Chiffre de chance](figures/prototype-2023-chiffre-de-chance-interface.png)
<!-- TODO figure: à recréer -->

![Exemples d'exécution de l'application « Chiffre de chance » : fenêtres d'erreur (le Nom/Prénom doit être alphabétique ; Vérifier ... ; message sur la date) et la fenêtre avec le tableau affiché : Ben Aissa Mohamed 12/10/1996 chiffre 2, Ben Ammar Tarek 02/10/1991 chiffre 5, Attia Youssef 20/06/1996 chiffre 6](figures/prototype-2023-chiffre-de-chance-executions.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: l'énoncé mentionne le fichier « chance.dat » (extension .dat) alors que l'Exercice 1 utilise « Chance.txt » ; transcrit tel quel. Les captures d'exécution se chevauchent dans le PDF : seul un message d'erreur est entièrement lisible (« le Nom/Prénom doit être alphabétique ! »), les autres sont partiellement masqués -->
