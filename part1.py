import math
import random
import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

class LSystem:
    def __init__(self, axiom, angle, initial_dir, rules):
        self.axiom = axiom
        self.angle = float(angle)
        self.initial_dir = float(initial_dir)
        self.rules = rules

    def expand(self, iterations):
        s = self.axiom
        for _ in range(iterations):
            s = ''.join(self.rules.get(ch, ch) for ch in s)
        return s

    def interpret(self, s, step=1.0, jitter=0.0, step_decay=1.0):
        x, y = 0.0, 0.0
        angle = math.radians(self.initial_dir)
        stack, segments, depth = [], [], 0

        for ch in s:
            if ch in 'F':
                current_step = step * (step_decay ** depth)   
                nx = x + current_step * math.cos(angle)
                ny = y + current_step * math.sin(angle)
                segments.append((x, y, nx, ny, depth))
                x, y = nx, ny
            elif ch == '+':
                angle += math.radians(self.angle + random.uniform(-jitter, jitter))
            elif ch == '-':
                angle -= math.radians(self.angle + random.uniform(-jitter, jitter))
            elif ch == '[':
                stack.append((x, y, angle, depth))
                depth += 1
            elif ch == ']':
                x, y, angle, depth = stack.pop()
            elif ch == '@':
                angle += math.radians(random.uniform(-self.angle / 2, self.angle / 2))

        return segments

def load_lsystem(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.strip() for ln in f
                 if ln.strip() and not ln.lstrip().startswith('#')]
    header = lines[0].split()
    axiom = header[0]
    angle = float(header[1])
    initial_dir = float(header[2]) if len(header) > 2 else 90.0
    rules = {}
    for ln in lines[1:]:
        if ':' in ln:
            k, v = ln.split(':', 1)
            rules[k.strip()] = v.strip()
    return LSystem(axiom, angle, initial_dir, rules)


