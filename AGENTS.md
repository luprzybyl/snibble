# AGENTS.md — working notes for agent sessions

## Layout

- `main.py` — Kivy entry point (+ `--auto` autopilot demo flags)
- `snibble/world.py` — pure simulation: snakes, crystals, collisions,
  cannons, frogs, portals. No UI dependencies.
- `snibble/bot.py` — bot AI (`decide()`)
- `snibble/kivy_app.py` — Kivy front: menu, game, HUD, pictogram icons
  (`IconWidget`), modules toggles
- `snibble/render.py` + `snibble/__main__.py` — curses front
- `build_apk.sh` — builds both ABIs (sed-switches `android.archs`,
  restores spec via trap)
- `recipes/kivy/` — vendored p4a recipe, see "build traps" below

`world.py`/`bot.py` know nothing about curses or Kivy — same simulation
drives terminal, desktop and Android.

## Local build environment (Arch)

```bash
PATH=$HOME/.local/bin:$PATH PIP_BREAK_SYSTEM_PACKAGES=1 \
  JAVA_HOME=$HOME/.local/jdks/jdk-21.0.13+9 \
  ~/.local/bin/buildozer android debug
```

- Buildozer runs from **system** python, not `.venv` — it calls
  `pip install --user` internally.
- Gradle 8.14.x can't read JDK 27 classes → pin `JAVA_HOME` to JDK 21.
- `android.archs` takes ONE arch per build (`armeabi-v7a` or
  `arm64-v8a`). Each arch = full recompile in its own `.buildozer` dir.
- If a rebuild fails in `python -m venv` on an existing venv — delete
  `build/venv` and retry.

## CI (`.github/workflows/build.yml`)

- Matrix `armeabi-v7a` + `arm64-v8a` on `ubuntu-latest`, then a
  `release` job → `v<version>-b<run_number>` with both APKs.
- Buildozer toolchain cached under key `buildozer-<arch>-<hash(spec, recipes)>`.
- Release job needs `permissions: contents: write` (default token is
  read-only → 403 otherwise).
- Required apt deps include `libltdl-dev` — without it, `autoreconf` in
  the libffi/openssl recipes dies on `LT_SYS_SYMBOL_USCORE`.

## Build traps already discovered (do not rediscover)

- **`p4a.local_recipes` must live in the `[app]` section** of
  `buildozer.spec`. In `[buildozer]` it is silently ignored — p4a then
  uses upstream recipes.
- Vendored `recipes/kivy` sets `python_depends = ['filetype']`.
  Upstream pulls `requests` → `charset_normalizer`, whose Android wheel
  tag makes pip fail with "not a supported wheel on this platform".
- Kivy `Ellipse` defaults to `size=(100,100)` — in world units that's a
  giant disk. Always construct with explicit `pos=`/`size=`. A stray
  100×100 ellipse was once a mysterious pale disk covering a third of
  the map (pooled cannon projectiles).
- **World Y axis is inverted in the renderer** (`Scale.y = -cell`):
  larger world `y` renders lower on screen. Any asymmetric sprite
  (frogs got eyes/legs upside down once) must offset accordingly.
- Debug: press `g` during a game → dumps all `_wl` canvas instructions
  with bounding boxes to `/tmp/wl_dump.txt` + screenshot
  `/tmp/wl_shot*.png`.

## Gameplay constants worth knowing

- Snake: continuous model (float pos, angle, turn rate ~4.5 rad/s,
  speed ~10 cells/s, boost ~1.9x, min boost length ~5)
- Food values: crystal +1, corpse crystal +2, frog +5, rainbow +30
- Bite-through: victim's tail severed at contact → crystals; attacker
  unharmed; victim dies if < ~4 cells left.
- Portal wormhole: head teleports, `_trim` consumes old tail points —
  renderer splits polylines at >4×`SEG_DIST` gaps. Cooldown vs ping-pong.
- Cannons: random angle, range-limited projectiles; pool of 48 Kivy
  ellipses.
- Settings/toggles persist in `settings.json`.

## Conventions

- UI text: almost none by design — pictograms via `IconWidget`
  primitives (no emoji; Android fonts are unreliable). Keep `MENU`
  and the name input as text.
- Offline only: no network permission in `buildozer.spec`.
- Commit after each working change; push to `master` triggers CI build
  + release automatically.
