#!/usr/bin/env bash
# zoom.sh : crop detail views from the latest renders
cd "$(dirname "$0")/../../.."
S=design/shots/overprint
crop() { uv run --quiet --with pillow python design/scratch/overprint/crop.py "$@"; }
crop $S/Cand-y-System-1200w-light-t3.2.png $S/z-comp.png 40 1020 720 200
crop $S/Cand-y-System-1200w-light-t3.2.png $S/z-bot.png 380 1420 800 280
crop $S/Cand-y-Feed-390w-light-t3.png $S/z-plate.png 0 200 390 270
