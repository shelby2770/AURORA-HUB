import { test, expect } from "@playwright/test";
import { setupApiMocks } from "./mocks";
import { configureAndStart } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setupApiMocks(page);
});

// Web branch of rule 6: a WebView can't download, but on the web the Share
// button must produce an ordinary browser download with the report.
test("share on web triggers a results download", async ({ page }) => {
  await configureAndStart(page, { mode: "exam" });
  const options = page.getByTestId("option");
  await options.nth(1).click(); // Q1 correct
  await page.getByTestId("next").click();
  await options.nth(0).click(); // Q2 correct
  await page.getByTestId("next").click();
  await options.nth(1).click(); // Q3 correct
  await page.getByTestId("finish").click();

  await expect(page).toHaveURL(/\/results/);

  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("share-results").click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe("aurora-hub-results.txt");

  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const c of stream) chunks.push(c as Buffer);
  const text = Buffer.concat(chunks).toString("utf8");

  expect(text).toContain("Aurora Hub — Quiz Results");
  expect(text).toContain("Score: 3 / 3");
  expect(text).toMatch(/Q1\.\s+\[CORRECT\]/);
});
