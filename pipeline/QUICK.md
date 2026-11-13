# Quick explainers

The manual for a quick explainer: the short page one agent builds from a paper's title and abstract alone, so that every card in the feed has a picture and a page. Read this file and `quick-starter.html`, nothing else: not `AUTHORING.md`, not the kit's source, not other pages. Everything a quick page needs is here, and every code example below ran in a page that passed the render check.

## What it is

A reader taps a card and lands on a page that explains that one paper with its own picture and its own words. A full explainer (`AUTHORING.md`) is built from the full text by three agents. A quick explainer is built from the abstract by one, so it is shorter and says less, but it has the same look, the same parts, and the same honesty. Its plate is the card's image in the feed, so the plate carries the page.

## Input and output

The work folder `work/papers/<id>/` holds `candidate.json`, the scout's record. Use these fields: `title`, `abstract`, `authors`, `venue`, `published`, `status` (`preprint` or `peer_reviewed`), `url`, `field`, `hook`, `hook_turn`, `readout`, `doi`, `arxiv_id`. Write:

- `explainer/index.html`: the page, started from `pipeline/quick-starter.html`.
- `card.json`, only when the record has a `readout` that is not printed in the title or abstract: `{"readout": null}`. Publish then shows the card with no number.

The render check writes `check.json`, `shots/`, and the plates `explainer/hero.webp` and `explainer/hero-night.webp`.

## Honesty: the abstract is the only source

- Every fact, number, mechanism, and claim about this paper comes from its title or abstract. Nothing from memory, nothing from other papers, nothing guessed about the methods or data the abstract does not describe.
- Background a textbook would give is allowed, in plain words, to set up the question (what ozone is, what a proof is, what chemotaxis is). It never reads as a result of this paper.
- Every number printed on the page (prose, labels, tables, readout) is printed in the title or abstract, with its unit. Copy its precision and its range (`0.63 ± 0.19`, `around 80%`). No arithmetic: no differences, ratios, or conversions you worked out, and no endpoint of a range unless it is printed (draw `± 0.19` as a band, label it `± 0.19`). A ruler's tick values are a scale, not a claim, and may be any round numbers.
- Say it at the abstract's strength: "suggests", "in a lab", "in a model", "in this sample". If the abstract says a result challenges models, do not write that models are wrong.
- Never write what the paper does not show as if it did. The ledger says what this page could not check ("This page cannot say which models, or by how much.").
- The page says what it is built from. `data-depth="abstract"` stays on the `article`, and the ledger's last row keeps the starter's words: "Built from the paper's abstract, not its full text." The check fails without them (`missing-depth-note`).

## The page

Copy the starter and fill it in this order. Aim for 200 to 300 words in all: the dek, the key idea, the sections, and the ledger notes, not counting labels or the ledger's last row. A paragraph is one to three sentences. No em dashes, American English, plain words, active voice, sentence case.

1. **Tag row.** `.pb-tag` is the field, capitalized (`Math`, `Earth`; `cs` is `Computer science`, `social` is `Social science`). The badge is `data-status="peer_reviewed"` with the text `Peer-reviewed`, or `data-status="preprint"` with `Preprint`. The journal link is the venue's name pointing at `url`.
2. **Headline.** The `hook`, word for word, with the `hook_turn` wrapped in `<em>`. No `hook_turn`: no `<em>`. Copy the hook into `<title>` as plain text.
3. **Plate.** See "The plate". `data-kind="data"` when it plots the abstract's numbers, otherwise `data-kind="illustration"`. The plate slug says the same: `Plate 1<br>Data, from<br>the abstract` or `Plate 1<br>Illustration,<br>not to scale`.
4. **Readout row.** When the record has a `readout` printed in the abstract or title, show it: `value` in `.pb-readout` (a power of ten is `1.0<span class="pb-sign">×</span>10<sup>−21</sup>`), `unit` in `.pb-unit`, `label` in `.pb-label`. Otherwise leave the first `<div>` of the row empty (`<div></div>`) and keep the plate slug.
5. **Dek.** Two or three sentences: the finding, then one sentence that tells the reader how to read the plate.
6. **Key idea.** One sentence a reader should keep.
7. **The question.** Background, then the open question the abstract names. Fig. 1 goes here when it sets up the question; put it in the findings when it shows a result.
8. **What they did.** One to three sentences of method as the abstract states it. No figure needed.
9. **What they found.** The result, then Fig. 2.
10. **How sure is this?** The ledger. Strengths and limits come from the abstract: a proof, a sample size, an uncertainty, an agreement, a stated scope, a setting (in a lab, in simulation), what was extrapolated. The Review row is a strength for a peer-reviewed paper (note: the journal and date) and a limit for a preprint (note: not yet peer reviewed). Keep the standing row exactly as the starter has it.
11. **Why it matters.** One or two sentences, no stronger than the abstract.
12. **Source.** Title, up to six authors then "and others", venue and id, the date as "Month D, YYYY" from `published` and the review status, "Read the paper" linking `url`, and the starter's closing note.

