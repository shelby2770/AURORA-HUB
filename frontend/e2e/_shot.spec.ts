import { test } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { selectCourse } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

test("shot", async ({ page }) => {
  await page.goto("/");
  await selectCourse(page, "Operating Systems");
  await page.waitForTimeout(400);
  await page.screenshot({ path: "test-results/shot-setup.png" });
});
