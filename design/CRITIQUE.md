# Critique: the seven First Light boards

Judge: independent. Date: 2026-11-13. I made none of this work.

## What was looked at

Every board was rendered fresh with `design/tools/dc_shot.py` and every PNG was read. Renders are in `design/shots/judge/` (crops in `design/shots/judge/crops/`).

| Board | Render | Tool result |
|---|---|---|
| `App-Feed-Day`, `App-Feed-Night` | 390 by 844, frames 0.2, 1.5, 4 s | `overflow_x` false, no console errors, three families loaded |
| `Explainer-Day` | 390 wide `--full` (5,464 px), read as seven slices, plus frames 0.2, 1.5, 4 s of the first screen | same |
| `Explainer-Night` | 390 wide `--full` (1,800 px), read as two slices, plus the three frames | same |
| `Site` | `--full` at 1440 (4,522 px, five slices) and at 390 (6,513 px, eight slices), plus the three frames of the first screen at both widths | same |
| `Motion` | 1200 by 1000, frames 0.3, 1, 2, 3.5 s | same |
| `Brand` | 1200 by 900, frames 1 and 4 s | same |

Also measured with a script (`design/scratch/judge/targets.py`): the size of every link, button, and input, and every computed text size, on every board.

## Reference points

Type is held against the feature openers of The New York Times Magazine and Bloomberg Businessweek. Charts are held against the NYT graphics desk and The Pudding. Motion and finish on a phone are held against Apple Design Award and Google Play Best Of winners. A 9 means the board could stand next to those as it is.

## Result

No board passes the rubric (no category below 8, and 68 of 80). Two boards are within reach of it. The day feed and the motion board are the strongest. The night feed is the weakest. The set is clearly one product.

| Category | Feed Day | Feed Night | Explainer Day | Explainer Night | Site | Brand | Motion |
|---|---|---|---|---|---|---|---|
| Typography | 8 | 7 | 8 | 8 | 7 | 8 | 8 |
| Color | 8 | 6 | 7 | 6 | 8 | 8 | 8 |
| Graphic language | 8 | 6 | 7 | 7 | 7 | 7 | 8 |
| Motion | 8 | 7 | 6 | 7 | 6 | 7 (static by brief) | 7 |
| Originality | 8 | 7 | 8 | 7 | 8 | 8 | 8 |
| Fit to the owner's direction | 8 | 6 | 7 | 7 | 8 | 8 | 8 |
| Legibility and accessibility | 7 | 7 | 8 | 8 | 7 | 7 | 7 |
| Buildability | 7 | 8 | 8 | 8 | 8 | 6 | 8 |
| **Total of 80** | **62** | **54** | **59** | **58** | **59** | **59** | **62** |
| **Overall of 10** | **7.8** | **6.8** | **7.4** | **7.3** | **7.4** | **7.4** | **7.8** |

## The owner's hard rules, checked one by one

| Rule | Result |
|---|---|
| No box, card, callout, or tab with a colored stripe or bar on its left edge | No board has one as a resting design. **One risk, in `Motion` cell 06:** the frozen frame "12 ms after the tap" is a still picture of a button with a solid black slab on its left edge, and at the start of each loop a thin vertical sliver shows on the left edge of the live button. It is an ink flood caught halfway, but as a picture it is the form he said he hates. Fix 1 under Motion. A second, smaller risk is in cell 07 (fix 2 under Motion). |
| No bland default look | Passed on every board. Nothing here could be mistaken for a template. The night feed is the closest to plain: most of that screen is the day layout with the colors swapped. |
| Better fonts | Passed. Noto Serif Display 800 at width 62.5 against its own 300 italic is a real two-voice headline, and it holds on all seven boards. Weak points: the hairline multiplication sign and greater-than sign next to weight 800 numerals, and three bad wraps on the site. |
| Better graphics | Passed by day. The engraved wave field and the chirp on its trap are well beyond mockups A and B. Weak points: the well figure still reads as a pair of eyes, the AlphaFold plate is a striped field, and by night the halo reads as a brown casing, not as light. |
| Better animations | Passed on the feed and the motion board. The explainer and the site each animate only their first screen. |
| Real facts only | Passed with one exception. Every number traces to `CONTENT.md`. The exception: `Explainer-Day` files the sky position under a subhead "Open question". The content file lists it as a limit and gives no open questions. |
| No em dashes | Passed. Zero in all seven files. |
| No emoji, gradient washes, rounded gray cards, fake status bars | Passed. The only gradient function is the PREPRINT hatch the system allows. The only round shapes are dots. |
| Touch targets 44 px | Passed everywhere except the wordmark home link on the site (42 px tall at 1440, 37 px at 390). |

