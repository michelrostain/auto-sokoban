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
WINDOW_W, WINDOW_H = 1200, 880
SPLIT_X    = 720
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

ALGO_LABELS = {"BFS": "BFS", "DFS": "DFS", "Astar": "A*"}


# ── Button ──────────────────────────────────────────────────────────
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


# ── Slider ──────────────────────────────────────────────────────────
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
        label = self.font.render(f"Vitesse : {self.value} coup/s", True, TEXTE_C)
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


# ── App ──────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        pygame.init()
        self.screen       = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Sokoban")
        self.clock_pygame = pygame.time.Clock()
        self.font         = pygame.font.SysFont("DejaVu Sans Mono", 29)
        self.font_lg      = pygame.font.SysFont("DejaVu Sans Mono", 43, bold=True)
        self.font_sm      = pygame.font.SysFont("DejaVu Sans Mono", 24)

        self.screen_state = "home"
        self.mode         = None
        self.niveau       = None

        self.matrice           = None
        self.matrice_originale = None
        self.historique        = []
        self.coups             = 0
        self.start_time        = None
        self.elapsed_victory   = 0.0
        self.input_text        = ""

        self.solver_algo         = "BFS"
        self.solver_thread       = None
        self.solver_stop         = False
        self.solver_status       = "idle"
        self.solver_chemin       = None
        self.solver_etapes       = 0
        self.solver_visites      = 0
        self.solver_exploration_log  = []
        self.matrice_solver_init = None
        self.matrice_base        = None

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
        if   self.screen_state == "home":          self._handle_home(event)
        elif self.screen_state == "level_select":  self._handle_level_select(event)
        elif self.screen_state == "game":          self._handle_game(event)
        elif self.screen_state == "victory":       self._handle_victory(event)
        elif self.screen_state == "solver":        self._handle_solver(event)
        elif self.screen_state == "scores":        self._handle_scores(event)

    def _update(self, dt):
        if (self.screen_state == "solver"
                and self.replay_active
                and self.solver_chemin):
            speed    = self.speed_slider.value if self.speed_slider else 3
            interval = 1000 / speed
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

    def _draw(self):
        self.screen.fill(FOND)
        if   self.screen_state == "home":          self._draw_home()
        elif self.screen_state == "level_select":  self._draw_level_select()
        elif self.screen_state == "game":          self._draw_game()
        elif self.screen_state == "victory":       self._draw_victory()
        elif self.screen_state == "solver":        self._draw_solver()
        elif self.screen_state == "scores":        self._draw_scores()
        pygame.display.flip()

    # ── Solver ──────────────────────────────────────────────────────
    def _draw_solver(self):
        RX = SPLIT_X + 27

        cell, ox, oy = self._grid_params(self.matrice, SPLIT_X - 13, WINDOW_H - 27)
        self._draw_grid(self.matrice, ox + 7, oy + 13, cell)

        pygame.draw.line(self.screen, MUR_C, (SPLIT_X, 0), (SPLIT_X, WINDOW_H), 3)

        self.screen.blit(
            self.font_sm.render("Algorithme :", True, TEXTE2_C), (RX, 47))

        for i, algo in enumerate(("BFS", "DFS", "Astar")):
            label = ALGO_LABELS[algo]
            btn = Button(RX, 87 + i * 87, 320, 67, label, self.font)
            if self.solver_algo == algo:
                pygame.draw.rect(self.screen, ACCENT_C,
                                 pygame.Rect(RX - 4, 87 + i * 87 - 4, 328, 75),
                                 3, border_radius=16)
            btn.draw(self.screen)

        # Bouton "Arrêt" pendant le calcul, "Réinitialiser" après
        if self.solver_status == "running":
            Button(RX, 360, 320, 61, "Arrêt", self.font_sm).draw(self.screen)
        elif self.solver_status in ("done", "no_solution", "stopped"):
            Button(RX, 360, 320, 61, "Réinitialiser", self.font_sm).draw(self.screen)

        if self.speed_slider:
            self.speed_slider.draw(self.screen)

        if self.solver_status == "idle":
            Button(RX, 627, 320, 73, "Résoudre", self.font).draw(self.screen)
        elif self.solver_status == "running":
            self.screen.blit(
                self.font.render("Calcul en cours...", True, TEXTE2_C), (RX, 633))
        else:
            self._draw_solver_stats(RX)

        if self.solver_status in ("done", "stopped", "no_solution"):
            Button(7, WINDOW_H - 160, 340, 57,
                   "Voir la résolution de graphe", self.font_sm).draw(self.screen)

        Button(RX, WINDOW_H - 93, 320, 67, "< Accueil", self.font_sm).draw(self.screen)

    def _draw_solver_stats(self, rx):
        if self.solver_status == "stopped":
            self.screen.blit(
                self.font_sm.render("Calcul interrompu", True, CAISSE_C), (rx, 627))
            for i, line in enumerate([
                f"Ops      : {self.solver_etapes}",
                f"Sommets  : {self.solver_visites}",
            ]):
                self.screen.blit(
                    self.font_sm.render(line, True, TEXTE_C), (rx, 667 + i * 40))
        elif self.solver_status == "no_solution":
            self.screen.blit(
                self.font.render("Aucune solution :(", True, CAISSE_C), (rx, 627))
        else:
            coups = len(self.solver_chemin) - 1 if self.solver_chemin else 0
            for i, line in enumerate([
                f"Coups    : {coups}",
                f"Ops      : {self.solver_etapes}",
                f"Sommets  : {self.solver_visites}",
            ]):
                self.screen.blit(
                    self.font_sm.render(line, True, TEXTE_C), (rx, 627 + i * 40))

    def _handle_solver(self, event):
        RX = SPLIT_X + 27

        if Button(RX, WINDOW_H - 93, 320, 67, "< Accueil", self.font_sm).clicked(event):
            self.solver_stop = True
            self.show_home()
            return

        for i, algo in enumerate(("BFS", "DFS", "Astar")):
            label = ALGO_LABELS[algo]
            if Button(RX, 87 + i * 87, 320, 67, label, self.font).clicked(event):
                self.solver_algo = algo

        if self.speed_slider:
            self.speed_slider.handle_event(event)

        if self.solver_status == "idle":
            if Button(RX, 627, 320, 73, "Résoudre", self.font).clicked(event):
                self._start_solver()
        elif self.solver_status == "running":
            if Button(RX, 360, 320, 61, "Arrêt", self.font_sm).clicked(event):
                self.solver_stop = True
        elif self.solver_status in ("done", "no_solution", "stopped"):
            if Button(RX, 360, 320, 61, "Réinitialiser", self.font_sm).clicked(event):
                self._reset_solver()

        if self.solver_status in ("done", "stopped", "no_solution"):
            if Button(7, WINDOW_H - 160, 340, 57,
                      "Voir la résolution de graphe", self.font_sm).clicked(event):
                self._open_graph_view()

    def _start_solver(self):
        self.solver_stop   = False
        self.solver_status = "running"
        self.solver_thread = threading.Thread(
            target=self._solver_worker, daemon=True)
        self.solver_thread.start()

    def _solver_worker(self):
        chemin, etapes, nb_visites, exploration_log = solveur(
            copy.deepcopy(self.matrice_solver_init), self.solver_algo,
            stop_flag=lambda: self.solver_stop,
        )
        self.solver_exploration_log = exploration_log
        self.solver_etapes  = etapes
        self.solver_visites = nb_visites
        if self.solver_stop:
            self.solver_chemin = None
            self.solver_status = "stopped"
        elif chemin:
            self.solver_chemin = chemin
            self.solver_status = "done"
            self.replay_index  = 0
            self.replay_timer  = 0
            self.matrice       = self._reconstruct_matrice(chemin[0])
            self.replay_active = True
        else:
            self.solver_chemin = None
            self.solver_status = "no_solution"

    def _reset_solver(self):
        self.matrice        = copy.deepcopy(self.matrice_solver_init)
        self.solver_stop    = False
        self.solver_status  = "idle"
        self.solver_chemin  = None
        self.solver_etapes  = 0
        self.solver_visites = 0
        self.solver_exploration_log  = []
        self.replay_active  = False
        self.replay_index   = 0
        self.replay_timer   = 0

    def _open_graph_view(self):
        import multiprocessing
        from graph_view import _run_graph_process
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

    # ── Victoire ────────────────────────────────────────────────────
    def _draw_victory(self):
        m, s = divmod(int(self.elapsed_victory), 60)
        self._blit_centered(self.font_lg, "Bravo !", CIBLE_C, 187)
        self._blit_centered(self.font,
            f"Niveau {self.niveau}  —  {m:02d}:{s:02d}  —  {self.coups} coups",
            TEXTE_C, 280)
        lbl = self.font_sm.render("Ton prénom (12 car. max) :", True, TEXTE2_C)
        self.screen.blit(lbl, lbl.get_rect(center=(WINDOW_W // 2, 393)))
        field = pygame.Rect(WINDOW_W // 2 - 200, 427, 400, 67)
        pygame.draw.rect(self.screen, BTN_C, field, border_radius=11)
        pygame.draw.rect(self.screen, ACCENT_C, field, 3, border_radius=11)
        name_surf = self.font.render(self.input_text + "|", True, TEXTE_C)
        self.screen.blit(name_surf, name_surf.get_rect(center=field.center))
        Button(WINDOW_W // 2 - 107, 533, 213, 67, "Valider", self.font).draw(self.screen)

    def _handle_victory(self, event):
        btn = Button(WINDOW_W // 2 - 107, 533, 213, 67, "Valider", self.font)
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

    # ── Jeu ─────────────────────────────────────────────────────────
    def _draw_game(self):
        cell, ox, oy = self._grid_params(self.matrice, 907, WINDOW_H - 27)
        self._draw_grid(self.matrice, ox, oy + 13, cell)

        hx = 933
        self.screen.blit(
            self.font_sm.render(f"Niveau {self.niveau}", True, TEXTE2_C), (hx, 53))
        self.screen.blit(
            self.font_lg.render(self._time_str(), True, TEXTE_C), (hx, 93))
        self.screen.blit(
            self.font.render(f"{self.coups} coups", True, TEXTE_C), (hx, 153))
        Button(hx, 613, 213, 67, "Undo", self.font).draw(self.screen)
        Button(hx, 707, 213, 67, "< Accueil", self.font_sm).draw(self.screen)

    def _handle_game(self, event):
        if Button(933, 707, 213, 67, "< Accueil", self.font_sm).clicked(event):
            self.show_home()
            return
        if Button(933, 613, 213, 67, "Undo", self.font).clicked(event):
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

    # ── Sélection de niveau ─────────────────────────────────────────
    def _draw_level_select(self):
        label = "Mode Joueur" if self.mode == "joueur" else "Mode Solver"
        self._blit_centered(self.font_lg, f"Choisir un niveau — {label}", TEXTE_C, 200)
        for i in range(1, 6):
            bx = WINDOW_W // 2 - 360 + (i - 1) * 180
            Button(bx, 360, 147, 87, str(i), self.font_lg).draw(self.screen)
        Button(40, 40, 160, 59, "< Retour", self.font_sm).draw(self.screen)

    def _handle_level_select(self, event):
        if Button(40, 40, 160, 59, "< Retour", self.font_sm).clicked(event):
            self.show_home()
            return
        for i in range(1, 6):
            bx = WINDOW_W // 2 - 360 + (i - 1) * 180
            if Button(bx, 360, 147, 87, str(i), self.font_lg).clicked(event):
                if self.mode == "joueur":
                    self.show_game(i)
                else:
                    self.show_solver(i)

    # ── Accueil ─────────────────────────────────────────────────────
    def _draw_home(self):
        self._blit_centered(self.font_lg, "SOKOBAN", ACCENT_C, 213)
        Button(WINDOW_W//2 - 160, 347, 320, 73, "Joueur", self.font).draw(self.screen)
        Button(WINDOW_W//2 - 160, 447, 320, 73, "Solver", self.font).draw(self.screen)
        Button(WINDOW_W//2 - 160, 547, 320, 73, "Scores", self.font).draw(self.screen)

    def _handle_home(self, event):
        if Button(WINDOW_W//2 - 160, 347, 320, 73, "Joueur", self.font).clicked(event):
            self.show_level_select("joueur")
        elif Button(WINDOW_W//2 - 160, 447, 320, 73, "Solver", self.font).clicked(event):
            self.show_level_select("solver")
        elif Button(WINDOW_W//2 - 160, 547, 320, 73, "Scores", self.font).clicked(event):
            self.screen_state = "scores"

    # ── Scores ──────────────────────────────────────────────────────
    def _draw_scores(self):
        self._blit_centered(self.font_lg, "Scores", ACCENT_C, 93)
        scores = []
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                scores = json.load(f)

        if not scores:
            self._blit_centered(self.font, "Aucun score enregistré.", TEXTE2_C, 400)
        else:
            cols = [160, 427, 667, 880]
            headers = ["Prénom", "Niveau", "Temps", "Coups"]
            for cx, h in zip(cols, headers):
                self.screen.blit(self.font_sm.render(h, True, TEXTE2_C), (cx, 187))
            pygame.draw.line(self.screen, MUR_C,
                             (133, 220), (WINDOW_W - 133, 220), 2)
            for i, entry in enumerate(scores[-14:]):
                y = 240 + i * 43
                color = TEXTE_C if i % 2 == 0 else TEXTE2_C
                for cx, key in zip(cols, ["prenom", "niveau", "temps", "coups"]):
                    self.screen.blit(
                        self.font_sm.render(str(entry.get(key, "")), True, color),
                        (cx, y))

        Button(40, 40, 160, 59, "< Retour", self.font_sm).draw(self.screen)

    def _handle_scores(self, event):
        if Button(40, 40, 160, 59, "< Retour", self.font_sm).clicked(event):
            self.screen_state = "home"

    # ── Transitions d'écran ─────────────────────────────────────────
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
        self.niveau              = niveau
        self.matrice_solver_init = copy.deepcopy(charger_niveau(niveau))
        self.matrice             = copy.deepcopy(self.matrice_solver_init)
        self.matrice_base        = self._make_base_matrice(self.matrice_solver_init)
        self.solver_status       = "idle"
        self.solver_chemin       = None
        self.solver_stop         = False
        self.solver_exploration_log  = []
        self.replay_active       = False
        self.replay_index        = 0
        self.replay_timer        = 0
        self.speed_slider        = Slider(
            SPLIT_X + 27, 520, 320, 1, 10, 3, self.font_sm
        )
        self.screen_state = "solver"

    # ── Helpers ─────────────────────────────────────────────────────
    def _make_base_matrice(self, matrice):
        base = copy.deepcopy(matrice)
        for row in base:
            for x in range(len(row)):
                v = row[x]
                if v == JOUEUR:               row[x] = SOL
                elif v == JOUEUR_SUR_CIBLE:   row[x] = CIBLE
                elif v == CAISSE:             row[x] = SOL
                elif v == CAISSE_SUR_CIBLE:   row[x] = CIBLE
        return base

    def _reconstruct_matrice(self, etat):
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

    def _grid_params(self, matrice, max_w, max_h):
        rows = len(matrice)
        cols = len(matrice[0])
        cell_size = min(max_w // cols, max_h // rows)
        ox = (max_w - cols * cell_size) // 2
        oy = (max_h - rows * cell_size) // 2
        return cell_size, ox, oy

    def _draw_grid(self, matrice, origin_x, origin_y, cell_size):
        for y, row in enumerate(matrice):
            for x, val in enumerate(row):
                rx = origin_x + x * cell_size
                ry = origin_y + y * cell_size
                self._draw_cell_sprite(val, rx, ry, cell_size)

    # ── Sprites programmatiques ─────────────────────────────────────
    def _draw_cell_sprite(self, val, rx, ry, size):
        bg = FOND if val == MUR else SOL_C
        pygame.draw.rect(self.screen, bg, pygame.Rect(rx, ry, size, size))

        if val == MUR:
            self._sprite_wall(rx, ry, size)
        elif val == CIBLE:
            self._sprite_target(rx, ry, size)
        elif val == CAISSE:
            self._sprite_box(rx, ry, size, CAISSE_C)
        elif val == CAISSE_SUR_CIBLE:
            self._sprite_target(rx, ry, size)
            self._sprite_box(rx, ry, size, CAISSE_CIBLE_C)
        elif val == JOUEUR:
            self._sprite_player(rx, ry, size)
        elif val == JOUEUR_SUR_CIBLE:
            self._sprite_target(rx, ry, size)
            self._sprite_player(rx, ry, size)

        pygame.draw.rect(self.screen, FOND,
                         pygame.Rect(rx, ry, size, size), 1)

    def _sprite_wall(self, rx, ry, size):
        base = MUR_C
        pygame.draw.rect(self.screen, base, pygame.Rect(rx, ry, size, size))
        light = tuple(min(255, c + 30) for c in base)
        dark  = tuple(max(0,   c - 30) for c in base)
        h = max(4, size // 3)
        for row in range(3):
            y0 = ry + row * h
            pygame.draw.line(self.screen, dark, (rx, y0), (rx + size, y0), 1)
            offset = (size // 4) if row % 2 == 0 else (3 * size // 4)
            pygame.draw.line(self.screen, dark,
                             (rx + offset, y0), (rx + offset, y0 + h), 1)
        pygame.draw.line(self.screen, light, (rx + 1, ry + 1), (rx + size - 2, ry + 1), 1)
        pygame.draw.line(self.screen, light, (rx + 1, ry + 1), (rx + 1, ry + size - 2), 1)

    def _sprite_target(self, rx, ry, size):
        cx, cy = rx + size // 2, ry + size // 2
        r = max(4, size // 3)
        d = max(3, int(r * 0.65))
        col = CIBLE_C
        thick = max(2, size // 20)
        pygame.draw.line(self.screen, col, (cx - r, cy), (cx + r, cy), thick)
        pygame.draw.line(self.screen, col, (cx, cy - r), (cx, cy + r), thick)
        pygame.draw.line(self.screen, col, (cx - d, cy - d), (cx + d, cy + d), thick)
        pygame.draw.line(self.screen, col, (cx + d, cy - d), (cx - d, cy + d), thick)
        pygame.draw.circle(self.screen, col, (cx, cy), max(2, size // 12))

    def _sprite_box(self, rx, ry, size, color):
        pad   = max(3, size // 8)
        inner = pygame.Rect(rx + pad, ry + pad, size - 2 * pad, size - 2 * pad)
        pygame.draw.rect(self.screen, color, inner, border_radius=4)
        light  = tuple(min(255, c + 55) for c in color)
        shadow = tuple(max(0,   c - 55) for c in color)
        thick  = max(1, size // 20)
        pygame.draw.line(self.screen, light,
                         (rx + pad, ry + pad), (rx + size - pad, ry + pad), thick)
        pygame.draw.line(self.screen, light,
                         (rx + pad, ry + pad), (rx + pad, ry + size - pad), thick)
        pygame.draw.line(self.screen, shadow,
                         (rx + pad, ry + size - pad),
                         (rx + size - pad, ry + size - pad), thick)
        pygame.draw.line(self.screen, shadow,
                         (rx + size - pad, ry + pad),
                         (rx + size - pad, ry + size - pad), thick)
        cx, cy = rx + size // 2, ry + size // 2
        arm = max(3, (size - 2 * pad) // 4)
        pygame.draw.line(self.screen, shadow, (cx - arm, cy), (cx + arm, cy), thick)
        pygame.draw.line(self.screen, shadow, (cx, cy - arm), (cx, cy + arm), thick)

    def _sprite_player(self, rx, ry, size):
        cx, cy = rx + size // 2, ry + size // 2
        r = max(5, size // 3)
        pygame.draw.circle(self.screen, JOUEUR_C, (cx, cy), r)
        dark = tuple(max(0, c - 60) for c in JOUEUR_C)
        pygame.draw.circle(self.screen, dark, (cx, cy), r, max(1, size // 20))
        ey  = cy - r // 4
        ex1 = cx - r // 3
        ex2 = cx + r // 3
        eye_r = max(2, r // 4)
        for ex in (ex1, ex2):
            pygame.draw.circle(self.screen, (240, 240, 255), (ex, ey), eye_r)
            pygame.draw.circle(self.screen, (40, 40, 70),
                               (ex, ey), max(1, eye_r // 2))
        smile_r = r // 2
        smile_rect = pygame.Rect(cx - smile_r, cy, smile_r * 2, smile_r)
        pygame.draw.arc(self.screen, (240, 240, 255),
                        smile_rect, 3.14159, 0.0, max(1, size // 22))


if __name__ == "__main__":
    App().run()
