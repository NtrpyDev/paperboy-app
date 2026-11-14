# Paperboy design addendum: app states and About

For the Android engineer (Jetpack Compose). Written 2026-11-13, after the design round closed.

`design/HANDOFF.md` left six things undrawn (section 3.1 last paragraph, the note in 6.7, section 8 item 11), and the app also needs an About screen. This file and two new boards draw them in the locked system. Nothing in `SYSTEM.md`, `HANDOFF.md`, or the seven final boards was changed. Where this file and `HANDOFF.md` disagree about one of these states, this file is later and was rendered. The two places it departs from a `HANDOFF.md` suggestion are listed in section 12.

**How to read the claims.** *Rendered* means the value is on the boards and was looked at in the local renderer. *Measured* means the number was read from the rendered page with `design/scratch/states/check.py`. *Code* means read in the app source on 2026-11-13. *Not checked* means my reading, untested. No Kotlin here was compiled, and nothing was run on a device.

Units: 1 px on the boards is 1 dp for layout and 1 sp for type, as in `HANDOFF.md` section 3. Token names are the ones in `HANDOFF.md` section 3 (Material roles in 3.1, type tokens in 3.2).

## 0. The boards

| File | Width | Height | What it is |
|---|---|---|---|
| `design/canvas/project/App-States-Day.dc.html` | 7,780 | 1,040 | 18 phone screens, each 390 by 844, in one row, 40 px apart, day |
| `design/canvas/project/App-States-Night.dc.html` | 7,780 | 1,040 | The same 18 screens, night |

*Measured* with `design/tools/dc_shot.py` at 7,780 wide: `overflow_x` false, no console errors, all three font families loaded, on both boards. Every screen root is 390 by 844. The layout is identical in both themes to the hundredth of a pixel, except the wordmark's width.

Generator: `design/scratch/states/states.py` (edit and rerun, do not hand-edit the boards). Checks and crops: `design/scratch/states/check.py`. Renders: `design/shots/states/` (`day/NN.png` and `night/NN.png` are the single screens at 2x, `NN-reduced.png` the reduced-motion stills, `measure-day.txt` and `measure-night.txt` the measured boxes).

No status bar is drawn. As on `App-Feed-Day`, the top 24 dp of a screen that starts at the top are open ground for the phone's own bar. In the app that is the status bar inset, whatever its height.

The screens:

| No. | Slug on the board | Code state |
|---|---|---|
| 01 | First load, loading | `FeedState.loading`, `items` empty. The locked loading state of `HANDOFF.md` 6.9, placed on the phone |
| 02 | First load failed, no connection | `FeedState.error = Offline`, `items` empty (test tag `first-load-error`) |
| 03 | First load failed, server error | `FeedState.error = Server`, `items` empty |
| 04 | Empty feed | `items` empty, not loading, no error |
| 05 | End of list, loading older | `FeedState.loading`, `items` not empty (the footer row) |
| 06 | End of list, older papers failed | `FeedState.error`, `items` not empty (test tag `more-error`) |
| 07 | End of the feed | `FeedState.reachedEnd` (test tag `end-of-feed`) |
| 08 | Pull to refresh, refreshing | `FeedState.refreshing` |
| 09 | Refreshed, new papers | `FeedModel.refreshed` emits `RefreshResult.Arrived(2)` |
| 10 | Refresh failed | `FeedModel.refreshed` emits `RefreshResult.Failed(Offline)` |
| 11 | Less like this, stamped | `ratings[id] == Less`, 0 to 700 ms after the tap |
| 12 | Less like this, feed up | About 762 ms after the tap, a held frame of the move |
| 13 | Less like this, hidden | `FeedModel.collapsed` emitted, from 1,060 ms |
| 14 | Explainer did not load | `PageFailure.Offline` in `ExplainerScreen.kt` (test tag `explainer-error`) |
| 15 | Feed, the way to About | The feed at rest, with the wordmark shown pressed |
| 16 | About, top | New screen |
| 17 | About, scrolled | The same screen, scrolled 774 dp |
| 18 | About, end | The same screen, scrolled to its end |

Screens 01 and 05 were not asked for. They are the locked loading state put where the phone needs it, because the failure, refresh, and retry states all start from it. They add no new design.

## 1. New parts

Five parts are new. All are built from existing tokens.

### 1.1 Head row

A row that says what a block is and what state it is in. It is the figure head row of `SYSTEM.md` 4.2 rule 8 used for the app's own voice.

- Left: the name, in `slug`, `onSurface`. Right: the state, in `label`, `onSurfaceVariant`, right aligned. Baselines aligned. At least 12 dp between them.
- 20 dp at the sides. 15 dp above it when it follows the masthead or a top bar, 13 dp when it follows a card divider or opens the refresh strip.
- Height of the text line: 13.65 dp. *Measured.*