Every head has two voices: the closing clause in `<em>`, the second voice never starting a head. Headlines state findings, with no hype and no exclamation marks. Define a term the first time it appears, in the sentence or as a tap-to-define term: `<span class="pb-term" data-def="One or two plain sentences.">hydrogen bond</span>`. Math goes in `\( ... \)`.

**Visuals: the plate and two figures.** No scroll steps. At most one control (`PB.slider` or `PB.toggle`), and only when the abstract's finding has an obvious dial, such as a quantity the paper varied and reports at several values. None of the samples needed one.

## The plate

The plate is the card's picture and the first thing on the page. It must be a real picture of this paper's finding: its subject, its mechanism, its comparison, or the shape of its result, drawn in the house style and complete as a still in both themes. Ask: could this plate sit on another paper's card? If yes, start again.

**The look.** A gray sheet with a plate engraved in one blue ink, and one vermilion line across it that the reader watches being drawn. By night the sheet is blue-black and the line is amber. Hierarchy comes from type, rules, and the one live line, never from boxes, tints, shadows, or colored edges. The kit gives night its colors; never write a hex color, never draw a night version.

**Three layers.** `PB.plate` hands `draw(p)` three groups, back to front:

- `p.print`: the engraving in plate ink. Draw the paper's subject as a field of lines: the sea, terrain, a flow, a density, a barrier. Use `engrave()` from the starter (contours of any function), `PB.engrave.rings` (waves leaving a source), or a line screen fill (`PB.screen`). Never a pattern that means nothing.
- `p.key`: the subject's outlines in black (`pb-contour-line`) over ground knockouts (`pb-knockout`): bodies, profiles, a horizon, a curve to compare against.
- `p.live`: the ruler, labels, and the one live line (`PB.live`), drawn last.

**One live mark.** The vermilion line marks only the finding: the value the paper reports, the range it proves, the path that wins. Everything else is ink, plate ink, or screen. A ruler and carriage go under the plate only when the live line is really plotted along that quantity; otherwise pass `ruler: false` and draw no axis (the pen point leads alone).

**Labels sit on the plate at their marks, on a knockout:** use the starter's `label()`. Mark labels are set in capitals, so write units in words or keep their case with `{ asIs: true }` (`m/day` would read `M/DAY`, meters turned into mega). Lowercase Greek keeps its case by itself. In labels, write chemistry in words ("IODIDE + ONE WATER"), not `I⁻·H₂O`: raised and lowered characters are redrawn after `label()` sizes its knockout. Keep plate labels to a few words; the dek explains.

**Pick a form.** Each sample below passed the check and was looked at in both themes.

### Form A: values on one ruler, over a picture of the subject (data)

For a few numbers in one unit. Here the land and the sea, each sink's average uptake as a line from zero with its stated range screened; the ocean's line is the finding. (Science, carbon sinks.)

