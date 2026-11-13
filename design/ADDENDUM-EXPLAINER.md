# Explainer patterns: addendum to the handoff

Written 2026-11-13, after the design round closed. It fills three gaps that `design/HANDOFF.md` lists as "not drawn in this round": section 4.2 (scroll steps, the segmented toggle, glossary terms, the chart tooltip, the data table, math), section 4.4 (a line chart with several series, a scatter, a dumbbell), and section 8 items 9, 10, and 12 (the same, plus a desktop explainer). It also draws the explainer's top bar for the web.

Read `design/CONTEXT.md`, `design/CONTENT.md`, `design/SYSTEM.md`, and `design/HANDOFF.md` first. Nothing here changes them. Token names are the ones in `HANDOFF.md` section 2. Animation names are the ones in `HANDOFF.md` section 6. No em dashes. American English.

How to read the labels in this file:

- *Rendered*: the value is in one of the three new boards, or in the CSS test page, and I looked at it in a render.
- *Measured*: read from the browser with a script (`design/scratch/patterns/audit.py` or `design/scratch/patterns/kit-test/shot.py`).
- **Not checked**: I wrote it and did not render or measure it. Treat it as a proposal.

## 0. The boards and their sources

All in `design/canvas/project/`. Sizes were measured in the local renderer on 2026-11-13.

| Board | What it is | Size |
|---|---|---|
| `Explainer-Patterns-Day.dc.html` | Eleven patterns in one explainer-style column, day. | 390 by 7,535, fixed width |
| `Explainer-Patterns-Night.dc.html` | The same sheet, night. | 390 by 7,535, fixed width |
| `Explainer-Wide.dc.html` | The explainer at desktop width: first screen, key idea, one section with a figure, and a strip of measures. Day only. | 1200 by 1,656, fixed |

The three boards are not in `canvas.json`. I was told not to edit that file.

| File | What it does |
|---|---|
| `design/scratch/patterns/patterns.py` | Writes the two pattern boards. Imports tokens, type helpers, line screens, the wave field, the traps, and the night halo from `design/scratch/engraved/lib.py`. |
| `design/scratch/patterns/wide.py` | Writes the wide board. Loads `design/scratch/web/site.py` by path and uses its hero plate, type helpers, range bar, and figure head, so the wide board and the website cannot drift apart. |
| `design/scratch/patterns/run.py`, `run_wide.py` | Build, render with `design/tools/dc_shot.py`, set the declared heights, slice. |
| `design/scratch/patterns/audit.py` | Root size, overflow, touch targets, text sizes, text contrast, shadows, gradients, left borders, radius, running animations under reduced motion. |
| `design/scratch/patterns/reduced.py` | Renders each board with reduced motion and compares it, pixel for pixel, with the resting frame of the normal render. |
| `design/scratch/patterns/kit-test/patterns.css`, `test.html`, `shot.py` | The CSS in this file, written against the handoff's tokens, in a page with real classes, rendered in both themes at 390 wide. It loads the handoff's own test stylesheet (`design/scratch/final/handoff-test/kit.css`) and the kit's own KaTeX (`kit/v1/vendor/katex`, version 0.19.1). |

Renders: `design/shots/patterns/final/` (the last full renders and their slices), `design/shots/patterns/reduced/` (reduced-motion stills), `design/shots/patterns/r1` to `r6` and `w1` to `w3` (the rounds). CSS test renders are beside the test page.

What the checks found, all *measured*:

- All three boards: `overflow_x` false, no console errors, Martian Mono, Noto Serif Display, and Source Serif 4 loaded. The two pattern boards also load Old Standard TT, for the math mock only (section 11).
- No link, button, input, or summary under 44 px in either dimension.
- No HTML text pair under 4.5:1 (3:1 at 24 px and up). SVG text is `ink` (14.85:1) or `ink-muted` (5.94:1) by day, `light` (14.90:1) or `light-muted` (6.56:1) by night.
- No box shadow, no CSS filter, no gradient, no left border over 1 px, no radius on any box wider than 8 px.
- Mono text is 10 px (tags) or 10.5 px on the pattern boards, and 10.5 px (tags) or 11 px on the wide board. Sentences are 15, 16, 17, or 19 px. The one smaller serif size is the exponent inside the math mock, 13.1 px, which is a superscript and not a sentence.
- With reduced motion: zero running animations, and the still is identical to the resting frame on all three boards (no differing pixel).

Facts on the boards come from `CONTENT.md`. Four charts need numbers that file does not have (a four-series line chart, a scatter, a dumbbell, error bars). Those four are specimens: every label is a placeholder in brackets, the kind slug reads "Specimen, placeholder data" in place of "Data, from the paper", and the shapes mean nothing. Their titles describe the specimen ("Four lines, one ruler"), not a finding.

## 1. Top bar on the web (`.pb-topbar`, new)

Board: the top of both pattern boards, and section 01. Wide form: the top of `Explainer-Wide`.

The app's bar has a "Feed" back link. In a browser there is no feed behind the page, so the web bar is the small wordmark alone, as a link to the site, over the double rule. Nothing else. The wordmark sits on the left, where the website's masthead has it.

| Part | Value |
|---|---|
| Row | 48 px tall (2 px above and below a 44 px link), 20 px side padding (`--pb-gutter`), then the double rule: 3 px, 2 px gap, 0.75 px, in `--pb-rule` |
| Link | 44 px tall, 10 px side padding, pulled 10 px left so the "P" sits on the margin. *Measured*: 115.6 by 44 by day, 117.1 by 44 by night |
| Type | `wordmark-s`: "Paper" in D1 (D2 at night) at 22 / 1.0, "boy" in D5 at 22, tracking −0.02em, the dot 4 px in `--pb-accent`, 2 px after the y, on the baseline |
| At 1160 px and wider | The website's masthead form: 38 / 1.0, "boy" in D4, dot 6.5 px, 3 px gap, padding `1px 0 5px`, 20 px above the row, 56 px side padding. *Rendered* on the wide board. *Measured*: 160.4 by 44 |
| Color | `--pb-ink` |

States: at rest. Pressed: the letters go to `--pb-ink-2` and the dot stays live. Focus: a 2 px outline in `--pb-ink`, 2 px off the 44 px box. All three are drawn in section 01. Hover (pointer devices only) is the pressed look. Hover is **not checked** in a render.

Motion: none. The wordmark does not Press in here. That move is for app launch only (`HANDOFF.md` 6.1).

Markup:

```html
<header class="pb-topbar"><a class="pb-wordmark" href="SITE" aria-label="Paperboy, to the website">Paper<em>boy</em><i></i></a></header>
<article class="pb">...</article>
```

