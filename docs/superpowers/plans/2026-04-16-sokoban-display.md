# Sokoban display_game.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer `display_game.py` — interface Pygame complète pour Sokoban avec mode Joueur (jeu interactif + scores JSON) et mode Solver (solveur BFS/DFS/A* avec replay animé).

**Architecture:** Classe `App` unique gérant tous les écrans via `screen_state`. Chaque écran a une méthode `_draw_*` et `_handle_*`. Toute la logique jeu est déléguée à `build_game.py` (seul `solveur()` est modifié pour retourner les stats).

**Tech Stack:** Python 3, Pygame, build_game.py (local), json / threading / copy / time (stdlib)

---

## File Map

| Fichier | Action | Responsabilité |
|---------|--------|---------------|
| `build_game.py` | Modifier | `solveur()` retourne `(chemin, etapes, nb_visites)` |
| `display_game.py` | Créer | Classe `App` — tous les écrans et l'animation |
| `main.py` | Créer | Point d'entrée : `App().run()` |
| `scores.json` | Auto-créé | Persistance des scores |

---

### Task 1 : Modifier solveur() dans build_game.py

**Files:**
- Modify: `build_game.py:272-289`

- [ ] **Step 1 : Modifier le return de succès**

Dans `build_game.py`, remplacer le bloc de succès (vers ligne 272) :
```python
        if est_gagne(actuel, matrice):
            print(f"Succès en {etapes} étapes")
            return reconstruire_chemin(prev, actuel)
```
par :
```python
        if est_gagne(actuel, matrice):
            return reconstruire_chemin(prev, actuel), etapes, len(visites)
```

- [ ] **Step 2 : Modifier le return d'échec**

Remplacer la fin de `solveur()` (vers ligne 288) :
```python
    print("Aucune solution trouvée")
    return None
```
par :
```python
    return None, etapes, len(visites)
```

- [ ] **Step 3 : Vérifier**

```bash
cd /data/michel/Documents/auto-sokoban
python3 -c "
import copy
from build_game import charger_niveau, solveur
m = copy.deepcopy(charger_niveau(1))
chemin, etapes, nb_visites = solveur(m, 'BFS')
print(f'chemin={len(chemin)} états, etapes={etapes}, visites={nb_visites}')
"
```
Résultat attendu : une ligne `chemin=N états, etapes=M, visites=K` sans erreur.

- [ ] **Step 4 : Commit**

```bash
git add build_game.py
git commit -m "feat: solveur() retourne (chemin, etapes, nb_visites)"
```

---

### Task 2 : Squelette App — init, couleurs, Button, Slider, run loop

**Files:**
- Create: `display_game.py`

- [ ] **Step 1 : Créer display_game.py**

