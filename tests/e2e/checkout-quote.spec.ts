/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/checkout-quote.spec.ts
 * Açıklama   : Misafir ödeme öncesi kanonik toplamı, yazımsız teklifi ve eski teklifin açık yeniden onayını sınar.
 */
import {test,expect,type Page,type APIRequestContext} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import pg from 'pg';
import {randomBytes,randomUUID} from 'node:crypto';
import {mkdir} from 'node:fs/promises';
import {money,type CheckoutQuote,type CheckoutResult,type Cart} from '../../src/shared/contracts';
import type {AddressProfile,AddressFieldId} from '../../src/shared/address-fields';
import {submitSignIn} from './helpers/sign-in';
const origin='http://127.0.0.1:3000';

async function fixture(){
 const url=new URL(process.env.DATABASE_URL??'http://invalid');
 if(!['development','test'].includes(process.env.APP_ENV??'')||!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname)||process.env.PAYMENT_PROVIDER!=='test')throw new Error('Teklif UI testi yalnız projenin yerel DB ve test ödeme adaptörüyle çalışır.');
 const pool=new pg.Pool({connectionString:url.href}),suffix=randomBytes(7).toString('hex'),productId=randomUUID(),variantId=randomUUID(),category=`quote-${suffix}`,sku=`QUOTE-${suffix}`,couponCode=`QT-${suffix.toUpperCase()}`;
 let actor='',couponId='';const cartIds=new Set<string>();
 async function cleanup(ownerIds:string[]=[]){
  const c=await pool.connect();try{await c.query('BEGIN');
   if(ownerIds.length)for(const row of (await c.query('SELECT id FROM carts WHERE user_id=ANY($1::text[])',[ownerIds])).rows)cartIds.add(row.id);
   const owned=(await c.query('SELECT v.id FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=$1 AND v.sku=$2 AND p.id=$3 AND p.fixture=true',[variantId,sku,productId])).rows.map(row=>row.id);
   const orders=(await c.query('SELECT DISTINCT o.id,o.cart_id FROM orders o LEFT JOIN order_items i ON i.order_id=o.id WHERE i.variant_id=ANY($1::text[]) OR o.cart_id=ANY($2::text[])',[owned,[...cartIds]])).rows;const ids=orders.map(row=>row.id);for(const row of orders)cartIds.add(row.cart_id);
   await c.query('DELETE FROM jobs WHERE payload->>\'orderId\'=ANY($1::text[]) OR dedupe_key=ANY($2::text[])',[ids,ids.flatMap(id=>[`reservation:${id}`,`confirmation:${id}`,`exception:${id}`])]);
   await c.query('DELETE FROM provider_events WHERE normalized->>\'orderId\'=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM payment_events WHERE payment_id IN(SELECT id FROM payments WHERE order_id=ANY($1::text[]))',[ids]);
   await c.query('DELETE FROM reservation_lots WHERE reservation_id IN(SELECT id FROM reservations WHERE order_id=ANY($1::text[]))',[ids]);
   await c.query('DELETE FROM reservations WHERE order_id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM coupon_usage WHERE order_id=ANY($1::text[]) OR coupon_id=$2',[ids,couponId]);
   await c.query('DELETE FROM order_agreements WHERE order_id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM order_history WHERE order_id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM payments WHERE order_id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM order_items WHERE order_id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM orders WHERE id=ANY($1::text[])',[ids]);
   await c.query('DELETE FROM cart_items WHERE variant_id=ANY($1::text[])',[owned]);
   await c.query('DELETE FROM carts c WHERE c.id=ANY($1::text[]) AND(c.user_id IS NULL OR c.user_id=ANY($2::text[])) AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=c.id) AND NOT EXISTS(SELECT 1 FROM cart_items i WHERE i.cart_id=c.id)',[[...cartIds],ownerIds]);
   await c.query('DELETE FROM inventory_movements WHERE variant_id=ANY($1::text[])',[owned]);await c.query('DELETE FROM inventory_balance WHERE variant_id=ANY($1::text[])',[owned]);await c.query('DELETE FROM variant_prices WHERE variant_id=ANY($1::text[])',[owned]);await c.query('DELETE FROM product_eligibility WHERE variant_id=ANY($1::text[])',[owned]);await c.query('DELETE FROM variants WHERE id=ANY($1::text[])',[owned]);
   await c.query('DELETE FROM products WHERE id=$1 AND fixture=true',[productId]);await c.query('DELETE FROM categories WHERE slug=$1',[category]);
   if(couponId)await c.query('DELETE FROM coupons WHERE id=$1 AND code=$2',[couponId,couponCode]);
   if(actor){await c.query('DELETE FROM audit_log WHERE actor_id=$1',[actor]);await c.query('DELETE FROM "user" WHERE id=$1',[actor]);}
   if(ownerIds.length){await c.query('DELETE FROM customer_addresses WHERE user_id=ANY($1::text[])',[ownerIds]);await c.query('DELETE FROM "user" WHERE id=ANY($1::text[])',[ownerIds]);}
   await c.query('COMMIT');
  }catch(error){await c.query('ROLLBACK');throw error;}finally{c.release();await pool.end();}
 }
 try{
  const {getAuth}=await import('../../src/server/auth');const signup=await getAuth().api.signUpEmail({body:{email:`quote-actor-${suffix}@example.invalid`,password:randomBytes(24).toString('base64url'),name:'Yerel Teklif Kaynak Yöneticisi'}});actor=signup.user.id;
  await pool.query('UPDATE "user" SET role=\'admin\' WHERE id=$1',[actor]);
  await pool.query('INSERT INTO categories(slug,name,name_en) VALUES($1,$2,$3)',[category,`Teklif testi ${suffix}`,`Quote test ${suffix}`]);
  await pool.query("INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,material,status,warnings,care,translations,fixture) VALUES($1,$2,$3,$4,'Yalnız bu testin kaynak ürün açıklaması.','Source product description owned by this test.',$5,'/media/atelier-01.svg','Saten','published','Yalnız yetişkinler içindir.','Üretici etiketini kontrol edin.',$6,true)",[productId,`quote-check-${suffix}`,`Teklif Maskesi ${suffix}`,`Quote Mask ${suffix}`,category,JSON.stringify({en:{warnings:'For adults only.',care:'Check the manufacturer label.'}})]);
  await pool.query("INSERT INTO variants(id,product_id,sku,name,name_en,price_minor,cost_minor,currency) VALUES($1,$2,$3,'Bordo','Burgundy',12345,100,'TRY')",[variantId,productId,sku]);
  await pool.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',12345)",[variantId]);
  await pool.query("INSERT INTO product_eligibility(variant_id,country,approved,review_note,approved_by,approved_at) VALUES($1,'TR',true,'Yalnız bu izole yerel teklif testinin uygunluk kaydı',$2,now())",[variantId,actor]);
  await pool.query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',3)",[variantId]);
  await pool.query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference,actor_id) VALUES($1,'main','receipt',3,'Yalnız izole teklif testinin mal kabulü',$2,$3)",[variantId,`quote-receipt:${suffix}`,actor]);
  couponId=(await pool.query("INSERT INTO coupons(code,discount_bps,minimum_minor,max_uses,minimum_contribution_minor,expires_at) VALUES($1,1000,1,10,0,now()+interval '1 day') RETURNING id",[couponCode])).rows[0].id;
  return {pool,suffix,variantId,productId,sku,couponCode,couponId,cartIds,cleanup};
 }catch(error){await cleanup();throw error;}
}
type Fixture=Awaited<ReturnType<typeof fixture>>;
async function putCart(request:APIRequestContext,f:Fixture){const response=await request.post('/api/cart',{headers:{Origin:origin},data:{variantId:f.variantId,quantity:1}});expect(response.status()).toBe(200);const cart=await response.json() as Cart;f.cartIds.add(cart.id);expect(cart.items.map(item=>item.variantId)).toEqual([f.variantId]);return cart;}
async function financialState(f:Fixture){
 const [row]=(await f.pool.query(`SELECT (SELECT count(*)::int FROM orders WHERE cart_id=ANY($1::text[])) orders,(SELECT count(*)::int FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.cart_id=ANY($1::text[])) items,(SELECT count(*)::int FROM payments p JOIN orders o ON o.id=p.order_id WHERE o.cart_id=ANY($1::text[])) payments,(SELECT count(*)::int FROM reservations WHERE variant_id=$2) reservations,(SELECT count(*)::int FROM coupon_usage WHERE coupon_id=$3) coupon_usage,(SELECT used_count FROM coupons WHERE id=$3) coupon_used,(SELECT on_hand FROM inventory_balance WHERE variant_id=$2 AND warehouse_id='main') on_hand,(SELECT count(*)::int FROM inventory_movements WHERE variant_id=$2) movements,(SELECT count(*)::int FROM jobs WHERE payload->>'orderId' IN(SELECT id FROM orders WHERE cart_id=ANY($1::text[]))) jobs`,[[...f.cartIds],f.variantId,f.couponId])).rows;return row;
}
async function address(request:APIRequestContext){
 const response=await request.get('/api/address-profile?country=TR');expect(response.status()).toBe(200);const profile=await response.json() as AddressProfile;
 const samples:Record<AddressFieldId,string>={fullName:'Yerel Teklif Testi',phone:'05550001122',line1:'Yerel Test Mahallesi Deneme Sokak 12',city:'İstanbul',region:'İstanbul',district:'Kadıköy',postalCode:'34000'};
 const values=Object.fromEntries(profile.fields.map(field=>{const candidate=field.format==='digits'?'1'.repeat(Math.max(field.minLength,Math.min(field.maxLength,field.id==='phone'?11:5))):samples[field.id];return [field.id,candidate.slice(0,field.maxLength).padEnd(field.minLength,field.format==='digits'?'1':'a')];}));return {profile,values};
}
async function assertAmounts(page:Page,quote:CheckoutQuote){const amounts=page.locator('dl[aria-label="Sipariş tutarları"]');await expect(amounts).toBeVisible();for(const [label,value]of [['Ara toplam',quote.subtotalMinor],['İndirim',-quote.discountMinor],['Teslimat',quote.shippingMinor],['Toplam',quote.totalMinor],['Toplama dahil vergi',quote.taxMinor]] as const){const row=amounts.locator('.summary-row').filter({has:page.getByText(label,{exact:true})});await expect(row).toHaveCount(1);await expect(row.getByRole('definition')).toHaveText(money(value,quote.currency,'tr'));}expect(quote.totalMinor).toBe(quote.subtotalMinor-quote.discountMinor+quote.shippingMinor);expect(quote.taxMinor).toBe(quote.goodsTaxMinor+quote.shippingTaxMinor);}