```js
var OCEAN = { v: 2.8, e: 0.4 }, LAND = { v: 1.0, e: 0.5 };
PB.plate("#hero", {
  band: function () { var v = window.innerWidth; return v >= 1160 ? 400 : v >= 930 ? 360 : v >= 700 ? 320 : 272; },
  label: "Data from the abstract, on one ruler in petagrams of carbon a year. Above the horizon, the land: 1.0, plus or minus 0.5. Below, the ocean: 2.8, plus or minus 0.4.",
  draw: function (p) {
    var x = d3.scaleLinear().domain([0, 4]).range([p.left, p.right]);
    var hz = Math.round(p.band * 0.4), yl = Math.round(hz * 0.58), yo = Math.round(hz + (p.band - hz) * 0.5);
    engrave(p.print, function (a, b) { return Math.sin(a / 47 + 0.6) * Math.cos(b / 23 - 0.4) + 0.7 * Math.sin((a + 2 * b) / 71) + b / 90; },
      { x0: 0, y0: 0, x1: p.width, y1: hz, levels: d3.range(-2, 3, 0.16) });                       // hills
    engrave(p.print, function (a, b) { return b + 2.6 * Math.sin(a / 13 + b / 7) * (0.4 + (b - hz) / (p.band - hz)); },
      { x0: 0, y0: hz, x1: p.width, y1: p.band, levels: d3.range(hz - 6, p.band + 12, 3.6) });      // swell
    p.key.append("line").attr("class", "pb-contour-line").style("stroke-width", "1.4px").attr("x1", 0).attr("x2", p.width).attr("y1", hz).attr("y2", hz);
    [[yl, x(LAND.v + LAND.e) + 6], [yo, x(OCEAN.v + OCEAN.e) + 6]].forEach(function (r) {
      p.key.append("rect").attr("class", "pb-knockout").attr("x", 0).attr("y", r[0] - 13).attr("width", r[1]).attr("height", 26);
    });
    [[LAND, yl], [OCEAN, yo]].forEach(function (r) {
      PB.fillShape(p.live, "screen", 1, function (q) { return q.append("rect").attr("x", x(r[0].v - r[0].e)).attr("y", r[1] - 8).attr("width", x(r[0].v + r[0].e) - x(r[0].v - r[0].e)).attr("height", 16); });
    });
    p.live.append("line").attr("class", "pb-line-trap").attr("x1", x(0)).attr("x2", x(LAND.v)).attr("y1", yl).attr("y2", yl);
    p.live.append("line").attr("class", "pb-beam").attr("x1", x(0)).attr("x2", x(LAND.v)).attr("y1", yl).attr("y2", yl);
    p.live.append("circle").attr("cx", x(LAND.v)).attr("cy", yl).attr("r", 4).style("fill", "var(--pb-ink)");
    PB.ruler(p.live, { x: x, y: p.rulerY, x1: 0, x2: p.width, major: [0, 1, 2, 3, 4], minor: 0.25, labels: [0, 1, 2], unit: "Pg C A YEAR", unitAt: "end", unitX: p.right });
    label(p.live, p.left, yl - 20, "LAND", { strong: true });
    label(p.live, x(LAND.v + LAND.e) + 10, yl - 3, "1.0 ± 0.5");
    label(p.live, x(LAND.v + LAND.e) + 10, yl + 11, "NO ROBUST TREND", { muted: true });
    label(p.live, p.left, hz + 20, "OCEAN", { strong: true });
    label(p.live, x(OCEAN.v + OCEAN.e) + 8, yo - 3, "2.8 ± 0.4");
    label(p.live, p.left, yo + 30, "RISING 0.63 EACH DECADE", { finding: true });
    PB.live(p.live, "M" + x(0) + " " + yo + "H" + x(OCEAN.v), { carriage: p.rulerY, pulse: true });
  }
});
```

### Form B: a threshold or a range on a ruler, over a drawing of the mechanism (illustration)

For a proof, a limit, or a regime: the ruler carries the abstract's exact values, the drawing above it is a sketch, so the plate is an illustration. Here a fluid (contours of a grid of eddies), clumps of cells as density profiles standing on a ruler of total mass, and the live line over every mass the proof covers. (arXiv, Keller-Segel.)

