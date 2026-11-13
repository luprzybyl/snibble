"""Front Kivy — Snibble na Androida i desktop.

Logika gry: world.py + bot.py (bez zmian). Tu: kamera za graczem,
rysowanie "komiksowe" (grube obrysy, pastelowa paleta, oczki)
i sterowanie palcem — dotyk wskazuje kierunek jazdy (kąt ciągły).
"""
import math
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, Mesh,
                           PopMatrix, PushMatrix, Rectangle, Scale,
                           Translate, Triangle)
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from .bot import decide
from .world import (BODY_R, SEG_DIST, WORLD_H, WORLD_W, World,
                    ang_diff, norm_angle)

KEY_DIRS = {
    273: (0, -1), 274: (0, 1), 275: (1, 0), 276: (-1, 0),   # strzałki
    ord('w'): (0, -1), ord('s'): (0, 1),
    ord('d'): (1, 0), ord('a'): (-1, 0),
}
KEY_TURN = 6.0    # rad/s — "odrobinę" w stronę przytrzymanej strzałki

SNAKE_RGB = [
    (0.20, 0.78, 0.35),   # zielony
    (0.00, 0.74, 0.83),   # cyjan
    (0.94, 0.21, 0.48),   # malina
    (1.00, 0.72, 0.05),   # pomarańcz
    (0.42, 0.36, 0.90),   # fiolet
    (0.95, 0.34, 0.27),   # koral
    (0.55, 0.76, 0.29),   # limonka
]
BORDER = (0.55, 0.36, 0.22, 1)
CRYSTAL = (1.0, 0.84, 0.25, 1)
CRYSTAL_BIG = (1.0, 0.35, 0.55, 1)
RAINBOW_OUT = (1.0, 1.0, 1.0, 1)
RAINBOW_RGB = [(1.0, 0.25, 0.35, 1), (0.25, 1.0, 0.4, 1),
               (0.35, 0.55, 1.0, 1)]
ZOOM_MIN, ZOOM_MAX = 14.0, 42.0   # komórek na wysokość ekranu

# opcjonalne moduły — toggle w menu, klucz -> World/bonus;
# zamiast tekstu obok checkboxa rysowany piktogram (ikonizacja
# = zero i18n, emoji na Androidzie i tak by nie zadziałały)
MODULES = [
    ('castles', 'castle'),
    ('cannons', 'cannon'),
    ('frogs', 'frog'),
    ('portals', 'portal'),
]


