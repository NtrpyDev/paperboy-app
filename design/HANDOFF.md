# Paperboy design handoff

For the engineers building the Android app, the explainer kit, and the website. Written 2026-11-13 at the close of the design round.

`design/SYSTEM.md` is the design system as built. This file says how to build it. Where the two disagree, `SYSTEM.md` wins on what the design is, and this file should be fixed.

**How to read the claims in this file.** A value marked *rendered* is in one of the seven final boards and was looked at in the local renderer. A statement marked *docs* was read on the page named, on 2026-11-13. A statement marked *not checked* is my reading and has not been tested. Kotlin in this file is a sketch: none of it was compiled.

## 0. The boards

All in `design/canvas/project/`. Open the `.dc.html` files in the Claude Design canvas, or render them with `design/tools/dc_shot.py` (see `design/CONTEXT.md`). Final renders are in `design/shots/final/`.

| File | Title | Width | Height | Fluid |
|---|---|---|---|---|
| `App-Feed-Day.dc.html` | Paperboy feed, day | 390 | 844 | no |
| `App-Feed-Night.dc.html` | Paperboy feed, night | 390 | 844 | no |
| `Explainer-Day.dc.html` | Explainer, Paper 1, day | 390 | 5,796 | no |
| `Explainer-Night.dc.html` | Explainer, Paper 1, night | 390 | 5,796 | no |
| `Site.dc.html` | Paperboy website, day | 1440 | 4,868 | yes. 5,550 tall at 1024, 6,697 at 700, 6,918 at 390 |
| `Brand.dc.html` | Paperboy brand: wordmark and app icon | 1200 | 900 | no |
| `Motion.dc.html` | Paperboy motion: the named animations | 1200 | 1000 | no |

Measured from the root element and from the screenshot tool's `scrollHeight`. No board overflows sideways. All three font families load on every board with no console errors.

## 1. Fonts to bundle

Three families, all under the SIL Open Font License 1.1. *Docs:* in github.com/google/fonts each family's `METADATA.pb` says `license: "OFL"` and each folder holds `OFL.txt` (`ofl/notoserifdisplay`, `ofl/sourceserif4`, `ofl/martianmono`). Ship each family's `OFL.txt` with the app and the kit, and add the three families to `NOTICE.md`. Source Serif 4's copyright line carries the Reserved Font Name "Source". What that means for a renamed or subset file was not checked: read the OFL before subsetting.

### 1.1 The cuts the design uses

Ten cuts. Nothing else is used anywhere.

| Cut | Family | Style | Weight | Width | Used for |
|---|---|---|---|---|---|
| D1 | Noto Serif Display | roman | 800 | 62.5 | Headlines, wordmark "Paper", readouts, section heads. Day. |
| D2 | Noto Serif Display | roman | 900 | 62.5 | The same, night. |
| D3 | Noto Serif Display | roman | 700 | 75 | Button labels. |
| D4 | Noto Serif Display | italic | 300 | 100 | Second voice, key idea, wordmark "boy". Day. |
| D5 | Noto Serif Display | italic | 400 | 100, and 87.5 inside a night headline | The same, night, and at 22 px or less. |
| T1 | Source Serif 4 | roman | 400 | | Body, summaries. |
| T2 | Source Serif 4 | roman | 500 | | Rating button labels. |
| T3 | Source Serif 4 | italic | 400 | | Notes, captions, units, journal link. |
| M1 | Martian Mono | roman | 500 | 75 | Labels. |
| M2 | Martian Mono | roman | 600 | 75 | Tags, slugs. |

### 1.2 Variable files (web, kit, and Android 8 and later)

*Docs:* these five files are what github.com/google/fonts ships. It has no static instances.

| File | Axes | Size |
|---|---|---|
| `NotoSerifDisplay[wdth,wght].ttf` | wdth 62.5 to 100, wght 100 to 900 | 1,835,176 bytes |
| `NotoSerifDisplay-Italic[wdth,wght].ttf` | same | 2,000,744 bytes |
| `SourceSerif4[opsz,wght].ttf` | opsz 8 to 60, wght 200 to 900 | 1,209,508 bytes |
| `SourceSerif4-Italic[opsz,wght].ttf` | same | 855,432 bytes |
| `MartianMono[wdth,wght].ttf` | wdth 75 to 112.5, wght 100 to 800 | 148,460 bytes |

That is about 6 MB before subsetting. Android resource names must be lowercase with no brackets (*docs:* the Compose fonts guide says the file name must be "all lowercase and doesn't contain any special characters"), so rename on import, for example `notoserifdisplay_variable.ttf`.

### 1.3 Static files (needed for Android 7, API 24 and 25)

*Docs:* the Compose fonts guide says "Variable fonts are only supported on Android O and above" and shows a guard on `Build.VERSION.SDK_INT >= Build.VERSION_CODES.O` with a static fallback. The app's `minSdk` is 24 (`app/build.gradle.kts`). So either `minSdk` goes to 26, or the app also bundles static files. That choice is the owner's.

Static files exist upstream for nine of the ten cuts. *Docs:* file listings read from the GitHub API.

| Cut | Static file | Where |
|---|---|---|
| D1 | `NotoSerifDisplay-ExtraCondensedExtraBold.ttf` | github.com/notofonts/notofonts.github.io, `fonts/NotoSerifDisplay/unhinted/ttf/` (72 files) |
| D2 | `NotoSerifDisplay-ExtraCondensedBlack.ttf` | same |
| D3 | `NotoSerifDisplay-CondensedBold.ttf` | same |
| D4 | `NotoSerifDisplay-LightItalic.ttf` | same |
| D5 | `NotoSerifDisplay-Italic.ttf`, and `NotoSerifDisplay-SemiCondensedItalic.ttf` for night headlines | same |
| T1 | `SourceSerif4-Regular.ttf` | github.com/adobe-fonts/source-serif, `TTF/` |
| T2 | none at weight 500. The static weights are ExtraLight, Light, Regular, Semibold, Bold, Black. | same |
| T3 | `SourceSerif4-It.ttf` | same |
| M1 | `MartianMonoCondensed-Medium.ttf` | github.com/evilmartians/mono, `fonts/ttf/` |
| M2 | `MartianMonoCondensed-SemiBold.ttf` | same |

Three things here are *not checked*: that "ExtraCondensed" is width 62.5, "Condensed" is 75, and "SemiCondensed" is 87.5 in the Noto files (the names fit the axis range, the files were not opened); that Martian Mono "Condensed" is width 75 (it is the narrowest of four named widths on an axis that starts at 75); and that those two repositories carry the same OFL text as the Google Fonts copies. T2 needs a decision on API 24 and 25: draw rating labels in Regular there, or make a 500 instance from the variable file.

### 1.4 Web

- **The website** may load the three families from Google Fonts with the `<link>` in `SYSTEM.md` section 2 (`CONTEXT.md`: "the site will load them"). Self-hosting works too.
- **The explainer kit** must self-host. `pipeline/EXPLAINER-CONTRACT.md` fails a page on any request to another host (`external-request`). Put the five variable files in the kit (as WOFF2 if you convert them, which was not done here) and declare them:

```css
@font-face { font-family: 'Noto Serif Display'; font-style: normal; font-weight: 100 900; font-stretch: 62.5% 100%; font-display: swap; src: url('/kit/v1/fonts/NotoSerifDisplay.woff2') format('woff2'); }
@font-face { font-family: 'Noto Serif Display'; font-style: italic; font-weight: 100 900; font-stretch: 62.5% 100%; font-display: swap; src: url('/kit/v1/fonts/NotoSerifDisplay-Italic.woff2') format('woff2'); }
@font-face { font-family: 'Source Serif 4'; font-style: normal; font-weight: 200 900; font-display: swap; src: url('/kit/v1/fonts/SourceSerif4.woff2') format('woff2'); }
@font-face { font-family: 'Source Serif 4'; font-style: italic; font-weight: 200 900; font-display: swap; src: url('/kit/v1/fonts/SourceSerif4-Italic.woff2') format('woff2'); }
@font-face { font-family: 'Martian Mono'; font-style: normal; font-weight: 100 800; font-stretch: 75% 112.5%; font-display: swap; src: url('/kit/v1/fonts/MartianMono.woff2') format('woff2'); }
```

These `@font-face` rules were *not rendered*: every board loaded the fonts from Google Fonts. The kit path is written as `v1` only as an example. `GLOSSARY.md` says old kit versions stay served forever, so whether this lands as a new kit version is the build team's call.

## 2. CSS custom properties, day and night

