import sys, pathlib, json
sys.path.insert(0, 'tools')
import dc_shot
from playwright.sync_api import sync_playwright
P = pathlib.Path('canvas/project')
jobs = [('Motion',1200,1000),('Brand',1200,900)]
JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('a[href],button,input')) {
    const r = el.getBoundingClientRect();
    out.push({tag: el.tagName, text: (el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,40), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + scrollY)});
  }
  const small = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = {};
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const cs = getComputedStyle(n.parentElement); const fs = parseFloat(cs.fontSize);
    const k = fs + '|' + cs.fontFamily.split(',')[0]; seen[k] = (seen[k]||0)+1;
  }
  const svgText = [...document.querySelectorAll('svg text')].map(t => parseFloat(getComputedStyle(t).fontSize) * (t.getCTM() ? t.getCTM().a : 1));
  return {els: out, sizes: seen, svgTextMin: svgText.length ? Math.min(...svgText) : null, svgTextCount: svgText.length};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=['--no-sandbox'])
    for name, w, h in jobs:
        src = (P / f'{name}.dc.html').resolve()
        tmp = src.with_name('.' + src.name + '.judge.html')
        tmp.write_text(dc_shot.to_plain_html(src.read_text()))
        try:
            pg = b.new_context(viewport={'width': w, 'height': h}).new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(600)
            r = pg.evaluate(JS)
        finally:
            tmp.unlink(missing_ok=True)
        print('==', name, w)
        for e in r['els']:
            flag = '  <-- under 44' if (e['h'] < 44 or e['w'] < 44) else ''
            print(f"  {e['tag']:6} {e['w']:4}x{e['h']:<4} y={e['y']:<5} {e['text']!r}{flag}")
        print('  sizes', dict(sorted(r['sizes'].items(), key=lambda kv: float(kv[0].split('|')[0]))))
        print('  svg text min px', r['svgTextMin'], 'count', r['svgTextCount'])
    b.close()
