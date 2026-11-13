# Paperboy

## App

The Android app is the Gradle project at the repo root (`app/`). It needs JDK 17 and the Android SDK; `tools/dev-env.sh` sets both up on the dev machine. The script is POSIX shell, so from fish run each command below as `bash -c 'source tools/dev-env.sh && ...'`.

Build a debug APK (written to `app/build/outputs/apk/debug/`):

```sh
source tools/dev-env.sh
./gradlew assembleDebug
```

Run the unit tests (JVM, no device needed):

```sh
./gradlew testDebugUnitTest
```

Run the instrumented tests (needs a running emulator or a connected device):

```sh
./gradlew connectedDebugAndroidTest
```

The app reads the feed and explainers from the content base, `https://paperboy.ntrpydev.workers.dev` by default. To point a debug build at another server, for example the fixture files in `app/src/fixtures` served on your machine:

```sh
python3 -m http.server 18765 --bind 127.0.0.1 --directory app/src/fixtures
adb reverse tcp:18765 tcp:18765
./gradlew installDebug -Ppaperboy.contentBase=http://localhost:18765/
```

Debug builds allow plain HTTP only to `localhost`, `127.0.0.1`, and `10.0.2.2`; release builds allow HTTPS only.

## Worker

The edge worker in `worker/` serves the site, the kit, the feed, and the explainers at `https://paperboy.ntrpydev.workers.dev`. It needs Node.js. Run its tests from that folder:

```sh
cd worker
npm install
npm test
```

`worker/README.md` describes what it serves and how to deploy it.
