"""AI botów: kryształki, przegryzanie krótszych, unikanie głów i ścian."""
import math

from .world import (BODY_R, CONTACT_D2, SELF_MARGIN, WORLD_H, WORLD_W,
                    ang_diff, dist2, norm_angle)

LOOK_STEPS = (2.0, 4.0, 7.0, 10.0)
CANDIDATES = (-1.4, -0.9, -0.5, -0.25, 0.0, 0.25, 0.5, 0.9, 1.4)


def decide(world, s):
    hx, hy = s.head
    rng = world.rng

    if world.crystals:
        (cx, cy), _ = min(world.crystals.items(),
                          key=lambda kv: dist2(hx, hy,
                                               kv[0][0] + .5, kv[0][1] + .5))
        tx, ty = cx + .5, cy + .5
    else:
        tx, ty = WORLD_W / 2, WORLD_H / 2

    # ofensywa: krótszy przeciwnik w pobliżu
    for o in world.snakes:
        if o is s or not o.alive:
            continue
        ox, oy = o.head
        d2 = dist2(hx, hy, ox, oy)
        if s.length > o.length and d2 < 144 and rng.random() < 0.5:
            if d2 < 36 and len(o.spine) > 1:
                # dobicie head-head: wyprzedź jego trasę
                tx = ox + math.cos(o.angle) * 3
                ty = oy + math.sin(o.angle) * 3
            elif len(o.spine) > 4:
                # przegryzienie: celuj w jego ciało
                tx, ty = o.spine[len(o.spine) // 3]
            break

    enemies = [o for o in world.snakes if o is not s and o.alive]
    own_tail = s.spine[SELF_MARGIN + 1:]
    base = math.atan2(ty - hy, tx - hx)
    best_a, best_score = s.angle, -1e18
    for da in CANDIDATES:
        a = norm_angle(s.angle + da)
        ca, sa = math.cos(a), math.sin(a)
        score = 20.0 - abs(ang_diff(a, base)) * 15.0 + rng.uniform(0, 2)
        for step in LOOK_STEPS:
            px, py = hx + ca * step, hy + sa * step
            if not (BODY_R < px < WORLD_W - BODY_R
                    and BODY_R < py < WORLD_H - BODY_R):
                score -= 60.0 / step
                break
            if world._hit_obstacle(px, py):
                score -= 60.0 / step
                break
            if any(dist2(px, py, b['x'], b['y']) < 16.0
                   for b in world.bullets):
                score -= 40.0 / step
                break
            if any(dist2(px, py, qx, qy) < CONTACT_D2
                   for qx, qy in own_tail):
                score -= 50.0 / step
                break
            head_risk = False
            for o in enemies:
                ed = dist2(px, py, *o.head)
                if ed < 25:
                    if o.length >= s.length * 0.9:
                        score -= 60.0 / (ed + 1)
                        head_risk = True
                    else:
                        score += 8.0   # krótszy przy głowie = łup
            if head_risk:
                break
        if score > best_score:
            best_score, best_a = score, a

    s.target_angle = best_a
    s.boost = best_score > 15 and dist2(hx, hy, tx, ty) > 400 \
        and rng.random() < 0.5
