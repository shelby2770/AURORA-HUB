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
| 1 | Mobile shell & navigation — safe-area, status bar, splash, keyboard + back managers | ✅ | No tab bar (linear flow); native bootstrap + safe-area on all fixed bars |
| 2 | Config / quiz-setup flow — touch-fixed selects, tap targets | ✅ | No free-text inputs; dropdown options ≥44px + 16px text |
| 3 | Exam runtime — one-per-screen, Framer Motion, KaTeX/Shiki overflow, timer survives backgrounding | ✅ | Built in web P3; added instant timer re-sync on app resume |
| 4 | Practice feedback & scoring — result screens, share/export (rule 6) | ✅ | Share button: native share sheet (cache file) vs web download |
| 5 | Account/settings/billing screens — payments via rule 7 (if applicable) | ✅ | **N/A** — no auth/accounts/billing; no external redirects to wire (rule 7) |
| 6 | Polish — real-notch safe-area, iOS zoom/overscroll, Android `env()=0` floor audit, asset sizes | ✅ | Toaster safe-area, fixed-chrome floor audit, hover gated by Tailwind v4, asset cleanup |
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
| 1 | **No bottom tab bar.** Phase 1 makes the existing linear-flow chrome native-correct instead of adding tabs. | User-selected; the app is Config→Quiz→Results with no sections to tab between (no history/settings screens). | ⬜ |
| 1 | Safe-area utilities are **additive** (`calc(env() + var(--safe-pad-*, 0))`) and set the per-bar base via a Tailwind arbitrary prop `[--safe-pad-top:1rem]`. | Lets each bar keep its visual padding with zero web regression (env()=0 on web), while the `.native-app` floor still applies the Android inset. | ⬜ |
| 1 | `keyboard-open` / `.hide-on-keyboard` infra is wired but **dormant** — the app currently has no free-text inputs (selects + buttons only). | Rule 5 says bake it in from the first screen; it activates automatically when/if text inputs are added. | ⬜ |
| 1 | **Hover gating (rule 10) deferred to Phase 6.** Kept Tailwind `hover:` utilities as-is for now. → **Resolved in Phase 6:** Tailwind v4 already gates all `hover:` behind `@media (hover:hover)` (verified in compiled CSS); nothing to rewrite. | All interactive elements already have `:active` feedback; a full `@media (hover:hover)` sweep is cheaper to do once in the polish phase than piecemeal. | ⬜ |
| 2 | Phase 2's text-input work is **N/A** — app has zero free-text inputs (selects + buttons only). Did the applicable parts instead: select option tap targets ≥44px and 16px text. | Can't add `inputMode`/`autoComplete` to inputs that don't exist; faking a text field to satisfy the checklist would be worse than documenting N/A. | ⬜ |
| 5 | **Phase 5 entirely N/A** — no settings/auth/billing screen built, `@capacitor/browser` not installed. | Spec excludes accounts/auth/payments; app is dark-only and stateless; grep shows no external links for rule 7. Fabricating these would contradict the spec. **Flagged: if you want a Settings/About screen, say so and I'll add one.** | ⬜ |

---

## 3. Capacitor Plugins table

| Plugin | Purpose | Phase | Status |
|--------|---------|:----:|:----:|
| `@capacitor/core` + `@capacitor/cli` | Runtime + native build CLI | 0 | ✅ |
| `@capacitor/android` | Android platform | 0 | ✅ |
| `@capacitor/ios` | iOS platform | 7 | ⬜ |
| `@capacitor/status-bar` | Overlay status bar, style for dark mode | 1 | ✅ |
| `@capacitor/splash-screen` | Splash control / hide on ready | 1 | ✅ |
| `@capacitor/keyboard` | `resize:native`, `keyboardWillShow` → `keyboard-open` class | 1 | ✅ |
| `@capacitor/app` | Android hardware back button, app state | 1 | ✅ |
| `@capacitor/filesystem` | Write export file to cache dir (rule 6) | 4 | ✅ |
| `@capacitor/share` | Native share sheet for export (rule 6) | 4 | ✅ |
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
- [x] ~~Bottom-nav + mobile topbar~~ → **N/A: no tab bar** (linear flow, user decision). Per-screen chrome made native-correct instead.
- [x] Safe-area insets on fixed bars (rules 2–3); `viewportFit:"cover"` viewport export (already present in `layout.tsx`).
- [x] `platform-class.tsx` → `.native-app` + Android `env()=0` floor (rule 3).
- [x] Splash + status-bar plugins wired (style matches dark mode) in `native-bootstrap.tsx`.
- [x] Global keyboard manager (rule 5) + back-button manager (rule 9), native-guarded, in `layout.tsx`.
- [x] Tap-target pass (≥44×44) — exit "✕" bumped 36→44px.
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** notch insets on a real device, status-bar overlay, hardware back.