## Coherence: do the five designers' boards look like one product?

Yes. The three families, the color tokens, the tag row, the ink slab, the rating row, the double rule, the figure head row, the ledger, and the ruler with its carriage are the same objects on every board. A stranger would say one hand made all seven. That is the strongest thing about the set.

The seams, in order of how much they show:

1. **Plate 1 is drawn two ways.** `App-Feed-Day` has rings with spiral crests and a well figure whose edge fades into the field. `Explainer-Day`, `Explainer-Night`, `Site`, and `Motion` cell 03 have evenly banded rings and a larger well figure with a hard closed outline (the "island" that Jury 1 item 7 asked to soften). The feed's version is the better drawing. All five boards should call one generator.
2. **Fig. 1 is drawn two ways.** `Explainer-Day` draws the detectors as double-line arms with end boxes and puts the 7 ms beam under the field. `Site` draws them as single-stroke Ls with T caps and puts the beam above the field. The site says it is showing an excerpt of the explainer, so it should show the explainer's figure.
3. **The rating stamp is built two ways.** `App-Feed-Night` fills the whole button at once. `Motion` cell 06 wipes the fill in diagonally from the left edge. `SYSTEM.md` section 12 describes the first.
4. **Paper 3 is two different cards.** In `App-Feed-Night` it is the short paywalled card with no plate and "Read the paper". In `Site` it is a full card with Plate 3 and "See it explained". `CONTENT.md` says Paper 3 is open access, so the site's card matches the facts and the feed's use of it as the paywalled example does not. The feed designer was told to use Paper 3 for the short card, so this one is for the director to settle, not the designer.
5. **The night halo is weak in the same way on four boards** (`App-Feed-Night`, `Explainer-Night`, `Motion` cell 04, `Brand` section 04). It is a system value, not a designer error. See "System-level fixes".
6. **The AlphaFold figure has two looks.** A plate with a striped field in `App-Feed-Night`, and the same marks on open ground in `Motion` cell 05. The open-ground version is clearer.
7. **The wordmark dot pulses in `Motion` cell 01 and nowhere else.** No masthead on any other board pulses its dot.

## System-level fixes (for the director, they change `SYSTEM.md`)

1. **Night halo, section 5.3.** The 7 px ground trap sits under a 7 px halo at 0.22 opacity, so the halo never touches the plate. What shows is the trap tinted amber: `#0E1116` plus 22 percent `#FFA63D` is about `#43321F`, a dark brown band. On the blue rings it reads as a brown casing around the line, and in the fast part of the chirp the casings merge into one brown block about 60 px wide. Change to: ground trap 4 px, then the halo as an 11 px stroke at about 0.16 opacity drawn over the plate so the ring lines under it turn warmer and brighter, then the 1.6 px core. Pen point: ground dot 5 px radius, halo 10 px radius at about 0.18. Render it and confirm the area around the line looks brighter than the plate, not darker.
2. **Night plate strength, section 3.2.** `plate-night` `#4D63C9` at all three ring weights covers about a quarter of the first night screen and is the brightest mass on it. The brief says the print layer goes dim at night and the line carries the picture. Drop the 1.85 px ring pass at night (keep 0.6 and 1.15), or draw that pass in a darker blue near `#3B4C9E`, and compare the two in a render at arm's length. The amber line should be the first thing seen.
3. **The multiplication sign and the greater-than sign.** In `1.0 × 10⁻²¹` and `> 5.1` the signs come from the display face as hairlines beside weight 800 numerals, so the readout reads as "1.0  10" at a glance. Draw both as inline stroke SVG at 2 px (0.5em box), or set them from Source Serif 4 at weight 600.
4. **Night chrome.** Rules, button outlines, and the stamped slab are all full-strength `light` at night, the same rank as text. Step the non-text chrome down to `light-muted` `#9C988D` (6.56:1 per `SYSTEM.md`): card dividers, outline button borders, tag outlines. Keep text and the one primary slab at `light`. This is what makes night a designed screen and not a swap.
5. **Stamped state.** A stamped rating is the same solid slab as the primary action. Set the stamped fill one step down (`ink-muted` by day with stock text, 5.94:1 per `SYSTEM.md`; `light-muted` by night with ground text, 6.56:1) and swap the plus for a check, so the primary action stays the heaviest thing on the card and the state is not carried by fill alone.
6. **A question, not a fix.** `SYSTEM.md` 4.2.1 draws the "3 solar masses" segment solid. `CONTENT.md` says "about 3". Solid is supposed to mean sure. Decide whether the live mark is exempt from that rule and say so in the system.

