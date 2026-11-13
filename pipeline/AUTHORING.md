# Authoring an explainer

How to build the page that teaches one paper. The automated rules are in `EXPLAINER-CONTRACT.md`; this file is the craft. The kit's components and helpers are listed at the end.

## What an explainer is

A reader scrolls a feed, sees a card, taps it, and gives you about ten seconds. By the end of the first screen they should know what was found. By the end of the page they should understand it well enough to explain it to a friend, including how sure anyone can be. They get there by looking and by playing, with short text between visuals. Text carries what pictures cannot; pictures carry everything else.

## The page, in order

1. **Hero.** Field and badge, the hook as the headline, a one or two sentence dek, and the hero visual on the stage. The hero visual is the finding itself, shown: the thing that moved, the signal that appeared, the structure that formed. Its still frame becomes the card image in the feed, so it must be striking and readable with no motion.
2. **The question** (`data-section="question"`). What nobody knew. Teach the one or two ideas the reader needs first, each with a small visual or an interactive if it helps.
3. **What they did** (`data-section="method"`). The method as a sequence the reader can watch: scroll steps driving one visual, or a diagram that builds.
4. **What they found** (`data-section="findings"`). The evidence, in charts drawn from the brief's evidence table. Lead with the single most important number as a number.
5. **How sure is this** (`data-section="confidence"`). Strengths, limits, open questions, from the brief. Plain and specific to this paper. A preprint says it has not been peer reviewed.
6. **Why it matters** (`data-section="matters"`). What changes, said without inflation.
7. **Source footer.** The citation, the license, a link to the paper, and the note that the page is machine written and can be wrong.

Aim for 5 to 8 visuals and 350 to 650 words of prose. A paragraph is two to four sentences.

## Writing

- Plain words, short sentences, active voice. Define a term the first time it appears, in the sentence or as a tappable glossary term.
- Say exactly as much as the paper supports. "Suggests", "in mice", "in a simulation", "in this sample of 48 people" when that is the truth.
- An analogy is labeled as one and says where it breaks.
- Headlines state findings. No questions, no hype words, no exclamation marks, no em dashes.
- Every number comes from the brief's evidence table, with its unit. Round only with "about".

## Visuals that teach

Decide what the reader must see, then pick the form.

- **One number is the story:** show it as a number, large, with one line of context. Not a chart.
- **Compare a few magnitudes:** horizontal bars from a zero baseline, sorted, thin, values at the bar ends. If one bar is the point, give it the accent and gray the rest.
- **A trend:** a line, two pixels, with the end point labeled. Two or three series at most, each labeled at its end.
- **Before and after:** a dumbbell (two dots joined by a line) per item.
- **Part of a whole:** one segmented bar, six parts at most. Never a pie or donut.
- **A distribution or many points:** dots, with the few that matter labeled.
- **A process or mechanism:** an illustration that builds in steps or animates the cause leading to the effect.
- **A relationship the reader can feel:** an interactive: a slider that changes the parameter the paper varied, with the visual responding.

Rules that hold for every chart:

- One vertical axis. Two measures with different scales get two charts.
- Start bars at zero. Label axes with units. Hairline solid gridlines, light. No chart junk.
- Direct labels on the marks that matter; a legend whenever there are two or more series. Text is always in the ink colors, never in a series color.
- Series colors come from the kit, in the kit's order. Never invent a color for data.
- Every data figure carries its numbers as a table (`PB.table`), a title that states what the chart shows, and a caption that says where in the paper the numbers come from.
- A concept drawing is marked `data-kind="illustration"`. It must not look like measured data: no fake axes with invented values, no scatter of made-up points.

## Motion

- Motion explains: a cause producing an effect, a signal arriving, a structure assembling, a quantity changing as the reader drags. Decoration that moves is noise.
- Every animation has a still frame that reads correctly alone. Pass `still` to `PB.animate` so readers with reduced motion, and the feed's card image, get the most informative frame, not the empty first one.
- Loops are calm, a few seconds long, with no flashing. Entrances happen once.
- Scroll steps: three to six steps, each a sentence or two, each changing the pinned visual in one clear way.

## Interaction

- A control changes one thing and the visual answers immediately. Label the control with what it changes and show its current value with units.
- Controls are at least 40 px tall and work with a thumb. The page works at 390 px wide with no sideways scrolling.
- Tappable glossary terms for jargon the reader will meet again.

## Honesty

- Data figures plot only numbers from the paper. If the paper gives four numbers, the chart has four marks.
- Where the paper gives uncertainty, show it (error bars, a band, a range in the label).
- Say what the paper does not show, in the confidence section, in plain words.
- A figure reproduced from the paper is allowed only when the brief's "Figures worth reproducing" lists it (license CC BY or CC0), marked `data-kind="paper"`, with its credit line.
- Never use a box or card with a colored bar or stripe down its left edge.

## Technical ground rules

- One file, `index.html`. Everything the page needs beyond the kit is inline: SVG, canvas code, data. No external requests of any kind.
- The kit provides d3, Observable Plot, and KaTeX. Page code goes inside `PB.ready(function () { ... })`.
- Draw with the kit's theme colors (`PB.theme(el)`), so day and night both work. Visuals on the stage use the stage's own colors.
- Redraw on resize: use `PB.plot`, `PB.svg`, or `PB.canvas`, which handle it.
- Keep the page light: no large embedded images, no data arrays beyond what the charts need.

## The kit

<!-- KIT-REFERENCE: this section is maintained with the kit. It lists every component class and every PB helper with a short example. -->
