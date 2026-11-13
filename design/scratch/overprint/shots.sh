#!/usr/bin/env bash
# shots.sh : rebuild both artboards, render, and crop the tile into readable parts
set -e
cd "$(dirname "$0")/../../.."
S=design/shots/overprint
python3 design/scratch/overprint/build_system.py >/dev/null
python3 design/scratch/overprint/build_feed.py >/dev/null
uv run --quiet --with playwright design/tools/dc_shot.py design/canvas/project/Cand-y-System.dc.html --out $S --width 1200 --height 1700 --frames ${1:-3.2} --scale 2 | python3 -c "import json,sys;d=json.load(sys.stdin);print('SYS overflow',d['overflow_x'],'console',d['console'],d['fonts'],d['size'])"
uv run --quiet --with playwright design/tools/dc_shot.py design/canvas/project/Cand-y-Feed.dc.html --out $S --frames ${2:-3} | python3 -c "import json,sys;d=json.load(sys.stdin);print('FEED overflow',d['overflow_x'],'console',d['console'],d['fonts'],d['size'])"
crop() { uv run --quiet --with pillow python design/scratch/overprint/crop.py "$@"; }
T=$S/Cand-y-System-1200w-light-t3.2.png
crop $T $S/sys-top.png 0 0 1200 600
crop $T $S/sys-mid.png 0 590 1200 620
crop $T $S/sys-bot.png 0 1190 1200 510