### 1.2 The strip

The flat live line of `HANDOFF.md` 6.9, placed. One horizontal path from x = 20 to x = 370 on a 390 dp screen (margin to margin), in a band 36 dp tall, the line at the band's middle (18 dp down). The band follows a head row directly, with no gap. It has three states, and it is the only place the live color appears in any of these screens besides the wordmark dot and a card's own plate.

| State | Drawn | Used in |
|---|---|---|
| **Loading** | The live line of `SYSTEM.md` 5.3 sweeps from left to right, its pen point at the tip, then the pen point pulses at the right end | 01, 05, 08 |
| **Rest** | The whole line, the pen point parked at the right end. Nothing moves | 04, 07 |
| **Idle** | No live line. A 0.9 dp track in `onSurfaceVariant` from x = 20 to x = 370, closed at the right end by a cap 10 dp tall and 0.9 dp wide. The pen point waits at the left end, centered on x = 20 | 02, 03, 06, 14 |

Line and pen point values are the ones in `SYSTEM.md` 5.3 and are not repeated here: 1.9 dp core, the trap, the night halo, the 3.6 dp pen point on its 6.5 dp ground dot (3.4 on 5 with the three-disc halo at night). The pen point is centered on the end of the path, so it overhangs the margin by its radius, as it does on Plate 1.

Why the idle state looks like this: it is the loading state at 0 ms (pen at the start, nothing drawn) plus the empty track. So when the reader taps "Try again", the sweep starts from exactly the frame on screen.

`role="img"` text for each state, for the content description: Loading: "Loading: a flat line is drawn across the sheet, then its pen point waits". Rest: "A flat line, fully drawn, with its pen point at rest at the end: nothing more to report". Idle: "No signal: an empty track, with the pen point waiting at its start".

The band height of 36 dp is my choice. The motion board's loading cell is not a phone layout and gives no value.

### 1.3 The cover

The block for "this did not load" and "there is nothing here". Top to bottom:

1. Head row (1.1).
2. The strip (1.2).
3. A two-voice headline, 2 dp under the band, 20 dp at the sides. `headline` (44 / 0.98) when the cover is the whole screen, `head-2` (30 / 1.02) in the feed's footer. The first voice says what, the second voice is always the turn.
4. One sentence in `body-feed`, `onSurface`, 10 dp under the headline.
5. One action, 14 dp under the sentence, 350 dp wide, 48 dp tall. Or none.

The cover sits at the top of the screen, under the masthead or the top bar, the way a lead story does. It is not centered in the screen.

### 1.4 The notice

Takes the Material snackbar's job (the undo message and the two refresh messages). *Rendered* on screens 09, 10, 13.

- A band across the foot of the screen, edge to edge (390 dp), flush with the bottom, square. No margin around it, no corner radius, no shadow, no elevation.
- Fill `secondary` (`#5A554B` day, `#9C988D` night). Text and outline `onSecondary` (`#E9E6DE` day, `#0E1116` night). Contrast 5.94:1 day, 6.56:1 night (`SYSTEM.md` section 3). This is the stamped rating's fill, one step under the primary slab, so a card's own action stays the heaviest thing in view.
- Minimum height 64 dp. Padding 10 dp top and bottom, 20 dp at the sides. In the app, add the navigation bar inset under the bottom padding so the band reaches the screen's edge. The boards draw no inset.
- Left: the message, one sentence, in Source Serif 4 regular at 16 sp with a 20.8 sp line height (the `body-feed` face at a tighter leading), `onSecondary`. It may wrap to two lines.
- Right, 16 dp from the message at least, one of: an outline button (44 dp tall, 1 dp outline in `onSecondary`, 14 dp padding at the sides, label in `rate`, then a 14 dp icon 9 dp after the label), or a `label` in `onSecondary` that says where to look, or nothing.
- It lies over the feed. The feed does not move for it.

Measured button widths: "Undo" 93.5 dp, "Try again" 123.8 dp.

### 1.5 Icons and one button form

- `RETURN`, new, 14 dp box, 1.5 dp stroke, square ends, for Undo: `<path d="M11.5 2.5v5.5H3M6 4.5L2.5 8 6 11.5">`.
- `ARROW` (the existing arrow) at two smaller sizes: 14 dp box at 1.5 dp stroke in the notice's "Try again" (`M1.5 7h10.5M8 3l4 4-4 4`), and 13 by 11 dp at 1.3 dp stroke after an in-app text link (`M1.5 5.5h9.5M7.5 2l3.5 3.5L7.5 9`). `OUTARROW` stays for links that leave the app.
- "Try again" on a cover is the 48 dp button of `SYSTEM.md` 9.6 with `ARROW` at 20 dp on the right: the primary slab on a full-screen cover, the outline form in the feed's footer.

