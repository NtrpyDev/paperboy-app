# Third-party notices

Paperboy's code is released under the GNU General Public License, version 3 or later (see `LICENSE`). This repository and the app bundle the following third-party work, each under its own license.

## Explainer kit

Vendored in `kit/v1/vendor/`. Each license text is in `kit/v1/vendor/licenses/`.

| Work | Version | License | License text |
|---|---|---|---|
| D3 | 7.9.2 | ISC | `kit/v1/vendor/licenses/d3-LICENSE` |
| Observable Plot | 0.6.19 | ISC | `kit/v1/vendor/licenses/plot-LICENSE` |
| KaTeX, including its fonts in `kit/v1/vendor/katex/fonts/` | 0.19.1 | MIT | `kit/v1/vendor/licenses/katex-LICENSE` |

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

## Explainer content

The explainers the pipeline produces are published separately under the Creative Commons Attribution 4.0 International license (CC BY 4.0), not under this repository's license.
