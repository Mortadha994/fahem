---
niveau: bac
chapitre: 1
titre: Les fichiers
type: cours
notions: organisation des fichiers, types d'accès, fichiers à accès séquentiel, déclaration d'un fichier, ouverture et fermeture, lecture et écriture, fin de fichier, fichiers texte, module pickle
source: Classroom — Chap 1 : Les fichiers
---

# Chapitre I : Les enregistrements et les fichiers — B. Les Fichiers

<!-- TODO vérifier: le PDF (6 pages, « chap les fichiers.pdf ») est intitulé « Chapitre I : Les enregistrements et les fichiers » avec le sous-titre « B. Les Fichiers » ; la partie A (enregistrements) n'est pas dans ce PDF. Le titre du chapitre est donc « Les fichiers » dans l'en-tête -->

<!-- TODO vérifier: mots-clés de l'algorithme écrits Tantque / Tant que / TantQue, Fin TantQue / Fin TantQue, Pour / Fin pour, faire / Faire, fin / Fin ; harmonisés en Tant que, Fin Tant que, Pour, Faire, Fin Pour, Si, Alors, Fin Si, Répéter, Jusqu'à, Vrai, Faux. Mots-clés Python du PDF (Import, For, While, X) écrits en minuscules (import, for, while) ; les autres écarts de l'original (n/N, X/x, I/i) sont transcrits tels quels et signalés -->

<!-- Le PDF contient du Python dans les tableaux de syntaxe et d'exemples ; rien n'a été ajouté. Les tableaux à trois colonnes (description | algorithme | Python) ont été séparés en blocs algorithme puis Python -->

## I. Introduction

- Avec les structures précédemment utilisées, les données d'un programme seront perdues dès l'arrêt de l'exécution de ce programme. Dans certains cas la sauvegarde des données est nécessaire d'où on fait recours à une nouvelle structure : **les fichiers**.
- Un fichier est un ensemble structuré des données de même type (réel, entier, caractère, chaîne, enregistrement ...) enregistrées sur une mémoire auxiliaire.

## II. Organisation des fichiers

L'organisation d'un fichier désigne le mode d'implémentation des informations et des enregistrements dans ce fichier et fournit les propriétés d'accès.

1. Organisation séquentielle : l'accès aux informations se fait en parcourant les enregistrements les uns après les autres.
2. Organisation relative (dite aussi directe) : les enregistrements sont identifiés par un numéro d'ordre.

## III. Types d'accès

En informatique, nous distinguons deux types d'accès aux données d'un fichier :

- **Accès séquentiel** : pour accéder à l'information d'ordre n, on doit passer par les (n-1) informations précédentes.
- **Accès direct** : on accède directement à l'information désirée, en précisant le numéro d'emplacement (le numéro d'ordre) de cette information.

**Remarque :** Tout fichier peut être utilisé avec l'un des deux types d'accès. Donc le choix de type d'accès dans un fichier ne concerne pas le fichier lui-même mais concerne la manière dont il va être traité par la machine (le choix de type d'accès se fait seulement dans le programme).

## IV. Les fichiers à accès séquentiel

### 1. Présentation

Un fichier est dit à accès séquentiel (ou fichier séquentiel) si l'accès à son nième information nécessite le passage par les (n-1) informations précédentes.

### 📌 2. Déclaration

En algorithmique :

T.D.N.T

```algorithme
Type
    Nom_fichier = Fichier de type_composant
```

T.D.O

| Objet | Type/Nature |
|---|---|
| Nom_logique | Nom_fichier |

**Remarque :**

- Comme on a déjà dit un fichier doit être enregistré sur un support externe, donc ce fichier doit avoir un nom et de préférence une extension. Ce nom est appelé le nom externe (ou le nom physique).
- Le nom de l'objet déclaré dans le tableau des objets comme nom de fichier est le nom interne du fichier (ou aussi le nom logique). C'est le nom utilisé dans les instructions du programme.
- Les fichiers de données (data) ont une extension .dat, .bin, .fch ...

**Activité :**

On veut écrire un programme permettant de saisir et enregistrer les informations de plusieurs produits présentés dans l'activité 1 des enregistrements. Présenter la déclaration en algorithme de la structure de données nécessaire.

En algorithmique :

T.D.N.T

```algorithme
Type
    Informations = Enregistrement
        Ref, design : chaîne
        Qte : Entier
        PVU, PVT : réel
    Fin
    Liste_prod = Fichier de Informations
```

T.D.O

| Objet | Type/Nature |
|---|---|
| Fichier_prod | Liste_prod |

<!-- TODO vérifier: l'indentation exacte du T.D.N.T de l'activité n'a pas été distinguée sur le rendu ; mise en forme standard (Fin sans mot qui suit, comme dans le PDF) -->

### 📌 3. Traitement sur les fichiers