class IconWidget(Widget):
    """Piktogram rysowany prymitywami Kivy — niezależny od
    czcionek. Jednostka u = połowa mniejszego boku widgetu."""
    ICONS = ('play', 'retry', 'bolt', 'castle', 'cannon',
             'frog', 'portal', 'skull')

    def __init__(self, icon, **kw):
        super().__init__(**kw)
        self.icon = icon
        self.bind(pos=lambda *_: self._redraw(),
                  size=lambda *_: self._redraw())

    def _redraw(self):
        self.canvas.clear()
        u = min(self.size) / 2
        if u <= 0:
            return
        cx, cy = self.center
        draw = getattr(self, f'_i_{self.icon}')
        with self.canvas:
            draw(cx, cy, u)

    def _i_play(self, cx, cy, u):
        Color(1, 1, 1, 1)
        Triangle(points=(cx - .5 * u, cy - .7 * u,
                         cx - .5 * u, cy + .7 * u,
                         cx + .7 * u, cy))

    def _i_retry(self, cx, cy, u):
        Color(1, 1, 1, 1)
        r = .62 * u
        # łuk 270°: od 135° do 405°(=45°); przerwa w prawym górnym
        Line(circle=(cx, cy, r, 135, 405), width=u * .11)
        # grot na końcu łuku (45°), styczna ↻ — krótki trójkąt
        a = math.radians(45)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        tx, ty = math.sin(a), -math.cos(a)
        nx, ny = math.cos(a), math.sin(a)
        tipx, tipy = px + tx * .45 * u, py + ty * .45 * u
        bx, by = px + tx * .08 * u, py + ty * .08 * u
        Triangle(points=(tipx, tipy,
                         bx + nx * .24 * u, by + ny * .24 * u,
                         bx - nx * .24 * u, by - ny * .24 * u))

    def _i_bolt(self, cx, cy, u):
        Color(1, .85, .1, 1)
        # wypełniona sylwetka błyskawicy (7 pkt, 5 trójkątów)
        vs = [(-.4, .8), (-.4, -.08), (-.16, -.08), (-.16, -.8),
              (.4, .16), (.08, .16), (.4, .8)]
        Mesh(vertices=[c for x, y in vs for c in (cx + x*u, cy + y*u, 0, 0)],
             indices=[0, 1, 6,  1, 6, 5,  2, 3, 4,  2, 4, 5,  1, 2, 5],
             mode='triangles')

    def _i_castle(self, cx, cy, u):
        Color(.62, .45, .36, 1)
        # korpus muru
        Rectangle(pos=(cx - .75*u, cy - .7*u), size=(1.5*u, 1.15*u))
        # blanki — 3 bloki z przerwami
        for bx in (-.75, -.175, .4):
            Rectangle(pos=(cx + bx*u, cy + .45*u), size=(.35*u, .3*u))
        # flaga na środkowym blanku — natychmiast czytana jako zamek
        Color(.85, .2, .2, 1)
        Line(points=(cx, cy + .95*u, cx, cy + .45*u), width=u * .06)
        Triangle(points=(cx, cy + .95*u, cx, cy + .72*u,
                         cx + .38*u, cy + .83*u))
        # brama — łuk
        Color(.15, .1, .08, 1)
        Rectangle(pos=(cx - .2*u, cy - .7*u), size=(.4*u, .62*u))
        Ellipse(pos=(cx - .2*u, cy - .1*u), size=(.4*u, .4*u))

    def _i_cannon(self, cx, cy, u):
        Color(.42, .42, .48, 1)
        # lufa — ścięty czworokąt, szeroka u nasady, wąska u wylotu
        Mesh(vertices=[cx - .48*u, cy + .12*u, 0, 0,
                       cx - .12*u, cy - .36*u, 0, 0,
                       cx + .42*u, cy + .52*u, 0, 0,
                       cx + .62*u, cy + .22*u, 0, 0],
             indices=[0, 1, 2, 3], mode='triangle_strip')
        # koło z piastą
        Ellipse(pos=(cx - .6*u, cy - .75*u), size=(.55*u, .55*u))
        Color(.15, .15, .18, 1)
        Ellipse(pos=(cx - .45*u, cy - .6*u), size=(.25*u, .25*u))
        # kula armatnia
        Ellipse(pos=(cx + .35*u, cy - .55*u), size=(.3*u, .3*u))

    def _i_frog(self, cx, cy, u):
        Color(.18, .7, .25, 1)
        Ellipse(pos=(cx - .65 * u, cy - .5 * u), size=(1.3 * u, .95 * u))
        Color(1, 1, 1, 1)
        Ellipse(pos=(cx - .45 * u, cy + .3 * u), size=(.34 * u, .34 * u))
        Ellipse(pos=(cx + .11 * u, cy + .3 * u), size=(.34 * u, .34 * u))
        Color(.05, .1, .05, 1)
        Ellipse(pos=(cx - .36 * u, cy + .39 * u), size=(.16 * u, .16 * u))
        Ellipse(pos=(cx + .2 * u, cy + .39 * u), size=(.16 * u, .16 * u))

    def _i_portal(self, cx, cy, u):
        # wąż wchodzi głową w lewy pierścień, wychodzi z prawego
        Color(.2, .85, .3, 1)
        Line(points=(cx - .98*u, cy + .2*u, cx - .9*u, cy + .28*u,
                     cx - .8*u, cy + .18*u),
             width=u * .12, cap='round')
        Triangle(points=(cx - .62*u, cy + .02*u,
                         cx - .82*u, cy + .16*u,
                         cx - .78*u, cy - .04*u))
        Line(points=(cx + .5*u, cy + .02*u, cx + .62*u, cy - .06*u,
                     cx + .74*u, cy - .12*u),
             width=u * .12, cap='round')
        Triangle(points=(cx + .95*u, cy - .18*u,
                         cx + .78*u, cy - .02*u,
                         cx + .72*u, cy - .24*u))
        # pierścienie — rozstawione szeroko, żeby nie robić ∞
        Color(*PORTAL_COLS[0])
        Line(circle=(cx - .52*u, cy, .26*u), width=u * .12)
        Color(*PORTAL_COLS[1])
        Line(circle=(cx + .52*u, cy, .26*u), width=u * .12)

    def _i_skull(self, cx, cy, u):
        Color(.92, .9, .85, 1)
        Ellipse(pos=(cx - .55 * u, cy - .35 * u), size=(1.1 * u, 1.05 * u))
        Rectangle(pos=(cx - .28 * u, cy - .62 * u), size=(.56 * u, .3 * u))
        Color(.1, .1, .12, 1)
        Ellipse(pos=(cx - .38 * u, cy - .05 * u), size=(.3 * u, .3 * u))
        Ellipse(pos=(cx + .08 * u, cy - .05 * u), size=(.3 * u, .3 * u))
        Triangle(points=(cx, cy - .15 * u,
                         cx - .1 * u, cy - .35 * u,
                         cx + .1 * u, cy - .35 * u))
        for tx in (-.18, 0, .18):
            Line(points=(cx + tx * u, cy - .62 * u, cx + tx * u, cy - .34 * u),
                 width=u * .05)


def _attach_icon(widget, icon):
    """Dokleja piktogram wycentrowany na widgecie (Button)."""
    ic = IconWidget(icon)
    widget.add_widget(ic)

    def _sync(*_):
        ic.pos, ic.size = widget.pos, widget.size
    widget.bind(pos=_sync, size=_sync)
    _sync()
    return ic
PORTAL_COLS = [(0.0, 0.85, 1.0, 1), (1.0, 0.3, 0.85, 1),
               (1.0, 0.65, 0.10, 1)]

# biomy: tło + rodzaj/gęstość dekoracji + kolor tekstu + obwódka
FLOWER_COLS = [(1.0, 0.6, 0.75, 0.9), (1.0, 0.85, 0.3, 0.9),
               (1.0, 1.0, 1.0, 0.9), (0.85, 0.55, 1.0, 0.9)]
THEMES = [
    {"bg": (0.87, 0.95, 0.78, 1), "kind": "flowers",
     "dot": (1.0, 1.0, 1.0, 0.55),
     "density": 0.45, "step": 4,
     "fg": (0, 0, 0, 1), "border": BORDER},                       # łąka
    {"bg": (0.95, 0.86, 0.62, 1), "kind": "rocks",
     "dot": (0.80, 0.66, 0.38, 0.7),
     "density": 0.5, "step": 4,
     "fg": (0, 0, 0, 1), "border": (0.55, 0.40, 0.20, 1)},        # pustynia
    {"bg": (0.50, 0.72, 0.46, 1), "kind": "bushes",
     "dot": (0.34, 0.58, 0.32, 0.9),
     "density": 0.6, "step": 4,
     "fg": (0, 0, 0, 1), "border": (0.30, 0.24, 0.14, 1)},        # las
    {"bg": (0.04, 0.05, 0.15, 1), "kind": "stars",
     "dot": (1.0, 1.0, 1.0, 0.9),
     "density": 0.6, "step": 3,
     "fg": (1, 1, 1, 1), "border": (0.4, 0.45, 0.75, 1)},         # kosmos
]


