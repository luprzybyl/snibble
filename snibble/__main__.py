"""Pętla gry: input (8-kierunkowa kwantyzacja) -> world.tick -> render."""
import curses
import time

from .bot import decide
from .render import draw, init_colors
from .world import ANGLE8, World

KEYMAP = {
    curses.KEY_UP: "N", ord('w'): "N", ord('k'): "N",
    curses.KEY_DOWN: "S", ord('s'): "S", ord('j'): "S",
    curses.KEY_LEFT: "W", ord('a'): "W", ord('h'): "W",
    curses.KEY_RIGHT: "E", ord('d'): "E", ord('l'): "E",
    ord('q'): "NW", ord('e'): "NE", ord('z'): "SW", ord('c'): "SE",
    ord('y'): "NW", ord('u'): "NE", ord('b'): "SW", ord('n'): "SE",
    curses.KEY_A1: "SW", curses.KEY_A3: "SE",
    curses.KEY_C1: "NW", curses.KEY_C3: "NE",
}


def main(stdscr, player_name):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)
    init_colors()
    world = World(player_name=player_name)
    paused = False
    boost_until = 0.0
    last = time.monotonic()
    while True:
        now = time.monotonic()
        dt = min(now - last, 0.05)
        last = now
        while True:
            ch = stdscr.getch()
            if ch == -1:
                break
            if ch == 27:
                return
            if ch == ord(' '):
                boost_until = now + 0.35
            elif ch in (ord('p'), ord('P')):
                paused = not paused
            elif ch in (ord('r'), ord('R')) and not world.player.alive:
                world.respawn_player()
            elif ch in KEYMAP:
                world.player.target_angle = ANGLE8[KEYMAP[ch]]
        world.player.boost = now < boost_until
        if not paused:
            world.tick(dt, decide)
        draw(stdscr, world)
        time.sleep(0.016)


def run():
    try:
        name = input("Imię węża [Ty]: ").strip() or "Ty"
    except EOFError:
        name = "Ty"
    curses.wrapper(main, name)


if __name__ == "__main__":
    run()
