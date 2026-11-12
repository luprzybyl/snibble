"""Symulacja świata MultiSnake — czysty Python, bez zależności od UI.

Model ciągły: pozycje float w "komórkach", wąż ma kierunek (kąt) i skręca
płynnie z ograniczoną prędkością kątową. Kolizje rasteryzowane na siatkę
komórek — ten sam model działa pod curses i pod Kivy.
"""
from __future__ import annotations

import math
import random

# --- konfiguracja ---
WORLD_W = WORLD_H = 300.0        # świat w komórkach
START_LEN = 12.0                 # długość łuku w komórkach
NUM_BOTS = 9
SEG_DIST = 0.5                   # odstęp punktów kręgosłupa
BODY_R = 0.8                     # promień ciała (kolizje/AI)
HEAD_R = BODY_R
CONTACT_D2 = 1.3 ** 2            # kontakt głowa-ciało -> przegryzienie
MIN_SURVIVE_LEN = 4.0            # krótszy kikut po odgryzieniu -> śmierć
SPEED = 10.0                     # komórek/s
BOOST_MULT = 1.9
BOOST_MIN_LEN = 8.0
BOOST_DRAIN = 3.0                # długość/s spalana przy booscie
TURN_RATE = 4.5                  # rad/s
SELF_MARGIN = 8                  # punkty przy głowie bez self-collision
CRYSTAL_DENSITY = 1 / 150
CRYSTAL_R = 0.35
CORPSE_EVERY = 4                 # co który punkt zwłok -> kryształek
CORPSE_VALUE = 2
CORPSE_TTL = 15.0        # s — bazowy czas zycia krysztalu ze zwlok
CORPSE_TTL_JIT = 4.0     # +-s losowy jitter TTL (nie znikaja naraz)
RESPAWN_DELAY = 3.0
SPAWN_CLEARANCE = 9.0
SPAWN_SHIELD = 1.5        # s — duch po spawnie/respawnie
CASTLE_COUNT = 5          # liczba zamków (moduł)
CASTLE_SIZE = 18.0        # bok zamku
CASTLE_TOWER = 3.0        # bok wieży narożnej
CASTLE_KEEP = 2.2         # bok wieży środkowej
CASTLE_WALL = 0.9         # grubość muru zamku
CASTLE_GATE = 4.8         # szerokość bramy (3 grubości węża)
RAINBOW_VALUE = 30        # tęczowy kryształ w głębi zamku
CANNON_COUNT = 6          # liczba armat (moduł)
CANNON_R = 0.7            # pół przeszkody armaty
CANNON_PERIOD = (2.5, 4.5)  # s — okres strzału (losowy)
CANNON_RANGE = (18.0, 40.0) # zasięg pocisku (losowy)
BULLET_SPEED = 15.0       # komórek/s
BULLET_R = 0.3
FROG_COUNT = 8            # żab na planszy (moduł)
FROG_R = 0.55             # promień żaby (zjadanie)
FROG_IDLE = (0.8, 2.2)    # s — pauza między skokami
FROG_HOP_T = 0.35         # s — czas lotu
FROG_HOP_D = (3.0, 7.0)   # zasięg skoku
FROG_VALUE = 5            # +długość za zjedzenie
PORTAL_PAIRS = 3          # par portali (moduł)
PORTAL_R = 1.0            # promień wejścia
PORTAL_CD = 1.2           # s — blokada re-entry po teleporcie
BOT_THINK_DIV = 3                # bot myśli co 3. tick (rozmieszczone po sid)

DIRS8 = {
    "N": (0, -1), "NE": (1, -1), "E": (1, 0), "SE": (1, 1),
    "S": (0, 1), "SW": (-1, 1), "W": (-1, 0), "NW": (-1, -1),
}
ANGLE8 = {n: math.atan2(dy, dx) for n, (dx, dy) in DIRS8.items()}

BOT_NAMES = ["Boa", "Pyton", "Żmija", "Kobra", "Anakonda",
             "Żarłacz", "Grzechotnik", "Taipan", "Mamba"]


def norm_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def ang_diff(a, b):
    return norm_angle(b - a)


def dist2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