## 2. First load: loading, failed, empty (screens 01 to 04)

All four share the masthead at the top (0 to 73.75 dp: 24 inset, a 44 dp row, the 5.75 dp double rule).

### 2.1 Loading (01)

**When:** `state.loading` and `state.items.isEmpty()`. Replaces the `CircularProgressIndicator` in `EmptyFeed`.

**Layout:** masthead, head row, strip. *Measured:* head row text at 88.75 to 102.39 dp, band 102.39 to 138.39, line at 120.39. Nothing else on the screen.

**Copy:** `Loading new papers` and `No signal yet` (the locked words of `HANDOFF.md` 6.9).

**Motion:** Loading (`HANDOFF.md` 6.9): Sweep and Travel, 1,900 ms, `linear`, 320 ms delay, then Pulse (2,400 ms, `ease-in-out`, from 2,400 ms). The first card replaces the block.

**Reduced-motion still:** the whole line with the pen point at its right end.

### 2.2 First load failed (02, 03)

**When:** `state.error != null` and `state.items.isEmpty()` and not loading. Replaces the centered column in `EmptyFeed`.

**Layout:** masthead, then the cover (1.3) with the strip idle. *Measured* from the top of the screen: head row text 88.75 to 102.39, band 102.39 to 138.39 (track at 120.39), headline box 138.39 to 226.61 (2 dp of padding, then two lines of 43.12), sentence box 226.61 to 259.33 (10 dp of padding, then one 22.72 dp line), button 273.33 to 321.33. The rest of the screen is open ground.

**Type and color:** head row as 1.1. Headline `headline`, first line D1, second line the second voice, `onSurface`. Sentence `body-feed`, `onSurface`. Button: the primary slab, `primary` fill, `onPrimary` label in `button`, `ARROW` 20 dp.

**Copy.** The headline is the same for every reason. The head row's right label and the sentence carry the reason. The sentences are the app's current `failureText` strings, unchanged.

| `Reason` | Head row | Headline | Sentence |
|---|---|---|---|
| `Offline` | `Feed not loaded` / `No connection` | The feed / *did not load.* | You are offline, or the feed cannot be reached. |
| `Server` | `Feed not loaded` / `Server error` | The feed / *did not load.* | The feed server had a problem. |
| `BadData` | `Feed not loaded` / `Unreadable data` | The feed / *did not load.* | The feed arrived in a form this app cannot read. |

Button: `Try again` (was "Retry"). `BadData` is given as copy only. Its screen was not drawn, because nothing else differs.

What differs between "no connection" and the other failures: the right label and the sentence. Nothing else. The code does not say more than that, so the drawing does not either.

**Motion:** on arrival the two headline lines Press (190 ms, `cubic-bezier(0.2, 0, 0, 1)`, 0 and 50 ms). The strip changes from loading to idle in one step, with no move: the live line is removed, the track and the pen point at the left are there. On "Try again" the cover is replaced by the loading block (2.1) and the sweep starts from the pen point's place. The swap itself has no animation.

**Reduced-motion still:** the screen as drawn.

### 2.3 Empty feed (04)

**When:** `state.items.isEmpty()`, not loading, no error (the `else` branch of `EmptyFeed`, today "No papers yet.").

**Layout:** as 2.2, with the strip at rest, no button, and under the sentence: 20 dp, a 64 dp footnote rule (0.75 dp, `outlineVariant`), then the link `About Paperboy` (44 dp target, `note` italic, 0.75 dp underline 3 dp under, `ARROW` 13 by 11 after it). *Measured:* link box 280.08 to 324.08.

**Copy:** head row `Feed loaded` / `Nothing to show`. Headline: No papers yet. / *The feed is empty.* Sentence: Pull down to check for new papers.

The screen stays scrollable so the pull works, as the code has it. There is no button because the code has none (section 13, question 6).

**Motion:** headline lines Press. **Reduced-motion still:** as drawn.

## 3. The end of the list (screens 05 to 07)

The footer is the last row of the list (`FeedFooter`, key `footer`). It follows the last card's divider (the hairline and the 3 dp rule), so the heavy rule reads as its head, as it does for a card. The boards show the footer under the short card. *Measured:* divider ends at 533.67 dp on all three screens, which is where the footer starts.

Open ground under the footer was not set by the boards. I would leave 40 dp. *Not checked.*

### 3.1 Loading older (05)

**When:** `state.loading` with items. Replaces the footer's `CircularProgressIndicator`.

**Layout:** head row (13 dp above), strip. 62.64 dp tall in all. *Measured.*

**Copy:** `Loading older papers` / `No signal yet`.

