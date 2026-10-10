---
niveau: bac
chapitre: 4
titre: Les interfaces graphiques
type: cours
notions: interface graphique (GUI), programmation évènementielle, PyQt5, Qt Designer, chargement d'un fichier .ui, widgets, signaux et slots, fenêtres d'alerte (QMessageBox)
source: Classroom — Cours les interfaces graphiques
---

# Chapitre 4 : Les interfaces graphiques

<!-- TODO vérifier: le PDF (8 pages, « cours les interfaces graphiques.pdf ») est intitulé « Les interfaces graphiques » sans numéro de chapitre ; numéro 4 retenu selon l'ordre du programme. Le cours utilise PyQt5 (Qt Designer + loadUi) et non Tkinter ; la mention de Tkinter n'apparaît que dans une phrase de la partie II -->

<!-- TODO vérifier: les sous-titres des composants (pages 4 à 8) sont dans le PDF « Widget Box > ... > » suivis d'une icône du composant ; le nom du composant (Label, Line Edit, Text Edit, Combo Box, Push Button, Check Box, Radio Button, List Widget, Table Widget) est lu sur l'icône ou déduit des exemples. Ces sous-titres ne sont pas numérotés dans le PDF : ils sont rangés en ### sous la partie IX pour la structure -->

<!-- TODO vérifier: l'indentation du code Python du PDF est reprise telle quelle (les lignes « ......... » des fonctions traitement sont dans le PDF) ; les fautes d'orthographe de l'original (« coché », « Décoché », « Vérifié », « comme de commande ») sont conservées -->

## I. Présentation de l'interface graphique (GUI) :

Les interfaces graphiques (ou interfaces homme-machine) sont appelées **GUI** (**G**raphical **U**ser **I**nterface), permet à un utilisateur d'interagir avec un programme informatique grâce à l'utilisation de nombreux composants graphiques (boutons, menus, cases à cocher, etc.). Ces éléments sont généralement contrôlés avec une souris ou un clavier.

**Exemple d'interface :**

![Fenêtre « Jeux de Chance » ouverte dans Qt Designer : un formulaire avec les étiquettes Identifiant, Numéro de Téléphone, Genre, Ville, Etat, des champs de saisie, deux boutons radio (Masculin, Féminin), une liste déroulante, une case à cocher, deux boutons « Afficher Chance » et « Afficher Gagnants » et deux grandes listes ; des flèches indiquent le type de chaque composant : Label, Line edit, Radio Button, Combo Box, Check Box, Push Button, List Widget, Table Widget](figures/exemple-interface-gui.png)
<!-- TODO figure: à recréer -->

## II. La programmation évènementielle

Une interface graphique est pilotée par les événements, contrairement à une application en mode console, qui est traitée de manière séquentielle. Les activités de l'utilisateur telles que cliquer sur un bouton, sélectionner un élément dans une collection ou un clic de souris, entre autres, déclenchent l'exécution de fonctions ou de méthodes.

Les scripts écrits en Python affichent actuellement des informations dans la console et sont donc en mode texte. Python inclut un certain nombre de bibliothèques pour manipuler les interfaces graphiques, notamment : PyQt5 et Tkinter. Il y en a beaucoup plus.

## III. Méthodes de création d'interfaces graphiques GUI en Python

Il existe deux approches pour créer une interface utilisateur graphique :

- Soit utiliser un langage de programmation pour écrire le code qui correspond à l'interface.
- Soit utiliser un outil de conception et de création d'interfaces graphiques pour créer des objets graphiques (zone de texte, case à cocher, bouton radio, bouton, menu), on parle d'un éditeur graphique tel que Qt Designer ou Qt Creator.

