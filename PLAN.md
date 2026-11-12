# Plan MultiSnake

## Faza 1 — terminal (curses)  ← TERAZ
- `multisnake/world.py` — symulacja: model ciągły (float, kąt + prędkość
  skrętu), kolizje rasteryzowane na siatkę, kryształki, boost, respawn.
- `multisnake/bot.py` — AI botów (seek/avoid/agresja).
- `multisnake/render.py` + `__main__.py` — curses: viewport+kamera,
  leaderboard, game over, 8-kierunkowa kwantyzacja klawiatury.
- **Kryterium akceptacji**: użytkownik gra i jest zadowolony.

## Faza 2 — Android (Kivy + Buildozer)  ← W TRAKCIE
- [x] `multisnake/kivy_app.py` — front: komiksowa grafika (obrysy,
  pastele, oczki na głowach), sterowanie palcem = kąt ciągły,
  menu z imieniem, BOOST button, game over + "JESZCZE RAZ".
- [x] `main.py` + `buildozer.spec` — szkielet APK.
- [x] Test na żywym Wayland: appka startuje, tickuje, renderuje.
- [x] `pip install buildozer` + `buildozer android debug` —
  `bin/multisnake-0.1-arm64-v8a-debug.apk` (~20 MB, arm64, INTERNET).
- [x] Sideload APK dzieciom (`adb install`) — armeabi-v7a dziala na tablecie.

## Faza 3 — multiplayer ← WYCOFANY po testach (Wi-Fi + Family Link + opóźnienia); gra jest offline-only.
