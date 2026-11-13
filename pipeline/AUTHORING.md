# Authoring an explainer

How to build the page that teaches one paper. The automated rules are in `EXPLAINER-CONTRACT.md`; this file is the craft and the kit. The kit's classes and helpers are listed in full at the end. `kit/v2/gallery.html` is a complete explainer built only from them (the Paper 1 explainer of the design boards, then every other pattern): read its source before you write, and write your page the same way.

## What an explainer is

A reader scrolls a feed, sees a card, taps it, and gives you about ten seconds. By the end of the first screen they should know what was found. By the end of the page they should understand it well enough to explain it to a friend, including how sure anyone can be. They get there by looking and by playing, with short text between visuals. Text carries what pictures cannot; pictures carry everything else.

## The look, in one paragraph

A gray printed sheet, set like a broadsheet front page, carrying an engraved plate in one blue ink. Across the plate runs one vermilion line that is drawn as the reader watches, with a pen point at its tip and a carriage riding the ruler under it. By night the sheet is a blue-black light table, the plate is drawn in dim blue light, and the line is amber and glows. Everything except that line is still. Hierarchy comes from type size, from the two voices of the headlines, and from horizontal rules. Never from boxes, tints, shadows, rounded corners, or colored edges. The kit draws all of this; you choose the content and the marks.

## The page, in order

1. **Hero** (`.pb-hero`). The tag row (the field as an outline tag, the review status as a badge, the journal as a link), the headline, the plate, the readout row (the one number and what it measures on the left, the plate slug on the right), then the dek: two to four plain sentences.
2. **Key idea** (`.pb-callout[data-kind="key"]`). One sentence a reader should keep, in the display italic. Nothing around it.
3. **The question** (`data-section="question"`). What nobody knew. Teach the one or two ideas the reader needs first.
4. **What they did** (`data-section="method"`). The method as something the reader can watch: scroll steps driving one figure, or a diagram.
5. **What they found** (`data-section="findings"`). The evidence, in figures drawn from the brief's evidence table. Lead with the single most important number as a stat.
6. **How sure is this?** (`data-section="confidence"`). The ledger: strengths, limits, open questions, from the brief. Its head is the title; it has no slug. A preprint says it has not been peer reviewed.
7. **Why it matters** (`data-section="matters"`). What changes, said without inflation.
8. **Source footer** (`.pb-source`). The paper's title, authors, journal and date and license, "Read the paper", and the closing line that the page was written by a machine and can be wrong.

Every section opens with a double rule (the kit draws it), a slug, and a two-voice head. Aim for 5 to 8 visuals and 350 to 650 words of prose. A paragraph is two to four sentences.

## Writing

- **Two voices.** Every headline and section head is set in the display face. Its last clause turns to the italic second voice: mark it with `<em>`. "Two black holes merged. `<em>`Earth felt space stretch.`</em>`" The second voice never starts a head. Sentence case, never all caps. If nothing should turn, leave out the `<em>`. The kit decides where the turn breaks.
- Plain words, short sentences, active voice. Define a term the first time it appears, in the sentence or as a tappable glossary term.
- Say exactly as much as the paper supports. "Suggests", "in mice", "in a simulation", "in this sample of 48 people" when that is the truth.
- Headlines state findings. No questions in a hero headline, no hype words, no exclamation marks, no em dashes.
- Every number comes from the brief's evidence table, with its unit. Round only with "about". Use a real minus (−) and real superscripts (`10<sup>−21</sup>`). In running text the multiplication sign is typed (×); beside a display numeral it is drawn (`<span class="pb-sign">×</span>`).
- **A caveat is a footnote, not a box.** Type a dagger (†) right after the claim it qualifies, then put the note in a `.pb-callout[data-kind="caveat"]` that opens with the same dagger. A second caveat in the same section uses ‡.
- **An analogy is a figure.** Draw the familiar thing and the paper's thing on one scale (`<figure class="pb-fig" data-kind="illustration" data-slug="For scale">`) and put the one sentence that makes the comparison in the `figcaption`. Say where the analogy breaks if it does.

## Visuals that teach

Decide what the reader must see, then pick the form.

- **One number is the story:** a stat (`.pb-stat`), the number at 72 px with what it is beside it, then the figure that shows its range (`PB.rangeBar`).
- **Compare a few magnitudes:** bars on one ruler (`PB.barRows`), 20 px tall with a 0.9 px outline, figures above them in the display face.
- **A trend:** lines on a ruler (`PB.plot` with `c.marks.line` and `live`), each named at its end. Four lines at most.
- **Before and after:** a dumbbell: an open ring before, a solid dot after, joined by a beam, one row per item.
- **Part of a whole:** one segmented bar (`PB.barRows` with several segments in one row), six parts at most. Never a pie or donut.
- **A distribution or many points:** dots (`c.marks.dots`), the few that matter named.
- **A value with a range:** the range bar. Several measured values with ranges: error bars. A range along a line: a screened band.
- **A process or mechanism:** a drawing that builds in scroll steps (`PB.steps`) or animates the cause leading to the effect.
- **A relationship the reader can feel:** a control: the carriage on a ruler (`PB.slider`) or a toggle (`PB.toggle`) that changes what the paper varied, with the figure answering at once.

