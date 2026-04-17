# Graph View — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter une fenêtre Pygame séparée affichant l'arbre de recherche animé de l'algorithme de résolution Sokoban (BFS/DFS/A*), accessible après résolution complète, partielle ou interrompue.

**Architecture:** `solveur()` retourne un `exploration_log` en plus de ses valeurs actuelles. `display_game.py` reçoit quelques lignes pour stocker ce log et ouvrir la fenêtre via `multiprocessing`. Tout le rendu vit dans le nouveau fichier `graph_view.py`.

**Note Pygame :** Pygame ne supporte qu'une seule fenêtre par processus. On utilise `multiprocessing.get_context('spawn').Process` (pas `threading.Thread`) pour obtenir une vraie deuxième fenêtre dans un processus fils indépendant.

**Tech Stack:** Python 3, Pygame 2, multiprocessing (stdlib), collections.deque (stdlib)

---

## Fichiers touchés

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `build_game.py` | Modifier | `solveur()` retourne `exploration_log` en 4ème valeur |
| `display_game.py` | Modifier | Stocker le log, afficher le bouton, lancer le processus |
| `graph_view.py` | Créer | Toute la fenêtre graphe : layout, rendu, replay, scroll |
| `tests/test_solveur_log.py` | Créer | Tests unitaires sur `solveur()` et le layout |

---

## Task 1 : Modifier `solveur()` — ajouter `exploration_log`

**Files:**
- Modify: `build_game.py:254-294`

### Objectif

`solveur()` doit retourner une 4ème valeur : liste ordonnée des états découverts avec leur parent (et h_score pour A*).

- [ ] **Étape 1 : Créer le fichier de tests**

Créer `tests/test_solveur_log.py` :

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from build_game import solveur, charger_niveau, get_etat
import copy

def test_solveur_retourne_4_valeurs():
    m = copy.deepcopy(charger_niveau(1))
    result = solveur(m, mode='BFS')
    assert len(result) == 4, f"Attendu 4 valeurs, obtenu {len(result)}"

def test_exploration_log_bfs_format():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='BFS')
    assert len(log) > 0
    # Premier entrée = racine, parent None
    etat0, parent0 = log[0]
    assert parent0 is None
    # Toutes les autres entrées ont un parent
    for etat, parent in log[1:]:
        assert parent is not None

def test_exploration_log_astar_a_h_score():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='Astar')
    assert len(log) > 0
    # Toutes les entrées ont 3 éléments
    for entry in log:
        assert len(entry) == 3, f"A* attendu 3 éléments par entrée, obtenu {len(entry)}"
        etat, parent, h = entry
        assert isinstance(h, (int, float))
        assert h >= 0

def test_exploration_log_dfs_format():
    m = copy.deepcopy(charger_niveau(1))
    chemin, etapes, nb_visites, log = solveur(m, mode='DFS')
    assert len(log) > 0
    etat0, parent0 = log[0]
    assert parent0 is None

def test_log_pas_de_doublons():
    m = copy.deepcopy(charger_niveau(1))
    _, _, _, log = solveur(m, mode='BFS')
    etats = [entry[0] for entry in log]
    assert len(etats) == len(set(etats)), "Chaque état doit apparaître une seule fois"

def test_nb_visites_coherent_avec_log():
    m = copy.deepcopy(charger_niveau(1))
    _, _, nb_visites, log = solveur(m, mode='BFS')
    assert nb_visites == len(log)
```

- [ ] **Étape 2 : Lancer les tests — vérifier qu'ils échouent**

```bash
cd /data/michel/Documents/auto-sokoban
python -m pytest tests/test_solveur_log.py -v 2>&1 | head -30
```

Résultat attendu : `FAILED` (solveur retourne 3 valeurs, pas 4).

- [ ] **Étape 3 : Modifier `solveur()` dans `build_game.py`**

Remplacer la fonction `solveur` entière (lignes 254-294) :

```python
def solveur(matrice, mode='BFS', stop_flag=None):
    etat_initial = get_etat(matrice)
    prev = {etat_initial: None}

    if mode == 'Astar':
        file_ou_pile = [(0, etat_initial)]
        h0 = heuristique(etat_initial, matrice)
        exploration_log = [(etat_initial, None, h0)]
    else:
        file_ou_pile = [etat_initial]
        exploration_log = [(etat_initial, None)]

    visites = {etat_initial}
    etapes = 0

    while file_ou_pile:
        etapes += 1

        if stop_flag is not None and etapes % 500 == 0 and stop_flag():
            return None, etapes, len(visites), exploration_log

        if mode == 'BFS':
            actuel = file_ou_pile.pop(0)
        elif mode == 'DFS':
            actuel = file_ou_pile.pop()
        elif mode == 'Astar':
            priorite, actuel = heapq.heappop(file_ou_pile)

        if est_gagne(actuel, matrice):
            return reconstruire_chemin(prev, actuel), etapes, len(visites), exploration_log

        for voisin in get_voisins(actuel, matrice):
            if voisin not in visites:
                visites.add(voisin)
                prev[voisin] = actuel
                if mode == 'Astar':
                    h = heuristique(voisin, matrice)
                    f_score = etapes + h
                    heapq.heappush(file_ou_pile, (f_score, voisin))
                    exploration_log.append((voisin, actuel, h))
                else:
                    file_ou_pile.append(voisin)
                    exploration_log.append((voisin, actuel))

    return None, etapes, len(visites), exploration_log
