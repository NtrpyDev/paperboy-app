# Paperboy design brief: First Light

Read `design/CONTEXT.md` and `design/CONTENT.md` first. They are the spec. This brief sets the direction inside that spec. Where this brief and CONTEXT.md disagree, CONTEXT.md wins.

The owner asked for a fusion of mockup A (Late Edition) and mockup B (Night Lab), with better fonts, better graphics, and better animations, at an award-winning level. He hates boxes with a colored left edge and he called the first draft bland. This brief answers those four things.

## 1. The idea in three sentences

Every Paperboy screen is a printed sheet that is still receiving a signal. The sheet is print: big editorial type and ink built from line screens, heavy and still. One hair-thin line per view is alive, drawing the paper's own finding in real time, as wet ink by day and as light by night.

The language is called **First Light**. "First light" is the astronomy term for the first time a new instrument records an image, and it sits where A's "Late Edition" sat: an edition name. It is an internal name for the design language. It is not approved product copy.

**The one unforgettable thing: the live line.** Heavy printed mass, and across it a single precise line that moves. If a viewer remembers one thing, it is that line.

## 2. What was weak in A and B (seen in the renders)

Renders are in `design/shots/director/` (`Main-390w-light-t4.png`, `B-Night-Lab-390w-light-t4.png`).

### A, Late Edition

Keep: front-page hierarchy, the headline as the hero, spot inks, hard rules, the feeling of a physical sheet.

Weak:

- Anton in all caps. Every headline shouts at the same volume, with no italic and no second voice.
- The top strap wraps into two ragged two-line columns at 390 px.
- The overprint is uncontrolled. Yellow multiplied on blue turned dark olive green. Four saturated colors at equal strength, so nothing leads.
- The "halftone" is a uniform dot grid. Every dot is the same size, so it carries no tone and reads as polka dots. The same dot texture runs behind the body text.
- The black holes read as cartoon eyes. The rotated "FREE" and "3 SUNS" stickers are gimmicks.
- The chirp is a 2.5 px polyline with visible corners. It looks like data but is a drawing, and nothing says so.
- No motion. There are no `@keyframes` in the file.
- The rating controls are a bare plus and a bare minus with no visible meaning.

### B, Night Lab

Keep: the signal itself is the hero, the large readouts, the calm precision, one luminous line on a dark ground.

Weak:

- Space Grotesk with JetBrains Mono is the default developer-tool pairing. The headline has no drama.
- Acid lime on neutral near-black over a grid is the stock dashboard look. The grid runs behind all the text.
- A rounded bordered panel and rounded buttons: the generic card.
- The trace is one polyline stretched 2.4 times vertically, so its left half shows stair steps and its stroke thins unevenly. The glow is a CSS drop shadow.
- The dashed "merger" line runs through the plus sign of the "36 + 29" readout.
- The plot has no axis, no unit, and no label saying whether it is data or a drawing.
- Categories are told apart by hue alone (lime Physics, cyan Biology).
- No motion. No day theme was designed.

## 3. Principles

1. **Print is still. Signal moves.** Type, ink shapes, rules, and labels never loop. Only the live line is alive.
2. **One live line per view.** Never two. If a screen has a hero trace, nothing else on that screen animates continuously.
3. **Ink by day, light by night.** Day is subtractive: inks on paper, overlaps get darker. Night is additive: light on a dark ground, overlaps get brighter. Same geometry, opposite physics.
4. **Tone comes from line screens, not from gray.** A lighter tone is a thinner line in the screen or a second ink. Never black at reduced opacity for a fill.
5. **Solid means sure. Screened means not yet sure.** Solid ink is measured or peer reviewed. A line-screen fill is a range, an estimate, or a preprint. This holds in badges, charts, and the "how sure" section.
6. **Every mark has a job.** A registration cross points at something. A tick scale is a real axis. A color bar is the legend. No decorative readouts, no fake coordinates.
7. **The headline is the hero's equal.** Sentence case, large, tight, with a real italic or a real second weight for a second voice. Drama comes from type scale and contrast, not from stickers.
8. **Nothing sits behind reading text.** No grid, no dots, no grain under a headline or a paragraph.
9. **Say what a picture is.** Every figure carries a slug: `DATA, FROM THE PAPER` or `ILLUSTRATION, NOT TO SCALE`. The chirp shape in the mockups is an illustration. Only the labeled numbers from CONTENT.md are data.

