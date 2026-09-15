import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  timeout: 20000,
  use: {
    baseURL: "http://127.0.0.1:5192",
    channel: "chrome",
    headless: true,
    viewport: { width: 1120, height: 820 },
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:5192",
    reuseExistingServer: false,
  },
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
});