**Motion:** Loading, as 2.1, starting when the footer comes into view. **Still:** the whole line.

**Pulse rule.** `HANDOFF.md` 6.5 allows one pulsing pen point on a screen. While a strip is loading it holds the pulse, and the pen point of any plate in view rests at full opacity. *Not checked* in the app: the feed's plates may be still pictures with no pulse at all (`HANDOFF.md` 3.6).

### 3.2 Older papers failed (06)

**When:** `state.error != null` with items.

**Layout:** the cover (1.3) at footer size, strip idle. *Measured* from the footer's top: head row text 13 to 26.64, band 26.64 to 62.64, headline box 62.64 to 95.24 (one line of 30.6), sentence box 95.24 to 150.67 (two lines), outline button 164.67 to 212.67.

**Type and color:** headline `head-2`, D1 then the second voice on the same line. Sentence `body-feed`. Button: the outline form (1 dp `outline`, label `onSurface` in `button`), because the cards above keep their own slabs.

**Copy:** head row `Older papers not loaded` and the reason label from 2.2. Headline: Older papers *did not load.* Sentence: the reason sentence from 2.2, then `The papers above are still here.` Button: `Try again`.

At 390 dp the headline fits on one line (326.7 dp of the 350, *measured*). On a narrower phone break before the second voice, never inside it (`SYSTEM.md` 2.2 rule 3).

**Motion:** the headline Presses. On "Try again" the block becomes 3.1. **Still:** as drawn.

### 3.3 The end of the feed (07)

**When:** `state.reachedEnd`, not loading, no error.

**Layout:** the cover at footer size, strip at rest, no button, then 16 dp, the 64 dp footnote rule, and the link `About Paperboy`. *Measured* from the footer's top: headline box 62.64 to 125.83 (two lines), sentence 125.83 to 181.27, link box 198.02 to 242.02.

**Copy:** head row `End of the feed` / `Nothing older`. Headline: You have reached / *the end of the feed.* (the current sentence, kept). Sentence: There are no older papers. New ones arrive at the top of the feed.

The second sentence is true by `FeedSession.refresh()` (*code*): new papers go above the first card.

**Motion:** if the footer was loading, the line simply stays and the pen point stops pulsing. The headline Presses. **Still:** as drawn.

## 4. Pull to refresh (screens 08 to 10)

### 4.1 Refreshing (08)

**When:** `state.refreshing`. Replaces the indicator of `PullToRefreshBox`. No spinner.

**Layout:** the strip opens between the masthead and the first card, in the place the first load draws it, and the cards move down by its height. Top to bottom: masthead, head row (13 dp above), band (36), then a card divider with no space above it (0.75, 2, 3: 5.75 dp), then the first card with its usual 13 dp above the tag row. *Measured:* the strip block is 73.75 to 136.39 dp (62.64 tall), so the first card starts 68.39 dp lower than at rest. (`App-Feed-Day` gives the first card 15 dp above its tag row and 16 above its plate, a tuning of that board that `HANDOFF.md` does not carry. Screen 08 uses the usual 13 and 12. Screens 09, 10, and 15 repeat `App-Feed-Day` as it is.)

**Copy:** `Loading new papers` / `No signal yet`, the same as the first load.

**Motion.** The line is drawn by the pull:

1. While the finger pulls, the block opens with the pull (its height follows the pull, up to 62.64 dp), and the live line's length follows the pull too: at the release threshold the line is whole. No easing, it is under the finger.
2. Released past the threshold: `onRefresh` runs. If the line is not whole yet it finishes at the hero's speed (1,900 ms for the whole width, `linear`). Then Pulse until the result arrives.
3. Released short of the threshold: the block closes by Feed up (360 ms, `cubic-bezier(0.2, 0, 0, 1)`) and nothing is asked.
4. When the result arrives, the cards feed up over the block (Feed up, 360 ms, same easing) and the notice lands (4.2).

Steps 1 to 4 are a specification. Only the resting frame of step 2 was rendered. How `PullToRefreshBox` takes a custom indicator that pushes content, and how the pull distance is read, was *not checked*.

**Reduced-motion still:** the block open, the whole line, the pen point at the right end. It opens and closes in one step.

### 4.2 Refreshed (09) and refresh failed (10)

**When:** each value from `FeedModel.refreshed`.

**Layout:** the notice (1.4) over the feed. The feed is where the reader left it.

| Result | Message | Right side |
|---|---|---|
| `Arrived(0)` | No new papers | nothing |
| `Arrived(1)` | 1 new paper | label `At the top of the feed` |
| `Arrived(n)` | n new papers (the board shows "2 new papers") | label `At the top of the feed` |
| `Failed(Offline)` | Could not refresh. No connection. | button `Try again`, `ARROW` 14 |
| `Failed(Server)` | Could not refresh. Server error. | button `Try again` |
| `Failed(BadData)` | Could not refresh. Unreadable data. | button `Try again` |

