import { test, expect } from "@playwright/test";

const TEST_USER = {
  username: `e2euser_${Date.now()}`,
  password: "testpass123",
};

test.describe("Authentication flow", () => {
  test("register a new user and auto-login", async ({ page }) => {
    await page.goto("/");

    // Should show the login/register page when not authenticated
    await expect(page.getByText("AI 面试助手")).toBeVisible();
    await expect(page.getByText("登录")).toBeVisible();
    await expect(page.getByText("注册")).toBeVisible();

    // Switch to register tab
    await page.getByText("注册").click();

    // Fill in registration form
    await page.getByPlaceholder("用户名").fill(TEST_USER.username);
    await page.getByPlaceholder("显示名称（可选）").fill("E2E User");
    await page.getByPlaceholder("密码").fill(TEST_USER.password);

    // Submit
    await page.getByRole("button", { name: "注册并登录" }).click();

    // Should redirect to the main app
    await expect(page.getByText("闲聊")).toBeVisible();
    await expect(page.getByText("E2E User")).toBeVisible();
  });

  test("login with existing account", async ({ page }) => {
    // First register
    await page.goto("/");
    await page.getByText("注册").click();
    await page.getByPlaceholder("用户名").fill(TEST_USER.username);
    await page.getByPlaceholder("密码").fill(TEST_USER.password);
    await page.getByRole("button", { name: "注册并登录" }).click();
    await expect(page.getByText("闲聊")).toBeVisible();

    // Logout
    await page.getByText(TEST_USER.username).click();
    // Wait for login page
    await expect(page.getByText("登录")).toBeVisible();

    // Login
    await page.getByPlaceholder("用户名").fill(TEST_USER.username);
    await page.getByPlaceholder("密码").fill(TEST_USER.password);
    await page.getByRole("button", { name: "登录" }).click();

    // Should be back in the app
    await expect(page.getByText("闲聊")).toBeVisible();
  });

  test("shows error on wrong password", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("用户名").fill("nonexistent_user");
    await page.getByPlaceholder("密码").fill("wrongpass");
    await page.getByRole("button", { name: "登录" }).click();

    // Should show error toast
    await expect(page.getByText("登录失败")).toBeVisible();
  });
});
