# Aurora Hub — Mobile (Android + iOS) Source of Truth

Single source of truth for the native build. **Built only after the web version is declared stable
(see [`PLAN.md`](./PLAN.md) Phase 6).** The web app is a Next.js 15 static export (`output:'export'`)
wrapped with Capacitor 8 — same codebase, no SSR.

**Working agreement**
- **Before each phase:** post the checklist + intended approach; wait for approval, then build.
- **After each phase:** run the verification gate (below), update the Status table + Judgment log, open the PR.
- **One PR per phase minimum**, branch naming `mobile/phase-N-<slug>`.
- **Unanticipated decision:** make the call, log it with a "Why," flag it for review — don't block.
- **Daily build command:** `nvm use 22 && npm run build && npx cap sync android` (Capacitor CLI needs Node 22).

Status legend: ⬜ not started · 🔄 in progress · ✅ done · ⚠️ blocked / needs attention

---

## 1. Quick Status table

| Phase | Area | Status | Notes |
|------|------|:----:|------|
| 0 | Infra — Capacitor install, config, `android/` committed, smoke script | ✅ | Capacitor 8.4 + Android platform; `npm run smoke` @375px green |
| 1 | Mobile shell & navigation — bottom-nav, topbar, safe-area, keyboard + back managers | ⬜ | Depends on Phase 0 |
| 2 | Config / quiz-setup flow — mobile inputs, touch-fixed selects | ⬜ | |
| 3 | Exam runtime — one-per-screen, Framer Motion, KaTeX/Shiki overflow, timer survives backgrounding | ⬜ | |
| 4 | Practice feedback & scoring — result screens, share/export (rule 6) | ⬜ | |
| 5 | Account/settings/billing screens — payments via rule 7 (if applicable) | ⬜ | May be N/A (no auth yet) |
| 6 | Polish — real-notch safe-area, iOS zoom/overscroll, Android `env()=0` floor audit, asset sizes | ⬜ | |
| 7 | iOS project + CI/CD — `cap add ios`, GitHub Actions macOS runner, TestFlight, Android APK workflow | ⬜ | No local Mac |
| 8 | E2E — Playwright suites @375px green + full device checklist (emulator + iOS) + dark-mode pass | ⬜ | Drains Pending-device backlog |

---

## 2. Judgment Calls & Decisions log

Append a row every time you deviate from the plan or make a non-obvious call. Owner reviews and ticks.

| Phase | Decision | Why | Reviewed? |
|------|----------|-----|:--------:|
| 0 | App identity `com.aurorahub.app` / "Aurora Hub". | User-selected from offered options; baked into `android/` namespace + `applicationId` (hard to change later). | ⬜ |
| 0 | Local Android toolchain is fully present (Node 22, JDK 21, Android SDK at `~/Android/Sdk`). So `cap sync android` runs locally, not only in CI. iOS (Phase 7) remains the only "no local machine" gap. | Better than the plan assumed; reduces risk for Phases 1–6. | ⬜ |
| 0 | Gate runs `cap sync android` but **not** a full `gradlew assembleDebug`. | APK build is heavy and not required to prove the project wires up; emulator launch stays a Pending device-verification item per the plan. | ⬜ |
| 0 | Smoke spec drives into a practice quiz (3 mock questions: plain / code / latex) and asserts no horizontal overflow on each, beyond just the config shell. | Overflow from KaTeX/Shiki blocks is the top mobile-layout risk; cheap to cover now at 375px. | ⬜ |
| 0 | Smoke lives in its own `playwright.smoke.config.ts` at 375×812; main e2e (`testIgnore`) skips it. | Keeps the 375px gate concern separate from the Pixel-7 functional e2e. | ⬜ |

---

## 3. Capacitor Plugins table

