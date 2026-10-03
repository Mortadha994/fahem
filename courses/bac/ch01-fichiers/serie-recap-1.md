---
niveau: bac
chapitre: 1
titre: Série Récap N° 1 : Les fichiers
type: serie
notions: fichiers typés, fichiers texte, fichiers d'enregistrements, création et remplissage, recherche dans un fichier, ajout suppression et modification, menu
source: Classroom — Série 1+2+3 Récap- Les fichiers (série Récap 1 les fichiers (série 1+2+3).pdf)
---

# Série Récap N° 1 : Les fichiers

<!-- TODO vérifier: le PDF (4 pages) est intitulé « Les fichiers — Série de Récap N°1 » ; la numérotation des exercices (1 à 6) est conservée telle quelle. Les mentions « (Algo + python) », « (Algo) » et « (sujet bac 2008 (12 pts)) » des titres d'exercices sont reprises en première ligne de l'énoncé ; l'exercice 1 n'a pas de mention -->

## Série d'exercices

### Exercice 1

Soit les déclarations suivantes :

**T.D.N.T**

```algorithme
TYPE
Chapitre = enregistrement
    Titre : chaine
    Nbpage : entier
Fin
Livre = enregistrement
    Nom : chaine
    Cours : chapitre
    Prix : réel
    Note : tableau de 3 réel
Fin
Fliv = fichier de livre
Fent = fichier d'entier
Tab = tableau de 50 chapitre
```

**T.D.O**

| Objet | Type/Nature |
|---|---|
| E | Livre |
| X | Booléen |
| C | Chapitre |
| T | Tab |
| Ft | Texte |
| Fl | Fliv |
| Fe | Fent |

1- Pour ses propositions, répondre par « **V** » (Vrai) ou « **F** » (Faux), justifier si la proposition est fausse : (**5 points**)

| Instruction |
|---|
| `Lire(E)` |
| `Ecrire(Fin_fichier(Fe)-3)` |
| `Lire(T[1].Cours.Titre)` |
| `Ecrire(Fe, E.Cours.Nbpage)` |
| `Ecrire_nl(Fl, E)` |
| `T ← C` |
| `Ecrire(Ft, Livre.Nom)` |
| `E.Note[3] ← 12 .5` |
| `Ecrire(sous_chaine(C.Titre, 3, 7))` |
| `Fin_fichier(Fe) ← X` |

<!-- grille de réponse supprimée -->

2- Complétez par les instructions algorithmiques correspondant aux traitements proposés. (**10 points**)

**N.B :**

- Le fichier contient **20** livres enregistré sous la racine **C**.
- Les instructions doivent inclurent **l'ouverture** et la **fermeture** des fichiers
- Ft → textes.txt | Fl → livres.dat | Fe → entiers.dat

Traitements à réaliser :

- Supprimer **les 3 derniers** livres du fichier **Fl** (contient 20 livres)
- Ajouter le nombre de page (NbPage) du premier livre de fichier Fl à la fin du fichier Fe
- Afficher le nom du livre qui occupe la position milieu du fichier Fl (contient 20 livres)
- Ajouter le mot « FIN » à la fin du fichier Ft

<!-- grille de réponse supprimée -->

### Exercice 2

(Algo + python)

Écrire un algorithme et un programme python qui permet de créer un fichier « **lettre.dat** » sur le disque « **c :** » dont :

- Le contenu est ensemble de caractères alphabétiques
- Le nombre d'éléments n'est pas connu d'avance, l'arrêt de saisie est réalisé lorsque l'utilisateur tape ''#''

Le programme doit assurer

- Mettre les voyelles dans un 1er fichier « **voyelles.dat** » et les consonnes dans un 2ème fichier « **consonnes.dat** »
- Afficher le fichier des voyelles ainsi que le nombre de voyelles se trouvant dans le fichier.
- Afficher le fichier des consonnes ainsi que le nombre de consonnes se trouvant dans le fichier.

### Exercice 3

(Algo + python)

Ecrire un programme qui permet de :

- Créer un fichier texte nommé « **fiche.txt** » sur « **c:\devoir** »
- Remplir le fichier jusqu'à donner le mot « **Fin** » qui ne sera pas stocké.
- Compter le nombre des mots dans le fichier sachant que la ligne est bien saisie (pas d'espace double, pas d'espace au début et pas d'espace à la fin).
- Afficher le résultat trouvé.

### Exercice 4

(Algo + python)

Écrire un algorithme et un programme qui permet de créer et de remplir un fichier « **FE** » sous la racine **c:\eleves.dat**, qui contient des informations sur les élèves d'un lycée

Chaque élève comporte :

- **Matricule** : chaine de 6 lettres.
- **Nom**, **Prénom** : chaines non vides d'au maximum 30 lettres.
- **Moyenne générale** : réel entre 0 et 20.

Puis afficher la liste des élèves de ce lycée dont la moyenne générale entre 16 et 20.

Écrire un module qui permet de chercher un élève dans le fichier « **FE** » à partir de sa matricule si l'élève est trouvé alors le programme affichera son **nom**, son **prénom**, sa moyenne, sinon il affichera le message « **élève non trouvé** ».

### Exercice 5

(sujet bac 2008 (12 pts)) (Algo)

Le directeur du lycée veut organiser les résultats du baccalauréat. Les données relatives au un résultat sont enregistrées dans un fichier typé intitulé **Bac.dat**. Il comporte N enregistrements relatifs aux n élèves. Chaque enregistrement comporte les informations suivantes :

- Num_CIN (chaîne de 8 chiffres)
- Nom (chaîne de 20 lettres)
- Prenom (chaîne de 20 lettres)
- Section (chaîne de 15 caractères)
- Moyenne_annuelle (réel entre 0 et 20)

On se propose d'écrire une application qui traite ces données pour produire deux nouveaux fichiers :

- Le premier, intitulé **resultat.dat**, contient n enregistrements comportant en plus des données précédentes, deux autres champs « moyenne_bac » et « admis » de types respectifs réel et booléen. Un élève est admis s'il possède une moyenne en bac supérieure ou égale à 10 sinon s'il possède une moyenne générale supérieur ou égale à 10 sachant que :

  **Moyenne générale = (2\*moyenne_bac + moyenne_annuelle)/3**

- Trier le fichier **resultat.dat** selon la moyenne du bac en ordre décroissant (tri par sélection)
- Le seconde fichier intitulé **details.txt** de type texte. Comporte :
  - Dans la première ligne : le nombre des élèves admis.
  - Dans la seconde ligne : le taux (%) de réussite des élèves. Sachant que le **Taux de réussite = (nombre admis\*100)/nombre des élèves**.
  - Dans la troisième ligne : le nom et le prénom de l'élève qui possède la meilleure moyenne suivie d'un espace puis leur moyenne et leur section.

**N.B :** on suppose que tous les fichiers seront mis à la racine du lecteur C.

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