def _outline(c):
    return (c[0] * 0.55, c[1] * 0.55, c[2] * 0.55, 1)


def _emit(bucket, verts):
    """Doklej czworokąt (4 wierzchołki po 4 floaty: pos2+tc2) do (v, i)."""
    v, i = bucket
    b = len(v) // 4
    v += verts
    i += (b, b + 1, b + 2, b, b + 2, b + 3)


def _quad_verts(x, y, r):
    return [x - r, y - r, 0, 0, x + r, y - r, 0, 0,
            x + r, y + r, 0, 0, x - r, y + r, 0, 0]


def _dia_verts(x, y, r):
    return [x, y - r, 0, 0, x + r, y, 0, 0,
            x, y + r, 0, 0, x - r, y, 0, 0]


def _rect_verts(x0, y0, x1, y1):
    return [x0, y0, 0, 0, x1, y0, 0, 0, x1, y1, 0, 0, x0, y1, 0, 0]


def _rot_verts(x, y, a, hl, hw):
    """Obrócony prostokąt: środek (x,y), oś w kącie a, półdł. hl,
    półszer. hw."""
    ca, sa = math.cos(a), math.sin(a)
    px, py = -sa * hw, ca * hw
    return [x - ca * hl + px, y - sa * hl + py, 0, 0,
            x + ca * hl + px, y + sa * hl + py, 0, 0,
            x + ca * hl - px, y - sa * hl - py, 0, 0,
            x - ca * hl - px, y - sa * hl - py, 0, 0]