```css
/* 01 the top bar on the web */
.pb-topbar { position: relative; max-width: calc(var(--pb-measure) + 2 * var(--pb-gutter)); margin: 0 auto; padding: 2px var(--pb-gutter) 7.75px; }
.pb-topbar::before, .pb-topbar::after { content: ""; position: absolute; left: var(--pb-gutter); right: var(--pb-gutter); background: var(--pb-rule); }
.pb-topbar::before { bottom: 2.75px; height: 3px; }
.pb-topbar::after { bottom: 0; height: 0.75px; }
.pb-wordmark { display: inline-block; box-sizing: border-box; height: 44px; margin-left: -10px; padding: 9.5px 10px 12.5px; font-family: var(--pb-display); font-size: 22px; line-height: 22px; font-weight: var(--pb-w-voice1); font-stretch: 62.5%; letter-spacing: -0.005em; color: var(--pb-ink); text-decoration: none; white-space: nowrap; }
.pb-wordmark em { font-style: italic; font-weight: 400; font-stretch: 100%; letter-spacing: -0.02em; }
.pb-wordmark i { display: inline-block; width: 4px; height: 4px; margin-left: 2px; border-radius: 50%; background: var(--pb-accent); }
.pb-wordmark:active { color: var(--pb-ink-2); }
.pb-wordmark:focus-visible { outline: 2px solid var(--pb-ink); outline-offset: 2px; }
@media (hover: hover) { .pb-wordmark:hover { color: var(--pb-ink-2); } }
```

*Rendered* at 390 wide in both themes. The 1160 px form is section 12.

Build notes, **not checked**: the bar sits outside `<article class="pb">`, so the contract's rule that the root is that article still holds. The app draws its own bar, so the page has to hide this one inside the app's WebView. How the page knows where it is (a class the app sets, a query parameter, a user agent token) is not decided.

## 2. Data table (`.pb-data`, `.pb-table`)

Board: section 02. The chart is Fig. 3 of the explainer ("Where the mass went"), unchanged.

The table is the last row of a data figure. Closed, it is one 44 px row between two hairlines: the slug "The numbers" on the left and a plus on the right. The figure now opens with a hairline and closes with one. Opened, the plus becomes a minus, the lower hairline goes, and the table follows: a caption, a head row, and the rows.

| Part | Value |
|---|---|
| Position | 14 px under the legend (or under the chart when there is no legend) |
| Row | `summary`, 44 px tall at least, full column width. *Measured*: 350 by 44 |
| Row rules | 0.75 px `--pb-rule` above. 0.75 px `--pb-rule` below when closed |
| Label | "The numbers", `label` in M2, `--pb-ink` |
| Icon | `PLUS` closed, `MINUS` open (`SYSTEM.md` section 8), 14 px, in the text color, at the right end |
| Caption | `note` (T3, 15 / 1.4), `--pb-ink`, 12 px above the head row. It says what the head row does not: here, "All four values are estimates." |
| Head cells | `label` in M1, `--pb-ink-2`, 7 px under them a 0.75 px rule in `--pb-rule` |
| Body cells | T1 at 15 / 1.4, `--pb-ink`, `font-variant-numeric: tabular-nums lining-nums`, 8 px above and 9 px below (a 38 px row) |
| Row lines | 0.6 px in `--pb-grid` between rows, 0.75 px in `--pb-rule` under the last row |
| Columns | 12 px apart. Text columns left. Number columns right, in a `num` class, as the kit already writes them |

States: closed, open, pressed (label and icon go to `--pb-ink-2`), focus (2 px outline in `--pb-ink`, 2 px off the row). Closed and open are on the boards. Focus was seen in the CSS test. Pressed is **not checked** in a render.

Motion: on opening, the table lands with **Press**, one step (190 ms, `cubic-bezier(0.2, 0, 0, 1)`). Nothing moves on closing. Reduced-motion still: the open table, in place.

```css


/* 02 the data table: the last row of a data figure */
.pb-data { margin: 14px 0 0; font-size: 15px; border-top: 0.75px solid var(--pb-rule); border-bottom: 0.75px solid var(--pb-rule); }
.pb-data[open] { border-bottom: 0; }
.pb-data > summary { list-style: none; min-height: 44px; display: flex; align-items: center; justify-content: space-between; gap: 16px; cursor: pointer; color: var(--pb-ink);
  font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 600; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-data > summary::-webkit-details-marker { display: none; }
.pb-data > summary::before { content: none; }
.pb-data > summary::after { content: ""; flex: none; width: 14px; height: 14px; background: currentColor; -webkit-mask: var(--pb-ico-plus) center / 14px 14px no-repeat; mask: var(--pb-ico-plus) center / 14px 14px no-repeat; }
.pb-data[open] > summary::after { -webkit-mask-image: var(--pb-ico-minus); mask-image: var(--pb-ico-minus); }
.pb-data > summary:active { color: var(--pb-ink-2); }
.pb-data > summary:focus-visible { outline: 2px solid var(--pb-ink); outline-offset: 2px; }
.pb-table-wrap { overflow-x: auto; margin: 0; padding-bottom: 2px; }
.pb-data[open] > .pb-table-wrap { animation: pb-press 190ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-table { border-collapse: collapse; width: 100%; font-family: var(--pb-font); font-size: 15px; line-height: 1.4; font-variant-numeric: tabular-nums lining-nums; color: var(--pb-ink); }
.pb-table caption { caption-side: top; text-align: left; padding: 0 0 12px; font-style: italic; color: var(--pb-ink); }
.pb-table th { padding: 0 12px 7px 0; text-align: left; white-space: nowrap; border-bottom: 0.75px solid var(--pb-rule); color: var(--pb-ink-2);
  font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-table td { padding: 8px 12px 9px 0; text-align: left; vertical-align: baseline; white-space: normal; border-bottom: 0.6px solid var(--pb-grid); }
.pb-table tbody tr:last-child td { border-bottom: 0.75px solid var(--pb-rule); }
.pb-table th.num, .pb-table td.num { text-align: right; padding-right: 0; padding-left: 12px; white-space: nowrap; }
```

*Rendered* in both themes, with the markup `PB.table` writes today (`details.pb-data > summary + div.pb-table-wrap > table.pb-table`).

Build notes:

- The kit's default summary text is "Show the numbers". Change it to "The numbers". A label that says "Show" is wrong once the row is open, and the icon already says which way it goes.
- A number that is an estimate is not marked cell by cell. The caption says it, once.
- A table wider than the column scrolls sideways inside `.pb-table-wrap`. That is the kit's rule today. It is **not checked** here: the board's table fits.

## 3. Scroll steps (`.pb-steps`, `.pb-steps-visual`, `.pb-step`, `.pb-step-n`)

