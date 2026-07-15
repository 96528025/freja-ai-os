import { expect, test } from "@playwright/test";

test("desktop supports the focused brief workflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Desktop workflow runs in the desktop project.");
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "你的 AI 每日简报" })).toBeVisible();
  await expect(page.getByRole("list", { name: "简报流程" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "选择来源" })).toBeVisible();
  await expect(page.getByRole("button", { name: "全选" })).toBeVisible();
  await expect(page.getByRole("button", { name: "全不选" })).toBeVisible();
  await expect(page.getByRole("button", { name: /生成简报/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "今日简报" })).toBeVisible();

  const firstOriginal = page.locator(".brief-markdown a").first();
  if (await firstOriginal.isVisible()) {
    await expect(firstOriginal).toHaveAttribute("target", "_blank");
    await expect(firstOriginal).toHaveAttribute("rel", "noopener noreferrer");
  }

  await page.screenshot({ path: "test-results/freja-desktop.png", fullPage: true });
});

test("mobile workflow fits without horizontal overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "Mobile workflow runs in the mobile project.");
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "你的 AI 每日简报" })).toBeVisible();
  await expect(page.getByRole("button", { name: /生成简报/ })).toBeVisible();
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(hasOverflow).toBe(false);
  await page.screenshot({ path: "test-results/freja-mobile.png", fullPage: true });
});

test("source selection shows only current product sources", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Source checks run in the desktop project.");
  await page.goto("/");

  await expect(page.getByLabel("Include Reddit")).toBeVisible();
  await expect(page.getByLabel("Include 小红书 / Rednote")).toBeVisible();
  await expect(page.getByLabel("Include OpenAI Blog")).toBeVisible();
  await expect(page.getByLabel("Include GitHub Trending")).toBeVisible();
  await expect(page.getByText("Twitter / X", { exact: true })).toHaveCount(0);
  await expect(page.getByText("LinkedIn", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Hacker News", { exact: true })).toHaveCount(0);

  await page.screenshot({ path: "test-results/freja-sources.png", fullPage: true });
});