This block keeps the names the kit already has (`--pb-page`, `--pb-ink`, `--pb-ink-2`, `--pb-muted`, `--pb-grid`, `--pb-axis`, `--pb-accent`), so `PB.theme()` in `kit/v1/paperboy.js` keeps reading them, and adds the rest. It switches the same way `kit/v1/paperboy.css` does: the system setting, with `data-theme="light"` or `data-theme="dark"` on `<html>` to force one. *Rendered* in a test page in both themes at 390 wide (`design/scratch/final/handoff-test/`).

```css
:root {
  color-scheme: light dark;

  /* names the kit already has (PB.theme() reads these) */
  --pb-page: #E9E6DE;      /* stock */
  --pb-ink: #16130F;       /* ink: text */
  --pb-ink-2: #5A554B;     /* ink-muted: second-rank text */
  --pb-muted: #5A554B;     /* the design has two text ranks, so this equals ink-2 */
  --pb-grid: #5A554B;      /* grid, drop, and leader lines, 0.6 px */
  --pb-axis: #16130F;      /* ruler lines and ticks, 0.9 px */
  --pb-accent: #E0330A;    /* live: the one live mark. Never text. */

  /* new names */
  --pb-rule: #16130F;      /* rules, tag outlines, button outlines */
  --pb-slab: #16130F;      /* primary button, solid tag */
  --pb-on-slab: #E9E6DE;
  --pb-stamp: #5A554B;     /* stamped rating */
  --pb-on-stamp: #E9E6DE;
  --pb-plate: #1F3FD0;     /* print ink: screens and engraved rings only */
  --pb-contour: #16130F;   /* the black plate layer */
  --pb-screen: #16130F;    /* estimate and range screens */
  --pb-carriage: #16130F;

  /* type */
  --pb-display: 'Noto Serif Display', Didot, 'Bodoni MT', Georgia, serif;
  --pb-font: 'Source Serif 4', Georgia, 'Times New Roman', serif;
  --pb-mono: 'Martian Mono', 'DejaVu Sans Mono', Menlo, monospace;
  --pb-w-voice1: 800;      /* D1 */
  --pb-w-voice2: 300;      /* D4 */
  --pb-st-voice2: 100%;    /* width of the second voice inside a headline */
  --pb-ls-readout: -0.005em;
  --pb-fs-label: 10.5px;
  --pb-fs-tag: 10px;

  /* the live line */
  --pb-live-core: 1.9px;
  --pb-live-trap: 7px;
  --pb-halo-a: 0; --pb-halo-b: 0; --pb-halo-c: 0;   /* opacity of the 17, 11, 6 px halo strokes */
  --pb-pen: 3.6px;
  --pb-pen-trap: 6.5px;

  /* the plate */
  --pb-ring: 0.5px;
  --pb-ring-opacity: 1;

  --pb-measure: 34em;
  --pb-gutter: 20px;
  --pb-radius: 0;
}

@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --pb-page: #0E1116; --pb-ink: #E9E4D7; --pb-ink-2: #9C988D; --pb-muted: #9C988D;
    --pb-grid: #5E6573; --pb-axis: #9C988D; --pb-accent: #FFA63D;
    --pb-rule: #9C988D; --pb-slab: #E9E4D7; --pb-on-slab: #0E1116;
    --pb-stamp: #9C988D; --pb-on-stamp: #0E1116;
    --pb-plate: #4D63C9; --pb-contour: #9C988D; --pb-screen: #9C988D; --pb-carriage: #E9E4D7;
    --pb-w-voice1: 900; --pb-w-voice2: 400; --pb-st-voice2: 87.5%; --pb-ls-readout: 0.02em;
    --pb-live-trap: 4px; --pb-halo-a: 0.05; --pb-halo-b: 0.12; --pb-halo-c: 0.08;
    --pb-pen: 3.4px; --pb-pen-trap: 5px;
    --pb-ring: 0.6px; --pb-ring-opacity: 0.55;
  }
}
:root[data-theme="dark"] {
  --pb-page: #0E1116; --pb-ink: #E9E4D7; --pb-ink-2: #9C988D; --pb-muted: #9C988D;
  --pb-grid: #5E6573; --pb-axis: #9C988D; --pb-accent: #FFA63D;
  --pb-rule: #9C988D; --pb-slab: #E9E4D7; --pb-on-slab: #0E1116;
  --pb-stamp: #9C988D; --pb-on-stamp: #0E1116;
  --pb-plate: #4D63C9; --pb-contour: #9C988D; --pb-screen: #9C988D; --pb-carriage: #E9E4D7;
  --pb-w-voice1: 900; --pb-w-voice2: 400; --pb-st-voice2: 87.5%; --pb-ls-readout: 0.02em;
  --pb-live-trap: 4px; --pb-halo-a: 0.05; --pb-halo-b: 0.12; --pb-halo-c: 0.08;
  --pb-pen: 3.4px; --pb-pen-trap: 5px;
  --pb-ring: 0.6px; --pb-ring-opacity: 0.55;
}
```

Every hex value is a token from `SYSTEM.md` section 3, where its contrast ratio is listed.

What happens to the other tokens in `kit/v1/paperboy.css`:

| Kit v1 token | In this design |
|---|---|
| `--pb-surface`, `--pb-raised`, `--pb-wash` | Gone. There are no surfaces, tints, or raised cards. Everything sits on `--pb-page`. |
| `--pb-border` | `--pb-rule`, at full strength. |
| `--pb-accent-ink` | Gone. No text wears the accent. The section eyebrow is `--pb-ink`. |
| `--pb-radius: 16px` | 0. |
| `--pb-s1` to `--pb-s8` (eight hued series) | Five series told apart by lightness and form, four at most in a chart (section 4.4). |
| `--pb-seq-*`, `--pb-div-*` (sequential and diverging ramps) | Not designed in this round. No board has a heatmap or a diverging chart. |
| `--pb-good`, `--pb-warning`, `--pb-serious`, `--pb-critical` | Gone from the confidence section, which must not use status colors. Not redesigned for any other use. |
| `.pb-stage` always dark | Gone. A plate has a day drawing and a night drawing (section 4.6). |

## 3. Android Compose mapping

The app today (`app/src/main/java/io/github/ntrpydev/paperboy/ui/`) uses plain Material 3 defaults: `PaperboyTheme.kt` calls `lightColorScheme()` or `darkColorScheme()` by `isSystemInDarkTheme()`, and `FeedCard.kt` is a Material `Card` with an image, four `Text`s, and Material buttons. `PaperboyTheme.kt` says the visual design replaces it. This section is that replacement.

Units: the boards are 390 px wide. Read 1 px as 1 dp for layout and 1 sp for type. Phones are not all 390 dp wide, and the headline line breaks on the boards were set by hand, so the app needs its own rule for breaking a headline (`SYSTEM.md` 2.2 rule 3). That rule was not prototyped in Compose.

### 3.1 Color scheme

Role names are from the `ColorScheme` reference (*docs:* developer.android.com/reference/kotlin/androidx/compose/material3/ColorScheme). The text I captured from that page was cut off after `surfaceContainerHighest`, so `surfaceContainerLow` and `surfaceContainerLowest` are assumed from the pattern.

| Material role | Day | Night | Why |
|---|---|---|---|
| `background`, `surface`, `surfaceVariant`, `surfaceBright`, `surfaceDim`, every `surfaceContainer*` | `#E9E6DE` | `#0E1116` | One ground. No tonal surfaces. |
| `surfaceTint` | `#E9E6DE` | `#0E1116` | So elevation adds no tint. |
| `onBackground`, `onSurface` | `#16130F` | `#E9E4D7` | Text. |
| `onSurfaceVariant` | `#5A554B` | `#9C988D` | Second-rank text. |
| `primary` | `#16130F` | `#E9E4D7` | The primary slab and the solid tag. |
| `onPrimary` | `#E9E6DE` | `#0E1116` | |
| `secondary` | `#5A554B` | `#9C988D` | The stamped rating. |
| `onSecondary` | `#E9E6DE` | `#0E1116` | |
| `tertiary` | `#E0330A` | `#FFA63D` | The live mark. Graphics only, never text, never a button. |
| `onTertiary` | `#E9E6DE` | `#0E1116` | Not used by the design. Set so the role is complete. |
| `outline` | `#16130F` | `#9C988D` | Tag, button, and rating outlines, 1 dp. |
| `outlineVariant` | `#16130F` | `#9C988D` | Hairlines, 0.75 dp. |
| `inverseSurface` | `#16130F` | `#E9E4D7` | A snackbar, drawn as the ink slab. See the note below. |
| `inverseOnSurface` | `#E9E6DE` | `#0E1116` | |
| `inversePrimary` | `#E9E6DE` | `#0E1116` | |
| `scrim` | `#16130F` | `#0E1116` | |
| `primaryContainer`, `secondaryContainer`, `tertiaryContainer` and their `on` roles, `error` and its roles | not designed | not designed | No board uses a container color or an error color. |

