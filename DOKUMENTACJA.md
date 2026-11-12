# MultiSnake — dokumentacja

Wielowężowa gra w stylu slither.io / Snake Clash! — bez reklam, bez
sklepu, bez sieci. Granie na jednej planszy z botami. Działa
w terminalu (curses) i jako aplikacja Kivy (desktop + Android APK).

## Zasady w skrócie

Pełne zasady: [ZASADY.md](ZASADY.md). Najważniejsze:

- Kryształki wydłużają węża; poziom = długość.
- Głowa w cudzym ciele → **przegryzasz**: odcinasz ofierze ogon
  (zamienia się w kryształki do zebrania).
- Głowa w głowę → przegrywa **krótszy** wąż; remis zabija obu.
- Własne ciało i krawędź mapy = śmierć.
- BOOST (spacja / przycisk): ×1.9 prędkości, spala długość, sypie
  kryształkami z ogona.
- Moduł **ZAMKI** (toggle w menu): murowane zamki z bramą
  na planszy — wjazd w mur zabija. Stan toggle zapamiętywany
  w `settings.json` razem z imieniem.

## Struktura projektu

```
multisnake/
├── main.py                  # wejście Kivy (+ flagi demo/autopołączenia)
├── buildozer.spec           # konfiguracja budowy APK
├── multisnake/
│   ├── world.py             # symulacja: węże, kryształki, kolizje (bez UI)
│   ├── bot.py               # AI botów (decide())
│   ├── render.py            # renderer curses
│   ├── __main__.py          # `python -m multisnake` — wersja terminalowa
│   └── kivy_app.py          # UI Kivy: menu, gra, HUD, ranking, biomy
├── ZASADY.md · PLAN.md · event_log.md
```

Separacja: `world.py`/`bot.py` nie znają ani curses, ani Kivy — ta
sama symulacja napędza terminal, desktop i Android.

## Uruchamianie

```bash
python3 -m venv .venv && .venv/bin/pip install kivy

# tryb lokalny — terminal (ncurses)
.venv/bin/python -m multisnake

# tryb lokalny — okno Kivy (menu: imię + GRAJ)
.venv/bin/python main.py

# demka autopilota bez menu
.venv/bin/python main.py --auto [--pos x,y] [--size W,H]
```

### Sterowanie (Kivy)

| Wejście | Działanie |
|---|---|
| Palec / kursor myszy | głowa podąża za punktem (kąt ciągły) |
| Strzałki / WASD | skręcanie (priorytet nad myszą) |
| BOOST (przycisk) / trzymanie | nitro |
| `+` / `-` / kółko | zoom (14–42 komórki na wysokość) |

## Android (APK)

### Budowa

```bash
pip install buildozer        # + zależności: openjdk, zlib, patch...
buildozer -v android debug   # pierwszy build ~30-60 min (SDK+NDK ~2 GB)
# → bin/multisnake-*.apk
```

`buildozer.spec`: orientacja landscape, **zero uprawnień** (gra
offline), `requirements = python3,kivy,filetype`,
`android.archs = <jeden arch>`.

### Który arch?

`android.archs` przyjmuje **jeden** arch na build (bug p4a —
patrz niżej). Aby mieć oba APK, budujesz dwa razy, przełączając:

| `android.archs` | Dla jakich urządzeń |
|---|---|
| `armeabi-v7a` | stare/32-bit tablety (np. `adb shell getprop ro.product.cpu.abilist` → `armeabi-v7a`) |
| `arm64-v8a` | współczesne telefony/tablety |

Sprawdzenie ABI urządzenia: `adb shell getprop ro.product.cpu.abilist`.
Każdy build to osobny katalog w `.buildozer` (pełna rekompilacja).

### Znane problemy builda (Arch, 2026)

- Buildozer odpalany z **systemowego** pythona (`~/.local/bin`,
  `PIP_BREAK_SYSTEM_PACKAGES=1`) — w venv nie działa, bo
  wywołuje `pip install --user`.
- Licencje SDK: `~/.buildozer/android/platform/android-sdk/licenses/
  android-sdk-license` z hashami akceptacji (sdkmanager jest za
  stary na `--licenses`).
- **JDK**: Gradle 8.14.3 nie czyta klas JDK 27 —
  `JAVA_HOME=~/.local/jdks/jdk-21.0.13+9` (Temurin 21).
- p4a: receptura `kivy` ciągnie `requests` → `charset_normalizer`
  z androidowym wheel tagiem → `python_depends = []` w
  `.buildozer/.../recipes/kivy/__init__.py` (UrlRequest nieużywany).
- p4a `python -m venv` na istniejącym venv miesza pipy — przy
  powtórkach kasować `build/venv` (jeden arch = problem znika).
- Pełna komenda rebuildu:
  ```bash
  PATH=$HOME/.local/bin:$PATH PIP_BREAK_SYSTEM_PACKAGES=1 \
    JAVA_HOME=$HOME/.local/jdks/jdk-21.0.13+9 \
    ~/.local/bin/buildozer android debug
  ```

### Instalacja na tabletach — stan po zmianach Google

Google wprowadza **developer verification**: od 30.09.2026 aplikacje
instalowane z certyfikowanych sklepów (Play, Galaxy Store, GetApps
itd.) muszą pochodzić od zweryfikowanych deweloperów — na razie
**tylko** w Brazylii, Indonezji, Singapurze i Tajlandii. Globalnie
(w tym Polska) wymóg wejdzie w **2027**.

Dziś, w Polsce, nadal działa klasyczny sideload:

1. Prześlij APK na tablet (kabel, mail, dysk, `adb push`).
2. Otwórz plik → system poprosi o zgodę „instalowanie z nieznanych
   źródeł" dla danej aplikacji-źródła → zezwól → zainstaluj.

Opcje na 2027+, gdy weryfikacja obejmie wszystko:

- **`adb install`** (rekomendowane, omija weryfikację całkowicie):
  na tablecie włącz *Opcje programisty → Debugowanie USB*,
  podłącz kablem do komputera i:
  ```bash
  adb install bin/multisnake-*.apk
  ```
  Instalacje przez ADB są wyłączone z wymogu weryfikacji i okresu
  oczekiwania.
- **Advanced sideloading flow** (dla power userów): Opcje
  programisty → instalacja niezweryfikowanych → uwierzytelnienie +
  restart + **24 h oczekiwania**, potem zgoda na 7 dni albo na stałe.
- **Konto „limited distribution"** (Android Developer Console):
  bezpłatne, bez legitymacji tożsamości, dystrybucja do **20
  urządzeń** — wymaga rejestracji u Google i podpięcia podpisu APK.
- Pełna weryfikacja dewelopera ($25 + dokument tożsamości) —
  overkill dla gry rodzinnej.

Dla „dzieci grają w domu" wystarczy dziś sideload, a jutro `adb`.
