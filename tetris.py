# 테트리스 코드
import pygame
import sys
import random

# --- Constants ---
COLS, ROWS = 10, 20
CELL = 30
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
PANEL_W = 160
WIN_W = BOARD_W + PANEL_W + 36  # gap between board and panel
WIN_H = BOARD_H

FPS = 60
LEVEL_LINES = 10
SCORE_TABLE = [0, 100, 300, 500, 800]

BG        = (8,   8,  15)
GRID_BG   = (11,  11, 24)
GRID_LINE = (20,  20, 40)
PANEL_BG  = (13,  13, 31)
BORDER    = (30,  30, 64)
TEXT_DIM  = (74,  74, 122)
TEXT      = (200, 200, 232)
ACCENT    = (0,   229, 255)

COLORS = {
    'I': (0,   229, 255),
    'O': (255, 230,   0),
    'T': (204,  68, 255),
    'S': (0,   255, 136),
    'Z': (255,  51,  85),
    'L': (255, 136,   0),
    'J': (51,  136, 255),
}

PIECES = {
    'I': [[0,0,0,0],
          [1,1,1,1],
          [0,0,0,0],
          [0,0,0,0]],
    'O': [[1,1],
          [1,1]],
    'T': [[0,1,0],
          [1,1,1],
          [0,0,0]],
    'S': [[0,1,1],
          [1,1,0],
          [0,0,0]],
    'Z': [[1,1,0],
          [0,1,1],
          [0,0,0]],
    'L': [[0,0,1],
          [1,1,1],
          [0,0,0]],
    'J': [[1,0,0],
          [1,1,1],
          [0,0,0]],
}
PIECE_KEYS = list(PIECES.keys())


def rotate(shape):
    n = len(shape)
    return [[shape[n - 1 - r][c] for r in range(n)] for c in range(len(shape[0]))]


def create_board():
    return [[None] * COLS for _ in range(ROWS)]


def random_piece():
    key = random.choice(PIECE_KEYS)
    shape = [row[:] for row in PIECES[key]]
    x = (COLS - len(shape[0])) // 2
    return {'shape': shape, 'color': key, 'x': x, 'y': 0}


def valid(board, shape, ox, oy):
    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if not cell:
                continue
            nx, ny = ox + c, oy + r
            if nx < 0 or nx >= COLS or ny >= ROWS:
                return False
            if ny >= 0 and board[ny][nx]:
                return False
    return True


def ghost_y(board, piece):
    gy = piece['y']
    while valid(board, piece['shape'], piece['x'], gy + 1):
        gy += 1
    return gy


def lock_piece(board, piece):
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:
                ny, nx = piece['y'] + r, piece['x'] + c
                if ny < 0:
                    return False  # topped out
                board[ny][nx] = piece['color']
    return True


def clear_lines(board):
    cleared = 0
    r = ROWS - 1
    while r >= 0:
        if all(board[r]):
            del board[r]
            board.insert(0, [None] * COLS)
            cleared += 1
        else:
            r -= 1
    return cleared


def draw_cell(surface, x, y, color, alpha=255, size=CELL, offset=(0, 0)):
    px = offset[0] + x * size
    py = offset[1] + y * size
    base = pygame.Surface((size, size), pygame.SRCALPHA)
    r, g, b = color
    base.fill((r, g, b, alpha))
    # highlight top edge
    pygame.draw.rect(base, (255, 255, 255, 46), (2, 2, size - 4, 3))
    # highlight left edge
    pygame.draw.rect(base, (255, 255, 255, 20), (2, 5, 3, size - 7))
    # border glow
    pygame.draw.rect(base, (r, g, b, min(alpha, 200)), (1, 1, size - 2, size - 2), 1)
    surface.blit(base, (px, py))


def draw_ghost(surface, board, piece, offset):
    gy = ghost_y(board, piece)
    if gy == piece['y']:
        return
    color = COLORS[piece['color']]
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:
                px = offset[0] + (piece['x'] + c) * CELL
                py = offset[1] + (gy + r) * CELL
                ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                ghost.fill((*color, 45))
                pygame.draw.rect(ghost, (*color, 100), (1, 1, CELL - 2, CELL - 2), 1)
                surface.blit(ghost, (px, py))