Les fonctions et les procédures sur les fichiers (fichiers typés). Mode d'ouverture :

- `"rb"` : Lecture (pointer au début)
- `"wb"` : Ecriture (remise à zéro)
- `"ab"` : Ajout à la fin du fichier

**Ouvrir** : avant d'utiliser un fichier il faut associer (relier) son nom logique à son nom physique.

```algorithme
Ouvrir (nom physique, nom logique, Mode)
```

```python
nom logique = open (nom physique, mode)
```

Exemple : `Ouvrir ("c:\Bac\Nombre.data",f,"rb")` en algorithme et `F=Ouvrir ("c:\Bac\Nombre.data","rb")` en Python.

<!-- TODO vérifier: dans la colonne Python de l'exemple d'ouverture, le PDF écrit « F=Ouvrir (...) » au lieu de « F=open (...) » ; transcrit tel quel -->

**Ecrire ou modifier une valeur ou un enregistrement dans un fichier.**

```algorithme
Ecrire (nom_logique, variable)
```

```python
import pickle as pk
pk.dump (variable,nom_logique)
```

Exemple : `Ecrire (f, e)` en algorithme et `pk.dump (e, f)` en Python.

**Lire une valeur ou un enregistrement à partir d'un fichier.**

```algorithme
Lire (nom_logique, variable)
```

```python
import pickle as pk
variable =pk.load (nom_logique)
```

Exemple : `Lire (f, e)` en algorithme et `e =pk.dump ( f)` en Python.

<!-- TODO vérifier: l'exemple Python de lecture du PDF utilise pk.dump au lieu de pk.load ; transcrit tel quel -->

**Fermer un fichier.**

```algorithme
Fermer (nom_logique)
```

```python
nom_logique.close ()
```

Exemple : `Fermer (f)` en algorithme et `f .close ()` en Python.

**Fonction booléenne vérifiant si la fin du fichier a été atteinte.**

```algorithme
Fin_Fichier (nom logique)
```

Exemple en algorithme :

```algorithme
Tant que (non(Fin_Fichier(f))) Faire
    #Traitements
Fin Tant que
```

Version Python :

```python
B=True
while B :
    try:
        #Traitements
        .........
    except :
        B=False
```

**Exercice :**

Ecrire un programme en python permettant de :

- créer un fichier des élèves. Chaque élève est caractérisé par :
  - nom
  - note de contrôle 1
  - note de contrôle 2
  - note de synthèse
  - moyenne
- ouvrir le fichier élève et constituer deux autres fichiers : le premier contiendra la liste des données correspondante aux élèves ayant une moyenne supérieure ou égale à 10 et le deuxième contiendra les données correspondante aux autres élèves.
- Déterminer et afficher le nombre des élèves qui ont une moyenne >= 10, leurs noms et leurs moyennes.
- Déterminer et afficher le nombre des élèves qui ont une moyenne < 10, leurs noms et leurs moyennes.
- Déterminer et afficher le numéro, le nom et la moyenne des élèves qui ont la moyenne la plus élevées.

## V. Les fichiers texte

### 1. Présentation

Un fichier texte (ou ASCII) est un fichier contenant des caractères.

### 2. Déclaration

T.D.O

| Objet | Type/Nature |
|---|---|
| Nom_logique | Fichier Texte |

**Remarque :**

Les fichiers texte contiennent des caractères de type « Retour chariot » (CR) ou « Fin de ligne » (Eoln) et « Fin de texte » (code CTRL-Z).

### 📌 3. Procédures et fonctions prédéfinies

Mode d'ouverture :

- `"r"` : Lecture (pointer au début)
- `"w"` : Ecriture (remise à zéro)
- `"a"` : Ajout à la fin du fichier

**Ouvrir** : avant d'utiliser un fichier il faut associer (relier) son nom logique à son nom physique.

```algorithme
Ouvrir (nom physique, nom logique, Mode)
```

```python
nom logique = open (nom physique, mode)
```

Exemple : `Ouvrir ("c:\Bac\Phrases.txt",f,"r")` en algorithme et `F=Ouvrir ("c:\Bac\Phrases.txt","r")` en Python.

<!-- TODO vérifier: même écart que pour les fichiers typés (« F=Ouvrir » dans la colonne Python) ; transcrit tel quel -->

**Ecriture dans un fichier texte sans retour à la ligne.**

```algorithme
Ecrire (nom_logique, variable)
```

```python
nom_logique.write(variable)
```

Exemple : `Ecrire (f, ch)` en algorithme et `f .write (ch)` en Python.

**Ecriture dans un fichier texte avec retour à la ligne.**

```algorithme
Ecrire_NL(nom_logique, variable)
```

```python
nom_logique.write(variable+"\n")
```

Exemple : `Ecrire_NL (f, ch)` en algorithme et `f .write (ch+"\n")` en Python.

