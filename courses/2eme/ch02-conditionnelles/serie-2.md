---
niveau: 2eme
chapitre: 2
titre: Série N° 2 : Les structures de contrôle conditionnelles
type: serie
notions: structure conditionnelle Si, conditions imbriquées, structure conditionnelle Selon, chaînes de caractères, nombres aléatoires, dates et heures
source: Classroom — Série N° 2 - Les structures Conditionnelles
---

# Série N° 2 : Les structures de contrôle conditionnelles

<!-- TODO vérifier: la numérotation de l'original continue celle de la série 1 (14 à 27) ; elle comporte deux « Exercice n°19 » et saute le n°26 ; conservée telle quelle -->

## Série d'exercices

### Exercice 14

On voudra programmer le jeu « **devine_inverse** » qui devine le nombre inverse d'un nombre choisi au hasard par un ordinateur entre **10 et 99** et d'afficher le message gagnant ou perdant.

Ecrire **un algorithme** avec **T.D.O** correspond à cette Démarche :

1. L'ordinateur choisit au hasard un nombre **nbpc** entre 10 et 99
2. Saisir votre nombre **nb** (donnée)
3. Calculer l'inverse du nombre choisi par l'ordinateur **inv_nbpc**
   **Exemple** : pour **nbpc**=32 **inv_nbpc**= 2 * 10 + 3 = 2 3 avec 2 est le chiffre d'unité de **nbpc** et 3 est le chiffre de dizaine de **nbpc**
4. Si (**nb**=**inv_nbpc**) alors le programme affiche (" Vous avez gagné ... !!!")
   Sinon il affiche (" Vous avez perdu ... !!!")

**Voici l'interface du jeu si l'ordinateur a choisi nbpc=32**

![Illustration d'un ordinateur portable avec des bulles de dialogue, accompagnant l'interface du jeu](figures/serie2-ex14-interface.png)
<!-- TODO figure: à recréer -->

- Dans le premier cas le joueur a entré 23, il a gagné car 23 est l'inverse du 32
- Dans le deuxième cas le joueur a entré 45 il a perdu car 45 n'est pas l'inverse du 32

<!-- TODO vérifier: le contenu de l'écran du portable (copies d'écran des deux cas) n'est pas lisible dans le PDF ; seul le texte à côté est transcrit -->

### Exercice 15

Le jeu de Dé proposé se déroule entre deux joueurs et a comme principe le suivant :

- Le joueur 1 lance le dé afin d'avoir une valeur aléatoire entre 1 et 6
- la même chose pour le joueur 2
- le joueur gagnant c'est lui qui a **la valeur maximale** de Dé.

Afin de simuler ce jeu écrire un programme **python** qui permet de saisir **aléatoirement** les valeurs **choixj1** et **choixj2** qui sont respectivement les valeurs obtenues de **joueur 1** et **joueur 2** puis afficher le joueur gagnant.

**Exemple :**

- Si **choixj1=5** et **choixj2 =1** alors le programme affiche **"le joueur 1 gagne"**.
- Si **choixj1=3** et **choixj2 =6** alors le programme affiche **"le joueur 2 gagne"**.

### Exercice 16

Ecrire un programme qui permet de calculer le coût de la consommation d'eau (en m3) comme suit :

- Les 30 m3 premiers sont facturés à 0,200 D,
- Les 10 m3 suivants sont facturés à 0,250 D,
- La quantité au-delà de 40 m3 est facturée à 0,320 D.

**Exemples :**

- Consommation = 25 m3 → Coût = 25 * 0,2 = 5,000 D
- Consommation = 38 m3 → Coût = (30 * 0,2) + (8 * 0,25) = 8,000 D
- Consommation = 46 m3 → Coût = (30 * 0,2) + (10 * 0,25) + (6 * 0,32) = 10,420 D

### Exercice 17

Ecrire un programme qui permet de saisir une chaîne on suppose que **la chaine** soit **formée de 4 caractères** dont *le premier et le dernier caractère sont des lettres alphabétiques* et *les 2 caractères du milieu sont des chiffres*.

On demande d'écrire l'algorithme d'un programme qui permet d'extraire les 2 caractères chiffres de **ch** et tester si l'entier formé par *ces chiffres* est *pair* dans ce cas *calculer et afficher la somme des chiffres* sinon *afficher la valeur maximale des deux chiffres*.

**Exemple :**

- Si **Ch="L25H"** : On extraire les chiffres du milieu on aura alors "**25**" → l'entier équivalent n'est pas pair donc on affiche **max=5**
- Si **Ch="K14M"** : On extraire les chiffres du milieu on aura alors "14" → l'entier équivalent est pair donc on affiche s=1+4=5

<!-- TODO vérifier: le texte extrait montre « "25"èl'entier » ; la flèche entre le chiffre extrait et « l'entier » est lue comme → -->

