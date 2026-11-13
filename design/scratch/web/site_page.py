"""The production website, built from the Site board's own generator (site.py).

  python3 design/scratch/web/site_page.py

writes site/index.html, the hero plate layers site/plate1-*.svg, and the Open Graph card
source design/scratch/web/og.html (og_shot.py renders that to site/og.png).

The page is the board's markup with these changes, each asserted to apply exactly once:

- Fonts come from the kit (/kit/v2/fonts/fonts.css). No request goes to another host.
- The hero plate's two print layers (blue and black) are image files loaded through
  <picture>, so a browser fetches only the drawing for its width. The board inlines all
  four drawings. There are still four drawings (230, 284, 318, 354 px tall): ring pitch and
  line weights are fixed in px, so one drawing scaled to every width would not look the same.
  Windows for other widths are display: none, so their animations do not run.
- The phone mock is scaled with transform: scale() inside a wrapper sized to the scaled box,
  in place of the board's CSS zoom.
- Download links go to the latest release's APK, the journal links to the paper's DOI, and
  the footer's Site row names the host the site is served at (SITE_HOST).
- Figures below the first screen draw in once, when they scroll into view (a few lines of
  script). Without the script, or with reduced motion, every figure shows its resting frame.
"""
import html
import importlib.util
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
SITE = REPO / "site"

# Change the site's address here. It is used in the footer and the Open Graph tags.
SITE_HOST = "paperboy.ntrpydev.workers.dev"
SITE_URL = f"https://{SITE_HOST}/"

GITHUB = "https://github.com/NtrpyDev/paperboy-app"
# GitHub docs, "Linking to releases": /releases/latest/download/<asset name>.
# .github/workflows/release.yml uploads the APK under this fixed name as well as paperboy-<version>.apk.
APK = "https://github.com/NtrpyDev/paperboy-app/releases/latest/download/paperboy.apk"
# Physical Review Letters 116, 061102. Resolves to journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.061102.
PAPER = "https://doi.org/10.1103/PhysRevLett.116.061102"

TITLE = "Paperboy: new science and math papers, explained in pictures"
# Facts from design/CONTENT.md only.
DESCRIPTION = ("A free, open source Android app: a feed of newly released science and math papers. "
               "Papers with a free legal full text get a visual explainer. No account. No ads.")

# The phone mock's outer size at scale 1 is 392 (390 and a 1 px border) by SHEET_H. Height measured on the board in Chromium (getBoundingClientRect).
SHEET_H = 897.52

_spec = importlib.util.spec_from_file_location("site_board", HERE / "site.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def once(text, old, new):
    n = text.count(old)
    assert n == 1, f"expected one {old[:60]!r}, found {n}"
    return text.replace(old, new)


# ------------------------------------------------------------------ links
S.RELEASES = APK
S.GITHUB = GITHUB

# ------------------------------------------------------------------ hero plate layers as files
# One window per plate height. The board shows each at these widths (site.py, --h-* properties).
PLATE_MEDIA = {
    230: "(max-width: 699.98px)",
    284: "(min-width: 700px) and (max-width: 929.98px)",
    318: "(min-width: 930px) and (max-width: 1159.98px)",
    354: "(min-width: 1160px)",
}
BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
_plate_gw = S.plate_gw
PLATE_FILES = {}


def plate_gw(pid, W, band, *a, **kw):
    out = _plate_gw(pid, W, band, *a, **kw)
    h = band + 34
    pat = re.compile(rf'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block">.*?</svg>', re.S)
    layers = pat.findall(out)
    assert len(layers) == 2, (pid, len(layers))
    for name, svg in zip(("blue", "black"), layers):
        fname = f"plate1-{h}-{name}.svg"
        PLATE_FILES[fname] = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1).replace(
            ' aria-hidden="true" style="display: block"', "", 1)
        pic = (f'<picture><source media="{PLATE_MEDIA[h]}" srcset="{fname}">'
               f'<img src="{BLANK}" width="{W}" height="{band}" alt="" decoding="async" '
               f'style="display: block; width: {W}px; height: {band}px; max-width: none"></picture>')
        out = once(out, svg, pic)
    return out


S.plate_gw = plate_gw

# ------------------------------------------------------------------ figures that draw in on view
for fn_name in ("plate_m87", "fig_detectors", "range_bar"):
    def _wrap(*a, _f=getattr(S, fn_name), **kw):
        out = _f(*a, **kw)
        tag = out[: out.index(" ")]
        return out.replace(tag + " ", tag + " data-draw ", 1)
    setattr(S, fn_name, _wrap)

_made = S.made_figure
S.made_figure = lambda: _made().replace("<div ", "<div data-draw ", 1)

# ------------------------------------------------------------------ the phone mock without zoom
_sheet = S.sheet