```js
var piLabel = function (v) { return v === 0 ? "0" : (v === 1 ? "" : v) + "π"; };
function bump(g, cx, s, a, y0) {   // a density profile with nested contours over a knockout
  var pts = function (k) {
    var out = [], w = s * Math.sqrt(Math.log(a / 0.5));
    for (var xx = cx - w; xx <= cx + w; xx += 1.5) out.push([xx, y0 - k * a * Math.exp(-Math.pow((xx - cx) / s, 2))]);
    return out;
  };
  var outer = pts(1);
  g.append("path").attr("class", "pb-knockout").attr("d", d3.line()(outer.concat([[outer[outer.length - 1][0], y0 + 2], [outer[0][0], y0 + 2]])) + "Z");
  [0.25, 0.5, 0.75].forEach(function (k) { g.append("path").attr("class", "pb-contour-line").style("stroke-width", "0.6px").attr("d", d3.line()(pts(k))); });
  g.append("path").attr("class", "pb-contour-line").style("stroke-width", "1.3px").attr("d", d3.line()(outer));
}
PB.plate("#hero", {
  band: function () { var v = window.innerWidth; return v >= 1160 ? 400 : v >= 930 ? 360 : v >= 700 ? 320 : 272; },
  label: "Illustration on a ruler of total mass. A fluid stirs the field. Clumps of cells stand on a bright line from 0 to 4π, every mass the proof covers. A ring marks 2π, where a 2020 result stopped.",
  draw: function (p) {
    var x = d3.scaleLinear().domain([0, 6]).range([p.left, p.right]), base = p.band - 56, cell = 0.3 * p.band;
    engrave(p.print, function (a, b) { return Math.sin(Math.PI * (a + 0.35 * cell) / cell) * Math.sin(Math.PI * (b + 0.2 * cell) / cell); },
      { x0: 0, y0: 0, x1: p.width, y1: p.band, levels: d3.range(-0.92, 0.93, 0.115).filter(function (l) { return Math.abs(l) > 0.05; }) });
    bump(p.key, x(1), 0.05 * p.width + 6, 0.13 * p.band, base);
    bump(p.key, x(2.95), 0.04 * p.width + 4, 0.27 * p.band, base);
    bump(p.key, x(5), 0.012 * p.width + 2, 3 * p.band, base);     // runs off the top: blow-up
    PB.ruler(p.live, { x: x, y: p.rulerY, x1: 0, x2: p.width, major: [0, 2, 4], minor: [1, 3, 5, 6], format: piLabel, unit: "TOTAL MASS", unitAt: "end", unitX: p.right });
    label(p.live, x(1), base - 0.13 * p.band - 10, "CLUMPS OF CELLS", { anchor: "middle", strong: true });
    label(p.live, x(5) - 12, 44, "WITHOUT FLUID,", { anchor: "end" });
    label(p.live, x(5) - 12, 58, "SOME BLOW UP", { anchor: "end" });
    label(p.live, x(5) - 12, 72, "ABOVE 4π", { anchor: "end" });
    label(p.live, x(2), base - 12, "2020: 2π", { anchor: "middle" });
    label(p.live, p.left, base + 22, "PROVED: BOUNDED BELOW 4π", { finding: true });
    PB.live(p.live, "M" + x(0) + " " + base + "H" + x(4), { carriage: p.rulerY, cap: 5, pulse: true });
    p.live.append("circle").attr("class", "pb-ring").attr("cx", x(2)).attr("cy", base);
  }
});
```

### Form C: a mechanism with no axis (illustration)

For a "how": a path, a barrier, a before and after. No ruler, no numbers on the drawing; the plate says only what the abstract says (here: which barrier is lower). Bare iodide's energy climb is an engraved mountain, the path with one water molecule crosses lower, and the reacting ions sit at the start. (JACS, iodide and ozone.)