def draw_board_surface(board, piece):
    surf = pygame.Surface((BOARD_W, BOARD_H))
    surf.fill(GRID_BG)

    # grid lines
    for c in range(COLS + 1):
        pygame.draw.line(surf, GRID_LINE, (c * CELL, 0), (c * CELL, BOARD_H))
    for r in range(ROWS + 1):
        pygame.draw.line(surf, GRID_LINE, (0, r * CELL), (BOARD_W, r * CELL))

    # locked cells
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]:
                draw_cell(surf, c, r, COLORS[board[r][c]])

    if piece:
        draw_ghost(surf, board, piece, (0, 0))
        for r, row in enumerate(piece['shape']):
            for c, cell in enumerate(row):
                if cell:
                    draw_cell(surf, piece['x'] + c, piece['y'] + r, COLORS[piece['color']])

    return surf


def draw_next_piece(surface, next_piece, rect):
    pygame.draw.rect(surface, PANEL_BG, rect)
    pygame.draw.rect(surface, BORDER, rect, 1)

    if not next_piece:
        return

    cs = 20
    shape = next_piece['shape']
    color = COLORS[next_piece['color']]
    off_x = (rect.width  - len(shape[0]) * cs) // 2
    off_y = (rect.height - len(shape)    * cs) // 2

    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if cell:
                px = rect.x + off_x + c * cs
                py = rect.y + off_y + r * cs
                tile = pygame.Surface((cs, cs), pygame.SRCALPHA)
                tile.fill((*color, 255))
                pygame.draw.rect(tile, (255, 255, 255, 46), (2, 2, cs - 4, 2))
                pygame.draw.rect(tile, (*color, 200), (1, 1, cs - 2, cs - 2), 1)
                surface.blit(tile, (px, py))


def draw_panel(surface, font_lg, font_sm, score, level, lines, next_piece, ox):
    pad = 16
    x = ox + pad

    def panel_box(y, h):
        r = pygame.Rect(ox, y, PANEL_W - 4, h)
        pygame.draw.rect(surface, PANEL_BG, r)
        pygame.draw.rect(surface, BORDER, r, 1)
        return r

    # Next piece
    next_rect = panel_box(0, 100)
    lbl = font_sm.render("NEXT", True, TEXT_DIM)
    surface.blit(lbl, (x, next_rect.y + 8))
    inner = pygame.Rect(next_rect.x + 8, next_rect.y + 26, next_rect.width - 16, 64)
    draw_next_piece(surface, next_piece, inner)

    # Score
    y = 108
    for label, value in [("SCORE", str(score)), ("LEVEL", str(level)), ("LINES", str(lines))]:
        box = panel_box(y, 58)
        lbl = font_sm.render(label, True, TEXT_DIM)
        surface.blit(lbl, (x, box.y + 8))
        val = font_lg.render(value, True, TEXT)
        surface.blit(val, (x, box.y + 24))
        y += 66

    # Controls
    y_ctrl = y
    ctrl_box = panel_box(y_ctrl, WIN_H - y_ctrl)
    lbl = font_sm.render("CONTROLS", True, TEXT_DIM)
    surface.blit(lbl, (x, ctrl_box.y + 8))

    controls = [
        ("← →",   "Move"),
        ("↑",     "Rotate"),
        ("↓",     "Soft drop"),
        ("Space", "Hard drop"),
        ("P",     "Pause"),
    ]
    cy = ctrl_box.y + 26
    for key, action in controls:
        k_surf = font_sm.render(key, True, TEXT)
        a_surf = font_sm.render(action, True, TEXT_DIM)
        surface.blit(k_surf, (x, cy))
        surface.blit(a_surf, (x + 52, cy))
        cy += 18


