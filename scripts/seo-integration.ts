/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/seo-integration.ts
 * Açıklama   : SEO düzenleme, dil bazlı tekil yollar, yönlendirme ve rapor güvenliğini izole veritabanında sınar.
 */
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
const base=process.env.TEST_DATABASE_URL;if(!base)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(base);if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('İzole yerel test veritabanı gerekir.');
const name=`sexsogate_${randomBytes(5).toString('hex')}_seo_test`,control=new pg.Client({connectionString:base});await control.connect();await control.query(`CREATE DATABASE "${name}"`);url.pathname='/'+name;
process.env.DATABASE_URL=url.toString();process.env.APP_ENV='test';
const {pool,query}=await import('../src/server/db');
const seo=await import('../src/server/seo-management');const {seoReport}=await import('../src/server/seo');
const admin={id:'seo-test-admin',role:'admin' as const,mfa:true};
let passed=0;async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
const metadata={action:'product',productId:'p1',locale:'tr',slug:'ic-giyim',title:'İç Giyim — Ölçü ve Özellikler',description:'İstanbul, İzmir, Iğdır ve Çeşme için doğal bakım bilgileri.',alt:'Bordo maskenin ön görünümü'};
try{
 await migrate(process.env.DATABASE_URL);
 await query("INSERT INTO categories(slug,name,name_en) VALUES('aksesuarlar','Aksesuarlar','Accessories')");
 await query("INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,status,fixture) VALUES('p1','first','İç Giyim','Intimate wear','Türkçe ürün açıklaması','English product description','aksesuarlar','/media/atelier-01.svg','published',true),('p2','second','Başka Ürün','Another product','İkinci açıklama','Second description','aksesuarlar','/missing.svg','draft',true)");
 await query("INSERT INTO variants(id,product_id,sku,name,price_minor) VALUES('v1','p1','LOCAL-SEO-1','Standart',12345)");
 await check('Dil bazlı metadata ve slug Türkçe metni korur; diğer dil bağımsız kalır',async()=>{
  await seo.saveProductSEO(metadata,admin);await seo.saveProductSEO({...metadata,locale:'en',slug:'intimate-wear',title:'Intimate wear and care',description:'Product care and material details for this local example.'},admin);
  assert.equal((await seo.productSEO('p1','tr'))?.slug,'ic-giyim');assert.equal((await seo.productSEO('p1','tr'))?.title,metadata.title);assert.equal((await seo.productSEO('p1','en'))?.slug,'intimate-wear');
 });
 await check('Aynı dilde çakışan slug ve yetkisiz/MFA eksik değişiklik engellenir',async()=>{
  await assert.rejects(()=>seo.saveProductSEO({...metadata,productId:'p2'},admin));
  await assert.rejects(()=>seo.saveProductSEO(metadata,{...admin,role:'warehouse'}));
  await assert.rejects(()=>seo.saveProductSEO(metadata,{...admin,mfa:false}));
  await assert.rejects(()=>query("INSERT INTO products(slug,name,name_en,category) VALUES('ic-giyim','Çakışma','Collision','aksesuarlar')"));
 });
 await check('Ürün yolu değişirken aynı ürün yönlendirmesi düzleşir; geri dönüş döngü yaratmaz',async()=>{
  assert.equal(await seo.publicRedirect('/urun/first'),'/urun/ic-giyim');
  await seo.saveProductSEO({...metadata,slug:'olcu-bakim'},admin);assert.equal(await seo.publicRedirect('/urun/first'),'/urun/olcu-bakim');assert.equal(await seo.publicRedirect('/urun/ic-giyim'),'/urun/olcu-bakim');
  await seo.saveProductSEO(metadata,admin);assert.equal(await seo.publicRedirect('/urun/ic-giyim'),null);assert.equal(await seo.publicRedirect('/urun/olcu-bakim'),'/urun/ic-giyim');
 });
 await check('Açık yönlendirme, özel sayfa, aktif ürün devralma ve yönlendirme zinciri engellenir',async()=>{
  for(const to of ['https://evil.test','//evil.test','/hesap','/en/odeme','/urun/not-found'])await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/old-page',to,reason:'Yerel güvenlik sınaması'},admin));
  await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/urun/ic-giyim',to:'/',reason:'Yayındaki ürünü devralma sınaması'},admin));
  await seo.manageRedirect({action:'redirect',from:'/eski-rehber',to:'/rehber',reason:'Aynı rehber alanının eski yolu'},admin);
  await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/daha-eski',to:'/eski-rehber',reason:'Zincir oluşmasını önleme sınaması'},admin));
  assert.equal(await seo.publicRedirect('/eski-rehber'),'/rehber');
 });
 await check('Sayfalı rapor gerçek eksikleri ve kırık görseli gösterir; örnekleri sitemap saymaz',async()=>{
  for(let i=0;i<28;i++)await query("INSERT INTO products(slug,name,name_en,category,image,fixture) VALUES($1,$2,'Duplicate title','aksesuarlar','/missing.svg',true)",[`extra-${i}`,`İzmir ${i}`]);
  const first=await seoReport(admin);assert.equal(first.rows.length,25);assert.equal(first.total,30);assert.equal(first.summary.eligible,0);assert(first.rows.some(row=>row.issues.includes('Görsel dosyası bulunamadı')));
  for(const page of [NaN,Infinity,-1,0,1.2,100001])await assert.rejects(()=>seoReport(admin,{page}));
  const second=await seoReport(admin,{page:2});assert.equal(second.rows.length,5);const searched=await seoReport(admin,{q:'izmir'});assert.equal(searched.total,28);
  assert((await query("SELECT id FROM audit_log WHERE resource='seo'")).length>=5);
 });
 await check('Sitemap dizini örnekleri dışlar ve dil bazlı canonical eşlerini gerçek değişiklik tarihiyle sunar',async()=>{
  const {sitemapIndex,sitemapPart}=await import('../src/server/sitemaps');
  assert(!(await sitemapIndex()).includes('<sitemap>'));
  await query("UPDATE products SET fixture=false WHERE id='p1'");process.env.APP_ENV='production';
  try{assert((await sitemapIndex()).includes('/sitemaps/products-0'));const xml=await sitemapPart('products-0');assert(xml?.includes('/urun/ic-giyim'));assert(xml?.includes('/en/urun/intimate-wear'));assert(xml?.includes('hreflang="x-default"'));assert(xml?.includes('<lastmod>'));assert(!xml?.includes('second'));assert.equal(await sitemapPart('products-1'),null);assert.equal(await sitemapPart('untrusted'),null);}finally{process.env.APP_ENV='test';}
 });
 await check('Son varyantı veya kategorisi kapatılmış ürün sitemap ve yönlendirme hedefi olamaz',async()=>{
  const {sitemapPart}=await import('../src/server/sitemaps');await query("UPDATE variants SET active=false WHERE id='v1'");
  await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/gecersiz-hedef',to:'/urun/ic-giyim',reason:'Kapanmış varyant doğrulaması'},admin));
  assert(!(await seoReport(admin,{q:'İç Giyim'})).rows[0].eligibleForSitemap);
  process.env.APP_ENV='production';try{assert.equal(await sitemapPart('products-0'),null);}finally{process.env.APP_ENV='test';}
  await query("UPDATE variants SET active=true WHERE id='v1'");await query("UPDATE categories SET active=false WHERE slug='aksesuarlar'");
  await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/gecersiz-kategori',to:'/urun/ic-giyim',reason:'Kapanmış kategori doğrulaması'},admin));
  assert.equal(await seo.publicRedirect('/urun/first'),null);
 });
 await check('Rehber yönlendirmesi mevcut projection yerine yürürlükteki içerik sürümünü kullanır',async()=>{
  const cms=await import('../src/server/cms');const draft=await cms.saveCMS({action:'pageDraft',slug:'scheduled-guide',locale:'tr',title:'Planlanan rehber',body:'Yayınlandığında görünecek güvenli içerik.',kind:'guide'},admin);
  await cms.saveCMS({action:'pagePublish',id:draft.id,publishAt:new Date(Date.now()+3600000).toISOString()},admin);await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/onceki-rehber',to:'/rehber/scheduled-guide',reason:'Zamanlanmış içerik uygunluk kontrolü'},admin));
  await query("UPDATE content_revisions SET publish_at=now()-interval '1 minute' WHERE id=$1",[draft.id]);await seo.manageRedirect({action:'redirect',from:'/onceki-rehber',to:'/rehber/scheduled-guide',reason:'Yürürlüğe girmiş içerik uygunluk kontrolü'},admin);assert.equal(await seo.publicRedirect('/onceki-rehber'),'/rehber/scheduled-guide');
  const [page]=await query("SELECT id FROM content_pages WHERE slug='scheduled-guide' AND locale='tr'");await cms.saveCMS({action:'pageArchive',id:page.id},admin);assert.equal(await seo.publicRedirect('/onceki-rehber'),null);
  const fixture=await cms.saveCMS({action:'pageDraft',slug:'fixture-guide',locale:'tr',title:'Yerel rehber',body:'Yalnız yerel örnek rehber.',kind:'guide',fixture:true},admin);await cms.saveCMS({action:'pagePublish',id:fixture.id},admin);process.env.APP_ENV='production';try{await assert.rejects(()=>seo.manageRedirect({action:'redirect',from:'/ornek-eski',to:'/rehber/fixture-guide',reason:'Üretimde örnek içerik sızıntısı kontrolü'},admin));}finally{process.env.APP_ENV='test';}
 });
 console.log(`SEO integration: ${passed} checks passed.`);
}finally{await pool.end();await control.query('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1',[name]);await control.query(`DROP DATABASE "${name}"`);await control.end();}
