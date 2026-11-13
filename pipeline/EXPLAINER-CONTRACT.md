# Explainer contract

Every explainer must follow these rules. `paperboy-pipeline check` enforces them and names the broken rule in `check.json` by the id in brackets. `kit/v1/gallery.html` follows every rule except `hero-without-kind`, which is newer than kit v1.

## The document

- One HTML document, `index.html`.
- Load the kit by absolute path: every stylesheet and every script with a `src` comes from `/kit/v<N>/...` for one kit version N, including `/kit/v<N>/paperboy.css` and `/kit/v<N>/paperboy.js`. Every kit file on a page comes from the same version. [`kit-not-absolute`]
- Declare both color schemes: `<meta name="color-scheme" content="dark light">`. [`missing-color-scheme`]
- Include a viewport meta: `<meta name="viewport" content="width=device-width, initial-scale=1">`. [`missing-viewport`]
- Put all page code inside `PB.ready(function () { ... })`. Each inline script must be one `PB.ready(...)` call. [`code-outside-ready`]

## The structure

- The root is `<article class="pb">`. [`missing-root`]
- First, the hero: `.pb-hero` holding a `.pb-title`, a `.pb-dek`, and exactly one `.pb-stage` with the hero visual. [`hero-incomplete`]
- The hero's `.pb-stage` has `data-kind` set to `data` (it plots the paper's numbers) or `illustration`. An illustration drawn to scale also has `data-scale="true"`. [`hero-without-kind`]
- Then five sections marked with `data-section`, each exactly once, in this order: `question`, `method`, `findings`, `confidence`, `matters`. Other sections may sit between them. [`missing-section`, `duplicate-section`, `section-order`]
- Last, a `.pb-source` footer [`missing-source`] with a link to the paper [`missing-source-link`] and the words "machine written" [`missing-source-note`].

## Figures

- Every `figure` has `data-kind` set to `data`, `illustration`, or `paper`. [`figure-without-kind`]
- Every `figure[data-kind="data"]` contains a `table` of its numbers (`PB.table` makes one). [`data-figure-without-table`]
- Every `figure[data-kind="paper"]` has a credit line, `.pb-credit`. [`paper-figure-without-credit`]

## In the browser

The check loads the page at 390 by 844 px four times: in light, in dark, and with reduced motion in light and in dark.

- The kit sets `data-pb-ready="1"` on `<html>` within 20 seconds. [`not-ready`]
- No script errors, including errors the kit caught inside `PB.ready`. [`script-error`]
- No requests to any host other than the one serving the page: no CDNs, fonts, images, or data from elsewhere. [`external-request`]
- No horizontal overflow at 390 px wide. Wide content must sit inside a container that scrolls or clips it. [`overflow-x`]
- No text smaller than 11 px computed size. [`small-text`]
- Buttons, range inputs, and `.pb-btn` links are at least 40 px in their smaller dimension. [`small-control`]
- The hero stage can be captured as the card's plate, at rest (reduced motion) in light and in dark: at least 300 px wide, not empty, and neither screenshot is a single flat color. [`hero-not-capturable`]
- With reduced motion on, every animation shows a still frame that reads correctly on its own. The check captures these frames (`shots/still-*.png`, light and dark) and the checker agent judges them; no rule id.