def draw_overlay(surface, font_title, font_sm, title, sub, final_score=None):
    overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
    overlay.fill((8, 8, 15, 224))
    surface.blit(overlay, (0, 0))

    cy = BOARD_H // 2 - 60

    t = font_title.render(title, True, ACCENT)
    surface.blit(t, (BOARD_W // 2 - t.get_width() // 2, cy))
    cy += t.get_height() + 16

    if final_score is not None:
        lbl = font_sm.render("SCORE", True, TEXT_DIM)
        surface.blit(lbl, (BOARD_W // 2 - lbl.get_width() // 2, cy))
        cy += lbl.get_height() + 4
        sc = font_title.render(str(final_score), True, TEXT)
        surface.blit(sc, (BOARD_W // 2 - sc.get_width() // 2, cy))
        cy += sc.get_height() + 16

    s = font_sm.render(sub, True, TEXT_DIM)
    surface.blit(s, (BOARD_W // 2 - s.get_width() // 2, cy))
    cy += s.get_height() + 20

    btn_text = font_sm.render("[ ENTER / SPACE ]", True, ACCENT)
    surface.blit(btn_text, (BOARD_W // 2 - btn_text.get_width() // 2, cy))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("TETRIS")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("couriernew", 42, bold=True)
        font_lg    = pygame.font.SysFont("couriernew", 26, bold=True)
        font_sm    = pygame.font.SysFont("couriernew", 13)
    except Exception:
        font_title = pygame.font.SysFont("monospace", 42, bold=True)
        font_lg    = pygame.font.SysFont("monospace", 26, bold=True)
        font_sm    = pygame.font.SysFont("monospace", 13)

    PANEL_X = BOARD_W + 12

    # Game state
    board = create_board()
    current = random_piece()
    next_p  = random_piece()
    score = level = 0
    level = 1
    lines = 0
    drop_interval = 800
    accumulated = 0
    game_over = False
    paused = False
    started = False

    DAS_DELAY = 170   # ms before auto-repeat
    DAS_REPEAT = 50   # ms between repeats
    das_key = None
    das_timer = 0

    def reset():
        nonlocal board, current, next_p, score, level, lines
        nonlocal drop_interval, accumulated, game_over, paused, started
        board = create_board()
        current = random_piece()
        next_p  = random_piece()
        score = 0; level = 1; lines = 0
        drop_interval = 800; accumulated = 0
        game_over = False; paused = False; started = True

    def do_lock():
        nonlocal current, next_p, score, level, lines, drop_interval, game_over
        ok = lock_piece(board, current)
        if not ok:
            game_over = True
            return
        cleared = clear_lines(board)
        if cleared:
            lines += cleared
            score += SCORE_TABLE[min(cleared, 4)] * level
            level = lines // LEVEL_LINES + 1
            drop_interval = max(100, 800 - (level - 1) * 70)
        current = next_p
        next_p = random_piece()
        if not valid(board, current['shape'], current['x'], current['y']):
            game_over = True

    prev_time = pygame.time.get_ticks()

    while True:
        now = pygame.time.get_ticks()
        dt  = now - prev_time
        prev_time = now

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if not started or game_over:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        reset()
                    continue

                if event.key == pygame.K_p:
                    paused = not paused

                if paused:
                    continue

                if event.key == pygame.K_UP:
                    rotated = rotate(current['shape'])
                    for dx in (0, -1, 1, -2, 2):
                        if valid(board, rotated, current['x'] + dx, current['y']):
                            current['shape'] = rotated
                            current['x'] += dx
                            break

                if event.key == pygame.K_DOWN:
                    if valid(board, current['shape'], current['x'], current['y'] + 1):
                        current['y'] += 1
                        score += 1
                    else:
                        do_lock()

                if event.key == pygame.K_SPACE:
                    drop = ghost_y(board, current) - current['y']
                    score += drop * 2
                    current['y'] = ghost_y(board, current)
                    do_lock()

                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    das_key = event.key
                    das_timer = -DAS_DELAY
                    dx = -1 if event.key == pygame.K_LEFT else 1
                    if valid(board, current['shape'], current['x'] + dx, current['y']):
                        current['x'] += dx

            if event.type == pygame.KEYUP:
                if event.key == das_key:
                    das_key = None

        # --- DAS (auto-repeat) ---
        if das_key and started and not game_over and not paused:
            das_timer += dt
            while das_timer >= DAS_REPEAT:
                das_timer -= DAS_REPEAT
                dx = -1 if das_key == pygame.K_LEFT else 1
                if valid(board, current['shape'], current['x'] + dx, current['y']):
                    current['x'] += dx

        # --- Gravity ---
        if started and not game_over and not paused:
            accumulated += dt
            if accumulated >= drop_interval:
                accumulated -= drop_interval
                if valid(board, current['shape'], current['x'], current['y'] + 1):
                    current['y'] += 1
                else:
                    do_lock()

        # --- Draw ---
        screen.fill(BG)

        # Board
        board_surf = draw_board_surface(board, current if started and not game_over else None)
        pygame.draw.rect(screen, BORDER, (0, 0, BOARD_W, BOARD_H), 1)
        screen.blit(board_surf, (0, 0))

        # Panel
        draw_panel(screen, font_lg, font_sm, score, level, lines, next_p if started else None, PANEL_X)

        # Overlays
        if not started:
            draw_overlay(screen, font_title, font_sm, "TETRIS", "PRESS ENTER TO START")
        elif game_over:
            draw_overlay(screen, font_title, font_sm, "GAME OVER", "PRESS ENTER TO RETRY", score)
        elif paused:
            draw_overlay(screen, font_title, font_sm, "PAUSED", "PRESS P TO RESUME")

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
