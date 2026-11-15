import {chromium,webkit} from '../../artifacts/qa/node_modules/playwright/index.mjs';
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';

// Real packaged/local or live site. No response interception or source overrides.
const origin=process.env.NODENO_QA_URL;
const phase=process.env.NODENO_QA_PHASE;
assert.ok(origin&&['red','local','live'].includes(phase));
const folder='artifacts/inline-gallery';await mkdir(folder,{recursive:true});
const report={phase,origin,at:new Date().toISOString(),sourceOverride:false,checks:[],errors:[]};
for(const engine of phase==='red'?['chromium']:['chromium','webkit']){
 const browser=await (engine==='chromium'?chromium:webkit).launch({headless:true,executablePath:engine==='chromium'?'C:/Users/Hamza ÖZBALKAN/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe':'C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno/artifacts/runtime-browsers/webkit-2370/Playwright.exe'});
 try{
  const api=await browser.newContext();
  const health=await(await api.request.get(origin+'/api/health',{timeout:180000})).json();report.releaseHash=health.releaseHash;
  if(process.env.NODENO_QA_RELEASE)assert.equal(health.releaseHash,process.env.NODENO_QA_RELEASE);
  const catalog=await(await api.request.get(origin+'/api/catalog')).json();
  const baseline=JSON.parse(await readFile('artifacts/cpanel-preview-d53b68f4a8f278f7/private/catalog.json','utf8'));
  assert.deepEqual(catalog.products,baseline.products);assert.deepEqual(catalog.categories,baseline.categories);
  const userProduct=catalog.products.find(p=>/HMA-012-NT-5/i.test(p.code));assert.ok(userProduct,'screenshot product exists');
  await api.close();
  const cases=phase==='red'?[['tr',390,userProduct.id]]:['tr','en','ru','ar'].flatMap(lang=>[320,390,430,1366].map(width=>[lang,width,width===390?userProduct.id:'2393']));
  for(const [lang,width,productId] of cases){
   const context=await browser.newContext({viewport:{width,height:844},isMobile:width<700,hasTouch:width<700});
   const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
   page.on('response',r=>{if(r.url().startsWith(origin)&&r.status()>=400)report.errors.push(r.status()+' '+r.url());});
   const product=catalog.products.find(p=>p.id===productId);
   await page.goto(`${origin}/?product=${productId}&lang=${lang}`,{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>document.querySelector('.gallery-main img')?.naturalWidth>0&&!document.querySelector('[data-detail-add]')?.disabled);
   await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});
   await page.evaluate(()=>document.fonts.ready);
   const picker=index=>page.locator(`[data-gallery${width<700?'-point':''}="${index}"]`);
   await picker(0).click();
   const main=page.locator('.gallery-main');await main.scrollIntoViewIfNeeded();
   const client=engine==='chromium'?await context.newCDPSession(page):null;
   async function swipe(locator,forward=true,vertical=false){
    const b=await locator.boundingBox(),start={x:b.x+b.width*(vertical?.5:forward?.8:.2),y:b.y+b.height*(vertical?.7:.5)};
    const end={x:b.x+b.width*(vertical?.5:forward?.2:.8),y:b.y+b.height*(vertical?.3:.5)};
    await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[start]});
    for(let i=1;i<=10;i++){await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:start.x+(end.x-start.x)*i/10,y:start.y+(end.y-start.y)*i/10}]});await page.waitForTimeout(25);}
    await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(350);
   }
   async function indexIs(index){await page.waitForFunction(i=>document.querySelector(`[data-gallery="${i}"]`)?.getAttribute('aria-pressed')==='true',index,{timeout:6000});}
   if(client&&width<700)await swipe(main);
   else await page.locator('#gallery-viewport').evaluate(v=>v.scrollBy({left:v.clientWidth,behavior:'instant'}));
   try{await indexIs(1);}catch(error){
    await page.screenshot({path:`${folder}/${phase}-failure-${engine}-${lang}-${width}.png`});
    report.failure='Normal product photo swipe did not select the next image';
    throw error;
   }
   assert.equal(await page.locator('#photo-dialog').getAttribute('open'),null,'swipe must not open zoom');
   if(phase==='red')throw new Error('Expected current production swipe to fail');
   async function frame(){const d=await page.evaluate(()=>({x:scrollX,w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}));assert.equal(d.x,0);assert.ok(d.doc<=d.w+1&&d.body<=d.w+1,JSON.stringify(d));}
   await frame();
   assert.equal(await page.locator('[data-gallery-step="-1"]').isDisabled(),false);
   if(client&&width<700){await swipe(main,false);await indexIs(0);const y=await page.evaluate(()=>scrollY);await swipe(main,true,true);assert.ok((await page.evaluate(()=>scrollY))>y+20,'vertical page scroll from image remains available');await indexIs(0);await main.scrollIntoViewIfNeeded();}
   await picker(2).click();await indexIs(2);
   await page.locator('#gallery-viewport').focus();await page.keyboard.press('Home');await indexIs(0);assert.equal(await page.locator('[data-gallery-step="-1"]').isDisabled(),true);
   await page.keyboard.press('End');await indexIs(product.images.length-1);assert.equal(await page.locator('[data-gallery-step="1"]').isDisabled(),true);
   await page.keyboard.press('ArrowLeft');await indexIs(product.images.length-2);await page.keyboard.press('ArrowRight');await indexIs(product.images.length-1);
   await picker(1).click();await indexIs(1);
   await page.locator('[data-gallery-step="1"]').click();await indexIs(2);await page.locator('[data-gallery-step="-1"]').click();await indexIs(1);
   await main.scrollIntoViewIfNeeded();await main.click();await page.locator('#photo-dialog[open]').waitFor();
   await page.waitForFunction(()=>{const v=document.querySelector('#photo-viewport');return Math.abs(v.scrollLeft/v.clientWidth-1)<.03;});
   await page.locator('[data-photo-step="1"]').click();
   await page.waitForFunction(()=>{const v=document.querySelector('#photo-viewport');return Math.abs(v.scrollLeft/v.clientWidth-2)<.03;});
   await page.locator('#photo-dialog [data-close]').click();await indexIs(2);
   assert.equal(await page.locator('[data-gallery-slide="2"]').evaluate(e=>e===document.activeElement),true);
   await page.waitForFunction(()=>{const v=document.querySelector('#gallery-viewport');return Math.abs(v.scrollLeft/v.clientWidth-2)<.03;});
   if(width===390)await page.screenshot({path:`${folder}/${phase}-${engine}-${lang}-390.png`});
   await page.setViewportSize({width:width===1366?1024:375,height:844});
   await page.waitForFunction(()=>{const v=document.querySelector('#gallery-viewport');return Math.abs(v.scrollLeft/v.clientWidth-2)<.03;});await frame();
   report.checks.push({engine,lang,width,productId,nativeTouch:!!client&&width<700,verticalScroll:!!client&&width<700,zoomSync:true,keyboard:true,buttons:true,resize:true,noPageOverflow:true});
   console.log(JSON.stringify(report.checks.at(-1)));await context.close();
  }
 }catch(error){report.failure??=error.message;report.passed=false;await writeFile(`${folder}/${phase}-report.json`,JSON.stringify(report,null,2));throw error;}
 finally{await browser.close();}
}
assert.deepEqual(report.errors,[]);report.passed=true;await writeFile(`${folder}/${phase}-report.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({passed:true,checks:report.checks.length,releaseHash:report.releaseHash}));
