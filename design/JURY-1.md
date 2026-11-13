# Jury 1: three explorations of First Light

Judge: creative director. Date: 2026-11-13.

## What was looked at

Every file was rendered fresh with `design/tools/dc_shot.py` on 2026-11-13. The screenshots left by the earlier, interrupted run were not used.

| File | Render | Result |
|---|---|---|
| `Cand-x-Feed.dc.html`, `Cand-y-Feed.dc.html`, `Cand-z-Feed.dc.html` | 390 by 844, frames 0.2, 1.5, 4 s | `overflow_x` false, no console errors, all named fonts loaded |
| `Cand-x-System.dc.html`, `Cand-y-System.dc.html`, `Cand-z-System.dc.html` | 1200 by 1700, frames 1 and 4 s, read as three crops each | `overflow_x` false, no console errors, all named fonts loaded |

PNGs are in `design/shots/jury/` (crops in `design/shots/jury/fresh/`).

The first frame the tool captures is later than its label says. The 0.2 s frame of every feed already shows the line about a third drawn. Early motion states were therefore checked on the lock proof with a start delay (`design/shots/jury/hold/sheet.png`, `design/shots/jury/hold3/sheet.png`), not on the candidates.

## Reference points for the scores

Each score is held against work at the top of its field: the print covers and feature openers of Bloomberg Businessweek and The New York Times Magazine for type, The Pudding and the NYT graphics desk for honest charts with a voice, and Apple Design Award and Google Play Best Of winners for motion and finish on a phone. A 9 means it could stand next to those as it is. No candidate reaches 9 in any category. None passes the rubric (no category below 8 and 68 of 80). That is normal for a first pass.

No candidate contains an item from section 8 of the brief, so none is zeroed.

## Scores

| Category | x Engraved Broadsheet | y Two-Ink Overprint | z Strip Chart |
|---|---|---|---|
| Typography | 8 | 6 | 7 |
| Color | 6 | 7 | 6 |
| Graphic language | 7 | 6 | 6 |
| Motion | 7 | 7 | 7 |
| Originality | 7 | 6 | 6 |
| Fit to the owner's direction | 6 | 5 | 5 |
| Legibility and accessibility | 6 | 7 | 7 |
| Buildability | 7 | 6 | 8 |
| **Total of 80** | **54** | **50** | **52** |

## x, Engraved Broadsheet: 54

**Typography 8.** The only candidate with a real front-page voice. Noto Serif Display 800 at width 62.5 against its own 300 italic at full width gives two voices from one family, and the turn happens inside the headline ("merged. *Earth felt space stretch.*"). The wordmark uses the same turn. Readouts are typeset properly: a real multiplication sign, a raised exponent, a real minus. It loses points for mono labels at 8.5 to 9.5 px and a 13.5 px italic source link, which are too small on a phone.

**Color 6.** One hot ink on gray stock is disciplined and the leader is clear. But in the feed the color is one thin line and one dot. The screen reads as black and white. Night exists only as a band on the tile, where the plate turns to a flat gray-blue and loses its tone.

**Graphic language 7.** The engraved wave field is the best single piece of drawing in the three: fine rings that swell where a crest crosses them, so tone comes from line weight and never from gray. The two wells are a contour map built from the 36 to 29 mass ratio. Plate 3 (M87) is better still, because the vermilion ring is drawn inside the engraving. In the feed the line and the plate do not touch. The plate is a still picture and the live line is a 60 px strip on bare ground under it.

**Motion 7.** Press on the headline lines, a wipe along the screen angle, a constant-speed Sweep with the pen point leading, one pulse loop, and a complete reduced-motion frame. Register is a single layer sliding 5 px, so it is a slide, not two plates locking.

**Originality 7.** It could not be mistaken for a template. The risk named in the brief is real, though: without the engraving it would be cream paper and a serif.

**Fit 6.** It is mostly A. B's instrument is present as a ruler, a readout, and a strip. The night side is not designed as a screen.

**Legibility 6.** All contrast pairs pass and targets are 44 px. The small labels hold it down.

**Buildability 7.** Strokes, pattern fills, a clip-path wipe, a path-length reveal. Two things need care: the swelling rings use an SVG mask, and the display face depends on the width axis of a variable font.

## y, Two-Ink Overprint: 50

**Typography 6.** Bricolage Grotesque 800 has character. The second voice is the same face at 300 in blue, which is a weight change and a color change with no change of voice. The headline breaks after one word of the second voice ("Earth" alone, then "felt space stretch."). The large wordmark has letters colliding (the r into the b).

**Color 7.** The best color thinking of the three. The overlap was sampled from the render, there is no black, and the split plate that is darkest where inks overlap by day and brightest where lights overlap by night is the clearest statement of "same geometry, opposite physics" anyone made. It loses points because blue, pink, and indigo sit at near equal strength across the page, and because pink is promised to the live line and then also used for a bar, a masthead rule, and a second line in the analogy.

**Graphic language 6.** The screens carry real tone. But two overlapping discs read as a Venn diagram, the designer's own notes say earlier versions read as eyes, and the live line slips under the bottom of the discs without a clear relationship to them.

**Motion 7.** The only true two-plate Register. Sweep and the single loop are correct.