Board: section 03. The picture is Fig. 1 of the explainer built in steps, held at step 3 of 4: both detectors drawn, the wave field inked up to a front that has just reached Hanford, and the 7 millisecond beam ruled off. The field stops at the front. That is new: in Fig. 1 the field covers the band.

The layout:

1. **The pinned block.** The figure (its hairline, its head row, the drawing) and under it the gauge. It sticks to the top of the screen for as long as its steps are passing. It has the page color behind it, so a step that scrolls up goes out of sight behind it.
2. **The gauge.** The foot of the pinned block is a double rule, heavy on top. The heavy rule is cut into one part per step, 4 px apart. A part is printed once its step has been reached. So at step 3 of 4 three parts are printed and the fourth is open ground over the hairline. When the last step is reached it is a whole double rule.
3. **The steps.** Plain blocks on open ground under the pinned block, 40 px apart. Each is a slug ("Step 3 of 4") and one or two sentences in `body`. No card, no rule, no shadow.

The current step is told apart three ways, none of them a box: its text is `--pb-ink` where the others are `--pb-ink-2`, its slug is M2 where the others are M1, and the gauge's last printed part is its own. Steps before it and steps after it look the same.

| Part | Value |
|---|---|
| Pinned block | `position: sticky; top: 0`, page color behind it, bleeds to the screen edges with 20 px padding |
| Gauge | 16 px under the drawing. Parts 3 px tall in `--pb-rule`, 4 px apart, equal widths. 2 px under them a 0.75 px hairline in `--pb-rule`, full measure |
| Step slug | `label`, M1 in `--pb-ink-2`. Current: M2 in `--pb-ink` |
| Step text | `body` (17 / 1.47), 6 px under the slug, `--pb-ink-2` (5.94:1 by day, 6.56:1 by night). Current: `--pb-ink` |
| Between steps | 40 px |
| Before the first step | So that step 1 is still under the reading line when the block pins: 58 percent of the screen height minus the height of the pinned block, 16 px at least |
| After the last step | 40 percent of the screen height |
| Reading line | A step becomes current when it crosses a band from 55 to 65 percent of the screen height. The kit's band is 45 to 55 percent today |

States: at rest (not current), current. A step is not a control: it has no pressed or focus state.

Motion: the steps themselves do not animate. The change from muted to ink is one step, with no fade (`transition: none`), because text does not fade in this system (`HANDOFF.md` 4.2, `.pb-reveal`). The picture's change at each step uses the named draw-ins: on the board the field inks in with **Ink wipe** (520 ms) and the beam draws with **Sweep** and **Travel** (900 ms, the short-beam range). One draw-in per step. Reduced-motion still: every state of the picture is drawn complete, and the gauge and the ink color still say which step is current. Authors must give each step a complete still, as `PB.animate` already asks.

Markup, with one new element (the gauge) that the kit writes:

```html
<div class="pb-steps">
  <div class="pb-steps-visual">
    <figure class="pb-fig" data-kind="illustration" data-slug="Fig. 1">...</figure>
    <div class="pb-steps-gauge" role="img" aria-label="Step 3 of 4"><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i></i></div>
  </div>
  <div class="pb-step"><span class="pb-step-n">Step 1 of 4</span><p>...</p></div>
  ...
</div>
```

```css
/* 03 scroll steps: the figure is pinned, the steps pass under it */
.pb-steps { position: relative; margin: 24px 0 0; }
.pb-steps-visual { position: sticky; top: 0; z-index: 2; margin: 0 calc(-1 * var(--pb-gutter)); padding: 0 var(--pb-gutter); background: var(--pb-page); }
.pb-steps-visual > .pb-fig { margin-top: 0; }
.pb-steps-gauge { display: flex; gap: 4px; box-sizing: border-box; height: 5.75px; margin-top: 16px; border-bottom: 0.75px solid var(--pb-rule); }
.pb-steps-gauge i { flex: 1 1 0; height: 3px; }
.pb-steps-gauge i.is-on { background: var(--pb-rule); }
.pb-step { position: relative; z-index: 1; margin: 0 0 40px; padding: 0; background: none; border: 0; border-radius: 0; box-shadow: none; opacity: 1; color: var(--pb-ink-2); transition: none; }
.pb-steps-visual + .pb-step { margin-top: var(--pb-steps-lead, 18vh); }   /* the kit sets --pb-steps-lead, see the addendum */
.pb-steps > .pb-step:last-child { margin-bottom: 40vh; }
.pb-step-n { display: block; color: inherit; font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-step p { margin: 6px 0 0; color: inherit; }
.pb-step.is-active { color: var(--pb-ink); }
.pb-step.is-active .pb-step-n { font-weight: 600; }
```

*Rendered* in both themes in the CSS test, with a script that stands in for `PB.steps`. *Measured* there at 390 by 844: the block pins at the top, step 1 is current when it pins, steps 2, 3, and 4 take over in turn as the page scrolls, the gauge follows, and the step before the current one stays readable above it until it slides behind the block.

Build notes, for `PB.steps` in `kit/v1/paperboy.js`. These are changes to code I did not edit:

- Write the gauge into `.pb-steps-visual`: one `<i>` per step, `is-on` on every part up to the current one, and the `aria-label`.
- Change the observer's `rootMargin` from `-45% 0px -45% 0px` to `-55% 0px -35% 0px`.
- Set `--pb-steps-lead` on the first step to `max(16, 0.58 × innerHeight − height of .pb-steps-visual)` in px, and again on resize.
- The kit's own first-step rule (`.pb-step:first-of-type`) never matches, because the pinned block before it is also a `div`. The rule above uses `.pb-steps-visual + .pb-step`.
- Kit v1 puts the steps above the picture (`z-index: 2` over `1`) as cards. Here it is the other way round: the block is above (`2`) and the steps pass behind it (`1`).

**Not checked**: the app's own top bar above a WebView (the block pins at `top: 0` of the page, which is right if the app bar is outside the WebView), a pinned block taller than about half the screen, and landscape.

## 4. Glossary term and its definition (`.pb-term`, `.pb-term-pop`)

Board: section 04.

**The term.** It is body text in the text color with a dotted underline: 1.5 px dots in `--pb-ink`, 4 px under the baseline. No text wears the live color. A link in this system is italic with a solid 0.75 px underline and an arrow, so the two cannot be mistaken: a term is roman, dotted, and has no arrow. The hit area is the word plus 10 px above and below and 4 px each side, which costs no space in the line. *Measured*: 50 by 44 for "chirp" at 17 px.