```js
function atom(g, cx, cy, r) {   // an engraved ball
  g.append("circle").attr("class", "pb-knockout").attr("cx", cx).attr("cy", cy).attr("r", r + 2);
  for (var k = 0.3; k < 1; k += 0.22) g.append("circle").attr("class", "pb-contour-line").style("stroke-width", "0.6px").attr("cx", cx - r * 0.25 * (1 - k)).attr("cy", cy - r * 0.25 * (1 - k)).attr("r", r * k);
  g.append("circle").attr("class", "pb-contour-line").style("stroke-width", "1.3px").attr("cx", cx).attr("cy", cy).attr("r", r);
}
PB.plate("#hero", {
  band: function () { var v = window.innerWidth; return v >= 1160 ? 400 : v >= 930 ? 360 : v >= 700 ? 320 : 272; },
  ruler: false,
  label: "Illustration, not to scale: bare iodide climbs a high energy barrier, drawn as an engraved mountain. Iodide carrying one water molecule crosses a lower barrier, the bright line.",
  draw: function (p) {
    var W = p.right - p.left, y0 = p.band * 0.8, X = function (u) { return p.left + W * u; };
    function path(h, peak) {
      return d3.range(0, 1.0001, 0.02).map(function (u) {
        return [X(u), y0 - h * Math.exp(-Math.pow((u - peak) / 0.17, 2)) + 6 * Math.exp(-Math.pow(u / 0.08, 2))];
      });
    }
    var high = path(p.band * 0.62, 0.5), low = path(p.band * 0.3, 0.52), hi = PB.curve(high);
    p.print.append("path").attr("d", hi + "L" + p.width + " " + p.band + "L0 " + p.band + "L0 " + high[0][1] + "Z").style("fill", PB.screen(p.print, { tone: "context", color: "plate", angle: 2 }));
    for (var k = 1; k <= 5; k++) {
      var ridge = path(p.band * 0.62 * (1 - k * 0.16), 0.5).map(function (q) { return [q[0], q[1] + k * 4]; });
      p.print.append("path").attr("class", "pb-field-hair").style("stroke-width", "0.9px").attr("d", PB.curve(ridge));
    }
    p.key.append("path").attr("class", "pb-line-trap").attr("d", hi);
    p.key.append("path").attr("class", "pb-line").style("stroke-width", "1.6px").attr("d", hi);
    var ix = X(0.06), iy = y0 - 44;
    atom(p.key, ix, iy, 15); atom(p.key, ix + 23, iy - 15, 7); atom(p.key, ix + 32, iy - 23, 3.6); atom(p.key, ix + 31, iy - 7, 3.6);
    label(p.live, p.left, 22, "HIGHER = MORE ENERGY", { muted: true });
    label(p.live, X(0.5), y0 - p.band * 0.62 - 10, "BARE IODIDE", { anchor: "middle", strong: true });
    label(p.live, X(0.52), y0 - p.band * 0.3 - 26, "WITH ONE WATER:", { anchor: "middle", finding: true });
    label(p.live, X(0.52), y0 - p.band * 0.3 - 12, "A LOWER PASS", { anchor: "middle" });
    label(p.live, p.left, iy - 34, "IODIDE + ONE WATER", { strong: true });
    label(p.live, X(1), y0 + 30, "ON TO IO⁻", { anchor: "end", strong: true });
    PB.live(p.live, PB.curve(low), { pulse: true });
  }
});
```

**Pictures for the print, by subject** (each a function for `engrave`, tested in the forms above): a sea surface `b + A * sin(a / 13 + b / 7)` with levels every 3.6 px; terrain, a sum of slow sines and cosines with levels every 0.16; a stirring flow, `sin(πa / L) * sin(πb / L)` with levels every 0.115; a barrier or a peak, its profile filled with `PB.screen(g, { tone: "context", color: "plate" })` and echoed by lower copies. For waves leaving a source use `PB.engrave.rings(p.print, { cx, cy, width: p.width, height: p.band })`.

**Sizes.** On a phone the plate is 390 px wide; `p.left` and `p.right` are the text column's edges (20 and 370). `band` 272 on a phone leaves room for a picture and three or four labels. The ruler sits at `p.rulerY` (the band's bottom) with 34 px of labels under it.

## The two figures

Fig. 1 sets up the question or the subject; Fig. 2 shows the result a second way, not the plate again. When the abstract gives numbers, at least one figure is `data-kind="data"` with its table; when it gives none worth drawing, both are illustrations. Every figure has a `data-slug` (`Fig. 1`, `Fig. 2`), a title in `.pb-fig-title` (or a stat), and a one-sentence `figcaption`. A data figure's caption says the numbers are from the abstract and what the head row does not say.

**Shares of a whole, or how far each result reached:** `PB.barRows` (one row is one segmented bar; several rows share a ruler). Segment kinds: `live` (the finding, one per figure), `solid` (an exact or earlier value), `screen` (an estimate or a conjecture), `context` (the rest). `figure` is the number set above a segment. Leave a remainder without a number when the abstract gives none.