### The plate and its marks

- The hero is a **plate** (`PB.plate`): full bleed, square, no frame, in the page's own theme. It has at most three layers: the print (plate ink: engraved rings, line screens), the key (the subject in contours or outlines over a ground knockout), and the live layer (the live line, the ruler, the carriage, direct labels at the marks). The readout and the plate slug sit under it on open ground, never on it. No type is set on a field.
- The plate's stills at rest, in the light and the dark color scheme, are the card's two images in the feed. Draw the plate so its still is complete and striking in both. The kit gives night its own colors through the tokens; never draw a separate night picture by hand.
- **One live mark per figure.** The live color (vermilion by day, amber by night) marks only the one thing that carries the paper's reported value or the finding: the live line, a marker, one segment, one point. It is always solid. It is never text, never a legend for anything else, never a second mark. Its legend key is the 7 px dot.
- **Solid means measured or reviewed. Screened means a range, an estimate, or a preprint.** An "about" value is drawn screened (`PB.screen`, or `kind: "screen"` in the chart helpers). Two screened series use the two screen angles, and where they overlap the weave (`kind: "weave"`). The live mark is the exception: always solid, with "about" in its label or caption.
- **Series are told apart by lightness and form, not hue**, in this order: 1 the finding (live), 2 ink, 3 plate ink, 4 an estimate (a screen for a band or bar; a thin muted line for a line). Four at most; more becomes small multiples (`.pb-multiples`).
- **A plate gets a ruler and a carriage only when its line is really plotted against that quantity.** A line with no real axis has no ruler; its pen point leads alone.
- The live line never touches plate ink directly: it rides on its ground trap. The kit draws the trap.

### Rules for every chart

- One axis, and it is a ruler (`PB.ruler`): a 0.9 px line, ticks below it, labels 20 px under, the unit written once. Two measures with different scales get two charts.
- Start bars at zero. Grid and drop lines are 0.6 px solid; value lines are named at their left end (`PB.valueLines`). Never dashed.
- Labels sit at the mark, horizontal, in the text color, never in a series color. A legend (`PB.legend`) appears only for two or more kinds of mark, and never repeats a mark that carries a direct label.
- Every figure has a head row: its slug on the left (`data-slug="Fig. 2"`, "For scale", "Try it") and its kind on the right, which the kit writes from `data-kind`.
- Every data figure carries its numbers as a table (`PB.table`), the last row of the figure, and a caption that says where in the paper the numbers come from, or what the head row does not say ("All four values are estimates.").
- A concept drawing is `data-kind="illustration"` (with `data-scale="true"` only when it is drawn to scale). It must not look like measured data: no fake axes with invented values, no scatter of made-up points.
- Every SVG that carries meaning has an `aria-label` that states its numbers. The kit's helpers take a `label` option for it.

## Motion

- Three verbs and one loop: a line of type **presses** in, a plate **inks in** and its layers slide into **register**, a live line **sweeps** with its pen point **traveling** along it. After the hero's sweep its pen point **pulses**. A marker **drops** onto its band; a solid live mark **floods** in. Nothing bounces, overshoots, or loops anywhere else.
- Every figure has exactly one draw-in, on its one live mark. The kit's helpers add it. A figure below the first screen holds its draw-in until it scrolls into view, and plays it once; a figure redrawn for a new width or theme does not play it again. The kit does both.
- Design the resting frame first: plate in register, line fully drawn, pen point parked at the end, carriage under it. With reduced motion every animation is removed and that frame is what shows. The kit's marks are already their resting frame without the animation, so a page built from them is complete. For your own canvas animations, pass `still` to `PB.animate` so readers with reduced motion get the most informative frame, not the empty first one.
- Motion explains: a cause producing an effect, a signal arriving, a structure assembling, a quantity changing as the reader drags. Decoration that moves is noise. Text never fades in.
- Scroll steps: three to six steps, each a sentence or two, each changing the pinned figure in one clear way.

## Interaction

- A control changes one thing and the figure answers immediately. Label it with what it changes and show its current value in words.
- Controls are 44 px tall (buttons 48), square, and work with a thumb. The page works at 390 px wide with no sideways scrolling.
- Tappable glossary terms (`.pb-term`) for jargon the reader will meet again.
- A touch readout (`PB.tooltip` with `PB.touch`) on a chart whose marks have values worth reading one by one.

## Honesty