**Originality 6.** Two-color risograph in blue and pink is a known genre.

**Fit 5.** It reads as A plus C. The owner rejected C, the flat-color poster, and the full-bleed blue key idea band and the saturated primary button pull this toward it. B appears only in the night half of one plate.

**Legibility 7.** 16 px body, blue text at 6.3:1 or better, pink never carries small text. Labels are 9.5 px.

**Buildability 6.** The look depends on multiply and screen blends with isolated groups. `BlendMode.Multiply` is documented as Android API 29 and above (developer.android.com/reference/kotlin/androidx/compose/ui/graphics/BlendMode), and the app's `minSdk` is 24 (`app/build.gradle.kts` line 31).

## z, Strip Chart: 52

**Typography 7.** Big Shoulders 700 with Literata italic on one baseline is a good idea and the headline is as large as the others. The two faces have different proportions and the join is a little rough. B612 Mono at 10 px is the most readable label of the three.

**Color 6.** Calm and coherent, with a clear leader. By day it is gray-green and quiet to the point of drab, and viridian is a cool signal, not a hot one. The phosphor night is the best night of the three.

**Graphic language 6.** The best charts: ruler axes in the paper's own unit, the range chart with a solid value on a screened band, direct labels with leaders. But the hero is graph paper. There is no line-screen tone anywhere in it, which is the brief's fourth principle, and the grid cut-outs behind the readout and the note are fussy.

**Motion 7.** The pen carriage riding the ruler while the nib writes the line is the best single motion idea in the three. Register is unused and the paper advance was not something I could see in the frames.

**Originality 6.** The carriage is memorable. The day feed around it is close to a lab notebook theme.

**Fit 5.** It is B with a day theme. The headline sits under the chart, so the front page is gone, and the solid dark masthead band on a light sheet is two styles side by side.

**Legibility 7.** 17 px body, 10 px labels, states told apart by form.

**Buildability 8.** Flat strokes, lines, and a path-length reveal. No masks and no blends.

## Winner: x, Engraved Broadsheet

It wins on the two things the owner asked for by name and that are hardest to add later: better fonts and better graphics. Its headline and its engraved plate are the only parts of any candidate that are close to award level today. Its weaknesses are the ones another candidate has already solved, so they can be grafted.

## Grafts

From **z, Strip Chart**:

1. The pen carriage. A block rides the plate's ruler axis under the pen point for the length of the Sweep.
2. The ruler in the paper's own unit as the bottom edge of the plate.
3. The range chart: a solid mark for the reported value on a line-screen band for the range.
4. Label size. Nothing in mono under 10 px.

From **y, Two-Ink Overprint**:

1. A second print ink. Blue `#1F3FD0`, which was A's own ink, becomes the plate ink. It is print only: never text, never chrome.
2. True two-plate Register: the blue layer and the black layer start 5 px and 3 px apart in opposite directions and lock.
3. The knockout trap: where the live line crosses ink it rides on a ground-colored stroke.
4. Night as light: the plate is drawn in a blue light by night and the line carries the picture.

All eight grafts were drawn and rendered before locking, in `design/scratch/director/LockProof-Day.dc.html`, `LockProof-Night.dc.html`, `LockParts-Day.dc.html`, and `LockParts-Night.dc.html` (renders in `design/shots/jury/lock/`). A black-ink version of the same plate was rendered next to the blue one (`LockProof-Day-ink`). The blue plate was chosen: it gives the feed the color mass A had, it makes night a designed light table, and it removes the cream-and-serif risk.

## Must fix in production

1. **The line must cross the plate.** In `Cand-x-Feed` the live line sits under the plate on bare ground. The locked hero puts it across the lower third of the plate, on a trap.
2. **Night feed.** Not drawn by the candidate. The lock proof draws one card. Production draws the full screen.
3. **Labels.** Mono labels 10.5 px, tags 10 px, source link 15 px.
4. **Second voice needs markup.** The content pipeline must mark the clause that turns italic. An unmarked headline is set all roman.
5. **Long journal names.** "The Astrophysical Journal Letters" does not fit beside two tags at 390 px. The lock proof lets the link wrap to its own row. Confirm on every card.
6. **Pink is gone, vermilion is rationed.** Vermilion is the live mark only: the line, its pen point, the wordmark dot, and the one reported value in a figure.
7. **The well figure.** With a blue field, the paper-colored contour figure has a hard outer edge and can read as an island. Test a softer boundary before the feed is final.
8. **Android build points, to confirm before code:** variable font axes need Android O or later and `minSdk` is 24; the ring swelling uses an SVG mask; `BlendMode.Multiply` is API 29 and above. `SYSTEM.md` section 13 gives the route around each.
9. **Unrequested items to put to the owner:** the theme toggle in the masthead (all three candidates added one) and the masthead strap "Science and math, newly released" (composed from the product facts, not supplied copy).

## Not verified

- The Claude Design canvas runtime. Only the local screenshot tool was used.
- The rating stamp and the feed-to-explainer transition. Neither was drawn by any candidate or by the lock proof.
- Desktop sizes above the style tile's 66 px display.
- Whether Google Fonts ships static instances of Noto Serif Display at width 62.5.