```js
PB.barRows("#fig1", {
  domain: [0, 100], unit: "%", major: [0, 50, 100], minor: 10,
  label: "Data from the abstract: of fossil emissions from 1990 to 2019, the ocean took up 35 percent and the land 13 percent.",
  rows: [{ label: "Fossil emissions", note: "1990 to 2019", segments: [
    { from: 0, to: 35, kind: "live", figure: "35" },
    { from: 35, to: 48, kind: "screen", angle: 2, figure: "13" },
    { from: 48, to: 100, kind: "context" }] }]
});
PB.legend("#fig1-legend", [{ kind: "live", label: "Ocean" }, { kind: "screen", angle: 2, label: "Land" }, { kind: "context", label: "The rest" }]);
PB.table("#fig1-table", {
  caption: "Share of fossil emissions taken up, 1990 to 2019.",
  columns: [{ key: "what", label: "Sink" }, { key: "v", label: "Percent", numeric: true }],
  rows: [{ what: "Ocean", v: "35" }, { what: "Land, net", v: "13" }]
});
```

```js
var piLabel = function (v) { return v === 0 ? "0" : (v === 1 ? "" : v) + "π"; };
PB.barRows("#fig2", {
  domain: [0, 4], unit: "MASS", major: [0, 2, 4], minor: [1, 3], format: piLabel,
  label: "Data from the abstract. A 2020 result covered masses below 2π. A 2024 conjecture from simulations put the threshold at 4π. This paper proves every mass below 4π.",
  rows: [
    { label: "2020", note: "proved below", segments: [{ from: 0, to: 2, kind: "solid", figure: "2π" }] },
    { label: "2024", note: "simulations suggest", segments: [{ from: 0, to: 4, kind: "screen", figure: "4π" }] },
    { label: "This paper", note: "proved below", segments: [{ from: 0, to: 4, kind: "live", figure: "4π" }] }
  ]
});
PB.legend("#fig2-legend", [{ kind: "live", label: "This proof" }, { kind: "screen", label: "From simulations" }]);
```

