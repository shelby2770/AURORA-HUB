import { test, expect } from "@playwright/test";
import { setupApiMocks, setupModelTestMocks } from "./mocks";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
  await setupModelTestMocks(page);
});

test("home entry card opens the model-test list", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("model-test-entry").click();
  await expect(page).toHaveURL(/\/model-test/);
  await expect(page.getByTestId("model-test-card")).toHaveCount(1);
});

test("start withholds answers; timer runs in exam style", async ({ page }) => {
  await page.goto("/model-test/");
  await page.getByTestId("model-test-card").click();
  await expect(page).toHaveURL(/\/model-test\/run/);
  await expect(page.getByTestId("progress-label")).toBeVisible();
  // 90-minute exam timer is shown and counting (no answers revealed yet).
  await expect(page.getByTestId("timer")).toBeVisible();
});

test("answer all, finish, see marks and pass/fail + subject breakdown", async ({
  page,
}) => {
  await page.goto("/model-test/");
  await page.getByTestId("model-test-card").click();
  const options = page.getByTestId("option");

  await options.nth(1).click(); // Q1 correct
  await page.getByTestId("next").click();
  await options.nth(0).click(); // Q2 correct
  await page.getByTestId("next").click();
  await options.nth(1).click(); // Q3 correct
  await page.getByTestId("finish").click();

  await expect(page).toHaveURL(/\/model-test\/result/);
  await expect(page.getByTestId("marks-value")).toHaveText("9 / 9 marks");
  await expect(page.getByTestId("verdict")).toHaveText("Passed");
  await expect(page.getByTestId("subject-row")).toHaveCount(3);
  await expect(page.getByTestId("review-item")).toHaveCount(3);
});

test("failing score shows 'Not passed'", async ({ page }) => {
  await page.goto("/model-test/");
  await page.getByTestId("model-test-card").click();
  const options = page.getByTestId("option");

  // Answer every question wrong (option index 2 is never correct here).
  for (let i = 0; i < 3; i++) {
    await options.nth(2).click();
    await page.getByTestId(i === 2 ? "finish" : "next").click();
  }

  await expect(page).toHaveURL(/\/model-test\/result/);
  await expect(page.getByTestId("verdict")).toHaveText("Not passed");
  await expect(page.getByTestId("marks-value")).toHaveText("0 / 9 marks");
});
