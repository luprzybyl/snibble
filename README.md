# Snibble

A slither.io / Snake Clash-style game for kids — **no ads, no shop, no
network, no retention mechanics**. Play for five minutes, put it down,
come back later. That was the design goal.

One board, many snakes: you + AI bots. Eat crystals, grow, bite other
snakes in half. Runs in a terminal (curses) and as a Kivy app
(desktop + Android APK).

## Rules in short

- Crystals grow your snake. Your level = your length.
- Head into another snake's body → **you bite through**: their tail is
  cut off and turns into crystals you can collect.
- Head-to-head → the **shorter** snake dies; equal length kills both.
- Your own body and the map edge (brick wall) = death.
- BOOST (space / button): ~2x speed, burns length, drops crystals
  behind your tail.
- Dead snakes turn into crystals laid along their body. Bots respawn.

## Optional modules (toggles in menu)

- **Castles** — walled forts with a gate; walls kill. Deep inside waits
  a **rainbow crystal +30**.
- **Cannons** — fire projectiles at random angles; a hit can sever a snake.
- **Frogs** — jumping prey worth **+5**, hard to catch.
- **Portals** — color-coded wormhole pairs: head goes in one side, comes
  out the other while the tail keeps streaming through.

All toggles persist in `settings.json` together with the player name.
UI is pictograms only — nothing to translate.

## Run it

```bash
python3 -m venv .venv python3 -m venv .venv && .venv/bin/pip install kivypython3 -m venv .venv && .venv/bin/pip install kivy .venv/bin/pip install -r requirements.txt

# Kivy app (menu → name → play)
.venv/bin/python main.py

# terminal version (curses)
.venv/bin/python -m snibble
```

### Controls

| Input | Action |
|---|---|
| finger / mouse cursor | head steers toward the point (continuous angle) |
| arrows / WASD | steering (overrides mouse) |
| space / BOOST button | nitro |
| `+` / `-` / wheel | camera zoom |
| `p` | pause |
| Esc / MENU button | back to menu |

## Android APK

Prebuilt debug APKs (arm64-v8a + armeabi-v7a) are attached to every
GitHub release — CI builds both on each push to `master`. Check a
device's ABI with `adb shell getprop ro.product.cpu.abilist`.

Install via sideload (enable "install from unknown sources") or, best,
over USB:

```bash
adb install bin/snibble-*-debug.apk
```

To build locally (Linux, needs Android SDK + JDK 21 + buildozer):

```bash
./build_apk.sh              # both architectures
./build_apk.sh arm64-v8a    # one architecture
```

No network permission is requested — the game is fully offline.
