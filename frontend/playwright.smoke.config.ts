import { defineConfig } from "@playwright/test";

// Phase 0 mobile smoke: load the static export at a small (375px) phone width
// and assert no uncaught JS / real console errors, no horizontal overflow, and
// that key content renders. This is the cheap headless proxy for "the WebView
// shell works" — device-only behavior is tracked separately in MOBILE.md.
export default defineConfig({
  testDir: "./e2e",
  testMatch: /smoke\.spec\.ts$/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    // 375×812 = iPhone SE / smallest common phone width we must not overflow.
    viewport: { width: 375, height: 812 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    trace: "on-first-retry",
  },
  webServer: {
    command: "npx serve out -l 3000 --no-clipboard",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