```python
import pygame
import sys
import json
import copy
import time
import threading
import os

from build_game import (
    charger_niveau, get_etat, est_gagne,
    deplacer_joueur, mouvement_valide, annuler_mouvement, solveur,
    MUR, SOL, CIBLE, CAISSE, JOUEUR, CAISSE_SUR_CIBLE, JOUEUR_SUR_CIBLE,
    HAUT, BAS, GAUCHE, DROITE,
)

# ── Constantes ──────────────────────────────────────────────────────
WINDOW_W, WINDOW_H = 900, 660
SPLIT_X = 540          # séparation gauche/droite en mode Solver
SCORES_FILE = "scores.json"

# Couleurs
FOND           = (30,  30,  46)
MUR_C          = (69,  71,  90)
SOL_C          = (49,  50,  68)
CAISSE_C       = (243, 139, 168)
CIBLE_C        = (166, 227, 161)
CAISSE_CIBLE_C = (137, 220, 235)
JOUEUR_C       = (203, 166, 247)
BTN_C          = (49,  50,  68)
BTN_HOVER_C    = (88,  91,  112)
TEXTE_C        = (205, 214, 244)
TEXTE2_C       = (108, 112, 134)
ACCENT_C       = (203, 166, 247)

CELL_COLORS = {
    MUR:              MUR_C,
    SOL:              SOL_C,
    CIBLE:            CIBLE_C,
    CAISSE:           CAISSE_C,
    JOUEUR:           JOUEUR_C,
    CAISSE_SUR_CIBLE: CAISSE_CIBLE_C,
    JOUEUR_SUR_CIBLE: JOUEUR_C,
}

# Noms internes → labels affichés
ALGO_LABELS = {"BFS": "BFS", "DFS": "DFS", "Astar": "A*"}


# ── Button ──────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font

    def draw(self, surface):
        color = BTN_HOVER_C if self.rect.collidepoint(pygame.mouse.get_pos()) else BTN_C
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        surf = self.font.render(self.text, True, TEXTE_C)
        surface.blit(surf, surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Slider ──────────────────────────────────────────────────────────
class Slider:
    def __init__(self, x, y, w, min_val, max_val, initial, font):
        self.track    = pygame.Rect(x, y, w, 8)
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
        pygame.draw.rect(surface, BTN_C, self.track, border_radius=4)
        hx = self.handle_x
        pygame.draw.rect(surface, ACCENT_C,
                         pygame.Rect(hx - 8, self.track.y - 6, 16, 20),
                         border_radius=4)
        label = self.font.render(f"Vitesse : {self.value} coup/s", True, TEXTE_C)
        surface.blit(label, (self.track.x, self.track.y - 28))

    def handle_event(self, event):
        hx = self.handle_x
        handle_rect = pygame.Rect(hx - 8, self.track.y - 6, 16, 20)
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


# ── App ──────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        pygame.init()
        self.screen        = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Sokoban")
        self.clock_pygame  = pygame.time.Clock()
        self.font          = pygame.font.SysFont("DejaVu Sans Mono", 22)
        self.font_lg       = pygame.font.SysFont("DejaVu Sans Mono", 32, bold=True)
        self.font_sm       = pygame.font.SysFont("DejaVu Sans Mono", 18)

        # Navigation
        self.screen_state = "home"
        self.mode         = None   # "joueur" | "solver"
        self.niveau       = None

        # Mode Joueur
        self.matrice           = None
        self.matrice_originale = None
        self.historique        = []
        self.coups             = 0
        self.start_time        = None
        self.elapsed_victory   = 0.0
        self.input_text        = ""

        # Mode Solver
        self.solver_algo          = "BFS"
        self.solver_thread        = None
        self.solver_stop          = False
        self.solver_status        = "idle"   # idle|running|done|no_solution
        self.solver_chemin        = None
        self.solver_etapes        = 0
        self.solver_visites       = 0
        self.matrice_solver_init  = None
        self.matrice_base         = None

        # Replay
        self.replay_active = False
        self.replay_index  = 0
        self.replay_timer  = 0
        self.speed_slider  = None

    # ── Boucle principale ───────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock_pygame.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)
            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_event(self, event):
        pass   # rempli dans les tâches suivantes

    def _update(self, dt):
        pass   # rempli dans les tâches suivantes

    def _draw(self):
        self.screen.fill(FOND)
        pygame.display.flip()

    # ── Transitions d'écran (stubs) ─────────────────────────────────
    def show_home(self):
        self.solver_stop  = True
        self.screen_state = "home"

    def show_level_select(self, mode):
        self.mode         = mode
        self.screen_state = "level_select"

    def show_game(self, niveau):
        self.niveau            = niveau
        self.matrice_originale = copy.deepcopy(charger_niveau(niveau))
        self.matrice           = copy.deepcopy(self.matrice_originale)
        self.historique        = []
        self.coups             = 0
        self.start_time        = time.time()
        self.screen_state      = "game"

    def show_victory(self):
        self.input_text   = ""
        self.screen_state = "victory"

    def show_solver(self, niveau):
        self.niveau               = niveau
        self.matrice_solver_init  = copy.deepcopy(charger_niveau(niveau))
        self.matrice              = copy.deepcopy(self.matrice_solver_init)
        self.matrice_base         = self._make_base_matrice(self.matrice_solver_init)
        self.solver_status        = "idle"
        self.solver_chemin        = None
        self.solver_stop          = False
        self.replay_active        = False
        self.replay_index         = 0
        self.replay_timer         = 0
        self.speed_slider         = Slider(
            SPLIT_X + 20, 390, 240, 1, 10, 3, self.font_sm
        )
        self.screen_state = "solver"

    # ── Helpers ─────────────────────────────────────────────────────
    def _make_base_matrice(self, matrice):
        """Copie sans joueur ni caisses (murs + cibles uniquement)."""
        base = copy.deepcopy(matrice)
        for row in base:
            for x in range(len(row)):
                v = row[x]
                if v == JOUEUR:             row[x] = SOL
                elif v == JOUEUR_SUR_CIBLE: row[x] = CIBLE
                elif v == CAISSE:           row[x] = SOL
                elif v == CAISSE_SUR_CIBLE: row[x] = CIBLE
        return base

    def _reconstruct_matrice(self, etat):
        """Reconstruit la matrice d'affichage depuis base + état (pour la replay)."""
        m = copy.deepcopy(self.matrice_base)
        for (bx, by) in etat[1]:
            m[by][bx] = CAISSE_SUR_CIBLE if m[by][bx] == CIBLE else CAISSE
        jx, jy = etat[0]
        m[jy][jx] = JOUEUR_SUR_CIBLE if m[jy][jx] == CIBLE else JOUEUR
        return m

    def _time_str(self):
        elapsed = time.time() - (self.start_time or time.time())
        m, s = divmod(int(elapsed), 60)
        return f"{m:02d}:{s:02d}"

    def _blit_centered(self, font, text, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(WINDOW_W // 2, y)))


if __name__ == "__main__":
    App().run()
```

