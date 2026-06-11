import { defineConfig, devices } from "@playwright/test";

// Web e2e for Phase 3. The backend is mocked via page.route in each spec, so
// these run against the client SPA alone (no FastAPI/Mongo needed).
export default defineConfig({
  testDir: "./e2e",
  // The mobile smoke runs under playwright.smoke.config.ts (375px) via `npm run smoke`.
  testIgnore: /smoke\.spec\.ts$/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 7"] },
    },
  ],
  // Serve the real static export (the artifact Capacitor ships), not `next dev`.
  // Run `npm run build` first; the `pretest:e2e` script does this automatically.
  webServer: {
    command: "npx serve out -l 3000 --no-clipboard",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
