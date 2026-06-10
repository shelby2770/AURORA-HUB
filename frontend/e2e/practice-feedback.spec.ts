import { test, expect } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { configureAndStart } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

test("practice mode reveals feedback after answering", async ({ page }) => {
  await configureAndStart(page, { mode: "practice" });

  // No explanation before answering.
  await expect(page.getByTestId("explanation")).toHaveCount(0);

  // Q1 correct index is 1; pick the wrong option 0.
  const options = page.getByTestId("option");
  await options.nth(0).click();

  // Explanation appears; correct option is highlighted, chosen one marked wrong.
  await expect(page.getByTestId("explanation")).toBeVisible();
  await expect(options.nth(0)).toHaveAttribute("data-state", "incorrect");
  await expect(options.nth(1)).toHaveAttribute("data-state", "correct");

  // Selection is locked after answering: other options are disabled + muted.
  await expect(options.nth(2)).toBeDisabled();
  await expect(options.nth(2)).toHaveAttribute("data-state", "muted");
});

test("practice feedback shows correct selection as correct", async ({
  page,
}) => {
  await configureAndStart(page, { mode: "practice" });
  const options = page.getByTestId("option");
  await options.nth(1).click(); // correct answer for Q1
  await expect(page.getByTestId("explanation")).toContainText("Correct");
  await expect(options.nth(1)).toHaveAttribute("data-state", "correct");
});
