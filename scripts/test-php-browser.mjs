/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-php-browser.mjs
 * Açıklama   : PHP test uygulamasını Chromium/WebKit ile gerçek tarayıcıda sınar.
 */
import { chromium,webkit } from 'playwright';
import { readFile,mkdir,writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
const remote=process.argv.includes('--remote');
const access=JSON.parse(await readFile(remote?'.local/php-stage-access.json':'.local/php-access.json','utf8'));
const base=remote?'https://sexogate.com/test':'http://127.0.0.1:3183/test';
const folder=remote?'docs/screenshots/php-hosting-remote':'docs/screenshots/php-hosting-local';await mkdir(folder,{recursive:true});const results=[];
function totp(secret){let bits='';for(const c of secret)bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5,'0');const key=Buffer.from(bits.match(/.{8}/g).map(b=>parseInt(b,2)));const time=Buffer.alloc(8);time.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const h=createHmac('sha1',key).update(time).digest();const offset=h[19]&15;return ((h.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0');}
for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]){
 const browser=await type.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:980},...(remote?{httpCredentials:{username:access.stageUser,password:access.stagePassword}}:{})});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let r=await page.goto(base+'/');await page.waitForLoadState('networkidle');await page.locator('#age-accept').click();assert.equal(r.status(),200);await page.screenshot({path:`${folder}/${engine}-home-desktop.png`,fullPage:true});
  assert.equal(await page.locator('.product-card').count(),3);assert.equal(await page.locator('img').evaluateAll(images=>images.filter(i=>!i.complete||i.naturalWidth===0).length),0);
  for(const width of [360,390,430,768,1440]){await page.setViewportSize({width,height:920});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${engine} ${width}`);}
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:`${folder}/${engine}-home-mobile.png`,fullPage:true});
  await page.goto(base+'/urun/saten-bag-detayi');await page.getByRole('button',{name:'Sepete ekle',exact:true}).click();await page.waitForURL('**/sepet');await page.getByRole('link',{name:'Ödemeye geç',exact:true}).click();await page.waitForURL('**/odeme');
  for(const [name,value] of Object.entries({email:'browser@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme Güvenli Alışveriş',city:'İstanbul',postalCode:'34000'}))await page.locator(`[name="${name}"]`).fill(value);
  assert.equal(await page.locator('[name="privacyAccepted"]').isChecked(),false);assert.equal(await page.locator('[name="termsAccepted"]').isChecked(),false);await page.screenshot({path:`${folder}/${engine}-checkout-mobile.png`,fullPage:true});
  await page.locator('[name="privacyAccepted"]').check();await page.locator('[name="termsAccepted"]').check();await page.getByRole('button',{name:'Ödemeye devam et',exact:true}).click();await page.waitForURL('**/odeme/test?**');await page.getByRole('button',{name:'Başarılı ödemeyi dene',exact:true}).click();await page.waitForURL('**/siparis/**');await page.getByRole('heading',{name:'Siparişiniz kaydedildi.'}).waitFor();await page.screenshot({path:`${folder}/${engine}-order.png`,fullPage:true});
  const orderUrl=page.url();const stranger=await browser.newContext(remote?{httpCredentials:{username:access.stageUser,password:access.stagePassword}}:{});const denied=await stranger.request.get(orderUrl.split('?')[0],remote?{headers:{Authorization:'Basic '+Buffer.from(access.stageUser+':'+access.stagePassword).toString('base64')}}:{});assert.equal(denied.status(),404);await stranger.close();
  await page.goto(base+'/en/urunler');assert.equal(await page.locator('html').getAttribute('lang'),'en');assert.equal(await page.getByRole('heading',{name:'Products',exact:true}).count(),1);
  assert.equal((await context.cookies()).filter(c=>/analytics|_ga|_fbp/i.test(c.name)).length,0);
  if(engine==='chromium'){
   await page.goto(base+'/yonetim/giris');if(remote&&await page.locator('form[action$="/_access"]').count()){const gate=page.locator('form[action$="/_access"]');await gate.locator('[name="username"]').fill(access.stageUser);await gate.locator('[name="password"]').fill(access.stagePassword);await Promise.all([page.waitForNavigation({waitUntil:'networkidle'}),gate.getByRole('button').click()]);}const form=page.locator('form[data-api="/api/auth/login"]');await form.locator('[name="email"]').fill(access.email);await form.locator('[name="password"]').fill(access.password);await form.getByRole('button').click();await page.waitForLoadState('networkidle');
   await page.waitForFunction(()=>document.querySelector('#mfa-start')||document.querySelector('form[data-api="/api/auth/mfa/login"]'));
   if(await page.locator('#mfa-start').count()){
    await page.locator('#mfa-start [name="password"]').fill(access.password);await page.locator('#mfa-start button').click();await page.locator('#mfa-secret').waitFor({state:'visible'});access.totpSecret=await page.locator('#mfa-secret').textContent();await page.locator('#mfa-confirm [name="code"]').fill(totp(access.totpSecret));await page.locator('#mfa-confirm button').click();await page.locator('#mfa-recovery').waitFor({state:'visible'});access.recoveryCodes=(await page.locator('#mfa-recovery pre').textContent()).split('\n');await writeFile(remote?'.local/php-stage-access.json':'.local/php-access.json',JSON.stringify(access,null,2));await page.locator('#mfa-recovery a').click();
   }else{await page.locator('form[data-api="/api/auth/mfa/login"] [name="code"]').fill(totp(access.totpSecret));await page.locator('form[data-api="/api/auth/mfa/login"] button').click();}
   await page.waitForURL('**/yonetim');await page.getByRole('heading',{name:'Yönetim',exact:true}).waitFor();await page.screenshot({path:`${folder}/${engine}-admin.png`,fullPage:true});
  }
  assert.deepEqual(errors,[]);results.push({engine,home:true,assets:true,mobileWidths:[360,390,430,768,1440],guestOrder:true,ownerIsolation:true,english:true,advertisingCookies:0,adminMfa:engine==='chromium'});await context.close();
 }finally{await browser.close();}
}
await writeFile(remote?'.local/php-browser-remote.json':'.local/php-browser-local.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
