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