## 4. Day and night

Night is designed, not inverted. The composition changes emphasis.

| | Day: the sheet | Night: the light table |
|---|---|---|
| Ground | Paper stock, a toned white | A deep dark with a hue (blue-black, indigo, or green-black), never neutral gray |
| Reading order | Mass first. Ink shapes and the headline carry the page, the line is a hot accent | Line first. The print layer goes dim and structural, the line carries the picture |
| Overlaps | Multiply. The overlap color is named in the palette and must look intended | Screen. Two lights overlapping go toward white |
| The live line | Solid ink, 1.5 to 2 px, with a pen point at its tip | A bright core 1.25 to 1.75 px over a wider soft halo of the same hue |
| Glow | None | Only on the live line and its pen point. Never on chrome, buttons, or text |
| Text | Ink on stock | Light on ground. Hairline serifs get one weight step heavier than day |
| Print layer | Full strength | A structure color about 3:1 on the ground, plus a quieter texture color for non-essential lines |

Build the halo as a second, wider stroke of the same path at 15 to 25 percent opacity under the core stroke. Do not use blur filters or `drop-shadow` for it.

## 5. Graphic language

### The plate

Every hero is a plate. A plate bleeds to both screen edges or off one edge. It is never a rounded, bordered panel.

A plate holds, at most:

- one print layer: shapes filled with line screens in one or two inks;
- the live line;
- one large readout number with its unit and what it measures;
- one slug in mono caps saying what the picture is;
- two direct labels with thin leader lines.

### Line screens

- A fill is parallel lines. Pitch 3 to 4 px. Tone is the line weight: light is about a quarter of the pitch, mid about half, heavy about two thirds. Show at least two tones in a plate so the screen reads as tone and not as stripes.
- Two inks use two angles that differ by about 60 degrees (for example 15 and 75) so their overlap makes a clean weave.
- In SVG this is a `<pattern>` with `patternTransform="rotate(...)"` holding one `<rect>`. This is confirmed working in the local renderer.
- Dot halftones are allowed only with three or more dot sizes that show a real gradient. A uniform dot grid is banned.

### The live line

- One continuous path. Smooth: cubic curves, or samples no more than 1.5 px apart with round joins and round caps. No visible corners.
- Never scale a stroked path unevenly. Bake the amplitude into the path data.
- It always ends in a pen point: a small filled dot at the leading end.
- For a paper with no waveform, the live line is the single path that carries the finding. AlphaFold: the measured distance being ruled off, or a chain folding. M87: the ring being drawn.

### Marks

Registration cross, trim ticks at plate corners, tick scale, color bar, plate number slug. Use at most three kinds on a screen, and only where they do a job. None on the left edge of a text block.

### Charts

The rules in CONTEXT.md hold. In addition:

- The axis is a ruler: ticks sit on the axis line, outside the plot.
- Grids are solid hairlines, 0.5 to 0.75 px, in the muted color, and stay inside the plot.
- The measured value is solid. A range is a line-screen band. Use the distance figure (410, range roughly 230 to 570 megaparsecs) to show this.
- The series that matters is the live line. Every other series is print.
- Labels sit at the point, horizontal, in the text color, with a leader line if needed. Never in the series color.
- Typeset numbers properly: a real multiplication sign and superscript for 1.0 × 10⁻²¹, a real minus sign, tabular figures in columns, units smaller than the number.

### Diagrams

Plotter drawings: one line weight, plan or elevation views, no perspective tricks, no flat fills. The interferometer is an L with two 4 km arms, drawn as lines, labeled.

### Icons and controls

Inline stroke SVG, 1.5 px, square ends. Buttons are solid ink slabs or ruled outlines with square corners or a radius of 2 px at most. "More like this" and "Less like this" must be understandable without a legend: show the words, at least once.