**The definition.** It opens under the line the term is in, as a slip of the sheet laid across the column. It is not a card: it has the page color behind it, a double rule (heavy on top) at its head, a hairline at its foot, and no side edges, no radius, no shadow. Inside it reads like a ledger row: the term as a slug on the left, "Glossary" in the muted label on the right, and the definition in `note` under them. While it is open the term is set solid, `--pb-page` on `--pb-ink`, with no underline. That and the repeated slug tie the slip to its word.

Two measures make it sit cleanly, and both need the kit's script:

- Its top is the foot of the term's line. The first 6 px are page color, then the double rule, so the solid term never touches the heavy rule.
- Its height is rounded up to a whole number of the paragraph's lines. So it covers whole lines and never cuts one in half.

| Part | Value |
|---|---|
| Term, at rest | `text-decoration: underline dotted`, thickness 1.5 px, offset 4 px, `--pb-ink` |
| Term, open | `--pb-page` on `--pb-ink`, 3 px side padding, no underline |
| Term, focus | 2 px outline in `--pb-ink`, 3 px off the word |
| Slip, position | Left edge and width of the paragraph (the column: 350 px at 390 wide). Top at the foot of the term's line |
| Slip, height | Whole lines of the paragraph: on the board 4 lines of 24.99 px, 100 px |
| Slip, head | 6 px of page color, then 3 px rule, 2 px gap, 0.75 px rule, all `--pb-rule` |
| Slip, head row | 10 px under the rule. The term in `label` M2 `--pb-ink`. "Glossary" in `label` M1 `--pb-ink-2`, right |
| Slip, text | `note` (T3, 15 / 1.4), `--pb-ink`, 6 px under the head row, 12 px of space under it at least |
| Slip, foot | 0.75 px rule in `--pb-rule`, on the last pixel row of the slip |

States: term at rest, open, focus (all drawn, in a paragraph and alone). Pressed is the open state: the tap opens it. A second tap on the term, a tap anywhere else, or a scroll closes it, as the kit does today.

Motion: the slip lands with **Press**, one step (190 ms). Nothing on closing. Reduced-motion still: the slip in place.

```css
/* 04 the glossary term and its definition */
.pb-term { padding: 10px 4px; margin: -10px -4px; cursor: pointer; border: 0; -webkit-tap-highlight-color: transparent;
  text-decoration: underline dotted var(--pb-ink); text-decoration-thickness: 1.5px; text-underline-offset: 4px; }
.pb-term[aria-expanded="true"] { padding: 0 3px; margin: 0 -3px; background: var(--pb-ink); color: var(--pb-page); text-decoration: none; }
.pb-term:focus-visible { outline: 2px solid var(--pb-ink); outline-offset: 3px; }
.pb-term-pop { position: absolute; z-index: 20; box-sizing: border-box; max-width: none; margin: 0; padding: 6px 0 0; display: flex; flex-direction: column;
  background: var(--pb-page); color: var(--pb-ink); border: 0; border-radius: 0; box-shadow: none;
  font-family: var(--pb-font); font-size: 15px; line-height: 1.4; font-style: italic; text-wrap: pretty;
  animation: pb-press 190ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-term-pop::before { content: ""; flex: none; height: 2px; border-top: 3px solid var(--pb-rule); border-bottom: 0.75px solid var(--pb-rule); }
.pb-term-pop::after { content: ""; flex: none; margin-top: auto; height: 0.75px; background: var(--pb-rule); }
.pb-term-pop b { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin: 10px 0 6px; font-style: normal; color: var(--pb-ink);
  font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 600; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-term-pop b::after { content: "Glossary"; font-weight: 500; color: var(--pb-ink-2); }
.pb-term-pop > span { padding-bottom: 12px; }
```

*Rendered* in both themes in the CSS test, with a script that stands in for the kit's `setupTerms`. *Measured* there: the slip's top is 0.98 of a line under the paragraph's top (the term is in the first line), its height is 4.00 lines, its left edge and width are the column's (20 and 350).

Build notes, for `setupTerms` in `kit/v1/paperboy.js`:

- Set `aria-expanded` on the term: `"false"` at setup, `"true"` while its slip is open.
- Measure the term before changing it. With `r` its box and `lh` the paragraph's computed line height: `top = r.top + r.height / 2 + lh / 2`.
- Set the slip's `left` and `width` from the paragraph's box, not from the term. After it is in the page, set `height = ceil(height / lh) × lh`.
- Put the definition in a `<span>` after the `<b>`, so it can carry the padding under it.
- The right-hand word "Glossary" is written by CSS. If it should be translatable, write it in the markup.

**Not checked**: a term in the last lines of the screen (the kit flips its popover above the word, and this slip was only drawn below), a term inside a caption or a ledger note, a term that breaks across two lines, and the slip at desktop width.

## 5. Segmented toggle (`.pb-toggle`)

Board: section 05. It switches Fig. 3 between its two rows, "Before" and "After". The second specimen has three positions with the field names from `CONTENT.md`.

It is the rating row's sibling. Two or three equal segments, 44 px tall, joined: each has a 1 px outline in `--pb-rule` and the outlines overlap by 1 px. The chosen segment is stamped exactly like a chosen rating: filled `--pb-stamp`, label in `--pb-on-stamp`, and a check before the label. So "chosen" looks the same everywhere in the product, and the state is carried by the check as well as by the fill.

| Part | Value |
|---|---|
| Group | Full width of the figure, `display: flex`, no gap, no frame of its own |
| Segment | Equal widths, 44 px tall at least, 10 px side padding, radius 0. *Measured*: 175.5 by 44 with two |
| Label | `rate` (T2, 16 / 1.0), centered |
| Not chosen | Transparent, 1 px `--pb-rule`, label `--pb-ink` |
| Chosen | `--pb-stamp` fill and border, label and `CHECK` (14 px, 8 px before the label) in `--pb-on-stamp`. 5.94:1 by day, 6.56:1 by night |
| Group label | `label` M1 in `--pb-ink-2`, 7 px above the group. It names what the switch changes ("Show the mass") |
| Position in a figure | Under the title, 14 px above the label, 18 px above the chart |

States, all drawn: not chosen, chosen, pressed (a segment that is not chosen, while held: label and outline go to `--pb-ink-2`), focus (2 px outline in `--pb-ink`, 2 px off the segment, drawn above its neighbors).

Motion: none on the switch. It changes in one step. It does not use **Stamp**: that move scales the button to 1.1, and a segment joined to its neighbors cannot grow without covering them. The figure answers the tap instead: its one live mark draws in with its own named move (on the board the "3" segment uses **Flood**). Reduced-motion still: the new state, complete.

