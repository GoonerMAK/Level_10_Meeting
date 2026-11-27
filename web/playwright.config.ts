import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8001;
const WEB_PORT = 3001;
const WEB_URL = `http://localhost:${WEB_PORT}`;

export default defineConfig({
  testDir: "e2e",
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: WEB_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      name: "api",
      command: `bash ../tools/e2e-server.sh ${API_PORT}`,
      url: `http://localhost:${API_PORT}/docs`,
      env: { WEB_ORIGIN: WEB_URL },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      name: "web",
      command: `pnpm build && pnpm start --port ${WEB_PORT}`,
      url: WEB_URL,
      env: { API_ORIGIN: `http://localhost:${API_PORT}` },
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});
