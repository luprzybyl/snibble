# MultiSnake — zasady gry

Wariant slither.io w konsoli: jedna plansza, wiele wężów. Gracz + boty AI.
Bez sieci — "multi" oznacza mnogość gadów, nie połączeń.

## Świat

- Plansza to siatka komórek (np. 200×200), większa niż ekran.
- Kamera podąża za wężem gracza — widok to viewport na świat.
- Krawędzie świata są śmiertelne (mur z cegieł — granica mapy zabija).
  *Alternatywa: torus (wrap-around) — do rozstrzygnięcia przy implementacji.*
- **Moduł ZAMKI** (opcjonalny, toggle w menu): kilka murowanych
  fort z bramą losowo na mapie — wjazd w mur zabija.
  Wąż-duch po spawnie (shield) przechodzi przez mury.
  W głębi każdego zamku czaka **tęczowy kryształ +30**
  (nie wygasa, nie respawnuje).

## Węże

- Na planszy żyje jednocześnie N wężów: 1 gracz + (N−1) botów (domyślnie N=10).
- Wąż = głowa + uporządkowana lista segmentów ciała.
- Długość startowa: np. 10 segmentów.
- Każdy wąż ma kolor i imię (widoczne na leaderboardzie).

## Ruch

- **Model ciągły**: pozycje float, wąż ma kierunek (kąt) i skręca płynnie
  z ograniczoną prędkością kątową (~4.5 rad/s) — jak w slither.io.
  Klawiatura kwantyzuje input do 8 kierunków; na dotyku kąt będzie wolny.
- Wąż ma promień ciała ~0.9 komórki (≈ grubość 2). Kręgosłup to punkty
  co ~0.5 komórki; kolizje rasteryzowane na siatkę.
- Prędkość: ~10 komórek/s (jednakowa we wszystkich kierunkach — model
  ciągły nie ma problemu √2).
- **Boost**: przytrzymanie klawisza przyspiesza (np. 2×) kosztem długości —
  wąż zrzuca segmenty, które zamieniają się w kryształki za ogonem.
  Minimalna długość do boostu: np. 5.
- Boty poruszają się wg prostej AI: dąż do jedzenia, unikaj ciał i ścian,
  okazjonalnie próbuj odcinać drogę mniejszym wężom.

## Kryształki (jedzenie)

- Kryształki rozrzucone losowo po planszy; stała gęstość
  (np. 1 na 100 komórek).
- Zjedzenie kryształka: +1 segment długości.
- Większe kryształki (z martwych wężów) dają więcej długości.

## Śmierć i kolizje

- Każdy wąż ma **poziom = długość** (większy = silniejszy).
- Głowa w **cudze** ciało → **PRZEGRYZIENIE**: ciało ofiary jest cięte
  w punkcie kontaktu; odgryziony ogon zamienia się w kryształki.
  Ofiara żyje, ale krótsza (jeśli zostaje < ~4 komórek → umiera).
  Przegryzający nie ponosi kary.
- Głowa w **własne** ciało → śmierć (sam się nie przegryziesz).
- Głowa w głowę → przegrywa wąż z mniejszym poziomem i zamienia się
  w kryształki; równy poziom → oba giną.
- Głowa w krawędź świata → śmierć.
- Martwy wąż zamienia się w większe kryształki rozłożone wzdłuż jego ciała
  (co drugi segment ≈ połowa masy odzyskiwana).
- Gracz po śmierci: ekran GAME OVER + wynik, opcjonalny respawn.
- Bot po śmierci respawnuje się po chwili w losowym bezpiecznym miejscu,
  żeby plansza nie pustoszała.

## Punktacja

- Wynik = aktualna długość węża.
- Leaderboard (top 10) wyświetlany w rogu ekranu na żywo.
- Rekord gracza zapisywany lokalnie (JSON).

## Sterowanie

- Strzałki / WASD / hjkl — kierunki proste.
- `q` `e` `z` `c` lub `y` `u` `b` `n` — skoski (NW/NE/SW/SE).
- Spacja — boost (trzymać; terminal powtarza klawisz).
- `p` — pauza, `r` — respawn po śmierci, Esc — wyjście.

## Założenia techniczne

- Python + `curses` (stdlib — zero zależności).
- Świat i logika niezależne od renderingu (łatwo podmienić front na np. web).
- Kolory przez `curses` color pairs; fallback na znaki ASCII.