```css
/* 05 the segmented toggle */
.pb-toggle { display: flex; flex-wrap: nowrap; gap: 0; padding: 0; background: none; border: 0; border-radius: 0; }
.pb-toggle button { flex: 1 1 0; min-width: 0; min-height: 44px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; justify-content: center; gap: 8px;
  background: transparent; border: 1px solid var(--pb-rule); border-radius: 0; box-shadow: none; color: var(--pb-ink); cursor: pointer;
  font-family: var(--pb-font); font-size: 16px; font-weight: 500; line-height: 1; }
.pb-toggle button + button { margin-left: -1px; }
.pb-toggle button[aria-pressed="true"] { background: var(--pb-stamp); border-color: var(--pb-stamp); color: var(--pb-on-stamp); box-shadow: none; }
.pb-toggle button[aria-pressed="true"]::before { content: ""; flex: none; width: 14px; height: 14px; background: currentColor; -webkit-mask: var(--pb-ico-check) center / 14px 14px no-repeat; mask: var(--pb-ico-check) center / 14px 14px no-repeat; }
.pb-toggle button[aria-pressed="false"]:active { color: var(--pb-ink-2); border-color: var(--pb-ink-2); }
.pb-toggle button:focus-visible { position: relative; z-index: 1; outline: 2px solid var(--pb-ink); outline-offset: 2px; }
.pb-toggle-label { display: block; margin: 14px 0 7px; }
```

*Rendered* in both themes in the CSS test, with the markup `PB.toggle` writes today (`div.pb-toggle[role=group] > button[aria-pressed]`). A tap was sent to the first segment and the state changed (*measured*: its background became `--pb-stamp`). Pressed is **not checked** in a render of the CSS. It is drawn on the boards.

Build notes: `PB.toggle` takes a `label` and writes it only as `aria-label`. Also write it as visible text before the group (`<span class="pb-label pb-toggle-label">`). Four or more options are not a toggle in this system. They were not designed.

## 6. Line chart with several series

Board: section 06, "Four lines, one ruler". A specimen: placeholder labels, no numbers.

This is `SYSTEM.md` section 4 applied to lines. Series are told apart by weight and lightness, then by the direct label at the end of each line. Hue alone never separates two lines.

| Order | Mark | Day | Night |
|---|---|---|---|
| 1, the finding | The live line (`HANDOFF.md` 4.5): 1.9 px core on its trap, the pen point at its end, the carriage under the pen on the ruler | `--pb-accent` | `--pb-accent`, with the halo |
| 2 | Solid line, 1.4 px | `--pb-ink` | `--pb-ink` |
| 3 | Solid line, 1.4 px | `--pb-plate` (6.28:1 on stock) | `--pb-plate` (3.55:1 on ground) |
| 4, an estimate | Thin line, 0.9 px | `--pb-ink-2` | `--pb-ink-2` |