## App-Feed-Day.dc.html: 62 of 80

The best board. The headline, the plate, and the sweep work together, and the resting frame is complete.

1. **The well figure reads as a pair of eyes.** Where: Plate 1, upper right. Two dark discs (blue hatch on solid ink) inside ringed contours look like pupils in goggles. Mockup A was marked down for the same thing. Make it: remove the solid dark discs. Close each well with three or four more contour lines tightening to its center, so the wells read as depth. Keep the 36 to 29 size ratio.
2. **The end of the live line looks like jitter.** Where: the last 60 px of the chirp, from about 0.21 s to the pen point. The decaying cycles are under 4 px wide and show as small uneven kinks. Make it: three clean decaying cycles after the peak, then a flat run of at least 30 px into the pen point. Regenerate with `chirp()`, do not hand-edit the path.
3. **The hairline multiplication sign.** Where: the readout `1.0 × 10⁻²¹`. See system fix 3.
4. **The second card is cut through its letters.** Where: the bottom edge. Only the top 20 px of "A neural network" shows, which looks like a rendering fault in a still. Make it: move the crop into the gap after the tag row (the headline starts at or below y = 846), so the screen ends on the Biology tag row and the Nature link.
5. **Interference patches in the rings.** Where: top center of the plate, around x 250 to 300, y 250 to 270, where the finest rings converge. Make it: drop the 0.5 px pass inside a 40 px radius of the ring center, or open the ring pitch there to 4 px.
6. **Use this plate everywhere.** This board's softened well edge is the right one. Move it into the shared generator so the explainer, site, and motion boards get it (coherence item 1).
7. **Build notes to carry forward.** The ring swelling is an SVG mask and the headline needs the width axis. Both are named in `SYSTEM.md` section 13 and neither is solved yet.

## App-Feed-Night.dc.html: 54 of 80

The weakest board. It proves the short card, the preprint card, and the stamp, but it does not prove night.

1. **The screen is the day layout with the colors swapped.** Where: everything below y = 100. The only color is one 2 px amber beam in the top strip. Make it: apply system fixes 4 and 5 (chrome stepped down to `light-muted`, stamped fill one step down with a check). Then the order on screen is text, amber, structure, which is a designed night.
2. **The halo is a brown casing.** Where: the amber beam and its pen point at the top of the screen. Make it: system fix 1.
3. **Plate 2 is a striped field.** Where: the top 100 px, and the whole plate in `design/scratch/feed/Proof-Hero2-Night`. One line screen floods the plate and ramps in tone from left to right with no subject. The brief caps graphic language at 6 for texture used as wallpaper. Make it: remove the field. Draw the carbon atom and the two beams on open ground, as `Motion` cell 05 does, and label all three at the mark: "AlphaFold, 0.96 Å", "Next best, 2.8 Å", "Carbon atom, about 1.4 Å". The gray beam has no label on the plate today.
4. **The stamped button outweighs the card's own action.** Where: the Paper 3 card. After the tap, "More like this" is a full light slab and "Read the paper" above it is an outline. Make it: system fix 5.
5. **The wrapped journal link crowds the tags.** Where: the Paper 3 tag row. "The Astrophysical Journal Letters" wraps to its own line with a row gap of 0, and its top nearly touches the PEER-REVIEWED box. Make it: `row-gap: 6px` on the wrapping row.
6. **The numerals in "42" touch.** Where: the Paper 3 stat at weight 900, width 62.5. Make it: `letter-spacing: 0.02em` on readouts at night.
7. **The screen opens on half a disc.** Where: the top edge. The plate is cut so that the carbon atom is an unexplained blue arc. Make it: after fix 3, scroll so at least 150 px of the plate shows, with the atom whole. If that pushes the preprint card's summary off the bottom, keep the title and the PREPRINT tag in view.

## Explainer-Day.dc.html: 59 of 80

Honest, well typeset, and complete. All four forms from the brief are present and none is a box. It loses points for stillness and for one content slip.

