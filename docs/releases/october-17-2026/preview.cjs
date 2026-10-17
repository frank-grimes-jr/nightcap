const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../../..');
const output = process.env.SCREENSHOT_DIR;
const notes = JSON.parse(fs.readFileSync(path.join(root,'eq-launcher/patch-notes.json')));
const server = http.createServer((req,res) => {
  const pathname = new URL(req.url,'http://localhost').pathname;
  const file = path.resolve(root,'wiki/dist','.'+(pathname==='/'?'/index.html':pathname));
  if (!file.startsWith(path.resolve(root,'wiki/dist')+path.sep) || !fs.existsSync(file)) {res.writeHead(404);return res.end();}
  res.setHeader('Content-Type', {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.json':'application/json','.png':'image/png','.svg':'image/svg+xml'}[path.extname(file)] || 'application/octet-stream');
  res.end(fs.readFileSync(file));
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
 const errors=[], sizes=[];
 try {
  fs.mkdirSync(output,{recursive:true});
  const page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(notes=>{
   const state={version:'0.6.0',channel:'Nightcap',client_dir:'C:\\Nightcap',phase:'stopped',message:'Ready to play',supported:true,configured:true,busy:false,release:2026101702,installed_release:2026101702,patch_notes:notes,recovery_required:false,files:[],remove:[],events:[],can_check:true,can_update:false,can_recover:false,can_play:true,access_required:false,access_saved:true};
   window.go={main:{App:{GetStatus:async()=>state}}};
  },notes);
  for (const [width,height] of [[1120,820],[780,620]]) {
   await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:5198/');
   await page.locator('.patch-release').waitFor();
   assert.equal(await page.locator('.patch-notes > .patch-changes > li').count(),10);
   assert.equal(await page.locator('.patch-history article').count(),14);
   assert.ok((await page.locator('.patch-notes').innerText()).includes('Recommended AA'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   const play=page.getByRole('button',{name:'Play Nightcap',exact:true});assert.equal(await play.isEnabled(),true);await play.scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(output,`patcher-${width}.png`),fullPage:true});
   sizes.push({width,height,latest_bullets:10,historical_patches:14,horizontal_overflow:false,play_reachable:true});
  }
  const wiki=await browser.newPage();wiki.on('pageerror',e=>errors.push(e.message));
  const base=`http://127.0.0.1:${server.address().port}`;
  for (const width of [1440,768,320]) {
   await wiki.setViewportSize({width,height:900});
   for (const slug of ['multiclass','combat','item-upgrades','tradeskills','features','recent-changes']) {
    const response=await wiki.goto(base+'/'+slug+'.html');assert.equal(response.status(),200);
    assert.equal(await wiki.locator('h1').count(),1);
    assert.equal(await wiki.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${slug} overflow at ${width}`);
   }
   await wiki.goto(base+'/multiclass.html#recommended-aa');
   assert.equal(await wiki.locator('#recommended-aa').count(),1);
   await wiki.screenshot({path:path.join(output,`wiki-${width}.png`),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  const result={status:'PASS',release:2026101702,method:'Real Chrome; exact launcher source with simulated native bridge; generated wiki',patcher:sizes,wiki_widths:[1440,768,320],changed_guides:6,page_errors:errors,native_owner_qa:'pending'};
  fs.writeFileSync(path.join(__dirname,'layout-verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
 } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
