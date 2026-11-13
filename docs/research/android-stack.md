# Android stack research for Paperboy

Researched 2026-11-12 against primary sources only. Every claim carries its source URL. Items a primary source did not answer are marked NOT FOUND and collected at the end. Version numbers are the stable releases listed on the cited pages on 2026-11-12.

Local facts were read from this machine, not the web: `~/Android/Sdk` holds `platforms/android-36`, `build-tools/36.0.0`, cmdline-tools `Pkg.Revision=22.0`, emulator `Pkg.Revision=37.2.12`, one old system image (`android-28/android-tv/x86`), and `java` is not on PATH (source: `~/Android/Sdk/*/source.properties`, `which java`).

---

## 1. Current stable versions and compatibility

### 1.1 Android Gradle Plugin (AGP)

- Latest stable line is AGP 9.5; the release notes list 9.5.0 and 9.5.1. "The maximum API level that Android Gradle plugin 9.5 supports is API level 37." Compatibility table for 9.5: Gradle minimum 9.6.0, default 9.6.0; SDK Build Tools 36.0.0; JDK minimum 17, default 17. Source: https://developer.android.com/build/releases/gradle-plugin
- AGP 9.3 (patches 9.3.0, 9.3.1, 9.3.2, 9.3.3): max API level 37; Gradle minimum 9.5.0; Build Tools 36.0.0; JDK minimum 17, default 17. Source: https://developer.android.com/build/releases/agp-9-3-0-release-notes
- AGP 9.4 (9.4.0): max API level 37; Gradle minimum 9.6.0; JDK 17. Source: https://developer.android.com/build/releases/agp-9-4-0-release-notes
- AGP to minimum Gradle table: 9.5 needs 9.6.0, 9.4 needs 9.6.0, 9.3 needs 9.5.0, 9.2 needs 9.4.1, 9.1 needs 9.3.1, 9.0 needs 9.1.0. Minimum tools per API level: API 37.0 needs AGP 9.1.1; API 36 needs AGP 8.9.1. Android Studio Rabbit 2 (2026.2.2) supports AGP 7.1 to 9.5. Source: https://developer.android.com/build/releases/about-agp
- Built-in Kotlin: "Android Gradle plugin 9.0 introduces built-in Kotlin support and enables it" by default; you remove the `org.jetbrains.kotlin.android` plugin. AGP 9.0 "has a runtime dependency on Kotlin Gradle plugin (KGP) 2.2.10", and to use a higher KGP you add `classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:KGP_VERSION")` to the top-level buildscript. Sources: https://developer.android.com/build/releases/agp-9-0-0-release-notes and https://developer.android.com/build/migrate-to-built-in-kotlin
- AGP 9.0 also flipped `android.newDsl` and `android.builtInKotlin` defaults to `true`. Source: https://developer.android.com/build/releases/agp-9-0-0-release-notes

### 1.2 Gradle

- The current Gradle user guide is for Gradle 9.9.1. "A JVM version between 17 and 27 is required to execute Gradle. JVM 28 and later versions are not yet supported." Running Gradle on Java 21 is supported from 8.5, Java 25 from 9.1.0, Java 26 from 9.4.0, Java 27 from 9.8.0. Source: https://docs.gradle.org/current/userguide/compatibility.html
- Consequence (derived from the line above): JDK 27 (`jdk-openjdk` on Arch) cannot run Gradle 9.5.0 or 9.6.0, the versions AGP 9.3 to 9.5 require, because Java 27 support starts at Gradle 9.8.0.

### 1.3 JDK

- AGP 9.3, 9.4 and 9.5 all list JDK minimum 17, default 17 (sources in 1.1).
- "The toolchain defaults to the JDK used to run Gradle", and specifying a toolchain gives more consistent builds across machines. Source: https://developer.android.com/build/jdks
- Install: `jdk17-openjdk`. It is the version AGP names as both minimum and default, and Gradle runs on it. `jdk21-openjdk` is also inside every documented range. Do not use `jdk-openjdk` (27) with Gradle below 9.8.0.

### 1.4 Kotlin

- Latest stable Kotlin is 2.4.21, released October 8, 2026 (bug fix release for 2.4.20 of September 7, 2026). Next planned: 2.5.0 in December 2026. Source: https://kotlinlang.org/docs/releases.html
- JetBrains' KGP compatibility table: KGP 2.4.20 to 2.4.21 supports Gradle 7.6.3 to 9.7.0 and AGP 8.5.2 to 9.3.1. KGP 2.4.0 to 2.4.10 supports Gradle 7.6.3 to 9.5.0 and AGP 8.5.2 to 9.1.0. Source: https://kotlinlang.org/docs/gradle-configure-project.html
- Conflict between vendors: Google's AGP page shows AGP 9.5.0 next to Kotlin 2.4.10 in its example (https://developer.android.com/build/releases/about-agp), while JetBrains lists AGP 9.1.0 as the maximum for KGP 2.4.10 and 9.3.1 as the maximum for 2.4.21 (https://kotlinlang.org/docs/gradle-configure-project.html). No published matrix covers Kotlin 2.4.x with AGP 9.4 or 9.5.

### 1.5 Compose compiler plugin

- "As of Kotlin 2.0, the Compose compiler is managed alongside the Kotlin compiler and uses the same version as the Kotlin compiler." Source: https://developer.android.com/develop/ui/compose/bom
- Plugin id `org.jetbrains.kotlin.plugin.compose`, version equal to the Kotlin version; catalog entry `compose-compiler = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }`; also set `buildFeatures { compose = true }`. Source: https://developer.android.com/develop/ui/compose/compiler

### 1.6 Compose BOM

