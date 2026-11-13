# Third-party notices

Paperboy's code is released under the GNU General Public License, version 3 or later (see `LICENSE`). This repository and the app bundle the following third-party work, each under its own license.

## Explainer kit

Vendored in `kit/v1/vendor/`. Each license text is in `kit/v1/vendor/licenses/`.

| Work | Version | License | License text |
|---|---|---|---|
| D3 | 7.9.2 | ISC | `kit/v1/vendor/licenses/d3-LICENSE` |
| Observable Plot | 0.6.19 | ISC | `kit/v1/vendor/licenses/plot-LICENSE` |
| KaTeX, including its fonts in `kit/v1/vendor/katex/fonts/` | 0.19.1 | MIT | `kit/v1/vendor/licenses/katex-LICENSE` |

## Fonts

In `kit/v2/fonts/`, as served by Google Fonts and unchanged. Each license text is beside the font files.

| Family | License | License text |
|---|---|---|
| Noto Serif Display | SIL Open Font License 1.1 | `kit/v2/fonts/OFL-notoserifdisplay.txt` |
| Source Serif 4 | SIL Open Font License 1.1 | `kit/v2/fonts/OFL-sourceserif4.txt` |
| Martian Mono | SIL Open Font License 1.1 | `kit/v2/fonts/OFL-martianmono.txt` |

## Android app

Libraries declared in `gradle/libs.versions.toml` and bundled into the APK:

| Library | Version | License |
|---|---|---|
| Kotlin standard library (`org.jetbrains.kotlin:kotlin-stdlib`) | 2.4.21 | Apache License 2.0 |
| Jetpack Compose UI (`androidx.compose.ui:ui`, `ui-tooling-preview`), from Compose BOM 2026.09.00 | 1.12.1 | Apache License 2.0 |
| Compose Material 3 (`androidx.compose.material3:material3`), from Compose BOM 2026.09.00 | 1.4.0 | Apache License 2.0 |
| Activity Compose (`androidx.activity:activity-compose`) | 1.13.0 | Apache License 2.0 |
| Lifecycle (`androidx.lifecycle:lifecycle-viewmodel-compose`, `lifecycle-runtime-compose`) | 2.11.0 | Apache License 2.0 |
| Navigation 3 (`androidx.navigation3:navigation3-runtime`, `navigation3-ui`) | 1.2.1 | Apache License 2.0 |
| AndroidX WebKit (`androidx.webkit:webkit`) | 1.18.0 | Apache License 2.0 |
| OkHttp (`com.squareup.okhttp3:okhttp`) | 5.5.1 | Apache License 2.0 |
| kotlinx.serialization JSON (`org.jetbrains.kotlinx:kotlinx-serialization-json`) | 1.13.0 | Apache License 2.0 |
| kotlinx.coroutines (`org.jetbrains.kotlinx:kotlinx-coroutines-android`) | 1.11.0 | Apache License 2.0 |
| Coil (`io.coil-kt.coil3:coil-compose`, `coil-network-okhttp`) | 3.6.3 | Apache License 2.0 |

Their transitive dependencies in the release APK also declare the Apache License 2.0 in their published POM files.

Fonts bundled in the APK, in `app/src/main/res/font/`: the variable font files from github.com/google/fonts (`ofl/notoserifdisplay`, `ofl/sourceserif4`, `ofl/martianmono`), unchanged except for their file names, which Android resource names require. Each family's license text is in `app/src/main/res/raw/`, and the About screen shows it.

| Family | Files | License | License text |
|---|---|---|---|
| Noto Serif Display | `notoserifdisplay_variable.ttf`, `notoserifdisplay_italic_variable.ttf` | SIL Open Font License 1.1 | `app/src/main/res/raw/ofl_notoserifdisplay.txt` |
| Source Serif 4 | `sourceserif4_variable.ttf`, `sourceserif4_italic_variable.ttf` | SIL Open Font License 1.1 | `app/src/main/res/raw/ofl_sourceserif4.txt` |
| Martian Mono | `martianmono_variable.ttf` | SIL Open Font License 1.1 | `app/src/main/res/raw/ofl_martianmono.txt` |

## Explainer content

The explainers the pipeline produces are published separately under the Creative Commons Attribution 4.0 International license (CC BY 4.0), not under this repository's license.