## 6. Motion language

Three verbs. Nothing bounces. A press and an instrument do not overshoot.

| Verb | What it does | Duration | Easing |
|---|---|---|---|
| **Press** | Print matter lands: opacity 0 to 1 with a 6 px rise or a scale from 1.015 to 1 | 160 to 220 ms, lines staggered 40 to 60 ms, at most 4 steps | `cubic-bezier(0.2, 0, 0, 1)` |
| **Register** | The plate's two ink layers start a few px apart (about 5 px in x, 3 px in y, opposite directions) and slide into exact register | 420 to 520 ms | `cubic-bezier(0.16, 1, 0.3, 1)`, no overshoot |
| **Sweep** | The live line draws from start to end at constant speed, pen point leading | 1400 to 2200 ms for a hero, about 200 px per second | `linear`. Instruments sweep at a constant rate |

Rules:

- Order on arrival: headline and summary are readable within 200 ms. Register runs 0 to 500 ms. Sweep starts at about 300 ms. Everything rests by 2.6 s.
- After the sweep, the pen point may pulse slowly (opacity 1 to 0.55, 2.4 s period). That is the only infinite animation allowed on a screen.
- A rating tap is a stamp: 120 ms, scale 1.1 to 1, the fill floods in.
- Feed to explainer: the plate stays put and the sheet feeds up under it, 360 ms, Press easing. Show it as frames if you show it.
- Draw the line with `pathLength="1"`, `stroke-dasharray: 1`, and a `stroke-dashoffset` keyframe from 1 to 0. This is confirmed working in the local renderer. Animate the night halo with the same keyframe, or it shows as a ghost of the whole line before the core arrives.
- Design the resting frame first. A reduced-motion user sees only that frame: plates in register, line fully drawn, pen point parked at the end. It must be complete and beautiful as a still.
- Check start, middle, and rest with `--frames 0.2,1.2,3`.

## 7. Key idea, caveat, analogy, and "how sure is this"

Four kinds of content, four different forms. None is a box. None has a rule, bar, stripe, or tint on a side edge, in any color. They are told apart by form, not by a colored container.

| Content | Form | How it is set |
|---|---|---|
| **Key idea** | Type at scale | One sentence in the display face or its italic, 26 to 34 px on a phone, full measure, with at least 40 px of space above and below. A mono slug above it. Nothing around it. One angle may instead reverse it out of a full-bleed ink band that touches both screen edges. |
| **Caveat** | A note | A dagger (†) sits in the running text right after the claim it qualifies. The caveat follows that paragraph as a note in the text italic, about 2 px smaller than body, opening with the same dagger. It may sit under a short horizontal hairline, like a footnote. The dagger is in the text color. |
| **Analogy** | A drawing | The analogy is drawn: a small plotter figure that puts the strange thing next to a familiar thing on one ruler, with the slug `ILLUSTRATION`, then one sentence in the text italic. Sources in CONTENT.md: the arm length change far smaller than a proton, and the carbon atom at about 1.4 angstroms for scale. |
| **How sure is this** | An instrument reading | A ledger: rows split by full-measure horizontal hairlines, label in mono on one side, value in display figures on the other. Rows: review status, the paper's own certainty figures (greater than 5.1 sigma, a false alarm less than once in 203,000 years), the known limits (sky position within about 600 square degrees, distance 410 with a range of roughly 230 to 570 megaparsecs), and the standing line that the explainer is machine written and can be wrong, with a link to the paper. Ranges are drawn: solid mark for the value, line-screen band for the range. |

Also:

- PEER-REVIEWED is a solid ink label. PREPRINT is the same label with a line-screen fill or an outline. They differ in weight and lightness, not in hue.
- No invented confidence score, no percent meter, no traffic-light colors, no gauge needle.

## 8. Forbidden

From the owner and CONTEXT.md, without exception:

- Any box, card, callout, or tab with a colored stripe or bar on its left edge. Extend this to any side: no vertical accent rule beside a text block at all, and no quote bar.
- Emoji. Gradient washes. Generic rounded gray cards. Fake phone status bars.
- Em dashes. Invented facts, numbers, testimonials, or counts.

