const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../..');
const assets = ['index.html', 'site-assets/site.css', 'site-assets/moon.svg', 'site-assets/traders-at-dusk.png', 'site-assets/master-of-three.png'];
const csp = "default-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'";
const forbidden = /ever\s*quest|\beq\b|eqemu|rof2|macroquest/i;
(async () => {
  for (const name of assets.filter(name => !name.endsWith('.png'))) {
    assert.ok(!forbidden.test(fs.readFileSync(path.join(root, name), 'utf8')), `Brand leak in ${name}`);
  }
  const server = http.createServer((req, res) => {
    const name = new URL(req.url, 'http://localhost').pathname.slice(1) || 'index.html';
    if (!assets.includes(name)) { res.writeHead(404); return res.end(); }
    res.setHeader('Content-Security-Policy', csp);
    res.setHeader('Content-Type', {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'}[path.extname(name)]);
    res.end(fs.readFileSync(path.join(root, name)));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = process.env.SITE_URL || `http://127.0.0.1:${server.address().port}/`;
  let browser;
  try {
    browser = await chromium.launch({headless:true, executablePath:process.env.BROWSER_EXECUTABLE || undefined});
    const page = await browser.newPage({viewport:{width:1440,height:1000}, javaScriptEnabled:false, reducedMotion:'reduce'});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => { if (['error','warning'].includes(msg.type())) errors.push(msg.text()); });
    page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    const response = await page.goto(url);
    assert.equal(response.status(), 200);
    assert.deepEqual(await response.body(), fs.readFileSync(path.join(root, 'index.html')), 'Hosted HTML differs from source');
    assert.ok(response.headers()['content-security-policy'].includes("default-src 'none'"));
    assert.equal(await page.locator('h1').count(), 1);
    assert.equal(await page.locator('script,iframe,form').count(), 0);
    assert.ok(!forbidden.test(await page.locator('html').textContent()), 'Public text brand leak');
    assert.equal(await page.locator('.catalog-group details').count(), 21);
    assert.equal(await page.locator('#roadmap article').count(), 6);
    const links = await page.locator('a').evaluateAll(items => items.map(a => a.getAttribute('href')));
    for (const href of links) {
      assert.ok(href.startsWith('#'), `Unexpected external link ${href}`);
      assert.equal(await page.locator(href).count(), 1, `Broken target ${href}`);
    }
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip').evaluate(el => el === document.activeElement), true);
    await page.locator('nav a[href="#faq"]').click();
    assert.ok(page.url().endsWith('#faq'));
    const faq = page.locator('#faq details').first();
    await faq.locator('summary').press('Enter');
    assert.equal(await faq.getAttribute('open'), '');
    await faq.locator('summary').press('Space');
    assert.equal(await faq.getAttribute('open'), null);
    await page.locator('nav a[href="#changes"]').click();
    await page.goBack();
    assert.ok(page.url().endsWith('#faq'));
    await page.goto(url + '#pets');
    await page.locator('#pets summary').press('Enter');
    assert.ok(await page.locator('#pets .detail-body').isVisible());
    for (const detail of await page.locator('details').all()) {
      if (await detail.getAttribute('open') === null) await detail.locator('summary').click();
    }
    for (const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:1000});
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px overflow`);
      const clipped = await page.locator('summary,nav,.roadmap-grid article,.detail-body').evaluateAll(els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.slice(0,60)));
      assert.deepEqual(clipped, [], `${width}px clipped content`);
    }
    // Reflow at 200% text size; all disclosures remain usable without scripts.
    const zoomPage = await browser.newPage({viewport:{width:1440,height:1000}, javaScriptEnabled:false});
    await zoomPage.route('**/site-assets/site.css', async route => {
      const response = await route.fetch();
      await route.fulfill({response, body:(await response.text()) + '\nhtml{font-size:200%}'});
    });
    await zoomPage.goto(url);
    assert.ok(await zoomPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '200% text overflow');
    await zoomPage.close();
    await page.reload();
    await page.setViewportSize({width:1440,height:1000});
    const output = process.env.SCREENSHOT_DIR;
    if (output) {
      fs.mkdirSync(output,{recursive:true});
      await page.goto(url);
      await page.screenshot({path:path.join(output,'desktop.png')});
      await page.screenshot({path:path.join(output,'desktop-full.png'),fullPage:true});
      await page.setViewportSize({width:390,height:844});
      await page.screenshot({path:path.join(output,'mobile-top.png')});
      await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    }
    for (const img of await page.locator('img').all()) {
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(el => el.decode());
      assert.ok(await img.evaluate(el => el.naturalWidth > 0 && !!el.alt), 'Broken or unlabeled artwork');
    }
    assert.deepEqual(errors, []);
    for (const name of assets) {
      const asset = await page.request.get(new URL(name === 'index.html' ? './' : name, url).href);
      assert.equal(asset.status(), 200, `Asset unavailable: ${name}`);
      assert.deepEqual(await asset.body(), fs.readFileSync(path.join(root,name)), `Hosted bytes differ: ${name}`);
    }
    console.log(JSON.stringify({result:'PASS',url,checks:['brand and metadata guard','21 feature entries / 6 workbench entries','all anchor targets','keyboard disclosures','history and deep links','5 responsive widths','200% text reflow','images','no JavaScript needed','strict CSP','clean console/network']},null,2));
  } finally { if(browser) await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