| Plugin | Purpose | Phase | Status |
|--------|---------|:----:|:----:|
| `@capacitor/core` + `@capacitor/cli` | Runtime + native build CLI | 0 | ✅ |
| `@capacitor/android` | Android platform | 0 | ✅ |
| `@capacitor/ios` | iOS platform | 7 | ⬜ |
| `@capacitor/status-bar` | Overlay status bar, style for dark mode | 1 | ⬜ |
| `@capacitor/splash-screen` | Splash control / hide on ready | 1 | ⬜ |
| `@capacitor/keyboard` | `resize:native`, `keyboardWillShow` → hide bottom tab bar | 1 | ⬜ |
| `@capacitor/app` | Android hardware back button, app state | 1 | ⬜ |
| `@capacitor/filesystem` | Write export file to cache dir (rule 6) | 4 | ⬜ |
| `@capacitor/share` | Native share sheet for export (rule 6) | 4 | ⬜ |
| `@capacitor/browser` | External redirects / OAuth / payments (rule 7) | 5 | ⬜ |

---

## 4. Non-negotiable Capacitor rules (bake in from the first screen — device-confirmed traps)

1. **Navigation: ONLY Next's client router** (`router.push`/`router.replace`/`<Link>`), never `window.location.*` for in-app nav. Static export writes `foo.html` not `foo/index.html`, so a hard nav 404s to a blank WebView page and drops chrome. Cast `next`-query paths `as Route`.
2. **Safe-area insets on the FIXED bars, not `body`** (`body` padding fights `position:fixed`). Topbar `padding-top: env(safe-area-inset-top)`, bottom nav `padding-bottom: env(safe-area-inset-bottom)`, content column reserves both. **Prereq:** a `viewport` export with `viewportFit:"cover"` in `app/layout.tsx`, or `env()` returns 0 and notch handling silently no-ops.
3. **Android WebView reports `env(safe-area-inset-top)=0`** even with viewport-fit cover + overlay status bar (iOS reports real values). Floor it **native-only**: `components/mobile/platform-class.tsx` sets `.native-app` on `<html>` when `Capacitor.isNativePlatform()`, then `.native-app .<fixed-bar> { padding-top: max(env(safe-area-inset-top), 24px) }`. A floor on mobile-web would add dead space.
4. **Click-outside / menu-close listeners use `pointerdown`, not `mousedown`** (mouse fires pointer events so desktop is unchanged; iOS Safari is unreliable synthesizing mousedown on divs). Custom select/option taps use `onPointerDown`.
5. **Soft keyboard:** `@capacitor/keyboard`, `resize:native`. On `keyboardWillShow`, hide the bottom tab bar via a `keyboard-open` body class — don't float it above the keyboard. Mount **one** global keyboard listener in `layout.tsx`, native-guarded; don't duplicate per screen.
6. **File downloads** (export results/PDF/TXT): a WebView can't trigger a browser download. Branch on `Capacitor.isNativePlatform()` → write to cache dir + open native share sheet (`@capacitor/filesystem` + `@capacitor/share`, dynamically imported); web keeps the browser download.
7. **External redirects** (payments, OAuth, off-origin): open via `@capacitor/browser` (`Browser.open`), never navigate the app WebView to an external URL — it discards the app + session with no way back.
8. **Inputs ≥16px font** app-wide at mobile widths or iOS auto-zooms on focus. `html,body { overscroll-behavior:none }` for app-feel; `-webkit-touch-callout:none` on images/canvas.
9. **Android hardware back button:** `@capacitor/app` — step back through in-app history when `canGoBack`, else `App.exitApp()` at root. Global, native-guarded, no-op on web/iOS.
10. **Hover:** gate layout-affecting `:hover` behind `@media (hover:hover)`; use `:active` for tap feedback so sticky hover states don't linger after a tap.

---

## 5. Verification gate (run after EVERY phase — never trust the build alone)

1. `npm run build` — typecheck + static export must pass.
2. `nvm use 22 && npx cap sync android` — confirms the native project still wires up.
3. **375px smoke test** — `npm run smoke`: serves `out/`, loads public signed-out routes at 375px viewport, asserts **no uncaught JS / real console errors**, **no horizontal overflow** (content ≤ viewport width), **key element present**.
4. **Pending device verification** — auth-gated / device-only behavior (keyboard resize, share sheet, status-bar insets, camera) can't be headless-tested. List each under the phase's "Pending device verification" so it feeds the final Phase 8 E2E pass. **Never silently mark such items done.**

