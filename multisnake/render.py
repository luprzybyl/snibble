"""Rysowanie świata w curses: viewport + kamera, HUD, leaderboard."""
import curses

from .world import WORLD_H, WORLD_W

SNAKE_COLORS = [curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_MAGENTA,
                curses.COLOR_YELLOW, curses.COLOR_BLUE, curses.COLOR_RED,
                curses.COLOR_WHITE]
PAIR_CRYSTAL = 8
PAIR_BIG = 9


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    for i, col in enumerate(SNAKE_COLORS, start=1):
        curses.init_pair(i, col, -1)
    curses.init_pair(PAIR_CRYSTAL, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_BIG, curses.COLOR_RED, -1)


def _put(stdscr, y, x, ch, attr=0):
    try:
        stdscr.addch(y, x, ch, attr)
    except curses.error:
        pass


def _text(stdscr, y, x, s, attr=0):
    try:
        stdscr.addstr(y, x, s, attr)
    except curses.error:
        pass


def draw(stdscr, world):
    h, w = stdscr.getmaxyx()
    px, py = world.player.head
    cam_x = min(max(int(px - w / 2), 0), max(0, int(WORLD_W) - w))
    cam_y = min(max(int(py - h / 2), 0), max(0, int(WORLD_H) - h))

    stdscr.erase()

    for (cx, cy), v in world.crystals.items():
        sx, sy = cx - cam_x, cy - cam_y
        if 0 <= sx < w and 0 <= sy < h:
            if v > 1:
                _put(stdscr, sy, sx, '◆',
                     curses.color_pair(PAIR_BIG) | curses.A_BOLD)
            else:
                _put(stdscr, sy, sx, '◆',
                     curses.color_pair(PAIR_CRYSTAL) | curses.A_BOLD)

    sid2snake = {s.sid: s for s in world.snakes}
    for (cx, cy), (sid, idx) in world.occ.items():
        sx, sy = cx - cam_x, cy - cam_y
        if 0 <= sx < w and 0 <= sy < h:
            _put(stdscr, sy, sx, '█',
                 curses.color_pair(sid2snake[sid].color))

    for s in world.snakes:
        if not s.alive:
            continue
        sx, sy = int(s.head[0]) - cam_x, int(s.head[1]) - cam_y
        if 0 <= sx < w and 0 <= sy < h:
            _put(stdscr, sy, sx, '◉',
                 curses.color_pair(s.color) | curses.A_BOLD)

    _hud(stdscr, world, w)
    if not world.player.alive:
        _gameover(stdscr, world, h, w)
    stdscr.noutrefresh()
    curses.doupdate()


def _hud(stdscr, world, w):
    p = world.player
    info = f" LEN {p.length:.0f} " + ("BOOST " if p.boost else "")
    _text(stdscr, 0, 0, info,
          curses.A_REVERSE | (curses.color_pair(PAIR_BIG) if p.boost else 0))
    board = sorted(world.snakes, key=lambda s: -s.length)
    pos = next(i for i, s in enumerate(board) if s is p)
    lo = max(0, min(pos - 2, len(board) - 5))
    for row, i in enumerate(range(lo, min(lo + 5, len(board)))):
        s = board[i]
        mark = ">" if s is p else " "
        attr = curses.color_pair(s.color)
        if s is p:
            attr |= curses.A_BOLD
        _text(stdscr, row, w - 18,
              f"{mark}{i + 1}. {s.name[:8]:8} {s.length:5.0f}", attr)


def _gameover(stdscr, world, h, w):
    p = world.player
    msg = f" ZGINĄŁEŚ — długość {p.length:.0f} "
    hint = " [r] respawn   [Esc] wyjście "
    y = h // 2
    _text(stdscr, y, max(0, (w - len(msg)) // 2), msg,
          curses.A_REVERSE | curses.A_BOLD)
    _text(stdscr, y + 1, max(0, (w - len(hint)) // 2), hint,
          curses.A_REVERSE)
