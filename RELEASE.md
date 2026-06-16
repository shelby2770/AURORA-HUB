# Aurora Hub — App Release Guide

How to produce the publishable mobile builds. The web app is a Next.js static
export (`output:'export'`) wrapped by Capacitor; every build is
`npm run build` (production env → Render backend) → `cap sync` → native build.

## Android — signed AAB (Google Play) ✅ working

**Artifact:** `AuroraHub-release.aab` (repo root) — a signed Android App Bundle.

### Signing key (read this — it is unrecoverable)
- Keystore: `frontend/android/app/aurora-hub-release.jks`
- Credentials: `frontend/android/keystore.properties`
- **Both are gitignored and MUST be backed up somewhere safe** (password manager /
  secure storage). If you lose them you can never ship an update to the same Play
  listing — Google will not let you re-key it (unless you enrolled in Play App
  Signing, in which case Google holds the app signing key and this is the upload
  key, which *can* be reset).
- Cert: `CN=Aurora Hub`, SHA-256 fingerprint:
  `AB:60:AE:1C:40:33:D7:C1:35:D5:96:49:0A:42:34:D3:C4:FD:E7:63:9E:65:F9:B9:97:2C:69:E9:3C:94:1F:DD`

### Rebuild the AAB
```bash
cd frontend
npm run build            # production export → Render backend baked in
npx cap sync android
cd android
ANDROID_HOME=$HOME/Android/Sdk ./gradlew bundleRelease
# → app/build/outputs/bundle/release/app-release.aab
```

### Publish
1. Google Play Console → create the `com.aurorahub.app` app.
2. Upload `AuroraHub-release.aab` to an Internal testing track first.
3. Keep **Play App Signing** enabled (recommended) — Google manages the final
   signing key; the keystore above becomes your *upload* key.

### Bump the version for each release
Edit `frontend/android/app/build.gradle`:
- `versionCode` — integer, must increase every upload (1 → 2 → 3…).
- `versionName` — user-visible string ("1.0" → "1.1").

### Sideload APK (testing)
`./gradlew assembleDebug` → `app/build/outputs/apk/debug/app-debug.apk`
(`adb install -r app-debug.apk`). The debug APK is debug-signed, for testing only.

## iOS — not buildable on this machine ⚠️

iOS requires **macOS + Xcode + CocoaPods** and a **paid Apple Developer account**
($99/yr) to sign and reach the App Store / TestFlight. None of that runs on Linux,
so the iOS app is **not built yet**. What's already in place:

- `@capacitor/ios` is installed and declared in `frontend/package.json`.
- `.github/workflows/ios.yml` builds on a GitHub macOS runner (unsigned compile
  check now; signed archive + TestFlight once you add the Apple secrets it lists).

### When you have a Mac
```bash
cd frontend
npm install
npm run build
npx cap add ios          # generates ios/ (needs CocoaPods)
npx cap sync ios
npx cap open ios         # opens Xcode
```
In Xcode: select your Team under Signing & Capabilities, set the bundle id to
`com.aurorahub.app`, then **Product → Archive → Distribute App** to TestFlight /
App Store. Generate the app icon set from `frontend/assets/brand/` artwork.

### When you have only an Apple Developer account (no Mac)
Use `.github/workflows/ios.yml`: add the signing secrets it documents
(distribution cert `.p12`, provisioning profile, App Store Connect API key) and
fill in the archive/upload steps; CI produces and ships the `.ipa`.
