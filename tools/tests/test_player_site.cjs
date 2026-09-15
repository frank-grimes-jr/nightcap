const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const html = fs.readFileSync(path.resolve(__dirname, '../../index.html'));
  const server = http.createServer((req, res) => {
    if (req.url === '/favicon.ico') { res.writeHead(204); return res.end(); }
    res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = process.env.SITE_URL || `http://127.0.0.1:${server.address().port}/`;
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.BROWSER_EXECUTABLE || undefined });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(url);
    const ids = ['home', 'features', 'changes', 'faq'];
    async function selected(id) {
      assert.equal(await page.locator(`#tab-${id}`).getAttribute('aria-selected'), 'true');
      assert.equal(await page.locator('section.panel:visible').count(), 1);
      assert.ok(await page.locator(`#${id}`).isVisible());
    }
    await selected('home');
    for (const id of ids) { await page.locator(`#tab-${id}`).click(); await selected(id); }
    await page.locator('#tab-faq').press('ArrowRight'); await selected('home');
    await page.locator('#tab-home').press('End'); await selected('faq');
    await page.locator('#tab-faq').press('Home'); await selected('home');
    await page.locator('#tab-home').press('ArrowLeft'); await selected('faq');
    assert.equal(await page.locator('#tab-faq').evaluate(el => el === document.activeElement), true);
    await page.locator('#tab-features').click(); await page.locator('#tab-changes').click();
    await page.goBack(); await selected('features');
    await page.goto(url + '#faq'); await selected('faq');
    await page.locator('summary').first().click();
    assert.equal(await page.locator('details').first().getAttribute('open'), '');
    const output = process.env.SCREENSHOT_DIR;
    if (output) fs.mkdirSync(output, { recursive: true });
    await page.locator('#tab-home').click();
    if (output) await page.screenshot({ path: path.join(output, 'desktop-home.png'), fullPage: true });
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      for (const id of ids) {
        await page.locator(`#tab-${id}`).click(); await selected(id);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px ${id} horizontal overflow`);
      }
      if (width === 390 && output) {
        await page.locator('#tab-home').click(); await page.screenshot({ path: path.join(output, 'mobile-home.png'), fullPage: true });
        await page.locator('#tab-features').click(); await page.screenshot({ path: path.join(output, 'mobile-features.png'), fullPage: true });
      }
    }
    const noJS = await browser.newPage({ javaScriptEnabled: false });
    await noJS.goto(url);
    assert.equal(await noJS.locator('section.panel:visible').count(), 4);
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ result: 'PASS', url, checks: ['four tabs', 'keyboard wrap/Home/End/focus', 'history', 'deep link', 'FAQ disclosure', '16 viewport/panel overflow checks', 'no-JavaScript content', 'no console/page errors'] }, null, 2));
  } finally { if (browser) await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