test('guest sees the full quote and explicitly accepts a changed total before any order is reserved',async({page})=>{
 test.setTimeout(65000);const f=await fixture(),quotes:CheckoutQuote[]=[],attempts:{status:number;data:Record<string,unknown>;request:Record<string,unknown>}[]=[];
 try{
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',url:origin},{name:'sexsogate_country',value:'TR',url:origin},{name:'sexsogate_currency',value:'TRY',url:origin}]);
  expect((await (await page.request.get('/api/session')).json()).user).toBeNull();
  const cart=await putCart(page.request,f),baseline=await financialState(f),delivery=await address(page.request);expect(baseline).toMatchObject({orders:0,payments:0,reservations:0,coupon_usage:0,on_hand:3});
  await page.route(url=>url.pathname==='/api/checkout/quote',async route=>{const response=await route.fetch();if(response.ok())quotes.push(await response.json() as CheckoutQuote);await route.fulfill({response});});
  await page.route(url=>url.pathname==='/api/checkout',async route=>{const response=await route.fetch();attempts.push({status:response.status(),data:await response.json(),request:route.request().postDataJSON()});await route.fulfill({response});});
  await page.setViewportSize({width:1440,height:1000});await page.goto('/odeme');await expect.poll(()=>quotes.length).toBeGreaterThan(0);const initial=quotes.at(-1)!;expect(initial.lines).toHaveLength(1);expect(initial.lines[0]).toMatchObject({variantId:f.variantId,unitMinor:12345,quantity:1});await assertAmounts(page,initial);expect(await financialState(f)).toEqual(baseline);
  await page.getByRole('textbox',{name:'E-posta',exact:true}).fill(`quote-guest-${f.suffix}@example.invalid`);for(const field of delivery.profile.fields)await page.getByRole('textbox',{name:field.label.tr,exact:true}).fill(String(delivery.values[field.id]));await page.getByRole('checkbox',{name:/Aydınlatma metnini okudum/}).check();await page.getByRole('checkbox',{name:/Ön bilgilendirme/}).check();
  const coupon=page.getByRole('textbox',{name:'İndirim kodu',exact:true});await coupon.fill(f.couponCode);await coupon.focus();await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Kodu uygula',exact:true})).toBeFocused();await page.keyboard.press('Enter');await expect.poll(()=>quotes.filter(quote=>quote.discountMinor>0).length).toBeGreaterThan(0);const discounted=quotes.filter(quote=>quote.discountMinor>0).at(-1)!;expect(discounted.discountMinor).toBe(1235);await assertAmounts(page,discounted);expect(await financialState(f)).toEqual(baseline);
  await mkdir('docs/screenshots',{recursive:true});for(const viewport of [{width:1440,height:1000,name:'desktop'},{width:390,height:844,name:'mobile'}]){await page.setViewportSize({width:viewport.width,height:viewport.height});await page.evaluate(()=>document.fonts.ready);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await assertAmounts(page,discounted);const a11y=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(a11y.violations).toEqual([]);await page.screenshot({path:`docs/screenshots/checkout-quote-${test.info().project.name}-${viewport.name}.png`,fullPage:true});}
  await f.pool.query("UPDATE variant_prices SET amount_minor=14345 WHERE variant_id=$1 AND currency='TRY'",[f.variantId]);
  const continueButton=page.getByRole('button',{name:'Ödemeye devam et',exact:true});await continueButton.click();await expect.poll(()=>attempts.length).toBe(1);expect(attempts[0].status).toBe(409);expect(attempts[0].data.code).toBe('CHECKOUT_QUOTE_CHANGED');expect(await financialState(f)).toEqual(baseline);await expect(page).toHaveURL(/\/odeme$/);
  await expect.poll(()=>quotes.filter(quote=>quote.lines[0]?.unitMinor===14345).length).toBeGreaterThan(0);const refreshed=quotes.filter(quote=>quote.lines[0]?.unitMinor===14345).at(-1)!;await assertAmounts(page,refreshed);await expect(continueButton).toBeEnabled();expect(attempts).toHaveLength(1);expect(await financialState(f)).toEqual(baseline);
  await continueButton.click();await expect.poll(()=>attempts.length).toBe(2);expect(attempts[1].status).toBe(200);const success=attempts[1].data as unknown as CheckoutResult;expect(success.totalMinor).toBe(refreshed.totalMinor);expect(success.currency).toBe(refreshed.currency);expect(attempts[1].request.idempotencyKey).toBe(attempts[0].request.idempotencyKey);await expect(page.getByRole('heading',{name:'Test ödemesi',exact:true})).toBeVisible();
  const [order]=(await f.pool.query('SELECT o.id,o.cart_id,o.subtotal_minor,o.discount_minor,o.shipping_minor,o.tax_minor,o.total_minor,p.amount_minor,p.status FROM orders o JOIN payments p ON p.order_id=o.id WHERE o.id=$1 AND o.cart_id=$2',[success.orderId,cart.id])).rows;expect(order).toMatchObject({subtotal_minor:refreshed.subtotalMinor,discount_minor:refreshed.discountMinor,shipping_minor:refreshed.shippingMinor,tax_minor:refreshed.taxMinor,total_minor:refreshed.totalMinor,amount_minor:refreshed.totalMinor,status:'pending'});const state=await financialState(f);expect(state).toMatchObject({orders:1,items:1,payments:1,reservations:1,coupon_usage:1,coupon_used:0,on_hand:3});
 }finally{await page.unrouteAll({behavior:'wait'}).catch(()=>{});await f.cleanup();}
});

