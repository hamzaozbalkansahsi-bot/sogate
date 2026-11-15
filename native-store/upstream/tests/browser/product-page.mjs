import {chromium,webkit} from '../../artifacts/qa/node_modules/playwright/index.mjs';
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
const origin=process.env.NODENO_QA_URL,phase=process.env.NODENO_QA_PHASE;
assert.ok(origin&&['red','local','live'].includes(phase));
const folder='artifacts/product-page';await mkdir(folder,{recursive:true});
const report={origin,phase,at:new Date().toISOString(),sourceOverride:false,checks:[],errors:[],nativeSharing:'OS transport not automated'};
for(const engine of phase==='red'?['chromium']:['chromium','webkit']){
 const browser=await(engine==='chromium'?chromium:webkit).launch({headless:true,executablePath:engine==='chromium'?'C:/Users/Hamza ÖZBALKAN/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe':'C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno/artifacts/runtime-browsers/webkit-2370/Playwright.exe'});
 try{
  const api=await browser.newContext();const catalog=await(await api.request.get(origin+'/api/catalog')).json();
  const baseline=JSON.parse(await readFile('artifacts/cpanel-preview-f0836a66e50b0bce/private/catalog.json','utf8'));
  assert.deepEqual(catalog.products,baseline.products);assert.deepEqual(catalog.categories,baseline.categories);
  report.releaseHash=(await(await api.request.get(origin+'/api/health',{timeout:180000})).json()).releaseHash;
  if(process.env.NODENO_QA_RELEASE)assert.equal(report.releaseHash,process.env.NODENO_QA_RELEASE);await api.close();
  const metadata=await browser.newContext();
  for(const lang of ['tr','en','ru','ar']){
   const response=await metadata.request.get(origin+'/?product=2541&lang='+lang);assert.equal(response.status(),200);const html=await response.text();
   assert.ok(html.includes('property="og:image" content="https://nodenohome.com/media/2541/'));
   assert.ok(html.includes(`property="og:url" content="https://nodenohome.com/?lang=${lang}&amp;product=2541"`));
  }
  await metadata.close();
  const cases=phase==='red'?[['tr',390]]:['tr','en','ru','ar'].flatMap(lang=>[320,390,430,768,1366].map(width=>[lang,width]));
  for(const [lang,width]of cases){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width<700,hasTouch:width<700});const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
   await page.goto(`${origin}/?lang=${lang}&product=2541`,{waitUntil:'domcontentloaded'});
   await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});
   await page.locator('.product-about-highlights').waitFor({timeout:6000});
   assert.equal(await page.locator('#product-information .detail-description').count(),0,'remove identity soup');
   assert.ok((await page.locator('.product-about-highlights li').allTextContents()).length>=3);
   await page.locator('[data-product-buy]').first().waitFor({state:'attached'});
   for(const id of ['product-specs','product-questions','product-faq','product-reviews','product-collections'])assert.equal(await page.locator('#'+id).count(),1,id);
   async function frame(){const d=await page.evaluate(()=>({x:scrollX,w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}));assert.equal(d.x,0);assert.ok(d.doc<=d.w+1&&d.body<=d.w+1,JSON.stringify(d));}
   await frame();
   if(width===390||width===1366){await page.screenshot({path:`${folder}/${phase}-${engine}-${lang}-${width}-hero.png`});await page.locator('#product-information').scrollIntoViewIfNeeded();await page.screenshot({path:`${folder}/${phase}-${engine}-${lang}-${width}-about.png`});}
   const faq=page.locator('#product-faq details').first();await faq.locator('summary').click();assert.ok(await faq.getAttribute('open')!==null);
   await page.locator('.detail-secondary [data-share]').click();await page.locator('#share-dialog[open]').waitFor();
   const message=new URL(await page.locator('[data-share-channel=whatsapp]').getAttribute('href')).searchParams.get('text');assert.ok(message.includes('product=2541'));
   assert.equal(await page.locator('#share-content textarea,#share-content input').count(),0);assert.equal(await page.locator('.share-apps-primary img').count(),3);assert.ok(!(await page.locator('#share-content').textContent()).includes('http'));
   await page.waitForFunction(()=>[...document.querySelectorAll('.share-apps-primary img')].every(img=>img.complete&&img.naturalWidth>0));
   if(lang==='tr')assert.equal(message,`Görmeni istediğim bir ürün var; ${origin}/?lang=tr&product=2541`);
   assert.equal(new URL(await page.locator('[data-share-channel=whatsapp]').getAttribute('href')).searchParams.get('text'),message);
   assert.equal(new URL(await page.locator('[data-share-channel=facebook]').getAttribute('href')).searchParams.get('u'),`${origin}/?lang=${lang}&product=2541`);
   await frame();
   if(width===390)await page.screenshot({path:`${folder}/${phase}-${engine}-${lang}-share.png`});
   await page.locator('#share-dialog [data-close]').click();assert.equal(await page.locator('#share-dialog').getAttribute('open'),null);
   if(width===390){
    await page.locator('#detail-quantity').fill('3');await page.locator('#detail-quantity').dispatchEvent('change');
    await page.locator('.mobile-purchase [data-product-buy]').click();await page.locator('.guest-entry').waitFor();
    await page.locator('[data-action=guest-start]').click();await page.locator('#guest-checkout-form').waitFor();
    const state=await page.evaluate(()=>JSON.parse(localStorage.getItem('nodeno.cart.v1')));assert.equal(state.find(v=>v.id==='2541').quantity,3);await frame();
   }
   report.checks.push({engine,lang,width,about:true,faq:true,sharePanel:true,channels:true,buyNow:width===390,rootContained:true});console.log(JSON.stringify(report.checks.at(-1)));await context.close();
  }
  if(phase!=='red'){
   // Only the OS handoff is replaced. Real catalog/media/file decoding and UI
   // run unchanged; this does not claim delivery to a native destination app.
   const context=await browser.newContext({viewport:{width:390,height:900},isMobile:true,hasTouch:true});
   await context.addInitScript(()=>{
    window.shareCaptures=[];window.shareError='';
    Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{if(window.shareError)throw new DOMException('Test OS response',window.shareError);window.shareCaptures.push(data);}});
   });
   const page=await context.newPage();await page.goto(origin+'/?product=2541&lang=tr',{waitUntil:'domcontentloaded'});await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});
   await page.locator('.detail-secondary [data-share]').click();await page.locator('#share-native').click();
   await page.waitForFunction(()=>window.shareCaptures.length===1);const capture=await page.evaluate(()=>window.shareCaptures[0]);assert.equal(capture.text,`Görmeni istediğim bir ürün var; ${origin}/?lang=tr&product=2541`);assert.equal(capture.files,undefined);
   await page.evaluate(()=>{window.shareError='AbortError';});await page.locator('#share-native').click();assert.equal(await page.evaluate(()=>window.shareCaptures.length),1);assert.equal(await page.locator('#share-ready-note').textContent(),'');
   await page.evaluate(()=>{window.shareError='NotAllowedError';});await page.locator('#share-native').click();await page.waitForFunction(()=>document.querySelector('#share-ready-note').textContent.startsWith('Paylaşım açılamadı'));
   await page.locator('#share-dialog [data-close]').click();await page.waitForFunction(()=>document.querySelector('#share-content').childElementCount===0);
   report[engine+'ShareBridge']={osTransportStub:true,selectedProductLink:true,noVisibleMessageOrInput:true,cancelHandled:true,errorHandled:true,memoryClearedOnClose:true};await context.close();
  }
 }catch(error){report.passed=false;report.failure=error.message;await writeFile(`${folder}/${phase}-report.json`,JSON.stringify(report,null,2));throw error;}
 finally{await browser.close();}
}
assert.deepEqual(report.errors,[]);report.passed=true;await writeFile(`${folder}/${phase}-report.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({passed:true,checks:report.checks.length,releaseHash:report.releaseHash}));