The failed message is shorter than today's ("Could not refresh. " plus the whole reason sentence), so it fits beside the button in two lines. The second sentence is the reason label of 2.2. `Arrived(0)`, `Arrived(1)`, and the server and bad data failures are copy only, not drawn.

**Motion:** the notice lands by Press (190 ms, `cubic-bezier(0.2, 0, 0, 1)`: opacity 0 to 1 and a 6 dp rise), after the block of 4.1 has closed. It stays as long as the snackbar does today: `SnackbarDuration.Short` for arrivals and `Long` for a failure (*code*; the lengths of Short and Long were *not checked*). It leaves by Press run backward (190 ms, same easing, opacity 1 to 0 with a 6 dp fall). `HANDOFF.md` section 6 names no exit, so this reuse in reverse is the one move in this file that is not a named animation as written. "Try again" calls `onRefresh` and the notice leaves at once.

**Reduced-motion still:** the notice in place. It appears and leaves in one step.

## 5. "Less like this" (screens 11 to 13)

**When:** a tap on "Less like this" (`FeedModel.rate`). The code waits `COLLAPSE_DELAY_MS` (700 ms), then calls `collapse` and emits the id on `collapsed`.

**The feed item.** One item is a card and the divider under it (18 dp of space, the 0.75 dp hairline, 2 dp, the 3 dp rule: 23.75 dp). The short card on the boards is 294.02 dp, so its item is 317.77 dp. *Measured.*

**Timeline, from the tap:**

| Time | What happens | Animation |
|---|---|---|
| 0 to 120 ms | The "Less like this" button is stamped: fill `secondary`, label `onSecondary`, minus turned to a check | Stamp (`HANDOFF.md` 6.7), 120 ms, `cubic-bezier(0.2, 0, 0, 1)`, label and icon in one step at 60 ms |
| 120 to 700 ms | Nothing moves. The reader sees what they chose (screen 11) | none |
| 700 to 1,060 ms | The card leaves (screen 12 is this move at about 762 ms, 42 percent of the way) | Feed up (`HANDOFF.md` 6.8), 360 ms, `cubic-bezier(0.2, 0, 0, 1)` |
| 1,060 to 1,250 ms | The notice lands: `Paper hidden`, button `Undo` with `RETURN` (screen 13) | Press, 190 ms, `cubic-bezier(0.2, 0, 0, 1)` |

