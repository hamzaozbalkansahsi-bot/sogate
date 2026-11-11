/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/staff-orders.spec.ts
 * Açıklama   : Depo rolünün sipariş ayrıntısından doğrulamalı manuel sevke ulaşmasını sınar.
 */
import {prepareMfaFixture} from './helpers/mfa';
import {test,expect} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
test('Depo personeli SKU doğrulamasıyla toplar, paketler ve yalnız kalan adedi gerçek takip ile sevk eder',async({page})=>{
 test.skip(!['test','development'].includes(process.env.APP_ENV??''),'Yalnız izole yerel geliştirme/test verisi');
 const databaseUrl=new URL(process.env.DATABASE_URL??'');if(!['127.0.0.1','localhost'].includes(databaseUrl.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(databaseUrl.pathname))throw new Error('Personel E2E verisi yalnız bu projenin yerel geliştirme/test veritabanına yazılabilir.');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL}),suffix=randomBytes(7).toString('hex'),password=randomBytes(24).toString('base64url'),sku=`STAFF-UI-${suffix}`,origin='http://127.0.0.1:3000';let userId='',productId='',variantId='',orderId='',cartId='';
 try{
  // Personel iş akışı sınanır; fixture hazırlığı herkese açık kayıt kotasını tüketmez.
  const {getAuth}=await import('../../src/server/auth');
  const signup=await getAuth().api.signUpEmail({body:{email:`staff-${suffix}@example.invalid`,password,name:'Depo Akış Testi'},returnHeaders:true});userId=signup.response.user.id;
  await page.context().addCookies(signup.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],separator=pair.indexOf('=');return {name:pair.slice(0,separator),value:pair.slice(separator+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));
  await pool.query("UPDATE \"user\" SET role='admin' WHERE id=$1",[userId]);
  const verified=await prepareMfaFixture(page.context(),password);expect(verified.ok()).toBeTruthy();
  const created=await page.request.post('/api/admin/products',{headers:{origin},data:{name:'Depo doğrulama ürünü',nameEn:'Warehouse verification',slug:`staff-ui-${suffix}`,category:'aksesuarlar',sku,variantName:'Standart',variantNameEn:'Standard',priceMinor:10000,image:'/media/atelier-01.svg',taxClass:'*'}});expect(created.ok(),await created.text()).toBeTruthy();({id:productId,variantId}=await created.json());
  const invalidPreference=await page.request.post('/api/favorites?currency=BAD',{headers:{origin},data:{productId,active:true}});expect(invalidPreference.status()).toBe(400);expect((await pool.query('SELECT count(*)::int n FROM wishlists WHERE user_id=$1',[userId])).rows[0].n).toBe(0);
  cartId=(await pool.query('INSERT INTO carts(token_hash) VALUES($1) RETURNING id',[randomBytes(32).toString('hex')])).rows[0].id;
  orderId=(await pool.query("INSERT INTO orders(cart_id,idempotency_key,request_hash,tracking_hash,status,payment_status,currency,subtotal_minor,shipping_minor,tax_minor,total_minor,email,address,snapshot,expires_at) VALUES($1,$2,$2,$2,'confirmed','succeeded','TRY',20000,0,0,20000,'private-staff@example.invalid',$3,'{}',now()+interval '15 minutes') RETURNING id",[cartId,suffix,JSON.stringify({fullName:'Yerel Depo Testi',phone:'05000000000',line1:'İstanbul Şişli Çeşme 12',city:'İstanbul',postalCode:'34000',country:'TR'})])).rows[0].id;
  await pool.query("INSERT INTO order_items(order_id,variant_id,name,sku,quantity,unit_minor,cost_minor,snapshot) VALUES($1,$2,'Depo doğrulama ürünü',$3,2,10000,2500,'{}')",[orderId,variantId,sku]);await pool.query("UPDATE \"user\" SET role='warehouse' WHERE id=$1",[userId]);
  const number=(await pool.query('SELECT number FROM orders WHERE id=$1',[orderId])).rows[0].number;
  const projected=await page.request.get(`/api/admin/orders/${orderId}`);expect(projected.ok(),await projected.text()).toBeTruthy();expect(projected.headers()['cache-control']).toContain('no-store');const projectedBody=await projected.json();expect(projectedBody.items[0].sku).toBe(sku);expect(projectedBody).not.toHaveProperty('contact');expect(projectedBody).not.toHaveProperty('totals');expect(projectedBody).not.toHaveProperty('payment');expect(projectedBody).not.toHaveProperty('history');
  await page.goto('/yonetim/orders');await page.getByRole('searchbox',{name:'Kayıtlarda ara'}).fill(number);await page.getByRole('button',{name:'Ara',exact:true}).click();await page.getByRole('row').filter({hasText:number}).getByRole('button',{name:'Siparişi aç'}).click();
  const detail=page.getByRole('dialog',{name:'Sipariş ayrıntısı'});await expect(detail.getByText(number,{exact:true})).toBeVisible();await expect(detail).not.toContainText('private-staff@example.invalid');await expect(detail).not.toContainText('Alış maliyeti');await expect(detail).not.toContainText('Tahsilat toplamı');
  await detail.getByLabel(`Paket adedi · ${sku}`,{exact:true}).fill('1');await detail.getByRole('button',{name:'Paket hazırlığı oluştur',exact:true}).click();
  const picking=detail.getByRole('form',{name:'Toplama doğrulaması'});await picking.getByLabel('Barkod veya stok kodu',{exact:true}).fill(sku);await picking.getByRole('button',{name:'Toplamayı doğrula',exact:true}).click();
  const packing=detail.getByRole('form',{name:'Paketleme doğrulaması'});await packing.getByLabel('Barkod veya stok kodu',{exact:true}).fill(sku);await packing.getByRole('button',{name:'Paketlemeyi doğrula',exact:true}).click();
  const shipping=detail.getByRole('form',{name:'Manuel sevkiyat'});await shipping.getByLabel('Gerçek taşıyıcı adı',{exact:true}).fill('Taşıyıcı belge kaydı');await shipping.getByLabel('Gerçek takip numarası',{exact:true}).fill(`TRACK-${suffix}`);await shipping.getByRole('button',{name:'Manuel sevki kaydet',exact:true}).click();await expect(detail.getByText('Sevk edildi',{exact:true}).first()).toBeVisible();
  expect((await pool.query('SELECT count(*)::int n FROM shipments WHERE order_id=$1',[orderId])).rows[0].n).toBe(1);expect((await pool.query('SELECT quantity FROM shipment_items WHERE shipment_id IN(SELECT id FROM shipments WHERE order_id=$1)',[orderId])).rows[0].quantity).toBe(1);
  await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:'docs/screenshots/staff-order-mobile.png',fullPage:true});
 }finally{
  if(userId)await pool.query('DELETE FROM wishlists WHERE user_id=$1',[userId]);if(orderId){await pool.query('DELETE FROM fulfillment_commands WHERE order_id=$1',[orderId]);await pool.query('DELETE FROM fulfillment_task_items WHERE task_id IN(SELECT id FROM fulfillment_tasks WHERE order_id=$1)',[orderId]);await pool.query('DELETE FROM fulfillment_tasks WHERE order_id=$1',[orderId]);await pool.query('DELETE FROM shipment_items WHERE shipment_id IN(SELECT id FROM shipments WHERE order_id=$1)',[orderId]);await pool.query('DELETE FROM shipments WHERE order_id=$1',[orderId]);await pool.query('DELETE FROM order_history WHERE order_id=$1',[orderId]);await pool.query('DELETE FROM order_items WHERE order_id=$1',[orderId]);await pool.query('DELETE FROM orders WHERE id=$1',[orderId]);}if(cartId)await pool.query('DELETE FROM carts WHERE id=$1',[cartId]);if(variantId){await pool.query('DELETE FROM variant_prices WHERE variant_id=$1',[variantId]);await pool.query('DELETE FROM inventory_balance WHERE variant_id=$1',[variantId]);await pool.query('DELETE FROM variants WHERE id=$1',[variantId]);}if(productId)await pool.query('DELETE FROM products WHERE id=$1',[productId]);if(userId)await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);await pool.end();
 }
});