test('quote capabilities cannot move between guest carts or accept caller supplied amounts',async({page,browser})=>{
 const f=await fixture(),other=await browser.newContext({baseURL:origin});
 try{
  await putCart(page.request,f);await putCart(other.request,f);const baseline=await financialState(f),input={country:'TR',currency:'TRY',locale:'tr',couponCode:f.couponCode};
  const quoted=await page.request.post('/api/checkout/quote',{headers:{Origin:origin},data:input});expect(quoted.status()).toBe(200);expect(quoted.headers()['cache-control']).toContain('no-store');const quote=await quoted.json() as CheckoutQuote;expect(quote.lines[0]).toMatchObject({variantId:f.variantId,unitMinor:12345});expect(await financialState(f)).toEqual(baseline);
  for(const extra of [{priceMinor:1},{discountMinor:12345}]){const rejected=await page.request.post('/api/checkout/quote',{headers:{Origin:origin},data:{...input,...extra}});expect(rejected.status()).toBe(400);}
  const delivery=await address(other.request),checkout={...delivery.values,email:`quote-other-${f.suffix}@example.invalid`,...input,idempotencyKey:randomUUID(),privacyAccepted:true,termsAccepted:true,quoteToken:quote.quoteToken};
  const foreign=await other.request.post('/api/checkout',{headers:{Origin:origin},data:checkout});expect(foreign.status()).toBe(409);const failure=await foreign.json();expect(failure.code).toBe('CHECKOUT_QUOTE_CHANGED');expect(JSON.stringify(failure).includes('quote-guest')).toBe(false);
  const forged=await page.request.post('/api/checkout',{headers:{Origin:origin},data:{...checkout,idempotencyKey:randomUUID(),totalMinor:1}});expect(forged.status()).toBe(400);expect(await financialState(f)).toEqual(baseline);
 }finally{await other.close();await f.cleanup();}
});