Five colors have no Material role. Carry them in a small class of your own through a `CompositionLocal`: `plate` (`#1F3FD0` / `#4D63C9`), `contour` (`#16130F` / `#9C988D`), `screen` (`#16130F` / `#9C988D`), `grid` (`#5A554B` / `#5E6573`), and the night `texture` `#2B303B`, which the final boards do not use.

Not drawn in this round, so not specified: the snackbar that offers to undo a "less like this" rating (`FeedModel.collapsed`), the pull-to-refresh message (`FeedModel.refreshed`), the feed's failure state with its retry (`FailureStatesTest`), and the explainer's load-failure cover (`ExplainerScreen.kt`). The loading state is drawn (section 6.9). Build the others from the parts: text in `body-feed`, the outline button for "Try again", the ink slab for a snackbar.

### 3.2 Type styles

Font loading follows the Compose fonts guide (*docs*): `Font(R.font.x, variationSettings = FontVariation.Settings(FontVariation.weight(800), FontVariation.width(62.5f)))` inside a `FontFamily`, guarded for API 26, with static `Font(R.font.x, FontWeight.X, FontStyle.Y)` entries as the fallback. A custom axis is set with `FontVariation.Setting("opsz", value)`, as the guide does for `"YTAS"`. Whether Compose applies Source Serif 4's optical size on its own was not checked. On the web it is automatic.

One style per token. Line height is size times the ratio. Tracking is in em.

| Token | Family and cut | Size sp | Line height sp | Tracking em | Suggested Material slot |
|---|---|---|---|---|---|
| `readout-xl` | D1 (D2 night) | 72 | 62 | −0.005 (0.02 night) | `displayLarge` |
| `headline` | D1, second voice D4 | 44 | 43 | −0.005, second voice −0.012 | `displayMedium` |
| `readout` | D1 | 44 | 44 | −0.005 (0.02 night) | `displaySmall` |
| `wordmark` | D1 + D4 | 33 | 33 | −0.005, "boy" −0.02 | none, it is one composable |
| `head-2` | D1, second voice D4 | 30 | 30.6 | same as headline | `headlineLarge` |
| `key-idea` | D4 (D5 night) | 30 | 31.8 | −0.012 | `headlineMedium` |
| `readout-s` | D1 | 30 | 30 | −0.005 | `headlineSmall` |
| `button` | D3 | 23 | 23 | 0.005 | `titleLarge` |
| `wordmark-s` | D1 + D5 | 22 | 22 | as wordmark | none |
| `body` | T1 | 17 | 25 | 0 | `bodyLarge` |
| `body-feed` | T1 | 16 | 22.7 | 0 | `bodyMedium` |
| `rate` | T2 | 16 | 16 | 0 | `labelLarge` |
| `note` | T3 | 15 | 21 | 0 | `bodySmall` |
| `label` | M1, caps | 10.5 | 13.65 | 0.06 | `labelMedium` |
| `slug` | M2, caps | 10.5 | 13.65 | 0.06 | `titleSmall` |
| `tag` | M2, caps | 10 | 13 | 0.06 | `labelSmall` |

The slot names are from the `Typography` constructor (*docs:* fifteen parameters, `displayLarge` to `labelSmall`). The mapping onto them is only so stock Material components pick up sane defaults. Call the tokens by their own names in your code.

- The second voice is a span inside the headline's string: italic, weight 300 (400 at night), width 100 (87.5 in a night headline). The content marks it. See section 3.5 for the missing field.
- All numerals are lining figures. In CSS that is `font-variant-numeric: lining-nums`. The Compose equivalent was not checked.
- Display leading is tight (0.86 to 1.02). How Compose's font padding and line height trimming treat that was not checked, and it will need a look on a device.
- The multiplication sign and the greater-than sign beside display numerals are drawn as two-stroke paths in a box half the font size, stroke 1.05 in a 10 unit box (`SYSTEM.md` 2.2 rule 6). Do not type them in the display face.
- Mono text is never under 10 sp and sentences are never under 15 sp. These are sp, so they follow the reader's font scale.

### 3.3 Shapes

Everything is square. *Docs:* `Shapes(extraSmall, small, medium, large, extraLarge)` takes `CornerBasedShape` values, and the reference says "by default, buttons use the shape style 'full'". So:

- Set all five to a zero-radius corner shape (`RoundedCornerShape(0.dp)`, not compiled).
- Do not use Material `Button`, `OutlinedButton`, or `Card` for the designed parts. Their defaults (full-round shape, elevation, tonal fill, minimum widths, ripple shape) all fight the design. Build the slab, the outline button, the rating button, the tag, and the card as your own composables from `Box`, `Row`, `border`, and `clickable` or `toggleable`. Keep the semantics the current `RatingButton` has.
- The only circles are the pen point, the wordmark dot, the legend dot, and the theme icon.

### 3.4 Components

Measurements are in `SYSTEM.md` section 9 with the exact markup. In short:

| Part | Build |
|---|---|
| Double rule | Two rectangles: 3 dp and 0.75 dp, 2 dp apart. Heavy on top under a masthead or at a section head, hairline on top between cards. Night color `#9C988D`. |
| Masthead | Wordmark 33 sp, strap in `label` right aligned, theme button 44 dp, double rule. |
| Explainer top bar | A 48 dp row with a back control ("Feed", `slug`, 44 dp target) and the 22 sp wordmark, then the double rule. The board shows the bar and the page as one screen. I would build the bar natively above the WebView, because the same page is also served on the web, where a "Feed" link has nothing to go back to. Today `ExplainerScreen.kt` is a full-screen WebView with no bar. Whichever side draws it, only one side should. |
| Tag row | Field tag (1 dp outline), badge (solid for PEER-REVIEWED, hatched frame for PREPRINT: parallel lines at 135 degrees, 1.1 dp on a 3.2 dp pitch, clipped to a 3.5 dp frame), journal link right aligned in `note` with an 11 dp out-arrow and a 44 dp target. The row wraps with a 6 dp row gap. |
| Headline | `headline` on a hero card, `head-2` on a short card. Two voices. |
| Plate | Full width, no padding, no corner radius, no border. Section 3.6. |
| Readout row | Numeral in `readout`, its label under it in `label` muted, the plate slug right aligned in `label` muted over three lines. |
| Summary | `body-feed`. |
| Primary button | 48 dp tall ink slab, label in `button`, a 20 dp arrow at the right. "See it explained". |
| Outline button | The same box with a 1 dp outline and a 15 dp out-arrow. "Read the paper". |
| Rating row | Two equal 44 dp outline buttons 8 dp apart, 14 dp icon, label in `rate`. Stamped: fill `secondary`, label `onSecondary`, plus turned to a check. |
| Short card | No plate, no summary: tag row, `head-2` headline, optional stat (44 sp numeral beside a two-line label), outline button, rating row. |

Margins: 20 dp at the sides. Inside a card: 13 above the tag row, 10 above the headline, 12 above the plate, 6 above the readout row, 10 above the summary, 14 above the buttons, 8 between buttons, 18 under them before the divider.

**Theme switch.** The masthead on the boards has a theme button. The owner has not ruled on it (`SYSTEM.md` section 14). Today `themes.xml` makes the WebView's `prefers-color-scheme` follow the system. If the button stays, the app must also push its choice into the explainer page, and the kit already has the hook for that: `data-theme` on `<html>`.

### 3.5 What a card needs that the feed item does not have

`schema/feed-item.schema.json` against the card on the boards:

| Card part | Feed item field | Gap |
|---|---|---|
| Field tag | `field` | none |
| Badge | `status` | none |
| Journal link | `venue`, `url` | none |
| Headline | `hook` | `hook` is a plain string. The second voice needs the turning clause marked, and it must be marked by whoever writes the hook, never guessed from position. With no mark the whole headline is D1, which is allowed. |
| Plate | `hero` (one image, captured from the dark page) | Section 3.6. |
| Readout numeral, unit, and label | none | New data. The pipeline would have to supply the one number, its unit, and what it measures. |
| Plate slug ("Plate 1, Illustration, not to scale") | none | New data: whether the plate is data or an illustration, and to scale or not. What the plate number counts in a live feed was not defined. On the boards it is 1, 2, 3 for the three example papers. |
| Summary | `summary` | none |
| Short card stat | none | The same readout data. Optional. |

The design does not show `tags`, `published`, `authors_short`, or `significance` on a card. That is a statement about the boards, not a request to remove the fields.

### 3.6 The plate in the app

This is the largest open build question, and `SYSTEM.md` section 13 leaves it open.

What the design asks for on a card:

1. A plate in the reader's theme: a day drawing on stock or a night drawing on the blue-black ground. Not one always-dark image.
2. The plate at 390 by 196 (the print band) with a ruler strip under it when the line is plotted on a real axis, 230 tall in all. Full bleed, square.
3. One live line that draws in when the card first comes into view, with its pen point and carriage, then rests. One per screen.
4. A resting frame that is complete as a still. A reader with reduced motion sees only that.

What exists: the pipeline captures `hero.webp` from the dark render of the page's `.pb-stage`, at most 1200 px wide, and the app shows it with Coil at the image's own ratio.

Two routes, with what each costs:

- **Pictures.** The pipeline captures two stills per paper, day and night, of the plate at rest, at the plate's ratio. The card shows the one for the theme. The feed has no sweep. Point 4 makes this acceptable: the still is designed to stand alone. This needs a second capture, a second image field, and a contract change, since `.pb-stage` is fixed dark today.
- **Drawing.** The pipeline also publishes the live line as path data with its ruler, and the app draws the line over the still print layers. *Docs:* `PathMeasure.getSegment`, `getPosition`, `getTangent`, and `length` cover the sweep, the pen point, and the carriage from one progress value. This keeps the sweep in the feed and is more work in both the pipeline and the app.

Either way the app does not need to draw rings, wells, or line screens itself. If it ever does: a ring is a circle, a swell is a closed path of two arcs, a screen is parallel lines under a rotation and a clip. None of that was built in Compose.

## 4. The explainer page

The explainer is one HTML document per paper that loads the kit (`pipeline/EXPLAINER-CONTRACT.md`, `pipeline/AUTHORING.md`). The board `Explainer-Day.dc.html` is the target for a page at 390 wide. This section maps the kit's classes onto the design and gives a stylesheet that was *rendered* in a test page in both themes (`design/scratch/final/handoff-test/kit.css` and `test.html`). The test covers the patterns named below. It does not cover the kit's JavaScript.

### 4.1 Page order

The board's order matches the contract's five `data-section` values:

| Order | Contract | Slug on the page | Head on the board (second voice in italics) |
|---|---|---|---|
| 1 | `.pb-hero` with `.pb-title`, `.pb-dek`, one `.pb-stage` | tag row | "Two black holes merged. *Earth felt space stretch.*" then the plate, the readout row, the summary |
| 2 | | `KEY IDEA` | one sentence in the display italic |
| 3 | `data-section="question"` | `THE QUESTION` | "Can a machine on Earth *feel space stretch?*" |
| 4 | `data-section="method"` | `WHAT THEY DID` | "Two detectors, *each an L with 4 km arms.*" |
| 5 | `data-section="findings"` | `WHAT THEY FOUND` | "One chirp, *a fifth of a second long.*" |
| 6 | `data-section="confidence"` | none | "How sure *is this?*" |
| 7 | `data-section="matters"` | `WHY IT MATTERS` | "Two firsts *in one signal.*" |
| 8 | `.pb-source` | `SOURCE` | title, authors, journal line, "Read the paper", closing line |

In the hero the dek comes after the plate and the readout. The contract only asks that all three sit inside `.pb-hero`.

### 4.2 Class by class

| Kit v1 class | What it draws today | What it draws in this design |
|---|---|---|
| `.pb` | A 680 px column | A 34em column with 20 px gutters. Plates and bleed figures break out to the screen edges. |
| `.pb-kicker`, `.pb-badge` | Caps line with a pill | The tag row: outline field tag, solid or hatched badge, journal link. No pills. |
| `.pb-title` | Sans headline | `headline`, two voices through `<em>`. |
| `.pb-dek` | Gray lead | The summary, in the text color at `body`. |
| `.pb-stage` | A dark rounded 4:3 frame | The plate: full bleed, square, in the theme's own colors. No frame. |
| `.pb-section`, `.pb-eyebrow` | Padded section, accent-colored eyebrow | A double rule (heavy on top), the slug in ink, then a two-voice `h2`. |
| `.pb-fig[data-kind]` | A bordered rounded card with a pill label | A hairline, then a head row: `data-slug` on the left ("Fig. 2", "For scale", "Try it"), the kind on the right ("Data, from the paper", "Illustration, not to scale", or "Illustration, drawn to scale" with `data-scale="true"`). No box. |
| `.pb-fig-title` | Bold line | `head-2` in D1 ("Where the mass went"). |
| `figcaption` | Small gray text | One sentence in `note`, in the text color. |
| `.pb-legend` | Row of rounded swatches | Row in `label`: a 7 px dot for the live mark, a 22 by 10 px screen swatch for a screen. |
| `.pb-callout[data-kind="key"]` | Tinted box with a colored left border | **Key idea.** The slug, then one sentence at 30 / 1.06 in the display italic with 40 px above. Nothing around it. |
| `.pb-callout[data-kind="caveat"]` | Tinted box with a colored left border | **Caveat.** A dagger typed in the running text after the claim. Then a 64 px hairline and the note in `note`, opening with the same dagger. The label is hidden. |
| `.pb-callout[data-kind="analogy"]` | Tinted box with a colored left border | **Analogy.** A figure, not a callout: `<figure class="pb-fig" data-kind="illustration" data-slug="For scale">`, the drawing, then one sentence as the `figcaption`. An analogy with no drawing would be a `note` under a slug. That bare form is spec, not rendered. |
| `.pb-stats`, `.pb-stat`, `.pb-hero-number` | Bordered tiles | **Stat.** One numeral at 72 / 0.86 with a slug and an italic line beside it, bottoms aligned, then the figure that draws its range. No tile. One stat per figure. |
| `.pb-confidence` | Cards with a green, amber, or purple dot | **Confidence.** A ledger: rows split by full-width hairlines, label in mono on the left, value in display figures on the right, an italic note under. Subheads `STRENGTHS` and `LIMITS`. No dots, no status colors. |
| `.pb-source` | Small gray footer | **Source.** Double rule, slug, title in the text italic at 17, authors muted at 15, two mono lines, the outline button, the closing line. |
| `.pb-btn` | Rounded tinted button | The outline button, or the ink slab with `data-kind="primary"`. 48 px tall, square. |
| `.pb-slider` | Track with a round accent thumb | The carriage on the ruler: a transparent 44 px input laid over the figure's ruler, with a 12 by 22 px square thumb in the text color. |
| `.pb-reveal` | Fade and rise on scroll | Replaced by the named draw-ins (section 6). Text does not fade in on scroll. Only a figure's one live mark draws in. |
| `.pb-steps`, `.pb-step` | Sticky visual with shadowed step cards | **Not drawn in this round.** |
| `.pb-toggle` | Rounded segmented control | **Not drawn in this round.** |
| `.pb-term`, `.pb-term-pop` | Dotted accent underline, rounded shadowed popover | **Not drawn in this round.** |
| `.pb-tip` | Rounded shadowed tooltip | **Not drawn in this round.** |
| `.pb-data`, `.pb-table` | Disclosure with a table of the chart's numbers | **Not drawn in this round.** The contract requires a table in every data figure, and the board's data figures do not show one. |
| KaTeX math | KaTeX defaults | **Not drawn in this round.** |

The five patterns marked not drawn need a design pass before the kit can ship in this language. Until then the rules that would govern them are in `SYSTEM.md` section 10: no boxes, no tints, no shadows, no radius, hierarchy from type and rules.

Every rule in `kit/v1/paperboy.css` that draws a `border-left` on a callout must go. That is the form the owner named first.

### 4.3 Stylesheet

Tokens are in section 2. Motion is in section 6. This is the rest.