**How the card leaves.** By Feed up and nothing else. The item's height goes from its full height to 0. Its content is held to the item's bottom edge and clipped to the item, so the card and everything under it rise together as one sheet, and the card goes under the rule above it (the previous card's divider), top first. The stamped button is the last part of it to go. Everything above the item stays where it is. Nothing fades, nothing slides sideways, nothing wipes, and no frame has a filled bar on a left edge: the only edge in the move is the horizontal rule the card passes under. The divider under the card is part of the item, so when the move ends the next card sits directly under the rule that was above the hidden one.

In Compose I would animate the item's height with `tween(360, easing = CubicBezierEasing(0.2f, 0f, 0f, 1f))`, with the content bottom-aligned and `clipToBounds()`, in place of the default `Modifier.animateItem()`. *Not checked.*

The stamp frames were *rendered* at 2,090, 2,124, 2,170, and 2,400 ms of the board's clock, where the stamp starts at 2,100 (`design/shots/states/stamp-frames-2090-2124-2170-2400ms.png`): outline, half strength at 1.05 with the minus, full fill with the check, rest. The board's stamp is the stepped form `HANDOFF.md` 6.7 says to build. The Feed up move itself was not animated on the board. Screen 12 is a still made by clipping the card to 160 dp.

**Undo.** The notice stays for `SnackbarDuration.Short` (*code*), then leaves by Press backward (4.2). A tap on `Undo` calls `onUndoLess`, the notice leaves at once, and the card comes back by Feed up run backward (360 ms, same easing): the item opens from 0 to its height and the card comes down from under the rule, with its rating cleared (both buttons outlined, the minus back). The return was *not rendered*.

The message keeps the current words `Paper hidden` and `Undo`.

**Reduced-motion still:** the stamped button without the jump, the card removed in one step at 700 ms, the notice in place.

## 6. Explainer did not load (screen 14)

**When:** `failure != null` in `ExplainerScreen.kt`. Replaces `PageFailed`. It covers the WebView under the explainer top bar.

**Layout:** the explainer top bar of `SYSTEM.md` 9.2 with the 24 dp inset above it (0 to 77.75 dp: inset, a 48 dp row, the 5.75 dp double rule), then the cover (1.3), strip idle, on the screen's ground from the bar to the bottom. *Measured:* head row text 92.75 to 106.39, band 106.39 to 142.39, headline box 142.39 to 230.61, sentence box 230.61 to 286.05 (two lines), button 300.05 to 348.05.

The top bar's back control ("Feed", `slug`, 44 dp target) and the phone's back both leave the screen. Today the screen has no bar (`HANDOFF.md` 3.4), so the bar is part of this state's build.

**Copy:**

| `PageFailure` | Head row | Headline | Sentence |
|---|---|---|---|
| `Offline` | `Explainer not loaded` / `No connection` | This explainer / *did not load.* | You are offline, or the server cannot be reached. |
| `Server` | `Explainer not loaded` / `Server error` | This explainer / *did not load.* | The server had a problem. |

Button: `Try again`, the primary slab. The sentences are the current strings. The server case is copy only.

**Motion:** headline lines Press. "Try again" removes the cover and reloads, as the code does. What shows while the page loads is not designed (section 13, question 8). **Still:** as drawn.

## 7. About (screens 15 to 18)

### 7.1 Getting there and back (15)

The masthead does not change to the eye. **The wordmark is the link.** Its box in the masthead row (140 by 44 dp by day, 145.7 by 44 at night, *measured*) is a button with the content description "About Paperboy". Pressed, the wordmark's letters go to `onSurfaceVariant` and the dot keeps the live color. No ripple. Screen 15 shows it pressed.

Because that link has no label of its own, the words `About Paperboy` also appear as a text link in two places where the reader has run out of feed: under the empty feed (2.3) and at the end of the feed (3.3).

I did not add a visible control to the masthead. Between the wordmark (ends at x = 160) and the strap (starts at x = 209) there are 49 dp, and the theme button's target runs from x = 337 to 381 (*measured* on screen 02, whose masthead is the one on `App-Feed-Day`). A second 44 dp target beside the theme button, with the row's 10 dp gap, would push the strap to within about 5 dp of the wordmark. Section 13, question 2 gives the alternative.

Back: the top bar's `Feed` control, and the phone's back.

### 7.2 The screen (16 to 18)

A fixed top bar (the explainer top bar, 0 to 77.75 dp) over one scrolling column, 20 dp at the sides. The column, top to bottom, with the measured position of each block's top in the column (0 is the bar's bottom edge):

| Top, dp | Block | Type and color | Copy |
|---|---|---|---|
| 15 | Head row | `slug` / `label` | `About` / `Version 0.1.0` |
| 38.6 | Title, three lines | `headline`, third line second voice | New science / and math papers, / *explained visually.* |
| 182 | Paragraph, 14 dp above | `body` | Paperboy is a free, open source Android app: an endless feed of newly released science and math papers, peer-reviewed and preprints, each labeled as one or the other. No account. No ads. |
| 318.9 | Paragraph, 12 dp above | `body` | Every card links to the original paper. “More like this” and “Less like this” tune the feed, and your ratings stay on this phone. |
| 433.8 | Section: 40 dp, double rule (heavy on top), 12, head row, 8, head | `slug` / `label`, `head-2` | `How an explainer is made` / `Machine written`. Three AI agents, / *one job each.* |
| 546.4 | Paragraph, 12 dp above | `body` | Papers with a free legal full text get a visual explainer, made by three agents in turn. |
| 636.4 | Figure: 40 dp, hairline, 10, head row, 14, the drawing (84 tall) | `slug` / `label` | `Paper in, explainer out` / `Illustration` |
| 772.8 | Three rows, 14 dp under the drawing. Each: hairline, 12, label, 8, statement, 14 | label `slug` with "of 3" in `label` muted, statement `head-2` | `Agent 1 of 3` Reads the paper / *as a domain expert.* `Agent 2 of 3` Builds *the visuals.* `Agent 3 of 3` Checks every number / against the paper, / *and checks the* / *visuals are clear.* |
| 1,156.9 | Row: 24 dp, hairline, 12, label, 10, sentence, 12, paragraph | `label` muted, `key-idea`, `body` | `Every explainer`. *Machine written, and it can be wrong.* The page says so, and links the source so you can check it against the paper. |
| 1,359.1 | Section | `slug`, `head-2` | `Source`. Free and *open source.* |
| 1,441 | Paragraph, then 14, the outline button (48), then 14, the address | `body`, `button` with `OUTARROW` 15, `note` | Paperboy’s source code is public. `Source on GitHub`. github.com/NtrpyDev/paperboy-app |
| 1,603 | Section | `slug`, `head-2` | `Licenses`. The app, the typefaces, / *and the libraries.* |
| 1,715.6 | Ledger, 12 dp under the head: three rows as `SYSTEM.md` 9.16 (hairline, 11, label left and value right on one baseline, 4, note, 12), then a closing hairline | label `label` muted, value `readout-s`, note `note` | `The app` **GPL 3.0** The GNU General Public License, version 3 or later. `Typefaces` **OFL 1.1** Noto Serif Display, Source Serif 4, and Martian Mono, each under the SIL Open Font License 1.1. `Libraries` **NOTICE.md** The open source libraries in the app, each with its license. |
| 1,995.6 | Text link, 44 dp target | `note`, `OUTARROW` 11 | Read it on GitHub |

