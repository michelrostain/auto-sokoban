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
SPLIT_X    = 540          # séparation gauche/droite en mode Solver
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
        self.screen       = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Sokoban")
        self.clock_pygame = pygame.time.Clock()
        self.font         = pygame.font.SysFont("DejaVu Sans Mono", 22)
        self.font_lg      = pygame.font.SysFont("DejaVu Sans Mono", 32, bold=True)
        self.font_sm      = pygame.font.SysFont("DejaVu Sans Mono", 18)

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
        self.solver_algo         = "BFS"
        self.solver_thread       = None
        self.solver_stop         = False
        self.solver_status       = "idle"   # idle|running|done|no_solution
        self.solver_chemin       = None
        self.solver_etapes       = 0
        self.solver_visites      = 0
        self.matrice_solver_init = None
        self.matrice_base        = None

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
        self.niveau              = niveau
        self.matrice_solver_init = copy.deepcopy(charger_niveau(niveau))
        self.matrice             = copy.deepcopy(self.matrice_solver_init)
        self.matrice_base        = self._make_base_matrice(self.matrice_solver_init)
        self.solver_status       = "idle"
        self.solver_chemin       = None
        self.solver_stop         = False
        self.replay_active       = False
        self.replay_index        = 0
        self.replay_timer        = 0
        self.speed_slider        = Slider(
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
                if v == JOUEUR:               row[x] = SOL
                elif v == JOUEUR_SUR_CIBLE:   row[x] = CIBLE
                elif v == CAISSE:             row[x] = SOL
                elif v == CAISSE_SUR_CIBLE:   row[x] = CIBLE
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
