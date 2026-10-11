# Q'uq' Matemáticas — Android wrapper

Packs each grade's web app (`../primero/public`, `../segundo/public`, `../tercero/public`) into its own
offline APK that families download from the Utz'tutor at `http://tutorbox/descargas/`, where the
child picks the grade. See [pwa/README.md §3](../../README.md#3-tareas--take-home-math-apps-tareas)
for why this is an APK and not an installable PWA.

## How it works

One `Activity` with a `WebView` (`app/src/main/java/org/tutorbox/primero/MainActivity.java`):

- **One product flavor per grade** (`primero`, `segundo`, `tercero` in `app/build.gradle`): same
  Java wrapper, own `applicationId` (`org.tutorbox.<grade>`, so the three install side by side) and own
  launcher label (`src/<grade>/res/values/strings.xml`: "Q'uq' 1º/2º/3º"). Primero keeps the id it
  first shipped with, so installed copies update in place.
- **No copy of the lessons.** Each flavor's assets point at `../../<grade>/public`, so every build
  packs whatever the web app currently is.
- **Served from `https://appassets.androidplatform.net/`** (a host Android reserves for this). A real
  https origin, not `file://`, is what lets the ES module scripts load and `localStorage` keep progress.
- **Speech:** WebView has no `speechSynthesis`, so the activity exposes the phone's offline
  text-to-speech as `window.AndroidTTS`; `public/js/engine/audio.js` uses it when present.
- **No service worker** in the APK (guarded in `public/js/app.js`): the files are already on the phone,
  and a cache-first worker would keep serving old lessons after an update.
- **No `INTERNET` permission.** Nothing leaves the phone.

## Build

Needs the Android SDK (Android Studio installs it) and JDK 17+. From this folder:

```bash
./gradlew publishApk      # Windows: gradlew.bat publishApk
```

Builds the three release APKs and copies them to `../descargas/primero.apk`, `segundo.apk` and
`tercero.apk`, which the backend serves. One grade only: `./gradlew assembleSegundoRelease`
(output in `app/build/outputs/apk/segundo/release/`).

**Build on the machine that built the APKs already in families' hands.** Android refuses an update
signed with a different key (see below). The Jetson itself cannot build: it is ARM64 and Google
ships the Android build tools (`aapt2`) for x86-64 Linux, Windows and macOS only.
`local.properties` (`sdk.dir=...`) is machine-specific and not committed; Android Studio writes it,
or set `ANDROID_HOME`.

## Release signing — do this once, before the first family installs

Android only installs an update over an existing app when both are signed with the **same key**.
Without `keystore.properties` the build falls back to this computer's debug key, which is fine for
testing but differs on every machine. If families install a debug build, a later release can only be
installed after uninstalling — which **deletes the child's progress**.

```bash
keytool -genkeypair -v -keystore quq-release.jks -alias quq -keyalg RSA -keysize 2048 -validity 10000
```

Then create `keystore.properties` next to this README (both files are git-ignored):

```properties
storeFile=quq-release.jks
storePassword=...
keyAlias=quq
keyPassword=...
```

Back up the `.jks` file and passwords outside the repo (a password manager). Losing them means no
more updates for installed copies.

## Releasing an update

1. Bump `versionCode` (and `versionName`) in `app/build.gradle` — Android refuses to install an APK
   whose `versionCode` is not higher.
2. `./gradlew publishApk`
3. Copy `../descargas/*.apk` to the Jetson checkout (same path) — no backend restart needed.

## Try it on the emulator

```bash
adb install -r ../descargas/segundo.apk
adb shell am start -n org.tutorbox.segundo/org.tutorbox.primero.MainActivity
```
