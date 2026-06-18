import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:3000",
    trace: process.env.CI ? "on-first-retry" : "retain-on-failure",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: "uvicorn backend.main:app --host 0.0.0.0 --port 8765",
      cwd: "../",
      port: 8765,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
      env: {
        DISABLE_RATE_LIMIT: "1",
        JWT_SECRET: "test-secret-for-e2e-tests-only-abcdef123456",
        DATA_DIR: "./data",
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      // CI: serve the static build (output: 'export'). Local: dev server.
      command: process.env.CI
        ? "npx serve out -p 3000 --single --no-clipboard"
        : "npm run dev",
      port: 3000,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
