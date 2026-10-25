import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://127.0.0.1:5173", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    { command: "npm run dev -- --host 127.0.0.1", url: "http://127.0.0.1:5173", reuseExistingServer: true },
    { command: "python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000", cwd: "../backend", url: "http://127.0.0.1:8000/api/v1/health", reuseExistingServer: true },
  ],
});
