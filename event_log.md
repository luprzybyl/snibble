# Event log — historia decyzji

## 2026-11-11
- Ustalono projekt: slither.io-like w konsoli, "multi" = wiele wężów
  (gracz + boty), NIE gra sieciowa.
- Utworzono `ZASADY.md`: świat 300×300 > ekran, kamera za graczem,
  śmiertelne krawędzie, boost za długość, head-head: krótszy przegrywa.
- Doprecyzowano zasadę "przecięcia": umiera ten, kto trafi głową;
  ciało jest bronią.
- Terminologia: jedzenie = "kryształki" (jak w Snake Clash!).
- Istniejące terminalowe węże (terminal-slither itd.) = klasyczny
  samotnik; nisza slither.io-w-terminalu wolna.
- Wybrano stack: **Python + curses (stdlib)** po rozważeniu C/C++/Go.
- Wymagania dodane: plansza > terminal (kamera), **8 kierunków**,
  wąż grubszy (grubość ~2 komórki).
- Cel docelowy ujawniony: **gra dla dzieci na Androida, bez reklam**.
  Wybrano **Kivy + Buildozer** (APK sideload, bez Google Play).
- Decyzja architektoniczna: **model ciągły** (pozycje float, kąt +
  ograniczona prędkość skrętu) zamiast siatki 8-kierunkowej — umożliwi
  reużycie `world.py`/`bot.py` 1:1 pod Kivy. Klawiatura w terminalu
  kwantyzuje input do 8 kierunków.
- Ustalono workflow: implementacja fazy 1 (curses) → akceptacja
  użytkownika → faza 2 (Kivy). Log zmian w `event_log.md`.
- Implementacja: `multisnake/{world,bot,render,__main__}.py` + `.venv`.
- Smoke test headless: 3600 ticków (60 s sim) OK, ~3.6 ms/tick.
  Boty rosną/ giną/ respawnują. Test curses na PTY: działa.
- Faza 1 gotowa do recenzji przez użytkownika. Faza 2 (Kivy) czeka
  na zielone światło.
- Bug #1 (z recenzji): przecięcie nie zabijało — rasteryzowana głowa
  maskowała w `occ` obce ciało pod sobą. Fix: kolizje na odległościach
  głowa↔punkty kręgosłupa (`CONTACT_D2=1.3²`), `occ` tylko dla renderu/AI.
- Bug #2 (z recenzji): węże rozmyte — ciało z koła r=0.9 zmienione
  na jednolity blok 2×2 na punkt (`body_cells`). Ostra wstęga.
- Testy: głowa→ciało = śmierć, mijanie z boku = życie, head-head
  krótszy przegrywa. Perf: 2.54 ms/tick (było 3.57).
- ZMIANA ZASAD (decyzja użytkownika): mechanika "przegryzania" zamiast
  śmierci od ciała + poziom = długość:
  * głowa w cudze ciało -> odcięcie ogona ofiary -> kryształki,
    ofiara żyje krótsza (< 4 komórek = śmierć), gryzący bez kary;
  * głowa w głowę -> mniejszy poziom zamienia się w kryształki;
  * własne ciało nadal śmiertelne; ściany nadal śmiertelne.
- `world.py`: +`_sever`, `arc_len`, `MIN_SURVIVE_LEN`; `_collide` przepisane.
- `bot.py`: przepisane AI — ciała to okazja (gryzienie), groźne tylko
  głowy dłuższych + własny ogon + ściany; ofensywa na krótszych.
- Testy: przegryzienie w połowie (ofiara 24->7.8, ogon->kryształki),
  gryzienie za głową = śmierć, head-head wg poziomu, self-collision
  przy przecięciu własnego śladu. Perf 4.34 ms/tick.