class Raster:
    def __init__(self, height=1000, width=1000, bg=(255, 255, 255)):
        self.h, self.w = height, width
        self.canvas = np.empty((height, width, 3), dtype=np.uint8)
        self.canvas[:] = bg
        
        self.xmin = self.ymin = self.xmax = self.ymax = None

    def fit_world(self, segments, margin=0.05):
        xs = [v for s in segments for v in (s[0], s[2])]
        ys = [v for s in segments for v in (s[1], s[3])]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        span = max(xmax - xmin, ymax - ymin, 1e-9)
        half = span / 2 * (1 + margin)

        self.xmin, self.xmax = cx - half, cx + half
        self.ymin, self.ymax = cy - half, cy + half

    def world_to_pixel(self, x, y):
        col = int((x - self.xmin) / (self.xmax - self.xmin) * (self.w - 1))
        row = int((y - self.ymin) / (self.ymax - self.ymin) * (self.h - 1))
        row = self.h - 1 - row
        return col, row

    def draw_line(self, p0, p1, color, thickness=1.0):
        x0, y0 = p0
        x1, y1 = p1
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        r = max(0, int(round(thickness / 2)))
        while True:
            self._stamp(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _stamp(self, cx, cy, r, color):
        if r == 0:
            if 0 <= cx < self.w and 0 <= cy < self.h:
                self.canvas[cy, cx] = color
            return
        x0 = max(0, cx - r)
        x1 = min(self.w, cx + r + 1)
        y0 = max(0, cy - r)
        y1 = min(self.h, cy + r + 1)
        if x0 < x1 and y0 < y1:
            self.canvas[y0:y1, x0:x1] = color

    def draw_segments(self, segments, color=(0, 0, 0),
                      thickness_fn=None, color_fn=None):
        max_d = max((s[4] for s in segments), default=1) or 1
        for x1, y1, x2, y2, d in segments:
            col = color_fn(d, max_d) if color_fn else color
            th = thickness_fn(d, max_d) if thickness_fn else 1.0
            p0 = self.world_to_pixel(x1, y1)
            p1 = self.world_to_pixel(x2, y2)
            self.draw_line(p0, p1, col, thickness=th)

    def save(self, path):
        Image.fromarray(self.canvas).save(path)

    def show(self, title=''):
        plt.figure(figsize=(8, 8))
        plt.imshow(self.canvas)
        plt.axis('off')
        plt.title(title)
        plt.tight_layout()
        plt.show()


def render_lsystem(segments, size=1000, bg=(255, 255, 255),
                   color=(0, 0, 0), thickness_fn=None, color_fn=None,
                   margin=0.05):
    raster = Raster(height=size, width=size, bg=bg)
    raster.fit_world(segments, margin=margin)
    raster.draw_segments(segments, color=color,
                         thickness_fn=thickness_fn, color_fn=color_fn)
    return raster


BROWN = np.array([91, 58, 26],   dtype=float)
GREEN = np.array([46, 125, 50],  dtype=float)

def tree_color(depth, max_depth):
    t = depth / max_depth if max_depth else 0.0
    c = (1 - t) * BROWN + t * GREEN
    return tuple(int(v) for v in c)

def tree_thickness(depth, max_depth):
    t = depth / max_depth if max_depth else 0.0
    return max(0.3, 7.0 * (1 - t) ** 1.3)


def write_example_files():
    examples = {
        'koch_curve.txt':            "F 60 0\nF: F-F++F-F\n",
        'koch_snowflake.txt':        "F++F++F 60 0\nF: F-F++F-F\n",
        'koch_island.txt':           "F+F+F+F 90 0\nF: F+F-F-FF+F+F-F\n",
        'sierpinski_carpet.txt':     "FXF--FF--FF 60 0\nF: FF\nX: --FXF++FXF++FXF--\n",
        'sierpinski_arrowhead.txt':  "YF 60 0\nF: F\nX: YF+XF+Y\nY: XF-YF-X\n",
        'hilbert.txt':               "X 90 0\nF: F\nX: -YF+XFX+FY-\nY: +XF-YFY-FX+\n",
        'dragon.txt':                "X 90 0\nF: F\nX: X+YF+\nY: -FX-Y\n",
        'gosper.txt':                "XF 60 0\nF: F\n"
                                     "X: X+YF++YF-FX--FXFX-YF+\n"
                                     "Y: -FX+YFYF++YF+FX--FX-Y\n",
        'bush1.txt':                 "F 22 90\nF: FF-[-F+F+F]+[+F-F-F]\n",
        'bush2.txt':                 "X 20 90\nF: FF\nX: F[+X]F[-X]+X\n",
        'bush3.txt':                 "X 22.5 90\nF: FF\nX: F-[[X]+X]+F[+FX]-X\n",
        'hex_mosaic.txt':            "X 60 0\nF: F\n"
                                     "X: [-F+F[Y]+F][+F-F[X]-F]\n"
                                     "Y: [-F+F[Y]+F][+F-F-F]\n",
        'random_tree.txt':           "X 25 90\nX: F[@[-X]+X]\n",
    }
    for name, content in examples.items():
        with open(name, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    write_example_files()

    demos = [
        ('koch_curve.txt',           4,  0.0, 'Кривая Коха'),
        ('koch_snowflake.txt',       5,  0.0, 'Снежинка Коха'),
        ('koch_island.txt',          4,  0.0, 'Квадратный остров Коха'),
        ('sierpinski_carpet.txt',    4,  0.0, 'Ковёр Серпинского'),
        ('sierpinski_arrowhead.txt', 5,  0.0, 'Наконечник Серпинского'),
        ('hilbert.txt',              5,  0.0, 'Кривая Гильберта'),
        ('dragon.txt',               12, 0.0, 'Дракон Хартера–Хейтуэя'),
        ('gosper.txt',               4,  0.0, 'Шестиугольная кривая Госпера'),
        ('bush1.txt',                5,  0.0, 'Куст 1'),
        ('bush2.txt',                6,  0.0, 'Куст 2'),
        ('bush3.txt',                5,  0.0, 'Куст 3'),
        ('hex_mosaic.txt',           4,  0.0, 'Шестиугольная мозаика'),
    ]

    for fname, it, jitter, title in demos:
        ls = load_lsystem(fname)
        segs = ls.interpret(ls.expand(it), step=1.0, jitter=jitter)
        raster = render_lsystem(segs, size=1000, color=(0, 0, 0))
        raster.show(f'{title} (n={it})')

    ls = load_lsystem('random_tree.txt')
    segs = ls.interpret(ls.expand(20), jitter=0.0, step_decay=0.9)
    raster = render_lsystem(
        segs, size=1200,
        color_fn=tree_color,
        thickness_fn=tree_thickness,
    )
    raster.show('Фрактальное дерево (толщина + коричневый→зелёный)')
    raster.save('out_tree.png')


if __name__ == '__main__':
    main()