- Latest stable BOM: `androidx.compose:compose-bom:2026.09.00`. Source: https://developer.android.com/develop/ui/compose/bom and https://developer.android.com/develop/ui/compose/compiler ("Always use the latest Compose BOM version: 2026.09.00").
- Stable Compose libraries listed on the AndroidX table: compose.ui, foundation, runtime, animation, material 1.12.1; material3 1.4.0. Source: https://developer.android.com/jetpack/androidx/versions
- Compose 1.12 requirement: "Updated Compose `compileSdk` to API 37. This means that a minimum AGP version of 9.2.0 is required when using Compose." Source: https://developer.android.com/jetpack/androidx/releases/compose-ui . Also: "starting with Compose 1.12.0, projects are required to use `compileSdk 37` and Android Gradle Plugin (AGP) 9." Source: https://developer.android.com/develop/ui/compose/compiler
- Next: Compose 1.13.0-rc01 moves Compose `compileSdk` to 37.1. Source: https://developer.android.com/jetpack/androidx/releases/compose-ui

### 1.7 compileSdk and targetSdk

- Android 17 is API level 37. "Android 17 has officially reached Platform Stability with Beta 3. The API surface is now locked" (March 2026). Source: https://developer.android.com/about/versions/17/release-notes
- The SDK repository manifest (stable channel) lists `platforms;android-37.0` revision 2, `platforms;android-37.1`, `platforms;android-37.2`, `platforms;android-36` revision 2, `platforms;android-36.1`, `build-tools;37.0.0`, `build-tools;36.1.0`, `cmdline-tools;latest` 23.0, `platform-tools` 37.0.1, `emulator` 37.2.13. Source: https://dl.google.com/android/repository/repository2-3.xml
- Because the Compose BOM needs `compileSdk 37` (1.6), the installed `platforms/android-36` alone is not enough; `platforms;android-37.0` must be added.
- Android 17 behavior example for apps targeting API 37: on large screens (sw >= 600dp) apps "can no longer opt-out of resizing or orientation changes." Source: https://developer.android.com/about/versions/17/release-notes

### 1.8 Known-compatible set

The only combination inside every vendor's published matrix:

| Component | Version | Why |
|---|---|---|
| JDK | 17 | AGP minimum and default (1.1) |
| Gradle | 9.5.0 | AGP 9.3 minimum and default; inside KGP 2.4.21 max 9.7.0 (1.1, 1.4) |
| AGP | 9.3.1 | Supports API 37; satisfies Compose's AGP 9.2.0 floor; at JetBrains' stated max for KGP 2.4.21 (1.1, 1.4, 1.6) |
| Kotlin (KGP, Compose compiler, serialization plugin) | 2.4.21 | Latest stable; documented for AGP up to 9.3.1 (1.4) |
| Compose BOM | 2026.09.00 | Latest stable (1.6) |
| compileSdk | 37 | Required by Compose 1.12 (1.6) |
| Build Tools | 36.0.0 (installed) | AGP 9.3 default (1.1) |

Alternative: AGP 9.5.1 with Gradle 9.6.0 is newer and is what Google's own pages show, but Kotlin 2.4.21 is not listed by JetBrains as supporting it (1.4).

---

## 2. Google Play target API level and minSdk

