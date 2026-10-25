# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: platform.spec.ts >> visualizer exposes playback controls
- Location: e2e/platform.spec.ts:16:1

# Error details

```
Error: page.goto: Target page, context or browser has been closed
Call log:
  - navigating to "http://127.0.0.1:5173/visualizer/astar-grid", waiting until "load"

```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | test("landing page and algorithm library are navigable", async ({ page }) => {
  4  |   await page.goto("/");
  5  |   await expect(page.getByRole("heading", { name: /Understand AI algorithms/i })).toContainText("Understand AI algorithms");
  6  |   await page.getByRole("link", { name: "Explore" }).click();
  7  |   await expect(page.getByRole("heading", { name: /Explore the systems/i })).toContainText("Explore the systems");
  8  | });
  9  | 
  10 | test("comparison workspace presents its shared-problem action", async ({ page }) => {
  11 |   await page.goto("/comparison");
  12 |   await expect(page.getByRole("heading", { name: /Compare algorithms/i })).toContainText("Compare algorithms");
  13 |   await expect(page.getByRole("button", { name: /Run A\* vs Greedy/i })).toContainText("Run A* vs Greedy");
  14 | });
  15 | 
  16 | test("visualizer exposes playback controls", async ({ page }) => {
> 17 |   await page.goto("/visualizer/astar-grid");
     |              ^ Error: page.goto: Target page, context or browser has been closed
  18 |   await expect(page.getByRole("heading", { name: /Watch the search frontier/i })).toContainText("Watch the search frontier");
  19 |   await expect(page.getByRole("button", { name: /Run astar-grid/i })).toContainText("Run astar-grid");
  20 | });
  21 | 
```