"""Punkt wejścia dla Buildozer/APK: python main.py.

Flagi demonstracyjne:
  --auto                                    autopilot (demka, pomija menu)
  --pos x,y --size W,H                      pozycja/rozmiar okna
"""
import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="Ty")
ap.add_argument("--auto", action="store_true")
ap.add_argument("--pos")
ap.add_argument("--size")
args = ap.parse_args()
sys.argv = [sys.argv[0]]        # Kivy też parsuje argv — zostaw puste

from kivy.config import Config

if args.pos:
    x, y = (int(v) for v in args.pos.split(","))
    Config.set("graphics", "position", "custom")
    Config.set("graphics", "left", str(x))
    Config.set("graphics", "top", str(y))
if args.size:
    w, h = (int(v) for v in args.size.split(","))
    Config.set("graphics", "width", str(w))
    Config.set("graphics", "height", str(h))

from snibble.kivy_app import GameWidget, SnibbleApp

app = SnibbleApp()
if args.auto:
    app.autostart = GameWidget(player_name=args.name, auto=True)
app.run()
