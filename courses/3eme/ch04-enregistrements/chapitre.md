---
niveau: 3eme
chapitre: 4
titre: Les enregistrements
type: cours
notions: définition d'un enregistrement, déclaration d'un enregistrement, affectation d'un champ, lecture d'un champ, écriture d'un champ, vecteur d'enregistrements
source: Classroom — Chapitre 4 : Les enregistrements
---

# Chapitre 4 : Les enregistrements

<!-- TODO vérifier: le PDF (4 pages) s'intitule « Les enregistrements et les fichiers » avec une partie « A. Les Enregistrements » ; aucune partie « B » (fichiers) n'existe dans le PDF. La lettre « A. » n'est pas reprise comme titre pour garder la hiérarchie I., II., ... -->

## I. Définition

Un enregistrement est un type de données défini par l'utilisateur et qui permet de grouper un nombre fini d'éléments (ou champs) de types éventuellement différents.

## 📌 II. Déclaration

### Déclaration d'une structure enregistrement

**En algorithmique :**

Puisque l'enregistrement est un nouveau type, on commence par sa déclaration :

Tableau de déclaration des nouveaux types

```algorithme
T.D.N.T
Type
Nom_type = Enregistrement
    champ 1 : Type 1
    - - - -
    champ n : Type n
Fin
```

Puis la déclaration des objets (variables) utilisant ce type

| Objet | Type / Nature |
|---|---|
| identificateur_objet | Nom_type |

**En Python :**

```python
Nom_type ={
    "champ_1" : type_1,
    - - - -
    "champ_n" : type_n
}

identificateur_objet = dict(Nom_type)
```

## III. Utilisation

### 📌 Utilisation pour une action d'affectation

L'affectation de valeurs aux différents champs d'une variable de type enregistrement se fait par une opération de type :

```algorithme
variable.champ ← valeur
```

```python
Variable["champ"] = valeur
```

**Exemple :**

**En algorithmique :**

```algorithme
T.D.N.T
Type
Fiche = enregistrement
    nom, prénom : Chaîne
    sexe : Caractère
    numéro : Entier
    moyenne : Réel
    num_cin : Entier
Fin
```

| Objet | Type / Nature |
|---|---|
| Elève | Fiche |

Affectation de valeurs à cette variable :

```algorithme
élève.nom ← "Swidi"
élève.prénom ← "Basma"
élève.sexe ← "F"
élève.numéro ← 18
élève.moyenne ← 13.25
élève.num_cin ← 12345678
```

**En Python :**

Le type enregistrement.

```python
Fiche={
    "nom" :str(),
    "prenom" : str(),
    "sexe" : str(),
    "numero" : int(),
    "moyenne" : float(),
    "num_cin" : int()
}

eleve = dict(Fiche)
```

Affectation des valeurs à cette variable :

```python
eleve["nom"] = "Swidi"
eleve["prenom"] = "Basma"
eleve["sexe"] = "F"
eleve["numero"] = 18
eleve["moyenne"] = 13.25
eleve["num_cin"] = 12345678
```

<!-- TODO vérifier: dans le PDF, le tableau T.D.O déclare « Elève » (majuscule) alors que l'algorithme utilise « élève » ; transcrit tel quel -->

### 📌 Utilisation pour une action de lecture

```algorithme
Lire (variable.champ)
```

```python
Variable["champ"]=TYPE(input("MSG"))
```

**Exemple :**

Au niveau de l'algorithme :

```algorithme
Ecrire ("Entrer le nom de l'élève : ") , Lire (élève.nom)
```

Au niveau du Python :

```python
eleve["nom"] = str(input ("Entrer le nom de l'élève : "))
```

### 📌 Utilisation pour une action d'écriture

```algorithme
Ecrire (variable.champ)
```

```python
print (variable["champ"]);
```

**Exemple :**

Au niveau de l'algorithme :

```algorithme
Ecrire ("Nom : ", élève.nom)
```

Au niveau du Python :

```python
print ("Nom : ", eleve["nom"]) ;
```

## IV. Vecteur d'enregistrements

Un tableau ne peut grouper ou contenir que des éléments de même type, et puisque les éléments d'un enregistrement sont de même type qui est celui de l'enregistrement, donc on peut utiliser un tableau ou un vecteur d'enregistrements.

<!-- TODO vérifier: la phrase ci-dessus est transcrite telle quelle (« les éléments d'un enregistrement sont de même type qui est celui de l'enregistrement ») -->

**En algorithme :**

```algorithme
T.D.N.T
Type
Fiche = enregistrement
    nom, prénom : Chaîne
    sexe : Caractère
    numéro : Entier non signé
    moyenne : Réel
    num_cin : Entier long
Fin
Tab = Tableau de 30 Fiches {tableau d'enregistrements fiches}
```

| Objet | Type / Nature |
|---|---|
| T | Tab |

**En Python :**

```python
Nom_type ={
    "champ_1" : type_1,
    - - - -
    "champ_n" : type_n
}

from numpy import *
T=array([ dict(Nom_Type) ]*N)
```

<!-- TODO vérifier: le PDF écrit « Nom_type » dans la déclaration puis « Nom_Type » dans l'appel dict(...) (casse différente) ; transcrit tel quel -->

**Exemple :**

**En algorithmique :**

```algorithme
T.D.N.T
Type
Fiche = enregistrement
    nom, prénom : Chaîne
    sexe : Caractère
    numéro : Entier
    moyenne : Réel
    num_cin : Entier
Fin
Tab = Tableau de 30 Fiche
```

| Objet | Type / Nature |
|---|---|
| T | Tab |

Affectation de valeurs à cette variable :

```algorithme
T[0].nom ← "Swidi"
T[0].prénom ← "Basma"
T[0].sexe ← "F"
T[0].numéro ← 18
T[0].moyenne ← 13.25
T[0].num_cin ← 12345678
```

**En Python :**

Le type enregistrement.

```python
Fiche = {
    "nom" : str(),
    "prenom" : str(),
    "sexe" : str(),
    "numero" : int(),
    "moyenne" : float() ,
    "num_cin" : int()
}
from numpy import *
T=array([dict(Fiche)]*30)
```

Affectation des valeurs à cette variable :

```python
T[0] ["nom"] = "Swidi"
T[0] ["prenom"] = "Basma"
T[0] ["sexe"] = "F"
T[0] ["numero"] = 18
T[0] ["moyenne"] = 13.25
T[0] ["num_cin"]= 12345678
```

## Série d'exercices

<!-- TODO vérifier: cet énoncé s'intitule « Activité » dans le PDF (à la fin du chapitre) ; placé ici sous « Exercice 1 » -->

### Exercice 1

Un médecin enregistre sur ordinateur les fiches de ses Patients. Une fiche à la structure suivante :

- un nom (chaîne de 30 caractères maximum)
- un numéro (entier)
- un numéro de téléphone (10 caractères maximum)
- un code d'assurance (entier non signé).

Questions :

1. Écrire les algorithmes des différents modules d'un programme nommé Fiche, qui permet la saisie et l'affichage de l'enregistrement d'un Patient.
2. Traduire ce programme en Python
3. refaire l'exercice avec N patients sachant que 4 ≤ N ≤ 30.
