#!/usr/bin/env bash
cd "$(git rev-parse --show-toplevel)"
JS="() => { const seen = new Set(); const out = []; for (const p of document.querySelectorAll('path[pathLength]')) { const r = p.getBoundingClientRect(); if (r.width === 0) continue; const L = Math.round(p.getTotalLength()); const k = L + '|' + Math.round(r.width); if (seen.has(k)) continue; seen.add(k); out.push(L + ' px long, ' + Math.round(r.width) + ' wide, 1 percent = ' + (L * 0.01).toFixed(1) + ' | ' + (p.getAttribute('style') || '').replace('stroke-dasharray: 1 1.5; ', '').slice(0, 50)) } return out }"
for spec in "Site 1440 900" "Site 390 844" "App-Feed-Day 390 844" "Explainer-Day 390 844" "Motion 1200 1000"; do
  set -- $spec
  echo "== $spec"
  uv run --quiet --with playwright python design/scratch/final/probe.py "$1" "$2" "$3" "$JS"
done
