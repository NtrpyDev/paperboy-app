# First Light: the Paperboy design system, as built

Locked 2026-11-13 after Jury 1 (`design/JURY-1.md`). Winner: candidate x, Engraved Broadsheet, with grafts from Strip Chart and Two-Ink Overprint.

Revised 2026-11-13 at the close of the design round, after the critique (`design/CRITIQUE.md`) and the fix round. This file now describes the seven final boards. Where an earlier value was replaced, the new value is here and the old one is gone.

Read `design/CONTEXT.md` and `design/CONTENT.md` first. They outrank this file. `design/BRIEF.md` gives the reasons behind the rules here. Where this file and the brief disagree, this file wins, because it is later and every value in it was rendered unless it says otherwise. `design/HANDOFF.md` turns this file into build instructions.

No em dashes in any copy. American English. Facts only from `CONTENT.md`.

## 0. The final boards and their sources

All in `design/canvas/project/`. Sizes were measured in the local renderer on 2026-11-13.

| Board | What it is | Size |
|---|---|---|
| `App-Feed-Day.dc.html` | The feed, day. Masthead, the hero card for Paper 1, the top of the next card. | 390 by 844, fixed |
| `App-Feed-Night.dc.html` | The feed, night, scrolled. Plate 2 with its card, the short card with a stamped rating, the preprint card. | 390 by 844, fixed |
| `Explainer-Day.dc.html` | The whole explainer for Paper 1 with the app chrome, day. | 390 by 5,796, fixed width |
| `Explainer-Night.dc.html` | The same page, night. | 390 by 5,796, fixed width |
| `Site.dc.html` | The website. | Fluid page. 4,868 tall at 1440 wide, 6,918 tall at 390 wide |
| `Brand.dc.html` | Wordmark construction and sizes, app icon masters, launcher layers, night marks. | 1200 by 900, fixed |
| `Motion.dc.html` | Every named animation as a looping cell with its timeline. | 1200 by 1000, fixed |

Generators. Edit and rerun these. Do not hand-edit path data.

| File | What it makes |
|---|---|
| `design/scratch/engraved/lib.py` | Tokens, type helpers, `patterns()` (line screens), `chirp()` (the live line as cubic curves), `gw_print()` (Plate 1: the ring field and the wells, no mask), `wells_open()`, `HALO` and `PEN_HALO`, `live_under_strokes()`, `pen_under_marks()`, `sign_times()`, `sign_gt()`, icons, `ink_keyframes()`, `page()` |
| `design/scratch/feed/app_feed.py`, `plates.py` | The two feed boards, Plate 2 |
| `design/scratch/explainer/explainer.py` | The two explainer boards |
| `design/scratch/web/site.py` | The website |
| `design/scratch/brandmotion/brand.py`, `motion.py`, `scenes.py`, `bm.py`, `parts.py` | The brand and motion boards |
| `design/scratch/final/` | The closing checks: `shoot.sh` (render), `audit.py` (targets, text sizes, contrast, overflow at eight widths), `reduced.py` (reduced-motion stills), `start_state.py` (a board paused at a given millisecond), `register_probe.py` (layer transforms at paused times) |

Three edits were made by hand to the final boards at the close and mirrored in the generators: the night core of the live mark is 1.9 px on every board, the sweep starts from a dash offset of 1.003, and the site's `drop` keyframe matches the explainer's. Sections 5.3 and 12 give the reasons. The generators were not rerun after those edits, so the boards on disk are the hand-edited ones.

The lock proofs in `design/scratch/director/` (`LockProof-*`, `LockParts-*`) and the candidates (`Cand-*`) are history. Do not copy from them.

Final renders are in `design/shots/final/` (crops in `crops/`, reduced-motion stills in `reduced/`, paused states in `state/`).

## 1. The idea in one paragraph

A gray printed sheet, set like a broadsheet front page, carrying an engraved plate in one blue ink. Across the plate runs one vermilion line that is being drawn as you watch, with a pen point at its tip and a carriage riding the ruler under it. By night the sheet is a blue-black light table, the plate is drawn in dim blue light, the chrome steps back, and the line is amber and glows. Everything except that line is still.

## 2. Type

Three families. All three are in the Google Fonts repository under the SIL Open Font License 1.1 (checked 2026-11-13: `METADATA.pb` says `license: "OFL"` and each folder holds an `OFL.txt`, at github.com/google/fonts under `ofl/notoserifdisplay`, `ofl/sourceserif4`, `ofl/martianmono`). All three loaded in every render.

```
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Martian+Mono:wdth,wght@75..112.5,100..800&family=Noto+Serif+Display:ital,wdth,wght@0,62.5..100,100..900;1,62.5..100,100..900&family=Source+Serif+4:ital,opsz,wght@0,8..60,200..900;1,8..60,200..900&display=swap">
```

Stacks, written in full in every inline style. In the snippets below they are abbreviated `DISP`, `TEXT`, `MONO`.

- `DISP`: `'Noto Serif Display', Didot, 'Bodoni MT', Georgia, serif`
- `TEXT`: `'Source Serif 4', Georgia, 'Times New Roman', serif`
- `MONO`: `'Martian Mono', 'DejaVu Sans Mono', Menlo, monospace`

### 2.1 The cuts, and what each one is for

These ten cuts are the whole system. Do not use any other weight, width, or style.

