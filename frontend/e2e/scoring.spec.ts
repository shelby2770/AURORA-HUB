import { test, expect } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { configureAndStart } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

// Correct indices: q1=1, q2=0, q3=1. Answer first two correctly, last wrong.
test("exam: answer all, finish, see score", async ({ page }) => {
  await configureAndStart(page, { mode: "exam" });
  const options = page.getByTestId("option");

  await options.nth(1).click(); // Q1 correct
  await page.getByTestId("next").click();

  await options.nth(0).click(); // Q2 correct
  await page.getByTestId("next").click();

  await options.nth(0).click(); // Q3 wrong (correct is 1)
  await page.getByTestId("finish").click();

  await expect(page).toHaveURL(/\/results/);
  await expect(page.getByTestId("score-value")).toHaveText("2 / 3");
  await expect(page.getByTestId("review-item")).toHaveCount(3);
});

test("results review shows correct/incorrect per question", async ({ page }) => {
  await configureAndStart(page, { mode: "exam" });
  const options = page.getByTestId("option");

  // Answer everything wrong (pick option 3 each, never correct).
  for (let i = 0; i < 3; i++) {
    await options.nth(3).click();
    const last = i === 2;
    await page.getByTestId(last ? "finish" : "next").click();
  }

  await expect(page).toHaveURL(/\/results/);
  await expect(page.getByTestId("score-value")).toHaveText("0 / 3");
  // Every review item carries an explanation panel.
  await expect(page.getByTestId("explanation")).toHaveCount(3);
});

test("new quiz returns to config", async ({ page }) => {
  await configureAndStart(page, { mode: "exam" });
  const options = page.getByTestId("option");
  for (let i = 0; i < 3; i++) {
    await options.nth(0).click();
    await page.getByTestId(i === 2 ? "finish" : "next").click();
  }
  await page.getByTestId("new-quiz").click();
  await expect(page).toHaveURL(/\/$|\/$/);
  await expect(page.getByTestId("course-select")).toBeVisible();
});
