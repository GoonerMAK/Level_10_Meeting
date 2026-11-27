import { expect, test, type Browser, type Page } from "@playwright/test";

const TEAM_PAGE = "/teams/team_lead";
const FOLLOWS_WITHIN = { timeout: 2_000 };

async function signedIn(browser: Browser, name: string): Promise<Page> {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto("/sign-in");
  await page.getByRole("button", { name }).click();
  await page.waitForURL(/\/teams\//);
  await page.goto(TEAM_PAGE);
  return page;
}

const sectionHeading = (page: Page, section: string) => page.getByRole("heading", { level: 1, name: section });

test("the facilitator advances the agenda and the second browser follows", async ({ browser }) => {
  const blake = await signedIn(browser, "Blake Brooks");
  const ellis = await signedIn(browser, "Ellis Evans");

  await blake.getByRole("button", { name: "Start meeting" }).click();
  await expect(sectionHeading(blake, "Scorecard")).toBeVisible();

  await ellis.getByRole("link", { name: "Join meeting · Scorecard" }).click(FOLLOWS_WITHIN);
  await expect(sectionHeading(ellis, "Scorecard")).toBeVisible();
  await expect(ellis.getByText("Blake Brooks runs this meeting")).toBeVisible();
  await expect(blake.getByRole("list", { name: "Attendees" })).toContainText("Ellis Evans", FOLLOWS_WITHIN);

  for (const section of ["IDS", "Conclude"]) {
    await blake.getByRole("button", { name: `Next: ${section}` }).click();
    await expect(sectionHeading(blake, section)).toBeVisible();
    await expect(sectionHeading(ellis, section)).toBeVisible(FOLLOWS_WITHIN);
    await expect(ellis.getByRole("list", { name: "Agenda" }).locator('[aria-current="step"]')).toContainText(section);
    await expect(ellis.getByRole("button", { name: /^Next:/ })).toHaveCount(0);
    await expect(ellis.getByRole("button", { name: "End meeting" })).toHaveCount(0);
  }

  await blake.getByRole("button", { name: "End meeting" }).click();
  await blake.getByRole("dialog").getByRole("button", { name: "End meeting" }).click();
  await expect(sectionHeading(blake, "Meeting summary")).toBeVisible();
  await expect(sectionHeading(ellis, "Meeting summary")).toBeVisible(FOLLOWS_WITHIN);
});
