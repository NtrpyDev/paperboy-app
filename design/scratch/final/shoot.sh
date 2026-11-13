#!/usr/bin/env bash
# usage: shoot.sh NAME [dc_shot args...]   prints a short summary line
cd "$(git rev-parse --show-toplevel)" || exit 1
name="$1"; shift
uv run --quiet --with playwright design/tools/dc_shot.py "design/canvas/project/$name.dc.html" --out design/shots/final "$@" \
 | python3 -c 'import sys,json; d=json.loads(sys.stdin.read()); print(sys.argv[1], d["size"], "overflow_x=",d["overflow_x"], sorted(set(d["fonts"])), d["console"]); [print("  ",s) for s in d["shots"]]' "$name"
