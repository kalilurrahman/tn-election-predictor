import { test } from '@playwright/test';

test('take screenshots', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });

  await page.goto('http://localhost:7860/?view=dashboard');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/dashboard.png', fullPage: true });

  await page.goto('http://localhost:7860/?view=candidates');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/candidate-registry.png', fullPage: true });

  await page.goto('http://localhost:7860/?view=strategy');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/strategy-lab.png', fullPage: true });

  await page.goto('http://localhost:7860/?view=polls');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/polls.png', fullPage: true });

  await page.goto('http://localhost:7860/?view=stats');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/statistics.png', fullPage: true });

  await page.goto('http://localhost:7860/?view=admin');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'docs/screenshots/admin.png', fullPage: true });
});
