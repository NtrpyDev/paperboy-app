# Paperboy

Paperboy is a free, open source Android app: an endless feed of newly released science and math papers, peer-reviewed and preprints, each labeled as one or the other. Every paper in the feed has its own picture and opens its own visual explainer, a page of diagrams, charts drawn from the paper's reported numbers, and plain text: the best few are built from the paper's free legal full text, the rest from its abstract, and each page says which. Every page links to the original paper. No account, no ads.

- Website: https://paperboy.ntrpydev.workers.dev/
- Download: the latest APK is on the [releases page](https://github.com/NtrpyDev/paperboy-app/releases). Not on Google Play yet.
- Published feed and explainers: [NtrpyDev/paperboy-content](https://github.com/NtrpyDev/paperboy-content), under CC BY 4.0.

Explainers are machine written and can be wrong. Each one says so and links its source so you can check it against the paper.

## How it works

1. A scheduled cloud run follows `pipeline/RUNBOOK.md`. A second way to run it, on an Anthropic API account in GitHub Actions for the fields paying subscribers picked, is built and off (`.github/workflows/pipeline-api.yml`). Once a day's papers are out, AI agents read their titles and abstracts, keep the best, and write each one's card text. The kept papers wait in a backlog in the content repo; nothing reaches the feed yet.
2. Each hourly run takes the best papers waiting, alternating preprints and peer-reviewed papers, and builds a page for each. The very best with a free legal full text get a full explainer, built and verified from the full text by three agents (an expert reader, a visualizer, and a checker). The rest get a quick explainer, built by one agent from the title and abstract and checked by code so that every number it prints is in the abstract. Runs pace their usage through the week, and a paper that waits more than a week without a page ages out.
3. A paper enters the feed only when its page passes. The run publishes the card, its picture, and its page to the content repo together.
4. A Cloudflare Worker serves the feed, the explainers, the kit, and the website from that repo.
5. The app reads the feed, ranks it on the phone from your "More like this" and "Less like this" taps, and opens explainers in place. Ratings never leave the phone.

## Repo layout

```
.claude/             Agent definitions the pipeline run uses: triage, scout, quick, expert, visualizer, checker
.github/             GitHub Actions workflows: tests on every push, the signed release APK, and the pipeline run on the API account
app/                 Android app (Kotlin, Jetpack Compose)
design/              Design system, build handoff, and the Claude Design artboards
docs/                Agent docs and the research notes behind the design decisions
gradle/              Gradle wrapper files and the version catalog
kit/                 Stylesheets, scripts, fonts, and vendored libraries every explainer page loads
pipeline/            Python package and runbook that turn new papers into feed items and explainers
schema/              JSON schemas for the records the pipeline, worker, and app pass to each other
site/                The website, a static page
tools/               Small scripts for development, feed fixtures, and reading Claude usage
worker/              Cloudflare Worker that serves the feed, explainers, kit, and website, and the subscription API
.gitignore           Files git never tracks
build.gradle.kts     Root Gradle build file
CLAUDE.md            Instructions for coding agents working in this repo
GLOSSARY.md          The project's vocabulary, one meaning per word
gradle.properties    Gradle properties for the Android build
gradlew, gradlew.bat Gradle wrapper scripts
LICENSE              GNU General Public License, version 3
NOTICE.md            Third-party libraries and fonts, with their licenses
README.md            This file
settings.gradle.kts  Gradle settings: the project name and its app module
```

Paperboy's code is under the GNU General Public License, version 3 or later.

## App

The Android app is the Gradle project at the repo root (`app/`). It needs JDK 17 and the Android SDK; `tools/dev-env.sh` sets both up on the dev machine. The script is POSIX shell, so from fish run each command below as `bash -c 'source tools/dev-env.sh && ...'`.

### Two builds

One codebase builds two apps, chosen at build time by product flavor:

- `free`: today's app. Reads the open feed, and the update cover links to GitHub releases. This is the APK the release workflow publishes.
- `paid`: the Google Play app. Google Play Billing (`app/src/paid/`), the entitlement call to the worker (`POST /v1/entitlement`), the pass on every feed and explainer request, the subscription screens, and the update cover linking to the Play Store listing. Only this build has the Play Billing Library and the `com.android.vending.BILLING` permission. Nothing can be bought yet: there is no Play listing, so its tests run against a fake Play (`app/src/sharedTest/`).

Both use the package name `io.github.ntrpydev.paperboy`. Code for both is in `app/src/main/`; `app/src/free/` and `app/src/paid/` hold what differs.

Build the debug APKs (written to `app/build/outputs/apk/free/debug/` and `app/build/outputs/apk/paid/debug/`):

```sh
source tools/dev-env.sh
./gradlew assembleFreeDebug
./gradlew assemblePaidDebug
```

Run the unit tests (JVM, no device needed), for each build:

```sh
./gradlew testFreeDebugUnitTest testPaidDebugUnitTest
```

Run the instrumented tests (needs a running emulator or a connected device). The free build runs `app/src/androidTest/`; the paid build runs those and `app/src/androidTestPaid/`:

```sh
./gradlew connectedFreeDebugAndroidTest
./gradlew connectedPaidDebugAndroidTest
```

Release builds need the signing variables the release workflow sets (`PAPERBOY_KEYSTORE_FILE`, `PAPERBOY_KEYSTORE_PASSWORD`, `PAPERBOY_KEY_ALIAS`, `PAPERBOY_KEY_PASSWORD`). The free release APK is `./gradlew assembleFreeRelease`. The paid build is published as an Android App Bundle, which Google Play requires for new apps (https://developer.android.com/guide/app-bundle): `./gradlew bundlePaidRelease`, written to `app/build/outputs/bundle/paidRelease/`. No workflow uploads it.

The paid build's subscription ids are placeholders until the subscription exists in Play Console. Set the real ones with `-Ppaperboy.productId=<product id> -Ppaperboy.basePlanId=<base plan id>`, or change the defaults in `app/build.gradle.kts`. The product id must match what the worker is sent and what Play Console shows.

### Content base

The app reads the feed and explainers from the content base, `https://paperboy.ntrpydev.workers.dev` by default. To point a debug build at another server, for example the fixture files in `app/src/fixtures` served on your machine:

```sh
python3 -m http.server 18765 --bind 127.0.0.1 --directory app/src/fixtures
adb reverse tcp:18765 tcp:18765
./gradlew installFreeDebug -Ppaperboy.contentBase=http://localhost:18765/
```

Debug builds allow plain HTTP only to `localhost`, `127.0.0.1`, and `10.0.2.2`; release builds allow HTTPS only.

## Worker

The edge worker in `worker/` serves the site, the kit, the feed, and the explainers at `https://paperboy.ntrpydev.workers.dev`, and the subscription API under `/v1/` (entitlement checks, Play notifications, and the active fields list). It needs Node.js. Run its tests from that folder:

```sh
cd worker
npm install
npm test
```

`worker/README.md` describes what it serves, the subscription API, and how to deploy it and take it live.