class GameWidget(FloatLayout):
    def __init__(self, player_name=None, auto=False, mods=None, **kw):
        super().__init__(**kw)
        self.auto = auto
        mods = mods or {}
        self.world = World(player_name=player_name,
                           castles=bool(mods.get('castles')),
                           cannons=bool(mods.get('cannons')),
                           frogs=bool(mods.get('frogs')),
                           portals=bool(mods.get('portals')))
        self._kb_angle = None
        self.steer_pos = None
        self.boost = False
        self.view_cells = ZOOM_MAX      # start: maksymalne oddalenie
        self.theme = random.choice(THEMES)
        self._over_widgets = []
        self.name_labels = {}

        fg = self.theme["fg"]
        self.lbl_board = Label(markup=True, font_size='16sp', halign='left',
                               valign='top', pos_hint={'right': 0.99, 'top': 0.99},
                               size_hint=(None, None), color=fg)
        self.btn_boost = Button(text='',
                                size_hint=(None, None),
                                size=(dp(120), dp(80)),
                                pos_hint={'right': 0.98, 'y': 0.02},
                                background_color=(1.0, 0.55, 0.2, 0.9))
        _attach_icon(self.btn_boost, 'bolt')
        self.btn_boost.bind(on_press=lambda *_: setattr(self, 'boost', True))
        self.btn_boost.bind(on_release=lambda *_: setattr(self, 'boost', False))
        self.btn_zin = Button(text='+', font_size='28sp',
                              size_hint=(None, None), size=(dp(64), dp(64)),
                              pos_hint={'x': 0.02, 'y': 0.10})
        self.btn_zout = Button(text='-', font_size='28sp',
                               size_hint=(None, None), size=(dp(64), dp(64)),
                               pos_hint={'x': 0.02, 'y': 0.02})
        self.btn_zin.bind(on_release=lambda *_: self._zoom(-3))
        self.btn_zout.bind(on_release=lambda *_: self._zoom(3))
        for wdg in (self.lbl_board, self.btn_boost,
                    self.btn_zin, self.btn_zout):
            self.add_widget(wdg)
        # desktop: śledź kursor bez klikania; na dotyku nie ma mouse_pos
        Window.bind(mouse_pos=self._on_mouse)
        Window.bind(on_key_down=self._on_key_down,
                    on_key_up=self._on_key_up)
        self.keys_held = set()
        self._ui_touches = set()    # uid dotyków pochłoniętych przez UI
        self._mouse_bound = True
        self._snake_g = {}          # sid -> dict trwałych instrukcji
        self._init_layers()
        Clock.schedule_interval(self._update, 1 / 30.0)

    def _zoom(self, d):
        self.view_cells = min(ZOOM_MAX, max(ZOOM_MIN,
                                            self.view_cells + d))

    # --- autopilot (demka/testy): kryształ + odpychanie ---
    def _autopilot(self):
        w = self.world
        p = w.player
        hx, hy = p.head
        vx = vy = 0.0
        # ściany -> do środka
        m = 18
        if hx < m or hx > WORLD_W - m or hy < m or hy > WORLD_H - m:
            return math.atan2(WORLD_H / 2 - hy, WORLD_W / 2 - hx)
        # przyciąganie: najbliższy kryształ
        best, bd = None, 1e9
        for (x, y) in w.crystals:
            d2 = (x - hx) ** 2 + (y - hy) ** 2
            if d2 < bd:
                bd, best = d2, (x, y)
        if best is not None:
            vx += (best[0] - hx) / max(math.sqrt(bd), 1)
            vy += (best[1] - hy) / max(math.sqrt(bd), 1)
        # odpychanie: punkty wszystkich ciał (w tym własnych od 6.)
        for s in w.snakes:
            if not s.alive:
                continue
            for sx, sy in s.spine[(6 if s is p else 0)::2]:
                dx, dy = hx - sx, hy - sy
                d2 = dx * dx + dy * dy
                if 0.01 < d2 < 81:
                    vx += dx / d2 * 3.0
                    vy += dy / d2 * 3.0
        return math.atan2(vy, vx) if vx or vy else p.angle

    # --- geometria ---
    def _cam(self):
        cell = max(self.height, 1) / self.view_cells
        vw, vh = self.width / cell, self.height / cell
        p = self.world.player
        px, py = p.head if p else (WORLD_W / 2, WORLD_H / 2)
        cx = min(max(px - vw / 2, 0), max(0.0, WORLD_W - vw))
        cy = min(max(py - vh / 2, 0), max(0.0, WORLD_H - vh))
        return cell, cx, cy

    def _sy(self, cell, cy, wy):
        return self.height - (wy - cy) * cell   # world +y = w dół ekranu

    # --- dotyk ---
    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            # dotyk wszedł w przycisk/widget UI — nie steruj nim wężem
            self._ui_touches.add(touch.uid)
            return True
        btn = getattr(touch, 'button', '')
        if btn == 'scrollup':
            self._zoom(-2)
            return True
        if btn == 'scrolldown':
            self._zoom(2)
            return True
        self.steer_pos = touch.pos
        return True

    def on_touch_move(self, touch):
        if touch.uid not in self._ui_touches:
            self.steer_pos = touch.pos
        return True

    def on_touch_up(self, touch):
        self._ui_touches.discard(touch.uid)
        self.steer_pos = None
        return True

    def _over_ui(self, pos):
        return any(b.collide_point(*pos) for b in
                   (self.btn_boost, self.btn_zin, self.btn_zout))

    def _on_mouse(self, _window, pos):
        # nie skręcaj, gdy kursor jest nad przyciskiem (BOOST, +/−)
        if self._over_ui(pos):
            return
        self.steer_pos = pos

    def _on_key_down(self, _w, key, *_a):
        if key in KEY_DIRS:
            self.keys_held.add(key)
        elif key == 32:                     # spacja = BOOST
            self.boost = True
        elif key == 103:                    # 'g' = dump _wl do debugowania
            self._dump_wl()                 # (d = skręt WASD)

    def _dump_wl(self):
        from kivy.graphics import (Ellipse, InstructionGroup, Line,
                                   Mesh, Rectangle)
        from kivy.core.window import Window as _W
        out = []
        def walk(ig, path):
            for k, ins in enumerate(ig.children):
                p = f"{path}/{k}"
                if isinstance(ins, InstructionGroup):
                    walk(ins, p)
                elif isinstance(ins, Ellipse):
                    out.append(f"{p} ELL {tuple(ins.pos)} {tuple(ins.size)}")
                elif isinstance(ins, Line):
                    out.append(f"{p} LINE w={ins.width} "
                               f"npts={len(ins.points) // 2}")
                elif isinstance(ins, Mesh):
                    vs = ins.vertices
                    if vs:
                        xs, ys = vs[0::4], vs[1::4]
                        out.append(f"{p} MESH n={len(vs)//4} "
                                   f"bbox=({min(xs):.1f},{min(ys):.1f})-"
                                   f"({max(xs):.1f},{max(ys):.1f})")
                    else:
                        out.append(f"{p} MESH empty")
                elif isinstance(ins, Rectangle):
                    out.append(f"{p} RECT {tuple(ins.pos)} {tuple(ins.size)}")
        walk(self._wl, "wl")
        w = self.world
        out.append(f"bullets={len(w.bullets)} "
                   f"crys={len(w.crystals)} "
                   f"player={tuple(round(v,1) for v in w.player.head)}")
        with open("/tmp/wl_dump.txt", "w") as f:
            f.write("\n".join(out))
        print("dump:", _W.screenshot(name="/tmp/wl_shot.png"))

    def _on_key_up(self, _w, key, *_a):
        self.keys_held.discard(key)
        if key == 32:
            self.boost = False

    # --- pętla ---
    def _update(self, dt):
        if not self.parent:
            if self._mouse_bound:
                Window.unbind(mouse_pos=self._on_mouse)
                Window.unbind(on_key_down=self._on_key_down,
                              on_key_up=self._on_key_up)
                self._mouse_bound = False
            return   # widget zdjęty (powrót do menu)
        w = self.world
        p = w.player
        cell, cx, cy = self._cam()
        # cel sterowania: mysz/dotyk -> kąt absolutny
        desired = None
        if self.auto and p is not None and p.alive:
            desired = self._autopilot()
        elif p is not None and p.alive and self.steer_pos is not None:
            wx = cx + self.steer_pos[0] / cell
            wy = cy + (self.height - self.steer_pos[1]) / cell
            hx, hy = p.head
            desired = math.atan2(wy - hy, wx - hx)
        # klawiatura: skręcaj własny cel (nadpisuje mysz, póki trzymana)
        dx = sum(KEY_DIRS[k][0] for k in self.keys_held)
        dy = sum(KEY_DIRS[k][1] for k in self.keys_held)
        if p is not None and p.alive and (dx or dy):
            if self._kb_angle is None:
                self._kb_angle = desired if desired is not None else p.angle
            want = math.atan2(dy, dx)
            d = ang_diff(self._kb_angle, want)
            mx = KEY_TURN * dt
            self._kb_angle = norm_angle(
                self._kb_angle + max(-mx, min(mx, d)))
            desired = self._kb_angle
        if desired is not None:
            p.target_angle = desired
        if p is not None:
            p.boost = self.boost
        w.tick(min(dt, 0.05), decide)
        self._draw(cell, cx, cy)
        self._names(cell, cx, cy)
        self._hud()
        if p is not None and not p.alive and not self._over_widgets:
            self._show_over()

    # --- rysowanie ---
    def _init_layers(self):
        """Geometria we WSPÓŁRZĘDNYCH ŚWIATA pod jedną macierzą kamery
        (Translate+Scale) — klatka to aktualizacja 4 liczb macierzy,
        a nie przeliczanie tysięcy wierzchołków w Pythonie.
        Dekoracje i ramka pieczone raz; kryształy tylko przy zmianie."""
        t = self.theme
        with self.canvas.before:
            Color(*t["bg"])
            self._bg = Rectangle(pos=(0, 0), size=self.size)
            PushMatrix()
            self._cam_tr = Translate(0, 0)
            self._cam_sc = Scale(1, 1, 1)
            self._wl = InstructionGroup()
            self.canvas.before.add(self._wl)
            PopMatrix()
        wl = self._wl
        # dekoracje: mesh per kolor, pieczone raz na start gry
        self._decor_meshes = {}
        for col in self._decor_colors():
            wl.add(Color(*col))
            m = Mesh(mode='triangles')
            wl.add(m)
            self._decor_meshes[col] = m
        self._bake_decor()
        # mur dookoła świata: zaprawa + 2 przesunięte rzędy cegieł
        self._wall_cols = [(0.42, 0.38, 0.35, 1),   # zaprawa
                           (0.48, 0.16, 0.10, 1),   # obrys cegły
                           (0.80, 0.36, 0.22, 1),   # cegła
                           (0.13, 0.14, 0.17, 1),   # żelazo (armaty)
                           (0.32, 0.34, 0.40, 1)]   # stal (lufa)
        self._wall_meshes = {}
        for col in self._wall_cols:
            wl.add(Color(*col))
            m = Mesh(mode='triangles')
            wl.add(m)
            self._wall_meshes[col] = m
        self._bake_wall()
        # kryształy: 4 grupy kolorów (obrys/fill × mały/duży)
        self._crys_meshes = {}
        for col in (_outline(CRYSTAL), CRYSTAL,
                    _outline(CRYSTAL_BIG), CRYSTAL_BIG,
                    RAINBOW_OUT, *RAINBOW_RGB):
            wl.add(Color(*col))
            m = Mesh(mode='triangles')
            wl.add(m)
            self._crys_meshes[col] = m
        self._crys_key = None
        # pociski armat: pool par Ellipse (obrys+blask); size=0, bo
        # domyślny rozmiar Ellipse to 100x100 = dysk na 1/3 mapy
        self._ball_g = []
        for _ in range(24):
            wl.add(Color(0.12, 0.12, 0.16, 1))
            eo = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(eo)
            wl.add(Color(0.85, 0.9, 0.95, 1))
            ei = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(ei)
            self._ball_g.append((eo, ei))
        # żaby: pool 12 × (obrys, 2 łapy+ciało, 2 oczy, 2 źrenice)
        self._frog_g = []
        for _ in range(12):
            wl.add(Color(0.10, 0.45, 0.20, 1))
            fo = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(fo)
            wl.add(Color(0.25, 0.80, 0.30, 1))
            l1 = Ellipse(pos=(0, 0), size=(0, 0))
            l2 = Ellipse(pos=(0, 0), size=(0, 0))
            ff = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(l1); wl.add(l2); wl.add(ff)
            wl.add(Color(1, 1, 1, 1))
            w1 = Ellipse(pos=(0, 0), size=(0, 0))
            w2 = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(w1); wl.add(w2)
            wl.add(Color(0, 0, 0, 1))
            p1 = Ellipse(pos=(0, 0), size=(0, 0))
            p2 = Ellipse(pos=(0, 0), size=(0, 0))
            wl.add(p1); wl.add(p2)
            self._frog_g.append(
                (fo, l1, l2, ff, w1, w2, p1, p2))
        # portale: statyczne pierścienie (obrys + dziura)
        for p in self.world.portals:
            col = PORTAL_COLS[p['pair'] % len(PORTAL_COLS)]
            wl.add(Color(*_outline(col)))
            wl.add(Ellipse(pos=(p['x'] - 1.1, p['y'] - 1.1),
                           size=(2.2, 2.2)))
            wl.add(Color(*col))
            wl.add(Ellipse(pos=(p['x'] - 0.95, p['y'] - 0.95),
                           size=(1.9, 1.9)))
            wl.add(Color(0.05, 0.05, 0.12, 1))
            wl.add(Ellipse(pos=(p['x'] - 0.55, p['y'] - 0.55),
                           size=(1.1, 1.1)))
        # węże: per-sid InstructionGroup dopinane do _wl w _draw

    def _decor_colors(self):
        if self.theme["kind"] == "flowers":
            return FLOWER_COLS + [(1.0, 0.9, 0.2, 1)]
        return [self.theme["dot"]]

    def _mk_snake(self, col):
        """Nowy komplet instrukcji węża: 2 linie + głowa + 2 oczka."""
        oc = _outline(col)
        lines = []
        for _ in range(3):       # max 3 kawałki (portalowe wyrwy)
            lo = Line(joint='bevel', cap='round')
            li = Line(joint='bevel', cap='round')
            lines.append((lo, li))
        ho, hf = (Ellipse(pos=(0, 0), size=(0, 0)) for _ in range(2))
        w1, w2 = (Ellipse(pos=(0, 0), size=(0, 0)) for _ in range(2))
        p1, p2 = (Ellipse(pos=(0, 0), size=(0, 0)) for _ in range(2))
        g = InstructionGroup()
        for lo, li in lines:
            g.add(Color(*oc))
            g.add(lo)
            g.add(Color(*col))
            g.add(li)
        g.add(Color(*oc))
        g.add(ho)
        g.add(Color(*col))
        g.add(hf)
        g.add(Color(1, 1, 1, 1))
        g.add(w1)
        g.add(w2)
        g.add(Color(0, 0, 0, 1))
        g.add(p1)
        g.add(p2)
        self._wl.add(g)
        return {"grp": g, "lines": lines, "ho": ho, "hf": hf,
                "w1": w1, "w2": w2, "p1": p1, "p2": p2}

    def _bake_decor(self):
        """Cała mapa dekoracji biomu w koordynatach świata — raz."""
        t = self.theme
        db = {c: ([], []) for c in self._decor_meshes}
        st = t["step"]
        for gy in range(0, int(WORLD_H) + 1, st):
            for gx in range(0, int(WORLD_W) + 1, st):
                h = ((gx * 73856093) ^ (gy * 19349663)) & 255
                if h / 255.0 > t["density"]:
                    continue
                ox = (((h * 37) & 15) / 15 - 0.5) * st * 0.7
                oy = (((h * 53) & 15) / 15 - 0.5) * st * 0.7
                self._decor(t, h, gx + ox, gy + oy, db)
        for col, mesh in self._decor_meshes.items():
            v, i = db[col]
            mesh.vertices = v
            mesh.indices = i

    def _bake_wall(self):
        """Mury: obwód planszy + przeszkody (zamki) — pieczone raz."""
        wm, bd, bf, iron, steel = self._wall_cols
        bk = {c: ([], []) for c in self._wall_meshes}
        W = 1.4                      # szerokość pasa murku
        rects = [(0, 0, WORLD_W, W),
                 (0, WORLD_H - W, WORLD_W, WORLD_H),
                 (0, W, W, WORLD_H - W),
                 (WORLD_W - W, W, WORLD_W, WORLD_H - W)]
        rects += list(self.world.obstacles)
        for x0, y0, x1, y1 in rects:
            _emit(bk[wm], _rect_verts(x0, y0, x1, y1))
            self._brick_fill(bk, bd, bf, x0, y0, x1, y1)
        for c in self.world.cannons:
            x, y, a = c['x'], c['y'], c['angle']
            ca, sa = math.cos(a), math.sin(a)
            # lufa: od środka wieży do 1.8 na zewnątrz
            _emit(bk[steel], _rot_verts(x + ca * 0.9, y + sa * 0.9,
                                        a, 0.95, 0.36))
            # wylot lufy — pogrubienie
            _emit(bk[steel], _dia_verts(x + ca * 1.85, y + sa * 1.85,
                                        0.4))
            # wieża: oktagon z dwóch kwadratów + jasny hub
            _emit(bk[iron], _rot_verts(x, y, 0, 1.0, 1.0))
            _emit(bk[iron], _rot_verts(x, y, math.pi / 4, 0.75, 0.75))
            _emit(bk[steel], _dia_verts(x, y, 0.3))
        for col, mesh in self._wall_meshes.items():
            v, i = bk[col]
            mesh.vertices = v
            mesh.indices = i

    def _brick_fill(self, bk, bd, bf, x0, y0, x1, y1):
        """Wykafelkuj rect cegłami (przesunięte rzędy jak w murze)."""
        L, H, G = 2.0, 0.55, 0.14    # cegła: długość, wysokość, fuga
        r = 0
        y = y0 + 0.06
        while y + 0.4 < y1:
            x = x0 + 0.06 - (L / 2 if r % 2 else 0.0)
            while x < x1:
                a0, a1 = max(x, x0), min(x + L, x1)
                if a1 - a0 >= 0.4:
                    _emit(bk[bd], _rect_verts(a0 - .06, y - .06,
                                              a1 + .06, y + H + .06))
                    _emit(bk[bf], _rect_verts(a0, y, a1, y + H))
                x += L + G
            y += H + G
            r += 1

    def _bake_crys(self):
        """Wszystkie kryształy świata w koordynatach świata."""
        cb = {c: ([], []) for c in self._crys_meshes}
        os_, oB = _outline(CRYSTAL), _outline(CRYSTAL_BIG)
        for (gx, gy), v in self.world.crystals.items():
            sx, sy = gx + 0.5, gy + 0.5
            if v >= 30:
                # tęczowy: biały obrys + 3 chromatyczne romby
                _emit(cb[RAINBOW_OUT], _dia_verts(sx, sy, 0.85))
                for c, (ox, oy) in zip(RAINBOW_RGB,
                                       ((-0.14, 0.12), (0.14, 0.12),
                                        (0.0, -0.16))):
                    _emit(cb[c], _dia_verts(sx + ox, sy + oy, 0.5))
            elif v > 1:
                _emit(cb[oB], _dia_verts(sx, sy, 0.7))
                _emit(cb[CRYSTAL_BIG], _dia_verts(sx, sy, 0.5))
            else:
                _emit(cb[os_], _dia_verts(sx, sy, 0.46))
                _emit(cb[CRYSTAL], _dia_verts(sx, sy, 0.33))
        for col, mesh in self._crys_meshes.items():
            v, i = cb[col]
            mesh.vertices = v
            mesh.indices = i

    def _draw(self, cell, cx, cy):
        w = self.world
        h = self.height
        self._bg.size = self.size
        # kamera = 4 liczby w macierzy: (x-cx)*cell, h-(y-cy)*cell
        self._cam_tr.x = -cell * cx
        self._cam_tr.y = h + cell * cy
        self._cam_sc.x = cell
        self._cam_sc.y = -cell

        # kryształy: przebudowa tylko gdy się zmieniły (fingerprint)
        cr = w.crystals
        key = len(cr) + sum(x * 31 + y * 7 + v
                            for (x, y), v in cr.items())
        if key != self._crys_key:
            self._bake_crys()
            self._crys_key = key

        # węże: punkty wprost w koordynatach świata
        alive = set()
        for s in w.snakes:
            if not s.alive or len(s.spine) < 2:
                continue
            alive.add(s.sid)
            g = self._snake_g.get(s.sid)
            if g is None:
                g = self._mk_snake(SNAKE_RGB[s.color % len(SNAKE_RGB)])
                self._snake_g[s.sid] = g
            sp = s.spine
            sampled = sp[::2] + ([sp[-1]] if (len(sp) - 1) % 2 else [])
            # rozcinaj polyline w miejscach wyrw (portal!)
            gap2 = (SEG_DIST * 4) ** 2
            pieces = [[sampled[0][0], sampled[0][1]]]
            for i in range(1, len(sampled)):
                px, py = sampled[i]
                qx, qy = sampled[i - 1]
                if (px - qx) ** 2 + (py - qy) ** 2 > gap2 \
                        and len(pieces) < len(g["lines"]):
                    pieces.append([])
                pieces[-1] += [px, py]
            for i, (lo, li) in enumerate(g["lines"]):
                pts = pieces[i] if i < len(pieces) else []
                lo.points = pts
                lo.width = BODY_R + 0.15
                li.points = pts
                li.width = BODY_R
            self._head(s, g)
        for sid in set(self._snake_g) - alive:
            self._wl.remove(self._snake_g.pop(sid)["grp"])

        # pociski: pool Ellipse, nieużywane zwijane do 0
        for i, (eo, ei) in enumerate(self._ball_g):
            if i < len(w.bullets):
                b = w.bullets[i]
                eo.pos = (b['x'] - 0.3, b['y'] - 0.3)
                eo.size = (0.6, 0.6)
                ei.pos = (b['x'] - 0.1, b['y'] + 0.04)
                ei.size = (0.2, 0.2)
            elif eo.size[0]:
                eo.size = ei.size = (0, 0)

        # żaby: owalne ciało, łapy, oczy wystające ponad łeb;
        # nieużywane sloty zwijane do 0
        for i, (fo, l1, l2, ff, w1, w2, p1, p2) in \
                enumerate(self._frog_g):
            if i < len(w.frogs):
                f = w.frogs[i]
                fx, fy = f['x'], f['y']
                # uwaga: oś Y świata jest odwrócona (+y = w dół
                # ekranu) — oczy na -y, łapy na +y
                hop = abs(math.sin(math.pi * f['jump'])) \
                    if f['jump'] is not None else 0.0
                fy -= hop * 1.2           # skok = w górę ekranu
                rw, rh = 0.62, 0.46       # pół szer./wys. ciała
                fo.pos = (fx - rw - 0.07, fy - rh - 0.07)
                fo.size = (2 * (rw + 0.07), 2 * (rh + 0.07))
                # łapy tylne — owalne płetwy pod bokami ciała
                l1.pos = (fx - 0.72, fy + 0.36)
                l1.size = (0.5, 0.26)
                l2.pos = (fx + 0.22, fy + 0.36)
                l2.size = (0.5, 0.26)
                ff.pos = (fx - rw, fy - rh)
                ff.size = (2 * rw, 2 * rh)
                # oczy ponad ciałem (wizualnie: -y świata)
                er, ey = 0.15, fy - 0.30
                w1.pos = (fx - 0.26 - er, ey - er)
                w1.size = (2 * er, 2 * er)
                w2.pos = (fx + 0.26 - er, ey - er)
                w2.size = (2 * er, 2 * er)
                pr = 0.065
                p1.pos = (w1.pos[0] + er - pr, w1.pos[1] + er - pr)
                p1.size = (2 * pr, 2 * pr)
                p2.pos = (w2.pos[0] + er - pr, w2.pos[1] + er - pr)
                p2.size = (2 * pr, 2 * pr)
            elif fo.size[0]:
                fo.size = l1.size = l2.size = ff.size = w1.size \
                    = w2.size = p1.size = p2.size = (0, 0)

    def _head(self, s, g):
        hx, hy = s.head
        hr = BODY_R * 1.3
        g["ho"].pos = (hx - hr - 0.1, hy - hr - 0.1)
        g["ho"].size = (2 * (hr + 0.1), 2 * (hr + 0.1))
        g["hf"].pos = (hx - hr, hy - hr)
        g["hf"].size = (2 * hr, 2 * hr)
        a = s.angle
        for i, side in enumerate((-1, 1)):
            ea = a + side * 0.85
            ex = hx + math.cos(ea) * hr * 0.55
            ey = hy + math.sin(ea) * hr * 0.55
            er = hr * 0.34
            g[f"w{i + 1}"].pos = (ex - er, ey - er)
            g[f"w{i + 1}"].size = (2 * er, 2 * er)
            pr = er * 0.45
            px = ex + math.cos(a) * er * 0.4
            py = ey + math.sin(a) * er * 0.4
            g[f"p{i + 1}"].pos = (px - pr, py - pr)
            g[f"p{i + 1}"].size = (2 * pr, 2 * pr)

    def _decor(self, t, h, x, y, db):
        """Emit jednego elementu dekoracji (koordynaty świata)."""
        kind = t["kind"]
        if kind == "flowers":
            r = 0.13
            b = db[FLOWER_COLS[h % len(FLOWER_COLS)]]
            for dx, dy in ((0, .9), (0, -.9), (.9, 0), (-.9, 0)):
                _emit(b, _quad_verts(x + dx * r * 2, y + dy * r * 2, r))
            _emit(db[(1.0, 0.9, 0.2, 1)], _quad_verts(x, y, r))
        elif kind == "rocks":
            _emit(db[t["dot"]],
                  _dia_verts(x, y, 0.15 + 0.2 * h / 255))
        elif kind == "bushes":
            r = 0.3
            b = db[t["dot"]]
            _emit(b, _quad_verts(x, y, r))
            _emit(b, _quad_verts(x - r * 1.2, y - r * 0.3, r * 0.7))
            _emit(b, _quad_verts(x + r * 1.0, y - r * 0.3, r * 0.7))
        elif kind == "stars":
            if h % 9 == 0:
                _emit(db[t["dot"]], _dia_verts(x, y, 0.28))
            else:
                _emit(db[t["dot"]],
                      _quad_verts(x, y, 0.05 + 0.1 * h / 255))

    def _names(self, cell, cx, cy):
        alive = set()
        for s in self.world.snakes:
            if not s.alive:
                continue
            alive.add(s.sid)
            lbl = self.name_labels.get(s.sid)
            if lbl is None:
                lbl = Label(text=f"[b]{s.name}[/b]", markup=True,
                            font_size='15sp', color=self.theme["fg"],
                            size_hint=(None, None))
                lbl.texture_update()
                lbl.size = lbl.texture.size
                self.name_labels[s.sid] = lbl
                self.add_widget(lbl)
            lbl.center_x = (s.head[0] - cx) * cell
            lbl.y = self._sy(cell, cy, s.head[1]) + BODY_R * cell * 1.7
        for sid in set(self.name_labels) - alive:
            self.remove_widget(self.name_labels.pop(sid))

    # --- HUD ---
    def _set_lbl(self, lbl, txt):
        """Nadpisz tekst tylko przy zmianie (texture regen jest droga)."""
        if lbl.text != txt:
            lbl.text = txt
            lbl.texture_update()
            lbl.size = lbl.texture_size

    def _hud(self):
        p = self.world.player
        if p is None:
            return
        board = sorted(self.world.snakes, key=lambda s: -s.length)
        pos = next(i for i, s in enumerate(board) if s is p)
        lo = max(0, min(pos - 2, len(board) - 5))
        lines = []
        for i in range(lo, min(lo + 5, len(board))):
            s = board[i]
            line = f"{i + 1}. {s.name[:10]} {s.length:.0f}"
            lines.append(f"[b]{line}[/b]" if s is p else line)
        self._set_lbl(self.lbl_board, "\n".join(lines))

    def _show_over(self):
        p = self.world.player
        skull = IconWidget('skull', size_hint=(None, None),
                           size=(dp(100), dp(100)),
                           pos_hint={'center_x': 0.5, 'center_y': 0.68})
        lbl = Label(markup=True, font_size='26sp',
                    text=f"[b]{p.name}: {p.length:.0f}[/b]",
                    pos_hint={'center_x': 0.5, 'center_y': 0.57},
                    size_hint=(None, None), color=(0.95, 0.95, 0.95, 1))
        btn = Button(text='',
                     size_hint=(None, None), size=(dp(220), dp(70)),
                     pos_hint={'center_x': 0.5, 'center_y': 0.44},
                     background_color=(0.2, 0.7, 0.3, 1))
        _attach_icon(btn, 'retry')
        btn.bind(on_release=lambda *_: self._restart())
        btn_menu = Button(text='MENU', font_size='22sp',
                          size_hint=(None, None), size=(dp(220), dp(70)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.33},
                          background_color=(0.4, 0.4, 0.4, 1))
        btn_menu.bind(
            on_release=lambda *_: App.get_running_app().show_menu())
        self._over_widgets = [skull, lbl, btn, btn_menu]
        for wdg in self._over_widgets:
            self.add_widget(wdg)

    def _restart(self):
        for wdg in self._over_widgets:
            self.remove_widget(wdg)
        self._over_widgets = []
        self.world.respawn_player()