```css
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--pb-page); color: var(--pb-ink); font-family: var(--pb-font); font-size: 17px; line-height: 1.47; overflow-x: hidden; }
.pb { max-width: calc(var(--pb-measure) + 2 * var(--pb-gutter)); margin: 0 auto; padding: 0 var(--pb-gutter) 40px; }
.pb p { margin: 14px 0 0; text-wrap: pretty; }
.pb a { color: var(--pb-ink); text-decoration-thickness: 0.75px; text-underline-offset: 3px; }
.pb a:focus-visible, .pb button:focus-visible { outline: 2px solid var(--pb-ink); outline-offset: 2px; }

/* the mono label, the section slug, the tag */
.pb-label, .pb-eyebrow, .pb-kicker, .pb-callout-label, .pb-legend, .pb-fig::before, .pb-fig::after, .pb-confidence b, .pb-confidence-head, .pb-source small {
  font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500;
  letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; color: var(--pb-ink-2);
}
.pb-eyebrow, .pb-callout-label, .pb-fig::before, .pb-confidence-head { font-weight: 600; color: var(--pb-ink); }

/* tags and badges: outline, solid, screened. Never told apart by hue. */
.pb-kicker { display: flex; flex-wrap: wrap; align-items: center; column-gap: 6px; row-gap: 6px; padding-top: 13px; }
.pb-tag, .pb-badge { font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-tag); font-weight: 600; letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase; color: var(--pb-ink); border: 1px solid var(--pb-rule); padding: 4px 6px 3px; white-space: nowrap; }
.pb-badge[data-status="peer_reviewed"] { color: var(--pb-on-slab); background: var(--pb-slab); border-color: var(--pb-slab); }
.pb-badge[data-status="preprint"] { border: 0; padding: 3.5px; background-image: repeating-linear-gradient(135deg, var(--pb-rule) 0 1.1px, transparent 1.1px 3.2px); }
.pb-badge[data-status="preprint"] > span { display: block; background: var(--pb-page); padding: 1.5px 4px 0.5px; }
.pb-journal { margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; font-family: var(--pb-font); font-stretch: 100%; font-size: 15px; font-weight: 400; font-style: italic; line-height: 1; letter-spacing: 0; text-transform: none; white-space: nowrap; }

/* the two voices */
.pb-title, .pb h2, .pb h3, .pb-readout, .pb-stat-value, .pb-hero-number, .pb-confidence .v {
  font-family: var(--pb-display); font-weight: var(--pb-w-voice1); font-stretch: 62.5%; letter-spacing: -0.005em; font-variant-numeric: lining-nums; margin: 0;
}
.pb-title em, .pb h2 em, .pb h3 em { font-style: italic; font-weight: var(--pb-w-voice2); font-stretch: var(--pb-st-voice2); letter-spacing: -0.012em; }
.pb-title { font-size: 44px; line-height: 0.98; padding-top: 10px; }
.pb h2 { font-size: 30px; line-height: 1.02; margin-top: 12px; }
.pb h3 { font-size: 30px; line-height: 1; margin-top: 10px; }
.pb-dek { font-size: 17px; line-height: 1.47; }

/* the readout row under a plate */
.pb-readout-row { display: flex; align-items: flex-end; justify-content: space-between; padding-top: 6px; }
.pb-readout { font-size: 44px; line-height: 1; letter-spacing: var(--pb-ls-readout); }
.pb-readout sup, .pb-stat-value sup { font-size: 0.56em; line-height: 0; vertical-align: 0.72em; letter-spacing: 0.01em; }
.pb p sup { font-size: 0.64em; line-height: 0; }
/* the multiplication sign and the greater-than sign beside display numerals are drawn: <svg class="pb-sign" viewBox="0 0 10 10"><path d="M1.6 1.6l6.8 6.8M8.4 1.6l-6.8 6.8"/></svg> and <path d="M1.8 1.4l6.6 3.6-6.6 3.6"/> */
.pb-sign { display: inline-block; width: 0.5em; height: 0.5em; margin: 0 0.13em 0 0.15em; vertical-align: 0.1em; fill: none; stroke: currentColor; stroke-width: 1.05; }
.pb-unit { font-family: var(--pb-font); font-size: 15px; font-weight: 400; font-style: italic; font-stretch: 100%; letter-spacing: 0; margin-left: 7px; }
.pb-plate-slug { text-align: right; line-height: 1.4; }

/* the plate: full bleed, never a panel */
.pb-stage { position: relative; margin: 12px calc(-1 * var(--pb-gutter)) 0; background: none; border-radius: 0; overflow: visible; }
.pb-stage > svg { display: block; width: 100%; height: auto; }

/* a section opens with a double rule, heavy on top, then a slug and a two-voice head */
.pb-section { margin-top: 40px; padding-top: 12px; border-top: 3px solid var(--pb-rule); position: relative; }
.pb-section::before { content: ""; position: absolute; left: 0; right: 0; top: 2px; height: 0.75px; background: var(--pb-rule); }

/* key idea: type at scale and nothing else */
.pb-callout { margin: 0; padding: 0; background: none; border: 0; border-radius: 0; }
.pb-callout[data-kind="key"] { padding: 40px 0 0; }
.pb-callout[data-kind="key"] p { margin: 12px 0 0; font-family: var(--pb-display); font-size: 30px; font-weight: var(--pb-w-voice2); font-stretch: 100%; line-height: 1.06; letter-spacing: -0.012em; font-style: italic; text-wrap: balance; }

/* caveat: a footnote under a short rule. The dagger is typed in the text and in the note. */
.pb-callout[data-kind="caveat"] { margin-top: 16px; }
.pb-callout[data-kind="caveat"]::before { content: ""; display: block; width: 64px; height: 0.75px; background: var(--pb-rule); }
.pb-callout[data-kind="caveat"] .pb-callout-label { display: none; }
.pb-callout[data-kind="caveat"] p, .pb-callout[data-kind="analogy"] p, .pb-fig figcaption, .pb-note { margin: 10px 0 0; font-size: 15px; line-height: 1.4; font-style: italic; }

/* figures: a hairline, a head row (slug left, kind right), the drawing, a caption */
.pb-fig { margin: 40px 0 0; padding: 10px 0 0; background: none; border: 0; border-top: 0.75px solid var(--pb-rule); border-radius: 0; display: grid; grid-template-columns: 1fr auto; }
.pb-fig > * { grid-column: 1 / -1; }
.pb-fig::before { content: attr(data-slug); grid-column: 1; grid-row: 1; }
.pb-fig::after { grid-column: 2; grid-row: 1; text-align: right; white-space: nowrap; }
.pb-fig[data-kind="data"]::after { content: "Data, from the paper"; }
.pb-fig[data-kind="illustration"]::after { content: "Illustration, not to scale"; }
.pb-fig[data-kind="illustration"][data-scale="true"]::after { content: "Illustration, drawn to scale"; }
.pb-fig[data-kind="paper"]::after { content: "Figure from the paper"; }
.pb-fig.pb-bleed > svg, .pb-fig .pb-bleed { margin-left: calc(-1 * var(--pb-gutter)); margin-right: calc(-1 * var(--pb-gutter)); }
.pb-fig svg { display: block; max-width: none; }
.pb-fig-title { font-family: var(--pb-display); font-size: 30px; font-weight: var(--pb-w-voice1); font-stretch: 62.5%; line-height: 1; margin: 10px 0 14px; }
.pb-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; margin: 8px 0 0; }
.pb-legend span { display: inline-flex; align-items: center; gap: 6px; }
.pb-legend i { width: 7px; height: 7px; border-radius: 50%; background: var(--pb-accent); flex: none; }
.pb-legend svg { width: 22px; height: 10px; flex: none; }

/* stat: one number, what it is, then the figure that shows its range */
.pb-stats { display: block; margin: 10px 0 0; }
.pb-stat { display: flex; align-items: flex-end; gap: 10px; padding: 0; background: none; border: 0; border-radius: 0; }
.pb-stat-value, .pb-hero-number { font-size: 72px; line-height: 0.86; letter-spacing: var(--pb-ls-readout); }
.pb-stat-label { display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px; font-size: 15px; line-height: 1.3; font-style: italic; margin: 0; color: var(--pb-ink); }
.pb-stat-label b { font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; font-style: normal; }

/* "How sure is this?": a ledger. No dots, no tints, no status colors. */
.pb-confidence { display: block; margin: 12px 0 0; padding: 0; list-style: none; }
.pb-confidence li { display: grid; grid-template-columns: auto 1fr; column-gap: 16px; row-gap: 4px; align-items: baseline; padding: 11px 0 12px; background: none; border: 0; border-top: 0.75px solid var(--pb-rule); border-radius: 0; font-size: 15px; line-height: 1.4; font-style: italic; }
.pb-confidence li::before { content: none; }
.pb-confidence li b { font-style: normal; }
.pb-confidence li.pb-confidence-head { display: block; padding: 8px 0; font-size: var(--pb-fs-label); line-height: 1.3; font-style: normal; }
.pb-confidence .v { grid-column: 2; text-align: right; font-size: 30px; line-height: 1; font-style: normal; }
.pb-confidence .note { grid-column: 1 / -1; }
.pb-confidence li[data-kind="standing"] { font-size: 17px; line-height: 1.47; font-style: normal; }
.pb-confidence li[data-kind="standing"] b { grid-column: 1 / -1; }

/* source footer */
.pb-source { margin-top: 40px; padding-top: 12px; border-top: 3px solid var(--pb-rule); position: relative; font-size: 15px; line-height: 1.4; color: var(--pb-ink-2); }
.pb-source::before { content: ""; position: absolute; left: 0; right: 0; top: 2px; height: 0.75px; background: var(--pb-rule); }
.pb-source cite { display: block; margin-top: 8px; font-size: 17px; font-style: italic; color: var(--pb-ink); }
.pb-source small { display: block; margin-top: 6px; }
.pb-source .pb-note { color: var(--pb-ink); }

/* buttons: an ink slab, or a ruled outline. Square. */
.pb-btn { min-height: 48px; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; margin-top: 14px; border: 1px solid var(--pb-rule); border-radius: 0; background: none; color: var(--pb-ink); text-decoration: none; font-family: var(--pb-display); font-size: 23px; font-weight: 700; font-stretch: 75%; line-height: 1; letter-spacing: 0.005em; cursor: pointer; }
.pb-btn[data-kind="primary"] { background: var(--pb-slab); border-color: var(--pb-slab); color: var(--pb-on-slab); }

/* the slider: the carriage on the ruler is the handle */
.pb-slider input[type="range"] { -webkit-appearance: none; appearance: none; width: 100%; height: 44px; margin: 0; padding: 0; background: transparent; border-radius: 0; color: var(--pb-carriage); cursor: ew-resize; touch-action: pan-y; }
.pb-slider input[type="range"]::-webkit-slider-runnable-track { -webkit-appearance: none; background: transparent; height: 44px; }
.pb-slider input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 22px; margin-top: 11px; background: currentColor; border: 0; border-radius: 0; }
.pb-slider input[type="range"]::-moz-range-track { background: transparent; height: 44px; }
.pb-slider input[type="range"]::-moz-range-thumb { width: 12px; height: 22px; background: currentColor; border: 0; border-radius: 0; }

/* the live line, drawn by the kit into any svg */
.pb-live-trap { fill: none; stroke: var(--pb-page); stroke-width: var(--pb-live-trap); stroke-linejoin: round; stroke-linecap: round; }
.pb-live-halo-a { fill: none; stroke: var(--pb-accent); stroke-width: 17px; stroke-opacity: var(--pb-halo-a); stroke-linejoin: round; stroke-linecap: round; }
.pb-live-halo-b { fill: none; stroke: var(--pb-accent); stroke-width: 11px; stroke-opacity: var(--pb-halo-b); stroke-linejoin: round; stroke-linecap: round; }
.pb-live-halo-c { fill: none; stroke: var(--pb-accent); stroke-width: 6px; stroke-opacity: var(--pb-halo-c); stroke-linejoin: round; stroke-linecap: round; }
.pb-live-core { fill: none; stroke: var(--pb-accent); stroke-width: var(--pb-live-core); stroke-linejoin: round; stroke-linecap: round; }
.pb-pen-trap { fill: var(--pb-page); r: var(--pb-pen-trap); }
.pb-pen { fill: var(--pb-accent); r: var(--pb-pen); }
.pb-axis-line { fill: none; stroke: var(--pb-axis); stroke-width: 0.9px; }
.pb-grid-line { fill: none; stroke: var(--pb-grid); stroke-width: 0.6px; }
.pb-tick-label { font-family: var(--pb-mono); font-stretch: 75%; font-size: var(--pb-fs-label); font-weight: 500; letter-spacing: 0.06em; fill: var(--pb-ink-2); }
```