def arc_len(pts):
    return sum(math.hypot(bx - ax, by - ay)
               for (ax, ay), (bx, by) in zip(pts, pts[1:]))


def cells_in_circle(x, y, r):
    """Komórki siatki, których środki leżą w kole (x, y, r)."""
    for cx in range(int(x - r), int(x + r) + 1):
        for cy in range(int(y - r), int(y + r) + 1):
            if (cx + 0.5 - x) ** 2 + (cy + 0.5 - y) ** 2 <= r * r:
                yield (cx, cy)


def body_cells(x, y):
    """Komórka zajmowana przez punkt ciała — cienka wstęga 1 komórki;
    punkty co 0.5 dają ciągłą linię (8-spójną)."""
    return ((int(x), int(y)),)


class Snake:
    def __init__(self, sid, name, color, x, y, angle, is_bot=True):
        self.sid = sid
        self.name = name
        self.color = color
        self.angle = angle
        self.target_angle = angle
        self.length = START_LEN
        self.is_bot = is_bot
        self.boost = False
        self.alive = True
        self.respawn_in = 0.0
        self.shield = SPAWN_SHIELD
        self.portal_cd = 0.0
        ca, sa = math.cos(angle), math.sin(angle)
        self.spine = [(x - ca * SEG_DIST * i, y - sa * SEG_DIST * i)
                      for i in range(int(START_LEN / SEG_DIST) + 1)]

    @property
    def head(self):
        return self.spine[0]

    def steer(self, dt):
        d = ang_diff(self.angle, self.target_angle)
        mx = TURN_RATE * dt
        self.angle = norm_angle(self.angle + max(-mx, min(mx, d)))

    def advance(self, step):
        hx, hy = self.spine[0]
        nx = hx + math.cos(self.angle) * step
        ny = hy + math.sin(self.angle) * step
        if len(self.spine) > 1 and math.hypot(nx - self.spine[1][0],
                                              ny - self.spine[1][1]) >= SEG_DIST:
            self.spine.insert(0, (nx, ny))
        else:
            self.spine[0] = (nx, ny)
        self._trim()

    def _trim(self):
        target = self.length
        total = 0.0
        pts = self.spine
        for i in range(1, len(pts)):
            gap = math.hypot(pts[i][0] - pts[i - 1][0],
                             pts[i][1] - pts[i - 1][1])
            if total + gap >= target:
                keep = target - total
                t = keep / gap if gap else 0.0
                pts[i] = (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t,
                          pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t)
                del pts[i + 1:]
                return
            total += gap


