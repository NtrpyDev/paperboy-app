"""Measure the feed boards: touch targets, text sizes, and where the cut lines fall.
Run from design/:  uv run --quiet --with playwright python scratch/feed/rev/measure.py FILE.dc.html ..."""
import pathlib
import sys
sys.path.insert(0, 'tools')
import dc_shot
from playwright.sync_api import sync_playwright

JS = """() => {
  const els = [];
  for (const el of document.querySelectorAll('a[href],button,input')) {
    const r = el.getBoundingClientRect();
    els.push({tag: el.tagName, text: (el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,40), w: +r.width.toFixed(1), h: +r.height.toFixed(1), y: +r.top.toFixed(1), b: +r.bottom.toFixed(1)});
  }
  const heads = [...document.querySelectorAll('h2')].map(h => { const r = h.getBoundingClientRect(); const f = h.firstElementChild ? h.firstElementChild.getBoundingClientRect() : r; return {text: h.innerText.slice(0,30), top: +r.top.toFixed(1), lineTop: +f.top.toFixed(1), bottom: +r.bottom.toFixed(1)}; });
  const tags = [...document.querySelectorAll('article > div:first-child')].map(d => { const r = d.getBoundingClientRect(); const s = d.querySelector('span'); const sr = s ? s.getBoundingClientRect() : r; return {top: +sr.top.toFixed(1), bottom: +sr.bottom.toFixed(1), rowBottom: +r.bottom.toFixed(1)}; });
  const seen = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const cs = getComputedStyle(n.parentElement); const k = parseFloat(cs.fontSize) + '|' + cs.fontFamily.split(',')[0]; seen[k] = (seen[k]||0)+1;
  }
  const svgText = [...document.querySelectorAll('svg text')].map(t => parseFloat(getComputedStyle(t).fontSize));
  return {els, heads, tags, sizes: seen, svgTextMin: svgText.length ? Math.min(...svgText) : null};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=['--no-sandbox'])
    for f in sys.argv[1:]:
        src = pathlib.Path(f).resolve()
        tmp = src.with_name('.' + src.name + '.measure.html')
        tmp.write_text(dc_shot.to_plain_html(src.read_text()))
        try:
            pg = b.new_context(viewport={'width': 390, 'height': 844}).new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(4000)
            r = pg.evaluate(JS)
        finally:
            tmp.unlink(missing_ok=True)
        print('==', src.name)
        for e in r['els']:
            vis = e['y'] < 844 and e['b'] > 0
            flag = '  <-- under 44' if (e['h'] < 44 or e['w'] < 44) else ''
            print(f"  {e['tag']:6} {e['w']:6}x{e['h']:<5} y={e['y']:<6} bottom={e['b']:<6} {'' if vis else '(off screen) '}{e['text']!r}{flag}")
        for h in r['heads']:
            print('  h2', h)
        for t in r['tags']:
            print('  tag row', t)
        print('  sizes', dict(sorted(r['sizes'].items(), key=lambda kv: float(kv[0].split('|')[0]))))
        print('  svg text min px', r['svgTextMin'])
    b.close()
