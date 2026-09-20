/**
 * The landing page's playable demo: three chapter-1 exercises with answers
 * written by hand, in the course's own notation.
 *
 * Written, not generated: a visitor tries Fahem before signing in, so these
 * must cost no token, never vary, and never be wrong. They are marketing
 * copy that happens to be a solution - the real tutor's answers come from
 * the model, grounded in the chapter (see app/llm/prompts.py).
 *
 * `answer` is the markdown the chat itself renders, so the demo shows the
 * real components: the Algorithme | Python table, its copy button, and
 * "▶ Exécuter le Python".
 */

const somme = {
  id: "somme",
  tab: "La somme",
  short: "Lire deux entiers, afficher leur somme.",
  statement:
    "Écrire un algorithme qui lit deux entiers A et B, calcule leur somme et l'affiche.",
  hint: "Tu as besoin de trois variables entières : les deux nombres lus, et la somme.\n\n**Indice** : additionne les deux valeurs lues et range le résultat dans une troisième variable avec `←`.\n\nQuelle instruction écrirais-tu pour calculer la somme ?",
  answer: `**Ce que demande l'exercice** : lire deux entiers, les additionner, afficher le résultat.

### Tableau de déclaration

| Objet | Nature/type |
|---|---|
| A | entier |
| B | entier |
| S | entier |

### Solution

| Algorithme | Python |
|---|---|
| Début | |
| Ecrire ("Donner A : ") | |
| Lire (A) | A = int(input("Donner A : ")) |
| Ecrire ("Donner B : ") | |
| Lire (B) | B = int(input("Donner B : ")) |
| S ← A + B | S = A + B |
| Ecrire ("La somme est ", S) | print("La somme est ", S) |
| Fin | |`,
  trace: `### Trace d'exécution (A = 7, B = 5)

| Étape | A | B | S |
|---|---|---|---|
| Lecture de A | 7 | – | – |
| Lecture de B | 7 | 5 | – |
| S ← A + B | 7 | 5 | 12 |

**Résultat** : le programme affiche \`La somme est 12\`.`,
  attempt: "Début\nLire (A)\nLire (B)\nS = A + B\nEcrire (S)\nFin",
  check: {
    verdict: "presque",
    content: `**Verdict : Presque**

**Ce qui est juste**
- Les deux lectures et le calcul de la somme.
- L'affichage du résultat.

**À corriger**

| Ligne | Ce que tu as écrit | Problème | Correction |
|---|---|---|---|
| 4 | S = A + B | En algorithme l'affectation s'écrit ←, pas = | S ← A + B |
| – | (rien) | Le tableau de déclaration est obligatoire avant l'algorithme | Ajoute A, B et S en entier |

**Test sur un exemple** : A = 7 et B = 5 donnent bien 12, mais le \`=\` coûte des points sur ta copie.

**À corriger en premier** : remplace \`=\` par \`←\`. Le reste de ton raisonnement est bon, continue comme ça !`,
  },
};

const carre = {
  id: "carre",
  tab: "Le carré",
  short: "Lire un réel, afficher son carré.",
  statement: "Écrire un algorithme qui lit un nombre réel X et affiche son carré.",
  hint: "Il te faut deux variables réelles : le nombre lu et son carré.\n\n**Indice** : multiplier un nombre par lui-même suffit, il n'y a pas de fonction à connaître ici.\n\nÉcris l'instruction qui calcule le carré.",
  answer: `**Ce que demande l'exercice** : lire un réel et afficher son carré.

### Tableau de déclaration

| Objet | Nature/type |
|---|---|
| X | réel |
| carre | réel |

### Solution

| Algorithme | Python |
|---|---|
| Début | |
| Ecrire ("Donner X : ") | |
| Lire (X) | X = float(input("Donner X : ")) |
| carre ← X * X | carre = X * X |
| Ecrire ("Le carré est ", carre) | print("Le carré est ", carre) |
| Fin | |`,
  trace: `### Trace d'exécution (X = 2.5)

| Étape | X | carre |
|---|---|---|
| Lecture de X | 2.5 | – |
| carre ← X * X | 2.5 | 6.25 |

**Résultat** : le programme affiche \`Le carré est 6.25\`.`,
  attempt: "Début\nLire (X)\ncarre ← X ** 2\nEcrire (carre)\nFin",
  check: {
    verdict: "a_revoir",
    content: `**Verdict : À revoir**

**Ce qui est juste**
- La lecture de X et l'affichage du résultat.

**À corriger**

| Ligne | Ce que tu as écrit | Problème | Correction |
|---|---|---|---|
| 3 | carre ← X ** 2 | \`**\` est un opérateur Python, il n'existe pas dans le cours | carre ← X * X |
| – | (rien) | Il manque le tableau de déclaration (X et carre en réel) | Objet \\| Nature/type |

**Test sur un exemple** : pour X = 2.5, la bonne réponse est 6.25.

**À corriger en premier** : écris la multiplication avec \`*\`. Tu y es presque !`,
  },
};

const chiffres = {
  id: "chiffres",
  tab: "Les chiffres",
  short: "Séparer les dizaines et les unités d'un nombre.",
  statement:
    "Écrire un algorithme qui lit un entier N de deux chiffres et affiche son chiffre des dizaines et son chiffre des unités.",
  hint: "Deux opérateurs du cours suffisent : l'un donne le quotient d'une division entière, l'autre son reste.\n\n**Indice** : `div` te donne la partie entière d'une division, `mod` le reste.\n\nLequel utiliserais-tu pour les dizaines ?",
  answer: `**Ce que demande l'exercice** : séparer les deux chiffres d'un nombre entre 10 et 99.

### Tableau de déclaration

| Objet | Nature/type |
|---|---|
| N | entier |
| d | entier |
| u | entier |

### Solution

| Algorithme | Python |
|---|---|
| Début | |
| Ecrire ("Donner N : ") | |
| Lire (N) | N = int(input("Donner N : ")) |
| d ← N div 10 | d = N // 10 |
| u ← N mod 10 | u = N % 10 |
| Ecrire ("Dizaines : ", d) | print("Dizaines : ", d) |
| Ecrire ("Unités : ", u) | print("Unités : ", u) |
| Fin | |`,
  trace: `### Trace d'exécution (N = 47)

| Étape | N | d | u |
|---|---|---|---|
| Lecture de N | 47 | – | – |
| d ← N div 10 | 47 | 4 | – |
| u ← N mod 10 | 47 | 4 | 7 |

**Résultat** : le programme affiche \`Dizaines : 4\` puis \`Unités : 7\`.`,
  attempt: "Début\nLire (N)\nd ← N // 10\nu ← N % 10\nEcrire (d, u)\nFin",
  check: {
    verdict: "presque",
    content: `**Verdict : Presque**

**Ce qui est juste**
- La démarche est la bonne : quotient pour les dizaines, reste pour les unités.

**À corriger**

| Ligne | Ce que tu as écrit | Problème | Correction |
|---|---|---|---|
| 3 | d ← N // 10 | \`//\` est du Python ; en algorithme on écrit \`div\` | d ← N div 10 |
| 4 | u ← N % 10 | \`%\` est du Python ; en algorithme on écrit \`mod\` | u ← N mod 10 |

**Test sur un exemple** : pour N = 47, tu obtiens bien 4 et 7.

**À corriger en premier** : remplace \`//\` et \`%\` par \`div\` et \`mod\`. C'est l'erreur qui coûte le plus de points, et tu ne la feras plus !`,
  },
};

export const DEMO_EXERCISES = [somme, carre, chiffres];
