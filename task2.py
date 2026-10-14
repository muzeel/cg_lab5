import tkinter as tk
import random


# Алгоритм midpoint displacement для генерации ломаной (профиля горного массива).
# Пошаговая визуализация: на каждом шаге строится всё более детализированная ломаная.
class MidpointApp:
    def __init__(self, root):
        self.root = root
        root.title("Midpoint Displacement - горный массив")
        root.geometry("1250x720")
        root.configure(bg='#e8e8ee')

        # Данные алгоритма
        self.steps = []          # steps[k] = список точек [(x, y), ...] на шаге k
        self.current = 0         # текущий отображаемый шаг
        self.n = 1               # число сегментов (2^iters)
        self.playing = False
        self.play_job = None

        self._build_ui()
        self.generate()

    # Интерфейс
    def _build_ui(self):
        main = tk.Frame(self.root, bg='#e8e8ee')
        main.pack(fill='both', expand=True)

        # Холст
        self.canvas = tk.Canvas(main, bg='white',
                                highlightthickness=1, highlightbackground='#999')
        self.canvas.pack(side='left', fill='both', expand=True,
                         padx=(8, 4), pady=8)
        self.canvas.bind('<Configure>', lambda e: self.render())

        # Панель управления
        panel = tk.Frame(main, bg='#f4f4f8', width=340)
        panel.pack(side='right', fill='y', padx=(4, 8), pady=8)
        panel.pack_propagate(False)

        tk.Label(panel, text="Параметры построения",
                 font=('Segoe UI', 13, 'bold'),
                 bg='#f4f4f8').pack(pady=(14, 10))

        def row(label, var, width=10):
            f = tk.Frame(panel, bg='#f4f4f8')
            f.pack(fill='x', padx=16, pady=3)
            tk.Label(f, text=label, bg='#f4f4f8', anchor='w',
                     font=('Segoe UI', 10)).pack(side='left')
            tk.Entry(f, textvariable=var, width=width,
                     font=('Consolas', 10)).pack(side='right')

        self.left_var  = tk.StringVar(value="0.0")
        self.right_var = tk.StringVar(value="0.0")
        self.d0_var    = tk.StringVar(value="1.0")
        self.rough_var = tk.StringVar(value="0.55")
        self.iters_var = tk.StringVar(value="8")
        self.seed_var  = tk.StringVar(value="42")

        row("Левый конец (y₀):",      self.left_var)
        row("Правый конец (y₁):",     self.right_var)
        row("Начальное смещение d₀:", self.d0_var)
        row("Шероховатость r:",       self.rough_var)
        row("Число итераций:",        self.iters_var)
        row("Seed (целое):",          self.seed_var)

        tk.Button(panel, text="Построить заново", command=self.generate,
                  font=('Segoe UI', 10, 'bold'), bg='#4a7ebb', fg='white',
                  relief='flat', padx=10, pady=6).pack(fill='x',
                  padx=16, pady=(14, 6))

        # Пошаговый просмотр
        tk.Label(panel, text="Пошаговый просмотр",
                 font=('Segoe UI', 11, 'bold'),
                 bg='#f4f4f8').pack(pady=(14, 4))

        navf = tk.Frame(panel, bg='#f4f4f8')
        navf.pack(fill='x', padx=16)
        tk.Button(navf, text="<- Пред", command=self.prev_step,
                  font=('Segoe UI', 10)).pack(side='left', expand=True,
                                              fill='x', padx=2)
        tk.Button(navf, text="След ->", command=self.next_step,
                  font=('Segoe UI', 10)).pack(side='left', expand=True,
                                              fill='x', padx=2)
        self.play_btn = tk.Button(navf, text="->-> Авто", command=self.toggle_play,
                                  font=('Segoe UI', 10))
        self.play_btn.pack(side='left', expand=True, fill='x', padx=2)

        self.step_var = tk.IntVar(value=0)
        self.step_scale = tk.Scale(panel, from_=0, to=0, orient='horizontal',
                                   variable=self.step_var, command=self.on_scale,
                                   bg='#f4f4f8', highlightthickness=0,
                                   length=280, showvalue=False)
        self.step_scale.pack(fill='x', padx=16, pady=(8, 2))

        self.step_label = tk.Label(panel, text="Шаг 0 / 0", bg='#f4f4f8',
                                   font=('Segoe UI', 10, 'bold'))
        self.step_label.pack()

        self.show_all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(panel, text="Показывать предыдущие шаги",
                       variable=self.show_all_var, command=self.render,
                       bg='#f4f4f8', font=('Segoe UI', 10),
                       activebackground='#f4f4f8').pack(pady=(10, 0))

        # Информация снизу
        self.info = tk.Label(panel, text="", bg='#f4f4f8', justify='left',
                             font=('Consolas', 9), fg='#444')
        self.info.pack(side='bottom', anchor='w', padx=16, pady=12)

    # Считает все шаги midpoint displacement и сохраняет их для отображения
    def generate(self):
        try:
            lh    = float(self.left_var.get())
            rh    = float(self.right_var.get())
            d0    = float(self.d0_var.get())
            r     = float(self.rough_var.get())
            iters = int(self.iters_var.get())
            seed  = int(self.seed_var.get())
        except ValueError:
            return  # некорректный ввод

        # Ограничения на параметры
        iters = max(0, min(14, iters))
        if not (0 < r < 1):
            r = max(0.05, min(0.95, r))

        random.seed(seed)

        n = 2 ** iters                 # число сегментов на последнем шаге
        pts = [None] * (n + 1)         # массив значений y для узлов x = 0..n
        pts[0] = lh
        pts[n] = rh

        # Шаг 0 - исходная прямая из двух концов
        steps = [[(0, lh), (n, rh)]]

        d = d0           # текущая амплитуда смещения
        step_size = n    # расстояние между известными точками
        while step_size > 1:
            half = step_size // 2
            # Проходим по всем серединам сегментов
            for i in range(half, n, step_size):
                mid_y = 0.5 * (pts[i - half] + pts[i + half])
                offset = random.uniform(-d, d)
                pts[i] = mid_y + offset
            d *= r       # уменьшаем амплитуду
            step_size = half

            # Запоминаем состояние после шага: известны точки кратные step_size
            cur = [(i, pts[i]) for i in range(0, n + 1, step_size)]
            steps.append(cur)

        self.steps = steps
        self.n = n
        self.current = len(steps) - 1   # по умолчанию показываем финальную ломаную
        self.step_scale.configure(to=len(steps) - 1)
        self.step_var.set(self.current)
        self.stop_play()
        self.render()

    # Управление пошаговым просмотром
    def on_scale(self, val):
        self.current = int(float(val))
        self.render()

    def prev_step(self):
        self.stop_play()
        if self.current > 0:
            self.current -= 1
            self.step_var.set(self.current)
            self.render()

    def next_step(self):
        self.stop_play()
        if self.current < len(self.steps) - 1:
            self.current += 1
            self.step_var.set(self.current)
            self.render()

    def toggle_play(self):
        if self.playing:
            self.stop_play()
        else:
            self.playing = True
            self.current = 0
            self.step_var.set(0)
            self.play_btn.config(text="■ Стоп")
            self._play_tick()

    def stop_play(self):
        self.playing = False
        if self.play_job:
            self.root.after_cancel(self.play_job)
            self.play_job = None
        self.play_btn.config(text="▶▶ Авто")

    def _play_tick(self):
        if not self.playing:
            return
        self.render()
        if self.current < len(self.steps) - 1:
            self.current += 1
            self.step_var.set(self.current)
            self.play_job = self.root.after(600, self._play_tick)
        else:
            self.stop_play()

    # Отрисовка
    def render(self):
        c = self.canvas
        c.delete('all')
        if not self.steps:
            return

        W = c.winfo_width()
        H = c.winfo_height()
        if W < 10: W = 850
        if H < 10: H = 600

        # Границы по y - берём по всем шагам, чтобы картинка не дёргалась
        all_ys = [y for st in self.steps for _, y in st]
        ymin, ymax = min(all_ys), max(all_ys)
        if ymax - ymin < 1e-9:
            ymin -= 1.0
            ymax += 1.0
        pad_y = (ymax - ymin) * 0.1
        ymin -= pad_y
        ymax += pad_y

        padx, pady = 55, 55

        def to_px(x, y):
            px = padx + (W - 2 * padx) * x / self.n
            py = H - pady - (H - 2 * pady) * (y - ymin) / (ymax - ymin)
            return px, py

        # Базовая линия y = 0 (если видна)
        if ymin < 0 < ymax:
            _, py0 = to_px(0, 0)
            c.create_line(padx, py0, W - padx, py0,
                          fill='#dddddd', dash=(4, 4))
            c.create_text(W - padx + 18, py0, text="0",
                          fill='#999', font=('Consolas', 8))

        # Рамка поля
        c.create_rectangle(padx, pady, W - padx, H - pady, outline='#cccccc')

        # Предыдущие шаги - серые, с плавным затемнением по номеру
        if self.show_all_var.get():
            total = max(1, len(self.steps) - 1)
            for idx in range(self.current):
                st = self.steps[idx]
                t = idx / total
                g = int(215 - t * 90)
                col = f'#{g:02x}{g:02x}{g:02x}'
                coords = []
                for x, y in st:
                    px, py = to_px(x, y)
                    coords.extend([px, py])
                c.create_line(*coords, fill=col, width=1)

        # Текущий шаг
        st = self.steps[self.current]
        coords = []
        for x, y in st:
            px, py = to_px(x, y)
            coords.extend([px, py])
        c.create_line(*coords, fill='#1a4e8a', width=2.5)

        # Точки текущего шага
        k = len(st)
        radius = 4 if k <= 33 else (2 if k <= 129 else 1)
        for x, y in st:
            px, py = to_px(x, y)
            if radius >= 2:
                c.create_oval(px - radius, py - radius,
                              px + radius, py + radius,
                              fill='#e84a3a', outline='#7a1a10')
            else:
                c.create_rectangle(px, py, px + 1, py + 1,
                                   fill='#e84a3a', outline='')

        # Заголовок на холсте
        total = len(self.steps) - 1
        c.create_text(W / 2, 24,
                      text=f"Midpoint Displacement — шаг {self.current} из {total}",
                      font=('Segoe UI', 13, 'bold'), fill='#333')

        # Подписи по оси X
        for i in (0, self.n // 2, self.n):
            px, _ = to_px(i, 0)
            c.create_text(px, H - pady + 14, text=str(i),
                          fill='#666', font=('Consolas', 9))

        # Информационная панель
        self.step_label.config(text=f"Шаг {self.current} / {total}")
        self.info.config(text=(
            f"точек на шаге : {k}\n"
            f"сегментов     : {k - 1}\n"
            f"множитель r^step = "
            f"{float(self.rough_var.get() or 0.5) ** self.current:.4f}\n"
            f"всего шагов   : {len(self.steps)}"
        ))


if __name__ == "__main__":
    root = tk.Tk()
    app = MidpointApp(root)
    root.mainloop()