- **The estimate is a thin line, not a screened one.** `SYSTEM.md` 4.1 gives the screen for bands and bars. A line cannot carry a screen. The rule it follows is `SYSTEM.md` 3.3: a lighter tone is a thinner line. The same line is already in the system as the part of the signal not yet played in "Try it". This is a decision of this pass (open question 4).
- **Order of drawing:** estimate, series 3, series 2, then the live line last on its trap. So the live line cuts the others where it crosses them and never touches them. The trap also cuts the value lines.
- **The ruler** is the x axis: `SYSTEM.md` 4.2 rule 2. The live line is plotted against it, so it carries the carriage (`SYSTEM.md` 9.4 rule 3).
- **Values** are read off value lines, not a second axis: three 0.6 px lines in `--pb-grid` across the plot, each named at its left end, 5 px above the line, in `label` in `--pb-ink-2`. The top one carries the unit.
- **Labels at the ends:** 12 px right of the plot, on each line's last point, in `label`. Series 2 and 3 in `--pb-ink`, the estimate in `--pb-ink-2`, the finding in M2. The finding also carries its last value in D1 at 25 px (D2 at night) above its name: the value's baseline 1 px under the pen point's center, the name 20 px under that.
- **Legend:** every line is named at its end, so the legend only explains the kinds: the 7 px dot ("The finding"), a 22 px piece of 1.4 px line ("Measured"), a 22 px piece of 0.9 px line ("An estimate").
- **Measures on the board:** the plot is 246 px wide and 150 px tall in a 350 px figure, which leaves 104 px for end labels. Lines that end less than about 14 px apart will have labels that collide (a rule of thumb from the label's height, **not checked**). The kit has to test for that and move a label along a 0.75 px leader when it happens. That case is **not drawn**.

States: at rest. Touch is section 8, with one difference that is **not drawn**: on a line chart the readout names every series at the touched x.

Motion: the live line draws with **Sweep** and **Travel** (1500 ms on the board, inside the 1400 to 2200 range), once, when the figure comes into view. The other lines do not animate. Reduced-motion still: every line whole, the pen point parked at the end, the carriage under it.

```css
/* 06 to 10 chart marks beyond HANDOFF.md 4.3 */
.pb-line { fill: none; stroke: var(--pb-ink); stroke-width: 1.4px; stroke-linejoin: round; stroke-linecap: round; }
.pb-line[data-series="3"] { stroke: var(--pb-plate); }
.pb-line[data-kind="estimate"] { stroke: var(--pb-ink-2); stroke-width: 0.9px; }
.pb-dot { fill: var(--pb-ink-2); r: 2.1px; }
.pb-dot[data-named] { fill: var(--pb-ink); r: 3.2px; }
.pb-ring { fill: var(--pb-page); stroke: var(--pb-ink); stroke-width: 0.9px; r: 4px; }
.pb-whisker { fill: none; stroke: var(--pb-ink); stroke-width: 0.9px; }
.pb-whisker-trap, .pb-line-trap { fill: none; stroke: var(--pb-page); stroke-width: 4.5px; }
.pb-band { stroke: var(--pb-ink); stroke-width: 0.6px; stroke-linejoin: round; }
.pb-mark-label { font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500; letter-spacing: 0.06em; fill: var(--pb-ink); }
.pb-mark-label[data-finding] { font-weight: 600; }
.pb-mark-figure { font-family: var(--pb-display); font-stretch: 62.5%; font-weight: var(--pb-w-voice1); font-size: 25px; font-variant-numeric: lining-nums; fill: var(--pb-ink); }
```

**Not rendered as CSS.** The boards draw these marks as inline SVG with the same values. `.pb-dot` and the touch marks were rendered in the CSS test. The rest of the block was not.

## 7. Scatter

Board: section 07, "Many points, three named". A specimen.

Three ranks of point, told apart by size and lightness:

| Rank | Mark | Color |
|---|---|---|
| The finding | The live mark: a 3.6 px dot (3.4 at night) on a 6.5 px ground dot (5 px, with the three-disc halo, at night). One per chart | `--pb-accent` |
| Named | 3.2 px solid dot, with its name beside it | `--pb-ink` |
| Every other point | 2.1 px solid dot, no name | `--pb-ink-2` |

- Points are solid. They are measured. A point that is an estimate was not designed (open question 5).
- Names are `label`, 9 px from the dot's center, on the dot's own line, horizontal, in `--pb-ink`. The finding's name is M2, 11 px away. A name goes on the side with open ground. A name never sits on a value line.
- The ruler and the value lines are as in section 6. There is no carriage: the finding is a point, and nothing is being drawn along the ruler.
- The legend has all three ranks, because two of them carry no name.
- The board has 46 points in a 286 by 160 px plot. Above about a hundred points this form will need a rule for overlap. That is **not drawn**.

Motion: the finding's dot arrives with **Flood** (260 ms). Reduced-motion still: every point in place.

## 8. Touch readout (`.pb-tip`)

Board: section 08, on the scatter of section 07, with one unnamed point touched.

Three things appear together, and all three go when the finger lifts:

1. **A ring on the mark.** A 6.5 px radius ring, 0.9 px, in `--pb-ink`, over an 8 px ground dot that clears the marks around it. The touched point is redrawn inside it at 2.6 px in `--pb-ink`.
2. **A drop line to the ruler.** 0.6 px in `--pb-grid`, from the mark to the ruler, and a 2 px tick 7 px long in `--pb-ink` on the ruler where it lands. Not a carriage: the carriage belongs to the live line.
3. **The slab.** A small solid slab above the mark, joined to the ring by a 0.75 px leader in `--pb-ink`. It is `--pb-slab` with `--pb-on-slab` text (14.85:1 by day, 14.90:1 by night), radius 0, no border, no shadow. Solid, so it reads over a screened bar or a ring field as well as over open ground. Its first line is the mark's name in `label` M2. Under it, one row per value: the quantity in `label` M1 on the left, the value in T1 at 15 / 1.2 with tabular lining figures on the right, its unit in T3.

| Part | Value |
|---|---|
| Slab padding | 8 px top and bottom, 10 px sides |
| Name to rows | 5 px |
| Quantity to value | 14 px. Rows 1 px apart |
| Slab to mark | Its foot is 14 px above the mark's center, centered on the mark, kept 12 px inside the screen (the kit does this today) |
| Width | As wide as its text, 240 px at most. *Measured* with the placeholder text: 143.5 by 71.6 |

The live mark is never used for touch. A touched mark is ringed in the text color.

States: hidden, shown. It is not focusable and takes no pointer events, as today.

Motion: the slab lands with **Press**, one step (190 ms). The ring, the drop line, and the tick appear with it, without a move of their own. Reduced-motion still: the three in place while the touch lasts.

```css
/* 08 the touch readout */
.pb-tip { position: fixed; z-index: 30; pointer-events: none; max-width: 240px; padding: 8px 10px; background: var(--pb-slab); color: var(--pb-on-slab); border: 0; border-radius: 0; box-shadow: none;
  font-family: var(--pb-font); font-size: 15px; line-height: 1.2; font-variant-numeric: tabular-nums lining-nums; animation: pb-press 190ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-tip b { display: block; margin: 0 0 5px; white-space: nowrap; font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 600; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-tip dl { display: grid; grid-template-columns: auto auto; column-gap: 14px; row-gap: 1px; align-items: baseline; margin: 0; }
.pb-tip dt { white-space: nowrap; font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; }
.pb-tip dd { margin: 0; text-align: right; white-space: nowrap; }
.pb-tip dd i { font-style: italic; }
/* the marks a chart adds under the readout */
.pb-touch-trap { fill: var(--pb-page); }
.pb-touch-ring { fill: none; stroke: var(--pb-ink); stroke-width: 0.9px; }
.pb-touch-core { fill: var(--pb-ink); }
.pb-touch-leader { fill: none; stroke: var(--pb-ink); stroke-width: 0.75px; }
.pb-touch-tick { fill: none; stroke: var(--pb-ink); stroke-width: 2px; }
```

*Rendered* in both themes in the CSS test (the slab, and the ring, drop line, leader, and tick as classes).

Build notes: `PB.tooltip().show(content, event)` takes a string or a node. For the slab to have its two ranks of text it needs a node of this form: `<b>name</b><dl><dt>quantity</dt><dd>value <i>unit</i></dd>...</dl>`. A plain string still works and is set in T1 at 15 px. The ring, the drop line, and the tick are drawn by the chart, in its own SVG. The kit has no helper for them today.

**Not checked**: the slab under the mark (the kit flips it when there is no room above), the readout on a bar, and on a line chart (section 6).

## 9. Dumbbell

Board: section 09, "Four pairs of values". A specimen.

One row per item, on one ruler.

| Part | Value |
|---|---|
| Before | An open ring: 4 px radius, 0.9 px outline in `--pb-ink`, filled `--pb-page` |
| After | A solid dot, 4 px radius, `--pb-ink` |
| The join | A 1.4 px beam in `--pb-ink` between the two, on a 5 px ground trap |
| The finding's row | Its solid dot is the live mark: 4 px (3.8 at night) in `--pb-accent` on a 6.5 px ground dot (5 px with the halo at night). Its name is M2 |
| Row names | `label` in `--pb-ink`, in a column 86 px wide at the left of the figure, on the row's center line |
| Rows | 30 px apart |
| Direct labels | The first row carries "Before" and "After" above its two marks, 12 px above the row's center line, in `label` |
| Value lines | Vertical here, because the values run along the ruler: 0.6 px in `--pb-grid` at the major ticks, from 6 px above the first row to the ruler. None at the ruler's zero end, so there is no line beside the row names |
| Ruler | As in `SYSTEM.md` 4.2, 24 px under the last row, with the unit at its right end |

Open and solid differ by form, so the pair reads without color. A row whose value fell has its solid dot on the left: the fourth row shows it.

Motion: the finding's solid dot arrives with **Flood** (260 ms). Reduced-motion still: every row complete.

## 10. Uncertainty: error bars and a band

Board: section 10, "Each value, its range". A specimen with both forms in one chart.

- **An error bar** belongs to a measured point. A vertical 0.9 px line in `--pb-ink` from the low end to the high end, with a 8 px cap across each end, under a 3.2 px solid dot. Each bar sits on a 4.5 px ground trap, so it stays whole where it crosses a band or a line.
- **A band** belongs to a line that is an estimate. The area between the low and high edges, filled with the `--pb-screen` line screen on angle −72 at tone 0.30, with a 0.6 px outline in `--pb-ink` all the way round. Its center line is a 1.4 px line in `--pb-ink` on a 4.5 px ground trap. The line's name sits at its end on a small ground patch, so a value line never runs through the name.
- **The finding** is one measured point: the live dot on its ground dot, over its own error bar.
- Solid means measured and screened means a range, as everywhere else (`SYSTEM.md` 4.2 rule 1).
- Legend: the dot ("The finding"), a small error bar with its dot ("Measured, with its range"), a screen swatch ("Estimated range").

How this sits with the forms already on the boards: one value with a range is the range bar of Fig. 2 (a screened band on the ruler with the live marker on it). Several measured values, each with a range, are error bars. A range that runs along a line is a band.

The band's tone is 0.30, the context-shape tone, not the 0.46 of the range bar. At 0.46 a band this large outweighed the points on it. This is a decision of this pass.

Motion: the finding's dot arrives with **Drop** (260 ms). Reduced-motion still: everything in place.

## 11. Math (KaTeX)

Board: section 11. On the boards the math is a mock in **Old Standard TT** (Google Fonts, SIL Open Font License), because the canvas cannot load KaTeX's fonts. It is the closest face there: KaTeX's fonts are Computer Modern, a "Modern" face, and Old Standard TT is one too. The sun symbol in the mock is a small drawing. The real thing was then *rendered* in the CSS test with the kit's own KaTeX 0.19.1 and its own fonts, and it matches the mock in size and position.

| Part | Value |
|---|---|
| Size | `.katex { font-size: 1.1em }`: 18.7 px in 17 px body text. KaTeX's default is 1.21em, the kit's is 1.05em. At 1.1em the x-height of the math sits level with the x-height of Source Serif 4. That was judged by eye in a 2x render, **not measured** |
| Color | `--pb-ink`. Never the live color, never the plate color |
| Inline | Sits in the sentence. It does not change the line height: the paragraph kept its 24.99 px lines in the render |
| Display equation | On its own line, set left, indented 20 px (`--pb-gutter`) from the column edge. Same size as inline math. 20 px above and 20 px below. *Measured* in the CSS test: 19.9 and 20.1 |
| Number | At the right edge of the column, on the equation's baseline, as "Eq. 1" in `label` M1, `--pb-ink-2`. It is written `\tag*{Eq. 1}` |
| Around it | Nothing. No rule, no box, no tint |
| Too wide | The equation scrolls sideways inside its own block (`overflow-x: auto`), as the kit does today. **Not checked** |

States: none. Motion: none.

```css
/* 11 math */
.katex { font-size: 1.1em; color: var(--pb-ink); }
.katex-display { margin: 20px 0; padding: 0; overflow-x: auto; overflow-y: hidden; }
.katex-display > .katex { text-align: left; padding-left: var(--pb-gutter); }
/* the equation number: write \tag*{Eq. 1}. Only the text is restyled, so KaTeX's own strut still sets it on the equation's baseline */
.katex .katex-tag .mord { font-family: var(--pb-mono) !important; font-stretch: 75%; font-size: var(--pb-fs-label) !important; font-weight: 500; font-style: normal; letter-spacing: 0.06em; text-transform: uppercase; color: var(--pb-ink-2); }
```

*Rendered* in both themes at 390 wide.

The content: the inline value is the peak strain from `CONTENT.md`. The display equation adds the four masses of `CONTENT.md` (36 and 29 before, 62 and 3 after), with "≈" because all four are "about" values. The sun symbol for a solar mass is standard notation. No number was added.

## 12. The explainer at desktop width

Board: `Explainer-Wide.dc.html`, 1200 by 1,656. It shows the first screen (top bar, tag row, headline, plate, readout row, summary), the key idea, the section "What they found" with Fig. 2, and under them a strip that draws the measures. The strip is a note on the board, not part of the page.

The questions it answers:

**How wide is the page?** The website's grid, unchanged: 1200 px at most, 56 px side margins, 12 columns with a 24 px gutter. A column is 68.67 px.

**How wide is the text?** Columns 1 to 7: 625 px. At the desktop body size (19 / 1.5) that is about 66 characters a line. `HANDOFF.md` gives the measure as 34em, which is 646 px at 19 px. Seven columns is the grid's nearest step to that.

**Where do figures go?** Columns 9 to 12 are a rail, 346 px wide. That is the phone's column (350 px) to within 4 px, so every phone-width figure sits in the rail unchanged: the stat and range bar, a small chart, an analogy drawing. Column 8 is left empty between the two. A figure in the rail starts level with the text block that follows it in the page, with its hairline on the tops of that block's first line (22 px under the previous block on the board).

**How wide is the plate, and what is bleed?** On a phone a plate runs from one screen edge to the other. At desktop width it starts at the left edge of the text (the 56 px margin) and runs off the right edge of the screen. It is never centered and never a panel. The live line crosses the 1088 px of the grid and parks there. The ruler and the field keep going to the screen edge. This is the website's hero, and the wide board uses the same drawing: the band is 320 px tall and the block 354 px with its tick labels, 34 px under the headline. On a screen wider than 1200 px the plate still ends at the screen's right edge, not at the grid's.

**The first screen**, top to bottom, as *rendered*:

| Part | Value |
|---|---|
| Top bar | 20 px above. The wordmark at 38 px as a link (section 1). The double rule across the 1088 px |
| Tag row | 13 px under the rule. Tags at 10.5 px on the left. The journal link (16 px italic) at the right end of the grid |
| Headline | 66 / 0.95, D1 then D4. 10 px under the tag row. The second voice takes the second line |
| Plate | 34 px under the headline, from x = 56 to the right edge, 354 px tall |
| Under the plate | 6 px under. Columns 1 to 4: the readout at 48 / 1.0 and its label. Columns 5 to 9: the summary in `body`. Columns 10 to 12: the plate slug, set right. This is the row under the website's hero |
| Key idea | 56 px under. The slug, then 40 / 1.04 in D4 across columns 1 to 10 |
| Section | 56 px under. The double rule across the grid, the slug, the head at 44 / 0.98 on one line when it fits |
| Text | 19 / 1.5, 625 px. 20 px under the head, 14 px between paragraphs. Caveat: the 64 px rule and a `note` at 16 / 1.42 |
| Fig. 2 in the rail | Its hairline and head row, "410" at 88 / 0.84 with its slug and italic line, the range bar at 346 px, the legend |

Type at 1160 px and wider is the website's desktop scale (`SYSTEM.md` 2.4): labels 11 px, tags 10.5 px. Space between sections is 56 px, not the website's 96 px: the website's 96 px goes with 66 px section heads, and an explainer's section heads are 44 px. This is a decision of this pass.

Three widths of figure follow from the grid. Only the first and the last are drawn:

| Kind | Width | Drawn |
|---|---|---|
| Rail | Columns 9 to 12, 346 px | yes (Fig. 2) |
| Column | Columns 1 to 7, 625 px, in the flow of the text | no |
| Bleed | From the left edge of the text off the right edge of the screen | yes (the plate). A bleed figure inside a section (Fig. 1's field, "Try it") is not drawn |

Breakpoints:

| Width | Layout | State |
|---|---|---|
| Under 618 px | The phone page: one column, 20 px gutters, plates from edge to edge | *Rendered* at 390 (the final explainer boards) |
| 618 to 1159 px | The phone page, centered: the column stops growing at 34em plus its gutters (`HANDOFF.md` 4.3, `.pb`) | **Not drawn, not checked.** A plate there is as wide as the column and has ground on both sides, which no board shows. See open question 7 |
| 1160 px and wider | This section | *Rendered* at 1200 only |

CSS, **not rendered**. The wide board is built from the website's inline styles and one float, not from this block:

```css
@media (min-width: 1160px) {
  :root { --pb-gutter: 56px; --pb-fs-label: 11px; --pb-fs-tag: 10.5px; }
  body { font-size: 19px; line-height: 1.5; }
  .pb { max-width: 1200px; padding-bottom: 56px;
    --pb-col: calc((100% - 264px) / 12);                  /* one of twelve columns, 24 px gutters */
    --pb-text: calc(7 * var(--pb-col) + 144px);           /* columns 1 to 7 */
    --pb-rail: calc(4 * var(--pb-col) + 72px);            /* columns 9 to 12 */
    --pb-edge: calc(-1 * (var(--pb-gutter) + max(0px, (100vw - 1200px) / 2))); }   /* from the grid's right edge to the screen's */
  .pb-topbar { max-width: 1200px; padding-top: 20px; }
  .pb-wordmark { height: auto; margin-left: 0; padding: 1px 0 5px; font-size: 38px; line-height: 1; }
  .pb-wordmark em { font-weight: var(--pb-w-voice2); }
  .pb-wordmark i { width: 6.5px; height: 6.5px; margin-left: 3px; }
  .pb-title { font-size: 66px; line-height: 0.95; }
  .pb h2 { font-size: 44px; line-height: 0.98; }
  .pb-readout { font-size: 48px; }
  .pb-stat-value, .pb-hero-number { font-size: 88px; line-height: 0.84; }
  .pb-callout[data-kind="key"] { padding-top: 56px; }
  .pb-callout[data-kind="key"] p { font-size: 40px; line-height: 1.04; max-width: calc(10 * var(--pb-col) + 216px); }
  .pb-callout[data-kind="caveat"] p, .pb-fig figcaption, .pb-note { font-size: 16px; line-height: 1.42; }
  .pb-section { margin-top: 56px; display: flow-root; }
  .pb-section > p, .pb-section > .pb-callout, .pb-section > .katex-display { max-width: var(--pb-text); }
  .pb-section > p { margin-top: 14px; }
  .pb-section > h2 + p { margin-top: 20px; }
  .pb-fig { float: right; clear: right; width: var(--pb-rail); margin: 22px 0 24px; }          /* a figure goes to the rail */
  .pb-fig[data-size="column"] { float: none; clear: both; width: var(--pb-text); margin: 28px 0 0; }
  .pb-fig.pb-bleed { float: none; clear: both; width: auto; margin: 28px 0 0; }
  .pb-stage, .pb-fig.pb-bleed > svg, .pb-fig .pb-bleed { margin-left: 0; margin-right: var(--pb-edge); }
  .pb-term-pop { max-width: var(--pb-text); }
}
```

What that block leaves open, all **not checked**: the row under the plate (readout, summary, slug in three groups of columns) needs the hero's children placed on a grid, and the contract only says the three sit inside `.pb-hero`. `data-size="column"` is a new attribute. `100vw` includes the scroll bar on desktop browsers, so the plate may run a few pixels under it: the handoff's `body { overflow-x: hidden }` hides that. A figure in the rail that is taller than the text beside it pushes the next section's rule down, because the section is a flow root. And the kit's charts draw themselves at their container's width, so a rail figure is drawn at 346 px, but that was not run.

## 13. Open questions

For the owner:

1. **A way to the app from the web bar.** The web top bar is the wordmark and nothing else, as asked. A reader who opens an explainer from a shared link has no route to the APK except through the site. A second link in the bar ("Download the APK", as on the website's masthead) was not drawn, because nobody asked for it.
2. **The step text of steps that are not current is muted.** It passes contrast (5.94:1 and 6.56:1), and the reader has either just read it or is about to. If every step should stay in full ink, the slug's weight and the gauge are what is left to mark the current one.
3. **The specimen charts carry no data.** Sections 06, 07, 09, and 10 use bracket placeholders because `CONTENT.md` has no numbers for those forms. If the boards should show them with real data, `CONTENT.md` needs a paper with a series over time, a set of points, a before and after per item, and ranges.

For design, decided in this pass and worth a second look:

4. **An estimate drawn as a line is a thin muted line** (0.9 px, `--pb-ink-2`), since a line cannot be screened. `SYSTEM.md` 4.1 only covers bands and bars.
5. **A scatter point that is an estimate** has no form. An open ring is taken by "before" in the dumbbell.
6. **Tick labels.** The final boards draw ruler labels in the text color by day (`ink`). `HANDOFF.md` 4.3 gives `.pb-tick-label` the muted color (`--pb-ink-2`). The new boards follow the boards for ruler labels and use the muted color for the labels on value lines. One of the two sources has to move.
7. **The explainer between 618 and 1159 px wide** is not drawn. The plate needs a rule there: centered at column width with ground on both sides (what the handoff's CSS does today), or from the column's left edge off the right edge of the screen (what the website does from 700 px).
8. **Label size.** The new boards use 10.5 px labels and 10 px tags, as the final boards do. The contract's floor is 11 px (`HANDOFF.md` 4.7). Still open there, and it now covers these patterns too.

For the build:

9. **How a page knows it is inside the app**, so it can hide the web bar (section 1).
10. **Changes to `kit/v1/paperboy.js`** that these designs need and that were only stood in for by test scripts: the steps gauge, the reading line, and the first step's lead (section 3). The term's `aria-expanded` and the slip's position, width, and height (section 4). The toggle's visible label (section 5). The readout's node and the chart's ring, drop line, and tick (section 8). The summary text (section 2).
11. **Charts.** Sections 6, 7, 9, and 10 were drawn by hand as SVG. Whether Observable Plot can be set to produce them (the trap under the live line, the carriage, end labels that avoid each other, the ground traps under error bars) was not tried.
12. **Not drawn at all:** the readout on a line chart and on a bar, the slip above its term, a table wider than the column, an equation wider than the column, a column-width figure and an in-section bleed figure at desktop width, night at desktop width, and four or more toggle positions.
