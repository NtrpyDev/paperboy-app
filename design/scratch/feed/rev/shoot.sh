#!/bin/sh
# Render files with the frames SYSTEM.md section 12 asks for. Usage: shoot.sh OUTDIR FRAMES file...
cd "$(git rev-parse --show-toplevel)" || exit 1
out="$1"; frames="$2"; shift 2
for f in "$@"; do
  uv run --quiet --with playwright design/tools/dc_shot.py "$f" --out "$out" --frames "$frames" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['file'].split('/')[-1], 'overflow_x', d['overflow_x'], 'console', d['console'], 'size', d['size'], 'fonts', sorted(set(' '.join(f.split(' ')[:-1]) for f in d['fonts'])))"
done
