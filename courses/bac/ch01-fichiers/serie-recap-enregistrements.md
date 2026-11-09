---
niveau: bac
chapitre: 1
titre: Série de récap N°1 : Les enregistrements
type: serie
notions: enregistrements, structure Info, tableaux d'enregistrements, tri par sélection, modules, menu, dates (j/m/a)
source: Classroom — Bac info - Série de récap - Les Enregistrements (série 1 enregistrement.pdf)
---

# Série N°1 : Les enregistrements

<!-- TODO vérifier: PDF de 2 pages intitulé « Série N°1 : Les enregistrements » (post Classroom « Bac info - Série de récap - Les Enregistrements »), 10 exercices, numérotation d'origine conservée. Les mentions « (Algorithme et Python) », « (Algorithme) », « (Python) » des titres d'exercices sont reprises en première ligne de l'énoncé ; les exercices 8 n'en ont pas. Aucun code ni figure dans ce PDF. Le niveau (bac) est celui annoncé par le titre du post ; le contenu (enregistrements) correspond aussi à un chapitre 3ème « Les enregistrements » -->

## Série d'exercices

### Exercice 1

(Algorithme et Python)

Écrire un programme qui permet de déterminer les coordonnées d'un point S, représentant la symétrie d'un point P dans un plan à deux dimensions.

Le point P est caractérisé deux coordonnées (x, y).

### Exercice 2

(Algorithme et Python)

Soit la structure **Info** constituée par le **nom** (chaîne de 30 caractères maximum), le **numéro de téléphone** (10 caractères maximum), le **numéro de carte bancaire** (entier non signé).

Écrivez un programme qui saisit puis affiche les enregistrements pour 3 personnes.

### Exercice 3

(Algorithme et Python)

Écrire un programme qui saisit deux personnes puis afficher la personne la plus âgée sachant qu'une personne est caractérisée par un **nom**, **prénom** et **date** de naissance est un enregistrement composé de **j**, **m** et **a**. avec j compris entre 1 et 31 et m entre 1 et 12.

### Exercice 4

(Algorithme)

Un élève est caractérisé par les données suivantes :

- **Nom** : chaîne [20], commençant par une lettre en majuscule.
- **Prénom** : chaîne [20], commençant par une lettre en majuscule.
- **Age** : entier de 6 à 22 ans
- **Moyenne** : Réel entre 0 et 20

Écrire un algorithme qui permet de saisir les données relatives à un **élève** et les afficher.

### Exercice 5

(Algorithme)

Exercice 4 avec une classe de **N** élèves (5 ≤ N ≤ 35).

### Exercice 6

(Python)

Faire la traduction en python, des algorithmes obtenus au niveau de l'exercice n°5 en ajoutant les modules suivants :

Module 1 : un sous-programme permettant d'afficher les noms et les prénoms des élèves ayant les moyenne ≥ 12.

Modules 2 : un sous-programme permettant de déterminer le nombre d'élèves refusés (leurs moyennes < 10).

### Exercice 7

(Algorithme et Python)

Écrire un algorithme d'un programme intitulé « Entreprise » qui permet de saisir les données relatives à ses employés et d'afficher le nombre des employés qui ont un salaire entre 550 DT et 1000 DT et qui une catégorie donnée par l'utilisateur.

Sachant qu'un employé est caractérisé par :

- **Code** : chaine de 5 caractères (les deux premiers caractères sont des lettres et les 3 autres sont des chiffres obligatoirement)
- **NomPrenom** : chaine de 50 caractères
- **Catégorie** : chaine de 10 caractères (les catégories acceptées sont : "technicien", "ingenieur", "directeur")
- **Salaire** : réel compris entre 400 et 5000

<!-- TODO vérifier: « et qui une catégorie donnée par l'utilisateur » (verbe manquant dans le PDF, transcrit tel quel) -->

### Exercice 8

Écrire un programme qui permet de saisir N médicaments (avec N comprise entre 2 et 10), puis afficher les noms des médicaments périmés après une date d'expiration saisie au clavier (j/m/a).

Sachant qu'un médicament est caractérisé par un code, nom, date de fabrication (j/m/a) et **date d'expiration** (j/m/a)

### Exercice 9

(Algorithme et Python)

On veut écrire un programme modulaire nommé « Concours » pour gérer les moyennes des élèves d'une classe, sachant qu'un élève est caractérisé par :

- Un nom : chaîne de 20 caractères au maximum
- Un prénom : chaîne de 20 caractères au maximum
- Une moyenne : Réel
- Un rang : entier non signé
- Une mention : chaîne de 10 caractères au maximum

On désire :

- Saisir toutes les données de N élèves
- Trier les élèves selon leurs moyennes :
    - Tri par sélection
    - Ordre décroissant
- Afficher tous les élèves classés en ordre décroissant selon leurs moyennes.
- Affecter la mention correspondante à chaque élève :
    - « Très bien » si la moyenne ≥ 14
    - « Bien » si 12 ≤ moyenne < 14
    - « Passable » si 10 ≤ moyenne < 12
    - « Redouble » si moyenne < 10
- Calculer et afficher la moyenne générale de la classe.
- Calculer et afficher le pourcentage et le nombre des élèves qui ont une moyenne supérieure ou égale à la moyenne générale de la classe.
- Affecter à chaque élève son rang selon la moyenne.
- Afficher les données de l'élève correspond à un rang saisi.

**Questions :**

1) Analyser ce problème en le décomposant en modules.
2) Déduire les algorithmes des modules envisagés.
3) Traduire ce programme en python

### Exercice 10

(Python)

On considère une entreprise commerciale spécialisée dans la vente d'articles scolaires, l'entreprise effectue ses achats chez des fournisseurs producteurs, et revend ses articles aux clients revendeurs.

Chaque article est défini par :

- **Code article** : chaîne de 4 caractères commencent obligatoirement par une lettre majuscule, les 3 derniers caractères sont obligatoirement des chiffres.
- **Libelle** (le nom d'article) : chaîne 30
- **Quantité de stock** : entier no signé
- **Prix unitaire d'achat** : réel
- **Prix unitaire de vente** : réel

Faire un programme python qui saisit la liste des articles dans un tableau (au maximum 150 articles), puis choisir un traitement à faire selon le menu suivant :

1. liste des produits
2. liste de produit à commander
3. liste des produits représentant le plus Max des bénéfices

- Notons qu'on doit commander un article lorsque la quantité en stock est <= 10
- Une fois qu'une action est réalisée, et tant que l'utilisateur ne choisit pas 0 (Quitter), alors ce dernier peut demander un autre traitement propose par le menu.

<!-- TODO vérifier: la dernière phrase du PDF (« …propose par le menu ») et la 3ème entrée du menu (« le plus Max des bénéfices ») sont transcrites telles quelles -->
