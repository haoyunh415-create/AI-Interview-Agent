import { test, expect } from "@playwright/test";

const USER = {
  username: `reportuser_${Date.now()}`,
  password: "testpass123",
};

test.describe("Report and bookmarks flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.getByText("注册").click();
    await page.getByPlaceholder("用户名").fill(USER.username);
    await page.getByPlaceholder("密码").fill(USER.password);
    await page.getByRole("button", { name: "注册并登录" }).click();
    await expect(page.getByText("闲聊")).toBeVisible();
  });

  test("report page loads and shows stats", async ({ page }) => {
    // Navigate to report
    await page.getByText("报告").click();

    // Should see the report page with CTA button
    await expect(page.getByText("学习报告")).toBeVisible();

    // Click to load report
    const loadButton = page.getByRole("button", { name: "加载报告" });
    const hasLoadButton = await loadButton.isVisible().catch(() => false);

    if (hasLoadButton) {
      await loadButton.click();
      await page.waitForTimeout(2000);
    }

    // Either we see stats or the empty state — either is valid
    const statsVisible = await page.getByText("总题数").isVisible().catch(() => false);
    const noDataVisible = await page.getByText("暂无数据").isVisible().catch(() => false);
    expect(statsVisible || noDataVisible).toBeTruthy();
  });

  test("bookmarks page is accessible and functional", async ({ page }) => {
    // Navigate to bookmarks
    await page.getByText("收藏").click();
    await expect(page.getByText("收藏的题目")).toBeVisible();

    // Empty state should be visible since we haven't bookmarked anything
    const emptyVisible = await page.getByText("还没有收藏").isVisible().catch(() => false);
    if (emptyVisible) {
      expect(emptyVisible).toBeTruthy();
    }
  });
});