class SnibbleApp(App):
    autostart = None          # GameWidget do wstrzyknięcia (zamiast menu)

    def build(self):
        self.title = 'Snibble'
        root = FloatLayout()
        root.add_widget(self.autostart or self._menu_box())
        return root

    # --- zapamiętywanie pól połączenia ---
    def _cfg_path(self):
        import os
        return os.path.join(self.user_data_dir, 'settings.json')

    def _load_cfg(self):
        import json
        try:
            with open(self._cfg_path()) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cfg(self):
        import json
        try:
            with open(self._cfg_path(), 'w') as f:
                json.dump({'name': self.ti.text.strip(),
                           'mods': self.mods}, f)
        except Exception:
            pass

    def _menu_box(self):
        cfg = self._load_cfg()
        saved = cfg.get('mods', {})
        self.mods = {k: bool(saved.get(k)) for k, _ in MODULES}
        box = BoxLayout(orientation='vertical', spacing=dp(10),
                        size_hint=(0.6, None), height=dp(340),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5})
        box.add_widget(Label(text='[b]Snibble[/b]', markup=True,
                             font_size='34sp', size_hint_y=None,
                             height=dp(60), color=(0.1, 0.5, 0.1, 1)))
        self.ti = TextInput(hint_text='Twoje imię', multiline=False,
                            text=cfg.get('name', ''),
                            font_size='22sp', size_hint_y=None, height=dp(55))
        btn = Button(text='', size_hint_y=None,
                     height=dp(60),
                     background_color=(0.2, 0.7, 0.3, 1))
        _attach_icon(btn, 'play')
        btn.bind(on_release=lambda *_: self._start())
        box.add_widget(self.ti)
        box.add_widget(btn)
        # toggle modułów — dopisuj nowe do MODULES, tu samo się pojawi
        for key, icon in MODULES:
            row = BoxLayout(orientation='horizontal', spacing=dp(10),
                            size_hint_y=None, height=dp(44))
            cb = CheckBox(active=self.mods[key],
                          size_hint=(None, None), size=(dp(36), dp(36)))
            cb.bind(active=lambda _cb, v, k=key:
                    self.mods.__setitem__(k, v))
            row.add_widget(cb)
            row.add_widget(IconWidget(icon, size_hint=(None, None),
                                      size=(dp(40), dp(40))))
            box.add_widget(row)
        return box

    def _start(self):
        name = self.ti.text.strip() or 'Ty'
        self._save_cfg()
        self.root.clear_widgets()
        self.root.add_widget(GameWidget(player_name=name,
                                        mods=self.mods))

    def show_menu(self):
        self.root.clear_widgets()
        self.root.add_widget(self._menu_box())