### Phase 2 — Config / quiz-setup flow
- [x] Create-exam / practice configuration screens (course, subtopic, count, difficulty, mode) — built in web Phase 3.
- [x] ~~Mobile input attrs~~ → **N/A: no free-text inputs** (flow is selects + buttons only). Rule-8 iOS-zoom / `inputMode` / `autoComplete` have nothing to act on; revisit if a text field is ever added.
- [x] Touch-fixed selects — base-ui Select handles outside-close via pointer events (rule 4 satisfied). Bumped dropdown options to ≥44px + 16px text; trigger text to 16px.
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** soft-keyboard behavior on focus, select tap on iOS.

### Phase 3 — Exam runtime (one question per screen)
- [x] Framer Motion question transitions (`AnimatePresence` in quiz page).
- [x] KaTeX math blocks `overflow-x:auto` (`math-text` + latex block); Shiki code blocks scroll horizontally (`code-block`).
- [x] Zustand timer survives WebView backgrounding — recomputes from `startedAt` each tick **+ instant recompute on `visibilitychange`→visible** so it snaps on resume (no catch-up lag).
- [x] Big tap targets for options (`min-h-14`); `:active` feedback (rule 10).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** timer accuracy after backgrounding, long-math/code horizontal scroll.

### Phase 4 — Practice feedback & scoring
- [x] Result / feedback screens (score + per-question review) — built in web Phase 3.
- [x] Share / export via rule 6 — `lib/export-results.ts` builds a plain-text report; native writes it to the cache dir + opens the share sheet (`@capacitor/filesystem` + `@capacitor/share`, dynamically imported), web does an ordinary browser download. Share button on the results screen; user-cancelled share is swallowed (no error toast).
- **Gate:** build + `cap sync` + smoke.
- **Pending device verification:** share sheet opens with the exported file.

### Phase 5 — Account / settings / billing (N/A now — no auth)
- [x] ~~Settings screen~~ → **N/A.** App is intentionally dark-only (no theme toggle to expose) and stateless; no other settings exist to surface. Not fabricating a screen the spec excludes.
- [x] ~~External redirect / payment (rule 7)~~ → **N/A.** Grep confirms zero external links / `window.open` / off-origin anchors in `src/`, so `Browser.open` has nothing to wire. `@capacitor/browser` intentionally **not** installed yet — add it the moment a real external link (payments/OAuth/docs) appears.
- **Gate:** no code change → covered by the Phase 4 gate (build + `cap sync` + smoke + e2e all green).
- **Pending device verification:** none (nothing built).

### Phase 6 — Polish
- [x] Safe-area sweep — added native safe-area offset for the sonner Toaster (top-center portal) so toasts clear the overlay status bar. Real-notch visual confirmation stays Pending (device).
- [x] iOS input-zoom / overscroll / long-press — `overscroll-behavior:none` + `-webkit-touch-callout:none` on media (Phase 1, rule 8); input-zoom N/A (no text inputs). iOS-specific behavior Pending (device).
- [x] Android `env()=0` floor audit — all fixed/sticky chrome carries safe classes: quiz header/footer, config & results CTAs, config/results scroll columns, and now the Toaster. No un-floored fixed chrome remains.
- [x] Asset-size pass — removed the 5 unused `create-next-app` placeholder SVGs; no raster images anywhere, icons are lucide SVG. Nothing multi-MB.
- [x] **Hover gating (rule 10) — resolved.** Confirmed in compiled CSS that Tailwind v4 already wraps every `hover:` utility in `@media (hover: hover)` by default; no hand-written hover rules exist. The Phase 1 deferral is closed — nothing to rewrite.
- **Gate:** build + `cap sync` + smoke + e2e (12) + eslint, all green.
- **Pending device verification:** full visual sweep on a notch device (toasts, insets, overscroll).

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
