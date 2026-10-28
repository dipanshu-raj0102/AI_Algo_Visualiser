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
  await expect(progress).not.toHaveAttribute("aria-valuenow", "0", { timeout: 5_000 });
  await page.getByRole("button", { name: /Pause comparison/i }).click();
  await page.getByRole("button", { name: "Fast-forward comparison" }).click();
  await page.getByRole("button", { name: "Restart comparison" }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
});

test("A* detail page links to the heuristic impact analysis", async ({ page }) => {
  await page.goto("/algorithms/astar-grid");
  const analysisLink = page.getByRole("link", { name: "Heuristic impact analysis", exact: true });
  await expect(analysisLink).toBeVisible({ timeout: 10_000 });
  await analysisLink.click();
  await expect(page.getByRole("heading", { name: /Same map\. Four ways/i })).toBeVisible();
});

test("comparison exposes measured analytics and complete metrics", async ({ page }) => {
  await page.goto("/compare/astar-heuristics");
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByRole("heading", { name: "Manhattan" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("heading", { name: /See the search effort/i })).toBeVisible();
  await expect(page.getByText("EXPANDED NODES", { exact: true })).toBeVisible();
  await expect(page.getByText("FRONTIER PROGRESSION", { exact: true })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Events" })).toBeVisible();
  await expect(page.getByText(/unit cost for each orthogonal move/)).toBeVisible();
  await expect(page.getByText("|dr| + |dc|", { exact: true }).first()).toBeVisible();
});

test("comparison controller steps, accelerates, and finishes real traces", async ({ page }) => {
  await page.goto("/compare/astar-heuristics");
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByRole("heading", { name: "Manhattan" })).toBeVisible({ timeout: 15_000 });
  const progress = page.getByRole("progressbar");
  const stepCounter = page.locator(".hcx-progress-wrap .mono");
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
  await expect(stepCounter).toHaveText(/1 \/ \d+/);
  await page.getByRole("button", { name: "Step forward" }).click();
  await expect(stepCounter).toHaveText(/2 \/ \d+/);
  await page.getByRole("button", { name: "Step backward" }).click();
  await expect(stepCounter).toHaveText(/1 \/ \d+/);
  const speed = page.getByRole("combobox", { name: "Playback speed" });
  await speed.selectOption("0.25");
  const slowStart = Date.now();
  await page.getByRole("button", { name: "Resume comparison" }).click();
  await expect(stepCounter).toHaveText(/2 \/ \d+/, { timeout: 3_000 });
  const slowElapsed = Date.now() - slowStart;
  await page.getByRole("button", { name: "Restart comparison" }).click();
  await speed.selectOption("8");
  const fastStart = Date.now();
  await page.getByRole("button", { name: "Resume comparison" }).click();
  await expect(stepCounter).toHaveText(/2 \/ \d+/, { timeout: 1_000 });
  const fastElapsed = Date.now() - fastStart;
  expect(fastElapsed).toBeLessThan(slowElapsed);
  await page.getByRole("button", { name: /Pause comparison/i }).click();
  await page.getByRole("button", { name: "Restart comparison" }).click();
  await page.getByRole("button", { name: "Fast-forward comparison" }).click();
  await expect(progress).not.toHaveAttribute("aria-valuenow", "0");
  await page.getByRole("button", { name: "Finish" }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "100");
});

test("comparison panels stack without horizontal overflow on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/compare/astar-heuristics");
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByRole("heading", { name: "Manhattan" })).toBeVisible({ timeout: 15_000 });
  const layout = await page.locator(".hcx-panel-grid").evaluate((element) => getComputedStyle(element).gridTemplateColumns);
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(layout.split(" ").length).toBe(1);
  expect(hasOverflow).toBe(false);
  await expect(page.getByRole("button", { name: "Run comparison" })).toBeVisible();
});

test("generic visualizer uses the shared playback transitions", async ({ page }) => {
  await page.goto("/visualizer/astar-grid");
  await page.getByRole("button", { name: /Run astar-grid/i }).click();
  await expect(page.getByRole("progressbar")).toBeVisible({ timeout: 15_000 });
  const progress = page.getByRole("progressbar");
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
  await page.getByRole("button", { name: "Next step" }).click();
  await expect(progress).not.toHaveAttribute("aria-valuenow", "0");
  await page.getByRole("button", { name: "Previous step" }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
});

test("reduced motion preserves keyboard playback controls", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/compare/astar-heuristics");
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByRole("heading", { name: "Manhattan" })).toBeVisible({ timeout: 15_000 });
  const transitionDuration = await page.locator(".hcx-progress span").evaluate((element) => getComputedStyle(element).transitionDuration);
  const durationMs = transitionDuration.endsWith("ms") ? Number.parseFloat(transitionDuration) : Number.parseFloat(transitionDuration) * 1000;
  expect(durationMs).toBeLessThanOrEqual(0.01);
  const stepCounter = page.locator(".hcx-progress-wrap .mono");
  await page.getByRole("button", { name: "Step forward" }).focus();
  await page.keyboard.press("Enter");
  await expect(stepCounter).toHaveText(/2 \/ \d+/);
});

test("comparison retains the application dark theme tokens", async ({ page }) => {
  await page.goto("/compare/astar-heuristics");
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await expect(page.locator(".app-shell.dark")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Same map\. Four ways/i })).toBeVisible();
});