- Data figures plot only numbers from the paper. If the paper gives four numbers, the chart has four marks.
- Where the paper gives uncertainty, show it: a range bar, error bars, a band, or "about" with the range in the caption.
- Say what the paper does not show, in the ledger, in plain words. No scores, no percentages of confidence, no meters, no traffic-light colors, no colored dots.
- A figure reproduced from the paper is allowed only when the brief's "Figures worth reproducing" lists it (license CC BY or CC0), marked `data-kind="paper"`, with its credit line (`.pb-credit`).
- Never use a box, card, callout, or tab with a colored bar or stripe on any edge. No tinted boxes, no shadows, no gradients, no rounded corners.

## Technical ground rules

- One file, `index.html`. Everything the page needs beyond the kit is inline: SVG, canvas code, data. No external requests of any kind: no fonts, images, or scripts from anywhere else. The kit carries its fonts.
- Load the kit from `/kit/v2/` exactly as the head below does, and wrap all page code in `PB.ready(function () { ... })`.
- Draw with the kit's tokens, never with hex colors: CSS classes (`pb-line`, `pb-shape`, ...) or `style("fill", "var(--pb-plate)")` in SVG, or `PB.theme(el)` in canvas and Plot code. Then day and night both work.
- Redraw on resize: use `PB.plate`, `PB.svg`, `PB.plot`, or `PB.canvas`, which handle it. Give them the drawing as a function of the width they pass you.
- Keep the page light: no large embedded images, no data arrays beyond what the charts need.

## The kit

<!-- KIT-REFERENCE: this section is maintained with the kit. It lists every component class and every PB helper with a short example. -->

Kit v2 lives at `/kit/v2/`. Old kit versions stay served forever; every new page uses v2.

### The page skeleton

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>The hook</title>
<link rel="stylesheet" href="/kit/v2/vendor/katex/katex.min.css">
<link rel="stylesheet" href="/kit/v2/paperboy.css">
<script src="/kit/v2/vendor/d3.min.js"></script>
<script src="/kit/v2/vendor/plot.umd.min.js"></script>
<script src="/kit/v2/vendor/katex/katex.min.js"></script>
<script src="/kit/v2/vendor/katex/auto-render.min.js"></script>
<script src="/kit/v2/paperboy.js"></script>
</head>
<body>
<article class="pb">
  ...hero, key idea, five sections, source footer...
</article>
<script>
PB.ready(function () {
  /* all page code */
});
</script>
</body>
</html>
```

The kit writes the web top bar (the wordmark, a link to the site) above the article. Inside the Android app, whose WebView user agent contains `PaperboyApp/`, it leaves the bar out because the app draws its own. Do not write a bar yourself.

The page follows the reader's color scheme. `data-theme="light"` or `"dark"` on `<html>` forces one; do not set it in an explainer.

### Hero

```html
<header class="pb-hero">
  <div class="pb-kicker">
    <span class="pb-tag">Physics</span>
    <span class="pb-badge" data-status="peer_reviewed">Peer-reviewed</span>
    <a class="pb-journal" href="https://doi.org/...">Physical Review Letters</a>
  </div>
  <h1 class="pb-title">Two black holes merged. <em>Earth felt space stretch.</em></h1>
  <div class="pb-stage" id="hero" data-kind="illustration"></div>
  <div class="pb-readout-row">
    <div>
      <div class="pb-readout">1.0<span class="pb-sign">×</span>10<sup>−21</sup></div>
      <span class="pb-label">Peak strain. Pitch 35 to 250 Hz</span>
    </div>
    <div class="pb-plate-slug">Plate 1<br>Illustration,<br>not to scale</div>
  </div>
  <p class="pb-dek">Two to four plain sentences: what was found, in this paper's terms.</p>
</header>
```

- `.pb-kicker`: the tag row. `.pb-tag` is the field (a ruled outline). `.pb-badge` with `data-status="peer_reviewed"` is a solid slab; with `data-status="preprint"` it is a hatched frame. `.pb-journal` is the journal link; the kit adds its arrow. If the row does not fit, the link takes its own line.
- `.pb-title`: the headline. `<em>` marks the second voice.
- `.pb-stage`: the plate. Exactly one in the hero, with `data-kind="data"` (it plots the paper's numbers) or `"illustration"`, and `data-scale="true"` only for an illustration drawn to scale. Draw it with `PB.plate`.
- `.pb-readout-row`: under the plate. `.pb-readout` is the number at 44 px (`.pb-readout-s` at 30 px); `.pb-unit` sets a unit after it in the text italic; `<sup>` is a real exponent; `.pb-sign` holding `×` or `>` becomes the drawn sign. `.pb-plate-slug` names the plate and its kind, three short lines.
- `.pb-dek`: the summary under the plate.

### Key idea and sections

```html
<div class="pb-callout" data-kind="key">
  <span class="pb-callout-label">Key idea</span>
  <p>The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</div>