- In force now: "Starting August 31 2026: New apps and app updates must target Android 16 (API level 36) or higher to be submitted to Google Play" (Wear OS and Automotive: 35; TV and XR: 34). "Existing apps must target Android 15 (API level 35) or higher to remain available to new users" on newer devices. Extension available "to November 1, 2026". Sources: https://developer.android.com/google/play/requirements/target-sdk and https://support.google.com/googleplay/android-developer/answer/11926878
- Next announced deadline: NOT FOUND. Neither page mentions a requirement beyond November 1, 2026 or an Android 17 target date.
- minSdk: "AndroidX libraries have the default `minSdk` of 24 ... The default `minSdk` is meant to cover 99% of Android users based on the Google Play Store check-in information, as is shown in Android Studio's New Project wizard. The default value is updated at a yearly cadence." Source: https://developer.android.com/jetpack/androidx/versions
- Per-library floors seen: Hilt minSDK 23 (https://github.com/google/dagger/releases/tag/dagger-2.60), Coil Android minimum SDK 23 since 3.5.0 (https://github.com/coil-kt/coil/blob/main/CHANGELOG.md), Paging default minSdk moved 21 to 23 (https://developer.android.com/jetpack/androidx/releases/paging).
- Per-API-level percentage table: NOT FOUND on the web. The data is shown inside Android Studio's New Project wizard ("Help me choose"), per https://developer.android.com/jetpack/androidx/versions .

---

## 3. Google Play account and Android developer verification

### 3.1 New personal Play developer account

- Fee: "There is a US$25 one-time registration fee." Source: https://support.google.com/googleplay/android-developer/answer/6112435
- Identity: "you may be asked for a valid government ID and a credit card, both under your legal name"; "personal account owners must verify access to an Android device using the Play Console mobile app"; "If this information is determined to be invalid, your registration fee will not be refunded." Source: https://support.google.com/googleplay/android-developer/answer/6112435
- Verification page: personal accounts without a verified payments profile provide an "Official government identity document"; "you will be asked to link a Google Payments profile"; "New personal accounts will be required to verify that they have access to a real Android mobile device"; email is verified with a 6-digit code. Source: https://support.google.com/googleplay/android-developer/answer/10841920
- Whether a personal account's home address is shown publicly on Play: NOT FOUND (the page says legal name and address are taken from the payments profile but does not state public display for personal accounts).
- Closed testing before production: applies to "personal developer accounts created after November 13, 2023"; you must "run a closed test for their app with a minimum of 12 testers who have been opted in continuously for at least 14 days"; then in Play Console "Open the Dashboard" and "Click Apply for production." Source: https://support.google.com/googleplay/android-developer/answer/14151465
- Format: "Starting August 2021, new apps are required to publish with the Android App Bundle on Google Play." Source: https://support.google.com/googleplay/android-developer/answer/9844279

### 3.2 Android developer verification (apps outside Play, including GitHub APKs)

Program page: https://developer.android.com/developer-verification . Guide: https://developer.android.com/developer-verification/guides . FAQ: https://developer.android.com/developer-verification/guides/faq

- Scope: "Android requires all apps to be registered by verified developers for users to install them on certified Android devices." If your app runs on a certified device "these requirements apply to you, regardless of your app's download source." Source: guides page.
- Timeline: August 2026 "Developer APIs, limited distribution accounts, and power user advanced flow launch." September 30, 2026 "Protections begin for all users who install apps from participating stores in Brazil, Indonesia, Singapore, and Thailand on certified devices running Android 7+." 2027: "Verification capability will be expanded globally for all apps on certified Android devices in 2027." Source: program page.
- Participating stores for September 30, 2026: Google Play, HONOR App Market, OPPO App Market, Samsung Galaxy Store, Transsion Palm Store, vivo V-Appstore, Xiaomi GetApps. Source: guides page.
- Sideloaded APKs today: "If you distribute your app through other stores, or if users sideload your app directly, these new verification requirements won't apply to your app yet ... we still recommend that you plan to complete your verification before the global rollout begins in 2027." (last updated July 15, 2026). Source: FAQ.
- Account types: Full distribution (identity verification required; distribute from any channel), Limited distribution (no ID; up to 20 devices; for students, hobbyists, personal use), and sideloading unregistered apps (users must use the advanced flow). Source: guides page.
- Fee outside Play: "The $25 fee for the Full Distribution account in the ADC ... similar to Play's $25 registration fee"; waived for Limited Distribution. Source: FAQ.
- Play developers: "developers with a Play Console account can use it as the single place to manage all their verification requirements, including for their apps distributed outside of Play." Apps using Play App Signing are claimed automatically. Source: FAQ.
- Steps: sign up for the Android Developer Console (if outside Play), verify identity, then "Register your package names: Prove ownership of your apps by providing the APK signed with your private key". Source: guides page.
- ADB: "As a developer, you are free to install apps without verification with ADB." Source: FAQ.
- Advanced flow for users installing unverified apps: enable developer mode, confirm no one is coaching you, restart and reauthenticate, wait a one-time one-day period, confirm with biometrics or PIN, then install "with the option of enabling for 7 days or indefinitely"; the user still sees an unverified-developer warning. "Unregistered apps can only be installed or updated when the advanced flow is enabled or by using ADB". Source: FAQ.
- Lost key: "If you lose your signing key you won't be able to register your packages." Source: FAQ.
- Open source repositories (for example F-Droid) that re-sign an app: register the package name and add the repository key's SHA-256 fingerprint; for existing apps re-signed by the registry, add an `adi-registration.properties` snippet to `assets` and publish that version. Source: https://developer.android.com/developer-verification/guides/open-source-app-registration

---

## 4. Rendering remote HTML explainers in a WebView

### 4.1 Compose integration

- "To use a `WebView` in Jetpack Compose, you must wrap it in an `AndroidView`." Google warns: "If you have complex use cases for `WebView`, we recommend not migrating that layout to use Compose until the Compose `WebView` equivalent is available" (issue 329866164). Source: https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/wrap-webview-in-compose
- Lifecycle: WebView "is **not recommended**" to outlive the Activity; persist history with `saveState`/`restoreState` and a `rememberSaveable` Bundle in `onRelease`; "failing to clean up and destroy `WebView` instances when leaving the composition causes cumulative `Activity` and native memory leaks." Same source. "You must explicitly remove the `WebView` from its parent `ViewGroup` and invoke `destroy()` when the view is no longer needed." Source: https://developer.android.com/develop/ui/views/layout/webapps/webview
- Back navigation: use Compose `BackHandler` and `canGoBack()`/`goBack()`. Source: compose wrap page above.
- Official Compose WebView: none stable. `androidx.web:web:1.0.0-alpha01` (November 4, 2026) adds `WebContent`, `WebContentView` and `DetachedWebContentView`; it is alpha and its notes do not describe a composable. Source: https://developer.android.com/jetpack/androidx/releases/web
- Jetpack Webkit latest stable: `androidx.webkit` 1.18.0. Source: https://developer.android.com/jetpack/androidx/versions

### 4.2 Settings: JavaScript on, everything else locked down

- JavaScript: "JavaScript is disabled in a `WebView` by default"; enable with `settings.javaScriptEnabled = true`. Source: https://developer.android.com/develop/ui/views/layout/webapps/webview
- File access defaults: `setAllowFileAccess()` is "`TRUE` in API level 29 and lower, and `FALSE` in API level 30 and higher"; `setAllowFileAccessFromFileURLs()` and `setAllowUniversalAccessFromFileURLs()` default to false from API 16; Google's sample explicitly sets all of `allowFileAccessFromFileURLs`, `allowUniversalAccessFromFileURLs`, `allowFileAccess`, `allowContentAccess` to `false`. Source: https://developer.android.com/privacy-and-security/risks/webview-unsafe-file-inclusion
- Content access: `setAllowContentAccess` "The default is enabled." Source: https://developer.android.com/reference/android/webkit/WebSettings
- Mixed content: "Apps targeting `Build.VERSION_CODES#LOLLIPOP` default to `MIXED_CONTENT_NEVER_ALLOW`. The preferred and most secure mode ... is `MIXED_CONTENT_NEVER_ALLOW`". Source: https://developer.android.com/reference/android/webkit/WebSettings
- Other defaults from the same reference: DOM storage default `false`; Geolocation default `true`; `setJavaScriptCanOpenWindowsAutomatically` default `false`. Source: https://developer.android.com/reference/android/webkit/WebSettings
- Popups: "pass `"true"` into `setSupportMultipleWindows` but not override the `onCreateWindow` method"; this prevents `target="_blank"` links from loading. Source: https://developer.android.com/develop/ui/views/layout/webapps/webview
- JS bridge: "don't use `addJavascriptInterface()` unless you wrote all of the HTML and JavaScript that appears in your `WebView`. Don't let the user navigate within your `WebView` to web pages that aren't your own." Source: https://developer.android.com/develop/ui/views/layout/webapps/webview
- Navigation to other origins: override `shouldOverrideUrlLoading`; return `false` for your host and launch an `ACTION_VIEW` Intent for anything else. Source: https://developer.android.com/develop/ui/views/layout/webapps/webview . Validate both scheme and full host, for example `uri.scheme == "https" && uri.host == trustedHostName`; do not use `startsWith`/`endsWith`/regex for host checks. Source: https://developer.android.com/privacy-and-security/risks/unsafe-uri-loading
- Cleartext: block HTTP via `android:usesCleartextTraffic="false"` or a Network Security Config. Source: https://developer.android.com/privacy-and-security/risks/webview-unsafe-file-inclusion . Android 17 notes say `usesCleartextTraffic` will be deprecated in a future SDK and apps will default to blocking cleartext. Source: https://developer.android.com/about/versions/17/release-notes
- Manifest needs `android.permission.INTERNET`. Source: https://developer.android.com/develop/ui/views/layout/webapps/webview
- Safe Browsing default: NOT FOUND in the WebSettings reference excerpt read.

### 4.3 Loading a downloaded HTML string or cached file with an https origin

- `loadDataWithBaseURL(baseUrl, html, "text/html", null, baseUrl)`: "baseUrl ... This must be an HTTP(S) URL"; encoding "is unused when `baseUrl` is an HTTP(S) URL"; "We strongly recommend using an HTTP(S) URL as the `baseUrl`, as this helps ensure your app complies with the same-origin policy." Use it "When your app only needs to load an HTML page and doesn't need to intercept subresources". Source: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
- `WebViewAssetLoader`: serves local content "with an HTTP(S) URL for compatibility with the same-origin policy" through `shouldInterceptRequest` in a `WebViewClientCompat`; can `setDomain(...)` and falls back to the network for paths no handler matches. Source: same page.
- Cached files: `InternalStoragePathHandler(context, directory)` hosts a directory under app internal storage, for example `/public/` on `appassets.androidplatform.net`; "assume any file under this directory could be accessed by any web page subject to same-origin rules." Source: https://developer.android.com/reference/androidx/webkit/WebViewAssetLoader.InternalStoragePathHandler
- Default domain: `DEFAULT_DOMAIN = "appassets.androidplatform.net"`, "An unused domain reserved for Android applications"; local files "should only be hosted on domains your organization owns ... or the default domain". Source: https://developer.android.com/reference/androidx/webkit/WebViewAssetLoader
- Avoid: `file://` and `data:` URLs are "opaque origins"; `loadData()` uses `data:` URLs; avoid `MIXED_CONTENT_ALWAYS_ALLOW`. Source: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
- Google recommends `WebViewCompat.navigate` in Jetpack Webkit over `loadUrl`. Source: https://developer.android.com/develop/ui/views/layout/webapps/webview

### 4.4 Dark theme

- "WebView always sets `prefers-color-scheme` according to `isLightTheme`. If `isLightTheme` is `true` or not specified, then `prefers-color-scheme` is `light`; otherwise, it is `dark`." Source: https://developer.android.com/develop/ui/views/layout/webapps/dark-theme
- So the value follows the Activity's XML theme attribute, not the Compose theme. Google's Compose page says: "apply a `DayNight` style theme to your `Activity`" (example parent `Theme.AppCompat.DayNight.NoActionBar`). Source: https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/wrap-webview-in-compose
- Default strategy `DARK_STRATEGY_PREFER_WEB_THEME_OVER_USER_AGENT_DARKENING` "requires the meta tag to honor the web page's `prefers-color-scheme` media queries"; add `<meta name="color-scheme" content="dark light">`. For first-party content using `prefers-color-scheme`, Google recommends `DARK_STRATEGY_WEB_THEME_DARKENING_ONLY`. Source: https://developer.android.com/develop/ui/views/layout/webapps/dark-theme
- Algorithmic darkening for apps targeting Android 13+: `WebSettingsCompat.setAlgorithmicDarkeningAllowed(settings, true)`; applies only if the content does not use `prefers-color-scheme` and does not disable darkening. Source: same page.
- Theme switches can update content "automatically without a page reload if handled correctly." Source: compose wrap page.

### 4.5 Nested scrolling and touch inside a feed or pager

- "Nested scrolling is not easily supported when using `WebView` in Compose. When placing a `WebView` inside a scrollable Compose container, such as a `LazyColumn`, the `WebView` may consume all scroll gestures ... nesting it with `LazyColumn` does not currently work properly." Tracking issue 148731508. Source: https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/wrap-webview-in-compose
- Inference, not from a source: hosting the explainer WebView as its own full-screen destination, outside the feed's `LazyColumn` or pager, avoids the documented nested-scroll problem.
- Guidance on WebView inside `HorizontalPager`/`VerticalPager`, and on horizontal drags for in-page sliders competing with the parent: NOT FOUND.
- Edge to edge: use `Modifier.windowInsetsPadding(WindowInsets.systemBars)`; in owned CSS use `env(safe-area-inset-top)`. Source: compose wrap page.

---

## 5. Standard libraries

| Need | Library and stable version | Minimum requirements found | Source |
|---|---|---|---|
| HTTP | OkHttp 5.5.1 (`com.squareup.okhttp3:okhttp:5.5.1`) | "OkHttp works on Android 5.0+ (API level 21+) and Java 8+." Uses AndroidX Startup. | https://github.com/square/okhttp (README, tags `parent-5.5.1`) |
| HTTP | Retrofit 3.0.0 (May 15, 2025) | "Retrofit requires at minimum Java 8+ or Android API 21+." 3.0.0 "Upgrade to OkHttp 4.12 (from 3.14)". | https://github.com/square/retrofit (README, CHANGELOG) |
| HTTP | Ktor client 3.6.1 (October 29, 2026) | Engine table: Android engine Android 1.x+, Java 8+; OkHttp engine Android 5.0+, Java 8+; CIO 7.0+ with desugaring for older. | https://github.com/ktorio/ktor/releases/tag/3.6.1 , https://ktor.io/docs/client-engines.html |
| JSON | kotlinx.serialization 1.13.0 (November 11, 2026) | "This release is based on Kotlin 2.4.10"; plugin `org.jetbrains.kotlin.plugin.serialization` "released in tandem with each new Kotlin compiler version"; ProGuard rules bundled. | https://github.com/Kotlin/kotlinx.serialization/releases/tag/v1.13.0 , README |
| Images | Coil 3.6.3 (September 18, 2026): `io.coil-kt.coil3:coil-compose`, plus a network artifact such as `coil-network-okhttp` | Android min SDK 23 since 3.5.0; 3.6.0 built with compile SDK 37, Kotlin 2.4.10, Compose 1.12.0; 3.6.3 fixes AGP 9.4.0 plus R8 builds. | https://github.com/coil-kt/coil (README, CHANGELOG.md) |
| Database | Room 2.8.5 (`androidx.room`) | Stable; minSdk NOT FOUND. | https://developer.android.com/jetpack/androidx/versions |
| Database | Room 3.0.3 (`androidx.room3`, 3.0.0 stable July 1, 2026) | New package; KSP required; Kotlin codegen only; all operations coroutine based; `SQLiteDriver` required; Paging via `room3-paging` and `@DaoReturnTypeConverters(PagingSourceDaoReturnTypeConverter::class)`; Room Gradle plugin `androidx.room3` with `schemaDirectory`. | https://developer.android.com/jetpack/androidx/releases/room3 |
| Key-value | DataStore 1.3.0 (October 21, 2026), `androidx.datastore:datastore-preferences:1.3.0` | minSdk NOT FOUND on the release page. | https://developer.android.com/jetpack/androidx/releases/datastore |
| Paging | Paging 3.5.3 (October 12, 2026), `androidx.paging:paging-compose:3.5.3` | Default minSdk 23. "Paging 3.0 and later provides Compose support through the androidx.paging:paging-compose library." | https://developer.android.com/jetpack/androidx/releases/paging , https://developer.android.com/develop/ui/compose/lists |
| Navigation | Navigation 3 1.2.1 (November 4, 2026), `navigation3-runtime`, `navigation3-ui`; 1.0.0 stable November 19, 2025 | "Navigation 3 is a new navigation library designed to work with Compose." 1.2 depends on Compose 1.10 and uses compileSdk 36. | https://developer.android.com/jetpack/androidx/releases/navigation3 |
| Navigation | Navigation Compose 2.10.2 (September 23, 2026) | NOT FOUND (minimums). | https://developer.android.com/jetpack/androidx/releases/navigation |
| DI | Hilt (Dagger) 2.60.1; plugin `com.google.dagger.hilt.android`; `ksp("com.google.dagger:hilt-compiler:2.60.1")`; AndroidX Hilt extensions 1.4.0 (July 1, 2026) | "minSDK for Hilt is now 23"; KSP or kapt supported. Compatibility with AGP 9 built-in Kotlin: NOT FOUND. | https://github.com/google/dagger/releases/tag/dagger-2.60 , https://dagger.dev/hilt/gradle-setup , https://developer.android.com/jetpack/androidx/releases/hilt |
| Annotation processing | KSP 2.3.13 (October 30, 2026) carries a "regression ... which may cause issues for concurrent executions"; previous 2.3.12 (September 9, 2026) | "KSP version is no longer tied to the Kotlin compiler version" since 2.3.0. | https://github.com/google/ksp/releases |
| Activity and lifecycle | `androidx.activity:activity-compose:1.13.0`, `androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0` | | https://developer.android.com/develop/ui/compose/compiler , https://developer.android.com/jetpack/androidx/versions |

Note on Retrofit: Retrofit 3.0.0 pins OkHttp 4.12 (CHANGELOG above) while the current OkHttp is 5.5.1. Whether Retrofit 3.0.0 runs correctly against OkHttp 5.x: NOT FOUND.

---

## 6. Headless testing on Linux

### 6.1 Tool status

- `sdkmanager`, `avdmanager` and `emulator` are each marked deprecated in favor of the new Android CLI (`android sdk`, `android emulator`). The old tools are still documented and shipped. Sources: https://developer.android.com/tools/sdkmanager , https://developer.android.com/tools/avdmanager , https://developer.android.com/studio/run/emulator-commandline
- Installed cmdline-tools is 22.0; repository lists 23.0 (local check and https://dl.google.com/android/repository/repository2-3.xml). The cmdline-tools need a JDK, which is not installed yet (local check).

### 6.2 System images (x86_64, stable channel)

From https://dl.google.com/android/repository/sys-img/google_apis/sys-img2-3.xml , https://dl.google.com/android/repository/sys-img/google_atd/sys-img2-3.xml , https://dl.google.com/android/repository/sys-img/aosp_atd/sys-img2-3.xml , https://dl.google.com/android/repository/sys-img/google_apis_playstore/sys-img2-3.xml (archive download sizes in bytes):

| Package | Revision | Download size |
|---|---|---|
| `system-images;android-37.0;google_apis;x86_64` | 8 | 2,143,899,425 |
| `system-images;android-36;google_apis;x86_64` | 7 | 1,895,447,397 |
| `system-images;android-35;google_apis;x86_64` | 9 | 1,738,815,903 |
| `system-images;android-37.0;google_atd;x86_64` | 7 | 940,150,639 |
| `system-images;android-36;google_atd;x86_64` | 1 | 859,633,861 |
| `system-images;android-37.0;aosp_atd;x86_64` | 1 | 798,992,458 |
| `system-images;android-36;aosp_atd;x86_64` | 1 | 745,532,480 |
| `system-images;android-36;google_apis_playstore;x86_64` | 7 | 1,924,689,206 |

- Variants: "System images labeled **Google APIs** include access to Google Play services and those labeled **Google Play** also include the Google Play Store." Source: https://developer.android.com/tools/releases/platforms
- ATD images are "optimized for headless automated tests" by "Removing most user-facing applications (for example Dialer, Settings, and SystemUI)" and "Disabling hardware renderer drawing". Source: https://developer.android.com/tools/releases/platforms
- A plain AOSP (non-ATD) x86_64 image for API 35 to 37: NOT FOUND (the `default` channel manifest URL did not return parseable XML).
- Installed disk size of an unpacked image and AVD: NOT FOUND. Only download sizes above are published.

### 6.3 Commands

- Install packages: `sdkmanager "platform-tools" "platforms;android-36"` style, each path quoted; `sdkmanager --licenses` on headless machines. Source: https://developer.android.com/tools/sdkmanager
- Create AVD: `avdmanager create avd -n name -k "sdk_id"`, for example `avdmanager create avd -n test -k "system-images;android-25;google_apis;x86"`; AVDs go to `~/.android/avd/` by default. Source: https://developer.android.com/tools/avdmanager
- KVM check: `emulator -accel-check`; Linux output example "KVM (version 12) is installed and usable." "Running KVM requires specific user permissions." Source: https://developer.android.com/studio/run/emulator-acceleration
- Headless start: `-no-window` "Disables graphical window display on the emulator. This option is useful when running the emulator on servers that have no display." Other useful flags: `-no-snapshot`, `-no-boot-anim`, `-no-audio`, `-wipe-data`, `-accel on`. Source: https://developer.android.com/studio/run/emulator-commandline
- GPU flag: `swiftshader_indirect` is "Deprecated in version 36.4.9" (installed emulator is 37.2.12). Current modes: `auto`, `host`, `software`, `lavapipe`, `swiftshader`, `swangle`. Source: https://developer.android.com/studio/run/emulator-acceleration
- Screenshot: `adb exec-out screencap -p > screen.png` ("use 'exec-out' instead of 'shell' to get raw data"). Source: https://developer.android.com/tools/adb
- Waiting for boot completion from a script: NOT FOUND in the pages read.

### 6.4 Instrumented and Compose UI tests

- Local unit tests `./gradlew test` (reports in `module/build/reports/tests/`); instrumented `./gradlew connectedAndroidTest` (reports in `module/build/reports/androidTests/connected/`); or `adb shell am instrument -w <test_package>/androidx.test.runner.AndroidJUnitRunner`. Source: https://developer.android.com/studio/test/command-line
- Compose UI test dependencies: `androidTestImplementation("androidx.compose.ui:ui-test-junit4")` and `debugImplementation("androidx.compose.ui:ui-test-manifest")` under the BOM. Source: https://developer.android.com/develop/ui/compose/compiler

### 6.5 Screenshot tests on the JVM, no emulator

- Official Compose Preview Screenshot Testing: "The standalone `com.android.compose.screenshot` plugin described on this page is no longer maintained. We recommend setting up screenshot tests with AGP test suites using Android Gradle Plugin (AGP) 9.5 or higher." Source: https://developer.android.com/studio/preview/compose-screenshot-testing
- Test-suite version: "**Experimental:** ... APIs and DSL syntax are subject to change." Requires AGP 9.5.0-alpha03 or higher, engine `0.0.1-alpha16`, JDK 17+, flags `android.experimental.enableScreenshotTest=true` and `android.experimental.testSuiteSupport=true`, DSL `testOptions { screenshotTests.create("screenshotTest") { ... } }`, tasks `update{SuiteName}{Target}{Variant}TestSuite` and `test{SuiteName}{Target}{Variant}TestSuite`. Previews are rendered host side through Layoutlib. Source: https://developer.android.com/studio/preview/compose-screenshot-testing-with-testsuites
- Roborazzi: latest 1.79.0 (November 12, 2026). Runs screenshot tests in JVM tests through Robolectric; "please use Robolectric 4.10 alpha 1 or later". Sources: https://github.com/takahirom/roborazzi/releases , https://github.com/takahirom/roborazzi (README)
- Robolectric 4.17 (September 10, 2026): "Robolectric 4.17 supports SDK 37". Source: https://github.com/robolectric/robolectric/releases
- Paparazzi: "render your application screens without a physical device or emulator"; tasks `recordPaparazziDebug` and `verifyPaparazziDebug`. Releases since 2025 are `2.0.0-alpha01` to `2.0.0-alpha05.1` (September 28, 2026); the last non-alpha tag is `1.3.5`. Paparazzi 1.3.5 support for AGP 9 or compileSdk 37: NOT FOUND. Sources: https://github.com/cashapp/paparazzi (README, tags)

---

## 7. Release pipeline on GitHub Actions

### 7.1 Actions (latest releases on 2026-11-12)

| Action | Latest | Notes from its README | Source |
|---|---|---|---|
| `actions/checkout` | v7.0.1 | | https://github.com/actions/checkout/releases |
| `actions/setup-java` | v6.2.0 | example `distribution: temurin` | https://github.com/actions/setup-java |
| `gradle/actions/setup-gradle` | v6.4.1 | "The recommended way to execute any Gradle build is with the help of the Gradle Wrapper" | https://github.com/gradle/actions |
| `softprops/action-gh-release` | v3.0.4 | `files:` multi-line globs; "This Action requires the following permissions on the GitHub integration token: `permissions: contents: write`"; examples gate on `if: github.ref_type == 'tag'` | https://github.com/softprops/action-gh-release |
| `reactivecircus/android-emulator-runner` | v2.38.0 | recommends `ubuntu-latest`; "Remember to enable KVM in your workflow" with a udev rule `KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"` | https://github.com/ReactiveCircus/android-emulator-runner |

### 7.2 Keystore as a base64 secret

- GitHub: "You can use Base64 encoding to store small binary blobs as secrets"; on Linux `base64 -w 0 cert.der > cert.base64`; `gh secret set CERTIFICATE_BASE64 < cert.base64`; "Base64 only converts binary to text, and is not a substitute for actual encryption." Secrets over 48 KB need the gpg workaround. Source: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions
- Android: the official pattern reads signing values from a `keystore.properties` file kept out of source control (`storePassword=...`). Source: https://developer.android.com/studio/publish/app-signing . A `signingConfig` that reads `System.getenv(...)`: NOT FOUND as an official Android example.
- Command-line signing: `apksigner sign --ks my-release-key.jks --out my-app-release.apk my-app-unsigned-aligned.apk`, after `zipalign`. Source: https://developer.android.com/build/building-cmdline

### 7.3 versionCode

- "The greatest value Google Play allows for versionCode is 2100000000"; each release must use a greater value; you cannot reuse one. Source: https://developer.android.com/studio/publish/versioning
- `GITHUB_RUN_NUMBER`: "A unique number for each run of a particular workflow ... begins at 1 ... This number does not change if you re-run the workflow run." Source: https://docs.github.com/en/actions/reference/workflows-and-actions/variables
- Reproducibility (inference from F-Droid's rule in 7.4 that APKs "must be completely identical" apart from the signature): a versionCode taken from a CI counter would not exist in an F-Droid source build, so the versionCode has to be committed in source (for example, set in the build file or derived from the git tag) for the F-Droid build to match the GitHub APK.

### 7.4 F-Droid inclusion

- "All applications in the repository must be Free, Libre and Open Source Software (FLOSS)". Source: https://f-droid.org/docs/Inclusion_Policy/
- "The implementation of proprietary tracking or advertising libraries and analytics tools such as Google Play Services and Firebase and Crashlytics and proprietary ad/tracking SDKs are strictly forbidden in all applications. Upstream developers must implement either a FLOSS alternative or a build flavour that does not require these dependencies". Source: https://f-droid.org/docs/Inclusion_Policy/
- "Library dependencies must be built from source or provided in a trusted Maven repo"; trusted repos include "Maven Central, Google Maven, OSS Sonatype, OSS JFrog, JitPack.io and Clojars"; binaries "must still be freely licensed". Source: https://f-droid.org/docs/Inclusion_Policy/
- "Applications must not download additional executable binary files (e.g. add-ons, auto-updates, etc.) without explicit user consent." Whether downloaded HTML and JavaScript explainers count as "executable binary files": NOT FOUND. Source: https://f-droid.org/docs/Inclusion_Policy/
- Anti-Features are labels that do not necessarily disqualify an app; "Non-Free Network Services - promotes or depends entirely on a non-free network service" and "Tethered Network Services - depends entirely on a certain instance of a network service". Sources: https://f-droid.org/docs/Inclusion_Policy/ , https://f-droid.org/docs/Anti-Features/
- Submission: metadata lives in `fdroiddata` (`metadata/<applicationId>.yml`), proposed by merge request; prerequisites include "a public source code repository and a FOSS license file". Source: https://f-droid.org/docs/Submitting_to_F-Droid_Quick_Start_Guide/
- Developer-signed APKs: F-Droid can "publish the signed binaries from the upstream developer after verifying that they match the ones built using an fdroiddata build recipe. Publishing only takes place if there is a proper match." Enabled with the `Binaries` metadata directive. "The APKs must be completely identical before and after signing (apart from the signature)"; developers should sign with `apksigner`. Source: https://f-droid.org/docs/Reproducible_Builds/

---

## 8. APK signing and sideloading

- Installing a sideloaded APK: "Android blocks such installs until the user opts into allowing the installation of apps from other sources." "On devices running Android 8.0 (API level 26) and higher, users must navigate to the Install unknown apps system settings screen to enable app installations from a particular location". Source: https://developer.android.com/distribute/marketing-tools/alternative-distribution
- From 2027, unregistered apps also need the advanced flow or ADB on certified devices (section 3.2).
- Losing the key: "If you lose access to your app signing key or your key is compromised, Google cannot retrieve the app signing key for you, and you will not be able to release new versions of your app to users as updates to the original app." "Users can only update your app if the update is signed with the same signing key". Recommended validity "25 years or more"; Play requires validity ending after 22 October 2033. Source: https://developer.android.com/studio/publish/app-signing . Lost key also blocks developer verification package registration (section 3.2).
- Play App Signing and an existing key: "If you provide the app signing key to Google when opting in your new or existing app, then you have the option to generate a new upload key during or after opting in ... If you do not generate a new upload key, you continue to use your app signing key as your upload key". "When you use Play App Signing, if you lose your upload key, or if it is compromised, you can request an upload key reset in the Play Console." Source: https://developer.android.com/studio/publish/app-signing
- Inference from the "same signing key" rule above: if Play App Signing generates its own app signing key instead of receiving the key used for the GitHub APKs, a user who installed the GitHub APK could not update to the Play build. Uploading the existing key at opt-in keeps one signing identity across GitHub, F-Droid (developer-signed mode) and Play.

---

## Recommended setup

Each line points to the section that cites it.

1. JDK: `jdk17-openjdk` (AGP minimum and default 17, section 1.1, 1.3). Not `jdk-openjdk` 27 (needs Gradle 9.8.0+, section 1.2).
2. Gradle wrapper: 9.5.0 (AGP 9.3 minimum and default; within KGP 2.4.21 max 9.7.0, sections 1.1, 1.4).
3. AGP: 9.3.1 (API 37 support, above Compose's 9.2.0 floor, JetBrains-listed max for KGP 2.4.21, sections 1.1, 1.4, 1.6). Built-in Kotlin on; do not apply `org.jetbrains.kotlin.android`; pin KGP 2.4.21 with the buildscript classpath line (section 1.1).
4. Kotlin: 2.4.21 for KGP, `org.jetbrains.kotlin.plugin.compose` and `org.jetbrains.kotlin.plugin.serialization` (sections 1.4, 1.5, 5).
5. KSP: 2.3.12, not 2.3.13 (known regression, section 5).
6. Compose BOM: `androidx.compose:compose-bom:2026.09.00` (section 1.6).
7. compileSdk 37; install `platforms;android-37.0` (section 1.6, 1.7).
8. targetSdk 36 (Play requirement in force, section 2). 37 is available but adds Android 17 behavior changes (section 1.7).
9. minSdk 24 (AndroidX default, "meant to cover 99% of Android users", section 2).
10. Build Tools 36.0.0, already installed (section 1.1).
11. WebView: `AndroidView` + `WebView`, `androidx.webkit:webkit:1.18.0`; JavaScript on; `allowFileAccess`, `allowContentAccess`, `allowFileAccessFromFileURLs`, `allowUniversalAccessFromFileURLs` all `false`; mixed content `MIXED_CONTENT_NEVER_ALLOW`; no `addJavascriptInterface`; `setSupportMultipleWindows(true)` without `onCreateWindow`; `shouldOverrideUrlLoading` allowing only the explainer origin by exact scheme and host, everything else to the browser; cleartext off; destroy on release (section 4.1, 4.2).
12. Load explainers with `loadDataWithBaseURL("https://<api host>/...", html, "text/html", null, sameUrl)`, or serve cached files via `WebViewAssetLoader` + `InternalStoragePathHandler` on `appassets.androidplatform.net` when subresources must load (section 4.3).
13. Dark mode: Activity theme `Theme.AppCompat.DayNight.NoActionBar` style so `isLightTheme` tracks the system; explainer HTML includes `<meta name="color-scheme" content="dark light">` and `prefers-color-scheme` rules; `DARK_STRATEGY_WEB_THEME_DARKENING_ONLY` (section 4.4).
14. Explainer as its own full-screen destination, not inside the scrolling feed (inference from the documented nested-scroll limitation, section 4.5).
15. Networking: OkHttp 5.5.1 + `kotlinx-serialization-json:1.13.0`; skip Retrofit 3.0.0 because it pins OkHttp 4.12 (section 5).
16. Images: Coil 3.6.3 with `coil-compose` and `coil-network-okhttp` (section 5).
17. Storage: Room 3.0.3 (`androidx.room3`, KSP, coroutines, `room3-paging`) for papers and ratings; DataStore Preferences 1.3.0 for settings (section 5). Room 2.8.5 is the fallback if a needed library depends on `androidx.room`.
18. Feed: Paging 3.5.3 with `paging-compose` (section 5).
19. Navigation: Navigation 3 1.2.1 (section 5).
20. DI: none at first (manual constructor injection). This is a judgment call: Hilt 2.60.1 adds a Gradle plugin and a KSP processor, and its compatibility with AGP 9 built-in Kotlin was NOT FOUND (section 5).
21. Emulator: `system-images;android-36;google_apis;x86_64` (rev 7, about 1.9 GB download) for the targetSdk, plus `system-images;android-37.0;google_apis;x86_64` for compileSdk behavior; run with `-no-window -gpu swiftshader -no-audio -no-boot-anim -no-snapshot` after `emulator -accel-check`; screenshots with `adb exec-out screencap -p > screen.png` (section 6).
22. JVM screenshot tests: Roborazzi 1.79.0 on Robolectric 4.17 (supports SDK 37). The official test-suite tool needs AGP 9.5 and is experimental; the standalone plugin is unmaintained; Paparazzi is alpha-only since 2025 (section 6.5).
23. CI: `actions/checkout@v7`, `actions/setup-java@v6` (temurin, 17), `gradle/actions/setup-gradle@v6`, keystore from a base64 secret decoded on the runner, `softprops/action-gh-release@v3` with `permissions: contents: write`, triggered on tags (section 7.1, 7.2).
24. versionCode committed in source (or derived from the tag), not from `GITHUB_RUN_NUMBER`, so F-Droid can reproduce the APK (section 7.3, 7.4).
25. No Google Play Services, Firebase or Crashlytics (F-Droid rule, section 7.4).
26. One signing key for GitHub, F-Droid developer-signed builds, and Play (upload it at Play App Signing opt-in); 25+ year validity; back it up (section 8).
27. Before the 2027 global rollout, verify identity and register `io.github.ntrpydev.paperboy` with that key, through the Play Console account once it exists (section 3.2).

## NOT FOUND

1. Next Google Play target API deadline after November 1, 2026 (no Android 17 or API 37 date on the requirement pages).
2. Per-API-level device distribution percentages on the web (only the "99%" statement for minSdk 24; the table lives in Android Studio's wizard).
3. Whether a personal Play account's home address is displayed publicly.
4. A published Kotlin compatibility statement for AGP 9.4 or 9.5 (JetBrains' table stops at AGP 9.3.1).
5. The KGP version AGP 9.3 and 9.5 depend on at runtime (only AGP 9.0's 2.2.10 found).
6. WebView Safe Browsing default value.
7. Guidance for WebView inside a Compose pager, and for in-page horizontal sliders competing with the parent gesture.
8. Whether F-Droid treats downloaded HTML and JavaScript explainers as "executable binary files" under its download rule.
9. Whether Paperboy would get the Non-Free Network Services or Tethered Network Services anti-feature (depends on the server's license and whether one instance is hard-coded; not stated anywhere for this case).
10. Room 2.8.5 and DataStore 1.3.0 minSdk values.
11. Navigation Compose 2.10.2 minimum requirements.
12. Hilt compatibility with AGP 9 built-in Kotlin.
13. Whether Retrofit 3.0.0 works against OkHttp 5.x.
14. Paparazzi 1.3.5 support for AGP 9 or compileSdk 37.
15. A plain AOSP (non-ATD) x86_64 system image for API 35 to 37.
16. Installed (unpacked) disk size of a system image or AVD.
17. A documented way to wait for emulator boot completion from a script.
18. An official Android example of a `signingConfig` that reads environment variables.