for(const mode of ['checkout','test-payment'] as const){
test(`a delayed A ${mode} response cannot redirect or expose the order after B signs in`,async({page})=>{
 test.setTimeout(90000);const f=await fixture(),users:string[]=[];
 let release=()=>{},settled=()=>{},held:{status:number;data:Record<string,unknown>;request:Record<string,unknown>}|null=null,createdCheckout:CheckoutResult|null=null,deliveryOutcome:'fulfilled'|'cancelled'|null=null,handlerError:unknown;
 const gate=new Promise<void>(resolve=>{release=resolve;}),finished=new Promise<void>(resolve=>{settled=resolve;});
 try{
  const {getAuth}=await import('../../src/server/auth');
  async function account(label:string,install:boolean){const email=`quote-owner-${label}-${f.suffix}@example.invalid`,password=randomBytes(24).toString('base64url'),signup=await getAuth().api.signUpEmail({body:{email,password,name:`Teklif Hesabı ${label} ${f.suffix}`},returnHeaders:true});users.push(signup.response.user.id);if(install)await page.context().addCookies(signup.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],separator=pair.indexOf('=');return {name:pair.slice(0,separator),value:pair.slice(separator+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));return {id:signup.response.user.id,email:signup.response.user.email,password,name:signup.response.user.name};}
  const a=await account('A',true),b=await account('B',false);
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',url:origin},{name:'sexsogate_country',value:'TR',url:origin},{name:'sexsogate_currency',value:'TRY',url:origin}]);
  await page.route(url=>url.pathname==='/api/cart',async route=>{const response=await route.fetch();if(response.ok()){const cart=await response.json() as Cart;if(cart.id)f.cartIds.add(cart.id);}await route.fulfill({response});});
  const cart=await putCart(page.request,f);expect((await f.pool.query('SELECT user_id FROM carts WHERE id=$1',[cart.id])).rows[0].user_id).toBe(a.id);
  const delivery=await address(page.request);await page.goto('/odeme');await expect(page.getByRole('textbox',{name:'E-posta',exact:true})).toHaveValue(a.email);
  for(const field of delivery.profile.fields)await page.getByRole('textbox',{name:field.label.tr,exact:true}).fill(String(delivery.values[field.id]));await page.getByRole('checkbox',{name:/Aydınlatma metnini okudum/}).check();await page.getByRole('checkbox',{name:/Ön bilgilendirme/}).check();
  if(mode==='test-payment')await page.route(url=>url.pathname==='/api/checkout',async route=>{const response=await route.fetch();if(response.ok())createdCheckout=await response.json() as CheckoutResult;await route.fulfill({response});});
  await page.route(url=>url.pathname===`/api/${mode}`,async route=>{
   try{const response=await route.fetch();held={status:response.status(),data:await response.json() as Record<string,unknown>,request:route.request().postDataJSON()};await gate;try{await route.fulfill({response});deliveryOutcome='fulfilled';}catch(error){if(!/Invalid InterceptionId|Invalid interception id|Unknown interception id|interception.*(?:not found|cancel)|Request (?:was )?cancel(?:ed|led)/i.test(String(error)))throw error;deliveryOutcome='cancelled';}}
   catch(error){handlerError=error;throw error;}finally{settled();}
  });
  const continueButton=page.getByRole('button',{name:'Ödemeye devam et',exact:true});await expect(continueButton).toBeEnabled();await continueButton.click();
  if(mode==='test-payment'){await expect(page.getByRole('heading',{name:'Test ödemesi',exact:true})).toBeVisible();await page.getByRole('button',{name:'Başarılı ödemeyi dene',exact:true}).click();}
  await expect.poll(()=>held?.status).toBe(200);
  // Gerçek sunucu işlemi tamamlanmıştır; yalnız orijinal HTTP yanıtının teslimi bekler.
  const original=mode==='checkout'?held!.data as unknown as CheckoutResult:createdCheckout!;expect(Boolean(original.orderId&&original.paymentUrl&&original.trackingToken)).toBe(true);expect(held!.data.orderId).toBe(original.orderId);if(mode==='test-payment'){expect(held!.data.ok).toBe(true);expect(held!.data.trackingToken).toBe(original.trackingToken);}
  const before=(await f.pool.query('SELECT o.user_id,o.status,p.status payment_status,r.status reservation_status FROM orders o JOIN payments p ON p.order_id=o.id JOIN reservations r ON r.order_id=o.id WHERE o.id=$1 AND o.cart_id=$2 AND r.variant_id=$3',[original.orderId,cart.id,f.variantId])).rows;expect(before).toEqual([{user_id:a.id,status:mode==='checkout'?'awaiting_payment':'confirmed',payment_status:mode==='checkout'?'pending':'succeeded',reservation_status:mode==='checkout'?'active':'consumed'}]);
  await page.evaluate(marker=>{(window as Window&{__checkoutClientNavigation?:string}).__checkoutClientNavigation=marker;},f.suffix);
  await page.getByRole('link',{name:'Hesabım',exact:true}).click();await expect(page).toHaveURL(/\/hesap$/);expect(await page.evaluate(()=>(window as Window&{__checkoutClientNavigation?:string}).__checkoutClientNavigation)).toBe(f.suffix);await expect(page.getByText(a.name,{exact:true})).toBeVisible();await expect(page.getByText(original.number,{exact:true})).toBeVisible();
  await page.locator('.account-nav').getByRole('button',{name:'Çıkış yap',exact:true}).click();await expect(page.locator('.auth-card')).toBeVisible();await page.locator('.auth-card').getByLabel('E-posta',{exact:true}).fill(b.email);await page.locator('.auth-card').getByLabel('Parola',{exact:true}).fill(b.password);await submitSignIn(page,page.locator('.auth-card').getByRole('button',{name:'Giriş yap',exact:true}));await expect(page.getByText(b.name,{exact:true})).toBeVisible();expect((await(await page.request.get('/api/session')).json()).user.id).toBe(b.id);
  const markers=[original.orderId,original.number,original.paymentUrl,original.trackingToken,a.email];
  await page.evaluate(markers=>{const state={leaked:false,observer:null as MutationObserver|null};const inspect=()=>{const visible=document.body.innerText,links=Array.from(document.querySelectorAll<HTMLAnchorElement>('a')).map(link=>link.href).join('\n'),values=Array.from(document.querySelectorAll<HTMLInputElement|HTMLTextAreaElement>('input,textarea')).map(input=>input.value).join('\n');if(markers.some(marker=>visible.includes(marker)||links.includes(marker)||values.includes(marker)||window.location.href.includes(marker)))state.leaked=true;};state.observer=new MutationObserver(inspect);state.observer.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true});inspect();(window as Window&{__checkoutPrivacyObservation?:typeof state}).__checkoutPrivacyObservation=state;},markers);
  const navigations:string[]=[];page.on('framenavigated',frame=>{if(frame===page.mainFrame())navigations.push(frame.url());});
  release();await finished;expect(handlerError).toBeUndefined();expect(['fulfilled','cancelled'].includes(deliveryOutcome??'')).toBe(true);await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/\/hesap$/);await expect(page.getByText(b.name,{exact:true})).toBeVisible();for(const marker of [original.number,a.email])await expect(page.getByText(marker,{exact:true})).toHaveCount(0);expect(navigations.every(value=>new URL(value).pathname==='/hesap')).toBe(true);expect(await page.evaluate(()=>Boolean((window as Window&{__checkoutPrivacyObservation?:{leaked:boolean}}).__checkoutPrivacyObservation?.leaked))).toBe(false);
  const after=(await f.pool.query('SELECT o.user_id,o.status,p.status payment_status,r.status reservation_status FROM orders o JOIN payments p ON p.order_id=o.id JOIN reservations r ON r.order_id=o.id WHERE o.id=$1 AND o.cart_id=$2 AND r.variant_id=$3',[original.orderId,cart.id,f.variantId])).rows;expect(after).toEqual(before);expect((await f.pool.query("SELECT on_hand FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main'",[f.variantId])).rows[0].on_hand).toBe(mode==='checkout'?3:2);expect((await page.request.get(`/api/orders/${original.orderId}`)).status()).toBe(404);expect((await(await page.request.get('/api/orders')).json()).orders.some((order:{id:string})=>order.id===original.orderId)).toBe(false);
 }finally{
  release();await page.unrouteAll({behavior:'wait'}).catch(()=>{});await page.evaluate(()=>{const browser=window as Window&{__checkoutPrivacyObservation?:{observer:MutationObserver|null};__checkoutClientNavigation?:string};browser.__checkoutPrivacyObservation?.observer?.disconnect();delete browser.__checkoutPrivacyObservation;delete browser.__checkoutClientNavigation;}).catch(()=>{});await f.cleanup(users);
 }
});
}