From the weaknesses of A and B:

- The five mockup faces: Anton, Newsreader, IBM Plex Mono, Space Grotesk, JetBrains Mono. Also Inter, Roboto, and Playfair.
- All-caps headlines.
- Acid lime on neutral black. Neutral near-black grounds.
- A grid, dot field, or grain behind reading text.
- A uniform dot grid passed off as halftone.
- Rotated sticker badges.
- Rounded bordered panels around a hero. Corner radius above 2 px on any container, label, or control.
- Polylines with visible corners. Unevenly scaled strokes.
- Glow on anything except the live line at night. `drop-shadow` or blur as a glow.
- A blend whose result was not looked at. Every overlap color is checked in a render.
- Categories or states told apart by hue alone.
- A chart-like picture with no slug saying data or illustration.
- Bounce, spring overshoot, parallax, shimmer, typing text, particles, star fields, or more than one looping animation on a screen.
- Fake readouts: random coordinates, status codes, version strings, clocks.
- More than three type families in one design.

## 9. Rubric

Each category is scored out of 10. A design passes with no category below 8 and a total of 68 or more out of 80. Any item from section 8 scores the design zero until it is fixed.

| Category | 9 to 10 looks like | Capped at 6 if |
|---|---|---|
| **Typography** | A headline face with real character, a second voice (italic or weight) used with intent, a clear scale of at most five sizes, tight leading on display and open leading on text, numbers typeset properly, no awkward wraps at 390 px | A default face, one flat voice, or a headline that wraps badly |
| **Color** | A small palette with one clear leader, every overlap intended, day and night each designed, the live color unmistakable in both | Colors compete at equal strength, an overlap goes muddy, or night is an inversion |
| **Graphic language** | Plates built from line screens with real tone, the live line smooth and precise, marks that all do a job, honest labeled charts | Texture used as wallpaper, clip-art shapes, or unlabeled chart-like pictures |
| **Motion** | Press, Register, and Sweep used with the stated timing, one loop at most, and a resting frame that is complete as a still | No motion, decorative motion, or a resting frame that looks unfinished |
| **Originality** | A stranger could not mistake it for a news site template or a dashboard template, and would remember the live line | It could be a theme from a template store |
| **Fit to the owner's direction** | It is plainly A and B as one idea, and visibly better than both in fonts, graphics, and animation. Nothing he said he hates is present | It reads as A or as B alone, or as two styles side by side |
| **Legibility and accessibility** | Text 4.5:1 (3:1 at 24 px and up), targets 44 px, states differ in lightness or form, real `<button>` and `<a href>`, labeled SVG, body text 16 px or more | Any contrast failure, a target under 44 px, or meaning carried by hue alone |
| **Buildability in Android Compose and plain HTML/CSS** | Everything is flat fills, strokes, line patterns, clip shapes, transforms, opacity, path-length reveals, and multiply or screen blends. Fonts are bundled Google Fonts. No runtime filters, no bitmap effects, no JavaScript-driven animation | It depends on SVG filters, blur, backdrop effects, or an effect with no clear drawing-code equivalent |

On Compose: the list above was chosen to map to canvas drawing, path trimming, and blend modes, but the exact Compose calls were not checked against the Compose documentation in this step. The build team confirms them before any angle is locked.

## 10. Three exploration angles

Three designers each take one angle. The angles share everything above. Each leads on a different axis, and each has its own typefaces, palette, and plate style. They are not three tints of one look.

A crude mechanics test of all three is at `design/shots/director/Sketch-1170w-light-t3.png` (source in `design/scratch/director/`). It proves the line screens, blends, halo, and sweep work. It is a floor to beat, not a target to copy.

All font families below were checked against `google-fonts-families.json`, and each was loaded and looked at in a specimen (`design/shots/director/SpecDisplay-part1.png` to `part3.png`, `SpecText-*.png`, `SpecMono-*.png`). The axis ranges given are the ones that loaded. Use at most three families.

All contrast figures were computed with the WCAG formula (`design/scratch/director/contrast.py`).

### Angle `engraved`: Engraved Broadsheet