```

- [ ] **Étape 4 : Lancer les tests — vérifier qu'ils passent**

```bash
python -m pytest tests/test_solveur_log.py -v
```

Résultat attendu : tous les tests `PASSED`.

- [ ] **Étape 5 : Commit**

```bash
git add build_game.py tests/test_solveur_log.py
git commit -m "feat: solveur() retourne exploration_log en 4ème valeur"
```

---

## Task 2 : Mettre à jour `display_game.py`

**Files:**
- Modify: `display_game.py`

### Objectif

Stocker `exploration_log`, afficher le bouton "Voir la résolution de graphe", lancer le processus graphe.

- [ ] **Étape 1 : Corriger le dépaquetage dans `_solver_worker`**

Dans `display_game.py`, ligne ~292, remplacer :

```python
    def _solver_worker(self):
        chemin, etapes, nb_visites = solveur(
            copy.deepcopy(self.matrice_solver_init), self.solver_algo,
            stop_flag=lambda: self.solver_stop,
        )
```

par :

```python
    def _solver_worker(self):
        chemin, etapes, nb_visites, exploration_log = solveur(
            copy.deepcopy(self.matrice_solver_init), self.solver_algo,
            stop_flag=lambda: self.solver_stop,
        )
        self.solver_exploration_log = exploration_log
```

- [ ] **Étape 2 : Ajouter les attributs dans `__init__`**

Dans `__init__`, après la ligne `self.solver_visites = 0` (~ligne 138), ajouter :

```python
        self.solver_exploration_log  = []
        self.solver_targets          = []   # positions (x,y) des CIBLE dans la matrice
```

- [ ] **Étape 3 : Réinitialiser les attributs dans `_reset_solver`**

Dans `_reset_solver`, après la ligne `self.solver_visites = 0`, ajouter :

```python
        self.solver_exploration_log  = []
        self.solver_targets          = []
```

- [ ] **Étape 4 : Ajouter le bouton dans `_draw_solver`**

Dans `_draw_solver`, juste avant la ligne qui dessine `"< Accueil"` (~ligne 233), ajouter :

```python
        if self.solver_status in ("done", "stopped", "no_solution"):
            Button(7, WINDOW_H - 160, 340, 57,
                   "Voir la résolution de graphe", self.font_sm).draw(self.screen)
```

- [ ] **Étape 5 : Ajouter le handler dans `_handle_solver` et la méthode `_open_graph_view`**

Dans `_handle_solver`, après le bloc `elif self.solver_status in ("done", "no_solution", "stopped"):`, ajouter la détection du nouveau bouton :

```python
        if self.solver_status in ("done", "stopped", "no_solution"):
            if Button(7, WINDOW_H - 160, 340, 57,
                      "Voir la résolution de graphe", self.font_sm).clicked(event):
                self._open_graph_view()
```

Ajouter la méthode `_open_graph_view` dans la classe `App`, après `_reset_solver` :

```python
    def _open_graph_view(self):
        import multiprocessing
        from graph_view import _run_graph_process
        # Extraire les positions des cibles depuis la matrice initiale
        from build_game import CIBLE
        targets = [
            (x, y)
            for y, row in enumerate(self.matrice_solver_init)
            for x, val in enumerate(row)
            if val == CIBLE
        ]
        ctx = multiprocessing.get_context('spawn')
        p = ctx.Process(
            target=_run_graph_process,
            args=(self.solver_exploration_log, self.solver_chemin,
                  self.solver_algo, targets),
            daemon=True,
        )
        p.start()
