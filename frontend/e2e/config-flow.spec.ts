import { test, expect } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { selectCourse } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

test("config flow: build a quiz and start it", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Aurora Hub" })).toBeVisible();

  // Start is disabled until a course is chosen.
  await expect(page.getByTestId("start-quiz")).toBeDisabled();

  await selectCourse(page, "Operating Systems");
  await page.getByTestId("count-20").click();
  await page.getByTestId("difficulty-hard").click();
  await page.getByTestId("mode-exam").click();

  await expect(page.getByTestId("start-quiz")).toBeEnabled();
  await page.getByTestId("start-quiz").click();

  await expect(page).toHaveURL(/\/quiz/);
  await expect(page.getByTestId("progress-label")).toHaveText(
    "Question 1 / 3",
  );
  await expect(page.getByTestId("timer")).toBeVisible();
});

test("whole-course scope exposes the 50 option", async ({ page }) => {
  await page.goto("/");
  await selectCourse(page, "Operating Systems");
  // Default subtopic is "Whole course" → 50 available.
  await expect(page.getByTestId("count-50")).toBeVisible();
});