class World:
    def __init__(self, seed=None, player_name="Ty", castles=False,
                 cannons=False, frogs=False, portals=False):
        self.rng = random.Random(seed)
        self.time = 0.0
        self.tick_count = 0
        self.snakes: list[Snake] = []
        self.crystals: dict[tuple[int, int], int] = {}
        self.crys_born: dict[tuple[int, int], float] = {}
        self.obstacles = self._gen_castles() if castles else []
        self.cannons = self._gen_cannons() if cannons else []
        self.bullets: list[dict] = []
        self.obstacles += [(c['x'] - CANNON_R, c['y'] - CANNON_R,
                            c['x'] + CANNON_R, c['y'] + CANNON_R)
                           for c in self.cannons]
        self.occ: dict[tuple[int, int], tuple[int, int]] = {}
        self._next_sid = 100        # sidy zdalnych graczy od 100
        self.player = None
        if player_name is not None:
            self.player = self._spawn(0, player_name or "Ty", 1,
                                      is_bot=False)
        for i in range(NUM_BOTS):
            self._spawn(i + 1, BOT_NAMES[i % len(BOT_NAMES)],
                        2 + i % 6, is_bot=True)
        self._fill_crystals()
        self.frogs = self._gen_frogs() if frogs else []
        self.portals = self._gen_portals() if portals else []

    def _gen_castles(self):
        """Rozstaw zamki: losowe pozycje, min. odstępy od siebie
        i krawędzi. Każdy = pierścień murów z bramą."""
        obs, placed = [], []
        for _ in range(300):
            if len(placed) >= CASTLE_COUNT:
                break
            m = CASTLE_SIZE / 2 + 12
            cx = self.rng.uniform(m, WORLD_W - m)
            cy = self.rng.uniform(m, WORLD_H - m)
            if any(abs(cx - px) < CASTLE_SIZE + 14
                   and abs(cy - py) < CASTLE_SIZE + 14
                   for px, py in placed):
                continue
            placed.append((cx, cy))
            gate = self.rng.randrange(4)
            obs += self._castle_rects(cx, cy, gate)
            # tęczowy kryształ: środek korytarza naprzeciw bramy
            dx, dy = ((0, 1), (0, -1), (1, 0), (-1, 0))[gate]
            cor = CASTLE_SIZE / 2 - CASTLE_TOWER - CASTLE_KEEP / 2
            off = CASTLE_KEEP / 2 + cor / 2
            self._drop_crystal((int(cx + dx * off),
                                int(cy + dy * off)), RAINBOW_VALUE)
        return obs

    def _castle_rects(self, cx, cy, gate):
        """Zamek: 4 wieże narożne + mury między nimi + keep na
        środku; brama na losowej stronie -> lista rectów."""
        S, TW, WT, G, K = (CASTLE_SIZE, CASTLE_TOWER, CASTLE_WALL,
                           CASTLE_GATE, CASTLE_KEEP)
        x0, y0, x1, y1 = cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2
        out = [(x0, y0, x0 + TW, y0 + TW),          # wieża LD
               (x1 - TW, y0, x1, y0 + TW),          # wieża PD
               (x0, y1 - TW, x0 + TW, y1),          # wieża LG
               (x1 - TW, y1 - TW, x1, y1),          # wieża PG
               (cx - K / 2, cy - K / 2,             # keep
                cx + K / 2, cy + K / 2)]

        def h(y, a, b):
            return (a, y, b, y + WT)

        def v(x, a, b):
            return (x, a, x + WT, b)

        for g, seg in ((0, h(y0 + TW - WT, x0 + TW, x1 - TW)),
                       (1, h(y1 - TW, x0 + TW, x1 - TW)),
                       (2, v(x0 + TW - WT, y0 + TW, y1 - TW)),
                       (3, v(x1 - TW, y0 + TW, y1 - TW))):
            if g == gate:        # brama = dwa krótkie odcinki
                a, b = (cx - G / 2, cx + G / 2) if g < 2 \
                    else (cy - G / 2, cy + G / 2)
                if g < 2:
                    out += [(seg[0], seg[1], a, seg[3]),
                            (b, seg[1], seg[2], seg[3])]
                else:
                    out += [(seg[0], seg[1], seg[2], a),
                            (seg[0], b, seg[2], seg[3])]
            else:
                out.append(seg)
        return [r for r in out
                if r[2] - r[0] > 0.1 and r[3] - r[1] > 0.1]

    def _hit_obstacle(self, x, y):
        return any(x0 <= x <= x1 and y0 <= y <= y1
                   for x0, y0, x1, y1 in self.obstacles)

    def _near_obstacle(self, x, y, r):
        """True gdy punkt jest bliżej niż r od którejś przeszkody."""
        for x0, y0, x1, y1 in self.obstacles:
            dx = max(x0 - x, 0.0, x - x1)
            dy = max(y0 - y, 0.0, y - y1)
            if dx * dx + dy * dy < r * r:
                return True
        return False

    def _gen_frogs(self):
        """Żaby: losowe wolne pozycje (z dala od głów na starcie)."""
        return [{'x': x, 'y': y,
                 'idle': self.rng.uniform(*FROG_IDLE), 'jump': None,
                 'eaten': False}
                for _ in range(FROG_COUNT)
                for x, y in [self._free_spot()]]

    def _tick_frogs(self, dt):
        """Skoki żab + zjadanie (+FROG_VALUE długości)."""
        eat_d2 = (HEAD_R + FROG_R + 0.3) ** 2
        for s in self.snakes:
            if not s.alive:
                continue
            hx, hy = s.head
            for f in self.frogs:
                if not f['eaten'] and dist2(hx, hy, f['x'], f['y']) \
                        < eat_d2:
                    f['eaten'] = True
                    s.length += FROG_VALUE
        self.frogs = [f for f in self.frogs if not f['eaten']]
        while len(self.frogs) < FROG_COUNT:
            x, y = self._free_spot()
            self.frogs.append({'x': x, 'y': y,
                               'idle': self.rng.uniform(*FROG_IDLE),
                               'jump': None, 'eaten': False})
        for f in self.frogs:
            if f['jump'] is not None:
                f['jump'] += dt / FROG_HOP_T
                t = min(f['jump'], 1.0)
                f['x'] = f['x0'] + (f['tx'] - f['x0']) * t
                f['y'] = f['y0'] + (f['ty'] - f['y0']) * t
                if t >= 1.0:
                    f['jump'] = None
                    f['idle'] = self.rng.uniform(*FROG_IDLE)
            else:
                f['idle'] -= dt
                if f['idle'] <= 0:
                    for _ in range(10):
                        a = self.rng.uniform(0, 2 * math.pi)
                        d = self.rng.uniform(*FROG_HOP_D)
                        tx = f['x'] + math.cos(a) * d
                        ty = f['y'] + math.sin(a) * d
                        if (2 <= tx < WORLD_W - 2
                                and 2 <= ty < WORLD_H - 2
                                and not self._hit_obstacle(tx, ty)):
                            f['jump'] = 0.0
                            f['x0'], f['y0'] = f['x'], f['y']
                            f['tx'], f['ty'] = tx, ty
                            break
                    else:
                        f['idle'] = 0.3

    def _gen_portals(self):
        """PORTAL_PAIRS × 2 portale; min. 30 komórek między nimi."""
        ports = []
        for pair in range(PORTAL_PAIRS):
            for _ in range(2):
                for _try in range(200):
                    x = self.rng.uniform(10, WORLD_W - 10)
                    y = self.rng.uniform(10, WORLD_H - 10)
                    if self._near_obstacle(x, y, 2.0):
                        continue
                    if any(dist2(x, y, q['x'], q['y']) < 900
                           for q in ports):
                        continue
                    ports.append({'x': x, 'y': y, 'pair': pair})
                    break
        return ports

    def _tick_portals(self, dt):
        """Wjazd = teleport głowy; reszta kręgosłupa zostaje w
        wejściu i jest konsumowana przez _trim."""
        for s in self.snakes:
            if not s.alive:
                continue
            if s.portal_cd > 0:
                s.portal_cd -= dt
                continue
            hx, hy = s.head
            for p in self.portals:
                if dist2(hx, hy, p['x'], p['y']) >= PORTAL_R ** 2:
                    continue
                q = next(q for q in self.portals
                         if q['pair'] == p['pair'] and q is not p)
                ca, sa = math.cos(s.angle), math.sin(s.angle)
                # teleport TYLKO głowy: wąż "przelewa się" przez
                # portal — ogon znika w wejściu wraz z trimem
                s.spine[0] = (q['x'] + ca * 1.3, q['y'] + sa * 1.3)
                s.portal_cd = PORTAL_CD
                s.shield = max(s.shield, 0.6)
                break

    def _gen_cannons(self):
        """Armaty: losowe pozycje (nie w murach), kąt, zasięg, okres."""
        cans = []
        for _ in range(300):
            if len(cans) >= CANNON_COUNT:
                break
            x = self.rng.uniform(15, WORLD_W - 15)
            y = self.rng.uniform(15, WORLD_H - 15)
            if self._near_obstacle(x, y, 4.0):
                continue
            if any(dist2(x, y, c['x'], c['y']) < 25 * 25
                   for c in cans):
                continue
            cans.append({'x': x, 'y': y,
                         'angle': self.rng.uniform(0, 2 * math.pi),
                         'range': self.rng.uniform(*CANNON_RANGE),
                         'period': self.rng.uniform(*CANNON_PERIOD),
                         'next': self.rng.uniform(0.5, 3.0)})
        return cans

    def _tick_cannons(self, dt):
        """Strzały armat + ruch pocisków + trafienia w węże."""
        for c in self.cannons:
            c['next'] -= dt
            if c['next'] <= 0:
                c['next'] = c['period']
                ca, sa = math.cos(c['angle']), math.sin(c['angle'])
                self.bullets.append({
                    'x': c['x'] + ca * (CANNON_R + 0.5),
                    'y': c['y'] + sa * (CANNON_R + 0.5),
                    'dx': ca, 'dy': sa, 'left': c['range']})
        if not self.bullets:
            return
        dead = set()
        step = BULLET_SPEED * dt
        for b in self.bullets:
            b['x'] += b['dx'] * step
            b['y'] += b['dy'] * step
            b['left'] -= step
            if (b['left'] <= 0
                    or not (0 <= b['x'] < WORLD_W
                            and 0 <= b['y'] < WORLD_H)
                    or self._hit_obstacle(b['x'], b['y'])):
                b['dead'] = True
                continue
            for s in self.snakes:
                if not s.alive or s.sid in dead or s.shield > 0:
                    continue
                if dist2(b['x'], b['y'], *s.head) \
                        < (HEAD_R + BULLET_R) ** 2:
                    dead.add(s.sid)        # headshot
                    b['dead'] = True
                    break
                cut = next((i for i in range(1, len(s.spine))
                            if dist2(b['x'], b['y'], *s.spine[i])
                            < (BULLET_R + 0.5) ** 2), None)
                if cut is not None:
                    self._sever(s, cut, dead)   # przecięcie
                    b['dead'] = True
                    break
        self.bullets = [b for b in self.bullets if not b.get('dead')]
        by_sid = {s.sid: s for s in self.snakes}
        for sid in dead:
            self._kill(by_sid[sid])

    def _drop_crystal(self, cell, v):
        self.crystals.setdefault(cell, v)
        # born + jitter: kazdy krysztal wygasa w innym momencie
        self.crys_born.setdefault(
            cell, self.time + self.rng.uniform(
                -CORPSE_TTL_JIT, CORPSE_TTL_JIT))

    # --- spawn / respawn ---
    def _free_spot(self):
        # progresywny margines — lepiej ciasno niż na środku mapy
        for r in (SPAWN_CLEARANCE, 6.0, 3.0, 1.0):
            for _ in range(200):
                x = self.rng.uniform(15, WORLD_W - 15)
                y = self.rng.uniform(15, WORLD_H - 15)
                if (all(c not in self.occ
                        for c in cells_in_circle(x, y, r))
                        and not self._near_obstacle(x, y, r)):
                    return x, y
        return WORLD_W / 2, WORLD_H / 2

    def _spawn(self, sid, name, color, is_bot):
        x, y = self._free_spot()
        s = Snake(sid, name, color, x, y,
                  self.rng.uniform(0, 2 * math.pi), is_bot)
        self.snakes.append(s)
        self.occ = self._occupancy()
        return s

    def _respawn(self, s):
        x, y = self._free_spot()
        s.__init__(s.sid, s.name, s.color, x, y,
                   self.rng.uniform(0, 2 * math.pi), s.is_bot)
        self.occ = self._occupancy()

    def respawn_player(self):
        if self.player is not None and not self.player.alive:
            self._respawn(self.player)

    # --- symulacja ---
    def tick(self, dt, controller=None):
        self.time += dt
        self.tick_count += 1
        for s in self.snakes:
            if s.alive:
                if s.shield > 0:
                    s.shield -= dt
                if s.is_bot and controller \
                        and self.tick_count % BOT_THINK_DIV == s.sid % BOT_THINK_DIV:
                    controller(self, s)
                s.steer(dt)
                boosting = s.boost and s.length > BOOST_MIN_LEN
                s.advance(SPEED * (BOOST_MULT if boosting else 1.0) * dt)
                if boosting:
                    s.length -= BOOST_DRAIN * dt
                    if self.rng.random() < BOOST_DRAIN * dt * 0.5:
                        tx, ty = s.spine[-1]
                        self._drop_crystal((int(tx), int(ty)), 1)
            elif s.is_bot:
                s.respawn_in -= dt
                if s.respawn_in <= 0:
                    self._respawn(s)
        if self.cannons:
            self._tick_cannons(dt)
        if self.frogs:
            self._tick_frogs(dt)
        if self.portals:
            self._tick_portals(dt)
        self.occ = self._occupancy()
        self._collide()
        self._expire_crystals()
        self._fill_crystals()

    def _occupancy(self):
        occ = {}
        for s in self.snakes:
            if not s.alive:
                continue
            for i, (x, y) in enumerate(s.spine):
                for c in body_cells(x, y):
                    cur = occ.get(c)
                    if cur is None or i < cur[1]:
                        occ[c] = (s.sid, i)
        return occ

    def _collide(self):
        dead = set()
        by_sid = {s.sid: s for s in self.snakes}
        alive = [s for s in self.snakes if s.alive]
        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                if a.shield > 0 or b.shield > 0:
                    continue
                if dist2(*a.head, *b.head) < (HEAD_R * 2) ** 2:
                    if a.length > b.length:
                        dead.add(b.sid)
                    elif b.length > a.length:
                        dead.add(a.sid)
                    else:
                        dead.update((a.sid, b.sid))
        for s in alive:
            if s.sid in dead:
                continue
            hx, hy = s.head
            if not (0 <= hx < WORLD_W and 0 <= hy < WORLD_H):
                dead.add(s.sid)
                continue
            if s.shield > 0:
                self._eat(s)
                continue
            if self._hit_obstacle(hx, hy):
                dead.add(s.sid)
                continue
            # własne ciało = nadal śmiertelne
            if any(dist2(hx, hy, px, py) < CONTACT_D2
                   for px, py in s.spine[SELF_MARGIN + 1:]):
                dead.add(s.sid)
                continue
            # cudze ciała -> przegryzienie (ofiarę tnie, nie zabija głowy)
            for o in alive:
                if o is s or o.sid in dead or o.shield > 0:
                    continue
                cut = next((idx for idx in range(1, len(o.spine))
                            if dist2(hx, hy, *o.spine[idx]) < CONTACT_D2),
                           None)
                if cut is not None:
                    self._sever(o, cut, dead)
                    break
            self._eat(s)
        for sid in dead:
            self._kill(by_sid[sid])

    def _sever(self, o, cut, dead):
        """Odcina wężowi ogon od indeksu `cut`; resztki -> kryształki."""
        for i, (x, y) in enumerate(o.spine[cut:]):
            if i % CORPSE_EVERY == 0:
                self._drop_crystal((int(x), int(y)), CORPSE_VALUE)
        del o.spine[cut:]
        o.length = arc_len(o.spine)
        if o.length < MIN_SURVIVE_LEN:
            dead.add(o.sid)

    def _eat(self, s):
        hx, hy = s.head
        cx, cy = int(hx), int(hy)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell = (cx + dx, cy + dy)
                v = self.crystals.get(cell)
                if v and dist2(hx, hy, cell[0] + 0.5, cell[1] + 0.5) \
                        < (HEAD_R + CRYSTAL_R + 0.3) ** 2:
                    del self.crystals[cell]
                    self.crys_born.pop(cell, None)
                    s.length += v

    def _kill(self, s):
        s.alive = False
        s.boost = False
        if s.is_bot:
            s.respawn_in = RESPAWN_DELAY
        for i, (x, y) in enumerate(s.spine):
            if i % CORPSE_EVERY == 0:
                self._drop_crystal((int(x), int(y)), CORPSE_VALUE)

    def _expire_crystals(self):
        """Kryształy ze zwłok wygasają po CORPSE_TTL (co ~1 s)."""
        if self.tick_count % 30:
            return
        cut = self.time - CORPSE_TTL
        old = [c for c, v in self.crystals.items()
               if v == CORPSE_VALUE
               and self.crys_born.get(c, 0.0) < cut]
        for c in old:
            del self.crystals[c]
            self.crys_born.pop(c, None)

    def _fill_crystals(self):
        target = int(WORLD_W * WORLD_H * CRYSTAL_DENSITY)
        heads = [s.head for s in self.snakes if s.alive]
        while len(self.crystals) < target:
            c = (self.rng.randrange(int(WORLD_W)),
                 self.rng.randrange(int(WORLD_H)))
            if c in self.occ:
                continue
            # nie siej w zasięgu głów — kryształek byłby jedzony
            # w następnym ticku ("mignięcie")
            if any(dist2(c[0] + .5, c[1] + .5, hx, hy) < 16
                   for hx, hy in heads):
                continue
            self._drop_crystal(c, 1)