```

- [ ] **Étape 6 : Vérifier que l'application démarre sans erreur**

```bash
cd /data/michel/Documents/auto-sokoban
python display_game.py &
sleep 2
kill %1
echo "OK si pas d'erreur"
```

Résultat attendu : Pygame démarre, pas d'ImportError (même si `graph_view.py` n'existe pas encore, l'import est dans la méthode donc pas déclenché au démarrage).

- [ ] **Étape 7 : Commit**

```bash
git add display_game.py
git commit -m "feat: bouton 'Voir la résolution de graphe' + plumbing display_game"
```

---

## Task 3 : Créer `graph_view.py` — squelette fonctionnel

**Files:**
- Create: `graph_view.py`

### Objectif

Fenêtre 1600×1000 qui s'ouvre, affiche un fond, et se ferme proprement. Pas encore de rendu d'arbre.

- [ ] **Étape 1 : Créer `graph_view.py` avec le squelette**

```python
import pygame
import sys
from collections import deque

# ── Constantes (mêmes valeurs que display_game.py, pas d'import croisé) ──
GW, GH   = 1600, 1000
SPLIT_X  = 1133          # séparateur zone arbre / panneau droit

FOND        = (30,  30,  46)
MUR_C       = (69,  71,  90)
SOL_C       = (49,  50,  68)
CAISSE_C    = (243, 139, 168)
CIBLE_C     = (166, 227, 161)
CAISSE_CIBLE_C = (137, 220, 235)
BTN_C       = (49,  50,  68)
BTN_HOVER_C = (88,  91, 112)
TEXTE_C     = (205, 214, 244)
TEXTE2_C    = (108, 112, 134)
ACCENT_C    = (203, 166, 247)

MUR    = -1
SOL    =  0
CIBLE  =  1
CAISSE =  2
JOUEUR =  3
CAISSE_SUR_CIBLE = 4
JOUEUR_SUR_CIBLE = 5

MAX_NODES = 10_000   # cap : on n'affiche pas plus de N nœuds

LEVEL_H   = 20       # hauteur en px entre deux niveaux de l'arbre
NODE_R    =  3       # rayon des nœuds en px

# ── Slider (copie de display_game.py) ────────────────────────────────────
class Slider:
    def __init__(self, x, y, w, min_val, max_val, initial, font):
        self.track    = pygame.Rect(x, y, w, 11)
        self.min_val  = min_val
        self.max_val  = max_val
        self.value    = initial
        self.font     = font
        self.dragging = False

    @property
    def handle_x(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.track.x + ratio * self.track.w)

    def draw(self, surface):
        pygame.draw.rect(surface, BTN_C, self.track, border_radius=5)
        hx = self.handle_x
        pygame.draw.rect(surface, ACCENT_C,
                         pygame.Rect(hx - 11, self.track.y - 8, 22, 27),
                         border_radius=5)
        label = self.font.render(f"Vitesse : {self.value} nœuds/s", True, TEXTE_C)
        surface.blit(label, (self.track.x, self.track.y - 37))

    def handle_event(self, event):
        hx = self.handle_x
        handle_rect = pygame.Rect(hx - 11, self.track.y - 8, 22, 27)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle_rect.collidepoint(event.pos) or self.track.collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])

    def _set_from_mouse(self, mx):
        ratio = (mx - self.track.x) / self.track.w
        ratio = max(0.0, min(1.0, ratio))
        self.value = round(self.min_val + ratio * (self.max_val - self.min_val))


