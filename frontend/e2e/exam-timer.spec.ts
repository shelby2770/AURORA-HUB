import { test, expect } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { configureAndStart, parseClock } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

test("exam timer is shown and counts down", async ({ page }) => {
  await configureAndStart(page, { mode: "exam" });

  const timer = page.getByTestId("timer");
  await expect(timer).toBeVisible();
  await expect(timer).toHaveText(/\d+:\d{2}/);

  const first = parseClock((await timer.textContent()) ?? "");
  await page.waitForTimeout(1800);
  const second = parseClock((await timer.textContent()) ?? "");

  expect(second).toBeLessThan(first);
});

test("practice mode has no timer", async ({ page }) => {
  await configureAndStart(page, { mode: "practice" });
  await expect(page.getByTestId("timer")).toHaveCount(0);
});