---

## 6. Per-phase checklists

### Phase 0 — Infra (shell first — everything depends on it)
- [ ] Install Capacitor 8 (`@capacitor/core`, `@capacitor/cli`, `@capacitor/android`).
- [ ] `capacitor.config.ts`: `webDir:'out'`, status bar overlay, splash, keyboard `resize:native`.
- [ ] Verify `output:'export'` produces a working `out/`.
- [ ] Commit `frontend/android/`; gitignore `out/`.
- [ ] Add `npm run smoke` script (serve `out/` + Playwright @375px).
- [ ] Document daily build command in this file.
- **Gate:** build + `cap sync android` + smoke.
- **Pending device verification:** app launches on Android emulator from `cap sync`.

### Phase 1 — Mobile shell & navigation
- [ ] Bottom-nav + mobile topbar; hide desktop sidebar at mobile widths.
- [ ] Safe-area insets on fixed bars (rules 2–3); `viewportFit:"cover"` viewport export.
- [ ] `platform-class.tsx` → `.native-app` + Android `env()=0` floor (rule 3).
- [ ] Splash + status-bar plugins wired (style matches dark mode).
- [ ] Global keyboard manager (rule 5) + back-button manager (rule 9), native-guarded, in `layout.tsx`.
- [ ] Tap-target pass (≥44×44).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** notch insets on a real device, status-bar overlay, hardware back.

### Phase 2 — Config / quiz-setup flow
- [ ] Create-exam / practice configuration screens (course, subtopic, count, difficulty, mode).
- [ ] Mobile input attrs: `autoComplete`, `inputMode`, `autoCapitalize`; inputs ≥16px (rule 8).
- [ ] Touch-fixed selects (`onPointerDown`, rule 4).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** soft-keyboard behavior on focus, select tap on iOS.

### Phase 3 — Exam runtime (one question per screen)
- [ ] Framer Motion question transitions.
- [ ] KaTeX math blocks `overflow-x:auto`; Shiki code blocks scroll horizontally.
- [ ] Zustand timer survives WebView backgrounding (recompute from `startedAt`, not interval ticks).
- [ ] Big tap targets for options; `:active` feedback (rule 10).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** timer accuracy after backgrounding, long-math/code horizontal scroll.

### Phase 4 — Practice feedback & scoring
- [ ] Result / feedback screens (score + per-question review).
- [ ] Share / export via rule 6 (native share sheet vs web download).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** share sheet opens with the exported file.

### Phase 5 — Account / settings / billing (likely N/A now — no auth)
- [ ] Settings screen (theme, etc.) if present.
- [ ] Any external redirect / payment via rule 7 (`Browser.open`).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** external browser returns to app cleanly.

### Phase 6 — Polish
- [ ] Safe-area sweep on a real notch.
- [ ] iOS input-zoom / overscroll / long-press audit.
- [ ] Android `env()=0` floor audit across **all** fixed chrome.
- [ ] Asset-size pass (no multi-MB images).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** full visual sweep on notch device.

### Phase 7 — iOS project + CI/CD
- [ ] `npx cap add ios`.
- [ ] GitHub Actions `macos-latest`: `npm install` → `npm run build` → `npx cap sync ios` → `xcodebuild` → artifact (no local Mac).
- [ ] TestFlight pipeline.
- [ ] Android APK build workflow.
- **Gate:** CI green; artifacts produced.
- **Pending device verification:** TestFlight install on a physical iPhone.

### Phase 8 — E2E
- [ ] Playwright suites (config flow, exam timer, practice feedback, scoring) green @375px.
- [ ] Full device checklist on Android emulator + iOS.
- [ ] Drain the entire accumulated "Pending device verification" backlog.
- [ ] Dark-mode pass (+ i18n if applicable).
- **Gate:** all suites green + device checklist signed off.