**Lecture de la totalité d'un fichier.**

```algorithme
Lire (nom_logique, variable)
```

```python
Variable= nom_logique.read()
```

Exemple : `Lire (f, ch)` en algorithme et `Ch=f .read ( )` en Python. Tout le contenu dans la chaîne ch.

**Lecture d'une ligne depuis un fichier texte.**

```algorithme
Lire_ligne (nom_logique, variable)
```

```python
Variable= nom_logique.readline()
```

Exemple : `Lire_ligne (f, ch)` en algorithme et `Ch=f .readline ( )` en Python.

**Fermer un fichier.**

```algorithme
Fermer (nom_logique)
```

```python
nom_logique.close ()
```

Exemple : `Fermer (f)` en algorithme et `f .close ()` en Python.

**Fonction booléenne vérifiant si la fin du fichier a été atteinte.**

```algorithme
Fin_Fichier (nom logique)
```

Exemple en algorithme :

```algorithme
Tant que (non(Fin_Fichier(f))) Faire
    #Traitements
Fin Tant que
```

Version Python :

```python
ch=f.readline()
while ch != "":
    #Traitements
    ch=f.readline()
```

**Exercice :**

Ecrire un programme permettant de :

- saisir et enregistrer une liste des noms des enseignants (nom par ligne).
- La liste se termine par un point (le point n'appartient pas au fichier).
- Déterminer et afficher le nombre de lettres par nom d'enseignant.

**Remarque :**

- La position initiale du pointeur dans un fichier de données est 0.
- Avant d'utiliser un fichier il faut l'ouvrir.
- Après l'utilisation d'un fichier il faut le fermer.

## VI. Exemples sur les fichiers

<!-- TODO vérifier: le PDF n'a pas de numéro de section pour cette partie (titre « Exemple sur les fichiers ») ; le numéro VI. et le pluriel sont ajoutés pour respecter la hiérarchie -->

### Remplir un fichier typé avec N entiers

```algorithme
Ouvrir("C:\entiers.dat",F,"wb")
Pour i de 1 à N Faire
    Ecrire("Donner un entier :")
    Lire(x)
    Ecrire(F,x)
Fin Pour
Fermer(F)
```

```python
import pickle as pk
F=open(r"C:\entiers.dat","wb")
for i in range(n) :
    x=int(input("Donner un entier")
    pk.dump(x,F)
F.close()
```

<!-- TODO vérifier: parenthèse fermante manquante dans « int(input("Donner un entier") » ; « range(n) » alors que l'algorithme utilise N ; transcrit tel quel -->

### Afficher un fichier typé rempli par N entiers

```algorithme
Ouvrir("C:\entiers.dat",F,"rb")
Pour i de 1 à N Faire
    Lire(F,x)
    Ecrire("l'entier est :",x)
Fin Pour
Fermer(F)
```

```python
import pickle as pk
F=open(r"C:\entiers.dat","rb")
for i in range(n) :
    X=pk.load(F)
    print("L'entier est :",x)
F.close()
```

<!-- TODO vérifier: « X=pk.load(F) » (majuscule) puis « print(...,x) » (minuscule) dans l'original ; transcrit tel quel -->

### Remplir un fichier typé avec N élèves (Nom, Pre, Age, Moy)

```algorithme
Ouvrir("C:\eleves.dat",F,"wb")
Pour i de 1 à N Faire
    Ecrire("Donner le nom:")
    Lire(x.nom)
    Ecrire("Donner le prénom:")
    Lire(x.pre)
    Ecrire("Donner l'age :")
    Lire(x.age)
    Ecrire("Donner la moyenne:")
    Lire(x.moy)
    Ecrire(F,x)
Fin Pour
Fermer(F)
```

```python
import pickle as pk
F=open(r"C:\eleves.dat","wb")
for i in range(n) :
    x={ } #dictionnaire
    x["nom"]=input("Donner le nom:")
    x["pre"]=input("Donner le prénom:")
    x["age"]=int(input("Donner l'age :"))
    x["moy"]=float(input("Donner la moyenne :"))
    pk.dump(x,F)
F.close()
```

### Afficher un fichier typé rempli par N élèves (Nom, Pre, Age, Moy)

```algorithme
Ouvrir("C:\eleves.dat",F,"rb")
Pour i de 1 à N Faire
    Lire(F,x)
    Ecrire("le nom:", x.nom)
    Ecrire("le prénom:", x.pre)
    Ecrire("l'age :", x.age)
    Ecrire("la moyenne:", x.moy)
Fin Pour
Fermer(F)
```

```python
import pickle as pk
F=open(r"C:\eleves.dat","rb")
for i in range(n) :
    X=pk.load(F)
    print("le nom:", x["nom"])
    print ("le prénom:", x["pre"])
    print ("l'age :", x["age"])
    print ("la moyenne:", x["moy"])
F.close()
```

### Transférer les données d'un fichier F de taille N vers un tableau T

Le type des cases du tableau et les données du fichier doit être de même type.

```algorithme
Ouvrir("C:\eleves.dat",F,"rb")
Pour i de 0 à N-1 Faire
    Lire(F,T[i])
Fin Pour
Fermer(F)
```

```python
import pickle as pk
from numpy import *
F=open(r"C:\eleves.dat","rb")
T=array([{type}]*N)
for i in range(n) :
    T[i]=pk.load(F)
F.close()
```

<!-- TODO vérifier: « T=array([{type}]*N) » (« {type} » à la place du type des cases, ailleurs « {} ») ; transcrit tel quel -->

### Transférer les données d'un tableau T de taille N vers un fichier F

Le type des cases du tableau et les données du fichier doit être de même type.

```algorithme
Ouvrir("C:\eleves.dat",F,"wb")
Pour i de 0 à N-1 Faire
    Ecrire(F,T[i])
Fin Pour
Fermer(F)
```

```python
import pickle as pk
F=open(r"C:\eleves.dat","rb")
for i in range(n) :
    pk.dump(T[i],F)
F.close()
```

<!-- TODO vérifier: le Python ouvre le fichier en "rb" alors que l'algorithme l'ouvre en "wb" (pk.dump exige "wb") ; transcrit tel quel -->

### Remplir un fichier texte FT par des chaînes (une chaîne par ligne)

L'arrêt de saisie lorsque l'utilisateur tape "N" sur la question « Continuer O/N : ».

```algorithme
Ouvrir("C:\chaines.txt",FT,"w")
Répéter
    Ecrire("Donner une chaine : ")
    Lire(ch)
    Ecrire_NL(FT,ch)
    Répéter
        Ecrire("Continuer O/N :")
        Lire(rep)
    Jusqu'à (Majus(rep) ∈ ["O","N"])
Jusqu'à (Majus(rep) ="N")
Fermer(FT)
```

```python
FT=open("C:\chaines.txt","w")
rep="O"
while(rep=="O") :
    ch=input("Donner une chaine : ")
    Ft.write(FT,ch+"\n")
    while((rep.upper() in ["O","N"]) and (len(rep)==1)):
        rep=input("Continuer O/N :")
FT.close()
```

<!-- TODO vérifier: Python de l'original discutable (« Ft.write(FT,ch+"\n") », boucle interne dont la condition est inversée par rapport à l'algorithme, « rep » non mis en majuscules) ; transcrit tel quel, mot-clé While écrit en minuscules -->

### Affichage d'un fichier texte FT

```algorithme
Ouvrir("C:\chaines.txt",FT,"r")
Tant que (non(fin_fichier(FT))) Faire
    Lire_Ligne(FT,ch)
    Ecrire(ch)
Fin Tant que
Fermer(FT)
```

```python
FT=open("C:\chaines.txt","r")
ch=FT.readline()
while(ch!=""):
    print(ch)
    ch=FT.readline()
FT.close()
```

### Tri d'un fichier typé F rempli par N élèves (Nom, Pre, Age, Moy)

```algorithme
Ouvrir("C:\eleves.dat",F,"rb")
Pour i de 0 à N-1 Faire
    Lire(F,T[i])
Fin Pour
Répéter
    permute ← Faux
    Pour i de 0 à N-2 Faire
        Si (T[i].moy < T[i+1].moy) Alors
            Aux ← T[i]
            T[i] ← T[i+1]
            T[i+1] ← Aux
            permute ← Vrai
        Fin Si
    Fin Pour
Jusqu'à (permute = Faux)
Ouvrir("C:\eleves.dat",F,"wb")
Pour i de 0 à N-1 Faire
    Ecrire(F,T[i])
Fin Pour
Fermer(F)
```

```python
import pickle as pk
from numpy import *
F=open(r"C:\eleves.dat","rb")
T=array([{}]*N)
for i in range(n) :
    T[i]=pk.load(F)
permute = True
while (permute) :
    permute = False
    for I in range(n-1):
        if (T[i]["moy"] > T[i+1]["moy" ]) :
            Aux=T[i]
            T[i] = T[i+1]
            T[i+1] = Aux
            permute = True
F=open(r"C:\eleves.dat","rb")
for i in range(n) :
    pk.dump(T[i],F)
F.close()
```

<!-- TODO vérifier: l'algorithme compare « < » (ordre décroissant) et le Python « > » (ordre croissant) ; « for I » (majuscule) puis T[i] ; le fichier est rouvert en "rb" avant pk.dump (devrait être "wb") et le premier fichier n'est pas fermé ; l'algorithme du PDF écrit « Jusqu'à (permute = faux) » (harmonisé en Faux) ; transcrit tel quel -->