The column is 2,102.6 dp tall on the boards with 63 dp of open ground at its end. The 63 was set so the last screen crops cleanly. Use 40 dp or more.

**The drawing** is the website's "Paper in, explainer out" (`SYSTEM.md` 9.20 item 5) at phone width, in both themes: three plates 100.67 dp wide and 84 tall, 24 dp apart, and one live line through their middle from the left margin to a pen point on the right margin. Plate one is the paper as lines of text (two 2.6 dp title lines, one 0.9 dp author line, then 0.8 dp lines 4.5 dp apart, in `outline`). Plate two is the ring field of Plate 1 in its fine pass only. Plate three is the same field with its swells. Both ring plates are `gw_print()` at scale 0.42, centered on the middle of each plate's right edge. The night drawing was made for this board (the website has no night theme): `plate-night` rings, text lines in light-muted, the amber line with its halo. In the app it can be one still picture per theme, with the line drawn over it, or two stills. Its `role="img"` text is in the board.

**Facts and their sources.** Product facts: `design/CONTENT.md`. "Explained visually" and "an endless feed": the product line in the repository's `CLAUDE.md`. Version: `versionName = "0.1.0"` in `app/build.gradle.kts`. The app should print `BuildConfig.VERSION_NAME`, not the literal. Licenses: `NOTICE.md` ("version 3 or later", the three font families under the SIL Open Font License 1.1, the library table).

**Links.** `Source on GitHub` opens `https://github.com/NtrpyDev/paperboy-app` in the browser. `Read it on GitHub` points at `NOTICE.md` in that repository. The board writes `/blob/main/NOTICE.md`. The branch name was *not checked*.

**Motion:** on open, the three title lines Press (0, 50, 100 ms). The drawing's line runs once by Line through plates (`HANDOFF.md` 6.10: 1,600 ms, `linear`, 900 ms delay). `HANDOFF.md` calls that animation website only. Using it here is new. If it is not wanted, draw the line whole. Nothing else moves.

**Reduced-motion still:** the screen as drawn, the line whole, the pen point at its right end.

## 8. Final copy, in one place

| Where | Was | Is |
|---|---|---|
| Every retry | Retry | Try again |
| First load failed, title | The feed could not load | The feed *did not load.* |
| First load failed, reason | (the three `failureText` sentences) | unchanged |
| Empty feed | No papers yet. | No papers yet. *The feed is empty.* Pull down to check for new papers. |
| Footer, failed | Older papers could not load. (reason) | Older papers *did not load.* (reason) The papers above are still here. |
| Footer, end | You have reached the end of the feed. | You have reached *the end of the feed.* There are no older papers. New ones arrive at the top of the feed. |
| Undo message | Paper hidden / Undo | unchanged |
| Refresh, arrived | No new papers, 1 new paper, n new papers | unchanged, with the label "At the top of the feed" when n is 1 or more |
| Refresh, failed | Could not refresh. (reason sentence) / Retry | Could not refresh. No connection. (or: Server error. Unreadable data.) / Try again |
| Explainer failed, title | This explainer could not load | This explainer *did not load.* |
| Explainer failed, reason | (the two sentences) | unchanged |
| Head row labels | none | Feed not loaded, Feed loaded, Loading older papers, Older papers not loaded, End of the feed, Explainer not loaded, No connection, Server error, Unreadable data, Nothing to show, Nothing older |

No exclamation marks, no em dashes. Italics above mark the second voice.

The instrumented tests assert some of the old strings: "Retry" (`FailureStatesTest`), "Older papers could not load. The feed server had a problem." as one node, and "You have reached the end of the feed." (`EndlessFeedTest`). They will need the new words. The tests were *not run*.

## 9. Semantics

- The cover's headline is a heading. The head row's two labels read before it.
- The strip has a content description per state (1.2) and is not focusable.
- The notice is a polite live region (`role="status"` on the boards) so its message is announced. Its button is a button with the label as drawn.
- The wordmark link's description is "About Paperboy". The rating buttons keep the semantics `RatingButton` has today.
- Every target on the two boards is at least 44 dp in both directions (112 targets per board, *measured*).

## 10. Reduced motion, in one place

