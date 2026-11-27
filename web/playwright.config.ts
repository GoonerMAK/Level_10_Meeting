import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8100;
const WEB_PORT = 3100;
const API_URL = `http://localhost:${API_PORT}`;
const WEB_URL = `http://localhost:${WEB_PORT}`;

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e/results",
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  reporter: "list",
  use: {
    baseURL: WEB_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1400, height: 900 } } }],
  webServer: [
    {
      name: "API",
      command: "uv run python -m app.e2e_server",
      cwd: "../server",
      url: `${API_URL}/api/auth/users`,
      env: { E2E_API_PORT: String(API_PORT), WEB_ORIGIN: WEB_URL },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      name: "Web",
      command: `pnpm build && pnpm start --port ${WEB_PORT}`,
      url: `${WEB_URL}/sign-in`,
      env: { API_ORIGIN: API_URL },
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});
