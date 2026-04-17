# Design : Visualisation de l'arbre de recherche

**Date :** 2026-04-17  
**Statut :** Approuvé

---

## Résumé

Après qu'un algorithme de résolution (BFS, DFS, A*) a terminé ou a été interrompu, l'utilisateur peut ouvrir une seconde fenêtre Pygame affichant l'arbre de recherche parcouru, animé nœud par nœud à vitesse réglable. La fenêtre principale reste inchangée et continue de fonctionner normalement.

---

## Contraintes

- L'affichage Sokoban existant (fenêtre principale 1200×880) reste **intact**. Aucune modification visuelle.
- Le code ajouté doit rester **le plus simple possible** — pas d'abstraction inutile.
- Sauvegarde de l'état actuel : tag git `v1.0-avant-graphe`.

---

## Quand le bouton est-il accessible ?

Le bouton **"Voir la résolution de graphe"** apparaît dans le panneau solver (sous la grille) uniquement quand `solver_status` est :

| Statut | Contenu affiché |
|--------|----------------|
| `done` | Exploration complète + chemin solution mis en évidence |
| `stopped` | Exploration jusqu'au moment de l'arrêt manuel |
| `no_solution` | Exploration complète de l'espace accessible |

En état `idle` ou `running`, le bouton est absent.

---

## Architecture

### Approche retenue : deuxième fenêtre Pygame indépendante

```
Fenêtre principale (1200×880)       Fenêtre graphe (1600×1000)
─────────────────────────────       ──────────────────────────
  [grille sokoban]                    [zone arbre | panneau droit]
  [bouton "Voir résolution"]  ──→     thread dédié, boucle Pygame séparée
```

La fenêtre graphe tourne dans un `threading.Thread` lancé au clic du bouton. Elle lit `exploration_log` et `solver_chemin` en **lecture seule** — pas de conflit de thread.

---

## Données exportées par `solveur()`

### Signature actuelle
```python
def solveur(matrice, mode='BFS', stop_flag=None):
    ...
    return chemin, etapes, len(visites)
```

### Nouvelle signature
```python
def solveur(matrice, mode='BFS', stop_flag=None):
    ...
    return chemin, etapes, len(visites), exploration_log
```

### Format de `exploration_log`

Liste ordonnée dans l'ordre de découverte des états :

- **BFS / DFS** : `[(état, parent), ...]`  
  - `état` : `((jx, jy), frozenset({(bx, by), ...}))`  
  - `parent` : même type, ou `None` pour la racine
- **A\*** : `[(état, parent, h_score), ...]`  
  - `h_score` : valeur heuristique (distance Manhattan) au moment de la découverte

La racine est toujours le premier élément, avec `parent = None`.

Construction dans `solveur()` : à chaque fois qu'un voisin est ajouté à `visites`, on l'appende à `exploration_log`. ~4 lignes de code supplémentaires.

---

## Modifications de `display_game.py`

### Dans `__init__`
```python
self.solver_exploration_log = []
```

### Dans `_reset_solver`
```python
self.solver_exploration_log = []
```

### Dans `_solver_worker`
```python
chemin, etapes, nb_visites, exploration_log = solveur(...)
self.solver_exploration_log = exploration_log
```

### Dans `_draw_solver`
Bouton ajouté sous la grille (côté gauche, sous SPLIT_X), visible si `solver_status in ("done", "stopped", "no_solution")` :
```python
Button(7, WINDOW_H - 80, 340, 57, "Voir la résolution de graphe", self.font_sm).draw(self.screen)
```

### Dans `_handle_solver`
```python
if self.solver_status in ("done", "stopped", "no_solution"):
    if Button(7, WINDOW_H - 80, 340, 57, "Voir la résolution de graphe", self.font_sm).clicked(event):
        self._open_graph_view()

def _open_graph_view(self):
    t = threading.Thread(
        target=_run_graph_window,
        args=(self.solver_exploration_log, self.solver_chemin, self.solver_algo),
        daemon=True,
    )
    t.start()
```

---

## Nouveau fichier `graph_view.py`

### Fenêtre

| Paramètre | Valeur |
|-----------|--------|
| Taille | 1600×1000 |
| Séparateur vertical | x = 1133 |
| Zone arbre | 0 → 1133px |
| Panneau droit | 1133 → 1600px (467px) |

### Import dans `display_game.py`

