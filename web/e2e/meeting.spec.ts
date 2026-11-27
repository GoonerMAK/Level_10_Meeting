import { expect, test, type Browser, type Page } from "@playwright/test";

const TEAM = "team_sales";
const LIVE = { timeout: 1_500 };

async function signIn(browser: Browser, name: string): Promise<Page> {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto("/sign-in");
  await page.getByRole("button", { name: new RegExp(`^${name}`) }).click();
  await page.waitForURL(`**/teams/${TEAM}`);
  return page;
}

const sectionHeading = (page: Page) => page.getByRole("heading", { level: 1 });

test("the facilitator runs a meeting and a second browser follows it live", async ({ browser }) => {
  const facilitator = await signIn(browser, "Finley Ford");
  const observer = await signIn(browser, "Gray Green");

  await test.step("the facilitator starts the meeting from the Team page", async () => {
    await facilitator.getByRole("button", { name: "Start meeting" }).click();
    await facilitator.waitForURL(`**/teams/${TEAM}/meeting`);
    await expect(sectionHeading(facilitator)).toHaveText("Scorecard");
    await expect(facilitator.getByRole("timer")).toHaveAccessibleName(/left in Scorecard/);
  });

  await test.step("the Observer joins and follows read-only", async () => {
    await observer.getByRole("link", { name: /Join meeting · Scorecard/ }).click();
    await expect(sectionHeading(observer)).toHaveText("Scorecard");
    await expect(observer.getByText("Finley Ford runs this meeting")).toBeVisible();
    await expect(observer.getByRole("button", { name: /^Next:/ })).toHaveCount(0);
    await expect(observer.getByRole("button", { name: "End meeting" })).toHaveCount(0);
    await expect(facilitator.getByRole("list", { name: "Attendees" })).toContainText("Gray Green", LIVE);
  });

  await test.step("Next moves the second browser to IDS", async () => {
    await facilitator.getByRole("button", { name: "Next: IDS" }).click();
    await expect(sectionHeading(observer)).toHaveText("IDS", LIVE);
    await expect(observer.getByRole("timer")).toHaveAccessibleName(/left in IDS/);
  });

  await test.step("an Issue added in IDS reaches the second browser", async () => {
    await facilitator.getByRole("button", { name: "New Issue" }).click();
    await facilitator.getByLabel("Title").fill("Lead form drops submissions");
    await facilitator.getByRole("button", { name: "Add Issue" }).click();
    await expect(observer.getByText("Lead form drops submissions")).toBeVisible(LIVE);
  });

  await test.step("Next moves the second browser to Conclude", async () => {
    await facilitator.getByRole("button", { name: "Next: Conclude" }).click();
    await expect(sectionHeading(observer)).toHaveText("Conclude", LIVE);
    await expect(facilitator.getByRole("button", { name: /^Next:/ })).toHaveCount(0);
  });

  await test.step("the facilitator rates and the Observer can't", async () => {
    await expect(observer.getByRole("group", { name: "Your rating" })).toHaveCount(0);
    await facilitator.getByRole("group", { name: "Your rating" }).getByRole("button", { name: "8", exact: true }).click();
    await expect(observer.getByText("8.0", { exact: true })).toBeVisible(LIVE);
  });

  await test.step("ending the meeting shows both browsers the summary", async () => {
    await facilitator.getByRole("button", { name: "End meeting" }).click();
    await facilitator.getByRole("dialog").getByRole("button", { name: "End meeting" }).click();
    await expect(sectionHeading(facilitator)).toHaveText("Meeting summary");
    await expect(sectionHeading(observer)).toHaveText("Meeting summary", LIVE);
    await expect(observer.getByText("Rating from 1")).toBeVisible();
    await expect(observer.getByRole("list", { name: "Attendees" })).toContainText("Finley Ford · 8");
  });
});