1. **Only the first 440 px of a 5,464 px page move.** Where: Fig. 1, Fig. 2, Fig. 3, "For scale", and "Try it" are stills. The product promise is animated diagrams. Make it: give each figure's one live mark its own draw-in, with the same keyframes as the hero. Fig. 1: the 7 ms beam sweeps from 0 to 7 with a carriage on the ms ruler. Fig. 2: the 410 marker drops onto the band. Fig. 3: the "3" segment floods in last. In the artboard, stagger them with delays so the frames show it. In production each runs once when it scrolls into view. How that trigger is built in the WebView was not checked here.
2. **"Open question" is not in the content file.** Where: the ledger, the subhead above "Sky position". `CONTENT.md` lists the sky position as a limit and has no open questions. Make it: move the row under LIMITS and delete the subhead. If the section must exist, show the placeholder `[OPEN QUESTIONS FROM THE PAPER]`.
3. **Fig. 1 shows when, not how.** Where: "What they did". Two L shapes with boxes at their ends and no label on any part. A reader does not learn what the L does. Make it: add leaders and labels on one L: "arm, 4 km" on each arm and "laser" at the corner (both are in the content file). Draw the laser path as a thin line down both arms and back. Keep every label inside the content file's facts.
4. **The hero plate is the old drawing.** Where: Plate 1. Make it: the feed's version (coherence item 1).
5. **"For scale" is loosely composed.** Where: the lens drawing. The proton sits right of the lens center, the label "Change in arm length" sits outside the lens with its leader crossing the rim, and the vermilion mark is a vertical stick with a dot on top that reads as a map pin, not as a length. Make it: center the proton in the lens. Put both widths on one ruler along the bottom of the lens, as `SYSTEM.md` 9.11 says: the proton's width as the ink beam it already has, and the arm change as a live beam so short it is only an end cap and the dot. Delete the vertical stick. Put the label inside the lens.
6. **Seven sections open the same way.** Where: the whole page. Double rule, slug, 30 px two-voice head, each time. After the hero only Fig. 1 bleeds to the edges. Make it: let "Try it" be the second full-bleed plate, with the chirp at hero scale (196 px band) on the engraved field. It is the interactive center of the page and should look like it.
7. **"Try it" looks like three sliders.** Where: three stacked copies of the control. Make it: one control at full size in the dragging state, then the other two positions as a row of two small thumbnails (about 165 px wide each) labeled "At rest, 35 Hz" and "At 0.2 seconds, 250 Hz". Raise the undrawn part of the signal from 0.6 px to 0.9 px, since it breaks up in the fast section.
8. **The ledger does not draw its range.** Where: the Distance row, which says "Drawn in Fig. 2". The brief says ranges in the ledger are drawn. Make it: a 120 px mini range bar in the row (screened band 230 to 570, live marker at 410) under the value.
9. **Fig. 3 legend.** Where: under the mass chart. "Left as waves" is printed twice (direct label and legend), and the legend keys a rectangle with a dot. Make it: remove "Left as waves" from the legend and keep the direct label. Also lighten both screens inside the "62" weave to the light tone (0.24), since the weave is now the darkest mass in the chart and pulls the eye from the vermilion segment.
10. **The inline exponent is 9.5 px.** Where: "its peak strain was 1.0 × 10⁻²¹" in body text. Make it: `font-size: 0.64em` for a `<sup>` in running text (about 11 px).
11. **The page ends on a disclaimer.** Where: the bottom. Consider the rating row under "Read the paper", since this is the moment the reader knows whether they want more like it. This adds a control nobody asked for, so it needs the owner's yes.

## Explainer-Night.dc.html: 58 of 80

1. **The halo is a brown casing, and here it is at its worst.** Where: the hero chirp. In the fast section the 7 px traps of neighboring cycles merge into a dark block that erases the rings behind the line. Make it: system fix 1.
2. **The plate is not dim.** Where: Plate 1 and the Fig. 1 wave field. The blue rings are the brightest mass on the screen and the amber line is a thin thing inside them. Make it: system fix 2, then raise the amber core from 1.6 to 1.9 px and compare.
3. **The well figure reads as goggles.** Where: Plate 1. A dark island with two gray ringed circles filled with blue hatch. Make it: the same change as Feed Day fix 1, with the well centers left open.
4. **Night chrome.** Where: double rules, tag outlines, the back link. Make it: system fix 4.
5. **The charts have no night board.** Where: this board stops at 1,800 px, as its task asked. Fig. 2, Fig. 3, the slider, and the ledger have never been shown at night on a canvas board. `design/scratch/explainer/Explainer-Night-Full.dc.html` exists. Promote it once fixes 1 to 4 are in.

