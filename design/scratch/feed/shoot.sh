#!/bin/sh
# Render the boards (and proofs when asked) with the frames SYSTEM.md section 12 asks for.
cd "$(git rev-parse --show-toplevel)" || exit 1
for f in "$@"; do
  uv run --quiet --with playwright design/tools/dc_shot.py "$f" --out design/shots/feed --frames 0.2,1.5,4 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['file'].split('/')[-1], 'overflow_x', d['overflow_x'], 'console', d['console'], 'size', d['size'], 'fonts', sorted(set(f.split(' ')[0]+' '+f.split(' ')[1] if f.startswith(('Martian','Noto','Source')) else f for f in d['fonts'])))"
done