<section class="pb-section" data-section="question">
  <p class="pb-eyebrow">The question</p>
  <h2>Can a machine on Earth <em>feel space stretch?</em></h2>
  <p>A gravitational wave is a ripple in spacetime. ...</p>
</section>
```

- `.pb-section`: a section. The kit draws its double rule. `data-section` marks the five required ones; other sections may sit between them. `.pb-eyebrow` is the slug ("The question", "What they did", "What they found", "Why it matters"). `h2` is the two-voice head; `h3` the same at a smaller step.
- `.pb-callout[data-kind="key"]`: the key idea, between the hero and the first section. One per page.
- `.pb-callout[data-kind="caveat"]`: a footnote under a 64 px rule. Its `.pb-callout-label` is hidden; open the note with the dagger you typed in the text.

```html
<p>... about 410 megaparsecs away, roughly 1.3 billion light years.†</p>
<div class="pb-callout" data-kind="caveat">
  <span class="pb-callout-label">Caveat</span>
  <p>† The mass and distance values carry wide error ranges. ...</p>
</div>
```

- `.pb-note`: a sentence in the text italic at 15 px (a note under a figure, the closing line).
- `.pb-label`: a mono label in the muted ink. `.pb-slug`: the same in ink, heavier.
- `.pb-sr`: text for screen readers only.

### Figures

```html
<figure class="pb-fig" data-kind="data" data-slug="Fig. 3">
  <p class="pb-fig-title">Where the mass went</p>
  <div id="mass"></div>
  <div id="mass-legend"></div>
  <div id="mass-table"></div>
  <figcaption>Masses as the paper reports them, Table 1.</figcaption>
</figure>
```

- `.pb-fig`: a hairline, then the head row: `data-slug` on the left, the kind on the right from `data-kind` (`data`: "Data, from the paper"; `illustration`: "Illustration, not to scale"; with `data-scale="true"`: "Illustration, drawn to scale"; `paper`: "Figure from the paper", with a `.pb-credit` line).
- `.pb-fig-title`: the figure's title in the display face, 30 px. Optional; a stat figure has none.
- `figcaption`: one sentence in the text italic.
- `.pb-bleed`: a child that runs from one screen edge to the other (a plate inside a figure). Give it to the element you draw a plate or a wide drawing into.
- `.pb-wide`: a figure that keeps the full width at desktop size instead of moving to the side rail. A figure holding a `.pb-bleed` is wide by itself. `data-size="column"` keeps a figure in the text column at desktop size.
- `.pb-chart`, `.pb-plot`: the kit adds these to the containers it draws charts into (14 px under the title).
- `.pb-legend`: the legend row; write it with `PB.legend`.
- `.pb-multiples`: two or three small drawings side by side, each a column with its label and value under it.
- At 1160 px and wider the page uses the website's grid: text in seven columns, figures in a rail on the right, the plate from the text's left edge off the right edge of the screen. You do not write anything for it.

### Stat

```html
<figure class="pb-fig" data-kind="data" data-slug="Fig. 2">
  <div class="pb-stat">
    <div class="pb-stat-value">410</div>
    <div class="pb-stat-label"><b>Megaparsecs away</b>roughly 1.3 billion light years</div>
  </div>
  <div id="distance"></div>   <!-- PB.rangeBar -->
  <div id="distance-legend"></div>
  <div id="distance-table"></div>
</figure>
```

- `.pb-stat`: one number at 72 px (`.pb-stat-value`) with what it is beside it (`.pb-stat-label`: the `<b>` in mono caps, then the italic line), bottoms aligned. No tile. One stat per figure; `.pb-stats` holds several stacked. `.pb-hero-number` is the same numeral outside a stat.

### How sure is this? (the ledger)

```html
<section class="pb-section" data-section="confidence">
  <h2>How sure <em>is this?</em></h2>
  <ul class="pb-confidence">
    <li class="pb-confidence-head">Strengths</li>
    <li><b>Review</b><span class="v"><span class="pb-badge" data-status="peer_reviewed">Peer-reviewed</span></span><span class="note">Physical Review Letters, February 11, 2016.</span></li>
    <li><b>Significance</b><span class="v"><span class="pb-sign">&gt;</span>5.1<span class="pb-unit">sigma</span></span><span class="note">A false alarm this strong is expected less than once in 203,000 years.</span></li>
    <li class="pb-confidence-head">Limits</li>
    <li><b>Distance</b><span class="v">410<span class="pb-unit">megaparsecs</span></span><span class="note">With a range of roughly 230 to 570.</span><span id="distance-mini"></span></li>
    <li class="pb-confidence-head">Open questions</li>
    <li><b>...</b><span class="note">...</span></li>
    <li data-kind="standing"><b>This explainer</b>Machine written, and it can be wrong. Check it against the paper.</li>
  </ul>