Notes on it:

- The kit's number helper `PB.fmt.sci` returns a typed × and Unicode superscripts. In a readout the design wants the drawn sign (`.pb-sign`) and a real `<sup>`.
- `.pb-fig::after` writes the kind slug from `data-kind`, as kit v1 does. A second attribute, `data-scale="true"`, says an illustration is drawn to scale. That attribute is new.
- The line-screen fill is an SVG `<pattern>` (`SYSTEM.md` 5.1): `width="40" height="3" patternTransform="rotate(-72)"` with one `<rect>` whose height sets the tone. Give the kit one helper that makes it, so authors never write a pattern by hand.

### 4.4 Charts

The kit draws charts with Observable Plot and d3 (`PB.plot`, `PB.svg`). The boards' charts are hand-built SVG. To get the same result from the kit, its chart defaults have to become these (`SYSTEM.md` section 4 has the full rules):

| Part | Value |
|---|---|
| Axis | One. A ruler: 0.9 px line in `--pb-axis`, ticks below it and outside the plot, 4 px minor and 7 px major, labels in `.pb-tick-label` with the baseline 20 px under the line, the unit once at the end. |
| Grid and drop lines | 0.6 px solid in `--pb-grid`, inside the plot. Never dashed. |
| Bars and bands | 16 to 20 px tall, 0.9 px outline in the text color. |
| The finding | The live mark: `--pb-accent`, solid, one per figure. A line with a pen point, a marker, or one segment. |
| Series 2 | `--pb-ink`, solid. |
| Series 3 | `--pb-plate`, solid. |
| An estimate or a range | A line screen in `--pb-screen`, mid tone (0.46 of the 3 px pitch), on angle −72. A second one in the same chart uses angle −12. Where the two overlap, both screens are drawn at the light tone (0.24). |
| A context shape | A line screen in `--pb-plate`, tone 0.30, with a 0.9 px outline. |
| A reported value on a range | 2 px line (1.9 px at night) on a ground-colored trap (7 px, or 6 px in the small bar), with a 3.6 px dot on top. |
| Labels | At the mark, horizontal, in the text color. Bar figures in D1 at 25 px. |
| Legend | Only for two or more kinds of mark, and never for a mark that has a direct label. |
| Limits | Four series at most. Solid means measured, screened means an estimate, a range, or a preprint. The live mark is always solid. |

Four charts are on the boards and are the reference for each form: the range bar (Fig. 2), the two-row bar chart on one ruler with a weave (Fig. 3), the beam on a time ruler (Fig. 1), and the played and unplayed line with a slider (Try it). A line chart with several series, a scatter, and a dumbbell are in `pipeline/AUTHORING.md` and are **not drawn in this round**.

### 4.5 The live line in a figure

Markup, in drawing order. Night differs only through the tokens.

```html
<path class="pb-live-trap pb-sweep" pathLength="1" d="..."/>
<path class="pb-live-halo-a pb-sweep" pathLength="1" d="..."/>
<path class="pb-live-halo-b pb-sweep" pathLength="1" d="..."/>
<path class="pb-live-halo-c pb-sweep" pathLength="1" d="..."/>
<path class="pb-live-core pb-sweep" pathLength="1" d="..."/>
<circle class="pb-pen-trap pb-travel" style="offset-path: path('...')"/>
<circle class="pb-pen pb-travel" style="offset-path: path('...')"/>
```

By day the three halo strokes have opacity 0. By night there are also three halo discs under the pen point (13 px at 0.05, 10 px at 0.14, 6.5 px at 0.09), which this stylesheet leaves out to stay short. The path is cubic curves with the amplitude baked in. Never scale a stroked path unevenly.

### 4.6 The hero and the card image

See section 3.6. For the page: the hero is a plate in the page's theme, so the reduced-motion capture and the card image should come from that plate at rest. The contract's `hero-not-capturable` rule (at least 300 px wide, not one flat color) still holds for it.

### 4.7 Where the design and the contract disagree

| Contract rule | The design | To settle |
|---|---|---|
| `small-text`: no text under 11 px | Labels are 10.5 px and tags are 10 px at phone width (11 and 10.5 on the desktop website) | Either set `--pb-fs-label` and `--pb-fs-tag` to 11 px in the kit, which costs half a pixel against the boards, or lower the check to 10. This is the owner's call (`SYSTEM.md` section 14). I would take 11 in the kit. |
| `small-control`: 40 px | Controls are 44 px and buttons 48 px | Nothing. The design is stricter. |
| `.pb-stage` is always dark, and `hero.webp` comes from the dark capture | A plate has day and night forms | Section 3.6. |
| Every data figure contains a table | No table is drawn | Section 4.2. Needs design. |

## 5. The website

Board: `Site.dc.html`. One page, day theme only. `site/index.html` is a stub today. Sections and copy are in `SYSTEM.md` 9.20. All copy on the board is from `CONTENT.md`.

### 5.1 Structure

```
header          wordmark (home link) · Source on GitHub · Download the APK · double rule
main
  section       hero: h1 · download slab, source button, note · Plate 1 bleeding right · readout, caption, paragraph, plate slug
  section       the feed: slug row · h2 · phone mock · five-row ledger of what a card does
  section       the explainer: slug · h2 · paragraph · excerpt (key idea, text with caveat, Fig. 1, Fig. 2, Fig. 3, ledger, source)
  section       how an explainer is made: slug row · h2 · figure of three plates on one live line · three agent sentences · "Every explainer" row
  section       download: slug · h2 · the same slab, button, and note
footer          wordmark at 150 px · Source row · Site row
```

The hero `section` has an `aria-label`. Each `section` after it has an `aria-labelledby` pointing at its `h2`. The phone mock is one `role="img"` with a full description, and its inner controls are `aria-hidden`, since they are a picture of the app and not controls.

### 5.2 Grid and breakpoints

The board drives its layout with custom properties set at these widths. Copy them from the board's helmet.

