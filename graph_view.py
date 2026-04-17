import pygame
import sys
from collections import deque

# ── Constantes ────────────────────────────────────────────────────────────
GW, GH   = 1600, 1000
SPLIT_X  = 1133

FOND           = (30,  30,  46)
MUR_C          = (69,  71,  90)
SOL_C          = (49,  50,  68)
CAISSE_C       = (243, 139, 168)
CIBLE_C        = (166, 227, 161)
CAISSE_CIBLE_C = (137, 220, 235)
BTN_C          = (49,  50,  68)
BTN_HOVER_C    = (88,  91, 112)
TEXTE_C        = (205, 214, 244)
TEXTE2_C       = (108, 112, 134)
ACCENT_C       = (203, 166, 247)

MAX_NODES = 10_000
LEVEL_H   = 20
NODE_R    =  3


# ── Slider ────────────────────────────────────────────────────────────────
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


# ── Button ────────────────────────────────────────────────────────────────
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
        self.chemin          = chemin
        self.algo            = algo
        self.targets         = targets or []

        self.replay_index   = 0
        self.replay_running = False
        self.replay_timer   = 0
        self.scroll_y       = 0
        self.hover_state    = None

        self.node_positions = {}
        self.parent_of      = {}
        self.tree_height    = 0
        self._max_h         = 1

        pygame.init()
        self.screen  = pygame.display.set_mode((GW, GH))
        pygame.display.set_caption("Résolution de graphe")
        self.clock   = pygame.time.Clock()
        self.font    = pygame.font.SysFont("DejaVu Sans Mono", 29)
        self.font_sm = pygame.font.SysFont("DejaVu Sans Mono", 24)

        self.speed_slider = Slider(SPLIT_X + 27, 380, 420, 1, 50, 10, self.font_sm)

        self._compute_layout()
        if self.algo == 'Astar':
            h_values = [e[2] for e in self.exploration_log if len(e) == 3]
            self._max_h = max(h_values, default=1) or 1

    # ── Layout ────────────────────────────────────────────────────────────
    def _compute_layout(self):
        if not self.exploration_log:
            return

        children = {}
        root = None
        for entry in self.exploration_log:
            etat, parent = entry[0], entry[1]
            self.parent_of[etat] = parent
            if parent is None:
                root = etat
            else:
                children.setdefault(parent, []).append(etat)

        depth_nodes = {}
        queue = deque([(root, 0)])
        while queue:
            etat, d = queue.popleft()
            depth_nodes.setdefault(d, []).append(etat)
            for child in children.get(etat, []):
                queue.append((child, d + 1))

        ZONE_W = SPLIT_X - 20
        MARGIN = 30
        usable = ZONE_W - 2 * MARGIN

        for depth, nodes in depth_nodes.items():
            count = len(nodes)
            y = 40 + depth * LEVEL_H
            for i, etat in enumerate(nodes):
                x = MARGIN + (usable // 2 if count == 1
                               else int(i / (count - 1) * usable))
                self.node_positions[etat] = (x, y)

        self.tree_height = 40 + max(depth_nodes.keys(), default=0) * LEVEL_H + 40

    # ── Main loop ─────────────────────────────────────────────────────────
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
        if not self.replay_running:
            return
        speed    = self.speed_slider.value
        interval = 1000 / speed
        self.replay_timer += dt
        while self.replay_timer >= interval:
            self.replay_timer -= interval
            if self.replay_index < len(self.exploration_log) - 1:
                self.replay_index += 1
            else:
                self.replay_running = False
                break

    # ── Drawing ───────────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(FOND)
        pygame.draw.line(self.screen, MUR_C, (SPLIT_X, 0), (SPLIT_X, GH), 3)
        self._draw_tree()
        self._draw_panel()
        if self.hover_state and self.hover_state in self.node_positions:
            self._draw_hover_preview(self.hover_state)

    def _draw_tree(self):
        if not self.node_positions:
            return

        visible     = self.exploration_log[:self.replay_index + 1]
        visible_set = {e[0] for e in visible}

        solution_set = set()
        if self.chemin:
            solution_set = {s for s in self.chemin if s in self.node_positions}

        active_path = set()
        if self.algo == 'DFS' and visible:
            etat = visible[-1][0]
            while etat is not None:
                active_path.add(etat)
                etat = self.parent_of.get(etat)

        clip = pygame.Rect(0, 0, SPLIT_X, GH)
        self.screen.set_clip(clip)

        # Edges
        for entry in visible:
            etat, parent = entry[0], entry[1]
            if parent is None or parent not in self.node_positions:
                continue
            x1, y1 = self.node_positions[parent]
            x2, y2 = self.node_positions[etat]
            sy1, sy2 = y1 - self.scroll_y, y2 - self.scroll_y
            if -10 < sy1 < GH or -10 < sy2 < GH:
                pygame.draw.line(self.screen, (60, 60, 80), (x1, sy1), (x2, sy2), 1)

        # Nodes
        current = visible[-1][0] if visible else None
        for entry in visible:
            etat = entry[0]
            x, y = self.node_positions[etat]
            sy = y - self.scroll_y
            if sy < -NODE_R or sy > GH + NODE_R:
                continue

            if etat == current:
                color, r = (255, 255, 255), NODE_R + 2
            elif etat in solution_set:
                color, r = CIBLE_C, NODE_R + 1
            elif self.algo == 'DFS':
                color, r = (ACCENT_C if etat in active_path else (80, 80, 100)), NODE_R
            elif self.algo == 'Astar':
                h = entry[2] if len(entry) == 3 else 0
                t = min(1.0, h / self._max_h)
                color, r = (int(220 * (1 - t)), 60, int(220 * t)), NODE_R
            else:  # BFS
                color, r = ACCENT_C, NODE_R

            pygame.draw.circle(self.screen, color, (x, sy), r)
            if etat == current:
                pygame.draw.circle(self.screen, ACCENT_C, (x, sy), r + 3, 1)

        self.screen.set_clip(None)

    def _draw_panel(self):
        RX = SPLIT_X + 27
        algo_label = {"BFS": "BFS", "DFS": "DFS", "Astar": "A*"}
        self.screen.blit(
            self.font.render(f"Algorithme : {algo_label.get(self.algo, self.algo)}",
                             True, TEXTE2_C), (RX, 47))
        pygame.draw.line(self.screen, MUR_C, (SPLIT_X + 10, 90), (GW - 10, 90), 1)

        total   = len(self.exploration_log)
        visible = self.replay_index + 1 if self.exploration_log else 0
        coups   = (len(self.chemin) - 1) if self.chemin else 0

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

        self.speed_slider.draw(self.screen)

        btn_label = "⏸ Pause" if self.replay_running else "▶ Rejouer"
        Button(RX, 460, 420, 67, btn_label, self.font).draw(self.screen)
        Button(RX, GH - 93, 420, 67, "✕ Fermer", self.font_sm).draw(self.screen)

    def _draw_hover_preview(self, state):
        if state not in self.node_positions:
            return

        (jx, jy), box_positions = state
        all_x = [jx] + [bx for bx, _ in box_positions]
        all_y = [jy] + [by for _, by in box_positions]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        span = max(max_x - min_x, max_y - min_y, 1)

        PREVIEW = 120
        cell = max(6, min(PREVIEW // (span + 2), 20))

        px, py = SPLIT_X + 10, 500
        bg = pygame.Rect(px - 4, py - 4, PREVIEW + 8, PREVIEW + 8)
        pygame.draw.rect(self.screen, (40, 40, 60), bg, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT_C, bg, 1, border_radius=8)

        def to_screen(cx, cy):
            return px + (cx - min_x + 1) * cell, py + (cy - min_y + 1) * cell

        jsx, jsy = to_screen(jx, jy)
        pygame.draw.circle(self.screen, ACCENT_C, (jsx, jsy), cell // 2)

        for bx, by in box_positions:
            bsx, bsy = to_screen(bx, by)
            pygame.draw.rect(self.screen, CAISSE_C,
                             pygame.Rect(bsx - cell // 2, bsy - cell // 2, cell, cell),
                             border_radius=2)

        if self.algo == 'Astar' and self.targets:
            for bx, by in box_positions:
                nearest = min(self.targets, key=lambda t: abs(t[0]-bx) + abs(t[1]-by))
                tx, ty = nearest
                bsx, bsy = to_screen(bx, by)
                tsx, tsy = to_screen(tx, ty)
                pygame.draw.line(self.screen, CIBLE_C, (bsx, bsy), (tsx, tsy), 1)
                dist = abs(tx - bx) + abs(ty - by)
                lbl = self.font_sm.render(str(dist), True, CIBLE_C)
                self.screen.blit(lbl, ((bsx + tsx) // 2, (bsy + tsy) // 2))

    # ── Events ────────────────────────────────────────────────────────────
    def _handle_event(self, event):
        self.speed_slider.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            max_scroll = max(0, self.tree_height - GH + 40)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            RX = SPLIT_X + 27
            btn_label = "⏸ Pause" if self.replay_running else "▶ Rejouer"
            if Button(RX, 460, 420, 67, btn_label, self.font).clicked(event):
                if self.replay_running:
                    self.replay_running = False
                else:
                    if self.replay_index >= len(self.exploration_log) - 1:
                        self.replay_index  = 0
                        self.replay_timer  = 0
                    self.replay_running = True

            if Button(RX, GH - 93, 420, 67, "✕ Fermer", self.font_sm).clicked(event):
                pygame.quit()
                sys.exit()

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx < SPLIT_X:
                self.hover_state = self._state_at(mx, my)
            else:
                self.hover_state = None

    def _state_at(self, mx, my):
        best_dist, best_state = 10, None
        for entry in self.exploration_log[:self.replay_index + 1]:
            etat = entry[0]
            if etat not in self.node_positions:
                continue
            x, y = self.node_positions[etat]
            d = abs(x - mx) + abs(y - (my + self.scroll_y))
            if d < best_dist:
                best_dist, best_state = d, etat
        return best_state


# ── Entry point ───────────────────────────────────────────────────────────
def _run_graph_process(exploration_log, chemin, algo, targets=None):
    """Called in a spawn subprocess. Opens the graph window."""
    win = GraphWindow(exploration_log, chemin, algo, targets)
    win.run()


if __name__ == '__main__':
    _run_graph_process([], None, 'BFS')