### Exercice 18

Calcul du salaire d'un employé.

L'utilisateur saisit le nombre d'heures travaillées, le salaire horaire et l'ancienneté de l'employé. Les retenues de sécurité sociale sont calculées à partir du salaire brut multiplié par le taux de retenue de la sécurité sociale qui est une constante valant 0.19. L'employé bénéficie d'une prime d'ancienneté qui équivaut à 2% du salaire brut pour + de 10 ans et -20 ans d'ancienneté et 5% du salaire brut pour + 20 ans d'ancienneté.

### Exercice 19

On se propose dans cet exercice d'écrire un algorithme permettant de :

1. Déclarer 3 variables entières permettant de conserver les valeurs des heures, des minutes et des secondes.
2. Saisir un nombre d'heures, de minutes et de secondes.
3. Contrôler la saisie. Dans le cas d'une saisie invalide l'algorithme doit afficher un message d'erreur, sinon l'algorithme doit :
   - Incrémenter l'heure d'une seule seconde.
   - Afficher le message : Il est ... heure(s) ... minute(s) ... seconde(s).

L'affichage doit respecter l'orthographe du singulier et du pluriel.

Refaire le même exercice en considérant les contraintes suivantes : Incrémentation de l'horaire par 7 secondes au lieu de 1 seconde et ensuite décrémentation de l'horaire saisi par 12 secondes.

### Exercice 19

Une année A est dite bissextile si elle est divisible par 4 et non divisible par 100 ou elle est divisible par 400.

Ecrire un algorithme et son programme en python qui permet de saisir une année (elle doit être >0) et d'afficher s'elle est bissextile ou non.

### Exercice 20

Ecrire un algorithme et un programme python intitulé JOURS, qui affiche le nombre de jours d'un mois donné. On convient que le mois est saisi sous forme d'un entier entre 1 et 12.

**Remarque :** Pour le mois de février (2) le programme demandera l'année.

**Exemple :**

- Entrée : 4.
- Sortie : 30.

### Exercice 21

On désire écrire un programme qui permet de saisir **une date** sous forme de **jj/mm/aa** puis de calculer et d'afficher la date du lendemain

**NB :** La date donnée est **une chaîne de 8 caractères** (aucun contrôle de saisie n'est demandé)

### Exercice 22

Ecrire un programme Python intitulé **ANCIENNETE**, qui fait lire une date initiale JJ/MI/AI et une date finale JF/MF/AF et qui fait calculer et afficher la durée (exprimée en années, mois et jours) qui les sépare.

### Exercice 23

Une boulangerie est ouverte de ***7 heures à 13 heures*** et ***de 16 heures à 20 heures***, sauf le lundi après-midi et le mardi toute la journée.

*On suppose que l'heure **h** est un entier entre **0** et **23**. Le jour j code **0** pour **lundi**, **1** pour **mardi**, etc.*

Ecrire l'algorithme d'un programme qui demande le jour et l'heure, puis affiche si la boulangerie est ouverte ou fermé.

### Exercice 24

On désire écrire un algorithme d'un programme qui permet de calculer la durée d'un trajet connaissant l'heure de départ et d'arrivée.

On se contente des heures et des minutes, la durée totale ne dépassera jamais ***24 heures***.

**Exemple :**

- L'heure de départ : **20h:30mn**,
- L'heure d'arrivée : **05h:20mn**,
- La durée = **8h:50mn**

**NB : L'heure de départ** et **l'heure d'arrivée** sont deux **chaînes de 8 caractères** chacune (aucun contrôle de saisie n'est demandé)

### Exercice 25

Ecrire un programme qui permet de saisir **le sexe** (M/F), **la taille** (cm), et **le poids** (kg) d'une **personne** et d'afficher :

1. **PI**, le poids idéal d'une personne, sachant que ce poids théorique est donné par la formule de Lorenz comme suit :
   - *Pour un homme* : **PI** = (**taille** – 100) – (**taille** – 150) / 4
   - *Pour une femme* : **PI** = (**taille** -100) – (**taille** – 120) /4
2. **BMI**, l'indicateur d'obésité (Body Mass Index) où **BMI = poids / taille²** avec taille en mètre
3. Si une personne est considérée comme : **Normale** (BMI <= 27), ou **obèse** (BMI > 27) ou **Malade** (BMI >= 32)

### Exercice 27

Pour les parents qui sortent le soir, une garde d'enfants offre pour eux ses services pour les prix d'un enfant suivants :

- 1,250 dinar l'heure entre 18 h et 21 h.
- 4,800 dinars l'heure entre 21h et minuit.

On désire connaître le montant que doit payer les parents qui ont laissé leur(s) enfant(s) dans cette garde de l'heure h1 à l'heure h2.