</section>
```

- `.pb-confidence`: rows split by full-width hairlines. Each `li` is a label (`b`), a value in display figures (`.v`, with a `.pb-unit`), and a note (`.note`). `.pb-confidence-head` rows are the subheads: Strengths, Limits, and Open questions when the brief has any. A limit that is a range carries the small range bar (`PB.rangeBar` with `mini: true`) beside its note. The last row is the standing row, `data-kind="standing"`, with this sentence.
- A row may have no value: then it is the label and the note.

### Source footer

```html
<footer class="pb-source">
  <p class="pb-eyebrow">Source</p>
  <cite>Observation of Gravitational Waves from a Binary Black Hole Merger</cite>
  <p class="pb-authors">B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)</p>
  <small>Physical Review Letters 116, 061102</small>
  <small>February 11, 2016. Peer-reviewed. CC BY 3.0</small>
  <a class="pb-btn" href="https://doi.org/10.1103/PhysRevLett.116.061102">Read the paper</a>
  <p class="pb-note">This page was written by a machine and can be wrong. The paper is the source.</p>
</footer>
```

### Buttons and controls

- `.pb-btn`: a 48 px ruled outline with the out arrow (a link out). `data-kind="primary"` makes it the ink slab with the forward arrow; one per page at most. A `button.pb-btn` has no arrow.
- `.pb-term`: a glossary term. `<span class="pb-term" data-def="One or two plain sentences.">chirp</span>`; `data-term` overrides the word shown in the slip. A tap opens the definition as a slip across the column, a second tap or a scroll closes it.
- Sliders, toggles, and the data table are written by `PB.slider`, `PB.toggle`, and `PB.table` below.

### Math

KaTeX renders `\( ... \)` inline and `\[ ... \]` on its own line. Number an equation with `\tag*{Eq. 1}`; the kit sets the tag as a label. Math is in the text color, never in the live or plate color. A wide equation scrolls sideways in its own block.

```html
<p>\[ 36\,M_\odot + 29\,M_\odot \approx 62\,M_\odot + 3\,M_\odot \tag*{Eq. 1} \]</p>
```

### Script: setup and drawing surfaces

- `PB.ready(fn)`: page code runs inside it, after the document, the kit, and math are set up. An error inside is recorded for the render check.
- `PB.theme(el)`: the tokens in effect at `el` as strings: `page`, `ink`, `ink2`, `grid`, `axis`, `rule`, `live` (also `accent`), `plate`, `contour`, `screen`, `carriage`, `slab`, `onSlab`, `stamp`, `onStamp`, the fonts `font`, `display`, `mono`, `labelSize`, `voice1`, the live line's sizes, `night` (true by night), and `series` (`[live, ink, plate, ink2]`). Use it in canvas and Plot code; in SVG prefer the classes and `var(--pb-...)`.
- `PB.responsive(el, fn)`: runs `fn(width, theme)` now and again when the width or theme changes. Returns a stop function; `.run()` reruns it with its draw-ins.
- `PB.svg(target, {height | aspect, label}, draw)`: a responsive SVG; `draw(svg, {width, height, theme})` must draw everything from scratch (the kit clears it). Returns the d3 selection; `.redraw()` draws it again with its draw-ins (for a step change).
- `PB.canvas(target, {aspect, label})`: a HiDPI canvas. Returns `{canvas, ctx, width(), height(), theme()}`.
- `PB.animate(target, frame, {still})`: a loop that runs only while the target is on screen; `frame(t, dt)`. With reduced motion it draws `still` once. Returns `{pause, play, reset, seek}`.
- `PB.el(tag, attrs, children)`: makes an element. `PB.reducedMotion()`: true when the reader asked for reduced motion. `PB.inApp`: true inside the Android app.

### Script: the plate

```js
PB.plate("#hero", {
  band: function (w) { return w >= 1160 ? 320 : w >= 930 ? 284 : w >= 700 ? 250 : 196; },
  label: "Illustration of the signal: a wave that rises in pitch ...",
  draw: function (p) {
    // p.print, p.key, p.live: d3 groups for the three layers
    // p.width, p.band, p.height, p.rulerY (= p.band), p.left and p.right (the text column's edges), p.theme
    var wells = PB.engrave.wells(p.key, { bodies: [{ x: 250, y: 70, m: 36 }, { x: 320, y: 40, m: 29 }], reach: 44 });
    PB.engrave.rings(p.print, { cx: 286, cy: 62, width: p.width, height: p.band, avoid: [wells.inside(60), wells.inside(76)] });
    var x = d3.scaleLinear().domain([0, 0.2]).range([p.left, p.left + 270]);
    PB.ruler(p.live, { x: x, y: p.rulerY, x2: p.width, major: [0, 0.1, 0.2], minor: 0.02, unit: "s" });
    PB.live(p.live, d, { carriage: p.rulerY, pulse: true });
  }
});
```

- `PB.plate(target, opts)`: draws a plate into `target` (the hero's `.pb-stage`, or a `.pb-bleed` inside a figure) and redraws it on resize and theme change. `band` is the print band's height (a number or a function of width; 196 on a phone), `ruler: false` leaves out the 34 px under the band for ruler labels, `below` sets that space in px instead. The print inks in along the screen angle and the print and key layers slide into register on arrival. Returns `{redraw}`.
- `PB.engrave.rings(g, opts)`: an engraved ring field: concentric rings 3.2 px apart around `cx, cy`, swelling into tapered lines where they cross the crests of a two-armed spiral, so the field reads as waves leaving a source. Fills `width` by `height`. Options: `rot` (the spiral's angle, degrees), `rmin` (no ring inside it), `k` (scale; 1 at a 390 px plate), `near: [r0, r1, w]` (every other ring between r0 and r1), `ramp: [r0, r1]` (swells grow in between these radii), `avoid: [fnBroad, fnNarrow]` (functions `(x, y)` true where no swell may be drawn). The night form comes from the theme.
- `PB.engrave.wells(g, opts)`: wells of point masses as contours only, over a ground knockout of the outer contour. `bodies: [{x, y, m}]`, `reach` (px from the heaviest body to the outer contour), `k`. Returns `{inside(r)}` for `rings`' `avoid`.
- `PB.screen(g, {tone, angle, color})`: a line screen in the SVG's defs, returned as `"url(#id)"` for a fill. `tone`: `"light"` (0.24), `"mid"` (0.46, the default), `"heavy"` (0.68), `"context"` (0.30), or a fraction. `angle`: 1 (−72 degrees, the default) or 2 (−12 degrees). `color`: `"screen"` (estimates and ranges, the default), `"plate"` (context shapes), `"ink"`. Never write a pattern by hand.

```js
svg.append("circle").attr("cx", 175).attr("cy", 146).attr("r", 56).style("fill", PB.screen(svg, { tone: "context", color: "plate" }));
```

- `PB.fillShape(g, kind, angle, make)`: a shape in a screen with its 0.9 px outline. `kind`: `"screen"`, `"weave"` (both angles at the light tone, where two estimates overlap), `"band"` (a range along a line), `"context"` (plate screen, for a familiar thing drawn for scale), `"solid"`, `"plate"`, `"live"`. `make(g)` appends the shape and returns it.

```js
PB.fillShape(svg, "context", 1, function (q) { return q.append("circle").attr("cx", 175).attr("cy", 146).attr("r", 56); });
```

### Script: the live mark

- `PB.curve(points, closed)`: a smooth path of cubic curves through `[[x, y], ...]`. A live line is one path of curves, never a polyline.
- `PB.live(g, d, opts)`: the live line from one path: the ground trap, the night halo, the core, the pen point (on its ground dot, with its night halo), and the carriage on the ruler when `carriage` is the ruler's y. It sweeps once when its figure is in view. Options: `ms` (sweep length; 1900 for a hero, 600 to 900 for a short beam), `delay`, `pulse` (the hero's pen point breathes after the sweep; nowhere else), `pen: false`, `cap` (end caps for a beam that rules off a length), `animate: false`, `label`, and `upTo: x` (draw the live part only up to x and the rest as the thin muted line not yet played; move it with `handle.set(x)`). Returns `{set(x), point(x), length, node}`.

```js
PB.live(p.live, "M26 192H236", { ms: 900, carriage: 222, cap: 5 });   // a 7 ms beam on a millisecond ruler
var h = PB.live(p.live, d, { upTo: 250 }); h.set(300);                  // played and not yet played
```

- `PB.marker(g, {x, y1, y2, trap, r, animate})`: the reported value on a band: a live beam on a ground trap with a dot on top. It drops in.
- `PB.beam(g, {x1, x2, y, cap, live})`: a 1.4 px beam with end caps for a length ("One arm, 4 km"); `live: true` for the finding's beam.

### Script: axes and charts

- `PB.ruler(g, opts)`: the one axis. `x` (a d3 scale), `y`, `major` and `minor` (arrays or steps), `labels` (default the majors), `format`, `unit` (after the last label, or at the right end with `unitAt: "end"` and `unitX`), `x1`, `x2` (the line may run past the scale, off the plate). The first label at the domain's start is set flush left. Units keep the case you write ("s", "Mpc", "SOLAR MASSES").

```js
PB.ruler(svg, { x: x, y: 44, major: [0, 200, 400, 600], minor: 50, unit: "Mpc", unitAt: "end", unitX: width });
```

- `PB.valueLines(g, {y, values, x1, x2, format, unit})`: 0.6 px reading lines across a plot, each named at its left end.
- `PB.rangeBar(target, opts)`: one value with its range on a ruler: the screened band, the live marker dropping onto it, end labels above the band. `domain`, `low`, `high`, `value`, `unit`, `major`, `minor`, `format`, `label`. With `mini: true` it is the ledger's 124 by 30 bar.

```js
PB.rangeBar("#distance", { domain: [0, 600], low: 230, high: 570, value: 410, unit: "Mpc", major: [0, 200, 400, 600], minor: 50,
  label: "Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570" });