| Width | What changes |
|---|---|
| under 700 | One column, 20 px margins, 56 px between sections. Display `clamp(34px, 10.7vw, 64px)`. Hero order: headline, download slab, plate, readout, caption, paragraph, source button, note. Plate 230 px tall. Masthead links read "Source" and "Download". |
| 700 | Plate 284 px tall. Section heads 44 px. Full link labels. |
| 760 | 12 columns with a 24 px gutter. The feed section and the excerpt go to two columns of six. |
| 930 | Plate 318 px tall. |
| 1160 | Desktop: 56 px margins inside a 1200 px wrap, 96 px between sections, the desktop type scale (`SYSTEM.md` 2.4), hero headline and download block side by side, plate 354 px tall, excerpt in three columns of four. |

The hero plate is four drawings of Plate 1, one per height, and only one is shown at a time. In production that should be one drawing made at the viewport's width, or one wide SVG, not four copies.

The phone mock is a 390 px sheet shrunk with the CSS `zoom` property in steps (0.71 to 1). `zoom` was seen working only in the local Chromium. A production page should use a picture of the feed, or a `transform` with a sized wrapper.

Checked for overflow and for 44 px targets at 1440, 1160, 1024, 900, 768, 700, 390, and 360 wide. Looked at in full at 1440, 1024, 700, and 390. Between 700 and 1160 the layout holds but is loose: the feed section leaves an empty block above its ledger.

### 5.3 Links

| Link | Target on the board |
|---|---|
| Download the APK | `https://github.com/NtrpyDev/paperboy-app/releases` |
| Source on GitHub, and the footer's Source row | `https://github.com/NtrpyDev/paperboy-app` |
| The journal links and "Read the paper" in the excerpt | `#paper`, a placeholder. `CONTENT.md` gives no address for the paper. |
| Site row in the footer | `[YOUR DOMAIN]`, a visible placeholder. No domain is chosen. |

Hover: a text link goes to `#5A554B`, the slab's background goes to `#5A554B`. Focus: a 2 px outline in the text color, 2 px away. Both are in the board's helmet and were not captured in a render.

The website has no night theme. One was not asked for and not drawn.

## 6. Animation