- [ ] **Step 2 : Vérifier le lancement**

```bash
cd /data/michel/Documents/auto-sokoban
python3 display_game.py
```
Attendu : fenêtre noire s'ouvre sans crash. Fermer avec la croix.

- [ ] **Step 3 : Commit**

```bash
git add display_game.py
git commit -m "feat: squelette App avec couleurs, Button, Slider"
```

---

### Task 3 : Helpers de rendu de grille

**Files:**
- Modify: `display_game.py` — ajouter `_draw_grid` et `_grid_params`

- [ ] **Step 1 : Ajouter les deux méthodes à App**

Ajouter après `_blit_centered` :

```python
    def _grid_params(self, matrice, max_w, max_h):
        """Retourne (cell_size, origin_x, origin_y) pour centrer la grille."""
        rows = len(matrice)
        cols = len(matrice[0])
        cell_size = min(max_w // cols, max_h // rows)
        ox = (max_w  - cols * cell_size) // 2
        oy = (max_h  - rows * cell_size) // 2
        return cell_size, ox, oy

    def _draw_grid(self, matrice, origin_x, origin_y, cell_size):
        for y, row in enumerate(matrice):
            for x, val in enumerate(row):
                rect = pygame.Rect(
                    origin_x + x * cell_size,
                    origin_y + y * cell_size,
                    cell_size, cell_size,
                )
                color = CELL_COLORS.get(val, SOL_C)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, FOND, rect, 1)   # séparateur
                # Joueur = disque violet centré
                if val in (JOUEUR, JOUEUR_SUR_CIBLE):
                    cx = origin_x + x * cell_size + cell_size // 2
                    cy = origin_y + y * cell_size + cell_size // 2
                    pygame.draw.circle(self.screen, JOUEUR_C, (cx, cy),
                                       cell_size // 3)
```

- [ ] **Step 2 : Test visuel rapide**

Modifier `_draw` temporairement :
```python
    def _draw(self):
        self.screen.fill(FOND)
        m = copy.deepcopy(charger_niveau(1))
        cell, ox, oy = self._grid_params(m, WINDOW_W, WINDOW_H)
        self._draw_grid(m, ox, oy, cell)
        pygame.display.flip()
```

```bash
python3 display_game.py
```
Attendu : grille du niveau 1 centrée à l'écran, cases colorées, joueur visible.

- [ ] **Step 3 : Remettre _draw vide**

