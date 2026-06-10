import { expect, type Page } from "@playwright/test";

export async function selectCourse(page: Page, name: string) {
  await page.getByTestId("course-select").click();
  await page.getByRole("option", { name }).click();
}

export async function configureAndStart(
  page: Page,
  opts: { mode: "exam" | "practice"; count?: number; difficulty?: string },
) {
  await page.goto("/");
  await selectCourse(page, "Operating Systems");
  await page.getByTestId(`count-${opts.count ?? 10}`).click();
  await page.getByTestId(`difficulty-${opts.difficulty ?? "medium"}`).click();
  await page.getByTestId(`mode-${opts.mode}`).click();
  await page.getByTestId("start-quiz").click();
  await expect(page).toHaveURL(/\/quiz/);
  await expect(page.getByTestId("progress-label")).toBeVisible();
}

export function parseClock(text: string): number {
  const m = text.match(/(\d+):(\d{2})/);
  if (!m) throw new Error(`not a clock: ${text}`);
  return Number(m[1]) * 60 + Number(m[2]);
}
