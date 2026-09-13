---
niveau: 2eme
chapitre: 2
titre: Les structures de contrôle conditionnelles
notions: la forme simple (Si … Alors), la forme alternative (Si … Sinon), les structures imbriquées, le choix multiple (Selon)
---

# Chapitre 2 : Les structures de contrôle conditionnelles

<!--
MODÈLE DE COURS FAHEM - à respecter à la lettre pour que l'import soit exact.

EN-TÊTE (entre les deux lignes ---), les 4 champs sont obligatoires :
  niveau   : 2eme
  chapitre : le numéro seul (2, 3, ...) - le même que dans le formulaire d'envoi
  titre    : le titre affiché aux élèves
  notions  : la LISTE des notions, séparées par des virgules (pas leur contenu)

TITRES :
  # Titre du chapitre   -> une seule fois, en haut (facultatif)
  ## I. Section         -> une grande partie du cours
  ### 1. Sous-partie    -> une sous-partie
  ### 📌 Syntaxe : ...  -> 📌 = FICHE DE RÉFÉRENCE : incluse dans CHAQUE réponse du
                           chapitre. Uniquement pour la syntaxe générale, jamais
                           pour un exemple. Garde-la courte et exacte.

CODE :
  - Toujours dans un bloc avec son langage : ```algorithme  ou  ```python
  - Jamais l'algorithme et le Python sur la même ligne ou côte à côte.
  - Affectation : toujours la flèche ←  (jamais <- ni -).
  - Une seule orthographe par mot-clé dans tout le cours (ex. : Si / Alors /
    Sinon / Fin Si, Selon / Fin Selon, Lire, Ecrire).

EXERCICES : à la fin, une section "## Série d'exercices", puis un
"### Exercice N" par exercice, suivi de son énoncé.

Ce bloc de commentaire peut rester dans le fichier : il est ignoré à l'import.
-->

## I. Introduction

[Un ou deux paragraphes : pourquoi on a besoin de ces structures.]

## II. La structure conditionnelle Si

### 📌 Syntaxe : forme simple

```algorithme
Si <condition> Alors
    <Traitement>
Fin Si
```

```python
if <condition> :
    <Traitement>
```

- `<condition>` : expression logique (Vrai ou Faux).
- `<Traitement>` : une ou plusieurs instructions.

### 📌 Syntaxe : forme alternative

```algorithme
Si <condition> Alors
    <Traitement 1>
Sinon
    <Traitement 2>
Fin Si
```

```python
if <condition> :
    <Traitement 1>
else :
    <Traitement 2>
```

### 1. Exemple

Une remise de 5 % est accordée si le montant dépasse 100.

```algorithme
Si Montant > 100 Alors
    Rem ← Montant * 0.05
Sinon
    Rem ← 0
Fin Si
```

```python
if Montant > 100 :
    Rem = Montant * 0.05
else :
    Rem = 0
```

**Remarque :** les opérateurs de comparaison sont `=`, `≠`, `<`, `≤`, `>`, `≥` ; les opérateurs logiques sont `ET`, `OU`, `NON`.

## III. La structure à choix multiple Selon

### 📌 Syntaxe : Selon

```algorithme
Selon <sélecteur>
    <valeur 1> : <Traitement 1>
    <valeur 2>, <valeur 3> : <Traitement 2>
    <valeur 4> .. <valeur 5> : <Traitement 3>
Sinon
    <Traitement n>
Fin Selon
```

```python
match <sélecteur> :
    case <valeur 1> :
        <Traitement 1>
    case <valeur 2> | <valeur 3> :
        <Traitement 2>
    case x if <valeur 4> <= x <= <valeur 5> :
        <Traitement 3>
    case _ :
        <Traitement n>
```

## Série d'exercices

### Exercice 1

Écrire un algorithme puis un programme Python qui lit un entier et affiche s'il est pair ou impair.

### Exercice 2

Écrire un algorithme puis un programme Python qui lit le numéro d'un mois (1 à 12) et affiche le nombre de jours de ce mois.
