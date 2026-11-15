import http from 'node:http';
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {chromium,webkit,request} from '../../artifacts/qa/node_modules/playwright/index.mjs';
import {filterProducts,categoryFamily} from '../../web/shop-core.js';
const phase=process.env.NODENO_STOREFRONT_PHASE||'source';
assert.ok(['source','local','live'].includes(phase));
const fixture=phase==='source',origin=fixture?'http://127.0.0.1:4191':process.env.NODENO_STOREFRONT_URL;
assert.ok(origin);const folder='artifacts/desktop-storefront';await mkdir(folder,{recursive:true});
let proxy;
if(fixture){proxy=http.createServer(async(req,res)=>{if(req.url.startsWith('/media/')){try{const path=new URL(req.url,origin).pathname;if(!mediaCache.has(path))mediaCache.set(path,(async()=>{const response=await api.get('https://nodenohome.com'+path);assert.equal(response.status(),200);return{body:await response.body(),contentType:response.headers()['content-type']};})());const media=await mediaCache.get(path);if(!res.destroyed){res.writeHead(200,{'Content-Type':media.contentType,'Connection':'close'});res.end(media.body);}}catch{if(!res.destroyed){res.writeHead(502);res.end();}}return;}const upstream=http.request({hostname:'127.0.0.1',port:4190,path:req.url,method:req.method,headers:{...req.headers,connection:'close'},agent:false},r=>{res.writeHead(r.statusCode,{...r.headers,connection:'close'});r.pipe(res);});upstream.on('error',()=>{res.writeHead(502);res.end();});req.pipe(upstream);});await new Promise(resolve=>proxy.listen(4191,'127.0.0.1',resolve));}
const api=await request.newContext(),mediaCache=new Map();
const catalog=await(await api.get(origin+'/api/catalog')).json(),products=catalog.products;
const product=products.find(p=>p.id==='2395');assert.ok(product);
const variants=products.filter(p=>p.modelId===product.modelId);
const report={phase,testOnly:fixture,backendFixture:fixture,sourceOverride:false,origin,checks:[],errors:[],sourceHashes:{},cspDiagnostics:[],cspDiagnosticContext:'Windows WebKit reports an inline style at the search-form line on the unchanged live baseline; the same diagnostic occurs locally with JavaScript disabled. Playwright screenshot preparation also injects body{}. Recorded separately; production CSP remains unchanged.'};
if(fixture)for(const name of ['app.js','styles.css','desktop-store.css','shop-core.js','shop-i18n.js'])report.sourceHashes[name]=createHash('sha256').update(await readFile('web/'+name)).digest('hex');
if(!fixture){const health=await(await api.get(origin+'/api/health',{timeout:180000})).json();report.releaseHash=health.releaseHash;if(process.env.NODENO_QA_RELEASE)assert.equal(report.releaseHash,process.env.NODENO_QA_RELEASE);}
try{
 for(const engine of ['chromium','webkit']){
  const browser=await(engine==='chromium'?chromium:webkit).launch({headless:true,executablePath:engine==='chromium'?'C:/Users/Hamza ÖZBALKAN/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe':'C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno/artifacts/runtime-browsers/webkit-2370/Playwright.exe'});
  try{
   if(fixture&&engine==='chromium'){
    const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
    await page.route('**/api/account',async route=>{const response=await route.fetch();await new Promise(resolve=>setTimeout(resolve,3000));await route.fulfill({response});});
    await page.goto(origin+'/?page=catalog&lang=tr',{waitUntil:'domcontentloaded'});await page.locator('#desktop-min-price').fill('8000');await page.locator('#desktop-max-price').fill('12000');
    await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});assert.equal(await page.locator('#desktop-min-price').inputValue(),'8000','Account hydration must preserve a filter draft');assert.equal(await page.locator('#desktop-max-price').inputValue(),'12000');
    await page.unrouteAll({behavior:'wait'});await context.close();report.filterDraftSurvivesAccountHydration=true;
   }
   const cases=process.env.NODENO_STOREFRONT_QUICK?[['tr',1440]]:[...['tr','en','ru','ar'].flatMap(lang=>[390,1440].map(width=>[lang,width])),['tr',1024],['tr',1920]];
   for(const [lang,width]of cases){
    const context=await browser.newContext({viewport:{width,height:1000},isMobile:width<700,hasTouch:width<700}),page=await context.newPage();
    page.on('pageerror',error=>report.errors.push(error.message));
    page.on('console',message=>{if(message.type()==='error'&&/Content Security Policy|Refused.*(?:style|script)/i.test(message.text()))report.cspDiagnostics.push({engine,lang,width,message:message.text()});});
    async function visit(url,options={waitUntil:'domcontentloaded'}){const ready=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/account/social');await page.goto(url,options);await(await ready).finished();}
    async function frame(route){const size=await page.evaluate(()=>({width:innerWidth,root:document.documentElement.scrollWidth,body:document.body.scrollWidth,wide:[...document.querySelectorAll('#page *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>innerWidth+2&&!e.closest('.gallery-viewport,.color-option-strip,.product-row,.category-circles,.catalog-shortcuts,.search-suggestions,.category-nav');}).slice(0,8).map(e=>e.className)}));assert.ok(size.root<=size.width+1&&size.body<=size.width+1,JSON.stringify({engine,lang,route,...size}));}
    async function screenshot(name){if(lang==='tr'&&[390,1440,1920].includes(width)){await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});await page.evaluate(async()=>{await document.fonts.ready;const visible=[...document.images].filter(img=>{const r=img.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth;});await Promise.all(visible.map(img=>img.decode().catch(()=>{})));});await page.screenshot({path:`${folder}/${phase}-${engine}-${lang}-${width}-${name}.png`,fullPage:false,caret:'initial'});}}
    await visit(`${origin}/?lang=${lang}`);await page.locator('.product-card').first().waitFor();
    assert.equal(await page.locator('.room-story').count(),3);assert.equal(await page.locator('.room-stories').isVisible(),width>=1000);
    await frame('home');await screenshot('home');
    await visit(`${origin}/?page=catalog&lang=${lang}`);await page.locator('#product-grid .product-card').first().waitFor();await frame('catalog');await screenshot('catalog');
    let form=page.locator('.desktop-filters .catalog-filter-form');
    if(width<700){await page.locator('[data-action=filter]').click();form=page.locator('#mobile-filters .catalog-filter-form');}
    await form.locator('[name=minPrice]').fill('12000');await form.locator('[name=maxPrice]').fill('8000');await form.locator('button[type=submit]').click();
    assert.ok(await form.locator('[name=maxPrice]').evaluate(input=>!input.validity.valid));assert.equal(new URL(page.url()).searchParams.has('minPrice'),false);
    await form.locator('[name=minPrice]').fill('8000');await form.locator('[name=maxPrice]').fill('12000');await form.locator('[name=color]').selectOption(product.variantColor.tr);
    await form.locator('button[type=submit]').click();await page.waitForURL(url=>url.searchParams.get('minPrice')==='8000',{waitUntil:'domcontentloaded'});
    const expected=filterProducts(products,{locale:lang,color:product.variantColor.tr,minPriceMinor:800000,maxPriceMinor:1200000,groupModels:true});
    assert.ok(expected.length>0);const ids=await page.locator('#product-grid .product-stage').evaluateAll(links=>links.map(a=>new URL(a.href).searchParams.get('product')));
    assert.deepEqual(ids,expected.slice(0,24).map(p=>p.id));assert.equal(await page.locator('.active-filters a').count(),3);await frame('filtered');
    await page.locator('#sort').selectOption('price-desc');await page.waitForURL(url=>url.searchParams.get('sort')==='price-desc',{waitUntil:'domcontentloaded'});
    const sorted=filterProducts(products,{locale:lang,color:product.variantColor.tr,minPriceMinor:800000,maxPriceMinor:1200000,sort:'price-desc',groupModels:true});
    assert.deepEqual(await page.locator('#product-grid .product-stage').evaluateAll(links=>links.map(a=>new URL(a.href).searchParams.get('product'))),sorted.slice(0,24).map(p=>p.id));
    assert.equal(new URL(page.url()).searchParams.get('minPrice'),'8000');
    await page.goBack();await page.waitForURL(url=>!url.searchParams.has('sort')||url.searchParams.get('sort')==='recommended',{waitUntil:'domcontentloaded'});await page.locator('#product-grid .product-card').first().waitFor();
    if(width>=1000){const category=catalog.categories.find(c=>!c.parentId&&product.categoryIds.some(id=>categoryFamily(c.id,catalog.categories).has(id)));assert.ok(category);await page.locator(`.category-filters a[href*="category=${category.id}"]`).click();await page.waitForURL(url=>url.searchParams.get('category')===category.id,{waitUntil:'domcontentloaded'});assert.equal(new URL(page.url()).searchParams.get('minPrice'),'8000');assert.equal(new URL(page.url()).searchParams.get('color'),product.variantColor.tr);assert.equal(await page.locator('#page h1').textContent(),category.name[lang]);}
    await visit(`${origin}/?lang=${lang}&product=${product.id}`);await page.locator('#gallery-viewport').waitFor();
    assert.equal(await page.locator('.product-service-panel').isVisible(),width>=1200);await frame('product');await screenshot('product');
    await page.locator('[data-gallery-step="1"]').first().click();await page.waitForFunction(()=>document.querySelector('#gallery-counter').textContent.trim().startsWith(new Intl.NumberFormat(document.documentElement.lang).format(2)));
    const next=variants.find(v=>v.id!==product.id);await page.locator(`[data-variant="${next.id}"]`).click();await page.waitForURL(url=>url.searchParams.get('product')===next.id,{waitUntil:'domcontentloaded'});await frame('variant');
    await page.locator('#detail-quantity').fill('2');await page.locator('#detail-quantity').dispatchEvent('change');await page.locator((width<700?'.mobile-purchase':'.product-buy-actions')+' [data-detail-add]').click();
    await page.locator('.product-section-nav [href="#product-specs"]').click();await page.waitForURL(url=>url.hash==='#product-specs',{waitUntil:'domcontentloaded'});
    const bounds=await page.evaluate(()=>({section:document.querySelector('#product-specs').getBoundingClientRect().top,header:document.querySelector('.store-header').getBoundingClientRect().bottom,nav:innerWidth>=1000?document.querySelector('.product-section-nav').getBoundingClientRect().height:0}));assert.ok(bounds.section>=bounds.header+bounds.nav-1,JSON.stringify(bounds));await screenshot('specifications');
    await visit(`${origin}/?page=cart&lang=${lang}`);await page.locator('.basket-item').first().waitFor();
    assert.equal(await page.locator(`[data-cart-quantity="${next.id}"]`).inputValue(),'2');assert.equal(await page.locator('[data-action=export],[data-action=export-json],[data-action=print]').count(),0);await frame('cart');await screenshot('cart');
    await page.locator('.basket-summary a[href*="page=checkout"]').click();await page.locator('.guest-entry').waitFor();await page.locator('[data-action=guest-start]').click();await page.locator('#guest-checkout-form').waitFor();await frame('checkout');await screenshot('checkout');
    for(const route of ['categories','favorites','help','login','account']){await visit(`${origin}/?page=${route}&lang=${lang}`);await page.locator('#page h1').waitFor();await page.locator('#account-menu a[href*="page=login"]').waitFor({state:'attached'});await frame(route);if(route==='login'||route==='categories')await screenshot(route);assert.equal(await page.locator('[data-panel=imagePolicy]').count(),0);}
    report.checks.push({engine,lang,width,pages:10,filters:true,priceSort:true,history:true,gallery:true,variant:true,cart:true,guestCheckout:true,overflow:false});console.log(JSON.stringify(report.checks.at(-1)));
    if(fixture)await page.unrouteAll({behavior:'wait'});await context.close();
   }
  }finally{await browser.close();}
 }
 assert.deepEqual(report.errors,[]);report.passed=true;
}catch(error){report.passed=false;report.failure=error.message;throw error;}
finally{await writeFile(`${folder}/${phase}-report.json`,JSON.stringify(report,null,2));await Promise.allSettled([...mediaCache.values()]);await api.dispose();if(proxy)await new Promise(resolve=>proxy.close(resolve));}
console.log(JSON.stringify({passed:report.passed,cases:report.checks.length,phase}));
