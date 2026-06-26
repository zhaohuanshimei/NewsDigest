import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",

  use: {
    baseURL: "http://localhost:4321",
    trace: "on-first-retry",
    channel: "chrome",
    headless: true,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    command:
      "PUBLIC_DIGEST_STATE=success PUBLIC_ARCHIVE_STATE=success PUBLIC_CLUSTER_STATE=success npm run build && npm run preview -- --port 4321",
    port: 4321,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
});
