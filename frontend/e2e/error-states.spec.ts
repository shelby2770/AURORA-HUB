import { test, expect, type Route } from "@playwright/test";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function preflight(route: Route) {
  return route.fulfill({ status: 204, headers: CORS });
}

test("backend unreachable: shows error with a working retry", async ({ page }) => {
  let attempt = 0;
  await page.route("**/courses", (route) => {
    if (route.request().method() === "OPTIONS") return preflight(route);
    attempt += 1;
    // Fail the first round (initial + retry:1), then succeed on user retry.
    if (attempt <= 2) return route.fulfill({ status: 500, headers: CORS });
    return route.fulfill({
      status: 200,
      headers: { "Content-Type": "application/json", ...CORS },
      body: JSON.stringify([
        { id: "c1", name: "Operating Systems", slug: "operating-systems", isActive: true },
      ]),
    });
  });

  await page.goto("/");

  const errorPanel = page.getByTestId("courses-error");
  await expect(errorPanel).toBeVisible();
  await expect(errorPanel).toHaveAttribute("role", "alert");

  await page.getByTestId("courses-retry").click();

  // Recovered → the real config form (course picker) is shown.
  await expect(page.getByTestId("course-select")).toBeVisible();
  await expect(page.getByTestId("courses-error")).toHaveCount(0);
});

test("database not seeded: shows the empty state with seed hint", async ({ page }) => {
  await page.route("**/courses", (route) => {
    if (route.request().method() === "OPTIONS") return preflight(route);
    return route.fulfill({
      status: 200,
      headers: { "Content-Type": "application/json", ...CORS },
      body: JSON.stringify([]),
    });
  });

  await page.goto("/");

  const empty = page.getByTestId("courses-empty");
  await expect(empty).toBeVisible();
  await expect(empty).toContainText("seed");
  await expect(page.getByTestId("course-select")).toHaveCount(0);
});
