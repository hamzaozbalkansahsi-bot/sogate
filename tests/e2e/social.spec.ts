/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/social.spec.ts
 * Açıklama   : Gerçek medya ve aynı SKU fiyatından özel, düzenlenebilir SVG indirmesini doğrular.
 */
import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import pg from 'pg';
import {randomBytes,createHash} from 'node:crypto';
import {readFile,rm,mkdir} from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import {prepareMfaFixture} from './helpers/mfa';
const origin='http://127.0.0.1:3000';
test('social SVG uses the selected SKU, actual language and current price without publishing',async({page})=>{
 test.setTimeout(65000);
 test.skip(!['development','test'].includes(process.env.APP_ENV??''),'Yalnız projenin yerel geliştirme/test verisi');
 const url=new URL(process.env.DATABASE_URL??'');if(!['127.0.0.1','localhost'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname)||process.env.STORAGE_PROVIDER==='s3')throw new Error('Sosyal UI testi yalnız bu projenin yerel DB ve dosya depolamasında çalışır.');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL}),suffix=randomBytes(6).toString('hex'),productId=`social-ui-product-${suffix}`,variantId=`social-ui-variant-${suffix}`,otherId=`social-ui-other-${suffix}`,category=`social-ui-${suffix}`,sku=`SOCIAL-UI-${suffix}`;
 let userId='',objectKey='';
 try{
  const {getAuth}=await import('../../src/server/auth'),password=randomBytes(24).toString('base64url');const signup=await getAuth().api.signUpEmail({body:{email:`social-ui-${suffix}@example.invalid`,password,name:'Sosyal Tasarım Testi'},returnHeaders:true});userId=signup.response.user.id;
  await page.context().addCookies(signup.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],separator=pair.indexOf('=');return {name:pair.slice(0,separator),value:pair.slice(separator+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));
  await pool.query('UPDATE "user" SET role=\'marketing\' WHERE id=$1',[userId]);expect((await prepareMfaFixture(page.context(),password)).ok()).toBeTruthy();
  const image=await sharp({create:{width:600,height:600,channels:3,background:'#E7B4BD'}}).webp().toBuffer();
  const upload=await page.request.post('/api/admin/media',{headers:{Origin:origin},multipart:{file:{name:'own-social-test.webp',mimeType:'image/webp',buffer:image},rightsReference:`Özgün yerel test görseli ${suffix}; model ya da üçüncü taraf ürün fotoğrafı içermez.`}});expect(upload.status()).toBe(201);const uploaded=await upload.json();objectKey=`products/${String(uploaded.url).split('/').at(-1)}`;
  await pool.query('INSERT INTO categories(slug,name,name_en) VALUES($1,$2,$3)',[category,'Sosyal test aksesuarı','Social test accessory']);
  await pool.query("INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,status,fixture) VALUES($1,$1,$2,$3,'Kaynak ürün metni','Source product description',$4,$5,'published',true)",[productId,`Özel maske ${suffix}`,`Special mask ${suffix}`,category,uploaded.url]);
  await pool.query("INSERT INTO variants(id,product_id,sku,name,name_en,price_minor) VALUES($1,$2,$3,'Gül kurusu','Dusty rose',12345),($4,$2,$5,'Diğer seçenek','Other option',98765)",[variantId,productId,sku,otherId,`OTHER-${suffix}`]);
  await pool.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',12345),($1,'EUR',4567) ON CONFLICT(variant_id,currency) DO UPDATE SET amount_minor=excluded.amount_minor",[variantId]);
  await page.goto('/yonetim/social');await expect(page.getByRole('heading',{name:'Kataloğunuzdan düzenlenebilir tasarımlar',exact:true})).toBeVisible();
  await page.getByRole('searchbox',{name:'Ürün ara',exact:true}).fill(suffix);await page.getByRole('button',{name:'Ürün ara',exact:true}).click();await expect(page.getByRole('combobox',{name:'Ürün',exact:true}).getByRole('option',{name:`Özel maske ${suffix}`,exact:true})).toHaveCount(1);await page.getByRole('combobox',{name:'Ürün',exact:true}).selectOption(productId);
  await expect(page.getByRole('combobox',{name:'Ürün seçeneği',exact:true}).getByRole('option').filter({hasText:sku})).toHaveCount(1);await page.getByRole('combobox',{name:'Ürün seçeneği',exact:true}).selectOption(variantId);
  await page.getByRole('button',{name:'Tasarımı hazırla',exact:true}).click();const downloadLink=page.getByRole('link',{name:'Düzenlenebilir SVG indir',exact:true});await expect(downloadLink).toBeVisible();
  await expect(page.getByText('Bu tasarım yerel örnek veriden üretildi.',{exact:false})).toBeVisible();
  const a11y=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(a11y.violations).toEqual([]);
  const firstDownload=page.waitForEvent('download');await downloadLink.click();const first=await firstDownload,firstPath=await first.path();expect(firstPath).not.toBeNull();const bytes=await readFile(firstPath!),svg=bytes.toString('utf8');
  expect(svg.includes(sku)).toBe(true);expect(svg.includes(`OTHER-${suffix}`)).toBe(false);expect(svg.includes('123,45')).toBe(true);expect(svg.includes('Özel maske')).toBe(true);expect(svg.includes('data:image/webp;base64,')).toBe(true);expect(svg.includes('SIL OPEN FONT LICENSE')).toBe(true);expect(svg.includes('<script>')).toBe(false);expect(svg.includes('<text')).toBe(true);expect(svg.includes('width="1080" height="1350"')).toBe(true);
  const [audit]=(await pool.query("SELECT details FROM audit_log WHERE actor_id=$1 AND resource='social' ORDER BY created_at DESC LIMIT 1",[userId])).rows;expect(audit.details.source.variantId).toBe(variantId);expect(audit.details.priceMinor).toBe(12345);expect(audit.details.sha256).toBe(createHash('sha256').update(bytes).digest('hex'));
  await page.getByRole('combobox',{name:'Tasarım dili',exact:true}).selectOption('en');await expect(downloadLink).toHaveCount(0);await page.getByRole('combobox',{name:'Şablon',exact:true}).selectOption('story');await page.getByRole('combobox',{name:'Görünüm',exact:true}).selectOption('dark');await page.getByRole('combobox',{name:'Fiyat listesi',exact:true}).selectOption('EUR');
  await expect(page.getByRole('combobox',{name:'Ürün',exact:true}).getByRole('option',{name:`Special mask ${suffix}`,exact:true})).toHaveCount(1);await page.getByRole('combobox',{name:'Ürün',exact:true}).selectOption(productId);await expect(page.getByRole('combobox',{name:'Ürün seçeneği',exact:true}).getByRole('option').filter({hasText:sku})).toHaveCount(1);await page.getByRole('combobox',{name:'Ürün seçeneği',exact:true}).selectOption(variantId);await page.getByRole('button',{name:'Tasarımı hazırla',exact:true}).click();await expect(downloadLink).toBeVisible();
  const secondDownload=page.waitForEvent('download');await downloadLink.click();const second=await secondDownload,secondSVG=(await readFile((await second.path())!)).toString('utf8');expect(secondSVG.includes('Special mask')).toBe(true);expect(secondSVG.includes('Dusty rose')).toBe(true);expect(secondSVG.includes('45.67')).toBe(true);expect(secondSVG.includes('width="1080" height="1920"')).toBe(true);expect(secondSVG.includes(sku)).toBe(true);
  await page.setViewportSize({width:390,height:844});await expect(page.getByRole('img',{name:'Hikâye tasarım önizlemesi',exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await mkdir('docs/screenshots',{recursive:true});await page.screenshot({path:`docs/screenshots/social-${test.info().project.name}-mobile.png`,fullPage:true});
  const forbidden=await page.request.post('/api/admin/social',{headers:{Origin:origin},data:{template:'product',theme:'light',locale:'tr',currency:'TRY',productId,variantId,priceMinor:1}});expect(forbidden.status()).toBe(400);
  await pool.query('UPDATE "user" SET role=\'warehouse\' WHERE id=$1',[userId]);const denied=await page.request.get('/api/admin/social');expect(denied.status()).toBe(403);expect(JSON.stringify(await denied.json()).includes(sku)).toBe(false);
 }finally{
  await pool.query('DELETE FROM audit_log WHERE actor_id=$1',[userId]);await pool.query('DELETE FROM variant_prices WHERE variant_id=ANY($1::text[])',[[variantId,otherId]]);await pool.query('DELETE FROM variants WHERE id=ANY($1::text[])',[[variantId,otherId]]);await pool.query('DELETE FROM products WHERE id=$1',[productId]);await pool.query('DELETE FROM categories WHERE slug=$1',[category]);
  if(objectKey){await pool.query('DELETE FROM media_assets WHERE object_key=$1 AND actor_id=$2',[objectKey,userId]);const root=path.resolve(process.env.STORAGE_LOCAL_PATH??'.local/media'),file=path.resolve(root,objectKey);if(file.startsWith(root+path.sep)&&/^products\/[a-f0-9-]{36}\.webp$/.test(objectKey))await rm(file,{force:true});}
  if(userId)await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);await pool.end();
 }
});