def sheet():
    out = _sheet()
    out = once(out, "zoom: var(--sz); width: 390px;",
               f"width: 392px; height: {SHEET_H}px; box-sizing: border-box; transform: scale(var(--sz)); transform-origin: 0 0;")
    return (f'<div style="width: calc(392px * var(--sz)); height: calc({SHEET_H}px * var(--sz))">{out}</div>')


S.sheet = sheet

# ------------------------------------------------------------------ build the board's body and style
captured = {}
S.page = lambda title, css, body, w, h: captured.update(css=css, body=body) or ""


class _Out:
    def write_text(self, s):
        pass

    def stat(self):
        return type("st", (), {"st_size": 0})()


S.OUT = _Out()
S.print = lambda *a, **k: None
S.build()
body, css = captured["body"], captured["css"]

body = body.replace('href="#paper"', f'href="{PAPER}"')
assert body.count(PAPER) == 2
body = once(body, "[YOUR DOMAIN]", SITE_HOST)
assert "#paper\"" not in body and "zoom" not in body
assert "releases\"" not in body

# Only the hero plate window for the current width is displayed, so the three hidden windows
# run no animations (the board hides them with visibility and a height of 0).
for v in "smnl":
    body = once(body, f"visibility: var(--v-{v});", f"visibility: var(--v-{v}); display: var(--dp-{v});")
css += """
:root{--dp-s:block;--dp-m:none;--dp-n:none;--dp-l:none}
@media (min-width:700px){:root{--dp-s:none;--dp-m:block}}
@media (min-width:930px){:root{--dp-m:none;--dp-n:block}}
@media (min-width:1160px){:root{--dp-n:none;--dp-l:block}}
.wait,.wait *{animation-play-state:paused!important}"""

SCRIPT = """<script>
(function () {
  // Figures below the first screen draw in once, when they come into view.
  var figs = document.querySelectorAll('[data-draw]');
  if (!('IntersectionObserver' in window) || !figs.length) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.remove('wait'); io.unobserve(e.target); }
    });
  }, { threshold: 0.35 });
  figs.forEach(function (f) { f.classList.add('wait'); io.observe(f); });
})();
</script>"""

FONT_FILES = ["NotoSerifDisplay-Roman-latin", "NotoSerifDisplay-Italic-latin", "SourceSerif4-Roman-latin",
              "SourceSerif4-Italic-latin", "MartianMono-Roman-latin"]
preload = "\n".join(f'<link rel="preload" href="/kit/v2/fonts/{f}.woff2" as="font" type="font/woff2" crossorigin>'
                    for f in FONT_FILES)
for f in FONT_FILES:
    assert (REPO / "kit" / "v2" / "fonts" / f"{f}.woff2").exists(), f

e = html.escape
head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{e(TITLE)}</title>
<meta name="description" content="{e(DESCRIPTION)}">
<link rel="canonical" href="{SITE_URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Paperboy">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{e(DESCRIPTION)}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}og.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Paperboy wordmark over Plate 1: an engraved field of blue rings with a red line drawn across it.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{preload}
<link rel="stylesheet" href="/kit/v2/fonts/fonts.css">
<style>
{css}
</style>
</head>
<body>
"""
page = head + body + "\n" + SCRIPT + "\n</body>\n</html>\n"
assert "\u2014" not in page, "em dash"
assert "googleapis" not in page and "gstatic" not in page

SITE.mkdir(exist_ok=True)
(SITE / "index.html").write_text(page)
for old in SITE.glob("plate1-*.svg"):
    old.unlink()
for fname, svg in PLATE_FILES.items():
    (SITE / fname).write_text(svg)
print("wrote", SITE / "index.html", len(page), "bytes;", len(PLATE_FILES), "plate files")

# ------------------------------------------------------------------ Open Graph card source
# 1200 by 630. The wordmark over Plate 1 at the desktop hero's scale, in its resting frame.
og_plate = _plate_gw("og", 1144, 330, 0, 1088, 1.6, 108, 46, 62, 0.005, 0.05, "wipeL", lab_px=13, sweep_ms=2100)
og = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Paperboy card</title>
<link rel="stylesheet" href="/kit/v2/fonts/fonts.css">
<style>
html,body{{margin:0;background:{S.STOCK}}}
*{{animation:none!important}}
</style>
</head>
<body>
<div style="width: 1200px; height: 630px; overflow: hidden; position: relative; background-color: {S.STOCK}; color: {S.INK}">
<div style="position: absolute; left: 56px; right: 56px; top: 44px">
<div style="font-size: 132px; line-height: 1; white-space: nowrap; padding-bottom: 14px">{S.wordmark("1em", "0.147em", "0.067em", ls=(-0.012, -0.025))}</div>
{S.DOUBLE}
</div>
<div style="position: absolute; left: 56px; right: 0; bottom: 34px">{og_plate}</div>
</div>
</body>
</html>
"""
(HERE / "og.html").write_text(og)
print("wrote", HERE / "og.html")