Composants graphiques présentés dans le PDF (légende d'une image) : Label, Line_edit, Radio Button, Check Box, Combo Box, Push Button, List Widget, Table Widget.

![Les composants graphiques de Qt Designer avec leur nom : Label, Line_edit, Radio Button, Check Box, Combo Box, Push Button, List Widget, Table Widget](figures/composants-graphiques.png)
<!-- TODO figure: à recréer -->

## IV. Préparer le labo pour utiliser PyQt5

PyQt est un module Python gratuit qui intègre la bibliothèque Qt avec le langage Python.

Qt est une bibliothèque logicielle qui fournit principalement un ensemble de composants d'interface graphique (souvent appelés widgets), ainsi que des composants non graphiques qui permettent, entre autres, l'accès aux données, les connexions réseau, la gestion des files d'attente, etc.

PyQt vous permet de construire des interfaces graphiques en Python tout en profitant de tous les avantages de Qt, tels que la bibliothèque de widgets GUI et la facilité avec laquelle vous pouvez créer des interfaces utilisateur personnalisables et des composants logiciels réutilisables.

Environ 440 classes et plus de 6000 fonctions et méthodes sont implémentées dans PyQt.

Python utilise actuellement PyQt version 6. Le rôle de PyQt est de maintenir tous ensemble. PyQt est un module Python qui s'interface avec la bibliothèque Qt. Cette bibliothèque comprend une large gamme de composants graphiques et est bien documentée.

<!-- TODO vérifier: le PDF dit « PyQt version 6 » alors que tout le cours porte sur PyQt5 ; transcrit tel quel -->

## V. Installation de PyQt5

1. La méthode la plus simple est d'ouvrir l'éditeur préféré et installer la package PyQt5 avec l'outil d'installation de packages. Dans l'editeur Thonny aller dans le menu Outils (Tools) puis Gérer les packages (Manage packages). Une zone de texte nous invite à écrire le nom du package. Après la recherche, je clique sur le nom du package désiré puis choisir installer.
2. Une autre méthode consiste à utiliser la commande pip install, ça peut marcher dans l'invite de comme de commande, mais on peut rencontrer des erreurs. Je conseille de lancer l'invite de commande depuis Thonny : choisir Ouvrir shell système (Open shell system) du menu Outils (Tools) puis lancer la commande `pip install PyQt5`
3. Une connexion Internet est nécessaire. Respecter la casse, `pip install pyqt5` ne donnera pas un bon résultat.

## VI. Qt Designer

Qt Designer est une application conviviale qui vous permet de développer des interfaces graphiques Qt. L'utilisateur peut facilement placer des composants GUI et définir leurs propriétés en les faisant glisser et en les déposant. Les fichiers GUI contiennent l'extension .ui et sont formatés en XML.

Le développement peut sembler long et répétitif. C'est amusant au début, mais après un certain temps, le code parait long et ce juste pour organiser les widgets sur l'écran.

C'est alors que Qt Designer arrive pour sauver la situation. Il s'agit d'un logiciel qui permet de dessiner graphiquement vos fenêtres. Qt Designer permet également de modifier les attributs des widgets, d'utiliser des mises en page et de lier des signaux et des slots. Qt Designer permet du gagner du temps et d'éviter d'écrire le code générant des fenêtres.

## VII. Installation de Qt Designer

- Utiliser simplement le https://build-system.fman.io/qt-designer-download
- Ou installer PyQt5Designer du menu Outils/Gérer les packages
- Ou installer avec la commande `pip install PyQt5Designer` dans le shell système.

## VIII. L'interface Qt Designer

![Capture de la fenêtre de Qt Designer avec quatre zones légendées : Boite des composants, Inspecteur des objets, Espace de travail (la fenêtre Interface en cours de conception) et Editeur de propriété](figures/interface-qt-designer.png)
<!-- TODO figure: à recréer -->

## 📌 IX. L'utilisation dans Python :

```python
# importations nécessaire à la réalisation d'une interface graphique
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication
......
# Création d'une application Qt avec QApplication
app = QApplication([])
# Charger la fenêtre à partir d'un fichier .ui
Fen = loadUi ("Nom_Interface.ui")
# Rendre la fenêtre visible
Fen.show()
# Un signal est émis chaque fois que le bouton est appuyé
Fen.Nom_Bouton.clicked.connect(Nom_Module)
# Exécution de l'application, l'exécution permet de gérer les événements
app.exec_()
```

<!-- TODO vérifier: la ligne « ...... » du PDF (importations omises) est conservée telle quelle dans le code ; plus loin dans le cours l'exemple utilise « app.exec() » au lieu de « app.exec_() » -->

### Widget Box > Display Widgets > Label

- Modifier le texte d'un label : `Fen.MyLabel.setText(" Un Titre ")`
- Récupérer le texte d'un label dans une variable : `ch=Fen.MyLabel.text()`
- Effacer le contenu d'un label : `Fen.MyLabel.clear()`
- Mettre un nombre dans d'un label : `Fen.MyLabel.setNum(18.5)`

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QLabel.html

### Widget Box > Input Widgets > Line Edit

**Fonction :**

- Récupérer le texte d'un « Line Edit » dans une variable : `ch=Fen.MyLine.text()`

**Slots :**

- Modifier le texte d'un « Line Edit » : `Fen.MyLine.setText(" Un texte ")`
- Effacer le contenu d'un « Line Edit » : `Fen.MyLine.clear()`
- Ajouter à la fin du contenu du champ de saisie : `Fen.MyLine.insert ("plus")`
- Pour que le champ prend le focus : `Fen.MyLine.setFocus()`

**Signaux :**

- Un signal est émis chaque fois que le texte est édité, et le traitement 1 est exécuté

```python
def traitement1() :
    .........
Fen.MyLine.textEdited.connect(traitement1)
```

**Remarque :** Il y a aussi `textChanged` : Détection de changement de champ de saisie par édition ou par affectation de variable.

- Un signal est émis chaque fois que la touche « Entrée » est enfoncée dans le champ de saisie, et le traitement 2 est exécuté.

```python
def traitement2() :
    .........
Fen.MyLine.returnPressed.connect(traitement2)
```

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QLineEdit.html

### Widget Box > Input Widgets > Text Edit

**Fonction :**

- Récupérer le texte d'un « Text Edit » dans une variable : `ch=Fen.MyTextEdit.toPlainText()`

**Remarque :** dans le cas d'un retour à la ligne le texte récupéré contient des `"\n"`

- Pour que le champ prend le focus : `Fen.MyTextEdit.setFocus()`

**Slots :**

- Modifier le texte d'un « Text Edit » : `Fen.MyTextEdit.setText(" Un texte ")`

**Remarque :** Il y a aussi `SetPlainText("Texte")`

- Effacer le contenu d'un « Text Edit » : `Fen.MyTextEdit.clear()`
- Ajouter à la fin du contenu d'un « Text Edit » : `Fen.MyTextEdit.append ("plus")`

**Remarque :** append ajoute un retour à la ligne précédente `"\n"`.

- Ajouter au début du contenu d'un « Text Edit » : `Fen.MyTextEdit.insertPlainText ("Begin")`

**Signaux :**

- Un signal est émis chaque fois que le texte est changé, et le traitement 3 est exécuté

```python
def traitement3() :
    .........
Fen.MyTextEdit.textChanged.connect(traitement3)
```

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QTextEdit.html

### Widget Box > Input Widgets > Combo Box (Liste déroulante)

**Fonction :**

- Ajouter à la fin d'une liste d'un « Combo Box » : `Fen.MyComboBox.addItem("New Item")`
- Pour ajouter plusieurs options à la liste : `Fen.MyComboBox.addItems ( ["New Item 1","New Item 2","New Item 3"] )`
- Pour retourner le nombre des options d'une liste : `N= Fen.MyComboBox.count()`
- Pour récupérer l'indice sélectionné : `ind = Fen.MyComboBox.currentIndex()`
- Pour récupérer le texte d'une option sélectionnée : `ch = Fen.MyComboBox.currentText()`
- Pour ajouter une option à une position : `Fen.MyComboBox.insertItem(ind,texte)`

**Remarque :** lors de l'ajout d'une nouvelle option, la liste sera décalée. Et pour plusieurs options : `insertItems(ind,[textes])`

- Pour supprimer une option : `Fen.MyComboBox.removeItem(ind)`

**Slots :**

- Effacer le contenu d'un « Combo Box » : `Fen.MyComboBox.clear()`
- Pour positionner à une option : `Fen.MyComboBox.setCurrentIndex(ind)`

**Signaux :**

- Un signal est émis chaque fois que l'indice est changé, et le traitement 4 est exécuté

```python
def traitement4() :
    .........
Fen.MyComboBox.currentIndexChanged.connect(traitement4)
```

**Remarque :** Il y a aussi les signaux : `activated()` et `highlighted()`

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QComboBox.html

### Widget Box > Buttons > Push Button

- Modifier le texte d'un bouton : `Fen.MyButton.setText(" Un Titre ")`
- Récupérer le texte d'un bouton dans une variable : `ch=Fen.MyButton.text()`

**Signaux :**

- Un signal est émis chaque fois que le bouton est appuyé, et le traitement 5 est exécuté

```python
def traitement5() :
    .........
Fen.MyButton.clicked.connect(traitement5)
```

**Remarque 1 :** Il y a aussi les signaux `pressed()` et `released()`

**Remarque 2 :**

- On peut fermer l'application en utilisant `Fen.MyButton.clicked.connect(Fen.close)`
- On peut effacer le contenu du champ de saisie `Fen.MyButton.clicked.connect(Fen.MyLine.clear)`

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QPushButton.html

**Exemple de script Python :** (Ecrire un texte dans le champ de saisie puis cliquer sur le bouton pour le reproduire dans le label)

```python
# importations à faire pour la réalisation d'une interface graphique
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication
def traitement():
    x=Fen.MyLine.text()
    Fen.MyLabel.setText(x)
app=QApplication([]) #Création d'une application Qt avec QApplication
Fen=loadUi("interface.ui") # Charger la fenêtre à partir d'un fichier
Fen.show() #Rendre la fenêtre visible
Fen.MyButton.clicked.connect(traitement)
app.exec() #Exécution de l'application (permet de gérer les événements en boucle(event loop))
```

### Widget Box > Buttons > Check Box

- Modifier le texte d'une case à coché : `Fen.MyCheckBox.setText(" Un Texte ")`
- Récupérer le texte d'une case à coché dans une variable : `ch=Fen.MyCheckBox.text()`
- Décoché une case à coché : `Fen.MyCheckBox.setChecked(False)`
- Vérifié si une case est coché ou non : `B=Fen.MyCheckBox.isChecked()`

**Signaux :**

- Un signal est émis chaque fois que la case est cochée, et le traitement 6 est exécuté

```python
def traitement6() :
    .........
Fen.MyCheckBox.clicked.connect(traitement6)
```

**Remarque :** Il y a aussi les signaux `pressed()`, `released()` et `toggled()`

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QCheckBox.html

### Widget Box > Buttons > Radio Button

- Modifier le texte d'un bouton Radio : `Fen.MyRadioButton.setText(" Un Texte ")`
- Récupérer le texte d'un bouton Radio dans une variable : `ch=Fen.MyRadioButton.text()`
- Décoché un bouton Radio :

```python
Fen.MyRadioButton.setAutoExclusive(False)
Fen.MyRadioButton.setChecked(False)
Fen.MyRadioButton.setAutoExclusive(True)
```

- Vérifié si un bouton Radio est coché ou non : `B=Fen.MyRadioButton.isChecked()`

**Signaux :**

- Un signal est émis chaque fois que le bouton Radio est coché, et le traitement 7 est exécuté

```python
def traitement7() :
    .........
Fen.MyButtonRadio.clicked.connect(traitement7)
```

<!-- TODO vérifier: le PDF écrit « Fen.MyButtonRadio » dans la ligne connect alors que le bouton s'appelle « MyRadioButton » partout ailleurs ; transcrit tel quel -->

**Remarque :** Il y a aussi les signaux `pressed()`, `released()` et `toggled()`

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QRadioButton.html

### Widget Box > Item Widgets > List Widget

**Fonction :**

- Ajouter à la fin d'une liste d'un « List Widget » : `Fen.MyListWidget.addItem("New Item")`
- Pour ajouter plusieurs lignes à la liste : `Fen.MyListWidget.addItems ( ["New Item 1","New Item 2","New Item 3"] )`
- Pour retourner le nombre des lignes d'une liste : `N= Fen.MyListWidget.count()`
- Pour récupérer l'indice de la ligne sélectionnée : `ind = Fen.MyListWidget.currentRow()`
- Pour récupérer le texte d'une ligne sélectionnée : `ch = Fen.MyListWidget.currentItem().text()`
- Pour ajouter une ligne à une position : `Fen.MyListWidget.insertItem(ind,texte)`

**Remarque :** lors de l'ajout d'une nouvelle ligne, la liste sera décalée. Et pour plusieurs lignes : `insertItems(ind,[textes])`

- Pour supprimer une option : `Fen.MyListWidget.takeItem(ind)`
- Pour positionner à une option : `Fen.MyListWidget.setCurrentIndex(ind)`

**Slots :**

- Effacer le contenu d'un « List Widget » : `Fen.MyListWidget.clear()`

**Signaux :**

- Un signal est émis chaque fois que la ligne est changée, et le traitement 8 est exécuté

```python
def traitement8() :
    .........
Fen.MyListWidget.currentItemChanged.connect(traitement8)
```

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QListWidget.html

### Widget Box > Item Widgets > Table Widget

**Fonction :**

- Ajouter une ligne à la liste d'une « Table Widget » :

```python
from PyQt5.QtWidgets import QTableWidgetItem
Fen.MyTableWidget.insertRow(indLigne)
```

Ou bien : `Fen.MyTableWidget.setRowCount(Nombre_de_Ligne)`

```python
Fen.MyTableWidget.setItem(indLigne,indColonne, QTableWidgetItem ("New Item"))
```

- Pour ajouter plusieurs lignes à la liste : `Fen.MyTableWidget.addItems ( ["New Item 1","New Item 2","New Item 3"] )`
- Pour retourner le nombre des lignes d'une liste : `N= Fen.MyTableWidget.rowCount()`
- Pour retourner le nombre des colonnes d'une liste : `N= Fen.MyTableWidget.columnCount()`
- Pour récupérer l'indice de la ligne sélectionnée : `indL = Fen.MyTableWidget.currentRow()`
- Pour récupérer l'indice de la colonne sélectionnée : `indC = Fen.MyTableWidget.currentColumn()`
- Pour récupérer le texte sélectionné : `ch = Fen.MyTableWidget.currentItem().text()`

**Slots :**

- Vider une « Table Widget » : `Fen.MyTableWidget.clear()`
- Effacer le contenu des lignes d'une « Table Widget » : `Fen.MyTableWidget.clearContents()`
- Pour supprimer une ligne : `Fen.MyTableWidget.removeRow (ind)`
- Pour supprimer une colonne : `Fen.MyTableWidget.removeColumn (ind)`
- Pour supprimer les lignes et leurs contenus :

```python
while Fen.tw.rowCount()>0 :
    Fen.tw.removeRow(Fen.tw.rowCount()-1)
```

**Signaux :**

- Un signal est émis chaque fois qu'une case est sélectionnée, et le traitement 9 est exécuté

```python
def traitement9() :
    .........
Fen.MyTableWidget.cellClicked.connect(traitement9)
```

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QTableWidget.html

<!-- TODO vérifier: le PDF utilise « addItems » sur un Table Widget et « Fen.tw » (au lieu de Fen.MyTableWidget) dans la boucle de suppression ; transcrit tel quel -->

### Pour rendre un composant Activé/Désactivé

`Fen.MyWidget.setEnabled(True/False)`

### Les fenêtres d'alerte : (QMessageBox)

Pour afficher des messages d'alerte via « QMessageBox » :

```python
from PyQt5.QtWidgets import QMessageBox
```

![Les quatre icônes des fenêtres d'alerte avec leur nom : Question (point d'interrogation), Information (i), Warning (triangle jaune), Critical (croix rouge)](figures/icones-qmessagebox.png)
<!-- TODO figure: à recréer -->