## Site.dc.html: 59 of 80

The hero is the strongest single screen of web design in the set, and the excerpt section shows the product instead of describing it. The page fades in its lower half and has three bad wraps.

1. **The lower 40 percent is type only, and nothing after the hero moves.** Where: "How an explainer is made", "Download", and the footer. The task asked for how explainers are made to be shown. It is three large sentences. Make it: one plotter figure across the 12 columns. A single horizontal vermilion line with three ticks labeled Agent 1, Agent 2, Agent 3 and a pen point at its end, the three existing two-voice sentences set at 30 px in three columns under their ticks, and the slug "Illustration". Let the line sweep.
2. **The mobile hero breaks the second voice after one word.** Where: 390 wide. "explained" sits alone on line 3 and "in pictures." on line 4, against `SYSTEM.md` 2.2 rule 3. Make it: three lines, "New science and", "math papers,", "explained in pictures.", with the italic at `font-stretch: 87.5%` if it needs it to hold one line inside 350 px.
3. **The phone mock's headline strands two words.** Where: the feed section, both widths. "The first picture / of a black hole's / shadow." leaves a roman "of" at the head of line 2 and "shadow." alone on line 3. Make it: set this card's headline at 38 px with the italic at 87.5% width so it holds two lines, "The first picture of" and "a black hole's shadow." Those sizes are estimated from the night feed render, where the same headline sets in two lines at 30 px. Check them in a render.
4. **Two rows of the feature ledger are not ledger rows.** Where: "Your ratings / Stay on the phone" and "Paywalled papers / A short card". The right side holds a 30 px display phrase set like a number, and the ratings row has no note, so it is shorter than the rest. Make it: all five rows the same form. Label on the left, a specimen of the real component on the right, one italic sentence under. Ratings: the sentence "Ratings stay on the phone." and no specimen. Paywalled: a small outline "Read the paper" button as the specimen and the sentence "Paywalled papers get a short card: no explainer, and a link out to the paper."
5. **On a phone the primary action starts at y = 795 of an 844 px screen.** Where: 390 wide. It sits under the plate, the readout, the caption, and the paragraph. Make it: below 700 px, order the hero as headline, "Download the APK" slab, plate. Keep "Source on GitHub" and "Not on Google Play yet." after the paragraph.
6. **The excerpt grid has dead zones at 1440.** Where: about 130 px of empty ground under Fig. 3 in columns 1 to 8, about 200 px under "Read the paper" in columns 9 to 12, and Fig. 3 itself split into a title on the left and a chart squeezed to about 490 px on the right, with "3 Left as waves" jammed against the bar behind a dash. Make it: Fig. 3 runs the full eight columns with its chart about 760 px wide under its title, and the Source block moves under it so both columns end together.
7. **Fig. 1 is not the explainer's Fig. 1.** Make it: use the explainer's drawing (coherence item 2).
8. **The stamped state shows twice on one screen.** Where: the "Tuned" row and the phone mock, where it stacks under the primary slab as a second solid block. Make it: stamped in the "Tuned" row only. The mock's rating buttons stay unpressed.
9. **The right third of the hero plate is empty.** Where: 1440 wide. The line ends at 0.25 s and the ruler runs on for about 300 px of unlabeled ticks. Make it: move the ring center and the wells to about two thirds across, and end the ruler ticks at the last label.
10. **The wordmark link is under 44 px.** Where: the header, 42 px tall at 1440 and 37 px at 390. Make it: vertical padding to reach 44 px.

## Brand.dc.html: 59 of 80

The wordmark construction is clear and correct, and the 512 icon is a strong image. The icon is not yet a launcher icon.

