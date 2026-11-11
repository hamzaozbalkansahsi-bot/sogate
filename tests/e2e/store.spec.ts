/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/store.spec.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { test, expect } from "@playwright/test";
import {createHash,randomBytes,randomUUID} from 'node:crypto';
import pg from 'pg';

test("adult notice traps focus and admits with keyboard", async ({ page }) => {
  await page.goto("/");
  const notice = page.getByRole("dialog", { name: "Yetişkinlere özel bir dünya" });
  await expect(notice).toBeVisible();
  await notice.getByRole("button", { name: "18 yaşından büyüğüm" }).focus();
  await page.keyboard.press("Enter");
  await expect(notice).not.toBeVisible();
  await expect(page.getByRole("heading", { name: /Tutkunu/ })).toBeVisible();
});

test("catalog, server cart, test checkout and private order", async ({ page }) => {
  const databaseUrl=new URL(process.env.DATABASE_URL??'http://invalid');
  if(!['development','test'].includes(process.env.APP_ENV??'')||!['127.0.0.1','localhost','[::1]'].includes(databaseUrl.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(databaseUrl.pathname)||process.env.PAYMENT_PROVIDER!=='test')throw new Error('Misafir alışveriş E2E yalnız projenin yerel test verisi ve test ödeme sağlayıcısıyla çalışabilir.');
  const pool=new pg.Pool({connectionString:databaseUrl.href}),suffix=randomBytes(8).toString('hex'),productId=randomUUID(),variantId=randomUUID(),slug=`guest-checkout-${suffix}`,sku=`GUEST-UI-${suffix}`;
  try{
  const setup=await pool.connect();
  try{
    await setup.query('BEGIN');
    const [category]=(await setup.query('SELECT slug FROM categories WHERE active=true ORDER BY slug LIMIT 1')).rows;expect(category).toBeTruthy();
    await setup.query("INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,material,status,warnings,care,fixture,translations) VALUES($1,$2,$3,$4,$5,$6,$7,'/media/atelier-01.svg','Saten','published',$8,$9,true,$10)",[productId,slug,`Misafir Akış Maskesi ${suffix}`,`Guest Flow Mask ${suffix}`,'Yalnız bu yerel testin kendine ait katalog kaydı.','Catalog record owned by this isolated local test.',category.slug,'Yalnız yetişkinler içindir.','Üretici etiketini kontrol edin.',JSON.stringify({en:{warnings:'For adults only.',care:'Check the manufacturer label.'}})]);
    await setup.query("INSERT INTO variants(id,product_id,sku,name,name_en,price_minor,cost_minor,currency) VALUES($1,$2,$3,'Bordo · Standart','Burgundy · Standard',99900,1000,'TRY')",[variantId,productId,sku]);
    await setup.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',99900)",[variantId]);
    await setup.query("INSERT INTO product_eligibility(variant_id,country,approved,review_note,approved_by,approved_at) VALUES($1,'TR',true,'Yalnız bu izole yerel misafir alışveriş testi',$2,now())",[variantId,`store-fixture-${suffix}`]);
    await setup.query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',2)",[variantId]);
    await setup.query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference) VALUES($1,'main','receipt',2,'İzole misafir alışveriş testi mal kabulü',$2)",[variantId,`guest-fixture:${suffix}`]);
    await setup.query('COMMIT');
  }catch(error){await setup.query('ROLLBACK');throw error;}finally{setup.release();}
  await page.context().addCookies([{ name: "sexsogate_adult", value: "yes", domain: "127.0.0.1", path: "/" }]);
  await page.goto(`/urunler?q=${encodeURIComponent(suffix)}`);
  await expect(page.locator('.product-card a.product-link')).toHaveCount(1);
  await expect(page.locator('.product-card a.product-link')).toHaveAttribute('href',`/urun/${slug}`);
  await page.locator(".product-card a.product-link").click();
  await page.getByRole("button", { name: "Sepete ekle", exact: true }).click();
  await expect(page.locator(".feedback[role=status]")).toContainText("Sepetinize eklendi");
  await page.goto("/sepet");
  await expect(page.locator(".cart-line").first()).toBeVisible();
  await page.getByRole("link", { name: "Ödemeye geç" }).click();
  await page.getByLabel("E-posta", { exact: true }).fill("checkout@example.test");
  await page.getByLabel("Ad soyad", { exact: true }).fill("Yerel Alışveriş");
  await page.getByLabel("Telefon", { exact: true }).fill("05550001122");
  await page.getByLabel("Adres", { exact: true }).fill("Test Mahallesi Deneme Sokak 12");
  await page.getByLabel("Şehir", { exact: true }).fill("İstanbul");
  await page.getByLabel("Posta kodu", { exact: true }).fill("34000");
  await page.getByLabel(/Aydınlatma metnini okudum/).check();
  await page.getByLabel(/Ön bilgilendirme/).check();
  await page.getByRole("button", { name: "Ödemeye devam et" }).click();
  await expect(page.getByRole("heading", { name: "Test ödemesi" })).toBeVisible();
  await page.getByRole("button", { name: "Başarılı ödemeyi dene" }).click();
  await expect(page.getByRole("heading", { name: "Siparişiniz alındı" })).toBeVisible();
  const location=new URL(page.url());const orderId=location.pathname.split('/').pop();const token=location.searchParams.get('token');
  const document=await page.request.get(`/api/orders/${orderId}/document?token=${encodeURIComponent(token??'')}`);expect(document.ok()).toBeTruthy();expect(document.headers()['content-type']).toBe('application/pdf');expect(document.headers()['cache-control']).toContain('no-store');expect((await document.body()).subarray(0,5).toString()).toBe('%PDF-');
  const agreements=await page.request.get(`/api/orders/${orderId}/document?token=${encodeURIComponent(token??'')}&format=json`);expect((await agreements.json()).agreements).toHaveLength(2);
  expect((await page.request.get(`/api/orders/${orderId}/document`)).status()).toBe(404);
  const ownOrder=(await pool.query('SELECT o.id,o.payment_status,b.on_hand FROM orders o JOIN order_items i ON i.order_id=o.id JOIN inventory_balance b ON b.variant_id=i.variant_id AND b.warehouse_id=\'main\' WHERE o.id=$1 AND i.variant_id=$2',[orderId,variantId])).rows;expect(ownOrder).toEqual([{id:orderId,payment_status:'succeeded',on_hand:1}]);
  }finally{
    const cookie=(await page.context().cookies().catch(()=>[])).find(value=>value.name==='sg_cart'&&value.domain==='127.0.0.1');
    const cleanup=await pool.connect();
    try{
      await cleanup.query('BEGIN');
      // Recover IDs from this fixture's product/SKU relationship even if browser
      // navigation failed after checkout committed. A URL alone never authorizes deletion.
      const owned=(await cleanup.query('SELECT v.id FROM variants v JOIN products p ON p.id=v.product_id WHERE p.id=$1 AND p.slug=$2 AND p.fixture=true AND v.id=$3 AND v.sku=$4',[productId,slug,variantId,sku])).rows.map(value=>value.id);
      const orders=(await cleanup.query('SELECT DISTINCT o.id,o.cart_id FROM orders o JOIN order_items i ON i.order_id=o.id WHERE i.variant_id=ANY($1::text[])',[owned])).rows;
      const orderIds=orders.map(value=>value.id),cartIds=new Set<string>(orders.map(value=>value.cart_id));
      for(const row of (await cleanup.query('SELECT cart_id FROM cart_items WHERE variant_id=ANY($1::text[])',[owned])).rows)cartIds.add(row.cart_id);
      if(cookie)for(const row of (await cleanup.query('SELECT id FROM carts WHERE token_hash=$1 AND user_id IS NULL',[createHash('sha256').update(cookie.value).digest('hex')])).rows)cartIds.add(row.id);
      await cleanup.query('DELETE FROM jobs WHERE payload->>\'orderId\'=ANY($1::text[]) OR dedupe_key=ANY($2::text[])',[orderIds,orderIds.flatMap(id=>[`reservation:${id}`,`confirmation:${id}`,`exception:${id}`])]);
      await cleanup.query('DELETE FROM provider_events WHERE normalized->>\'orderId\'=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM payment_events WHERE payment_id IN(SELECT id FROM payments WHERE order_id=ANY($1::text[]))',[orderIds]);
      await cleanup.query('DELETE FROM reservation_lots WHERE reservation_id IN(SELECT id FROM reservations WHERE order_id=ANY($1::text[]))',[orderIds]);
      await cleanup.query('DELETE FROM reservations WHERE order_id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM order_agreements WHERE order_id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM order_history WHERE order_id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM payments WHERE order_id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM order_items WHERE order_id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM orders WHERE id=ANY($1::text[])',[orderIds]);
      await cleanup.query('DELETE FROM cart_items WHERE variant_id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM carts c WHERE c.id=ANY($1::text[]) AND c.user_id IS NULL AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=c.id) AND NOT EXISTS(SELECT 1 FROM cart_items i WHERE i.cart_id=c.id)',[[...cartIds]]);
      await cleanup.query('DELETE FROM inventory_movements WHERE variant_id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM inventory_balance WHERE variant_id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM variant_prices WHERE variant_id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM product_eligibility WHERE variant_id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM variants WHERE id=ANY($1::text[])',[owned]);
      await cleanup.query('DELETE FROM products WHERE id=$1 AND slug=$2 AND fixture=true',[productId,slug]);
      await cleanup.query('COMMIT');
    }catch(error){await cleanup.query('ROLLBACK');throw error;}finally{cleanup.release();await pool.end();}
  }
});

for (const width of [360, 390, 430, 768, 1440]) {
  test(`home does not overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.context().addCookies([{ name: "sexsogate_adult", value: "yes", domain: "127.0.0.1", path: "/" }]);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Tutkunu/ })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.screenshot({ path: `test-results/home-${width}.png`, fullPage: true });
  });
}