<!-- TODO vérifier: la légende de l'image des icônes ne montre que quatre icônes lisibles : Question, Information, Warning, Critical -->

- `QMessageBox.critical(Fen, "Titre", "Texte")`

  **Exemple :** `QMessageBox.critical(Fen, "Erreur", "Veuillez saisir vos données !")`

  ![Fenêtre d'alerte « Erreur » avec une icône de croix rouge, le message « Veuillez saisir vos données ! » et un bouton OK](figures/qmessagebox-critical.png)
  <!-- TODO figure: à recréer -->

- `QMessageBox.information(Fen, "Titre", "Texte")`

  **Exemple :** `QMessageBox.information(Fen, "Good", "données ajoutés avec succès")`

  ![Fenêtre d'information « Good » avec une icône i bleue, le message « données ajoutées avec succès » et un bouton OK](figures/qmessagebox-information.png)
  <!-- TODO figure: à recréer -->

- `QMessageBox.warning(Fen, "Titre", "Texte")`

  **Exemple :** `QMessageBox.warning(Fen, "Erreur", "Veuillez saisir vos données !")`

  ![Fenêtre d'avertissement « Erreur » avec une icône de triangle jaune, le message « Veuillez saisir vos données ! » et un bouton OK](figures/qmessagebox-warning.png)
  <!-- TODO figure: à recréer -->

- `QMessageBox.question(Fen, "Titre", "Texte")`

  **Exemple :** `QMessageBox.question(Fen, "Question", "Voulez-vous Continuer ?")`

  ![Fenêtre de question « Question » avec une icône de point d'interrogation, le message « Voulez-vous Continuer ? » et deux boutons Yes et No](figures/qmessagebox-question.png)
  <!-- TODO figure: à recréer -->

- `QMessageBox.about(Fen, "Titre", "Texte")` (sans icon)

  **Exemple :** `QMessageBox.about(Fen, "Erreur", "Veuillez saisir vos données !")`

  ![Fenêtre « Erreur » sans icône avec le message « Veuillez saisir vos données ! » et un bouton OK](figures/qmessagebox-about.png)
  <!-- TODO figure: à recréer -->

Voir plus : https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QMessageBox.html

<!-- TODO vérifier: dans le PDF le message de l'exemple « information » est écrit « données ajoutés avec succès » (code) et « données ajoutées avec succès » (capture) ; transcrit tel quel -->
