import { test, expect, type Page } from "@playwright/test";
import { setupApiMocks } from "./mocks";

// Console/page errors that are not app bugs (browser-level noise). Keep tight.
const IGNORE = [/favicon/i, /Download the React DevTools/i];

function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (IGNORE.some((re) => re.test(text))) return;
    errors.push(`console: ${text}`);
  });
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  return errors;
}

// Fails if any element pushes the document wider than the viewport.
async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return {
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
    };
  });
  // 1px tolerance for sub-pixel rounding.
  expect(
    overflow.scrollWidth,
    `horizontal overflow: scrollWidth ${overflow.scrollWidth} > clientWidth ${overflow.clientWidth}`,
  ).toBeLessThanOrEqual(overflow.clientWidth + 1);
}

test("config screen renders at 375px with no overflow or errors", async ({ page }) => {
  const errors = watchErrors(page);
  await setupApiMocks(page);

  await page.goto("/");

  // Key element present.
  await expect(page.getByRole("heading", { name: "Aurora Hub" })).toBeVisible();
  await expect(page.getByTestId("course-select")).toBeVisible();

  await expectNoHorizontalOverflow(page);
  expect(errors, errors.join("\n")).toHaveLength(0);
});

test("quiz runtime renders at 375px with no overflow (math/code blocks)", async ({
  page,
}) => {
  const errors = watchErrors(page);
  await setupApiMocks(page);

  await page.goto("/");
  await page.getByTestId("course-select").click();
  await page.getByRole("option", { name: "Operating Systems" }).click();
  await page.getByTestId("mode-practice").click();
  await page.getByTestId("start-quiz").click();

  // Walk all three mock questions (plain, code snippet, latex block) — the
  // overflow-prone screens — checking width at each.
  await expect(page.getByTestId("progress-label")).toBeVisible();
  for (let i = 0; i < 3; i++) {
    await expect(page.getByTestId("options")).toBeVisible();
    await expectNoHorizontalOverflow(page);
    const next = page.getByTestId("next");
    if (await next.isVisible()) await next.click();
  }

  expect(errors, errors.join("\n")).toHaveLength(0);
});