1. **The icon does not hold at small sizes.** Where: the 72 px and 48 px tiles. The ring field collapses into blue noise with interference bands, and the stock outline around the P is gone. Make it: a second master for 96 px and below. On the 512 grid: five or six rings at a 24 px pitch and a 10 px stroke with no swelling, the pen point at a 56 px radius, the P unchanged. Show both masters on the board and say which sizes use which.
2. **The ring swells end in blunt cuts.** Where: the 512 icon. Each place a ring changes weight ends in a square step. The two worst are the fragments at about 1 o'clock and 5 o'clock on the ring nearest the pen point's clear zone. At this size they read as glitches. Make it: taper every swell over 20 to 30 degrees of arc, or let ring weight change only where the P hides it.
3. **The launcher treatment is one circle.** Where: section 03. The board shows a square and a circular mask. Make it: show the background layer (the field) and the foreground layer (the P and pen point) as two separate squares with their bleed, the safe zone drawn on them, the icon under a circle, a squircle, and a rounded square, and name the one-color version as the monochrome layer. The layer and safe-zone sizes must be taken from the Android adaptive icon documentation. I did not check them in this step.
4. **The P's outline is uneven.** Where: the 512 icon. The stock-colored trap is thick on the right of the bowl and under the foot serif and thin on the left of the stem, like a misregistration. Make it: an even 6 px all around at 512, or no outline and the rings masked back 8 px from the glyph.
5. **Night pen point.** Where: the 128 px and 48 px night icons. The amber dot sits in a dark brown ring. Make it: system fix 1.
6. **"Web hero, 150 px" has no specimen.** Where: the first row of section 02. Make it: relabel the construction drawing as that size if it is, or show the mark at 150 px, or cut the row.
7. **Icon rules are missing.** Where: section 03. Clear space and minimum size are given for the wordmark only. Make it: one label line each for the icon.
8. **The 512 icon crowds the bottom edge.** Where: 14 px of margin under it against 48 px at the top of the board. Make it: show the master at 480 px with the label "512 master, shown at 480".

## Motion.dc.html: 62 of 80

The clearest spec in the set. Putting each cell's timeline on the system's own ruler with a carriage for the clock is a smart use of the language. One cell needs to change before the owner sees it.

1. **The stamp passes through the form the owner hates.** Where: cell 06. The frozen frame "12 ms after the tap" shows an outline button with a solid black slab on its left edge. At the start of each loop a thin vertical sliver sits on the left edge of the live button (visible in the 0.3 s frame). It also disagrees with `SYSTEM.md` section 12 and with `App-Feed-Night`, which fill the whole button. Make it: flood the whole surface at once. Fill opacity 0 to 1 over the 120 ms while the slab scales 1.1 to 1, no directional wipe. Replace the frozen frames with three: "0 ms, outline at 1.1", "60 ms, half strength at 1.05", "120 ms, solid at 1". Make sure the fill layer is fully hidden before the tap.
2. **Seven vertical lines hug the left edge of the table.** Where: cell 07. Each row opens with a curve thumbnail whose vertical axis is a line on the row's left edge. They are axes, but in a list they read as left-edge marks. Make it: move the thumbnails to the right end of each row, or draw each with a baseline only.
3. **Feed up is listed and not shown.** Where: cell 07, last row. It is the transition a reader makes on every paper, and no board draws it. Make it: three frames (0, 180, 360 ms) with the plate fixed and the sheet rising under it. Take the room from cell 03, whose plate can drop to about 150 px tall.
4. **The wordmark dot loops.** Where: cell 01. If the masthead dot pulses while a hero pen point pulses, a screen has two loops, which the brief forbids. Make it: say in the cell where this entrance runs (app launch only), and end the wordmark's pulse row after the entrance, or cut it.
5. **Labels collide in the chart cell.** Where: cell 05. "About 1.4 Å wide" runs through the 2.8 drop line, and the 0.96 drop line cuts through the atom. At 0.3 s the labels are on screen before their marks. Make it: put the atom's label under the disc, stop the 0.96 drop line at the top of the disc, and Press each label in with its mark.
6. **Night is one cell.** Where: cell 04. Make it: system fixes 1 and 2 apply here.
7. **One type size carries the whole board.** Where: about 118 labels at 10.5 px mono caps. Cell titles, specs, and timeline labels differ by weight only. Make it: cell titles in the display face at 22 px.

## Not verified

- Register. The tool's first frame lands after the first 300 ms, so the two layers locking was not seen on any board. The keyframes are in the files.
- The Claude Design canvas runtime. Only the local screenshot tool was used.
- The site between 700 and 1160 px wide. Only 1440 and 390 were rendered, as the task asked.
- Contrast ratios. I did not recompute them. The figures quoted are the ones in `SYSTEM.md`.
- Android adaptive icon layer sizes, and how a scroll-triggered draw-in is built in the WebView.
- The sizes proposed for the site's mock headline (38 px, italic at 87.5%) are estimates from another render, not a render of the fix.