| Cut | Family and setting | Role |
|---|---|---|
| D1 | Noto Serif Display, roman, weight 800, `font-stretch: 62.5%` | The first voice. Headlines, the "Paper" of the wordmark, readout numerals, section heads, chart figures. Day. |
| D2 | Noto Serif Display, roman, weight 900, `font-stretch: 62.5%` | D1 on the night ground. One weight step heavier so the hairlines hold. |
| D3 | Noto Serif Display, roman, weight 700, `font-stretch: 75%` | Button labels ("See it explained", "Read the paper", "Download the APK"). Day and night. |
| D4 | Noto Serif Display, italic, weight 300, `font-stretch: 100%` | The second voice. The clause that turns in a headline, the key idea, the "boy" of the wordmark. Day. |
| D5 | Noto Serif Display, italic, weight 400, `font-stretch: 100%` (87.5% inside a night headline of 30 px or more, and in the website's display line under 700 px wide) | D4 on the night ground, and D4 at 22 px or less in either theme. |
| T1 | Source Serif 4, roman, weight 400 | Body text and card summaries. |
| T2 | Source Serif 4, roman, weight 500 | Rating button labels. |
| T3 | Source Serif 4, italic, weight 400 | Caveat notes, analogy sentences, captions, units, the journal link, the paper title in the source footer. |
| M1 | Martian Mono, weight 500, `font-stretch: 75%`, caps, tracking 0.06em | Labels, slugs that describe a picture, axis labels, the masthead strap. |
| M2 | Martian Mono, weight 600, `font-stretch: 75%`, caps, tracking 0.06em | Tags, badges, and section slugs ("KEY IDEA", "FIG. 2", "SOURCE"). |

Source Serif 4 uses its optical size axis automatically. Do not set `font-optical-sizing: none`.

### 2.2 Rules of the two voices

1. A headline is sentence case, never all caps, in D1.
2. The last sentence or clause of a headline turns to D4 at the same size. This is the second voice. The content marks it (`<em>` in the source text). If nothing is marked, the whole headline stays D1. Never pick the clause by position in code.
3. The second voice never starts a headline and never breaks after one word. If the turn leaves a single italic word at the end of a line, break before the clause.
4. The wordmark is `Paper` in D1, `boy` in D4 (D5 at night and at 22 px or less), then the dot.
5. Numbers: lining figures (`font-variant-numeric: lining-nums`), a real minus (−), exponents as `<sup style="font-size: 0.56em; line-height: 0; vertical-align: 0.72em; letter-spacing: 0.01em">` in a readout and at `font-size: 0.64em` in running text. Units are smaller than the number, in T3 or M1.
6. The multiplication sign and the greater-than sign beside display numerals are drawn, not typed. The face's own signs are hairlines next to weight 800 figures. Each is an inline stroke SVG in a 0.5em box at stroke 1.05 in a 10 unit box (`sign_times()`, `sign_gt()` in `lib.py`). In running text the typed × stays.
7. At night, readout numerals get `letter-spacing: 0.02em`, because weight 900 figures touched at −0.005em.

### 2.3 Scale, phone (390 wide)

All rendered in the final boards.

| Token | Size / line height | Cut | Tracking | Used for |
|---|---|---|---|---|
| `headline` | 44 / 0.98 | D1, second voice D4 | −0.005em, second voice −0.012em | Hero card headline, explainer title |
| `head-2` | 30 / 1.02 | D1, second voice D4 | same | Short card headline, explainer section heads, figure titles ("Where the mass went", 30 / 1.0) |
| `key-idea` | 30 / 1.06 | D4 | −0.012em | The key idea. `text-wrap: balance` |
| `readout-xl` | 72 / 0.86 | D1 | −0.005em | The one stat of a stat block ("410") |
| `readout` | 44 / 1.0 | D1 | −0.005em | Hero plate readout, short card stat (44 / 0.86) |
| `readout-s` | 30 / 1.0 | D1 | −0.005em | Ledger values |
| `button` | 23 / 1.0 | D3 | 0.005em | Primary and outline buttons |
| `body` | 17 / 1.47 | T1 | 0 | Explainer text. `text-wrap: pretty` |
| `body-feed` | 16 / 1.42 | T1 | 0 | Card summary |
| `rate` | 16 / 1.0 | T2 | 0 | "More like this", "Less like this" |
| `note` | 15 / 1.4 | T3 | 0 | Caveat note, analogy sentence, ledger notes, units, journal link (15 / 1.0 on one line) |
| `label` | 10.5 / 1.3 (1.4 on two or three lines) | M1 or M2 | 0.06em, caps | Every mono label |
| `tag` | 10 / 1.3 | M2 | 0.06em, caps | Tags and badges only |
| `wordmark` | 33 / 1.0 | D1 + D4 | −0.005em, "boy" −0.02em | Feed masthead |
| `wordmark-s` | 22 / 1.0 | D1 + D5 | same | Explainer top bar |

Read as a scale it is five text sizes (44, 30, 17, 15, 10.5) plus numerals and controls. Nothing in mono is under 10 px. Nothing a person reads as a sentence is under 15 px.

### 2.4 Scale, website at 1160 px and wider

All rendered in `Site.dc.html` at 1440.

| Token | Size / line height | Cut |
|---|---|---|
| `display` | `clamp(44px, 7.2vw, 88px)` / 0.94 | D1 + D4 |
| `headline` | 66 / 0.95 | D1 + D4. Section heads. |
| `head-2` | 44 / 0.98 | D1 + D4. Headline inside the phone mock. |
| `head-3` | 30 / 1.0 | D1. Figure titles, the agent sentences, "How sure is this?" |
| `key-idea` | 40 / 1.04 | D4 |
| `readout-xl` | 88 / 0.84 | D1 |
| `readout` | 48 / 1.0 | D1 |
| `button` | 23 / 1.0 | D3 |
| `body` | 19 / 1.5 | T1 |
| `note` | 16 / 1.42 | T3 |
| `label` | 11 / 1.3 | M1, M2 |
| `tag` | 10.5 / 1.3 | M2 |
| `wordmark` | 38 / 1.0 in the masthead (dot 6.5 px), 150 / 1.0 in the footer | D1 + D4 |

Under 1160 px the website uses the phone scale, with `display` at `clamp(34px, 10.7vw, 64px)` / 0.98 and section heads at 44 / 0.98 from 700 px up. Section 9.20 lists the breakpoints.

## 3. Color

### 3.1 Day: inks on stock

| Token | Hex | Use | Contrast on stock |
|---|---|---|---|
| `stock` | `#E9E6DE` | The ground. Gray, not cream. | |
| `ink` | `#16130F` | All text, rules, outlines, solid buttons, solid tags, the black plate layer | 14.85:1 |
| `ink-muted` | `#5A554B` | Second-rank labels, author line, grid and drop lines in figures, the stamped rating fill | 5.94:1 |
| `plate` | `#1F3FD0` | The print ink of plates and figure fills. Line screens and engraved rings only. | 6.28:1 |
| `live` | `#E0330A` | The live mark only (section 3.4) | 3.62:1 |

Other checked pairs: `stock` on `ink` 14.85:1 (primary button, solid tag). `stock` on `ink-muted` 5.94:1 (stamped rating). `live` against `plate` 1.73:1, which is why the trap rule in section 5.3 exists.

### 3.2 Night: lights on ground

| Token | Hex | Use | Contrast on ground |
|---|---|---|---|
| `ground` | `#0E1116` | The ground. Blue-black, never neutral. | |
| `light` | `#E9E4D7` | All text, the one primary slab, the solid tag, the carriage | 14.90:1 |
| `light-muted` | `#9C988D` | Second-rank labels, and all chrome that is not text: card dividers, double rules, tag outlines, outline button borders, rating button borders, ruler lines and tick labels, contour lines of the black plate layer, range screens, the stamped rating fill | 6.56:1 |
| `structure` | `#5E6573` | Grid, drop, and leader lines in figures | 3.23:1 |
| `texture` | `#2B303B` | Non-essential decoration only. Never carries meaning. Not used in the final boards. | 1.43:1 |
| `plate-night` | `#4D63C9` | The plate light: engraved rings and figure fills | 3.55:1 |
| `live-night` | `#FFA63D` | The live mark only, core and halo | 9.70:1 |

Other checked pairs: `ground` on `light` 14.90:1 (primary button, solid tag). `ground` on `light-muted` 6.56:1 (stamped rating). `live-night` against `plate-night` 2.73:1, so the trap rule holds at night too.

All figures are WCAG 2 contrast ratios, recomputed at the close with the WCAG formula. `design/scratch/final/audit.py` also checked every HTML text node on every board against its background: no pair is under 4.5:1 (3:1 at 24 px and up).

### 3.3 Rules

1. Text is `ink` or `ink-muted` by day, `light` or `light-muted` by night. Never `plate`, never `live`.
2. `plate` is print. It appears only as line screens and engraved lines inside plates and figures. Never a flat flood, never chrome, never a button, never a rule.
3. No tone is made with opacity or gray. A lighter tone is a thinner line in the screen. Two exceptions, both at night and both rendered: the halo of the live line (section 5.3), and the fine ring passes of the wave field at 0.55 stroke opacity.
4. Day overlaps get darker, night overlaps get brighter. In the final plates the black layer is drawn opaque over the blue layer, so no blend mode is used anywhere (zero `mix-blend-mode` in the seven boards).
5. Night is designed, not inverted. Three things change besides the colors: the plate loses its heaviest ring pass, the chrome steps down from `light` to `light-muted`, and the type steps up (D1 to D2, D4 to D5). The order on a night screen is text, amber, structure.
6. No gradients. The one CSS gradient function allowed is the hard-stop hatch of the PREPRINT frame (section 9.4).

### 3.4 Where vermilion and amber may appear

Only here:

1. The live line and its pen point.
2. The dot of the wordmark, which is the pen point.
3. The one mark in a figure that carries the paper's reported value: the 410 marker, the AlphaFold 0.96 beam, the "3 solar masses" segment, the 7 millisecond beam, the M87 ring, the change in arm length.
4. The legend dot for that mark.

One live mark per figure. One animating live line per viewport.

**The live mark is always solid.** The rule "solid means sure, screened means not yet sure" (section 4.2) governs every other mark. The live mark is exempt, because it has to stay one unbroken color. When the value it marks is approximate, the word "about" in its label or caption carries that, and where the paper gives a range the range is drawn as a screened band behind it. This settles the question the critique raised about the "about 3 solar masses" segment.

## 4. Chart palette and chart rules

### 4.1 Series, in the order they are assigned

Series are told apart by lightness and by form, not by hue. L* is CIE lightness computed from the hex.

| Order | Day | L* | Night | L* | Form |
|---|---|---|---|---|---|
| 1, the finding | `live` `#E0330A` | 50 | `live-night` `#FFA63D` | 75 | A line with a pen point, or one solid mark or segment |
| 2 | `ink` `#16130F` solid | 6 | `light` `#E9E4D7` solid | 91 | Solid bar, beam, or 1.4 px line |
| 3 | `plate` `#1F3FD0` solid | 35 | `plate-night` `#4D63C9` solid | 45 | Solid bar or 1.4 px line |
| 4, estimate or range | `ink` line screen, mid tone, 0.9 px outline | | `light-muted` `#9C988D` line screen, mid tone, 0.9 px `light` outline | | Screened band or bar |
| 5, context shape | `plate` line screen, light tone, 0.9 px `ink` outline | | `plate-night` line screen, light tone, 0.9 px `light` outline (`light-muted` on Plate 2 at night, where every mark but the live beam is second rank) | | Screened shape (the carbon atom, the proton) |

At most four series in one chart. More than that becomes small multiples. Two screened series in one chart use the two screen angles (−72 and −12 degrees), and their overlap is the weave ("Where the mass went": 36 on one angle, 29 on the other, 62 as the weave of both).

### 4.2 Rules

1. **Solid means measured or reviewed. Screened means a range, an estimate, or a preprint.** The four masses in CONTENT.md are "about" values, so the mass chart draws 36, 29, and 62 screened. The live mark is the one exception (section 3.4).
2. One axis. It is a ruler: a 0.9 px line in the text color (`light-muted` at night), ticks below it and outside the plot, 4 px minor and 7 px major, labels in `label` with their baseline 20 px under the axis line. The unit is written once, at the end of the axis or after the last tick label.
3. Grid and drop lines are 0.6 px solid, `ink-muted` by day and `structure` by night, and stay inside the plot. No dashed lines.
4. Bars and bands are 16 to 20 px tall with a 0.9 px outline in the text color.
5. Labels sit at the mark, horizontal, in the text color, never in the series color. Figures on bars are D1 at 25 px. Range ends are `label`.
6. A reported value drawn over a screened band is a 2 px `live` line (1.9 px at night) on a 7 px ground-colored trap, with a 3.6 px radius dot at its top. In the ledger's small range bar (124 by 30) the trap is 6 px and the dot 3.2 px.
7. A legend appears when there are two or more kinds of mark. It is a row under the chart in `label`, `ink-muted`: a 7 px dot for the live mark, a 22 by 10 px swatch for a screen. A mark that carries a direct label is not repeated in the legend. A legend key is never a vertical bar beside text.
8. Every figure has a head row: a section slug on the left (`FIG. 2`, `FOR SCALE`, `TRY IT`) in M2 and a kind slug on the right in M1 muted. The kind slug is one of: `DATA, FROM THE PAPER`, `ILLUSTRATION, NOT TO SCALE`, `ILLUSTRATION, DRAWN TO SCALE`. The chirp is an illustration. Only numbers from the paper are data.
9. Every `<svg>` that carries meaning has `role="img"` and an `aria-label` that states the numbers. Decorative layers have `aria-hidden="true"`.
10. Tick numbering is ordinary axis numbering. It is not a paper fact and needs no source.

## 5. Texture and line

### 5.1 Line screens

- A fill is parallel lines from an SVG `<pattern>`: `width="40" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(A)"` holding one `<rect>` whose height is the tone.
- Pitch 3.0 px (3.2 px in Plate 3). Angle A1 = −72 degrees, angle A2 = −12 degrees. They are 60 degrees apart, so two screens overlap as a clean weave.
- Tones, as a fraction of the pitch: light 0.24, mid 0.46, heavy 0.68 (on A2: 0.24, 0.44, 0.66). A context shape uses 0.30. Every tone has the same pitch and phase, so a line swells from one tone to the next without breaking.
- Show at least two tones in a plate. One tone alone reads as stripes.
- A screen fills a shape that has a subject. A screen never floods a whole plate as a background with nothing in it. (The first Plate 2 did that and was redrawn on open ground.)

```
<pattern id="p-a2" width="40" height="3.0" patternUnits="userSpaceOnUse" patternTransform="rotate(-72)"><rect x="0" y="0.810" width="40" height="1.380" fill="#16130F"></rect></pattern>
```

### 5.2 Engraved fields

Plate 1 is drawn by `gw_print()` in `lib.py`, and every board calls it: the feed, both explainers, the website hero at four widths, and the motion board. There is no SVG mask anywhere in the system now.

- **The field.** Concentric rings 3.2 px apart around one center, as full circles from two arcs each. The fine pass is 0.5 px (night: 0.6 px at 0.55 opacity).
- **The swell.** Where a ring crosses a crest of a two-armed spiral it swells. Each swell is a filled lune: the ring's own arc on one side and a second arc on the other, so it is thick in the middle and comes to a point at both ends. Two crest widths: a broad one that peaks at 1.5 px and a narrow one that peaks at 2.3 px. Night draws only the broad one, at 1.4 px, so the plate stays dim and the amber line leads.
- **Near the wells.** No ring is drawn within 50 px of the heavier body. From 50 to 66 px only every other ring is drawn, at 0.62 px. Swells grow from nothing at 46 px to full height at 118 px, and stop at 60 px (broad) and 76 px (narrow). A swell that would be cut to less than 0.4 of its length is left out, so nothing ends in a stub. Distances are at the 390 px plate and scale with it.
- **The wells.** Contours only, no solid discs. Each contour is a level of the combined pull of two masses of 36 and 29, so the two wells keep that ratio and merge into one figure below the saddle. Lines go from 0.55 px outside to 0.8 px near the centers, spacing tightens toward each center, and the centers stay open. `ink` by day, `light-muted` by night, over a ground-colored knockout of the outermost contour.

Plate 3 (M87) is concentric discs of the `plate` screen on angle A2 at three tones, lightest near the ring, with the shadow as a weave of `plate` and `ink` screens. Plate 2 (AlphaFold) has no field: marks on open ground.

### 5.3 The live line

| | Day | Night |
|---|---|---|
| Core | 1.9 px `live`, round joins and caps | 1.9 px `live-night`, round joins and caps |
| Under it, in drawing order | A 7 px stroke of the same path in `stock` (the trap) | A 4 px stroke in `ground` (the trap), then three strokes in `live-night`: 17 px at 0.05, 11 px at 0.12, 6 px at 0.08 (the halo) |
| Pen point, in drawing order | A 6.5 px radius `stock` dot, then a 3.6 px radius `live` dot | A 5 px radius `ground` dot, then three `live-night` discs: 13 px at 0.05, 10 px at 0.14, 6.5 px at 0.09, then a 3.4 px radius `live-night` dot |

- One continuous path of cubic curves. No polylines, no uneven scaling. Bake amplitude into the path (`chirp()`).
- The line never touches plate ink directly. It always rides on its trap.
- The night halo is wider than the trap, so it lies over the plate and warms the ring lines under it. The area around the line reads brighter than the plate, not darker. The first version had a 7 px halo on a 7 px trap, which showed as a brown casing.
- The night core is 1.9 px, the same as day. It was 1.6 px. The explainer raised it to hold against the rings, and at the close the feed and motion boards were set to match.
- No blur, no `drop-shadow`, no SVG filter. The halo is strokes.
- Where a paper has no waveform, the live line is the one path that carries the finding: the M87 ring (a circle drawn from 12 o'clock), the AlphaFold distance being ruled off.
- In the "Try it" control the part of the signal not yet played is a 0.9 px line in `ink-muted` (`light-muted` at night) on a 4.5 px trap.

### 5.4 Marks

Allowed, and only where they do a job: the ruler axis, the carriage, leader lines (0.75 px), drop lines, the plate slug, scale bars with end caps. Nothing decorative. Nothing on the left edge of a text block.

## 6. Corners, borders, spacing

**Corners.** Radius 0 on every container, tag, button, and control. The only round things are the pen point, the wordmark dot, the legend dot, the theme icon, and the launcher masks on the brand board.

**Borders and rules.**

| Token | Weight | Use |
|---|---|---|
| hairline | 0.75 px | Rules between ledger rows, section rules, the thin half of a double rule, leader lines |
| figure line | 0.9 px | Axes, outlines of bars, bands, and shapes |
| control | 1 px | Outlines of tags, outline buttons, rating buttons |
| beam | 1.4 px | Comparison beams and second-series lines in figures |
| heavy | 3 px | The thick half of a double rule |

The **double rule** is a 3 px rule and a 0.75 px rule 2 px apart. Under the masthead and at the head of an explainer section the heavy rule is on top. Between two cards in the feed the hairline is on top and the heavy rule is under it, so the heavy rule reads as the head of the next card. A **footnote rule** is 64 px wide and 0.75 px. By night every rule is `light-muted`.

All rules are horizontal. There is no vertical rule beside text anywhere in the system.

**Spacing.** Steps: 2, 4, 6, 8, 10, 12, 14, 16, 20, 40, 56 px.

- Screen margin, phone: 20 px each side. Plates ignore it and bleed.
- Inside a card: 13 px above the tag row, 10 px above the headline, 12 px above the plate, 6 px above the readout row, 10 px above the summary, 14 px above the buttons, 8 px between buttons, 18 px under the buttons before the divider.
- Tags are 6 px apart. A tag row that wraps has `row-gap: 6px`.
- Between explainer sections: 40 px. Around the key idea: 40 px above and 40 px below.
- Website at 1160 and wider: `max-width: 1200px` including 56 px side padding, 12 columns with a 24 px gutter, 96 px between sections. Under 1160: 20 px side padding, 56 px between sections.

**Touch targets.** 44 px at least, measured on every link, button, and input on every board. Primary and outline buttons are 48 px tall. The journal link is a 44 px tall hit area with negative vertical margin so it does not push the row apart. The slider is a 44 px tall input.

## 7. Artboard skeleton

Unchanged from `CONTEXT.md`. `page()` in `lib.py` writes it. The helmet holds only: the fonts link, `body{margin:0}`, link colors, keyframes, the reduced-motion rule, and the few rules that cannot be inline (the slider's thumb and track, the website's custom properties and media queries, hover and focus). Everything else is inline style. No `{{holes}}`, `sc-for`, or `sc-if`.

Phone root, day:

```
<div style="width: 390px; height: 844px; box-sizing: border-box; overflow: hidden; position: relative; background-color: #E9E6DE; color: #16130F; font-family: TEXT; display: flex; flex-direction: column">
```

For night, in every snippet below: `stock` to `ground`, `ink` to `light` for text and the primary slab, `ink` to `light-muted` for rules and outlines, `ink-muted` to `light-muted`, `plate` to `plate-night`, `live` to `live-night`, D1 to D2, D4 to D5.

## 8. Icons

Inline stroke SVG, 1.5 px, `stroke-linecap="square"`, `stroke="currentColor"`, `aria-hidden="true"`. All in `lib.py` except where noted.

- `ARROW` (20 px, primary button): `<path d="M3 10h13M11 5l5 5-5 5">`
- `BACK` (20 px, explainer top bar, in `explainer.py`): `<path d="M17 10H4M9 5l-5 5 5 5">`
- `DOWNLOAD` (20 px, website, in `site.py`): `<path d="M10 3v10.5M5.5 9.5l4.5 4.5 4.5-4.5M4 17.25h12">`
- `OUTARROW` (11 px on a link at 1.3 px stroke, 15 px on an outline button): `<path d="M2 9l7-7M3.5 2H9v5.5">`
- `PLUS` (14 px): `<path d="M7 1.5v11M1.5 7h11">`
- `MINUS` (14 px): `<path d="M1.5 7h11">`
- `CHECK` (14 px, the stamped rating): `<path d="M2 7.6l3.4 3.4 6.6-8">`
- `THEME` (22 px): a 7.25 radius circle with its right half filled.

New icons follow the same weight and ends. No icon stands alone without a text label or an `aria-label`.

## 9. Components

Each pattern is the day markup from the board named. Replace `DISP`, `TEXT`, `MONO` with the full stacks.

`LABEL` stands for `font-family: MONO; font-stretch: 75%; font-size: 10.5px; font-weight: 500; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase`. `SLUG` is `LABEL` at weight 600. `TAG` is `LABEL` at 10 px and weight 600.

### 9.1 Masthead (feed)

Board: `App-Feed-Day`. Wordmark left, strap right in two lines, theme button, then a double rule with the heavy rule on top.

```
<header style="padding: 8px 20px 0; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 10px">
<div style="font-family: DISP; font-size: 33px; font-weight: 800; font-stretch: 62.5%; line-height: 1; letter-spacing: -0.005em; padding-bottom: 4px">Paper<span style="font-family: DISP; font-size: 33px; font-weight: 300; font-stretch: 100%; line-height: 1; letter-spacing: -0.02em; font-style: italic">boy</span><span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: #E0330A; margin-left: 3px"></span></div>
<div style="margin-left: auto; text-align: right; LABEL; color: #5A554B; line-height: 1.35">Science and math,<br>newly released</div>
<button type="button" aria-label="Switch to night theme" style="width: 44px; height: 44px; margin-right: -11px; background-color: transparent; border: 0; color: #16130F; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0">THEME icon</button>
</div>
<div style="height: 3px; background-color: #16130F"></div><div style="height: 0.75px; background-color: #16130F; margin-top: 2px"></div>
</header>
```

Two items here were added by the designers and not asked for by the owner: the theme button and the strap copy. Both stay in the mockups in this position until the owner rules on them (section 14). If the theme button goes, the strap moves to the right edge.

The wordmark dot is 6 px at 33 px type, 6.5 px at 38, 4 px at 22, 18 px at 116, 22 px at 150. It sits on the baseline, 3 px after the y (2 px at 22). The masthead dot never pulses.

### 9.2 Explainer top bar (app chrome)

Board: `Explainer-Day`. A 48 px row: a back link on the left, the small wordmark on the right, then the double rule.

```
<header style="padding: 0 20px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; justify-content: space-between; height: 48px">
<a href="..." style="margin-left: -12px; padding: 0 12px; min-width: 44px; height: 44px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 8px; color: #16130F; text-decoration: none; SLUG">BACK icon<span>Feed</span></a>
<div style="font-family: DISP; font-size: 22px; font-weight: 800; font-stretch: 62.5%; line-height: 1; letter-spacing: -0.005em; padding-bottom: 3px">Paper<span style="font-family: DISP; font-size: 22px; font-weight: 400; font-stretch: 100%; letter-spacing: -0.02em; font-style: italic">boy</span><span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: #E0330A; margin-left: 2px"></span></div>
</div>
<div style="height: 3px; background-color: #16130F"></div><div style="height: 0.75px; background-color: #16130F; margin-top: 2px"></div>
</header>
```

The page under it opens exactly like the card it came from: tag row, headline, plate, readout row, summary. Then the key idea.

### 9.3 Paper card with hero

Board: `App-Feed-Day`, the first `<article>`. Order, top to bottom:

1. Tag row (9.5) with the journal link at its right end.
2. Headline, `headline` token, three lines at most at 390 px. Each line is a `display: block` span so Press can stagger.
3. Hero plate (9.4), full bleed.
4. Readout row: the readout and its label on the left, the plate slug on the right, bottoms aligned.
5. Summary in `body-feed`.
6. Primary button (9.6), then the rating row (9.7).
7. Card divider: a double rule with the hairline on top, 18 px under the buttons.

```
<h2 style="margin: 0; padding: 10px 20px 0; font-family: DISP; font-size: 44px; font-weight: 800; font-stretch: 62.5%; line-height: 0.98; letter-spacing: -0.005em">
<span style="display: block; animation: press 190ms cubic-bezier(0.2, 0, 0, 1) 0ms both">Two black holes</span>
<span style="display: block; animation: press 190ms cubic-bezier(0.2, 0, 0, 1) 50ms both">merged. <span style="font-family: DISP; font-size: 44px; font-weight: 300; font-stretch: 100%; line-height: 0.98; letter-spacing: -0.012em; font-style: italic">Earth felt</span></span>
<span style="display: block; animation: press 190ms cubic-bezier(0.2, 0, 0, 1) 100ms both; font-family: DISP; font-size: 44px; font-weight: 300; font-stretch: 100%; line-height: 0.98; letter-spacing: -0.012em; font-style: italic">space stretch.</span>
</h2>
```

Readout row:

```
<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px 20px 0">
<div style="display: flex; flex-direction: column; gap: 3px">
<div style="font-family: DISP; font-size: 44px; font-weight: 800; font-stretch: 62.5%; line-height: 1; letter-spacing: -0.005em; font-variant-numeric: lining-nums">1.0 SIGN_TIMES 10<sup style="font-size: 0.56em; line-height: 0; vertical-align: 0.72em; letter-spacing: 0.01em">−21</sup></div>
<div style="LABEL; color: #5A554B">Peak strain. Pitch 35 to 250 Hz</div>
</div>
<div style="text-align: right; LABEL; color: #5A554B; line-height: 1.4">Plate 1<br>Illustration,<br>not to scale</div>
</div>
```

A readout with a unit sets the unit after the numeral in T3 at 15 px, 7 px away ("0.96 angstroms").

Summary: `<p style="margin: 0; padding: 10px 20px 0; font-family: TEXT; font-size: 16px; line-height: 1.42; font-weight: 400; text-wrap: pretty">`.

Card divider: `<div style="margin: 18px 20px 0; height: 0.75px; background-color: #16130F"></div><div style="margin: 2px 20px 0; height: 3px; background-color: #16130F"></div>`.

The screen crops between cards in a gap, never through a line of type. The day feed ends on the next card's tag row.

### 9.4 Hero plate

On a phone the plate is 390 wide and bleeds to both edges. The print band is 196 px tall. The bottom edge of the band is the ruler. Tick labels sit under it, so the whole block is 230 px tall, with 12 px above it. Plate 2 has a 122 px band and a 156 px block.

Layers, back to front:

```
<div style="position: relative; width: 390px; height: 230px; margin-top: 12px">
  <div style="position: absolute; left: 0; top: 0; width: 390px; height: 196px; animation: inkproof 520ms cubic-bezier(0.2, 0, 0, 1) 60ms both">
    <div style="position: absolute; left: 0; top: 0; animation: registerA 480ms cubic-bezier(0.16, 1, 0.3, 1) 60ms both">
      <svg viewBox="0 0 390 196" width="390" height="196" aria-hidden="true" style="display: block">BLUE LAYER: the engraved field in plate ink</svg>
    </div>
    <div style="position: absolute; left: 0; top: 0; animation: registerB 480ms cubic-bezier(0.16, 1, 0.3, 1) 60ms both">
      <svg viewBox="0 0 390 196" width="390" height="196" aria-hidden="true" style="display: block">BLACK LAYER: the subject, in contours over a ground knockout</svg>
    </div>
  </div>
  <svg viewBox="0 0 390 230" width="390" height="230" role="img" aria-label="Illustration of the signal: ..." style="position: absolute; left: 0; top: 0">LIVE LAYER</svg>
</div>
```

The live layer, in this order: the trap path, (night: the three halo paths), the core path, the ruler and ticks, the carriage, the tick labels, the pen point's ground dot, (night: the three halo discs), the pen point.

```
<path d="..." fill="none" stroke="#E9E6DE" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="stroke-dasharray: 1 1.5; animation: sweep 1900ms linear 320ms both"></path>
<path d="..." fill="none" stroke="#E0330A" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="stroke-dasharray: 1 1.5; animation: sweep 1900ms linear 320ms both"></path>
<g stroke="#16130F" stroke-width="0.9" fill="none"><line x1="20" y1="196" x2="390" y2="196"></line> ticks: y1="196" y2="203" major, y2="200" minor </g>
<g clip-path="url(#rail)"><g style="offset-path: path('...'); offset-distance: 100%; offset-rotate: 0deg; animation: travel 1900ms linear 320ms both"><line x1="0" y1="-400" x2="0" y2="400" stroke="#16130F" stroke-width="9"></line></g></g>
<circle r="6.5" fill="#E9E6DE" style="offset-path: path('...'); offset-distance: 100%; offset-rotate: 0deg; animation: travel 1900ms linear 320ms both"></circle>
<circle r="3.6" fill="#E0330A" style="offset-path: path('...'); offset-distance: 100%; offset-rotate: 0deg; animation: travel 1900ms linear 320ms both, pulse 2400ms ease-in-out 2400ms infinite"></circle>
```

`#rail` is `<clipPath><rect x="0" y="195.5" width="390" height="8"></rect></clipPath>`. The carriage is a tall 9 px line that follows the pen point along the same path, and the clip leaves only the 8 px of it that sit on the ruler. So the carriage is always exactly under the pen. By night the ruler and its labels are `light-muted` and the carriage is `light`.

Rules:

1. The live line crosses the lower third of the plate (its zero line is 39 px above the ruler, amplitude 29 px). The subject of the plate sits in the upper right. The line and the subject do not overlap. After the peak the chirp has three clean decaying cycles and then a flat run of at least 30 px into the pen point.
2. The ruler starts at the left margin (x = 20) and runs off the right edge. It is in the paper's own unit. The time ruler here is labeled `0`, `0.1`, `0.2 s`. Ticks stop at the last label when the ruler is wide (website).
3. A plate gets a ruler and a carriage only when the live line is really plotted against that quantity. No real axis: no ruler, no carriage, and the pen point leads alone (Plate 3, which has a scale bar labeled "Ring diameter" under it).
4. A plate holds at most: one blue layer, one black layer, the live line, the ruler, and direct labels at the marks. The readout and the slug sit under the plate on open ground, not on it.
5. Nothing sits behind reading text. No type is set on a field. Plate 2 has no field, so its three labels sit at their marks on open ground: "AlphaFold, 0.96 Å" in the text color, "Next best, 2.8 Å" and "Carbon atom, about 1.4 Å" in the muted color. A label lands (Press) as its mark arrives, never before.
6. On the website a plate bleeds off the right edge of the page. It is never a bordered or rounded panel.

### 9.5 Tags and badges

All are `tag` type (M2, 10 px), `padding: 4px 6px 3px`, 1 px border, radius 0, 6 px apart.

```
Field tag, a ruled outline:
<span style="TAG; color: #16130F; border: 1px solid #16130F; padding: 4px 6px 3px">Physics</span>

PEER-REVIEWED, solid:
<span style="TAG; color: #E9E6DE; background-color: #16130F; border: 1px solid #16130F; padding: 4px 6px 3px">Peer-reviewed</span>

PREPRINT, a screened frame:
<span style="display: inline-flex; padding: 3.5px; background-image: repeating-linear-gradient(135deg, #16130F 0 1.1px, transparent 1.1px 3.2px)"><span style="TAG; color: #16130F; background-color: #E9E6DE; padding: 1.5px 4px 0.5px">Preprint</span></span>
```

The three differ by form: outline, solid, screened. Never by hue. The PREPRINT hatch runs at 135 degrees, not the system's 72, because 72 rendered unevenly at this size. It is the only hatch at that angle and the only use of a gradient function. By night the field tag's outline and the hatch are `light-muted`, and the solid tag is `light` with `ground` text.

The journal link closes the tag row:

```
<a href="..." style="margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; font-family: TEXT; font-size: 15px; line-height: 1; font-weight: 400; font-style: italic; color: #16130F; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">Physical Review Letters OUTARROW</a>
```

If the name does not fit beside the tags, the row wraps and the link takes its own line, right aligned (`flex-wrap: wrap; column-gap: 6px; row-gap: 6px` on the row, and the link inside `<span style="flex: 1 1 auto; display: flex; justify-content: flex-end; margin: -13px 0">`). Never abbreviate a journal name in code.

### 9.6 Buttons

Primary, a solid ink slab. One per card.

```
<a href="..." style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: #16130F; color: #E9E6DE; text-decoration: none; font-family: DISP; font-size: 23px; font-weight: 700; font-stretch: 75%; line-height: 1; letter-spacing: 0.005em"><span>See it explained</span>ARROW</a>
```

Outline, for the link out to the paper: the same box with `border: 1px solid #16130F; color: #16130F`, no background, and `OUTARROW` at 15 px. Label: "Read the paper". By night its border is `light-muted` and its label `light`.

Website: "Download the APK" is the primary slab with `DOWNLOAD`. "Source on GitHub" is the outline button. Hover: a text link goes to `ink-muted`, the slab's background goes to `ink-muted`. Focus: `outline: 2px solid` in the text color, `outline-offset: 2px`. Hover and focus are in the site's helmet. They were not captured in a render.

### 9.7 Rating controls

Two equal outline buttons with the words written out.

```
<div style="display: flex; gap: 8px">
<button type="button" aria-pressed="false" style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: transparent; border: 1px solid #16130F; border-radius: 0; color: #16130F; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">PLUS<span style="font-family: TEXT; font-size: 16px; line-height: 1; font-weight: 500">More like this</span></button>
<button ...>MINUS<span ...>Less like this</span></button>
</div>
```

Stamped (chosen): `aria-pressed="true"`, the fill one step under the primary slab, and the icon turned to `CHECK`.

| | Day | Night |
|---|---|---|
| Fill and border | `ink-muted` `#5A554B` | `light-muted` `#9C988D` |
| Label and icon | `stock` | `ground` |
| Contrast | 5.94:1 | 6.56:1 |

So the primary action stays the heaviest thing on the card, and the state is carried by the check as well as the fill. Only one of the two can be stamped. The words never shorten to bare icons. By night the unstamped border is `light-muted`.

### 9.8 Short card and preprint card

Board: `App-Feed-Night`. No plate and no summary. Order: tag row with journal link, headline in `head-2` (30 / 1.02) with its second voice, one stat if the content has one (numeral 44 / 0.86 in D1 beside a two-line `label` in the muted color, 10 px apart, bottoms aligned), the outline button "Read the paper", the rating row. It never shows "See it explained".

The board shows this card with Paper 3, because `CONTENT.md` says "a short card style is fine" for it. Paper 3 is open access. In the product a short card is a paywalled paper or one not yet explained (`GLOSSARY.md`). The website shows the same paper as a full card with Plate 3, which is what it would be once explained.

A preprint card is any card whose badge is the screened PREPRINT tag. With no real preprint facts, its field is `[FIELD]`, its title `[PREPRINT TITLE]` in `head-2`, and its summary `[ONE LINE SUMMARY]` in `body-feed`.

### 9.9 Key idea

Type at scale and nothing else. No box, no band, no rule, no mark beside it.

```
<section style="display: flex; flex-direction: column; padding: 40px 0">
<div style="SLUG; color: #16130F">Key idea</div>
<p style="margin: 12px 0 0; font-family: DISP; font-size: 30px; font-weight: 300; font-stretch: 100%; line-height: 1.06; letter-spacing: -0.012em; font-style: italic; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</section>
```

One key idea per explainer. Website at 1160 and wider: 40 / 1.04.

### 9.10 Caveat

A dagger in the running text right after the claim, then a note under a short rule. The dagger is in the text color.

```
<p style="margin: 0; font-family: TEXT; font-size: 17px; line-height: 1.47; text-wrap: pretty">Its shape matches two black holes spiraling into one, about 410 megaparsecs away, roughly 1.3 billion light years.†</p>
<div style="width: 64px; height: 0.75px; background-color: #16130F; margin-top: 16px"></div>
<p style="margin: 10px 0 0; font-family: TEXT; font-size: 15px; line-height: 1.4; font-style: italic; text-wrap: pretty">† The mass and distance values carry wide error ranges. The distance, for example, is 410 megaparsecs with a range of roughly 230 to 570.</p>
```

A second caveat in the same section uses the double dagger (‡).

### 9.11 Stat

One number at `readout-xl`, with what it is, then the figure that shows its range. Board: "Fig. 2" in `Explainer-Day`.

```
<section style="display: flex; flex-direction: column; margin-top: 40px">
<div style="height: 0.75px; background-color: #16130F"></div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px"><div style="SLUG; color: #16130F">Fig. 2</div><div style="LABEL; color: #5A554B">Data, from the paper</div></div>
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div style="font-family: DISP; font-size: 72px; font-weight: 800; font-stretch: 62.5%; line-height: 0.86; letter-spacing: -0.005em; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px"><div style="SLUG; color: #16130F">Megaparsecs away</div><div style="font-family: TEXT; font-size: 15px; line-height: 1.3; font-style: italic">roughly 1.3 billion light years</div></div>
</div>
<div style="margin-top: 14px">range bar SVG, 350 by 70</div>
<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; LABEL; color: #5A554B">
<span style="display: inline-flex; align-items: center; gap: 6px"><span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #E0330A"></span>Reported value</span>
<span style="display: inline-flex; align-items: center; gap: 6px">22 by 10 screen swatch<span>Range</span></span>
</div>
</section>
```

The range bar: a screened band from 230 to 570 at y 16 to 32 with a 0.9 px outline, the 410 marker from y 9 to the axis at y 44, end labels above the band, a ruler from 0 to 600 with `Mpc` at its right end. At night the band's screen is `light-muted` so the amber marker leads.

### 9.12 Bar chart ("Where the mass went")

Board: "Fig. 3" in `Explainer-Day`. Two rows on one ruler in solar masses. Each row has a `label` head ("BEFORE two black holes", "AFTER one black hole, and waves", the second part muted). Bars are 20 px tall with a 0.9 px outline. 36 is the mid screen on A1, 29 the mid screen on A2, 62 the weave of both at the light tone, and 3 is the solid live segment with the direct label "LEFT AS WAVES" beside it. Figures sit above their bars in D1 at 25 px. Two 0.6 px drop lines run from the edges of the 3 segment to the ruler. Legend: one screen swatch, "An estimate".

### 9.13 Analogy ("For scale")

A drawing, then one sentence. Board: "For scale" in `Explainer-Day`.

- Head row: `FOR SCALE` and `ILLUSTRATION, NOT TO SCALE` (or `DRAWN TO SCALE`, whichever is true).
- The drawing: the big thing as one 1.4 px beam with end caps and a label ("One arm, 4 km"). A 0.6 px lens circle at its end opens to a large detail circle by two leader lines. Centered in the detail, the familiar thing as a shape in the `plate` light screen with a 0.9 px outline ("A proton"), its width ruled off under it as a 1.4 px beam with 10 px end caps. On the same line, the paper's own value as the live mark: a beam so short it is only an end cap and the dot, with its label beside it ("Change in arm length").
- One sentence under it in `note`: "That strain is a change in arm length far smaller than a proton."

When both things can be drawn to one scale they share one ruler in a real unit, as in Plate 2 (the carbon atom on the angstrom ruler).

No perspective, no flat fills, one line weight per kind of mark.

### 9.14 Diagram (Fig. 1, the two detectors)

Board: "Fig. 1" in `Explainer-Day`. Two drawings in one figure.

1. One detector on open ground: an L of double-line arms with a box at each end and at the corner, the laser as a box feeding the corner, the light path as a thin line down each arm and back with small arrowheads, and three labels with dimension lines: "Arm, 4 km" on each arm and "Laser".
2. Full bleed under it: both detectors on a strip of the wave field, named above ("Livingston, Louisiana", "Hanford, Washington"). Two drop lines run from the corners to a millisecond ruler under the field. The live beam runs between them with the label "About 7 milliseconds later", and a carriage sits on the ruler under its dot.

The website's excerpt shows the second drawing only, in a column.

### 9.15 "Try it" (the slider)

Board: "Try it" in `Explainer-Day`. One control at hero scale, on a full-bleed plate of the wave field.

- The signal crosses the plate. The part already played is the live line with its pen point. The part not yet played is a 0.9 px muted line.
- The carriage on the ruler is the handle: a real `<input type="range">` laid over the ruler, 362 px wide and 44 px tall, with a 12 by 22 px square thumb in the text color and a transparent track. It has an `aria-label` and an `aria-valuetext` in words.
- Under it, a state row: `label` on the left ("Dragging"), a `note` on the right ("pitch rising").
- Then two thumbnails 165 px wide, each a small plate with its own ruler: "At rest, 35 Hz" and "At 0.2 seconds, 250 Hz", with the value in `readout-s` and the unit in T3.
- One instruction in `note`: "Drag the carriage along the ruler to move through the signal."

The artboard shows the dragging state as a still. The script that moves the line with the input is not part of the design files.

### 9.16 "How sure is this?" ledger

Board: `Explainer-Day`. A double rule (heavy on top), the head in `head-2` with its second voice, then rows split by full-measure hairlines.

```
<h3 style="margin: 12px 0 12px; font-family: DISP; font-size: 30px; font-weight: 800; font-stretch: 62.5%; line-height: 1; letter-spacing: -0.005em">How sure <span style="font-family: DISP; font-size: 30px; font-weight: 300; font-stretch: 100%; line-height: 1.06; letter-spacing: -0.012em; font-style: italic">is this?</span></h3>

<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid #16130F">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">
<div style="LABEL; color: #5A554B; flex: none">Significance</div>
<div style="font-family: DISP; font-size: 30px; font-weight: 800; font-stretch: 62.5%; line-height: 1; font-variant-numeric: lining-nums; text-align: right">SIGN_GT 5.1<span style="font-family: TEXT; font-size: 15px; line-height: 1; font-style: italic; margin-left: 6px">sigma</span></div>
</div>
<div style="font-family: TEXT; font-size: 15px; line-height: 1.4; font-style: italic; text-wrap: pretty">A false alarm this strong is expected less than once in 203,000 years.</div>
</div>
```

Rows, in this order:

- Subhead `STRENGTHS` (a `SLUG` between two hairlines): Review (the value is the PEER-REVIEWED or PREPRINT tag, the note is the journal and date), then the paper's own certainty figures (Significance, Detectors).
- Subhead `LIMITS`: each known limit (Distance, Masses, Sky position). A limit that is a range draws it: the Distance row carries a 124 by 30 px range bar beside its note (screened band 230 to 570, live marker at 410, a baseline from 0 to 600 with end ticks).
- The standing row `THIS EXPLAINER` with the sentence in `body`: "Machine written, and it can be wrong. Check it against the paper."

There is no "Open question" subhead in the boards, because `CONTENT.md` gives no open questions for Paper 1. When a paper's brief has open questions they take a third subhead, `OPEN QUESTIONS`, in the same row form. That subhead is spec, not rendered.

No score, no percent, no meter, no gauge, no traffic-light color, no colored dot.

### 9.17 Source footer

Double rule (heavy on top), slug `SOURCE`, the paper title in T3 at 17 / 1.4, the authors in T1 at 15 / 1.4 in the muted color, journal and date and license as two `label` lines in the muted color, then the outline button "Read the paper" 14 px below. Then the closing line in `note`: "This page was written by a machine and can be wrong. The paper is the source."

### 9.18 Explainer page order

`Explainer-Day`, top to bottom: top bar, tag row, headline, Plate 1, readout row, summary, key idea, then five sections, each opening with a double rule, a `SLUG`, and a two-voice `head-2`:

1. `THE QUESTION`: "Can a machine on Earth *feel space stretch?*"
2. `WHAT THEY DID`: "Two detectors, *each an L with 4 km arms.*" Holds Fig. 1.
3. `WHAT THEY FOUND`: "One chirp, *a fifth of a second long.*" Holds the caveat, Fig. 2, Fig. 3, For scale, and Try it.
4. "How sure *is this?*": the ledger (no slug, the head is the title).
5. `WHY IT MATTERS`: "Two firsts *in one signal.*"

Then the source footer. These five match the five `data-section` values in `pipeline/EXPLAINER-CONTRACT.md`.

### 9.19 Loading

Board: `Motion`, cell 02. No spinner. A `SLUG` "Loading new papers" on the left, a muted `label` "No signal yet" on the right, and under them one flat live line that sweeps across the sheet and then waits with its pen point pulsing. The first card replaces it. Copy under the line on the board ("A flat line: nothing to report yet. The first card replaces it. No spinner.") is a note to the reader of the board, not product copy.

### 9.20 Website

Board: `Site.dc.html`. One page, day theme only. Sections in order:

1. **Masthead.** Wordmark (a home link, 44 px tall), then two text links: "Source on GitHub" and "Download the APK" ("Source" and "Download" under 700 px). Double rule.
2. **Hero.** Display headline "New science / and math papers, / *explained in pictures.*". Beside it at 1160 and wider, under it below that: the slug "Android APK, from GitHub Releases", the slab "Download the APK", the outline button "Source on GitHub", the note "Not on Google Play yet." Then Plate 1, bleeding off the right edge, with its ruler. Under the plate: the readout and its label, a caption naming the paper with its journal link, the one-paragraph description, and the plate slug. Under 700 px the order is headline, slab, plate, readout, caption, paragraph, outline button, note, so the main action is on the first screen.
3. **The feed.** Slug "The feed", right slug "Free. No account. No ads." Head "Science and math, newly released. *Peer-reviewed and preprints.*" A phone mock (a 390 px sheet in a 1 px ink frame, square corners, no device chrome) showing the Paper 3 card with Plate 3 and the top of the Paper 2 card. A five-row ledger of what a card does, each row a label, a specimen of the real component, and one italic sentence: Labeled (the two badges), Linked (a journal link), Tuned (the rating row, "More like this" stamped), Your ratings (sentence only), Paywalled (the outline button).
4. **The explainer.** Head "Papers with a free full text *get a visual explainer.*" Then an excerpt of the Paper 1 explainer under an "Excerpt" head row: key idea, two short paragraphs with the caveat, Fig. 1, Fig. 2, Fig. 3, the ledger, the source footer.
5. **How an explainer is made.** Head "Three AI agents, *one job each.*" One figure, "Paper in, explainer out", slug "Illustration": a single live line runs left to right through three plates (lines of text, the ring field in its fine pass only, the ring field at full strength) and ends in a pen point. Under the plates, three two-voice sentences: Agent 1 of 3 "Reads the paper *as a domain expert.*", Agent 2 of 3 "Builds *the visuals.*", Agent 3 of 3 "Checks every number against the paper, *and checks the visuals are clear.*" Then a row "Every explainer": "*Machine written, and it can be wrong.*" and one sentence.
6. **Download.** Head "No account. No ads. *Free and open source.*" with the same slab, outline button, and note as the hero.
7. **Footer.** The wordmark at 150 px (fluid below 1160), and two ledger rows: Source (the GitHub address as a link) and Site (`[YOUR DOMAIN]`).

Layout: a 12 column grid with a 24 px gutter at 760 and wider, one column below. Breakpoints: 700 (plate height, section head size), 760 (grid), 930 (plate height), 1160 (desktop type scale, 56 px margins, hero in two columns). The hero plate is 230 px tall under 700, 284 from 700, 318 from 930, 354 from 1160, each its own drawing of Plate 1 at that width. The phone mock is scaled with `zoom` in steps from 0.71 to 1 so it fits its column.

Checked at 1440, 1160, 1024, 900, 768, 700, 390, and 360 wide: no horizontal overflow, no target under 44 px. Looked at in full at 1440, 1024, 700, and 390.

### 9.21 Brand

Board: `Brand.dc.html`.

- **Wordmark.** `Paper` in D1, `boy` in D4, the pen point on the baseline. Clear space: one x-height on every side. Sizes: 38 px web masthead (dot 6.5, gap 3), 33 px app masthead (dot 6, gap 3), 22 px the smallest (dot 4, gap 2). One-color versions: all ink on stock, all stock on ink, with the dot in the same color. Night: D2 and D5 with the amber dot.
- **App icon, large master** (above 96 px), on a 512 grid: the P of the wordmark in ink on a stock trap, the pen point at 43 px radius, and rings at 8 px pitch centered on the pen point that swell as arcs. No mask.
- **App icon, small master** (96 px and under, and launchers): the same grid redrawn. Five rings at 24 px pitch and one weight, pen point at 56 px radius, the P unchanged.
- **Rules.** Clear space: one pen point diameter. Smallest: 48 px. Under that, the one-color mark.
- **Launcher layers** (Android adaptive icon): background (the ground and the rings), foreground (the P on its trap and the pen point), monochrome (the P and the pen point in one color), each 108 by 108 dp, with the 66 dp safe zone drawn. Shown under a circle, a squircle, and a rounded square.
- **Night icon.** `ground`, `plate-night` rings, the P in `light`, the pen point amber. Its halo is engraved: amber rings that thin as they leave the pen point. There is no blur and no opacity halo in the icon.

The board is static. It has no animation.

## 10. Layout rules that hold everywhere

1. The headline comes before the plate. The front page leads with words.
2. One plate, one readout, one primary action per card.
3. Reading text sits on open ground. Nothing printed or drawn runs behind it.
4. Hierarchy comes from type size and the two voices, then from rules. Never from boxes, tints, or bars.
5. Forbidden without exception: any box, card, callout, or tab with a colored stripe or bar on a side edge; any vertical accent rule beside text; emoji; gradient washes; rounded gray cards; fake status bars; all-caps headlines; glow on anything but the live line at night. This holds for every frame of an animation too: the stamp floods the whole button at once and never passes through a button with a filled left edge.

## 11. Day and night at a glance

| | Day | Night |
|---|---|---|
| Ground | `#E9E6DE` | `#0E1116` |
| Text | `#16130F` | `#E9E4D7` |
| Muted text | `#5A554B` | `#9C988D` |
| Rules, outlines, ruler | `#16130F` | `#9C988D` |
| First voice | D1 (800) | D2 (900) |
| Second voice | D4 (300 italic) | D5 (400 italic; width 87.5 in headlines) |
| Readout tracking | −0.005em | 0.02em |
| Plate rings | `#1F3FD0`: 0.5 px rings, swells to 1.5 and 2.3 px | `#4D63C9`: 0.6 px rings at 0.55 opacity, swells to 1.4 px only |
| Black layer | `#16130F` contours | `#9C988D` contours |
| Live line | 1.9 px `#E0330A` on a 7 px stock trap | 1.9 px `#FFA63D` on a 4 px ground trap, under it a three-stroke halo (17, 11, 6 px) |
| Pen point | 3.6 px on a 6.5 px stock dot | 3.4 px on a 5 px ground dot, with a three-disc halo (13, 10, 6.5 px) |
| Primary slab and solid tag | ink, stock text | light, ground text |
| Stamped rating | `#5A554B`, stock text, check | `#9C988D`, ground text, check |
| Range screen | ink | `#9C988D` |
| Grid and drop lines | `#5A554B` | `#5E6573` |

## 12. Motion

Three verbs and one loop. Nothing bounces, nothing overshoots, nothing else loops.

Keyframes, as the final boards carry them:

```
@keyframes press{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}
@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}
@keyframes inkproof{from{clip-path:polygon(0% 0%,0% 0%,-16.3% 100%,0% 100%)}to{clip-path:polygon(0% 0%,116.3% 0%,100% 100%,0% 100%)}}
@keyframes sweep{from{stroke-dashoffset:1.003}to{stroke-dashoffset:0}}
@keyframes travel{from{offset-distance:0%}to{offset-distance:100%}}
@keyframes orbit{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}
@keyframes drop{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:none}}
@keyframes flood{from{opacity:0}to{opacity:1}}
@keyframes stamp{0%{transform:none;background-color:transparent;border-color:#16130F;color:#16130F}1%{transform:scale(1.1);background-color:transparent;border-color:#16130F;color:#16130F}100%{transform:none;background-color:#5A554B;border-color:#5A554B;color:#E9E6DE}}
@keyframes iconout{from{opacity:1}to{opacity:0}}
@keyframes iconin{from{opacity:0}to{opacity:1}}
@keyframes growx{from{transform:scaleX(0)}to{transform:none}}
@keyframes ridex{from{transform:translateX(-100%)}to{transform:none}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
```

The 16.3% in `inkproof` is for a 390 by 196 plate. For another size it is `|height / tan(72 degrees)| / width × 100` (`ink_keyframes()` in `lib.py`). The website uses a pixel form of the same wipe so one keyframe serves a fluid width (`wipeS`, `wipeM`, `wipeN`, `wipeL`, one per plate height). The night `stamp` uses `#9C988D` for the border and fill and `#0E1116` for the final label color.

`sweep` starts at 1.003, not 1.01. The line trails the pen point by that fraction of the path's length at the start of the sweep. At 1.01 that was 9 px on the phone plate, hidden under the pen's ground dot, but 19 px on the 1,864 px path of the desktop hero, where the pen visibly ran ahead of the line. At 1.003 it is 6 px at most and stays under the 6.5 px dot. The value must stay above 1, or the round cap shows as a dot at the start of the path before the sweep begins.

| Name | What it does | Duration | Delay | Easing | Seen in a render |
|---|---|---|---|---|---|
| **Press** | A line of type lands: opacity 0 to 1 and a 6 px rise. Lines stagger 50 ms. Four steps at most. A chart label presses in as its mark arrives. | 190 ms | 0, 50, 100, 150 ms | `cubic-bezier(0.2, 0, 0, 1)` | yes |
| **Ink wipe** | The plate inks in from the left along the 72 degree screen angle. | 520 ms | 60 ms | `cubic-bezier(0.2, 0, 0, 1)` | yes |
| **Register** | The blue layer starts 5 px right and 3 px up, the black layer 5 px left and 3 px down. Both slide into exact register. | 480 ms | 60 ms | `cubic-bezier(0.16, 1, 0.3, 1)` | not in a timed frame. Confirmed by reading the layer transforms at paused times (`register_probe.py`): 5 px off at 60 ms, 2.1 px at 120 ms, 0.14 px at 300 ms, exact at 540 ms. The ink wipe has uncovered only a quarter of the plate at 120 ms, so most of this move is hidden. |
| **Sweep** | The live line draws from start to end at constant speed. Trap, halo, and core share the keyframe and timing. `pathLength="1"`, `stroke-dasharray: 1 1.5`. | 1900 ms (1400 to 2200 allowed; a short beam 600 to 900) | 320 ms | `linear` | yes |
| **Travel** | The pen point, its ground dot and halo, and the carriage follow the same path with `offset-path`. | same as its sweep | same | `linear` | yes |
| **Orbit** | For a ring-shaped live line: the pen point rides a rotating group while the circle sweeps. | 1800 ms | 520 ms | `linear` | yes (website, Plate 3) |
| **Pulse** | After the sweep the pen point breathes, opacity 1 to 0.55 and back. The only loop on a screen. | 2400 ms, infinite | 2400 ms | `ease-in-out` | yes |
| **Drop** | A marker drops onto its band: opacity 0 to 1 and a 12 px fall (the 410 marker). | 260 ms | when in view | `cubic-bezier(0.2, 0, 0, 1)` | yes |
| **Flood** | A solid live mark appears in place: opacity 0 to 1 (the "3" segment, the arm-change mark). | 260 ms | when in view | `cubic-bezier(0.2, 0, 0, 1)` | yes |
| **Stamp** | A rating tap. The whole button jumps to scale 1.1 on the tap and settles to 1 while its fill floods the whole surface at once. No wipe, no moving edge. On the motion board the label color and the icon change over in one step at 60 ms, so the words are readable in every frame. The night feed board cross-fades them across the 120 ms instead. Build the 60 ms step. | 120 ms | on the tap | `cubic-bezier(0.2, 0, 0, 1)` | yes, with held frames at 0, 24, and 120 ms on the motion board |
| **Feed up** | Feed to explainer. The plate, its readout, and the summary stay where they are. The sheet under them (the buttons) feeds up and the key idea takes its place. | 360 ms | on open | `cubic-bezier(0.2, 0, 0, 1)` | as three held frames (0, 180, 360 ms) on the motion board |
| **Wordmark lands** | At app launch only: "Paper", "boy", and the pen point Press in, 50 ms apart. The dot lands last and rests. It never pulses. | 190 ms each | 0, 50, 100 ms | `cubic-bezier(0.2, 0, 0, 1)` | yes |
| **Loading** | A flat live line sweeps across, then its pen point pulses until the first card arrives. | sweep 1900 ms, then Pulse | 320 ms | `linear` | yes |
| **Line through plates** | Website only. The live line through the three agent plates grows left to right with its pen point riding the end (`growx`, `ridex`). | 1600 ms | 900 ms | `linear` | yes |

Rules:

1. Headline and summary are readable within 200 ms. A card is at rest by 2.6 s (the sweep ends at 2220 ms).
2. The brief's "about 200 px per second" cannot hold for a chirp, whose path is far longer than the plate is wide. The duration range governs: constant speed along the path, 1400 to 2200 ms.
3. Only the first plate in view sweeps on arrival. A plate or a figure that scrolls into view later draws in once. Nothing replays on its own.
4. In an explainer every figure's one live mark has a draw-in: the 7 ms beam sweeps with its carriage, the 410 marker drops, the "3" segment floods, the arm-change mark floods, the "Try it" plate inks in. The artboards stagger these with delays (2280 to 4950 ms) so frames can show them. In the product each runs once when its figure comes into view.
5. The resting frame is designed first: plate in register, line fully drawn, pen point parked at the end, carriage under it. With reduced motion every animation is removed and that frame is what shows. The inline styles already describe it (`offset-distance: 100%`, no dash offset, opacity 1), so nothing is missing. All seven boards were rendered with reduced motion on: zero running animations, and every still is complete (`design/shots/final/reduced/`).
6. The motion board's cells replay every 5.4 s so the board can be watched. That is a property of the board, not of the product.
7. To check motion: `--frames 0.2,1.5,4` for a card, `--frames 7 --full` for an explainer's resting frame, and `design/scratch/final/start_state.py` for anything in the first 300 ms.

## 13. Build notes

`design/HANDOFF.md` is the build document. These are the facts behind it.

- **Line trim and pen position.** `PathMeasure` has `getSegment(startDistance, stopDistance, destination, startWithMoveTo)`, `getPosition(distance)`, `getTangent(distance)`, and `length` (developer.android.com/reference/kotlin/androidx/compose/ui/graphics/PathMeasure, read 2026-11-13). `getPosition` and `getTangent` are marked as added in 1.4.0. That covers Sweep, Travel, and the carriage, and with one progress value for all three the pen cannot run ahead of the line.
- **Blend modes.** The system uses none. If one is ever added: the BlendMode reference marks `Multiply`, `Screen`, and others "can only be used on Android API level 29 and above", and the app's `minSdk` is 24.
- **Variable fonts.** The Compose fonts guide says "Variable fonts are only supported on Android O and above" and tells apps to guard with `Build.VERSION.SDK_INT >= Build.VERSION_CODES.O` and a static fallback (developer.android.com/develop/ui/compose/text/fonts, read 2026-11-13). The app's `minSdk` is 24, below Android O (API 26). The Google Fonts repository ships only the variable files for all three families (five files, listed in `HANDOFF.md`). It has no static instances.
- **The ring swell.** It is no longer a mask. Each swell is a closed path of two arcs, and each ring is a circle. A comment in `lib.py` proposes `Path.arcTo` twice per swell in Compose. That call was not checked against the Compose reference.
- **Adaptive icon.** The Android guide says: "Size all layers to 108x108 dp", the logo is "at least 48x48 dp" and "must not exceed 66x66 dp, because the inner 66x66 dp of the icon appears within the masked viewport", and "the outer 18 dp on each of the four sides of the layers is reserved for masking" (developer.android.com/develop/ui/views/launch/icon_design_adaptive, read 2026-11-13). The brand board's layers follow those numbers.
- **How the app gets a card's plate** (native drawing, or pictures made from the explainer) is not decided. `HANDOFF.md` section 4.6 lays out what the design needs from either route.
- **Web.** Plain HTML, CSS, and inline SVG. `offset-path: path()`, `clip-path: polygon()` animations, and `zoom` were seen working only in the local Chromium renderer, not in the Claude Design canvas and not in other browsers.

## 14. Open items for the owner

1. The theme button in the feed masthead: keep, or follow the phone's setting with no button.
2. The masthead strap "Science and math, newly released": approve or replace.
3. "First Light" stays an internal name unless he says otherwise.
4. A rating row at the end of the explainer, under "Read the paper". The critique suggested it. It was not added, because nobody asked for it.
5. Text size in the explainer: the design's labels are 10.5 px and its tags 10 px. `pipeline/EXPLAINER-CONTRACT.md` fails any text under 11 px. One of the two has to move (`HANDOFF.md` section 4.7).
6. The short card on the night feed uses Paper 3, which is open access, as its stand-in. If he wants the board to show a truly paywalled paper, `CONTENT.md` needs one.