**Axis: typographic voice.** A dramatic display serif carries everything. Type leads, the plate supports.

Typeface shortlist:

- Voice: **Noto Serif Display** (`ital,wdth,wght@0,62.5..100,100..900;1,62.5..100,100..900`). At 62.5 percent width and weight 800 it is a true front-page headline face, and its light italic at full width is the second voice. Alternates: **Gloock** (one weight, no italic), **Fraunces** (`ital,opsz,wght@0,9..144,100..900;1,9..144,100..900`), **Bodoni Moda** (`ital,opsz,wght@0,6..96,400..900;1,6..96,400..900`, day only and 40 px and up: in the specimen its plus sign nearly vanished at 34 px).
- Text: **Source Serif 4** (`ital,opsz,wght@0,8..60,200..900;1,8..60,200..900`), **Literata** (`ital,opsz,wght@0,7..72,200..900;1,7..72,200..900`), or **STIX Two Text** (`ital,wght@0,400..700;1,400..700`).
- Data and slugs: **Martian Mono** (`wdth,wght@75..112.5,100..800`), **Sometype Mono** (`wght@400..700`), or **DM Mono** (`wght@300;400;500`).
- Optional caption face: **Old Standard TT** (400 and 700 loaded; confirm the italic loads before relying on it).

Palette, one hot ink:

| Role | Day | Night |
|---|---|---|
| Ground | stock `#E9E6DE` | `#0E1116` |
| Text | ink `#16130F` (14.9:1) | `#E9E4D7` (14.9:1) |
| Muted text | `#5A554B` (5.9:1) | `#9C988D` (6.6:1) |
| Print layer | ink `#16130F` in line screens | structure `#5E6573` (3.2:1), texture `#2B303B` (decorative only) |
| Live line | vermilion `#E0330A` (3.6:1, so graphics and 24 px type only) | amber `#FFA63D` (9.7:1), halo of the same color |

Graphic ideas to try: plates drawn like a scientific engraving. Concentric ripple rings in fine ink lines, bodies shaded with cross-angled line screens in two or three tones, a numbered plate slug. The vermilion line crosses open paper under the engraving. The key idea as a large light italic.

Motion ideas to try: the engraving inks in with a wipe along the screen angle (a `clip-path` reveal), headline lines Press in one by one, then the Sweep. Register can be the black plate and the vermilion line locking together.

Risk to watch: it slides into the stock "cream paper and a serif" editorial look, with the instrument side reduced to garnish. Keep the stock gray rather than cream, keep the line precise and alive, and give the readouts real weight. Hairline serifs can fall apart on the night ground and at small sizes.

### Angle `overprint`: Two-Ink Overprint

**Axis: how print texture and instrument light combine.** Color physics leads. Two inks and no black by day, two lights by night.

Typeface shortlist:

- Voice: **Bricolage Grotesque** (`opsz,wdth,wght@12..96,75..100,200..800`) at 800, whose notched joints read like ink traps. Alternates: **Archivo** (`wdth,wght@62..125,100..900`, wide at 125 or compressed at 62), **Mozilla Headline** (`wdth,wght@75..100,200..700`), **Special Gothic Expanded One**, **Chivo** (`wght@100..900`) at 900.
- Text: **Schibsted Grotesk** (`wght@400..900`), **Hanken Grotesk** (`wght@100..900`), or **Atkinson Hyperlegible Next** (`wght@200..800`).
- Data and slugs: **Martian Mono**, **Azeret Mono** (`wght@100..900`), **Chivo Mono** (`wght@100..900`), or **Red Hat Mono** (`wght@300..700`).

Palette, A's own blue and pink without the yellow that went muddy:

| Role | Day | Night |
|---|---|---|
| Ground | stock `#F2F1EC` | `#0C0A26` |
| Text | overprint indigo `#1D0C72` (13.8:1). There is no black | `#F2EFF8` (17.0:1) |
| Muted text | `#4A3F8F` (7.7:1) | `#A9A4C8` (8.1:1) |
| Ink or light 1 | blue `#1F3FD0` (6.9:1) | blue light `#7A97FF` (7.1:1) |
| Ink or light 2 | pink `#F0308C` (3.4:1, so graphics and 24 px type only) | pink light `#FF74B8` (7.8:1) |
| Overlap | multiply gives `#1D0C72`, the text color | screen gives `#FFC6FF`, near white |
| Print layer at night | | structure `#5A56A8` (3.1:1), texture `#272458` (decorative only) |
| Live line | pink printed solid and last, not multiplied. Test knocking it out to paper where it crosses blue | white-hot `#FFF7FB` (18.4:1) with a pink halo |

Graphic ideas to try: large line-screen shapes in blue and pink that overlap each other and the paper, so a plate shows all four values: paper, blue, pink, and indigo. By day the overlap is the darkest thing on the page. By night the same overlap is the brightest. Use overprint for some shapes and knockout for others. The key idea reversed out of a full-bleed blue band.

Motion ideas to try: Register is the star here. The blue and pink plates arrive apart and lock, and the indigo overlap appears as they meet. Then the Sweep.

Risk to watch: mockup C (flat color poster) was rejected. Keep texture, line, and paper in every plate, and keep reading text on the stock. In the mechanics test, pink multiplied over a solid blue field disappeared, so do not flood a plate with one ink. Pink on stock is only 3.4:1, so it never carries small text.

### Angle `recorder`: Strip Chart

**Axis: structure and motion.** The instrument writes the newspaper. The feed is one continuous roll of chart paper and the pen is always visible.

Typeface shortlist:

- Voice: **Big Shoulders** (`opsz,wght@10..72,100..900`) at 500 to 700 in sentence case, an instrument-legend voice that stays calm. Alternates: **Sofia Sans Extra Condensed** (`wght@1..1000`), **Saira** (`wdth,wght@50..125,100..900`, condensed), **Science Gothic** (`wdth,wght@50..200,100..900`, condensed), **B612** (400 and 700).
- Human voice and text: **STIX Two Text**, **Literata**, or **Source Serif 4**. The serif italic speaks the key idea and the analogy, so the page has warmth.
- Data and slugs: **B612 Mono** (400 and 700), **Martian Mono**, **Spline Sans Mono** (`wght@300..700`), or **Sometype Mono**.

Palette, cool monochrome with one signal. This is the angle that carries B's luminous trace forward, in a new hue:

| Role | Day | Night |
|---|---|---|
| Ground | chart stock `#EDF0EA` | `#07130F` |
| Text | ink `#0F1F1A` (14.8:1) | `#DDE7DF` (14.9:1) |
| Muted text | `#4C5C55` (6.2:1) | `#8DA397` (7.1:1) |
| Plot grid | `#C3CFC6` (hairlines inside plots only) | `#173027` |
| Print layer | ink `#0F1F1A` | structure `#4A6E5E` (3.3:1) |
| Live line | viridian `#00794C` (4.8:1) | phosphor `#62F5A4` (13.6:1), halo of the same color |

Graphic ideas to try: the plate is a real chart with a ruler axis and a hairline grid, bleeding off the right edge where the pen sits. A horizontal tick scale ties cards together. Cards are separated by a full-width perforation line instead of a rule. Readouts are large and tabular. The key idea is pinned to the trace with a leader line, in the serif italic.

Motion ideas to try: the Sweep is the star. The pen carriage is visible, the line is written at constant speed, and the paper advances in exact steps when a new card arrives. Night may be the lead theme for this angle.

Risk to watch: it turns into the cold dashboard that B already was, and loses the editorial drama. Make the headline as large as in the other angles and let the serif carry the human sentences. Keep the grid inside plots. Any scale, perforation, or sprocket detail goes on the top, bottom, or right. Nothing decorative goes on the left edge.

## 11. What each exploration should prove

If your task text asks for something different, the task text wins. Otherwise show:

1. A feed card with its hero plate, in day and in night, at 390 by 844.
2. An explainer excerpt with all four forms from section 7.
3. The live line at start, middle, and rest.

Use only the facts in `design/CONTENT.md`. Score your own work against section 9 before you hand it in, and say where it falls short.