# ── Button (copie de display_game.py) ────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font

    def draw(self, surface):
        color = BTN_HOVER_C if self.rect.collidepoint(pygame.mouse.get_pos()) else BTN_C
        pygame.draw.rect(surface, color, self.rect, border_radius=14)
        surf = self.font.render(self.text, True, TEXTE_C)
        surface.blit(surf, surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── GraphWindow ───────────────────────────────────────────────────────────
class GraphWindow:
    def __init__(self, exploration_log, chemin, algo, targets=None):
        self.exploration_log = exploration_log[:MAX_NODES]
        self.chemin          = chemin        # liste d'états solution ou None
        self.algo            = algo
        self.targets         = targets or []  # positions (x,y) des cibles dans la matrice

        self.replay_index   = 0
        self.replay_running = False
        self.replay_timer   = 0
        self.scroll_y       = 0
        self.hover_state    = None

        self.node_positions = {}   # état → (x, y) absolu dans le canvas
        self.parent_of      = {}   # état → état parent
        self.tree_height    = 0    # hauteur totale du canvas

        pygame.init()
        self.screen = pygame.display.set_mode((GW, GH))
        pygame.display.set_caption("Résolution de graphe")
        self.clock  = pygame.time.Clock()
        self.font   = pygame.font.SysFont("DejaVu Sans Mono", 29)
        self.font_sm = pygame.font.SysFont("DejaVu Sans Mono", 24)

        self.speed_slider = Slider(
            SPLIT_X + 27, 380, 420, 1, 50, 10, self.font_sm)

        self._compute_layout()

    def run(self):
        while True:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                self._handle_event(event)
            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _update(self, dt):
        pass   # rempli en Task 7

    def _draw(self):
        self.screen.fill(FOND)
        pygame.draw.line(self.screen, MUR_C, (SPLIT_X, 0), (SPLIT_X, GH), 3)
        self._draw_tree()
        self._draw_panel()
        if self.hover_state and self.hover_state in self.node_positions:
            self._draw_hover_preview(self.hover_state)

    def _compute_layout(self):
        pass   # rempli en Task 4

    def _draw_tree(self):
        pass   # rempli en Task 5

    def _draw_panel(self):
        pass   # rempli en Task 6

    def _draw_hover_preview(self, state):
        pass   # rempli en Task 8

    def _handle_event(self, event):
        pass   # rempli en Task 7 + 8


# ── Point d'entrée multiprocessing ───────────────────────────────────────
def _run_graph_process(exploration_log, chemin, algo, targets=None):
    """Appelé dans un processus fils spawn. Ouvre la fenêtre graphe."""
    win = GraphWindow(exploration_log, chemin, algo, targets)
    win.run()


if __name__ == '__main__':
    # Pour test direct (développement)
    _run_graph_process([], None, 'BFS')
```

- [ ] **Étape 2 : Vérifier que le squelette s'ouvre**

```bash
cd /data/michel/Documents/auto-sokoban
python graph_view.py
```

Résultat attendu : fenêtre 1600×1000 fond sombre avec une ligne verticale, aucune erreur. Fermer manuellement.

- [ ] **Étape 3 : Commit**

```bash
git add graph_view.py
git commit -m "feat: graph_view.py squelette — fenêtre 1600x1000 fonctionnelle"
```

---

## Task 4 : Implémenter `_compute_layout()`

**Files:**
- Modify: `graph_view.py` (méthode `_compute_layout`)
- Modify: `tests/test_solveur_log.py` (ajouter tests layout)

### Objectif

Calculer `node_positions` : pour chaque état de `exploration_log`, une position `(x, y)` absolue dans le canvas. Utiliser un layout hiérarchique simple : profondeur = ligne, index dans la profondeur = colonne.

- [ ] **Étape 1 : Ajouter les tests de layout**

Ajouter dans `tests/test_solveur_log.py` :

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# (déjà présent en haut du fichier)

def _make_graph_window_stub(algo='BFS'):
    """Crée un GraphWindow minimal sans pygame pour tester le layout."""
    from build_game import solveur, charger_niveau
    import copy
    m = copy.deepcopy(charger_niveau(1))
    _, _, _, log = solveur(m, mode=algo)

    # Patch minimal : créer l'objet sans pygame.init()
    import graph_view
    obj = object.__new__(graph_view.GraphWindow)
    obj.exploration_log = log[:graph_view.MAX_NODES]
    obj.chemin          = None
    obj.algo            = algo
    obj.node_positions  = {}
    obj.parent_of       = {}
    obj.tree_height     = 0
    obj._compute_layout()
    return obj

def test_layout_bfs_positions_uniques():
    gw = _make_graph_window_stub('BFS')
    positions = list(gw.node_positions.values())
    # Pas de deux nœuds exactement au même endroit
    assert len(positions) == len(set(positions))

def test_layout_racine_en_haut():
    gw = _make_graph_window_stub('BFS')
    from build_game import charger_niveau, get_etat
    import copy
    m = copy.deepcopy(charger_niveau(1))
    etat_racine = get_etat(m)
    x, y = gw.node_positions[etat_racine]
    # Racine doit avoir le y minimum
    min_y = min(py for _, py in gw.node_positions.values())
    assert y == min_y

def test_layout_tous_les_etats_places():
    gw = _make_graph_window_stub('BFS')
    for entry in gw.exploration_log:
        etat = entry[0]
        assert etat in gw.node_positions
```

- [ ] **Étape 2 : Lancer les tests — vérifier qu'ils échouent**

```bash
python -m pytest tests/test_solveur_log.py::test_layout_bfs_positions_uniques -v
```

Résultat attendu : `FAILED` (AttributeError ou positions vides).

- [ ] **Étape 3 : Implémenter `_compute_layout()`**

Remplacer `def _compute_layout(self): pass` dans `graph_view.py` par :

```python
    def _compute_layout(self):
        if not self.exploration_log:
            return

        # Construire parent_of et children
        children = {}   # état → [enfants]
        root = None
        for entry in self.exploration_log:
            etat, parent = entry[0], entry[1]
            self.parent_of[etat] = parent
            if parent is None:
                root = etat
            else:
                children.setdefault(parent, []).append(etat)

        # BFS pour affecter une profondeur à chaque nœud
        depth_nodes = {}   # profondeur → [états dans l'ordre de découverte]
        depth_of    = {}
        queue = deque([(root, 0)])
        while queue:
            etat, d = queue.popleft()
            depth_of[etat] = d
            depth_nodes.setdefault(d, []).append(etat)
            for child in children.get(etat, []):
                queue.append((child, d + 1))

        # Calcul des positions (x, y) pour chaque nœud
        ZONE_W  = SPLIT_X - 20   # largeur utile de la zone arbre
        MARGIN  = 30
        usable  = ZONE_W - 2 * MARGIN

        for depth, nodes in depth_nodes.items():
            count = len(nodes)
            y = 40 + depth * LEVEL_H
            for i, etat in enumerate(nodes):
                if count == 1:
                    x = MARGIN + usable // 2
                else:
                    x = MARGIN + int(i / (count - 1) * usable)
                self.node_positions[etat] = (x, y)

        self.tree_height = 40 + max(depth_nodes.keys()) * LEVEL_H + 40
```

- [ ] **Étape 4 : Lancer les tests — vérifier qu'ils passent**

```bash
python -m pytest tests/test_solveur_log.py -v
```

Résultat attendu : tous `PASSED`.

- [ ] **Étape 5 : Commit**

```bash
git add graph_view.py tests/test_solveur_log.py
git commit -m "feat: _compute_layout() — layout hiérarchique de l'arbre"
```

---

## Task 5 : Implémenter `_draw_tree()`

**Files:**
- Modify: `graph_view.py` (méthode `_draw_tree`)

### Objectif

Dessiner les arêtes et les nœuds jusqu'à `replay_index`, avec les couleurs adaptées à l'algorithme.

- [ ] **Étape 1 : Implémenter `_draw_tree()`**

Remplacer `def _draw_tree(self): pass` par :

```python
    def _draw_tree(self):
        if not self.node_positions:
            return

        log     = self.exploration_log
        visible = log[:self.replay_index + 1]   # états déjà "apparus"

        # Ensemble des états visibles
        visible_set = {e[0] for e in visible}

        # Chemin solution (pour coloration verte)
        solution_set = set()
        if self.chemin:
            solution_set = {etat for etat in self.chemin if etat in self.node_positions}

        # Chemin actif DFS : chaîne racine → nœud courant
        active_path = set()
        if self.algo == 'DFS' and visible:
            etat = visible[-1][0]
            while etat is not None:
                active_path.add(etat)
                etat = self.parent_of.get(etat)

        # Surface de clip pour la zone arbre (évite de déborder sur le panneau)
        clip = pygame.Rect(0, 0, SPLIT_X, GH)
        self.screen.set_clip(clip)

        # ── Dessiner les arêtes ──
        for entry in visible:
            etat, parent = entry[0], entry[1]
            if parent is None or parent not in self.node_positions:
                continue
            x1, y1 = self.node_positions[parent]
            x2, y2 = self.node_positions[etat]
            y1 -= self.scroll_y
            y2 -= self.scroll_y
            if -10 < y1 < GH or -10 < y2 < GH:   # culling basique
                pygame.draw.line(self.screen, (60, 60, 80), (x1, y1), (x2, y2), 1)

        # ── Dessiner les nœuds ──
        current_state = visible[-1][0] if visible else None

        for entry in visible:
            etat = entry[0]
            x, y = self.node_positions[etat]
            y -= self.scroll_y
            if y < -NODE_R or y > GH + NODE_R:
                continue   # hors écran

            # Couleur du nœud
            if etat == current_state:
                color = (255, 255, 255)
                r = NODE_R + 2
            elif etat in solution_set:
                color = CIBLE_C
                r = NODE_R + 1
            elif self.algo == 'DFS':
                color = ACCENT_C if etat in active_path else (80, 80, 100)
                r = NODE_R
            elif self.algo == 'Astar':
                h = entry[2] if len(entry) == 3 else 0
                # dégradé bleu (h élevé) → rouge (h=0)
                # max_h calculé depuis le log (première fois, mémorisé)
                if not hasattr(self, '_max_h'):
                    self._max_h = max(
                        (e[2] for e in self.exploration_log if len(e) == 3),
                        default=1) or 1
                t = min(1.0, h / self._max_h)
                r_c = int(220 * (1 - t))
                b_c = int(220 * t)
                color = (r_c, 60, b_c)
                r = NODE_R
            else:   # BFS
                color = ACCENT_C
                r = NODE_R

            pygame.draw.circle(self.screen, color, (x, y), r)
            if etat == current_state:
                pygame.draw.circle(self.screen, ACCENT_C, (x, y), r + 3, 1)

        self.screen.set_clip(None)
```

- [ ] **Étape 2 : Vérifier visuellement**

```bash
python graph_view.py
```

La fenêtre s'ouvre avec fond sombre et ligne verticale. Pas encore de rendu car `replay_index=0` et `_compute_layout` ne tourne pas sans données. Normal à ce stade.

- [ ] **Étape 3 : Commit**

```bash
git add graph_view.py
git commit -m "feat: _draw_tree() — rendu nœuds + arêtes avec couleurs algo"
```

---

## Task 6 : Implémenter `_draw_panel()`

**Files:**
- Modify: `graph_view.py` (méthode `_draw_panel`)

### Objectif

Panneau droit (x=1133, largeur=467px) : algo, stats, slider, boutons.

- [ ] **Étape 1 : Implémenter `_draw_panel()`**

Remplacer `def _draw_panel(self): pass` par :

```python
    def _draw_panel(self):
        RX = SPLIT_X + 27

        # Algorithme
        algo_label = {"BFS": "BFS", "DFS": "DFS", "Astar": "A*"}
        self.screen.blit(
            self.font.render(f"Algorithme : {algo_label.get(self.algo, self.algo)}",
                             True, TEXTE2_C), (RX, 47))

        pygame.draw.line(self.screen, MUR_C,
                         (SPLIT_X + 10, 90), (GW - 10, 90), 1)

        # Stats
        total    = len(self.exploration_log)
        visible  = self.replay_index + 1 if self.exploration_log else 0
        coups    = (len(self.chemin) - 1) if self.chemin else 0

        lines = [
            f"Nœuds explorés : {total}",
            f"Affichés        : {visible}",
            f"Opérations      : {total}",
        ]
        if self.chemin:
            lines.append(f"Chemin solution : {coups} coups")
        if total >= MAX_NODES:
            lines.append(f"(limité à {MAX_NODES} nœuds)")

        for i, line in enumerate(lines):
            self.screen.blit(
                self.font_sm.render(line, True, TEXTE_C), (RX, 120 + i * 40))

        # Slider vitesse
        self.speed_slider.draw(self.screen)

        # Bouton Rejouer / Pause
        btn_label = "⏸ Pause" if self.replay_running else "▶ Rejouer"
        Button(RX, 460, 420, 67, btn_label, self.font).draw(self.screen)

        # Bouton Fermer
        Button(RX, GH - 93, 420, 67, "✕ Fermer", self.font_sm).draw(self.screen)
```

- [ ] **Étape 2 : Vérifier visuellement**

```bash
python graph_view.py
```

Le panneau droit doit afficher le texte, le slider et les boutons. Fermer manuellement.

- [ ] **Étape 3 : Commit**

```bash
git add graph_view.py
git commit -m "feat: _draw_panel() — panneau droit stats + slider + boutons"
```

---

## Task 7 : Replay animé

**Files:**
- Modify: `graph_view.py` (méthodes `_update`, `_handle_event`)

### Objectif

Le slider contrôle la vitesse. ▶ Rejouer lance le replay nœud par nœud. ⏸ Pause le stoppe. À la fin du replay, s'arrête.

- [ ] **Étape 1 : Implémenter `_update()`**

Remplacer `def _update(self, dt): pass` par :

```python
    def _update(self, dt):
        if not self.replay_running:
            return
        speed    = self.speed_slider.value   # nœuds/s
        interval = 1000 / speed              # ms entre chaque nœud
        self.replay_timer += dt
        while self.replay_timer >= interval:
            self.replay_timer -= interval
            if self.replay_index < len(self.exploration_log) - 1:
                self.replay_index += 1
            else:
                self.replay_running = False
                break
```

- [ ] **Étape 2 : Implémenter `_handle_event()`**

Remplacer `def _handle_event(self, event): pass` par :

```python
    def _handle_event(self, event):
        # Slider vitesse
        self.speed_slider.handle_event(event)

        # Scroll molette
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            max_scroll = max(0, self.tree_height - GH + 40)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            RX = SPLIT_X + 27

            # Bouton Rejouer / Pause
            if Button(RX, 460, 420, 67,
                      "⏸ Pause" if self.replay_running else "▶ Rejouer",
                      self.font).clicked(event):
                if self.replay_running:
                    self.replay_running = False
                else:
                    # Si replay terminé, recommencer depuis le début
                    if self.replay_index >= len(self.exploration_log) - 1:
                        self.replay_index   = 0
                        self.replay_timer   = 0
                    self.replay_running = True

            # Bouton Fermer
            if Button(RX, GH - 93, 420, 67, "✕ Fermer", self.font_sm).clicked(event):
                pygame.quit()
                sys.exit()

        # Hover pour mini-grille (détection dans la zone arbre)
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx < SPLIT_X:
                self.hover_state = self._state_at(mx, my)
            else:
                self.hover_state = None

    def _state_at(self, mx, my):
        """Retourne l'état le plus proche de (mx, my) si distance < 10px, sinon None."""
        best_dist  = 10
        best_state = None
        for entry in self.exploration_log[:self.replay_index + 1]:
            etat = entry[0]
            if etat not in self.node_positions:
                continue
            x, y = self.node_positions[etat]
            y -= self.scroll_y
            d = abs(x - mx) + abs(y - my)   # Manhattan, assez rapide
            if d < best_dist:
                best_dist  = d
                best_state = etat
        return best_state
```

- [ ] **Étape 3 : Tester le replay en lançant la vraie application**

```bash
python display_game.py
```

Aller dans Solver → choisir un niveau → cliquer Résoudre → attendre la fin → cliquer "Voir la résolution de graphe". La fenêtre graphe doit s'ouvrir. Appuyer sur ▶ Rejouer. Vérifier que les nœuds apparaissent progressivement.

- [ ] **Étape 4 : Commit**

```bash
git add graph_view.py
git commit -m "feat: replay animé avec slider vitesse + pause/rejouer"
```

---

## Task 8 : Scroll, hover preview et Manhattan A*

**Files:**
- Modify: `graph_view.py` (méthode `_draw_hover_preview`)

### Objectif

Au survol d'un nœud : afficher une mini-grille 120×120px reconstituée depuis l'état. Pour A* : tracer les lignes de Manhattan (caisse → cible la plus proche).

- [ ] **Étape 1 : Implémenter `_draw_hover_preview()`**

Remplacer `def _draw_hover_preview(self, state): pass` par :

```python
    def _draw_hover_preview(self, state):
        if state not in self.node_positions:
            return

        # Reconstituer la grille depuis l'état
        # état = ((jx, jy), frozenset({(bx, by), ...}))
        (jx, jy), box_positions = state

        # On n'a pas la matrice de base ici — on dessine juste les positions relatives
        # en utilisant les coordonnées min/max des entités connues
        all_x = [jx] + [bx for bx, by in box_positions]
        all_y = [jy] + [by for bx, by in box_positions]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        span = max(max_x - min_x, max_y - min_y, 1)

        PREVIEW_SIZE = 120
        cell = PREVIEW_SIZE // (span + 2)
        cell = max(6, min(cell, 20))

        # Position de la preview (à droite du curseur, dans le panneau droit)
        px = SPLIT_X + 10
        py = 500

        bg = pygame.Rect(px - 4, py - 4, PREVIEW_SIZE + 8, PREVIEW_SIZE + 8)
        pygame.draw.rect(self.screen, (40, 40, 60), bg, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT_C, bg, 1, border_radius=8)

        def cell_to_screen(cx, cy):
            sx = px + (cx - min_x + 1) * cell
            sy = py + (cy - min_y + 1) * cell
            return sx, sy

        # Joueur
        jsx, jsy = cell_to_screen(jx, jy)
        pygame.draw.circle(self.screen, (203, 166, 247), (jsx, jsy), cell // 2)

        # Caisses
        for bx, by in box_positions:
            bsx, bsy = cell_to_screen(bx, by)
            pygame.draw.rect(self.screen, CAISSE_C,
                             pygame.Rect(bsx - cell//2, bsy - cell//2, cell, cell),
                             border_radius=2)

        # Pour A* : lignes Manhattan (caisse → cible la plus proche)
        # self.targets = positions réelles des CIBLE dans la matrice originale
        if self.algo == 'Astar' and self.targets:
            for bx, by in box_positions:
                nearest = min(self.targets, key=lambda t: abs(t[0]-bx)+abs(t[1]-by))
                tx, ty = nearest
                bsx, bsy = cell_to_screen(bx, by)
                tsx, tsy = cell_to_screen(tx, ty)
                pygame.draw.line(self.screen, CIBLE_C, (bsx, bsy), (tsx, tsy), 1)
                dist = abs(tx - bx) + abs(ty - by)
                lbl = self.font_sm.render(str(dist), True, CIBLE_C)
                self.screen.blit(lbl, ((bsx + tsx) // 2, (bsy + tsy) // 2))
```

- [ ] **Étape 2 : Tester le hover**

```bash
python display_game.py
```

Ouvrir la fenêtre graphe, lancer le replay, puis survoler un nœud. Une mini-grille doit apparaître dans le panneau droit. Pour A*, les lignes Manhattan doivent être visibles.

- [ ] **Étape 3 : Commit**

```bash
git add graph_view.py
git commit -m "feat: hover preview mini-grille + lignes Manhattan pour A*"
```

---

## Task 9 : Tests finaux et nettoyage

**Files:**
- Modify: `tests/test_solveur_log.py`

### Objectif

Vérifier que l'intégration complète fonctionne sur les 5 niveaux avec les 3 algos.

- [ ] **Étape 1 : Ajouter un test d'intégration `solveur()` + log**

```python
def test_integration_tous_algos_niveau_1():
    import copy
    from build_game import solveur, charger_niveau
    for algo in ('BFS', 'DFS', 'Astar'):
        m = copy.deepcopy(charger_niveau(1))
        chemin, etapes, nb_visites, log = solveur(m, mode=algo)
        assert chemin is not None, f"{algo}: doit trouver une solution"
        assert len(log) > 0
        assert nb_visites == len(log)
        # La racine est dans le log
        root = log[0][0]
        assert log[0][1] is None   # parent de la racine = None
        # Chaque état du chemin solution est dans le log
        log_etats = {e[0] for e in log}
        for etat in chemin:
            assert etat in log_etats, f"État du chemin absent du log ({algo})"

def test_stop_flag_retourne_log_partiel():
    import copy
    from build_game import solveur, charger_niveau
    appels = [0]
    def stop_after_1000():
        appels[0] += 1
        return appels[0] >= 2   # True dès le 2ème check (1000 étapes)

    m = copy.deepcopy(charger_niveau(4))   # niveau difficile
    chemin, etapes, nb_visites, log = solveur(m, mode='DFS', stop_flag=stop_after_1000)
    assert chemin is None
    assert len(log) > 0    # log partiel retourné
    assert nb_visites == len(log)
```

- [ ] **Étape 2 : Lancer tous les tests**

```bash
python -m pytest tests/test_solveur_log.py -v
```

Résultat attendu : tous `PASSED`.

- [ ] **Étape 3 : Vérifier que `.gitignore` ignore `.superpowers/`**

```bash
grep -q '.superpowers' .gitignore && echo "OK" || echo "AJOUTER .superpowers/ dans .gitignore"
```

Si `AJOUTER` : ajouter la ligne `.superpowers/` dans `.gitignore`.

- [ ] **Étape 4 : Commit final**

```bash
git add tests/test_solveur_log.py .gitignore
git commit -m "test: intégration solveur + exploration_log tous algos"
```

---

## Récapitulatif des commits prévus

| # | Message |
|---|---------|
| 1 | `feat: solveur() retourne exploration_log en 4ème valeur` |
| 2 | `feat: bouton 'Voir la résolution de graphe' + plumbing display_game` |
| 3 | `feat: graph_view.py squelette — fenêtre 1600x1000 fonctionnelle` |
| 4 | `feat: _compute_layout() — layout hiérarchique de l'arbre` |
| 5 | `feat: _draw_tree() — rendu nœuds + arêtes avec couleurs algo` |
| 6 | `feat: _draw_panel() — panneau droit stats + slider + boutons` |
| 7 | `feat: replay animé avec slider vitesse + pause/rejouer` |
| 8 | `feat: hover preview mini-grille + lignes Manhattan pour A*` |
| 9 | `test: intégration solveur + exploration_log tous algos` |