**One number with its stated range:** a stat over a band. The figure's HTML is `<div class="pb-stat"><div class="pb-stat-value">0.63</div><div class="pb-stat-label"><b>Added each decade</b>to the ocean's yearly uptake, in Pg&nbsp;C</div></div>` followed by `<div id="fig2"></div><div id="fig2-legend"></div><div id="fig2-table"></div>`.

```js
var RISE = { v: 0.63, e: 0.19 };
PB.svg("#fig2", { height: 92, label: "Data from the abstract: the ocean sink rose by 0.63 petagrams of carbon a year each decade, plus or minus 0.19." }, function (svg, s) {
  var x = d3.scaleLinear().domain([0, 1]).range([0.5, s.width - 70]), y = 34, ry = 58;
  PB.fillShape(svg, "screen", 1, function (q) { return q.append("rect").attr("x", x(RISE.v - RISE.e)).attr("y", y - 8).attr("width", x(RISE.v + RISE.e) - x(RISE.v - RISE.e)).attr("height", 16); });
  svg.append("line").attr("class", "pb-grid-line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", y).attr("y2", ry);
  PB.live(svg, "M" + x(0) + " " + y + "H" + x(RISE.v), { ms: 900, carriage: ry, cap: 5 });
  label(svg, x(RISE.v + RISE.e) + 8, y + 4, "± 0.19");
  PB.ruler(svg, { x: x, y: ry, major: [0, 0.5, 1], minor: 0.1, labels: [0, 0.5], unit: "Pg C A YEAR", unitAt: "end", unitX: s.width });
});
PB.legend("#fig2-legend", [{ kind: "live", label: "Rise per decade" }, { kind: "screen", label: "Its range" }]);
```

**Two values compared, one with a stated error:** bars from zero with a whisker.

```js
PB.svg("#fig2", { height: 206, label: "Data from the abstract: with one water molecule, iodide reacts 23 times faster than bare iodide, give or take 6." }, function (svg, s) {
  var x = d3.scaleLinear().domain([0, 30]).range([0.5, s.width - 50]), ry = 172;
  var rows = [{ y: 56, name: "Bare iodide", note: "the reference", v: 1, kind: "solid", fig: "1" }, { y: 134, name: "With one water", note: "measured", v: 23, kind: "live", fig: "23" }];
  rows.forEach(function (r) {
    var head = svg.append("text").attr("class", "pb-mark-label").attr("x", 0).attr("y", r.y - 32);
    head.append("tspan").attr("data-strong", "").style("font-weight", 600).text(r.name);
    head.append("tspan").attr("dx", 8).style("fill", "var(--pb-ink-2)").text(r.note);
    var shape = PB.fillShape(svg, r.kind, 1, function (q) { return q.append("rect").attr("x", x(0)).attr("y", r.y - 10).attr("width", x(r.v) - x(0)).attr("height", 20); });
    if (r.kind === "live") shape.fills.forEach(function (f) { f.attr("class", "pb-flood"); });
    if (r.v < 3) svg.append("text").attr("class", "pb-mark-figure").attr("x", x(r.v) + 8).attr("y", r.y + 9).text(r.fig);
    else svg.append("text").attr("class", "pb-mark-figure").attr("x", x(r.v)).attr("y", r.y - 16).attr("text-anchor", "middle").text(r.fig);
  });
  var wy = 134;
  svg.append("line").attr("class", "pb-whisker-trap").attr("x1", x(17)).attr("x2", x(29)).attr("y1", wy).attr("y2", wy);
  var w = svg.append("g").attr("class", "pb-whisker");
  w.append("line").attr("x1", x(17)).attr("x2", x(29)).attr("y1", wy).attr("y2", wy);
  [17, 29].forEach(function (v) { w.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", wy - 6).attr("y2", wy + 6); });
  label(svg, x(29) + 6, wy + 4, "± 6");
  PB.ruler(svg, { x: x, y: ry, major: [0, 10, 20, 30], minor: 5, labels: [0, 10, 20], unit: "TIMES", unitAt: "end", unitX: s.width });
});
```

**A drawing of the subject (illustration):** `PB.svg` with marks from the classes below. Cells drifting toward the chemical they release, while a fluid sweeps across:

```js
PB.svg("#fig1", { height: 236, label: "Illustration: cells around a cloud of the chemical they release, each with a short arrow toward its center, while streamlines of a fluid sweep across them." }, function (svg, s) {
  var cx = s.width * 0.46, cy = 128;
  for (var i = 0; i < 4; i++) {
    var y0 = 206 + 9 * i;
    var line = PB.curve(d3.range(0, 1.001, 0.05).map(function (u) { return [u * s.width, y0 - 150 * Math.pow(u, 1.6) - 6 * i * u]; }));
    svg.append("path").attr("class", "pb-line").attr("data-series", "3").style("stroke-width", "0.9px").attr("d", line);
  }
  PB.fillShape(svg, "context", 1, function (q) { return q.append("ellipse").attr("cx", cx).attr("cy", cy).attr("rx", 84).attr("ry", 66); });
  [66, 48, 30, 13].forEach(function (r) { svg.append("ellipse").attr("class", "pb-contour-line").style("stroke-width", "0.9px").attr("cx", cx).attr("cy", cy).attr("rx", r * 84 / 66).attr("ry", r); });
  var rng = d3.randomLcg(4), first = null;
  for (var n = 0; n < 32; n++) {
    var a = rng() * 2 * Math.PI, r = 0.35 + rng() * 0.95, px = cx + 84 * r * Math.cos(a) * 1.15, py = cy + 66 * r * Math.sin(a) * 1.05;
    if (px < 10 || px > s.width - 10 || py < 34 || py > 214) continue;
    var dx = cx - px, dy = cy - py, l = Math.hypot(dx, dy);
    svg.append("circle").attr("cx", px).attr("cy", py).attr("r", 6).attr("class", "pb-ground");
    svg.append("line").attr("class", "pb-beam").attr("x1", px).attr("y1", py).attr("x2", px + 12 * dx / l).attr("y2", py + 12 * dy / l);
    svg.append("circle").attr("cx", px).attr("cy", py).attr("r", 3.2).style("fill", "var(--pb-ink)");
    if (!first || px < first[0]) first = [px, py];
  }
  label(svg, cx, 16, "THE CHEMICAL THEY RELEASE", { anchor: "middle", strong: true });
  label(svg, s.width - 2, 22, "FLUID FLOW", { anchor: "end", strong: true });
  label(svg, first[0], first[1] - 12, "CELLS", { anchor: "middle", strong: true });
});
```

## Kit reference: what a quick page uses

The starter loads the kit and wraps the code in `PB.ready(function () { ... })`; keep both. Draw with the classes and `var(--pb-...)` tokens, never hex colors.

- `PB.plate(target, {band, ruler, below, label, draw(p)})`: the hero plate (above). `p`: `print`, `key`, `live` (d3 groups), `width`, `band`, `height`, `rulerY`, `left`, `right`. `ruler: false` drops the 34 px under the band.
- `PB.svg(target, {height, label}, draw(svg, s))`: a responsive SVG figure, `s.width` and `s.height`. The kit clears and redraws it on resize and theme change.
- `PB.ruler(g, {x, y, major, minor, labels, format, unit, unitAt: "end", unitX, x1, x2})`: the one axis. With `unitAt: "end"` the unit is set right at `unitX`; leave the last tick or two unlabeled (`labels: [...]`) so no label lands under the unit.
- `PB.live(g, d, {pulse, carriage, cap, ms, label})`: the live line from one path (`PB.curve(points)` for a curve, `"M x y H x2"` for a straight beam). `pulse` on the plate only. `carriage: rulerY` only when the line is plotted along that ruler.
- `PB.fillShape(g, kind, angle, make)`: a shape with a fill and an outline; kinds `screen`, `band`, `context`, `weave`, `solid`, `plate`, `live`. `PB.screen(g, {tone, color, angle})` gives a line screen to use as a fill.
- `PB.barRows`, `PB.legend(target, [{kind, label}])`, `PB.table(target, {caption, columns, rows})`: as in the examples. A legend only for two or more kinds of mark, never repeating a mark that has a label.
- `PB.engrave.rings(g, {cx, cy, width, height, rmin})`: rings of waves leaving a source.
- `PB.curve(points)`: a smooth path through `[[x, y], ...]`.
- `PB.slider(target, {label, min, max, step, value, format, onInput})` and `PB.toggle(target, {label, options: [{value, label}], value, onChange})`: the one optional control.
- Starter helpers: `label(g, x, y, text, {anchor, strong, finding, muted, asIs})` and `engrave(g, f, {x0, y0, x1, y1, levels, step})`.
- SVG classes: `pb-contour-line` (key outline), `pb-knockout` and `pb-ground` (ground fills), `pb-field-hair` (plate-ink line), `pb-line` (1.4 px ink line; `data-series="3"` plate ink), `pb-line-trap` (ground under a line), `pb-beam`, `pb-grid-line`, `pb-outline`, `pb-shape`, `pb-ring` (an open ring), `pb-dot` (`data-named` for a larger dot), `pb-whisker` and `pb-whisker-trap`, `pb-mark-figure` (a number in the display face), `pb-mark-label` (with `data-strong`, `data-finding`, `data-muted`), `pb-flood` (the live fill's draw-in).
- In HTML: a unit with a space in it takes `&nbsp;` (`Pg&nbsp;C`) so it never breaks across lines; a minus sign is `−`; a power of ten is `10<sup>−21</sup>`.

## Steps, and what to spend

1. Read this file, `pipeline/quick-starter.html`, and the work folder's `candidate.json`. Read nothing else.
2. From the abstract, decide: the one finding; the plate's form and its picture; the two figures; which numbers the page will print. If the record's `readout` is not printed in the title or abstract, write `card.json` as `{"readout": null}` and leave the readout row's first `<div>` empty.
3. Copy the starter to `explainer/index.html` and fill it in one pass: words, then the plate, then the figures. Delete every placeholder.
4. Run the check from `pipeline/`: `uv run paperboy-pipeline check --explainer ../work/papers/<id>/explainer --kit ../kit`. Fix what it names until it exits 0.
5. Look once: open `explainer/hero.webp` and `explainer/hero-night.webp` (the card images), then each `shots/light-NN.png` (usually four). Not the dark, still, or still-dark shots: the plates already show night, and a page drawn with the kit's classes cannot differ there. Fix clipped or overlapping labels, a plate that reads as generic, a figure that does not teach. Run the check again and look at both plates and the shot you changed. Stop after two looks.
6. Before replying: `grep -n '\[' explainer/index.html` finds no placeholder left (a `[` in code is fine); every number on the page is in the abstract or title; the ledger's last row is the starter's.
