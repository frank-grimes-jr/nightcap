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
    res.setHeader('Cache-Control', 'private, no-store, no-transform');
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
    assert.equal(await page.locator('.change-list > li').count(), 73);
    assert.equal(await page.locator('#zone-rewards tbody tr').count(), 48);
    assert.ok((await page.locator('#zone-hunt').innerText()).includes('0.5%'));
    assert.ok((await page.locator('#zone-forge').innerText()).includes('#zoneforge'));
    assert.ok((await page.locator('#hunt-sockets').innerText()).includes('280'));
    const featuredSystems = [
      ['#advanced-loot', 'Custom loot window'], ['#pets', 'Multiple pets'],
      ['#pet-window', 'Custom pet window'], ['#pet-armor', 'Pet Armor tab']
    ];
    for (const [target, title] of featuredSystems) {
      const shortcut = page.locator(`.system-shortcuts a[href="${target}"]`);
      assert.ok((await shortcut.innerText()).includes(title));
      await shortcut.click();
      assert.ok(page.url().endsWith(target));
      assert.ok((await page.locator(target + ' > strong').innerText()).includes(title));
    }
    assert.ok((await page.locator('#pet-window').innerText()).includes('class, name, and health'));
    assert.ok((await page.locator('#pet-orders').innerText()).includes('Targeting an enemy keeps that selection'));
    assert.ok((await page.locator('#pet-armor').innerText()).includes('does not change your command selection'));
    assert.ok((await page.locator('#saved-loot').innerText()).includes('after reconnecting'));
    assert.equal(await page.locator('.quest-list > li').count(), 2);
    assert.equal(await page.locator('.candidate-list > li').count(), 8);
    assert.equal(await page.locator('#features details, #quests details').count(), 0, 'Lists must be readable without opening disclosures');
    assert.ok((await page.locator('#journal-candidate').innerText()).includes('not installed on the server'));
    assert.ok((await page.locator('#selling').innerText()).includes('Sales are immediate'));
    assert.ok((await page.locator('#ascension').innerText()).includes('100,000 platinum'));
    assert.ok((await page.locator('#waypoint-explorer').innerText()).includes('72'));
    assert.ok((await page.locator('#loot-all').innerText()).includes('current zone or instance'));
    assert.ok((await page.locator('#passive-abilities').innerText()).includes('full normal experience plus 10%'));
    assert.ok((await page.locator('#alternate-abilities').innerText()).includes('#aaexp on'));
    assert.ok(!(await page.locator('body').innerText()).includes('#aaexp 50'), 'Obsolete partial XP allocation');
    assert.ok((await page.locator('#free-trade').innerText()).includes('already-attuned'));
    assert.ok((await page.locator('#fixed-resale').innerText()).includes('1 platinum per physical item'));
    assert.ok((await page.locator('#selling').innerText()).includes('temporary summoned rewards'));
    assert.ok((await page.locator('#loot-all').innerText()).includes('no longer require a NO TRADE confirmation'));
    assert.ok((await page.locator('#loading-art').innerText()).includes('55 numbered loading screens'));
    assert.ok((await page.locator('#updates').innerText()).includes('fully close both the game and launcher'));
    const links = await page.locator('a').evaluateAll(items => items.map(a => a.getAttribute('href')));
    for (const href of links) {
      assert.ok(href.startsWith('#'), `Unexpected external link ${href}`);
      assert.equal(await page.locator(href).count(), 1, `Broken target ${href}`);
    }
    await page.goto(url);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip').evaluate(el => el === document.activeElement), true);
    await page.locator('nav a[href="#faq"]').click();
    assert.ok(page.url().endsWith('#faq'));
    const faq = page.locator('#faq details').first();
    await faq.locator('summary').press('Enter');
    assert.equal(await faq.getAttribute('open'), '');
    await faq.locator('summary').press('Space');
    assert.equal(await faq.getAttribute('open'), null);
    await page.locator('nav a[href="#quests"]').click();
    await page.goBack();
    assert.ok(page.url().endsWith('#faq'));
    await page.goto(url + '#pets');
    assert.ok(await page.locator('#pets').isVisible());
    await page.goto(url + '#journal-candidate');
    assert.ok(await page.locator('#journal-candidate').isVisible());
    for (const detail of await page.locator('details').all()) {
      if (await detail.getAttribute('open') === null) await detail.locator('summary').click();
    }
    for (const width of [320,390,768,1024,1440]) {
      await page.setViewportSize({width,height:1000});
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width}px overflow`);
      const clipped = await page.locator('summary,nav,.change-list li,.quest-list>li,.candidate-list li,.detail-body').evaluateAll(els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.slice(0,60)));
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
      await page.locator('#quests').screenshot({path:path.join(output,'quests.png')});
      await page.locator('#character').screenshot({path:path.join(output,'changes.png')});
      await page.locator('#items').screenshot({path:path.join(output,'zone-hunt-desktop.png')});
      await page.locator('#looting').screenshot({path:path.join(output,'loot-window.png')});
      await page.locator('#companions').screenshot({path:path.join(output,'pet-systems.png')});
      await page.locator('.system-shortcuts').screenshot({path:path.join(output,'featured-systems.png')});
      await page.setViewportSize({width:390,height:844});
      await page.screenshot({path:path.join(output,'mobile-top.png')});
      await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
      await page.locator('#quests').screenshot({path:path.join(output,'mobile-quests.png')});
      await page.locator('#companions').screenshot({path:path.join(output,'mobile-pets.png')});
      await page.locator('#zone-rewards summary').click();
      await page.locator('#zone-rewards').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,'zone-rewards-mobile.png')});
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
      const cache = asset.headers()['cache-control'].split(',').map(value => value.trim().toLowerCase());
      assert.ok(['private','no-store','no-transform'].every(value => cache.includes(value)), `Private cache directives missing: ${name}`);
      assert.ok(!cache.includes('public'), `Shared caching enabled: ${name}`);
      assert.deepEqual(await asset.body(), fs.readFileSync(path.join(root,name)), `Hosted bytes differ: ${name}`);
    }
    console.log(JSON.stringify({result:'PASS',url,checks:['brand and metadata guard','73 visible custom changes / 2 installed quests / 8 unreleased quests','all anchor targets','keyboard disclosures','history and deep links','5 responsive widths','200% text reflow','images','no JavaScript needed','strict CSP','private non-caching responses','clean console/network']},null,2));
  } finally { if(browser) await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
