/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/locale.spec.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {test,expect} from "@playwright/test";
import pg from "pg";
import {randomBytes} from "node:crypto";
test("English URL wins over a Turkish cookie and internal links preserve the language",async({page})=>{
 await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"},{name:"sexsogate_locale",value:"tr",domain:"127.0.0.1",path:"/"}]);
 await page.goto("/en");await expect(page.getByRole("heading",{name:/Discover.*your desire/})).toBeVisible();await expect(page.locator("html")).toHaveAttribute("lang","en");
 const products=page.locator(".desktop-nav").getByRole("link",{name:"Products",exact:true});await expect(products).toHaveAttribute("href","/en/urunler");await products.click();await expect(page).toHaveURL(/\/en\/urunler$/);await expect(page.locator(".product-card .product-link").first()).toHaveAttribute("href",/^\/en\/urun\//);
 await page.goto("/en/urunler?q=Maske");await page.locator(".announcement button").click();const preferences=page.getByRole("dialog",{name:"Shopping preferences"});await preferences.getByRole("combobox",{name:"Language",exact:true}).selectOption("tr");await preferences.getByRole("button",{name:"Apply preferences",exact:true}).click();await expect(page).toHaveURL(/\/urunler\?q=Maske$/);await expect(page.locator("html")).toHaveAttribute("lang","tr");await expect(page.locator(".desktop-nav").getByRole("link",{name:"Ürünler",exact:true})).toHaveAttribute("href","/urunler");
});

async function marketFixture(){
 const databaseUrl=new URL(process.env.DATABASE_URL??'http://invalid');if(!['development','test'].includes(process.env.APP_ENV??'')||!['127.0.0.1','localhost','[::1]'].includes(databaseUrl.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(databaseUrl.pathname))throw new Error('Pazar E2E hazırlığı yalnız projenin yerel geliştirme/test veritabanında çalışabilir.');
 const pool=new pg.Pool({connectionString:databaseUrl.href});
 const suffix=randomBytes(6).toString("hex");let productId="",variantId="";const codes:string[]=[],profileIds:string[]=[],taxIds:string[]=[];
 async function cleanup(){try{if(variantId){await pool.query("DELETE FROM cart_items WHERE variant_id=$1",[variantId]);await pool.query("DELETE FROM inventory_balance WHERE variant_id=$1",[variantId]);await pool.query("DELETE FROM variant_prices WHERE variant_id=$1",[variantId]);await pool.query("DELETE FROM product_eligibility WHERE variant_id=$1",[variantId]);await pool.query("DELETE FROM variants WHERE id=$1",[variantId]);}if(productId)await pool.query("DELETE FROM products WHERE id=$1",[productId]);await pool.query('DELETE FROM country_address_events WHERE profile_id=ANY($1::text[])',[profileIds]);await pool.query('DELETE FROM country_address_profiles WHERE id=ANY($1::text[]) AND country=ANY($2::text[]) AND fixture=true',[profileIds,codes]);await pool.query('DELETE FROM settings WHERE key=ANY($1::text[])',[taxIds.map(id=>`tax.source.${id}`)]);await pool.query('DELETE FROM tax_rules WHERE id=ANY($1::text[]) AND country=ANY($2::text[]) AND fixture=true',[taxIds,codes]);for(const code of codes)await pool.query("DELETE FROM country_rules WHERE code=$1 AND fixture=true",[code]);}finally{await pool.end();}}
 try{
  const free=(await pool.query("SELECT 'X'||letter code FROM unnest(ARRAY['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])letter WHERE NOT EXISTS(SELECT 1 FROM country_rules c WHERE c.code='X'||letter) LIMIT 2")).rows;
  expect(free).toHaveLength(2);codes.push(String(free[0].code),String(free[1].code));
  await pool.query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES($1,'Yerel Test Teslimatı',true,true,true,true,true,true,true,0,'USD',true),($2,'Kapalı Test Teslimatı',true,true,true,false,true,true,true,0,'USD',true)",codes);
  // Gerçek bir ülke oranı değildir: yalnız bu izole hayali pazarın kanonik teklif verisi.
  const tax=(await pool.query("INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,fixture) VALUES($1,'*',0,now()-interval '1 minute',true) RETURNING id",[codes[0]])).rows[0];taxIds.push(tax.id);
  await pool.query('INSERT INTO settings(key,value) VALUES($1,$2)',[`tax.source.${tax.id}`,JSON.stringify(`Yalnız ${suffix} yerel pazar testi için sıfır oran; gerçek ülke vergi kuralı değildir.`)]);
  const {seedFixtureAddressProfile}=await import('../../scripts/seed');const profile=await seedFixtureAddressProfile(pool,codes[0]);if(profile.created&&profile.id)profileIds.push(profile.id);
  const category=(await pool.query("SELECT slug FROM categories WHERE active=true ORDER BY slug LIMIT 1")).rows[0].slug;
  const slug=`market-check-${suffix}`;
  productId=(await pool.query("INSERT INTO products(slug,name,name_en,description,description_en,category,image,status,fixture,warnings,care,translations) VALUES($1,'Para Birimi Maskesi','Currency Selection Mask','Yerel katalog doğrulaması.','Local catalog verification.',$2,'/media/atelier-01.svg','published',true,'Yalnız yetişkinler içindir.','Üretici talimatlarını izleyin.','{\"en\":{\"warnings\":\"For adults only.\",\"care\":\"Follow manufacturer instructions.\"}}') RETURNING id",[slug,category])).rows[0].id;
  variantId=(await pool.query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,currency) VALUES($1,$2,'Standart','Standard',99900,'TRY') RETURNING id",[productId,`MARKET-${suffix}`])).rows[0].id;
  await pool.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',99900),($1,'EUR',1234),($1,'USD',5678)",[variantId]);
  await pool.query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',2)",[variantId]);
  await pool.query("INSERT INTO product_eligibility(variant_id,country,approved,review_note,approved_by,approved_at)VALUES($1,$2,true,'Yalnız bu izole yerel pazar testi',$3,now())",[variantId,codes[0],`locale-fixture-${suffix}`]);
  return {pool,productId,variantId,slug,country:codes[0],blockedCountry:codes[1],cleanup};
 }catch(error){await cleanup();throw error;}
}

test("approved delivery country, language, display price and settlement currency remain independent",async({page})=>{
 test.skip(!["development","test"].includes(process.env.APP_ENV??""),"Yalnız yerel/test veritabanı");
 const fixture=await marketFixture();
 try{
  const response=await page.request.get("/api/markets");expect(response.ok()).toBeTruthy();const markets=await response.json();
  expect(markets.markets.find((m:{countryCode:string})=>m.countryCode===fixture.country)?.settlementCurrency).toBe("USD");expect(markets.markets.some((m:{countryCode:string})=>m.countryCode===fixture.blockedCountry)).toBe(false);
  const product=(await (await page.request.get(`/api/catalog/${fixture.slug}?locale=en&currency=EUR`)).json()).product;
  expect(product.variants[0].displayPriceMinor).toBe(1234);expect(product.variants[0].displayCurrency).toBe("EUR");expect(product.variants[0].priceMinor).toBe(99900);
  await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"},{name:"sexsogate_currency",value:"EUR",domain:"127.0.0.1",path:"/"},{name:"sexsogate_country",value:fixture.country,domain:"127.0.0.1",path:"/"}]);
  await page.goto(`/en/urun/${fixture.slug}`);await expect(page.locator(".product-price")).toContainText("€12.34");await page.getByRole("button",{name:"Add to bag",exact:true}).click();await expect(page.locator(".feedback[role=status]")).toContainText("Added to your bag");
  await page.goto("/en/sepet");await expect(page.locator(".cart-line-total")).toContainText("€12.34");
  const quoteResponse=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/checkout/quote'&&response.request().method()==='POST').then(async response=>({status:response.status(),body:await response.json()}));
  await page.goto("/en/odeme");const quote=await quoteResponse;expect(quote.status).toBe(200);expect(quote.body.currency).toBe('USD');expect(quote.body.lines).toEqual([expect.objectContaining({variantId:fixture.variantId,unitMinor:5678,quantity:1})]);expect(quote.body.totalMinor).toBe(5678);await expect(page.locator(".order-summary")).toContainText("US$56.78");await expect(page.getByRole("note")).toContainText("collected in USD");
  await page.locator(".announcement button").click();const preferences=page.getByRole("dialog",{name:"Shopping preferences"});await expect(preferences.getByRole("combobox",{name:"Delivery country",exact:true})).toHaveValue(fixture.country);await expect(preferences.getByRole("combobox",{name:"Display currency",exact:true})).toHaveValue("EUR");await preferences.getByRole("combobox",{name:"Language",exact:true}).selectOption("tr");await preferences.getByRole("button",{name:"Apply preferences",exact:true}).click();await expect(page).toHaveURL(/\/odeme$/);await expect(page.getByRole("note")).toContainText("USD");
  const cookies=await page.context().cookies();expect(cookies.find(c=>c.name==="sexsogate_country")?.value).toBe(fixture.country);expect(cookies.find(c=>c.name==="sexsogate_currency")?.value).toBe("EUR");
 }finally{await fixture.cleanup();}
});

test("a missing requested price list is null and blocks adding and checkout",async({page})=>{
 test.skip(!["development","test"].includes(process.env.APP_ENV??""),"Yalnız yerel/test veritabanı");
 const fixture=await marketFixture();
 try{
  const response=await page.request.get(`/api/catalog/${fixture.slug}?locale=en&currency=GBP`);expect(response.ok()).toBeTruthy();const data=await response.json();expect(data.product.variants[0].displayPriceMinor).toBeNull();
  await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"},{name:"sexsogate_currency",value:"GBP",domain:"127.0.0.1",path:"/"},{name:"sexsogate_country",value:fixture.country,domain:"127.0.0.1",path:"/"}]);
  await page.goto(`/en/urun/${fixture.slug}`);await expect(page.locator(".product-price")).toContainText("Price unavailable in GBP");await expect(page.getByRole("button",{name:"Add to bag",exact:true})).toBeDisabled();
  expect((await page.request.post("/api/cart",{headers:{origin:"http://127.0.0.1:3000"},data:{variantId:fixture.variantId,quantity:1}})).ok()).toBeTruthy();
  await page.goto("/en/odeme");await expect(page.getByRole("button",{name:"Continue to payment",exact:true})).toBeDisabled();await expect(page.getByRole("alert").filter({hasText:"GBP"})).toContainText("GBP");
 }finally{await fixture.cleanup();}
});

test("product language changes use translated aliases and preserve query and hash",async({page},info)=>{
 test.skip(!["development","test"].includes(process.env.APP_ENV??""),"Yalnız yerel/test veritabanı");
 const fixture=await marketFixture(),suffix=fixture.slug.replace("market-check-",""),tr=`dil-tr-${suffix}`,en=`language-en-${suffix}`;
 try{
  await fixture.pool.query("UPDATE product_routes SET slug=CASE WHEN locale='tr' THEN $2 ELSE $3 END WHERE product_id=$1",[fixture.productId,tr,en]);
  await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"}]);
  await page.goto(`/urun/${tr}?selection=mask#urun-bilgileri`);await expect(page.getByRole("heading",{name:"Para Birimi Maskesi",exact:true})).toBeVisible();
  await expect(page.locator('link[rel="alternate"][hreflang="en"]')).toHaveAttribute("href",new RegExp(`/en/urun/${en}$`));
  const englishAPI=await page.request.get(`/api/catalog/${en}?locale=en&currency=TRY`);expect(englishAPI.status()).toBe(200);expect((await englishAPI.json()).product.nameEn).toBe("Currency Selection Mask");const englishDocument=await page.request.get(`/en/urun/${en}?selection=mask`),englishHTML=await englishDocument.text();const diagnostic={apiStatus:englishAPI.status(),documentStatus:englishDocument.status(),htmlLanguage:/<html[^>]*lang="([^"]+)"/.exec(englishHTML)?.[1],englishTitle:englishHTML.includes("Currency Selection Mask"),englishNotFound:englishHTML.includes("Product not found"),turkishNotFound:englishHTML.includes("Ürün bulunamadı")};console.log(JSON.stringify(diagnostic));await info.attach("alias-document-diagnostic",{body:JSON.stringify(diagnostic),contentType:"application/json"});expect(englishDocument.status()).toBe(200);expect(englishHTML).toContain("Currency Selection Mask");
  await page.locator(".announcement button").click();let preferences=page.getByRole("dialog",{name:"Alışveriş tercihleri"});await preferences.getByRole("combobox",{name:"Dil",exact:true}).selectOption("en");await preferences.getByRole("button",{name:"Tercihleri uygula",exact:true}).click();
  expect(englishHTML).toMatch(/<html[^>]*lang="en"/);expect(englishHTML).toContain('property="og:locale" content="en_GB"');expect(englishHTML).toContain(`<title>Currency Selection Mask`);
  await expect(page).toHaveURL(new RegExp(`/en/urun/${en}\\?selection=mask#urun-bilgileri$`));await expect(page.getByRole("heading",{name:"Currency Selection Mask",exact:true})).toBeVisible();await expect(page.locator('link[rel="alternate"][hreflang="tr-TR"]')).toHaveAttribute("href",new RegExp(`/urun/${tr}$`));
  await page.locator(".announcement button").click();preferences=page.getByRole("dialog",{name:"Shopping preferences"});await preferences.getByRole("combobox",{name:"Language",exact:true}).selectOption("tr");await preferences.getByRole("button",{name:"Apply preferences",exact:true}).click();
  await expect(page).toHaveURL(new RegExp(`/urun/${tr}\\?selection=mask#urun-bilgileri$`));await expect(page.getByRole("heading",{name:"Para Birimi Maskesi",exact:true})).toBeVisible();
 }finally{await fixture.cleanup();}
});

test("missing English product translation opens the English catalog",async({page})=>{
 test.skip(!["development","test"].includes(process.env.APP_ENV??""),"Yalnız yerel/test veritabanı");
 const fixture=await marketFixture(),tr=`ceviri-tr-${fixture.slug.replace("market-check-","")}`;
 try{
  await fixture.pool.query("UPDATE product_routes SET slug=$2 WHERE product_id=$1 AND locale='tr'",[fixture.productId,tr]);await fixture.pool.query("UPDATE products SET name_en='',description_en='' WHERE id=$1",[fixture.productId]);
  await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"}]);await page.goto(`/urun/${tr}?selection=mask#urun-bilgileri`);await expect(page.getByRole("heading",{name:"Para Birimi Maskesi",exact:true})).toBeVisible();await expect(page.locator('link[rel="alternate"][hreflang="en"]')).toHaveCount(0);
  await page.locator(".announcement button").click();const preferences=page.getByRole("dialog",{name:"Alışveriş tercihleri"});await preferences.getByRole("combobox",{name:"Dil",exact:true}).selectOption("en");await preferences.getByRole("button",{name:"Tercihleri uygula",exact:true}).click();
  await expect(page).toHaveURL(/\/en\/urunler\?selection=mask#urun-bilgileri$/);await expect(page.getByRole("heading",{name:"All products",exact:true})).toBeVisible();
 }finally{await fixture.cleanup();}
});

test("foreign product alternate cannot redirect a language choice off site",async({page})=>{
 test.skip(!["development","test"].includes(process.env.APP_ENV??""),"Yalnız yerel/test veritabanı");
 const fixture=await marketFixture();
 try{
  await page.context().addCookies([{name:"sexsogate_adult",value:"yes",domain:"127.0.0.1",path:"/"}]);await page.goto(`/urun/${fixture.slug}?selection=mask#urun-bilgileri`);await expect(page.locator('link[rel="alternate"][hreflang="en"]')).toHaveCount(1);
  await page.locator('link[rel="alternate"][hreflang="en"]').evaluate(element=>element.setAttribute("href","http://127.0.0.1:3009/en/urun/foreign-alternate"));
  await page.locator(".announcement button").click();const preferences=page.getByRole("dialog",{name:"Alışveriş tercihleri"});await preferences.getByRole("combobox",{name:"Dil",exact:true}).selectOption("en");await preferences.getByRole("button",{name:"Tercihleri uygula",exact:true}).click();
  await expect(page).toHaveURL(/http:\/\/127\.0\.0\.1:3000\/en\/urunler\?selection=mask#urun-bilgileri$/);await expect(page.getByRole("heading",{name:"All products",exact:true})).toBeVisible();
 }finally{await fixture.cleanup();}
});
