# Design : display_game.py — Interface Pygame pour Sokoban

Date : 2026-04-16

## Contexte

`build_game.py` fournit toute la logique du jeu (constantes, niveaux 1-5, déplacement,
annulation, solveur BFS/DFS/A*). `display_game.py` doit construire l'interface graphique
par-dessus, **sans réécrire** les fonctions existantes.

Une modification mineure de `build_game.py` est prévue : `solveur()` sera étendue pour
retourner `(chemin, etapes, nb_visites)` au lieu de `chemin` seul.

---

## Architecture générale

**Bibliothèque :** Pygame  
**Fichiers touchés :**
- `build_game.py` — modification de `solveur()` uniquement
- `display_game.py` — toute l'interface (classe `App`)
- `scores.json` — créé automatiquement à la première victoire

**Classe principale : `App`**

```
App
├── show_home()          → écran d'accueil
├── show_level_select()  → sélection du niveau (mode: "joueur" ou "solver")
├── show_game()          → mode joueur
├── show_victory()       → saisie du prénom + sauvegarde
├── show_solver()        → mode solver (split-screen)
└── run()                → boucle pygame principale
```

L'état courant de l'application est stocké dans `self.screen_state` (string : `"home"`,
`"level_select"`, `"game"`, `"victory"`, `"solver"`). Chaque méthode `show_*()` met à
jour cet état et réinitialise les données propres à l'écran.

---

## Palette de couleurs

| Élément           | Couleur hex  |
|-------------------|--------------|
| Fond / sol        | `#1E1E2E`    |
| Mur               | `#45475A`    |
| Caisse            | `#F38BA8`    |
| Cible             | `#A6E3A1`    |
| Caisse sur cible  | `#89DCEB`    |
| Joueur            | `#CBA6F7`    |
| Boutons           | `#313244`    |
| Boutons (hover)   | `#585B70`    |
| Texte principal   | `#CDD6F4`    |
| Texte secondaire  | `#6C7086`    |

---

## Mode Joueur

### Navigation
```
Accueil → Sélection niveau → Page de jeu → Page victoire → Accueil
```

### Sélection du niveau
- 5 boutons numérotés (1 à 5)
- Bouton "Retour" vers l'accueil

### Page de jeu
- Grille centrée, taille de case adaptée à la résolution du niveau
- En haut : horloge (format mm:ss, mise à jour chaque seconde), compteur de coups
- En bas : bouton "Undo", bouton "Accueil"
- Contrôles clavier : flèches directionnelles
- Historique : `self.historique` est une liste de copies profondes de la matrice ;
  `annuler_mouvement(historique)` de `build_game.py` est appelé pour dépiler

### Détection de victoire
- Après chaque déplacement, `est_gagne(get_etat(matrice), matrice)` est appelé
- Si victoire → `show_victory()`

### Page victoire
- Affiche le niveau, le temps et le nombre de coups
- Champ de saisie pygame pour le prénom (max 12 caractères)
- Bouton "Valider" → enregistre dans `scores.json` :
  ```json
  {"prenom": "...", "niveau": 1, "temps": "01:23", "coups": 42}
  ```
- Retour automatique à l'accueil après validation

---

## Mode Solver

### Navigation
```
Accueil → Sélection niveau → Page solver
```

### Layout split-screen
- **Gauche (60% de la fenêtre)** : grille du jeu
- **Droite (40%)** : panneau de contrôle

### Panneau droit — avant résolution
- 3 boutons radio : BFS / DFS / A* (sélection exclusive)
- Curseur de vitesse : de 1 coup/s (lent) à 10 coups/s (rapide)
- Bouton "Résoudre" → lance `solveur(matrice, mode)` dans un `threading.Thread`
  pour ne pas bloquer l'affichage
- Label "Calcul en cours..." affiché pendant le traitement

### Panneau droit — après résolution
- Nombre d'opérations (`etapes` retourné par `solveur`)
- Nombre de sommets explorés (`nb_visites` retourné par `solveur`)
- Nombre de coups de la solution (`len(chemin) - 1`)
- La replay démarre automatiquement

### Animation de la replay
- Les états du chemin sont comparés deux à deux pour déduire la direction :
  `direction = (nx - jx, ny - jy)` entre deux positions joueur consécutives
- `deplacer_joueur(matrice, direction)` est appelé à chaque tick d'animation
- Le timer d'animation est recalculé en temps réel selon la position du curseur
- Pendant la replay, le curseur de vitesse reste actif

### Bouton "Accueil"
Présent sur tous les écrans, interrompt immédiatement tout thread en cours (flag
`self.solver_stop`).

---

## Modification de build_game.py

La fonction `solveur()` est modifiée pour retourner un tuple :

```python
# Avant
return reconstruire_chemin(prev, actuel)

# Après
return reconstruire_chemin(prev, actuel), etapes, len(visites)
```

Et en cas d'échec :
```python
# Avant
return None

# Après
return None, etapes, len(visites)
```

---

## Gestion des données persistantes

- `scores.json` à la racine du projet
- Structure : liste JSON d'objets `{prenom, niveau, temps, coups}`
- Lecture/écriture avec `json` (stdlib)
- Le fichier est créé s'il n'existe pas

---

## Dépendances

- `pygame` (à installer via `pip install pygame`)
- `build_game` (import local)
- `json`, `threading`, `copy`, `time` (stdlib)