Every animated element's own style is its resting frame, as in `HANDOFF.md` 6.11. Both boards were rendered with `prefers-reduced-motion: reduce`: zero running animations on either, and a still of every screen is saved (`NN-reduced.png`). Twelve of the 36 stills were looked at (night 07 to 12, day 13 to 18) and are complete. In short: lines are whole with the pen point parked, the idle strip is as drawn, stamps and notices are in place with no jump or rise, and a hidden card is simply gone.

## 11. What was checked

- Both boards: `overflow_x` false, no console errors, three font families loaded (`dc_shot.py`, 7,780 wide, frames at 0.3, 1.2, and 4 s).
- `check.py --audit` on both boards: no target under 44 px, no HTML text pair under 4.5:1 (3:1 at 24 px and up), mono text never under 10 px, other text never under 15 px, no element with a shadow, no corner radius except circles.
- The live color is on no text and no button. The only rounded things are pen points and wordmark dots.
- Looked at: every screen in both themes at rest, twelve reduced-motion stills, the loading sweep part way (0.3 and 1.2 s), the stamp at four held times.
- *Not checked:* anything in Compose, any device, the Claude Design canvas itself (the boards were rendered only in the local Chromium tool), hover and focus states.

## 12. Where this departs from HANDOFF.md

1. `HANDOFF.md` 3.1 maps a snackbar to `inverseSurface` (the ink slab). The notice uses `secondary`, the stamped fill. An ink band the width of the screen was as heavy as a card's "See it explained", and at night it would have been a second `light` slab. This was reasoned, not rendered both ways.
2. `HANDOFF.md` 3.1 suggests the outline button for "Try again". The two full-screen covers use the primary slab, because it is the one action on the screen. The footer uses the outline form.

## 13. Open questions

For the owner:

1. **"An update is needed" is drawn on the Paid-States boards (phone 5, day and night).** `FeedState.updateNeeded` shows a tinted `Surface` above the feed with "Get the update" (test tag `update-needed`). It was not on the list for this pass and `HANDOFF.md` does not mention it. A tinted box is not in this language, so it needs a drawing. It could be a cover in the strip's place (head row, one sentence, the outline button). That is a suggestion, not rendered.
2. **The way to About has no visible label in the masthead.** The wordmark is the link, and the words "About Paperboy" appear only under an empty feed and at the end of the feed. If the theme button is removed (`HANDOFF.md` section 8 item 1), an `About` text link in `slug` could take its place at the right end. If it stays, the choice is this, or a crowded masthead.
3. **Does the masthead scroll away with the feed, or stay?** `App-Feed-Night` shows it gone, the app today has a fixed bar. Screens 09 and 10 assume the reader still sees the top of the feed after a refresh. If new papers are put above and the reader is not moved (`EndlessFeedTest`), what is on screen in the masthead's place needs a decision.
4. **Should the "n new papers" notice be a button that scrolls to the top?** Today it is a message only. Not drawn.
5. **The notice in the stamped fill**, not the ink slab (section 12, item 1).
6. **The empty feed has no button**, only "Pull down". A "Check again" button would call the same refresh. Not drawn, because the code has none.
7. **The About title says "explained visually"**, where the website says "explained in pictures". The website's line is 387.9 dp wide in the second voice at 44 sp and the column is 350 (*measured*). "Explained visually" is the wording in the repository's own description and fits at 333 dp by day and 338 at night.
8. **The explainer's loading state is not designed.** Nothing says what shows between the tap and the page. The cover's head row and a loading strip under the top bar would be consistent. Not drawn.
9. **Explainers are under CC BY 4.0** (`NOTICE.md`). About does not say so, because it was not in the brief's list of licenses.
10. **"GPL 3.0" as the ledger value.** The brief says GPL-3.0 and `NOTICE.md` says version 3 or later. The hyphen of the display face is a hairline beside weight 800 figures, so the board sets "GPL 3.0" to match "OFL 1.1" and puts "version 3 or later" in the note.

For the build team:

11. Custom pull-to-refresh that opens the strip and draws the line with the pull (4.1). Not prototyped.
12. Item removal by height with bottom-aligned, clipped content (section 5). Not prototyped.
13. The pulse rule when a loading strip and a plate are both in view (3.1).
14. `FeedSession.refresh()` called before any chunk has loaded returns `Arrived(items.size)`, so a pull on the failed first-load screen that succeeds would say "n new papers" for the whole first load (*code*). Whether that message is wanted there is a product call.
15. The lengths of `SnackbarDuration.Short` and `Long`, if the notice is built without Material's snackbar.
16. Two sentences on the boards use CSS `text-wrap: balance` (screen 06) or `pretty`. Line breaks in Compose will differ. Only headline breaks are part of the design.
17. The band height of the strip (36 dp) and the 24 dp status bar allowance are board values. Insets come from the phone.