```python
from graph_view import _run_graph_window
```

`graph_view.py` **ne doit pas** importer depuis `display_game.py` (éviter import circulaire). Il redéfinit localement les constantes de couleur (mêmes valeurs RGB) et la classe `Slider` (code identique).

### Point d'entrée public

```python
def _run_graph_window(exploration_log, chemin, algo):
    """Lancé dans un thread. Ouvre la fenêtre et bloque jusqu'à fermeture."""
    win = GraphWindow(exploration_log, chemin, algo)
    win.run()
```

### Classe `GraphWindow`

**État interne :**
```
exploration_log   # données brutes (lecture seule)
chemin            # solution ou None
algo              # "BFS" | "DFS" | "Astar"
replay_index      # nœud courant dans le replay (0..len(exploration_log))
replay_running    # bool
scroll_y          # décalage vertical du canvas arbre (px)
speed_slider      # instance Slider réutilisée
node_positions    # dict état → (x, y) calculé une fois à l'init
hover_state       # état sous la souris ou None
```

**Méthodes :**
- `run()` — boucle principale Pygame
- `_compute_layout()` — calcule `node_positions` une fois pour toutes
- `_draw_tree()` — dessine arêtes + nœuds jusqu'à `replay_index`
- `_draw_panel()` — panneau droit : algo, stats, slider, boutons
- `_draw_hover_preview(état)` — mini-grille 80×80px au survol
- `_handle_event(event)` — scroll molette, clic boutons, hover

### Layout de l'arbre

- Racine en haut, centrée horizontalement dans la zone arbre
- Espacement vertical entre niveaux : **20px**
- Les enfants d'un nœud s'étalent horizontalement, centrés sous leur parent
- Pas de rendu force-directed — layout hiérarchique simple calculé en un seul passage

### Couleurs des nœuds

| État du nœud | Couleur |
|--------------|---------|
| Non encore apparu | invisible |
| Découvert (BFS/A* : tous) ou chemin actif (DFS) | `ACCENT_C` = (203, 166, 247) violet |
| DFS — backtrack / chemin mort | (80, 80, 100) gris foncé |
| Nœud courant du replay | blanc + halo 2px |
| Chemin solution | `CIBLE_C` = (166, 227, 161) vert |
| A* : nœud selon h_score | dégradé bleu (h élevé) → rouge (h=0) |

**BFS** : pas de backtrack — tous les nœuds découverts restent violets, seul le nœud courant est blanc.  
**DFS** : la chaîne racine→nœud courant est violette, les branches abandonnées sont grises.  
**A\*** : couleur par h_score, le nœud courant reste blanc.

### Scroll

- Molette souris : `scroll_y += / -= 30px`
- Clamped : `scroll_y` entre `0` et `max(0, tree_height - 900)`
- Toutes les positions `(x, y)` du canvas sont affichées à `(x, y - scroll_y)`

### Slider vitesse

Réutilise la classe `Slider` de `display_game.py` (importée depuis le même module).  
Plage : 1 → 50 nœuds/s. Valeur initiale : 10.

### Panneau droit (x=1133, largeur=467px)

```
y=40    Algorithme : BFS / DFS / A*
y=90    ──────────────────────────
y=120   Nœuds explorés : 0
y=160   Opérations     : 0
y=200   Chemin         : - coups  (si solution)
y=260   [slider vitesse]
y=360   [▶ Rejouer / ⏸ Pause]
y=440   [< Fermer]
```

### Mise en évidence DFS

Pendant le replay, le nœud courant est identifié. L'algo remonte dans `parent` pour colorier la chaîne racine→nœud courant en violet. Les nœuds qui ne sont pas sur ce chemin actif sont grisés. Quand le replay atteint un nœud sans enfant (cul-de-sac), il reçoit un marqueur rouge avant que la prochaine étape remonte.

### Manhattan distance (A* uniquement)

Au survol d'un nœud A*, la mini-grille (hover preview) affiche en plus des lignes fines reliant chaque caisse à sa cible la plus proche, avec la distance annotée.

---

## Ce qui ne change pas

- `build_game.py` : seule `solveur()` est modifiée (return + ~4 lignes)
- Toute la logique de jeu, les niveaux, `deplacer_joueur`, etc. : inchangés
- `display_game.py` : ~15 lignes ajoutées, rien modifié
- Aucun nouveau package Python requis (pygame déjà présent)
