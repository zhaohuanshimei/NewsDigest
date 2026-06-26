import { expect, test } from "@playwright/test";

test.describe("E2E main flow", () => {
  test("1. Homepage loads and displays the latest digest", async ({ page }) => {
    await page.goto("/");

    // Verify the page title
    await expect(page).toHaveTitle("News Digest");

    // Verify navigation links exist
    await expect(page.locator('a[href="/"]')).toBeVisible();
    await expect(page.locator('a[href="/archive"]')).toBeVisible();
    await expect(page.locator('a[href="/rss"]')).toBeVisible();

    // Verify the digest date and headline are shown
    await expect(page.locator("text=2026-06-24")).toBeVisible();
    await expect(page.locator("text=AI 芯片与模型基础设施继续升温")).toBeVisible();
    await expect(page.locator("text=多家厂商围绕训练基础设施与推理部署发布新进展。")).toBeVisible();
  });

  test("2. Archive page lists digest dates", async ({ page }) => {
    await page.goto("/archive");

    // Verify the archive page title
    await expect(page).toHaveTitle("News Digest Archive");

    // Verify dates are listed
    await expect(page.locator("text=2026-06-24")).toBeVisible();
    await expect(page.locator("text=2026-06-23")).toBeVisible();
    await expect(page.locator("text=2026-06-22")).toBeVisible();
  });

  test("3. Cluster detail page renders from homepage link", async ({ page }) => {
    // Start at homepage
    await page.goto("/");

    // Click the digest entry headline to go to cluster detail
    await page.click('a[href="/clusters/cluster-ai-chip-001"]');

    // Verify the cluster detail is shown
    await expect(page).toHaveTitle("News Digest Cluster");
    await expect(page.locator("text=AI 芯片与模型基础设施继续升温")).toBeVisible();
    await expect(page.locator("text=多家厂商围绕训练基础设施与推理部署发布新进展，覆盖训练算力、推理成本与生态合作。")).toBeVisible();
  });

  test("4. RSS page describes subscription info", async ({ page }) => {
    await page.goto("/rss");

    // Verify the RSS page
    await expect(page).toHaveTitle("RSS 订阅 | News Digest");
    await expect(page.locator("text=RSS 订阅")).toBeVisible();
    await expect(page.locator("text=/feed.xml")).toBeVisible();
  });

  test("5. RSS feed XML returns valid content", async ({ page }) => {
    const response = await page.goto("/feed.xml");

    // Verify it's served as XML
    expect(response.headers()["content-type"]).toMatch(/xml/);

    // Read the raw response body
    const body = await response.text();
    expect(body).toContain('<?xml version="1.0"');
    expect(body).toContain("<rss");
    expect(body).toContain("<channel>");
    expect(body).toContain("AI 芯片与模型基础设施继续升温");
    expect(body).toContain("多家厂商围绕训练基础设施与推理部署发布新进展");
  });

  test("6. Full flow: Home -> Cluster detail -> Archive -> RSS", async ({ page }) => {
    // Step 1: Start at homepage
    await page.goto("/");
    await expect(page.locator("text=AI 芯片与模型基础设施继续升温")).toBeVisible();

    // Step 2: Click digest headline to cluster detail
    await page.click('a[href="/clusters/cluster-ai-chip-001"]');
    await expect(page).toHaveTitle("News Digest Cluster");

    // Step 3: Navigate to archive via nav
    await page.click('a[href="/archive"]');
    await expect(page).toHaveTitle("News Digest Archive");

    // Step 4: Navigate to RSS page via nav
    await page.click('a[href="/rss"]');
    await expect(page).toHaveTitle("RSS 订阅 | News Digest");

    // Step 5: Check feed XML
    const response = await page.goto("/feed.xml");
    const body = await response.text();
    expect(body).toContain("<channel>");
    expect(body).toContain("AI 芯片与模型基础设施继续升温");
  });
});