- Polish (recenzja #2): węże cieńsze — `body_cells` = 1 komórka
  (ciągła 8-spójna wstęga); kryształki większe — `◆` zamiast `·`
  (małe żółte, duże czerwone).
- Prompt o imię gracza przed startem curses (`input()`), fallback "Ty";
  `World(player_name=)`; wiersz gracza w leaderboardzie pogrubiony.
- Leaderboard: zamiast top-5 pokazuje kontekst gracza (pozycja + 2 wyżej
  + 2 niżej, okno 5 wierszy przesuwa się przy skrajach).
- FAZA 2 START (zielone światło): wersja na Androida.
- `kivy` 2.3.2 w .venv. Nowy front `multisnake/kivy_app.py`:
  komiksowa grafika (Line cap/joint round + obrysy, romby-kryształki,
  oczki na głowach, pastelowy bg z kropkami), sterowanie palcem
  (touch -> atan2 -> target_angle, pełny kąt), BOOST button,
  menu z imieniem, ekran KONIEC + JESZCZE RAZ.
- `main.py` (entry APK) + `buildozer.spec` (landscape, fullscreen,
  requirements=python3,kivy).
- Fix: UnboundLocalError cell/cx/cy w `_update` (cam liczone warunkowo).
- Test: appka uruchomiona na Wayland 8 s, tickuje bez wyjątków.
- Pozostało: `pip install buildozer`, `buildozer android debug`
  (~2 GB toolchain, pierwszy build długi), sideload.
- Bug "promienie": prawdopodobnie zdegenerowane segmenty w `Line`
  (joint='round') — punkty kręgosłupa filtruje dedupe >0.14 komórki.
- Zoom: `view_cells` per-instancja (14..42), przyciski +/− (mobile)
  i kółko myszy scrollup/scrolldown (desktop).
- Bug "żółte stożki z rogu": winowajca = `Mesh` w `_diamond` — domyślny
  fmt wierzchołków Kivy ≠ gołe pozycje, indeksy wskazywały śmieci.
  Kryształek teraz = `Rectangle` obrócony o 45°. (Dedupe punktów
  zostaje jako prewencja.)
- Bug "brak HUD/modala": `GameWidget` był `Widget` → `pos_hint` ignorowane,
  wszystkie kontrolki w rogu (0,0). Fix: `GameWidget(FloatLayout)`.
- Game over modal: KONIEC! + wynik + JESZCZE RAZ + MENU (powrót
  do ekranu imienia); HUD pokazuje LEN + POZ (level=int len);
  guard `self.parent` w `_update` po wyjściu do menu.
- Bug "mignięcie kryształka": `_fill_crystals` siał w zasięgu głów →
  insta-zjedzenie w następnym ticku. Fix: min. 4 komórki od głów.
- Bug "brak rankingu/kontrolek": `self.canvas.clear()` czyściło też
  canvasy dzieci — cała warstwa UI niewidoczna. Rysowanie świata
  przeniesione do `canvas.before`; `_head` rysuje w tym samym bloku.
- Sterowanie myszą: `Window.bind(mouse_pos=...)` — głowa podąża za
  kursorem bez klikania (hover). Dotyk bez zmian. Unbind przy
  zdjęciu widgetu.
- Imiona nad głowami wężów: `Label` per wąż w `name_labels` (sid),
  pozycja nad głową co frame, usuwane przy śmierci.
- Biomy (losowe per gra): łąka / pustynia / las / kosmos — tło,
  dekoracje deterministyczne per komórka (hash + jitter),
  kolor tekstu i obwódka świata dopasowane. `THEMES`.
- Start gry: maksymalne oddalenie (`view_cells = ZOOM_MAX = 42`).
- Klawiatura (desktop): strzałki/WASD skręcają `target_angle`
  (~6 rad/s) w stronę trzymanego kierunku; kombinacje = skoski.
  Klawiatura nadpisuje mysz, póki trzymana. `keys_held` + unbind.
- Biomy zróżnicowane typami dekoracji (`kind` + `_decor`):
  łąka=kwiatki (płatki+środek, 4 kolory), pustynia=kamyczki-romby,
  las=krzaki (3 koła), kosmos=gwiazdki (punkty + rzadkie romby).

## Multiplayer — serwer + klient ws (faza 3, wdrożona)
- `world.py`: `player_name=None` (tryb serwera bez gracza lokalnego),
  `add_snake()`/`remove_snake()` (sidy zdalnych od 100, rozpad na
  kryształki), `snapshot()` — kompaktowy stan (spine co 2. punkt).
- `multisnake/server.py`: asyncio + websockets, tick 30 Hz,
  broadcast snapshotów ~10 Hz. Hasło per serwer (`--password`);
  join/input/respawn. Autorytatywna symulacja + boty na pokładzie.
- `multisnake/net.py`: `NetClient` (join z hasłem, recv w wątku,
  input throttled 20 Hz) + `RemoteWorld` — interpolacja między
  snapshotami (bufor 120 ms), interfejs zgodny z World.
- `kivy_app.py`: GameWidget w trybie remote (net=) — sterowanie
  wysyła input zamiast ruszać lokalnym światem; menu z polami
  adres/port/hasło + przycisk GRAJ ONLINE.
- `buildozer.spec`: +websockets w requirements.
- Test e2e: serwer + 2 klientów — hasło odrzuca, snapshoty płyną,
  input steruje wężem, wzajemna widoczność działa.
- Fix: crash przy 1. snapshocie (krotka zamiast dict); snapshot niesie
  `is_bot`; `--bots N` w server.py (dosiewa >9 z suffiksami imion).

## Demo multiplayer + dokumentacja
- `main.py`: flagi `--host/--port/--password/--name` (autopołączenie
  bez menu), `--auto` (autopilot), `--pos/--size` (okno); argv czyszczone
  przed parserem Kivy.
- `kivy_app.py`: `GameWidget(auto=)` — autopilot demo (kryształ +
  odpychanie od ciał/ścian); `MultiSnakeApp.autostart`.
- Fix: `p.boost` ustawiane tylko lokalnie (RemoteSnake ma __slots__).
- Demo: serwer + 3 okna z autopilotami + obserwator leaderboardu.
- `DOKUMENTACJA.md`: architektura, sterowanie, serwer, budowa APK
  i instalacja na Androidzie po zmianach Google (developer
  verification 2026→2027; adb install jako obejście).

## APK zbudowane (faza 2 domknięta)
- `bin/multisnake-0.1-arm64-v8a-debug.apk` (~20 MB).
- Problemy i fixy builda:
  - buildozer z venv: `pip --user` zakazany -> buildozer na user-site
    systemowego pythona + `PIP_BREAK_SYSTEM_PACKAGES=1`.
  - sdkmanager: ręcznie utworzone `licenses/android-sdk-license`.
  - kivy recipe ciągnie `requests`->`charset_normalizer` z wheel
    `android_24_*` -> patch `python_depends = []` w p4a recipes/kivy.
  - p4a `python -m venv` na istniejącym venv miesza pip 25.3/26.3
    (ImportError capture_logging) -> kasować `build/venv` lub jeden
    arch. `android.archs = arm64-v8a` rozwiązało.
  - Gradle 8.14.3 vs JDK 27 (major 71) -> `JAVA_HOME=` JDK21
    (Temurin w ~/.local/jdks).
- Fix: android.permissions=INTERNET w spec (multiplayer w APK)
- Fix runtime APK: `ModuleNotFoundError: filetype` (kivy/core/image)
  -> `python_depends = ['filetype']` w recepurze kivy; `android.archs
  = armeabi-v7a` (tablet 32-bit). Rebuilt OK.
- APK na tablecie DZIALA: `filetype` dodany do `requirements` w
  buildozer.spec (pewna instalacja pip, nie tylko receptura).
  Instalacja OK na Samsung 32-bit (armeabi-v7a).
- Perf na slabych tabletach: renderer przepisany na trwale
  instrukcje (Mesh-buckety per kolor dla dekoracji/krysztalow,
  per-sid InstructionGroup dla wezy, Line joint='bevel'),
  30 FPS, HUD update tylko przy zmianie tekstu.
- Zapamietywanie pol polaczenia: settings.json w user_data_dir
  (imię+host+port+hasło, zapis po udanym connect).
- Fix sieci: ufw DROP na hoście blokował TCP -> `ufw allow 8765/tcp`.
- Net perf: adaptacyjny bufor interpolacji (EMA interwału snapów,
  deque 16), spine mutowane in-place, kryształy co 3. snapshot
  (~1/3 payloadu). Fix: modal respawnu nie znikał w trybie remote
  (flaga _respawning do czasu snapshotu z alive=True).
- TTL krysztalow ze zwlok: CORPSE_TTL=30s, born-time w _crys_born,
  _expire_crystals co ~1s w ticku (single + MP przez wspolny World).
- Fix: dotyk na BOOST/zoom nie kradnie sterowania (_ui_touches uid,
  hover nad przyciskami nie zmienia kierunku).
- Playout po zegarze serwera (tick/30) zamiast czasu przybycia paczki:
  Wi-Fi burst nie wywala alpha poza [0,1] (puff) i nie miesza stanow
  (tyl-przod). Zegar _rt płynie realtime, catch-up 1.3x po burscie.
- SPAWN_SHIELD=1.5s: waz-duch po spawnie/respawnie, zero kolizji
  (fix: puff-boty = spawn-kille); _free_spot progresywny 9/6/3/1.
- SNAP_EVERY=2 (15 Hz), bufor 24, dead-reckoning do 0.4s przy
  pustym buforze (ogon podciagany za glowa).
- Render v2: geometria w koordynatach swiata pod jedna macierza
  Translate+Scale (klatka = 4 floaty); dekoracje pieczone raz;
  krysztaly rebuild tylko przy zmianie fingerprintu.
- APK arm64-v8a zbudowane osobno (drugi tablet 64-bit); spec
  przelaczany per-arch, disty w cache -> szybkie repakietowanie.
  Uwaga: p4a build/venv na v7a byl skorumpowany (pip capture_logging)
  -> build na osobnym katalogu per arch dziala.
- WYCOFANY multiplayer po testach: skasowane server.py/net.py,
  sekcja online w menu, snapshot()/add_snake()/remove_snake()
  z world.py, flagi --host/--port/--password z main.py.
  requirements bez websockets, permissions puste (gra offline,
  zero uprawnien). _respawning/RemoteWorld/dead-reckoning out.
- Krysztaly ze zwlok: CORPSE_TTL 30->15s + jitter +-4s per krysztal
  (born przesuniety losowo -> wygasaja rozlozone w ~8s oknie).
- Granice planszy: murowany mur zamiast cienkiej linii — pas zaprawy
  + 2 przesuniete rzedu cegiel (obrys+fill), pieczony raz jak dekoracje.
- Klawiatura: spacja = BOOST (jak przycisk).
- Uwaga: Window.screenshot() na tym kompie daje pasy/artefakty GL
  (czysta apka Kivy tez) — nie diagnozowac rendererem przez screeny.
- Modul ZAMKI: world(castles=True) -> obstacles = ~5 zamkow
  (pierscien murow 10x10, brama 4 na losowej stronie, 25 rectow).
  Wjazd w mur = smierc (po shieldzie). _free_spot omija mury,
  boty unikaja w lookahead. Bake: _brick_fill kafelkuje kazdy
  rect (obwod + zamki). Menu: framework MODULES + CheckBox,
  mods trzymane w settings.json.
- Zamki wieksze: SIZE 18, wieze 3.0, keep 2.2, brama 4.0 (~2.5
  grubosci weza), korytarz dziedzinca ~4.9 -> da sie objechac keep.
- Teczowy krysztal +30 (RAINBOW_VALUE): po 1 w glebi kazdego zamku
  (srodek korytarza naprzeciw bramy). Nie wygasa (expire tylko
  v==CORPSE_VALUE). Render: bialy obrys + 3 chromatyczne romby.
  Uwaga: obstacles generowane PO self.crystals (kolejnosc w __init__).
- Modul ARMATY (toggle 'cannons', 6 szt.): losowy kat/zasieg/okres
  strzalu (2.5-4.5 s). Wiezyczka = przeszkoda (wjazd = smierc).
  Pociski 15 kom/s: headshot zabija, traf w cialo = przeciecie,
  shield przechodzi, znikaja na murach/koncu zasiegu.
  Boty unikaja pociskow w lookahead. Render: zelazna wieza + lufa
  (pieczone), pociski = pool 24 Ellipse. Menu: jasny tekst toggle'y.
- Bug: blady dysk ~100 komórek na planszy (przykrywal krysztaly,
  mury; weze widac). Przyczyna: Kivy Ellipse domyslnie size=100x100
  w jedn. swiata — pool armat i glowy wezy tworzone bez size=.
  Fix: Ellipse(pos=(0,0), size=(0,0)) przy tworzeniu — nigdy nie
  wyrenderuja sie jako olbrzym. + debug 'g' = dump _wl do /tmp.
- Modul ZABY (toggle 'frogs', 8 szt.): skoki co 0.8-2.2 s na 3-7
  komorek (lądowiska bez przeszkod). Zjedzenie +5 (także w locie),
  natychmiastowy respawn. Boty gonia żabe gdy bliższa niz ~1.5x
  krysztal. Render: pool 12 grup elips (cialo+oczy+zrenice).
- Debug: klawisz 'g' dumpuje _wl do /tmp/wl_dump.txt + screenshot.
- Modul PORTALE (toggle 'portals', 3 pary kolorowane): wjazd =
  teleport calego kregoslupa do partnera (+1.3 po kierunku jazdy).
  Cooldown 1.2 s + shield 0.6 s na wyjsciu. Boty uzywaja mimochodem.
- Portale: teleport tylko GLOWY (nie calego kregoslupa) — ogon
  stopniowo znika w wejsciu, glowa rosnie na wyjsciu. Renderer:
  polyline weza rozcinana na max 3 kawalki w miejscach wyrw
  (>2x SEG_DIST), kazdy kawalek osobna para Line.
- Fix: żaba była do góry nogami — świat ma odwróconą oś Y
  (Scale.y=-cell, +y świata = dół ekranu). Oczy/łapy/skok
  odwrócone. Dotyczyło wszystkich niesymetrycznych rysunków —
  żaba była pierwszym.
- UI bez tekstu: IconWidget — piktogramy rysowane primitivami
  (play, retry, bolt, castle, cannon, frog, portal, skull).
  GRAJ=>trojkat, BOOST=>blyskawica, JESZCZE RAZ=>strzalka kolowa,
  KONIEC=>czaszka+wynik, toggles=>piktogramy. MENU i imie zostaja.
- Ikony v2: dzialo jako scieta lufa+kolo+kula (koniec z dwuznacznym
  ksztaltem), portale rozstawione z wchodzacym/wychodzacym wezem,
  blyskawica ostra (miter+square), zamek = mur z blankami+luk+flaga.