PB.rangeBar("#distance-mini", { mini: true, domain: [0, 600], low: 230, high: 570, value: 410, label: "..." });
```

- `PB.barRows(target, opts)`: rows of segmented bars on one ruler. Each row has a `label`, a muted `note`, and `segments: [{from, to, kind, angle, figure, name}]`. `kind` as in `fillShape`; the `"live"` segment floods in, gets drop lines to the ruler, and carries its direct `name` (a `\n` breaks it). `figure` is the number set above the segment.

```js
PB.barRows("#mass", { domain: [0, 70], unit: "SOLAR MASSES", major: [0, 10, 20, 30, 40, 50, 60, 70], minor: 5,
  format: function (v) { return v % 20 === 0 ? String(v) : ""; }, label: "Data from the paper, in solar masses ...",
  rows: [
    { label: "Before", note: "two black holes", segments: [{ from: 0, to: 36, angle: 1, figure: "36" }, { from: 36, to: 65, angle: 2, figure: "29" }] },
    { label: "After", note: "one black hole, and waves", segments: [{ from: 0, to: 62, kind: "weave", figure: "62" }, { from: 62, to: 65, kind: "live", figure: "3", name: "Left as\nwaves" }] }
  ] });
```

- `PB.legend(target, items)`: the legend row. `items: [{kind, label}]` with `kind` `"live"` (the dot), `"screen"`, `"weave"`, `"band"`, `"context"`, `"line"` (1.4 px), `"thin"` (an estimate drawn as a line), `"named"`, `"point"`, `"ring"` (before), `"solid"` (after), `"errorbar"`.
- `PB.plot(target, build)`: an Observable Plot chart in the design. `build(c)` gets `{Plot, d3, theme, width, marks}` and returns Plot options. Plot draws the plain marks; the kit adds from Plot's own scales what Plot cannot draw: `ruler` (options as for `PB.ruler`), `values` (value lines), and `live: {data, x, y, label}` (the finding as the live line, with its carriage on the ruler). Plot's own axes are off; the default margins leave room for the ruler. `c.marks` gives Plot marks in the design: `line(data, {x, y, series: 2 | 3 | "estimate"})` (each on a ground trap), `dots(data, {x, y, named})`, `endLabels(data, {x, y, text, finding})`, `figure(data, {x, y, text})` (the finding's value in the display face).

```js
PB.plot("#trend", function (c) {
  return {
    height: 196, marginRight: 100, x: { domain: [0, 10] }, y: { domain: [0, 8] },
    values: { values: [2, 4.5, 7], unit: "[unit]" },
    marks: [
      c.marks.line(other, { x: "x", y: "y", series: 2 }),
      c.marks.endLabels([other[other.length - 1]], { x: "x", y: "y", text: function () { return "Other"; } })
    ],
    live: { data: finding, x: "x", y: "y", label: "..." },
    ruler: { major: [0, 5, 10], minor: 1, unit: "[unit]", unitAt: "end", unitX: c.width }
  };
});
```

Plot cannot draw the ruler, the trap under the live line, the carriage, screened fills, or end labels that avoid each other; the kit's helpers draw the first four, and labels that would collide (lines ending less than about 14 px apart) are yours to move along a leader (`.pb-leader`). For dumbbells, error bars, and bands, draw with `PB.svg` and the mark classes below, as the gallery does.

### Script: the classes for SVG marks

Use these on SVG elements so the marks follow the theme: `pb-axis-line` (0.9 px ruler), `pb-grid-line` (0.6 px grid and drop lines), `pb-leader` (0.75 px), `pb-outline` (0.9 px outline, no fill), `pb-shape` (ground fill, 0.9 px ink outline: a drawn object), `pb-beam` (1.4 px ink), `pb-ground` (the ground color, for traps and knockouts), `pb-line` (1.4 px ink line; `data-series="3"` plate ink; `data-kind="estimate"` the thin muted line), `pb-line-trap` (4.5 px ground under a line), `pb-dot` (2.1 px muted point; `data-named` 3.2 px ink), `pb-ring` (an open 4 px ring: a before value), `pb-whisker` and `pb-whisker-trap` (error bars), `pb-band` (a band's 0.6 px outline), `pb-live-beam`, `pb-live-fill`, `pb-pen`, `pb-pen-trap` (the live mark's parts), `pb-field-hair`, `pb-field-swell`, `pb-contour-line`, `pb-knockout` (plate layers), and for text `pb-tick-label`, `pb-mark-label` (a label at a mark, in caps; `data-strong` or `data-finding` heavier, `data-muted` muted), `pb-value-label`, `pb-mark-figure` (a number at a mark in the display face at 25 px).

```js
svg.append("circle").attr("class", "pb-ring").attr("cx", x(before)).attr("cy", y);
svg.append("text").attr("class", "pb-mark-label").attr("x", 0).attr("y", 12).text("Arm, 4 km");
```

The draw-in classes, for a mark you draw yourself: `pb-sweep` (on a path with `pathLength="1"`), `pb-travel` (on a mark with an `offset-path`), `pb-drop`, `pb-flood`, `pb-press` (a line of type; `--i` staggers by 50 ms), `pb-inkwipe`, `pb-register-a`, `pb-register-b`, `pb-orbit`. One per figure, on its live mark. `--pb-sweep-ms`, `--pb-sweep-delay`, and `--pb-delay` set their timing.

### Script: steps, controls, tables, readouts, numbers

- `PB.steps(root, onStep)`: scroll steps. `root` holds a `.pb-steps-visual` (the pinned figure) and `.pb-step` blocks, each a `.pb-step-n` ("Step 2 of 4") and a sentence or two. The kit writes the gauge under the pinned figure, makes a step current as it crosses the reading line (current steps in ink, the rest muted), and calls `onStep(index, el)`. Redraw the figure there (`handle.redraw()`), with one draw-in per step. Returns `{count, go(i)}`.

```html
<div class="pb-steps" id="steps">
  <div class="pb-steps-visual"><figure class="pb-fig" data-kind="illustration" data-slug="Fig. 1"><div class="pb-bleed" id="steps-plate"></div></figure></div>
  <div class="pb-step"><span class="pb-step-n">Step 1 of 4</span><p>Each detector is an L with two 4 km arms.</p></div>
  ...