Three verbs (Press, Register, Sweep), one loop (Pulse), and a few single-purpose moves. Nothing bounces or overshoots. The keyframes below are the boards' own, renamed with a `pb-` prefix and with colors as tokens. Three are restated: `pb-inkwipe` takes the wipe distance as a variable (the website's form), `pb-stamp` is split so the label and the icon step at 60 ms (the motion board's form), and `pb-feedup` takes its travel as a variable. The block was *rendered* in the test page, where Press, Ink wipe, Register, Sweep, Travel, Pulse, Drop, and the stamped state were seen. Feed up, Orbit, and the line through plates were not exercised there. `Motion.dc.html` shows each one as a looping cell with its timeline. That looping is the board's, not the product's: in the product each runs once.

```css
@keyframes pb-press { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
@keyframes pb-register-a { from { transform: translate(5px, -3px); } to { transform: none; } }
@keyframes pb-register-b { from { transform: translate(-5px, 3px); } to { transform: none; } }
@keyframes pb-inkwipe { from { clip-path: polygon(0 0, 0 0, calc(-1 * var(--pb-wipe-x)) 100%, 0 100%); } to { clip-path: polygon(0 0, calc(100% + var(--pb-wipe-x)) 0, 100% 100%, 0 100%); } }
@keyframes pb-sweep { from { stroke-dashoffset: 1.003; } to { stroke-dashoffset: 0; } }
@keyframes pb-travel { from { offset-distance: 0%; } to { offset-distance: 100%; } }
@keyframes pb-orbit { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes pb-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }
@keyframes pb-drop { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: none; } }
@keyframes pb-flood { from { opacity: 0; } to { opacity: 1; } }
@keyframes pb-stamp { 0% { transform: scale(1.1); background-color: transparent; border-color: var(--pb-rule); } 100% { transform: none; background-color: var(--pb-stamp); border-color: var(--pb-stamp); } }
@keyframes pb-stamp-ink { 0%, 50% { color: var(--pb-ink); } 50.01%, 100% { color: var(--pb-on-stamp); } }
@keyframes pb-stamp-old { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }
@keyframes pb-stamp-new { 0%, 50% { opacity: 0; } 50.01%, 100% { opacity: 1; } }
@keyframes pb-feedup { from { transform: translateY(0); } to { transform: translateY(calc(-1 * var(--pb-feedup))); } }
@keyframes pb-growx { from { transform: scaleX(0); } to { transform: none; } }
@keyframes pb-ridex { from { transform: translateX(-100%); } to { transform: none; } }

.pb-press { animation: pb-press 190ms cubic-bezier(0.2, 0, 0, 1) both; animation-delay: calc(var(--i, 0) * 50ms); }
.pb-inkwipe { animation: pb-inkwipe 520ms cubic-bezier(0.2, 0, 0, 1) 60ms both; }
.pb-register-a { animation: pb-register-a 480ms cubic-bezier(0.16, 1, 0.3, 1) 60ms both; }
.pb-register-b { animation: pb-register-b 480ms cubic-bezier(0.16, 1, 0.3, 1) 60ms both; }
.pb-sweep { stroke-dasharray: 1 1.5; animation: pb-sweep var(--pb-sweep-ms, 1900ms) linear 320ms both; }
.pb-travel { offset-distance: 100%; offset-rotate: 0deg; animation: pb-travel var(--pb-sweep-ms, 1900ms) linear 320ms both; }
.pb-travel.pb-pen { animation: pb-travel var(--pb-sweep-ms, 1900ms) linear 320ms both, pb-pulse 2400ms ease-in-out 2400ms infinite; }
.pb-orbit { animation: pb-orbit 1800ms linear 520ms both; }
.pb-drop { animation: pb-drop 260ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-flood { animation: pb-flood 260ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-rate { flex: 1 1 0; min-height: 44px; display: flex; align-items: center; justify-content: center; gap: 9px; padding: 0 12px; background: transparent; border: 1px solid var(--pb-rule); border-radius: 0; color: var(--pb-ink); font-family: var(--pb-font); font-size: 16px; font-weight: 500; line-height: 1; cursor: pointer; }
.pb-rate .ico { position: relative; display: inline-flex; width: 14px; height: 14px; }
.pb-rate .ico > * { position: absolute; left: 0; top: 0; }
.pb-rate .ico .on { opacity: 0; }
.pb-rate[aria-pressed="true"] { background: var(--pb-stamp); border-color: var(--pb-stamp); color: var(--pb-on-stamp); }
.pb-rate[aria-pressed="true"] .ico .off { opacity: 0; }
.pb-rate[aria-pressed="true"] .ico .on { opacity: 1; }
.pb-rate.is-stamping { animation: pb-stamp 120ms cubic-bezier(0.2, 0, 0, 1) both, pb-stamp-ink 120ms linear both; }
.pb-rate.is-stamping .ico .off { animation: pb-stamp-old 120ms linear both; }
.pb-rate.is-stamping .ico .on { animation: pb-stamp-new 120ms linear both; }
.pb-feedup { animation: pb-feedup 360ms cubic-bezier(0.2, 0, 0, 1) both; }
.pb-growx { transform-origin: 0 50%; animation: pb-growx 1600ms linear 900ms both; }
.pb-ridex { animation: pb-ridex 1600ms linear 900ms both; }

/* a figure below the first screen draws in once, when it scrolls into view */
.pb-wait .pb-sweep, .pb-wait .pb-travel, .pb-wait .pb-drop, .pb-wait .pb-flood, .pb-wait .pb-inkwipe, .pb-wait .pb-press { animation-play-state: paused; }

@media (prefers-reduced-motion: reduce) { .pb *, .pb *::before, .pb *::after { animation: none !important; } }
```

Two easings do all the work: `cubic-bezier(0.2, 0, 0, 1)` for type and ink landing, and `linear` for the instrument. Register alone uses `cubic-bezier(0.16, 1, 0.3, 1)`.

### 6.1 Press

- **What:** a line of type lands. Opacity 0 to 1 and a 6 px rise.
- **Timing:** 190 ms, `cubic-bezier(0.2, 0, 0, 1)`. Lines stagger 50 ms (`--i` is the line's index). Four steps at most.
- **Where:** headline lines on arrival. A chart label, as its mark arrives. The wordmark at app launch: "Paper", "boy", then the dot, 50 ms apart.
- **Still frame:** the text in place, fully opaque.

### 6.2 Ink wipe

- **What:** the plate's print layers are uncovered from the left along the 72 degree screen angle, by an animated `clip-path` polygon.
- **Timing:** 520 ms, delay 60 ms, `cubic-bezier(0.2, 0, 0, 1)`.
- **Set:** `--pb-wipe-x` to the plate's height divided by tan 72 degrees, in px. A 196 px band gives 63.7 px. A 122 px band gives 39.6 px.
- **Still frame:** the whole plate, no clip.

### 6.3 Register

- **What:** the blue layer starts 5 px right and 3 px up, the black layer 5 px left and 3 px down, and both slide into exact register.
- **Timing:** 480 ms, delay 60 ms, `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Still frame:** both layers in register.
- **Know this:** it runs under the ink wipe and ends fast. The layers are 2.1 px apart at 120 ms, when a quarter of the plate is uncovered, and 0.14 px apart at 300 ms (`design/scratch/final/register_probe.py`). So most of the move is hidden. If it should be seen, the wipe has to start later than the register, and that is a design change nobody has made.

### 6.4 Sweep and Travel

- **What:** the live line draws from start to end at constant speed. The pen point, its ground dot, its halo, and the carriage on the ruler follow the same path.
- **Timing:** 1900 ms for a hero (1400 to 2200 allowed, 600 to 900 for a short beam), delay 320 ms, `linear`. Set `--pb-sweep-ms`.
- **How:** every stroke of the line has `pathLength="1"` and `stroke-dasharray: 1 1.5`, and animates `stroke-dashoffset` from 1.003 to 0. Trap, halo, and core share the animation, or the halo shows as a ghost ahead of the line. The pen and carriage use `offset-path: path(...)` with the same path data and animate `offset-distance` from 0% to 100%. The carriage is a tall 9 px line on that path, clipped to the 8 px under the ruler.
- **Why 1.003:** the line trails the pen by that fraction of the path's length at the start. It must be above 1, or a round cap shows as a dot before the sweep. It must be small, or on a long path the pen visibly runs ahead: at 1.01 that gap was 19 px on the desktop hero. In Compose, drive the line's end and the pen from one progress value with `PathMeasure` and the problem does not exist.
- **Still frame:** the line fully drawn, the pen point parked at the end, the carriage under it. The inline `offset-distance: 100%` is that frame, so with the animation removed nothing is missing.
- **Ring form (Orbit):** for a circle as the live line (Plate 3), the circle sweeps from 12 o'clock and the pen point sits on a group that rotates 360 degrees. 1800 ms, delay 520 ms, `linear`. Still frame: the full ring with the pen point at 12 o'clock.

### 6.5 Pulse

- **What:** after the sweep the pen point breathes, opacity 1 to 0.55 and back.
- **Timing:** 2400 ms, `ease-in-out`, infinite, starting at 2400 ms.
- **Rule:** the only loop on a screen, and only on the pen point of the one live line in view. The wordmark dot never pulses.
- **Still frame:** the pen point at full opacity.

### 6.6 Drop and Flood

- **Drop:** a marker falls 12 px onto its band while it fades in (the 410 marker). 260 ms, `cubic-bezier(0.2, 0, 0, 1)`.
- **Flood:** a solid live mark fades in where it stands (the "3" segment, the arm-change mark). 260 ms, same easing.
- **When:** once, when the figure scrolls into view. Put `.pb-wait` on the figure, which holds its draw-ins at their first frame, and remove it when the figure is on screen. The kit already uses an `IntersectionObserver` for `.pb-reveal`, and the same observer can do this. That wiring was not built or tested here. The artboards stand in for it with fixed delays from 2280 to 4950 ms.
- **Still frame:** the mark in place, fully opaque.

In an explainer every figure has exactly one draw-in, on its one live mark: Fig. 1 the 7 ms beam sweeps (900 ms) after its field inks in, Fig. 2 the marker drops, Fig. 3 the segment floods, For scale the mark floods, Try it the plate inks in.

### 6.7 Stamp

- **What:** a rating tap. The whole button jumps to scale 1.1 and settles to 1 while its fill floods the whole surface at once. The label color and the icon (plus to check) change in one step at 60 ms, so the words are readable in every frame.
- **Timing:** 120 ms, `cubic-bezier(0.2, 0, 0, 1)`, on the tap.
- **How:** set `aria-pressed="true"` and add `.is-stamping` for the 120 ms. The resting stamped state is in the `[aria-pressed="true"]` rules, so it does not depend on the animation.
- **Never:** a directional wipe. A fill that comes in from one edge passes through a button with a filled left edge, which is the form the owner banned. The first motion board did that and was changed.
- **Still frame:** the stamped button: muted fill, check, label in the ground color.
- **Note:** the night feed board cross-fades the icon across the 120 ms instead of stepping it at 60. Build the step. The app also removes a card 700 ms after "Less like this" (`FeedModel.kt`). How the card leaves was not designed.

### 6.8 Feed up

- **What:** feed to explainer. The plate, its readout row, and the summary stay exactly where they are. The sheet under them (the buttons) slides up by its own height and the explainer's next block (the key idea) arrives in its place.
- **Timing:** 360 ms, `cubic-bezier(0.2, 0, 0, 1)`. Half the distance is covered very early: the board's middle frame, at 180 ms, is 88 percent up.
- **How on the web:** `.pb-feedup` on the moving sheet with `--pb-feedup` set to its travel in px. In the app this is a transition between two screens that share the plate. The navigation library's support for that was not checked.
- **Also changes, not shown on the board:** the masthead becomes the explainer top bar. The board's three frames start under the masthead.
- **Still frame:** the explainer at rest.

### 6.9 Loading

- **What:** no spinner. A slug "Loading new papers", a muted label "No signal yet", and one flat live line that sweeps across the sheet (1900 ms, `linear`, delay 320 ms), after which its pen point pulses until the first card replaces it.
- **Still frame:** the full flat line with the pen point at its right end.

### 6.10 Line through plates (website only)

- **What:** in "How an explainer is made" one live line grows from left to right through the three plates with its pen point riding the end.
- **Timing:** 1600 ms, delay 900 ms, `linear`. `.pb-growx` on the line (and its trap), `.pb-ridex` on a full-width holder whose right end carries the pen point.
- **Still frame:** the full line with the pen point at the right end.

### 6.11 Reduced motion

One rule removes every animation, and every element's own style is already its resting frame, so the page is complete. All seven boards were rendered with `prefers-reduced-motion: reduce`: zero running animations, and each still was looked at (`design/shots/final/reduced/`). The contract's check captures the same stills (`shots/still-*.png`).

Order on arrival, for a card or an explainer's first screen: headline readable by 200 ms, plate inked by 580 ms, sweep from 320 to 2220 ms, at rest by 2.6 s, then only the pulse.

## 7. Brand assets

Board: `Brand.dc.html`. Nothing on it is exported as a file yet.

- **Wordmark:** text, not an image, wherever the fonts are loaded: "Paper" in D1, "boy" in D4, then a dot of the live color on the baseline. Sizes, dot sizes, gaps, clear space, and the one-color and night versions are in `SYSTEM.md` 9.21.
- **App icon:** two masters on a 512 grid, a large one for sizes above 96 px and a small one for 96 px and under and for launchers. The generator is `design/scratch/brandmotion/bm.py` (`app_icon()`, `icon_layers()`).
- **Launcher:** an Android adaptive icon from the small master in three layers: background (the ground and the rings), foreground (the P and the pen point), monochrome (the P and the pen point in one color). *Docs* (developer.android.com/develop/ui/views/launch/icon_design_adaptive): "Size all layers to 108x108 dp", the logo is at least 48x48 dp and "must not exceed 66x66 dp, because the inner 66x66 dp of the icon appears within the masked viewport", the outer 18 dp on each side is reserved for masking, and the file is `res/mipmap-anydpi-v26/ic_launcher.xml` with `<background>`, `<foreground>`, and `<monochrome>`. The board draws the layers to those sizes.
- **To do:** export the three layers as vector drawables and the two masters as PNG or SVG. Not done in this round.

## 8. Decisions that are still open

For the owner:

1. The theme button in the feed masthead: keep it, or follow the phone's setting.
2. The masthead strap "Science and math, newly released".
3. A rating row at the end of the explainer. Suggested by the critique, not added.
4. `minSdk` 24 with static font files, or `minSdk` 26 with the variable files only (section 1.3).
5. Label text at 10.5 px against the contract's 11 px floor (section 4.7).

For the build team:

6. How a card gets its plate: two stills, or stills plus path data (section 3.6).
7. The new card data: the marked second voice, the readout, the plate's kind (section 3.5).
8. Whether this lands as a new kit version.

Needs a design pass before it can be built in this language:

9. Scroll steps, the segmented toggle, glossary terms and their popover, the chart tooltip, the data table, and math (section 4.2).
10. Line charts with several series, scatters, and dumbbells (section 4.4).
11. The undo snackbar, the refresh message, the two failure states, and how a card leaves after "Less like this" (sections 3.1 and 6.7).
12. A desktop explainer. The website's excerpt shows the parts at desktop width, but no full explainer page was drawn wider than 390.
13. A night website, if one is wanted.
