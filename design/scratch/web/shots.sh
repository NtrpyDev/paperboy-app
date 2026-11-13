#!/bin/bash
# Build the site artboard, render it full height at 1440 and 390, and split the PNGs into parts.
# usage: shots.sh [frame seconds, default 4]
set -e
T=${1:-4}
cd "$(git rev-parse --show-toplevel)"
python3 design/scratch/web/site.py
for W in 1440 390; do
  H=900; [ $W = 390 ] && H=844
  uv run --quiet --with playwright design/tools/dc_shot.py design/canvas/project/Site.dc.html --out design/shots/web --width $W --height $H --full --frames $T | python3 -c "import json,sys; d=json.load(sys.stdin); print($W, d['size'], 'overflow_x', d['overflow_x'], 'console', d['console'], sorted(set(d['fonts'])))"
done
rm -f design/shots/web/Site-*-p*.png
uv run --quiet --with pillow python design/scratch/web/crop.py design/shots/web/Site-1440w-light-t$T.png 1800 0.6
uv run --quiet --with pillow python design/scratch/web/crop.py design/shots/web/Site-390w-light-t$T.png 2200
