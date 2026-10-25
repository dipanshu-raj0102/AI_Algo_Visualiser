import { expect, test } from "@playwright/test";

test("landing page and algorithm library are navigable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Understand AI algorithms/i })).toContainText("Understand AI algorithms");
  await page.getByRole("link", { name: "Explore" }).click();
  await expect(page.getByRole("heading", { name: /Explore the systems/i })).toContainText("Explore the systems");
});

test("comparison workspace presents its shared-problem action", async ({ page }) => {
  await page.goto("/comparison");
  await expect(page.getByRole("heading", { name: /Compare algorithms/i })).toContainText("Compare algorithms");
  await expect(page.getByRole("button", { name: /Run A\* vs Greedy/i })).toContainText("Run A* vs Greedy");
});

test("visualizer exposes playback controls", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /Launch workspace/i }).click();
  await expect(page.getByRole("heading", { name: /Watch the search frontier/i })).toContainText("Watch the search frontier");
  await expect(page.getByRole("button", { name: /Run astar-grid/i })).toContainText("Run astar-grid");
});

test("A* heuristic comparison runs four synchronized traces", async ({ page }) => {
  await page.goto("/compare/astar-heuristics");
  await expect(page.getByRole("heading", { name: /Same map\. Four ways/i })).toContainText("Same map");
  await expect(page.getByRole("button", { name: "Run comparison" })).toBeVisible();
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByRole("heading", { name: "Manhattan" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("heading", { name: "Euclidean" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Chebyshev" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Zero / Dijkstra" })).toBeVisible();
  const progress = page.getByRole("progressbar");
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
  await page.getByRole("button", { name: /Resume comparison/i }).click();
  await page.waitForTimeout(450);
  await expect(progress).toHaveAttribute("aria-valuenow", /[1-9][0-9]?/);
  await page.getByRole("button", { name: /Pause comparison/i }).click();
  await page.getByRole("button", { name: "Fast-forward comparison" }).click();
  await page.getByRole("button", { name: "Restart comparison" }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
});
