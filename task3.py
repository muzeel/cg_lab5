import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Составная кубическая кривая Безье (управление точками)")
clock = pygame.time.Clock()

# --- Цвета ---
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
RED    = (220, 60, 60)
BLUE   = (60, 100, 220)
GRAY   = (190, 190, 190)
LIGHT  = (240, 240, 240)

POINT_RADIUS = 7
HIT_RADIUS   = 12
SEG_SAMPLES  = 60

points = [(150, 400), (350, 200), (600, 500), (850, 300)]

dragging_index = None
show_handles = True 


# ---------- Математика ----------

def bezier_point(p0, p1, p2, p3, t):
    mt = 1.0 - t
    x = (mt**3) * p0[0] + 3 * (mt**2) * t * p1[0] \
        + 3 * mt * (t**2) * p2[0] + (t**3) * p3[0]
    y = (mt**3) * p0[1] + 3 * (mt**2) * t * p1[1] \
        + 3 * mt * (t**2) * p2[1] + (t**3) * p3[1]
    return (x, y)


def build_segments(pts):
    n = len(pts)
    if n < 2:
        return []

    # Расширяем список на одну точку слева и справа (отражение)
    ext = []
    ext.append((2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1]))
    ext.extend(pts)
    ext.append((2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1]))

    segments = []
    for i in range(n - 1):
        p_prev  = ext[i]       # P_{i-1}
        p_cur   = ext[i + 1]   # P_i
        p_next  = ext[i + 2]   # P_{i+1}
        p_next2 = ext[i + 3]   # P_{i+2}

        b0 = p_cur
        b1 = (p_cur[0] + (p_next[0] - p_prev[0]) / 6.0,
              p_cur[1] + (p_next[1] - p_prev[1]) / 6.0)
        b2 = (p_next[0] - (p_next2[0] - p_cur[0]) / 6.0,
              p_next[1] - (p_next2[1] - p_cur[1]) / 6.0)
        b3 = p_next
        segments.append((b0, b1, b2, b3))
    return segments


def find_point_at(pos):
    for i, p in enumerate(points):
        if (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2 <= HIT_RADIUS ** 2:
            return i
    return None


# ---------- Отрисовка ----------

def draw_hint():
    font = pygame.font.SysFont("consolas", 16)
    hints = [
        "ЛКМ по пустому месту  - добавить точку",
        "ЛКМ по точке          - перетащить",
        "ПКМ по точке          - удалить",
        "H                     - показать/скрыть контрольные точки",
        "C                     - очистить всё",
    ]
    for i, h in enumerate(hints):
        screen.blit(font.render(h, True, BLACK), (10, 10 + i * 20))


def draw():
    screen.fill(WHITE)
    segments = build_segments(points)

    # 1. Контрольные полигоны и контрольные точки Безье (опционально)
    if show_handles:
        for b0, b1, b2, b3 in segments:
            pygame.draw.line(screen, GRAY, b0, b1, 1)
            pygame.draw.line(screen, GRAY, b2, b3, 1)
            pygame.draw.circle(screen, GRAY, (int(b1[0]), int(b1[1])), 3)
            pygame.draw.circle(screen, GRAY, (int(b2[0]), int(b2[1])), 3)

    # 2. Сама составная кривая Безье
    for b0, b1, b2, b3 in segments:
        prev = None
        for k in range(SEG_SAMPLES + 1):
            t = k / SEG_SAMPLES
            pt = bezier_point(b0, b1, b2, b3, t)
            if prev is not None:
                pygame.draw.line(screen, BLUE, prev, pt, 3)
            prev = pt

    # 3. Опорные точки
    for i, p in enumerate(points):
        outer = RED if i == dragging_index else BLACK
        pygame.draw.circle(screen, outer, (int(p[0]), int(p[1])), POINT_RADIUS)
        pygame.draw.circle(screen, WHITE, (int(p[0]), int(p[1])), POINT_RADIUS - 3)

    draw_hint()
    pygame.display.flip()


# ---------- Главный цикл ----------

def main():
    global dragging_index, points, show_handles

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    idx = find_point_at(event.pos)
                    if idx is not None:
                        dragging_index = idx
                    else:
                        points.append(event.pos)
                elif event.button == 3:  # ПКМ
                    idx = find_point_at(event.pos)
                    if idx is not None:
                        points.pop(idx)
                        dragging_index = None

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_index = None

            elif event.type == pygame.MOUSEMOTION:
                if dragging_index is not None and dragging_index < len(points):
                    points[dragging_index] = event.pos

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    points = []
                    dragging_index = None
                elif event.key == pygame.K_h:
                    show_handles = not show_handles

        draw()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()