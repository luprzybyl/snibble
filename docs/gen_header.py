#!/usr/bin/env python3
"""Snibble header: letters drawn as game-style snakes -> SVG + PNG."""
import math, random
from PIL import Image, ImageDraw

# ---- snake palette (game colors, pastel comic) ----
SNAKES = [
    ((0.25, 0.85, 0.95), (0.10, 0.42, 0.50)),   # cyan (player)
    ((0.95, 0.60, 0.20), (0.48, 0.28, 0.08)),   # orange
    ((0.70, 0.50, 0.95), (0.35, 0.22, 0.50)),   # purple
    ((0.95, 0.35, 0.40), (0.50, 0.15, 0.18)),   # red
    ((0.95, 0.80, 0.25), (0.48, 0.38, 0.10)),   # yellow
    ((0.45, 0.85, 0.45), (0.20, 0.45, 0.20)),   # green
    ((0.95, 0.55, 0.75), (0.50, 0.25, 0.38)),   # pink
]
BG = (0.55, 0.80, 0.45)          # meadow
EYE_W, EYE_P = (1, 1, 1), (0.08, 0.10, 0.12)

# ---- letter paths, grid units (x right, y down); head = LAST point ----
LETTERS = {
    'S': [(4,0),(1.6,0.15),(0.15,1.0),(0.1,2.7),(2.0,3.4),(3.8,4.1),(3.9,5.8),(2.4,6.9),(0.2,6.7)],
    'N': [(4,0),(4,7),(0,0),(0,7)],               # reversed: head bottom-left
    'I': [(0.7,0),(3.3,0),(2,0),(2,7),(3.3,7),(0.7,7)],
    'B': [(0,0.15),(0,7),(2.4,7),(3.6,6.1),(3.6,4.4),(2.7,3.6),(3.5,2.9),(3.5,1.0),(2.4,0.15),(0,0.15)],
    'L': [(0,0),(0,7),(4,7)],
    'E': [(4,0),(0,0),(0,3.5),(3,3.5),(0,3.5),(0,7),(4,7)],
}
WORD = "SNIBBLE"
CELL = 5.0          # letter width + gap in units
SCALE = 46          # px per unit
BODY = 1.05         # body diameter (units) — like game ~0.9-1.05
PAD = 1.6

def wig(pts, seed, amp=0.05):
    """Mild organic wiggle at corner points only."""
    rng = random.Random(seed)
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        out.append((x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)))
    out.append(pts[-1])
    return out

def catmull(pts, n=14):
    """Smooth curve through points (centripetal Catmull-Rom)."""
    if len(pts) < 3:
        return pts
    p = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(p) - 3):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out

def sc(pts):
    return [((x + PAD) * SCALE, (y + PAD) * SCALE) for x, y in pts]

def build():
    shapes = []   # (pts_px, fill, outline, head_dir)
    for i, ch in enumerate(WORD):
        base = [(x + i * CELL, y) for x, y in LETTERS[ch]]
        path = catmull(wig(base, seed=i * 77 + 5))
        fill, out = SNAKES[i % len(SNAKES)]
        (x1, y1), (x2, y2) = path[-2], path[-1]
        shapes.append((sc(path), fill, out, (x2 - x1, y2 - y1)))
    W = int((len(WORD) * CELL + 1.0 + 2 * PAD) * SCALE)
    H = int((7 + 2 * PAD) * SCALE)
    return shapes, W, H

def rgb(c): return tuple(int(v * 255) for v in c)

