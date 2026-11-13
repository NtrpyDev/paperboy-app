#!/usr/bin/env bash
cd "$(git rev-parse --show-toplevel)"
P=design/canvas/project
O=design/shots/judge
shot() { uv run --quiet --with playwright design/tools/dc_shot.py "$@" | tail -1 | cut -c1-900; echo; }
shot $P/Explainer-Day.dc.html --out $O --width 390 --height 844 --full --frames 4
shot $P/Explainer-Day.dc.html --out $O/top --width 390 --height 844 --frames 0.2,1.5,4
shot $P/Explainer-Night.dc.html --out $O --width 390 --height 844 --full --frames 4
shot $P/Explainer-Night.dc.html --out $O/top --width 390 --height 844 --frames 0.2,1.5,4
shot $P/Site.dc.html --out $O --width 1440 --height 900 --full --frames 4
shot $P/Site.dc.html --out $O --width 390 --height 844 --full --frames 4
shot $P/Site.dc.html --out $O/top --width 1440 --height 900 --frames 0.2,1.5,4
shot $P/Site.dc.html --out $O/top --width 390 --height 844 --frames 0.2,1.5,4
shot $P/Motion.dc.html --out $O --width 1200 --height 1000 --frames 0.3,1,2,3.5
shot $P/Motion.dc.html --out $O/full --width 1200 --height 1000 --full --frames 4
shot $P/Brand.dc.html --out $O --width 1200 --height 900 --frames 1,4
shot $P/Brand.dc.html --out $O/full --width 1200 --height 900 --full --frames 4