```python
    def _draw(self):
        self.screen.fill(FOND)
        pygame.display.flip()
```

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: helpers de rendu de grille _draw_grid / _grid_params"
```

---

### Task 4 : Écran d'accueil

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _draw_home et _handle_home**

```python
    def _draw_home(self):
        self.screen.fill(FOND)
        self._blit_centered(self.font_lg, "SOKOBAN", ACCENT_C, 180)
        Button(WINDOW_W//2 - 120, 290, 240, 55, "Joueur", self.font).draw(self.screen)
        Button(WINDOW_W//2 - 120, 370, 240, 55, "Solver", self.font).draw(self.screen)

    def _handle_home(self, event):
        if Button(WINDOW_W//2 - 120, 290, 240, 55, "Joueur", self.font).clicked(event):
            self.show_level_select("joueur")
        elif Button(WINDOW_W//2 - 120, 370, 240, 55, "Solver", self.font).clicked(event):
            self.show_level_select("solver")
```

- [ ] **Step 2 : Brancher dans _draw et _handle_event**

Remplacer `_draw` :
```python
    def _draw(self):
        self.screen.fill(FOND)
        if   self.screen_state == "home":         self._draw_home()
        pygame.display.flip()
```

Remplacer `_handle_event` :
```python
    def _handle_event(self, event):
        if   self.screen_state == "home":         self._handle_home(event)
```

- [ ] **Step 3 : Vérifier**

```bash
python3 display_game.py
```
Attendu : titre "SOKOBAN" + boutons "Joueur" et "Solver". Le hover change la couleur. Cliquer ne plante pas.

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: écran d'accueil"
```

---

### Task 5 : Écran de sélection de niveau

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _draw_level_select et _handle_level_select**

```python
    def _draw_level_select(self):
        self.screen.fill(FOND)
        label = "Mode Joueur" if self.mode == "joueur" else "Mode Solver"
        self._blit_centered(self.font_lg, f"Choisir un niveau — {label}", TEXTE_C, 150)
        for i in range(1, 6):
            bx = WINDOW_W // 2 - 270 + (i - 1) * 135
            Button(bx, 270, 110, 65, str(i), self.font_lg).draw(self.screen)
        Button(30, 30, 120, 44, "< Retour", self.font_sm).draw(self.screen)

    def _handle_level_select(self, event):
        if Button(30, 30, 120, 44, "< Retour", self.font_sm).clicked(event):
            self.show_home()
            return
        for i in range(1, 6):
            bx = WINDOW_W // 2 - 270 + (i - 1) * 135
            if Button(bx, 270, 110, 65, str(i), self.font_lg).clicked(event):
                if self.mode == "joueur":
                    self.show_game(i)
                else:
                    self.show_solver(i)
```

- [ ] **Step 2 : Brancher dans _draw et _handle_event**

Dans `_draw`, ajouter :
```python
        elif self.screen_state == "level_select": self._draw_level_select()
```

Dans `_handle_event`, ajouter :
```python
        elif self.screen_state == "level_select": self._handle_level_select(event)
```

- [ ] **Step 3 : Vérifier**

```bash
python3 display_game.py
```
Attendu : Accueil → "Joueur" → 5 boutons numérotés + "< Retour". Retour ramène à l'accueil.

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: écran de sélection de niveau"
```

---

### Task 6 : Écran de jeu — affichage + clavier + undo

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _draw_game**

```python
    def _draw_game(self):
        self.screen.fill(FOND)
        # Grille centrée dans les 680 premiers pixels (HUD à droite)
        cell, ox, oy = self._grid_params(self.matrice, 680, WINDOW_H - 20)
        self._draw_grid(self.matrice, ox, oy + 10, cell)

        # HUD
        hx = 700
        self.screen.blit(
            self.font_sm.render(f"Niveau {self.niveau}", True, TEXTE2_C), (hx, 40))
        self.screen.blit(
            self.font_lg.render(self._time_str(), True, TEXTE_C), (hx, 70))
        self.screen.blit(
            self.font.render(f"{self.coups} coups", True, TEXTE_C), (hx, 115))
        Button(hx, 460, 160, 50, "Undo", self.font).draw(self.screen)
        Button(hx, 530, 160, 50, "< Accueil", self.font_sm).draw(self.screen)
```

- [ ] **Step 2 : Ajouter _handle_game, _do_move, _do_undo**

```python
    def _handle_game(self, event):
        if Button(700, 530, 160, 50, "< Accueil", self.font_sm).clicked(event):
            self.show_home()
            return
        if Button(700, 460, 160, 50, "Undo", self.font).clicked(event):
            self._do_undo()
            return
        if event.type == pygame.KEYDOWN:
            key_map = {
                pygame.K_UP:    HAUT,
                pygame.K_DOWN:  BAS,
                pygame.K_LEFT:  GAUCHE,
                pygame.K_RIGHT: DROITE,
            }
            if event.key in key_map:
                self._do_move(key_map[event.key])

    def _do_move(self, direction):
        if mouvement_valide(self.matrice, direction):
            self.historique.append(copy.deepcopy(self.matrice))
            deplacer_joueur(self.matrice, direction)
            self.coups += 1
            if est_gagne(get_etat(self.matrice), self.matrice_originale):
                self.elapsed_victory = time.time() - self.start_time
                self.show_victory()

    def _do_undo(self):
        prev = annuler_mouvement(self.historique)
        if prev is not None:
            self.matrice = prev
            if self.coups > 0:
                self.coups -= 1
```

- [ ] **Step 3 : Brancher dans _draw et _handle_event**

Dans `_draw` :
```python
        elif self.screen_state == "game":    self._draw_game()
```

Dans `_handle_event` :
```python
        elif self.screen_state == "game":    self._handle_game(event)
```

- [ ] **Step 4 : Vérifier**

```bash
python3 display_game.py
```
Attendu : Joueur → niveau 1 → grille jouable. Flèches déplacent le joueur. Undo annule. Compteur de coups s'incrémente. Horloge tourne. "< Accueil" ramène à l'accueil.

- [ ] **Step 5 : Commit**

```bash
git add display_game.py
git commit -m "feat: écran de jeu avec déplacements et undo"
```

---

### Task 7 : Écran de victoire + sauvegarde JSON

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _draw_victory, _handle_victory, _save_score**

```python
    def _draw_victory(self):
        self.screen.fill(FOND)
        m, s = divmod(int(self.elapsed_victory), 60)
        self._blit_centered(self.font_lg, "Bravo !", CIBLE_C, 140)
        self._blit_centered(self.font,
            f"Niveau {self.niveau}  —  {m:02d}:{s:02d}  —  {self.coups} coups",
            TEXTE_C, 210)
        # Champ de saisie
        lbl = self.font_sm.render("Ton prénom (12 car. max) :", True, TEXTE2_C)
        self.screen.blit(lbl, lbl.get_rect(center=(WINDOW_W // 2, 295)))
        field = pygame.Rect(WINDOW_W // 2 - 150, 320, 300, 50)
        pygame.draw.rect(self.screen, BTN_C, field, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT_C, field, 2, border_radius=8)
        name_surf = self.font.render(self.input_text + "|", True, TEXTE_C)
        self.screen.blit(name_surf, name_surf.get_rect(center=field.center))
        Button(WINDOW_W // 2 - 80, 400, 160, 50, "Valider", self.font).draw(self.screen)

    def _handle_victory(self, event):
        btn = Button(WINDOW_W // 2 - 80, 400, 160, 50, "Valider", self.font)
        if btn.clicked(event) and self.input_text.strip():
            self._save_score()
            self.show_home()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_RETURN and self.input_text.strip():
                self._save_score()
                self.show_home()
            elif event.unicode and len(self.input_text) < 12:
                self.input_text += event.unicode

    def _save_score(self):
        m, s = divmod(int(self.elapsed_victory), 60)
        entry = {
            "prenom": self.input_text.strip(),
            "niveau": self.niveau,
            "temps":  f"{m:02d}:{s:02d}",
            "coups":  self.coups,
        }
        scores = []
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                scores = json.load(f)
        scores.append(entry)
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 2 : Brancher dans _draw et _handle_event**

Dans `_draw` :
```python
        elif self.screen_state == "victory":  self._draw_victory()
```

Dans `_handle_event` :
```python
        elif self.screen_state == "victory":  self._handle_victory(event)
```

- [ ] **Step 3 : Vérifier**

Jouer le niveau 1 jusqu'à la victoire. L'écran de victoire doit apparaître. Saisir un prénom, cliquer "Valider". Vérifier scores.json :
```bash
python3 -c "import json; print(json.dumps(json.load(open('scores.json')), indent=2, ensure_ascii=False))"
```
Attendu : liste avec `prenom`, `niveau`, `temps`, `coups`.

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: écran de victoire et sauvegarde JSON"
```

---

### Task 8 : Écran Solver — layout + panneau de contrôle

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _draw_solver et _handle_solver**

```python
    def _draw_solver(self):
        self.screen.fill(FOND)
        RX = SPLIT_X + 20   # x de départ du panneau droit

        # ── Grille (panneau gauche) ──────────────────────────────
        cell, ox, oy = self._grid_params(self.matrice, SPLIT_X - 10, WINDOW_H - 20)
        self._draw_grid(self.matrice, ox + 5, oy + 10, cell)

        # Séparateur
        pygame.draw.line(self.screen, MUR_C, (SPLIT_X, 0), (SPLIT_X, WINDOW_H), 2)

        # ── Panneau droit ────────────────────────────────────────
        self.screen.blit(
            self.font_sm.render("Algorithme :", True, TEXTE2_C), (RX, 35))

        for i, algo in enumerate(("BFS", "DFS", "Astar")):
            label = ALGO_LABELS[algo]
            btn = Button(RX, 65 + i * 65, 240, 50, label, self.font)
            if self.solver_algo == algo:
                pygame.draw.rect(self.screen, ACCENT_C,
                                 pygame.Rect(RX - 3, 65 + i * 65 - 3, 246, 56),
                                 2, border_radius=12)
            btn.draw(self.screen)

        if self.speed_slider:
            self.speed_slider.draw(self.screen)

        # Résoudre / statut / stats
        if self.solver_status == "idle":
            Button(RX, 470, 240, 55, "Résoudre", self.font).draw(self.screen)
        elif self.solver_status == "running":
            self.screen.blit(
                self.font.render("Calcul en cours...", True, TEXTE2_C), (RX, 475))
        else:
            self._draw_solver_stats(RX)

        # Bouton retour
        Button(RX, WINDOW_H - 70, 240, 50, "< Accueil", self.font_sm).draw(self.screen)

    def _draw_solver_stats(self, rx):
        if self.solver_status == "no_solution":
            self.screen.blit(
                self.font.render("Aucune solution :(", True, CAISSE_C), (rx, 470))
        else:
            coups = len(self.solver_chemin) - 1 if self.solver_chemin else 0
            for i, line in enumerate([
                f"Coups    : {coups}",
                f"Ops      : {self.solver_etapes}",
                f"Sommets  : {self.solver_visites}",
            ]):
                self.screen.blit(
                    self.font_sm.render(line, True, TEXTE_C), (rx, 470 + i * 30))

    def _handle_solver(self, event):
        RX = SPLIT_X + 20

        if Button(RX, WINDOW_H - 70, 240, 50, "< Accueil", self.font_sm).clicked(event):
            self.solver_stop = True
            self.show_home()
            return

        for i, algo in enumerate(("BFS", "DFS", "Astar")):
            label = ALGO_LABELS[algo]
            if Button(RX, 65 + i * 65, 240, 50, label, self.font).clicked(event):
                self.solver_algo = algo

        if self.speed_slider:
            self.speed_slider.handle_event(event)

        if self.solver_status == "idle":
            if Button(RX, 470, 240, 55, "Résoudre", self.font).clicked(event):
                self._start_solver()
```

- [ ] **Step 2 : Brancher dans _draw et _handle_event**

Dans `_draw` :
```python
        elif self.screen_state == "solver":   self._draw_solver()
```

Dans `_handle_event` :
```python
        elif self.screen_state == "solver":   self._handle_solver(event)
```

- [ ] **Step 3 : Vérifier**

```bash
python3 display_game.py
```
Attendu : Solver → niveau 1 → split-screen. Grille à gauche, BFS sélectionné (surligné), curseur, bouton "Résoudre", "< Accueil". Changer algo change le surlignage. Retour fonctionne.

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: écran solver layout et contrôles"
```

---

### Task 9 : Thread solveur + animation de replay

**Files:**
- Modify: `display_game.py`

- [ ] **Step 1 : Ajouter _start_solver et _solver_worker**

```python
    def _start_solver(self):
        self.solver_stop   = False
        self.solver_status = "running"
        self.solver_thread = threading.Thread(
            target=self._solver_worker, daemon=True)
        self.solver_thread.start()

    def _solver_worker(self):
        chemin, etapes, nb_visites = solveur(
            copy.deepcopy(self.matrice_solver_init), self.solver_algo
        )
        if self.solver_stop:
            return
        self.solver_etapes  = etapes
        self.solver_visites = nb_visites
        if chemin:
            self.solver_chemin = chemin
            self.solver_status = "done"
            self.replay_index  = 0
            self.replay_timer  = 0
            self.matrice       = self._reconstruct_matrice(chemin[0])
            self.replay_active = True
        else:
            self.solver_chemin = None
            self.solver_status = "no_solution"
```

- [ ] **Step 2 : Implémenter _update pour la replay**

Remplacer le stub `_update` :
```python
    def _update(self, dt):
        if (self.screen_state == "solver"
                and self.replay_active
                and self.solver_chemin):
            speed    = self.speed_slider.value if self.speed_slider else 3
            interval = 1000 / speed   # ms entre deux étapes
            self.replay_timer += dt
            if self.replay_timer >= interval:
                self.replay_timer -= interval
                nxt = self.replay_index + 1
                if nxt < len(self.solver_chemin):
                    self.replay_index = nxt
                    self.matrice = self._reconstruct_matrice(
                        self.solver_chemin[nxt])
                else:
                    self.replay_active = False
```

- [ ] **Step 3 : Vérifier le flux complet**

```bash
python3 display_game.py
```
1. Solver → niveau 1 → BFS → "Résoudre" → "Calcul en cours..." → stats apparaissent + grille s'anime
2. Bouger le curseur de vitesse change la vitesse de l'animation en temps réel
3. Cliquer "< Accueil" en plein calcul → retour immédiat sans crash
4. Solver → niveau 3 → A* → "Résoudre" → vérifier que les stats sont cohérentes

- [ ] **Step 4 : Commit**

```bash
git add display_game.py
git commit -m "feat: thread solveur et animation de replay"
```

---

### Task 10 : Point d'entrée main.py + test d'intégration final

**Files:**
- Modify: `main.py`

- [ ] **Step 1 : Écrire main.py**

```python
from display_game import App

if __name__ == "__main__":
    App().run()
```

- [ ] **Step 2 : Test d'intégration complet**

```bash
python3 main.py
```

Parcourir tous les flux :
1. Accueil → Joueur → niveau 2 → jouer → Undo → gagner → saisir prénom → Accueil
2. Accueil → Solver → niveau 1 → BFS → Résoudre → regarder la replay → < Accueil
3. Accueil → Solver → niveau 2 → A* → Résoudre → régler la vitesse → < Accueil
4. Accueil → Solver → niveau 1 → DFS → Résoudre → cliquer < Accueil en cours de calcul → pas de crash
5. Vérifier scores.json contient les parties jouées

- [ ] **Step 3 : Commit final**

```bash
git add main.py
git commit -m "feat: main.py — Sokoban Pygame complet"
```

---

## Auto-review du plan

**Couverture du spec :**
- ✅ Page d'accueil Joueur/Solver → Task 4
- ✅ Bouton retour sur tous les écrans → Tasks 4, 5, 6, 7, 8
- ✅ Sélection niveau 1-5 → Task 5
- ✅ Horloge + compteur de coups → Task 6
- ✅ Bouton Undo → Task 6
- ✅ Victoire : prénom 12 car. max + JSON → Task 7
- ✅ Solver split-screen → Task 8
- ✅ Choix BFS/DFS/A* + bouton Résoudre + curseur vitesse → Task 8
- ✅ Replay animé vitesse réglable → Task 9
- ✅ Stats : opérations + sommets explorés → Tasks 1 + 8
- ✅ Modification solveur() → Task 1

**Cohérence des noms :**
- `solveur(matrice, mode)` avec mode `"BFS"/"DFS"/"Astar"` — cohérent avec build_game.py
- `SPLIT_X = 540`, `RX = SPLIT_X + 20 = 560` — utilisé de façon identique dans `_draw_solver` et `_handle_solver`
- `self.matrice_solver_init` — même nom dans `show_solver`, `_solver_worker`, `_start_solver`
- `self.elapsed_victory` — même nom dans `_do_move`, `_draw_victory`, `_save_score`

**Aucun placeholder.**