def render_png(shapes, W, H, fname, ss=3):
    img = Image.new('RGB', (W * ss, H * ss), rgb(BG))
    d = ImageDraw.Draw(img)
    bw = BODY * SCALE * ss / 2
    border = 0.16 * SCALE * ss
    # crystals
    rng = random.Random(9)
    for _ in range(14):
        cx, cy = rng.uniform(0.05, 0.95) * W * ss, rng.uniform(0.05, 0.95) * H * ss
        r = rng.uniform(0.13, 0.22) * SCALE * ss
        col = rng.choice([(1.0, 0.85, 0.3), (1.0, 0.5, 0.7), (0.6, 0.9, 1.0)])
        d.polygon([(cx, cy - r), (cx + r * .7, cy), (cx, cy + r), (cx - r * .7, cy)],
                  fill=rgb(col), outline=rgb(tuple(v * .5 for v in col)))
    for pts, fill, out, hd in shapes:
        p = [(x * ss, y * ss) for x, y in pts]
        d.line(p, fill=rgb(out), width=int(bw * 2 + border * 2), joint='curve')
        d.line(p, fill=rgb(fill), width=int(bw * 2), joint='curve')
        hx, hy = p[-1]
        L = math.hypot(*hd) or 1
        ux, uy = hd[0] / L, hd[1] / L
        hr = bw * 1.12
        d.ellipse([hx - hr - border * .7, hy - hr - border * .7,
                   hx + hr + border * .7, hy + hr + border * .7],
                  fill=rgb(fill), outline=rgb(out), width=int(border * .8))
        base = math.atan2(uy, ux)
        for s in (-0.85, 0.85):
            a = base + s
            ex, ey = hx + math.cos(a) * hr * 0.55, hy + math.sin(a) * hr * 0.55
            er = hr * 0.42
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=rgb(EYE_W),
                      outline=rgb(out), width=int(border * .5))
            pr = er * 0.45
            px_, py_ = ex + math.cos(base) * er * 0.35, ey + math.sin(base) * er * 0.35
            d.ellipse([px_ - pr, py_ - pr, px_ + pr, py_ + pr], fill=rgb(EYE_P))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(fname)

def render_svg(shapes, W, H, fname):
    bw = BODY * SCALE
    border = 0.16 * SCALE
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{rgb_hex(BG)}"/>']
    rng = random.Random(9)
    for _ in range(14):
        cx, cy = rng.uniform(0.05, 0.95) * W, rng.uniform(0.05, 0.95) * H
        r = rng.uniform(0.13, 0.22) * SCALE
        col = rng.choice([(1.0, 0.85, 0.3), (1.0, 0.5, 0.7), (0.6, 0.9, 1.0)])
        s.append(f'<polygon points="{cx},{cy-r} {cx+r*.7},{cy} {cx},{cy+r} {cx-r*.7},{cy}" '
                 f'fill="{rgb_hex(col)}" stroke="{rgb_hex(tuple(v*.5 for v in col))}" stroke-width="2"/>')
    for pts, fill, out, hd in shapes:
        path = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        s.append(f'<path d="{path}" fill="none" stroke="{rgb_hex(out)}" '
                 f'stroke-width="{bw + 2 * border:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        s.append(f'<path d="{path}" fill="none" stroke="{rgb_hex(fill)}" '
                 f'stroke-width="{bw:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        hx, hy = pts[-1]
        L = math.hypot(*hd) or 1
        ux, uy = hd[0] / L, hd[1] / L
        hr = bw * 0.56
        base = math.atan2(uy, ux)
        s.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{hr:.1f}" fill="{rgb_hex(fill)}" '
                 f'stroke="{rgb_hex(out)}" stroke-width="{border:.1f}"/>')
        for sg in (-0.85, 0.85):
            a = base + sg
            ex, ey = hx + math.cos(a) * hr * 0.55, hy + math.sin(a) * hr * 0.55
            er = hr * 0.42
            px_, py_ = ex + math.cos(base) * er * 0.35, ey + math.sin(base) * er * 0.35
            s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{er:.1f}" fill="white" '
                     f'stroke="{rgb_hex(out)}" stroke-width="{border * .5:.1f}"/>')
            s.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="{er * .45:.1f}" fill="{rgb_hex(EYE_P)}"/>')
    s.append('</svg>')
    open(fname, 'w').write('\n'.join(s))

def rgb_hex(c): return '#%02x%02x%02x' % tuple(int(v * 255) for v in c)

if __name__ == '__main__':
    shapes, W, H = build()
    render_png(shapes, W, H, '/tmp/snibble_header.png')
    render_svg(shapes, W, H, '/tmp/snibble_header.svg')
    print(f'{W}x{H}')