</div>
```

- `PB.slider(target, opts)`: the carriage on a ruler. `label` (what it changes), `min`, `max`, `step`, `value`, `format(v)` (the current value in words, at the right of the row under it), `valueText(v)` (for screen readers), `caption` (the row's left text, default `label`), `onInput(v)`. By default the kit draws its own ruler. With `over: {left, top, width}` the input lies transparently over a ruler your figure drew (its thumb sits on the ruler at `top + 24`), and `row` names the element that takes the row. Returns `{value, set(v), input}`.

```js
PB.slider("#try", { label: "Time in the signal", min: 0, max: 1000, value: 665, row: "#try-row",
  over: { left: 14, top: 172, width: 362 },
  format: function (v) { return v < 780 ? "pitch rising" : "dying away"; }, onInput: function (v) { handle.set(20 + 0.35 * v); } });
```

- `PB.toggle(target, {label, options: [{value, label}], value, onChange})`: two or three joined segments; the chosen one is stamped with a check. `label` is shown above it. Returns `{set, value}`.
- `PB.table(target, {caption, columns: [{key, label, numeric, format}], rows, open})`: the table twin of a data figure, "The numbers", folded. Put it last in the figure. `format` may return a string or a node.
- `PB.tooltip()`: the touch readout, a small solid slab. `show({name, rows: [[quantity, value, unit]]}, at)` with `at` a pointer event or `{x, y}` in viewport px; `hide()`.
- `PB.touch(g, {x, y, rulerY})`: the marks under a readout: a ring on the touched mark, a drop line to the ruler, a tick on it. Remove the group when the finger lifts. The live mark is never used for touch.
- `PB.fmt`: `int(v)`, `fixed(digits)(v)`, `pct(v, digits)`, `compact(v)`, `minus(v)` (a real minus), and `sci(v, digits)`, which returns an element: the mantissa, the drawn multiplication sign, 10, and a real superscript. Use it where a node is allowed (`PB.table` formats, HTML); in running text type `1.0 × 10<sup>−21</sup>`.
- `PB.sign("times" | "gt")`: the drawn sign as a fragment, with the typed character for screen readers.

### Kept from kit v1

`.pb-lede` (a lead paragraph, now plain body text), `.pb-controls` (a column of controls), `.pb-stage-label` (not drawn: nothing sits on a plate), and the v1 token names `--pb-surface`, `--pb-raised`, `--pb-deemph`, `--pb-border` (all mapped to the page and its rules) still work so v1 page code runs, but a new page does not use them.

### What the kit does at load

It writes the web top bar, renders math, draws the `.pb-sign` signs and the preprint badge's frame, sets up glossary terms, holds the draw-ins of every figure below the first screen until it scrolls into view, runs the page's `PB.ready` code, sets where each head's second voice breaks, and then sets `data-pb-ready="1"` on `<html>`.
