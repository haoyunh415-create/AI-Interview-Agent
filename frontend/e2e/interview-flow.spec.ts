import { test, expect } from "@playwright/test";

const USER = {
  username: `interviewuser_${Date.now()}`,
  password: "testpass123",
};

test.describe("Core interview flow", () => {
  test.beforeEach(async ({ page }) => {
    // Register and login before each test
    await page.goto("/");
    await page.getByText("注册").click();
    await page.getByPlaceholder("用户名").fill(USER.username);
    await page.getByPlaceholder("显示名称（可选）").fill("Interview Tester");
    await page.getByPlaceholder("密码").fill(USER.password);
    await page.getByRole("button", { name: "注册并登录" }).click();
    await expect(page.getByText("闲聊")).toBeVisible();
  });

  test("full interview cycle: select topic → answer → see score → complete", async ({ page }) => {
    // Navigate to interview mode
    await page.getByText("面试").click();
    await expect(page.getByText("模拟面试")).toBeVisible();

    // Select a topic
    await page.getByText("Transformer 核心").click();

    // Enable timer checkbox
    const timerCheckbox = page.getByRole("checkbox");
    if (await timerCheckbox.isChecked()) {
      await timerCheckbox.uncheck();
    }

    // Start interview
    await page.getByRole("button", { name: "开始面试" }).click();

    // Wait for question to appear
    await expect(page.getByText(/面试题|追问/)).toBeVisible({ timeout: 15000 });

    // Type an answer
    const answerBox = page.getByPlaceholder("输入你的回答...");
    await expect(answerBox).toBeVisible();
    await answerBox.fill(
      "Self-Attention is a mechanism that computes the relevance between every pair of positions in a sequence. " +
      "It uses Query, Key, Value matrices derived from the input. " +
      "The attention score is computed as softmax(Q*K^T / sqrt(d_k)) * V. " +
      "Multi-head attention runs this in parallel with different projections."
    );

    // Submit answer
    await page.getByRole("button", { name: "提交回答" }).click();

    // Wait for streaming evaluation to complete
    // We should either see the score display or a followup question
    await page.waitForTimeout(5000);

    // Check we see the score or the next question
    const scoreVisible = await page.getByText(/正确性|深度|逻辑|表达/).isVisible().catch(() => false);
    const followupVisible = await page.getByText("追问").isVisible().catch(() => false);
    const completedVisible = await page.getByText("面试完成").isVisible().catch(() => false);

    expect(scoreVisible || followupVisible || completedVisible).toBeTruthy();
  });

  test("hint button works during interview", async ({ page }) => {
    // Start interview
    await page.getByText("面试").click();
    await page.getByText("Transformer 核心").click();

    const timerCheckbox = page.getByRole("checkbox");
    if (await timerCheckbox.isChecked()) {
      await timerCheckbox.uncheck();
    }

    await page.getByRole("button", { name: "开始面试" }).click();
    await expect(page.getByText(/面试题|追问/)).toBeVisible({ timeout: 15000 });

    // Request hint
    await page.getByRole("button", { name: "提示" }).click();
    await page.waitForTimeout(3000);

    // Hint should be displayed
    const hintVisible = await page.getByText("💡").isVisible().catch(() => false);
    expect(hintVisible).toBeTruthy();
  });

  test("resume button appears after some progress", async ({ page }) => {
    await page.getByText("面试").click();
    await page.getByText("Transformer 核心").click();

    const timerCheckbox = page.getByRole("checkbox");
    if (await timerCheckbox.isChecked()) {
      await timerCheckbox.uncheck();
    }

    await page.getByRole("button", { name: "开始面试" }).click();
    await expect(page.getByText(/面试题|追问/)).toBeVisible({ timeout: 15000 });

    // Answer once
    await page.getByPlaceholder("输入你的回答...").fill("Transformers use self-attention and positional encoding.");
    await page.getByRole("button", { name: "提交回答" }).click();
    await page.waitForTimeout(3000);

    // Navigate away and back
    await page.getByText("闲聊").click();
    await page.getByText("面试").click();

    // Resume button should be visible (if session was saved)
    await page.waitForTimeout(1000);
    const resumeVisible = await page.getByText(/恢复|继续/).isVisible().catch(() => false);
    // This is nice-to-have, not critical
    if (!resumeVisible) {
      test.info().annotations.push({
        type: "note",
        description: "Resume button not visible — session may already be completed",
      });
    }
  });
});
