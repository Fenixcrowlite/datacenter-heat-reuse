const {chromium}=require('playwright');
const path=require('node:path');
const fs=require('node:fs');
const assert=require('node:assert/strict');

(async()=>{
 const out=path.resolve(process.env.BROWSER_EVIDENCE||'.superpowers/sdd/2026-10-28-transfer/browser');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--disable-gpu']});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.TEST_BASE_URL||'http://127.0.0.1:18080';
 try {
  await page.goto(base);await page.locator('#model option').first().waitFor({state:'attached'});
  await page.selectOption('#scenario','Air25_Fixed70');
  assert.equal(await page.inputValue('#p-source_temp_C'),'25');
  await page.selectOption('#model','pool-v04');await page.fill('#steps','32');
  await page.click('#run');await page.locator('#export-csv:not([hidden])').waitFor();
  const first=await page.locator('#metric-heat').innerText();assert.notEqual(first,'—');
  assert.equal(await page.locator('[data-flow=direct-pool]').getAttribute('class'),'flow-line ');
  assert.equal(await page.locator('[data-flow=tes-charge]').getAttribute('class'),'flow-line inactive');
  await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
  const firstId=await page.locator('#export-csv').getAttribute('href');
  await page.uncheck('[data-parameter=pool_enabled]');await page.click('#run');
  await page.waitForFunction(old=>document.querySelector('#export-csv').getAttribute('href')!==old,firstId);
  const secondId=await page.locator('#export-csv').getAttribute('href');
  const result=await (await page.request.get(base+secondId.replace('.csv',''))).json();
  assert.equal(result.source_kind,'PYTHON_COMPUTED');assert.equal(result.metrics.pool_heat_MWh,0);
  assert.equal(result.rows.length,32);
  await page.click('#language');assert.equal(await page.locator('html').getAttribute('lang'),'sk');
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.click('[data-view=originals]');await page.locator('#original-diagram svg').waitFor();
  await page.screenshot({path:path.join(out,'original-model.png'),fullPage:true});
  await page.click('[data-view=documents]');assert.ok(await page.locator('.document-card').count()>0);
  const csv=await (await page.request.get(base+secondId)).text();assert.ok(csv.includes('T_bazen_C'));
  assert.deepEqual(errors,[]);
  const report={status:'PASS',checks:['new calculation','changed settings change outputs','CSV export','SK language','390px viewport without horizontal page overflow','original model SVG','source document list','no page errors']};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
