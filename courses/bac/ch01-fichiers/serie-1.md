---
niveau: bac
chapitre: 1
titre: Série N° 1 : Les fichiers
type: serie
notions: fichiers typés, fichiers texte, fichiers d'enregistrements, création et remplissage, recherche dans un fichier, ajout suppression et modification, menu
source: Classroom — Série 1+2+3 Normal - Les fichiers (série 1 les fichiers.pdf)
---

# Série N° 1 : Les fichiers

<!-- TODO vérifier: le PDF (2 pages) est intitulé « Les fichiers Série N°1 » ; la numérotation des exercices (1 à 6) est conservée telle quelle. Les mentions « (Algo + python) », « (Algo) » et « (sujet bac 2008 (12 pts)) » des titres d'exercices sont reprises en première ligne de l'énoncé ; l'exercice 4 n'a pas de mention -->

## Série d'exercices

### Exercice 1

(Algo + python)

Écrire un algorithme et un programme python qui permet de créer un fichier « **lettre.dat** » sur le disque « **c :** » dont :

- Le contenu est ensemble de caractères alphabétiques
- Le nombre d'éléments n'est pas connu d'avance, l'arrêt de saisie est réalisé lorsque l'utilisateur tape "#"

Le programme doit assurer :

- Mettre les voyelles dans un 1er fichier « **voyelles.dat** » et les consonnes dans un 2ème fichier « **consonnes.dat** »
- Afficher le fichier des voyelles ainsi que le nombre de voyelles se trouvant dans le fichier.
- Afficher le fichier des consonnes ainsi que le nombre de consonnes se trouvant dans le fichier.

### Exercice 2

(Algo + python)

Écrire un algorithme et un programme qui permet de créer et de remplir un fichier « **FE** » sous la racine **c:\eleves.dat**, qui contient des informations sur les élèves d'un lycée

Chaque élève comporte :

- **Matricule** : chaine de 6 lettres.
- **Nom**, **Prénom** : chaines non vides d'au maximum 30 lettres.
- **Moyenne générale** : réel entre 0 et 20.

Puis afficher la liste des élèves de ce lycée dont la moyenne générale entre 16 et 20.

Écrire un module qui permet de chercher un élève dans le fichier « **FE** » à partir de sa matricule si l'élève est trouvé alors le programme affichera son **nom**, son **prénom**, sa moyenne, sinon il affichera le message « **élève non trouvé** ».

### Exercice 3

(Algo + python)

Une bibliothèque désire informatiser la gestion de ses livres. Elle détient pour chaque livre les informations suivantes :

- Num : représentant le numéro d'un livre rempli automatiquement (1 pour le 1er et 2 pour 2ème ...)
- Titre : représentant le titre d'un livre (chaîne de 50 caractères maximum).
- Nom_aut : représentant le nom de l'auteur d'un livre (chaîne de 10 caractères maximum).
- Nom_edit : représentant le nom de l'éditeur d'un livre (chaîne de 20 caractères maximum).
- Année : représentant l'année de publication d'un livre (Année ≤ 2022).

Pour ceci on se propose de saisir les enregistrements de n livres (2 ≤ n ≤ 40) dans un fichier nommé « **bibliothéque.fch** ».

Saisir une année et déterminer et afficher les enregistrements des livres publiés donnée.

### Exercice 4

Ecrire un programme qui permet de :

- Créer un fichier texte nommé « **fiche.txt** » sur « **c:\devoir** »
- Remplir le fichier jusqu'à donner le mot « **Fin** » qui ne sera pas stocké.
- Compter le nombre des mots dans le fichier sachant que la ligne est bien saisie (pas d'espace double, pas d'espace au début et pas d'espace à la fin).
- Afficher le résultat trouvé.

### Exercice 5

(sujet bac 2008 (12 pts)) (Algo)

Les données relatives à un concours sont enregistrées dans un fichier de type intitulé « **concours.dat** ». Il comporte n enregistrements relatifs aux n candidats. Chaque enregistrement comporte dans cet ordre :

- Numéro (entier)
- Nom (chaîne de 30 caractères)
- Prénom (chaîne de 30 caractères)
- Matière1 (chaîne de 20 caractères)
- Note1 (réel)
- Matière2 (chaîne de 20 caractères)
- Note2 (réel)
- Matière3 (chaîne de 20 caractères)
- Note3 (réel)

**Notei** est la note obtenue par un candidat dans la matière **Matièrei.**

On se propose d'écrire une application qui trait ces données pour produire deux nouveaux fichiers. Le premier intitulé « **resultat.dat** », contient n enregistrements comportant en plus des données précédentes, deux autres champs moyenne et rang de types respectifs réel et entier. Les enregistrements de ce fichier sont classés par ordre de mérite c.-à-d. suivant un tri décroissant sur les moyennes. La moyenne d'un candidat est calculée comme suit :

**(1\*note1 + 2\*note2+2\*note3)/5**

Le seconde fichier intitulé « **details.txt** » de type texte, comporte :

- Dans 1ère ligne : le nombre d'admis (moyenne ≥ 10)
- Dans 2ème ligne : la meilleure note dans **matière1** suivie d'un espace puis du nombre de candidats ayant eu **note1** ≥ 10.
- Dans 3ème ligne : la meilleure note dans **matière2** suivie d'un espace puis du nombre de candidats ayant eu **note2** ≥ 10.
- Dans 4ème ligne : la meilleure note dans **matière3** suivie d'un espace puis du nombre de candidats ayant eu **note3** ≥ 10.

**N.B :** on suppose que tous les fichiers seront mis à la racine de lecture C.

### Exercice 6

(Algo + python)

Écrire un programme, qui crée sur la partition « **C:** » le fichier « **clients.dat** » contenant les données relatives aux comptes de clients de « **Essentiel banque** ».

Un compte clients est caractérisé par :

- Un numéro : entier positif, attribué automatique par l'ordinateur.
- Un nom : chaîne de 20 caractères au maximum.
- Un prénom : chaîne de 20 caractères au maximum.
- Un solde : réel.

Le programme assure les requêtes suivantes :

1. L'ajout d'un nouveau client à la fin du fichier.
2. La suppression d'un client choisi par son numéro de compte.
3. La modification du solde d'un client
4. L'affichage des données d'un client suite à la saisie de son numéro de compte avec l'affichage de l'expression « **débiteur** » pour celui qui a un solde < 0 ou « **créditeur** » dans le cas contraire.
5. L'affichage des données de tous les clients.

**N.B :**

- La création ne doit pas être réalisé que si le fichier est inexistant !
- Il est préféré d'utiliser un menu laissant le choix à l'utilisateur d'exécuter la tâche dont il aura besoin autant de fois qu'il le souhaite.
