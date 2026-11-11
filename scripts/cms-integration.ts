/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/cms-integration.ts
 * Açıklama   : CMS sürüm, yayın, zamanlama, hak ve yetki sınırlarını izole veritabanında doğrular.
 */
import assert from 'node:assert/strict';
import pg from 'pg';
import {randomBytes} from 'node:crypto';
import {migrate} from './migrate';
const base=process.env.TEST_DATABASE_URL;if(!base)throw new Error('TEST_DATABASE_URL gerekir.');
const url=new URL(base);if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('İzole yerel test veritabanı gerekir.');
const name=`sexsogate_${randomBytes(5).toString('hex')}_cms_test`,control=new pg.Client({connectionString:base});await control.connect();await control.query(`CREATE DATABASE "${name}"`);url.pathname='/'+name;process.env.DATABASE_URL=url.toString();process.env.APP_ENV='test';
const {pool,query}=await import('../src/server/db');const cms=await import('../src/server/cms');
const admin={id:'cms-local-admin',role:'admin' as const,mfa:true},marketing={id:'cms-local-marketing',role:'marketing' as const,mfa:true};
const hero={kind:'hero' as const,eyebrow:'Yeni koleksiyon',title:'Tutkunu Keşfet.',italic:'Kendi ritminde',description:'Size ait bir keşif.',cta:{label:'Koleksiyonu keşfet',href:'/urunler'}};
let passed=0;async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 await migrate(process.env.DATABASE_URL);
 await check('Boş DB içerik yüklemesi başlangıç sürümü ve örnek işareti oluşturur; tekrar yükleme düzenlemeyi ezmez',async()=>{
  const {seedContent}=await import('./seed');await seedContent(pool);const guides=await cms.publicContentPages('rehber','tr');assert.equal(guides.length,1);assert.equal(guides[0].fixture,true);assert.equal((await cms.publicContentPages('sss','en'))[0]?.kind,'faq');
  const before=Number((await query('SELECT count(*) n FROM content_revisions'))[0].n);await query("UPDATE content_pages SET title='Elle düzenlenen başlık' WHERE slug='rehber' AND locale='tr'");await seedContent(pool);assert.equal(Number((await query('SELECT count(*) n FROM content_revisions'))[0].n),before);assert.equal((await query("SELECT title FROM content_pages WHERE slug='rehber' AND locale='tr'"))[0].title,'Elle düzenlenen başlık');
 });
 await query("INSERT INTO categories(slug,name,name_en) VALUES('aksesuarlar','Aksesuarlar','Accessories')");
 await query("INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,status,fixture) VALUES('cms-p1','cms-maske','Maske','Mask','Ürün açıklaması','Product description','aksesuarlar','/media/atelier-01.svg','published',true),('cms-p2','cms-taslak','Taslak','Draft','Açıklama','Description','aksesuarlar','/media/atelier-01.svg','draft',true)");
 await query("INSERT INTO variants(id,product_id,sku,name,name_en,price_minor) VALUES('cms-v1','cms-p1','CMS-MASK','Standart','Standard',10000),('cms-v2','cms-p2','CMS-DRAFT','Standart','Standard',10000)");
 let first='',second='',pageDraft='';
 await check('Yetkisiz ve MFA eksik roller taslak, liste ve önizleme göremez',async()=>{
  for(const principal of [{...admin,mfa:false},{...admin,role:'warehouse' as const},{...admin,role:'customer' as const},{...admin,role:'catalog' as const}]){await assert.rejects(()=>cms.saveCMS({action:'draft',key:'hero',locale:'tr',payload:hero},principal));await assert.rejects(()=>cms.cmsAdmin(principal));await assert.rejects(()=>cms.cmsPreview(principal,'missing'));}
 });
 await check('Taslak anonim yanıtta yok; yetkili önizlemede tam sürüm görülebilir',async()=>{
  const result=await cms.saveCMS({action:'draft',key:'hero',locale:'tr',payload:hero},marketing);first=result.id;assert.equal((await cms.publicCMS()).regions.hero,undefined);assert.equal((await cms.cmsPreview(admin,first)).revision?.payload.kind,'hero');
 });
 await check('Yayın dili bağımsızdır; sonraki taslak mevcut yayını değiştirmez',async()=>{
  await cms.saveCMS({action:'publish',id:first},admin);assert.equal((await cms.publicCMS()).regions.hero?.title,hero.title);assert.equal((await cms.publicCMS('en')).regions.hero,undefined);
  const result=await cms.saveCMS({action:'draft',key:'hero',locale:'tr',payload:{...hero,title:'Gelecek kampanya'}},admin);second=result.id;assert.equal((await cms.publicCMS()).regions.hero?.title,hero.title);
 });
 await check('Gelecekteki yayın erken açılmaz; süresi gelince yeni sürüm çözülür',async()=>{
  await cms.saveCMS({action:'publish',id:second,publishAt:new Date(Date.now()+3600000).toISOString()},admin);assert.equal((await cms.publicCMS()).regions.hero?.title,hero.title);
  await query("UPDATE cms_region_revisions SET publish_at=now()-interval '1 minute' WHERE id=$1",[second]);assert.equal((await cms.publicCMS()).regions.hero?.title,'Gelecek kampanya');
 });
 await check('Yayındaki sürüm yeniden yazılamaz; eşzamanlı taslak sürümleri tekildir',async()=>{
  await assert.rejects(()=>cms.saveCMS({action:'publish',id:first},admin));const values=await Promise.all([1,2].map(n=>cms.saveCMS({action:'draft',key:'hero',locale:'tr',payload:{...hero,title:`Sürüm ${n}`}},admin)));assert.equal(new Set(values.map(row=>row.version)).size,2);assert(values.every(row=>Number(row.version)>2));
 });
 await check('Koleksiyon gerçek yayınlanabilir ürün ister; hak kaydı olmayan görsel reddedilir',async()=>{
  const payload={kind:'collection',title:'Maske seçimi',description:'Seçili aksesuarlar',image:'/media/atelier-01.svg',productIds:['cms-p2'],featured:true};const row=await cms.saveCMS({action:'draft',key:'masks',locale:'tr',fixture:true,payload},admin);await assert.rejects(()=>cms.saveCMS({action:'publish',id:row.id},admin));
  const bad=await cms.saveCMS({action:'draft',key:'unlicensed',locale:'tr',payload:{...payload,productIds:['cms-p1'],image:'/uploads/00000000-0000-0000-0000-000000000000.webp'}},admin);await assert.rejects(()=>cms.saveCMS({action:'publish',id:bad.id},admin));
 });
 await check('Yayımlanan koleksiyon gerçek fiyatlı ürün projectionı verir; kapanan ürün düşer',async()=>{
  const row=await cms.saveCMS({action:'draft',key:'selected-masks',locale:'tr',fixture:true,payload:{kind:'collection',title:'Seçili maskeler',description:'Aksesuar koleksiyonu',image:'/media/atelier-01.svg',productIds:['cms-p1'],featured:true}},admin);await cms.saveCMS({action:'publish',id:row.id},admin);const result=await cms.publicCMS('tr','TRY','selected-masks');assert.equal(result.collection?.productIds[0],'cms-p1');assert.equal(result.products?.[0]?.id,'cms-p1');await query("UPDATE products SET status='closed' WHERE id='cms-p1'");assert.equal((await cms.publicCMS()).collections.length,0);await query("UPDATE products SET status='published' WHERE id='cms-p1'");
 });
 await check('Mevcut sayfa kaynağı draft ve zamanlı sürümle geçmiş yayını korur',async()=>{
  const row=await cms.saveCMS({action:'pageDraft',slug:'cms-bakim',locale:'tr',title:'Ürün bakımı',body:'Üretici talimatlarını izleyin.',kind:'guide'},admin);pageDraft=row.id;assert.equal((await cms.publicContentPages('cms-bakim','tr')).length,0);await cms.saveCMS({action:'pagePublish',id:pageDraft},admin);assert.equal((await cms.publicContentPages('cms-bakim','tr'))[0].title,'Ürün bakımı');
  const next=await cms.saveCMS({action:'pageDraft',slug:'cms-bakim',locale:'tr',title:'Yeni bakım rehberi',body:'Yeni sürüm içeriği.',kind:'guide'},marketing);assert.equal((await cms.publicContentPages('cms-bakim','tr'))[0].title,'Ürün bakımı');await cms.saveCMS({action:'pagePublish',id:next.id,publishAt:new Date(Date.now()+3600000).toISOString()},admin);assert.equal((await cms.publicContentPages('cms-bakim','tr'))[0].title,'Ürün bakımı');await query("UPDATE content_revisions SET publish_at=now()-interval '1 minute' WHERE id=$1",[next.id]);assert.equal((await cms.publicContentPages('cms-bakim','tr'))[0].title,'Yeni bakım rehberi');
 });
 await check('Eski content yazıcısı aynı revision kaynağında görünür; HTML metni reddedilir',async()=>{
  const {adminAction}=await import('../src/server/commerce/admin');await adminAction('content',{slug:'legacy-guide',locale:'en',title:'Care guide',body:'Follow manufacturer instructions.',status:'published'},admin);assert.equal((await cms.publicContentPages('legacy-guide','en'))[0]?.title,'Care guide');await assert.rejects(()=>cms.saveCMS({action:'pageDraft',slug:'unsafe',locale:'tr',title:'Başlık',body:'<script>alert(1)</script>',kind:'guide'},admin));
 });
 await check('Production örnek bölge ve ürünleri dışlar; örnek yayınını engeller',async()=>{
  process.env.APP_ENV='production';try{assert.equal((await cms.publicCMS()).collections.length,0);const row=await cms.saveCMS({action:'draft',key:'real-collection',locale:'tr',payload:{kind:'collection',title:'Gerçek koleksiyon',description:'Gerçek katalog üyeliği.',image:'/brand/symbol.svg',productIds:['cms-p1'],featured:true}},admin);await assert.rejects(()=>cms.saveCMS({action:'publish',id:row.id},admin));await assert.rejects(()=>cms.saveCMS({action:'draft',key:'fixture-new',locale:'tr',fixture:true,payload:{kind:'collection',title:'Örnek',description:'Örnek koleksiyon',image:'/media/atelier-01.svg',productIds:['cms-p1'],featured:false}},admin));}finally{process.env.APP_ENV='test';}
 });
 await check('Yapısal menü ve footer yayını yalnız güvenli bağlantılar ve gerçek metin sunar',async()=>{
  const menu=await cms.saveCMS({action:'draft',key:'navigation',locale:'tr',payload:{kind:'navigation',links:[{label:'Koleksiyonlar',href:'/koleksiyonlar'}],categoryLinks:[]}},admin);await cms.saveCMS({action:'publish',id:menu.id},admin);
  const footer=await cms.saveCMS({action:'draft',key:'footer',locale:'tr',payload:{kind:'footer',description:'Özenli seçimler için bir alan.',columns:[{title:'Bilgi',links:[{label:'Rehber',href:'/rehber'}]}]}},admin);await cms.saveCMS({action:'publish',id:footer.id},admin);const result=await cms.publicCMS();assert.equal(result.regions.navigation?.links[0].href,'/koleksiyonlar');assert.equal(result.regions.footer?.description,'Özenli seçimler için bir alan.');
 });
 await check('Medya erişimi yalnız en son yürürlükteki açık CMS sürümünden doğar',async()=>{
  const filename='11111111-1111-1111-1111-111111111111.webp';await query("INSERT INTO media_assets(object_key,mime_type,size_bytes,sha256,rights_reference,actor_id) VALUES($1,'image/webp',100,$2,'Yerel hak kaynağı doğrulaması',$3)",[`products/${filename}`,'0'.repeat(64),admin.id]);
  const row=await cms.saveCMS({action:'draft',key:'hero',locale:'tr',payload:{...hero,image:`/uploads/${filename}`}},admin);assert.equal(await cms.publicCMSAsset(filename),false);await cms.saveCMS({action:'publish',id:row.id,publishAt:new Date(Date.now()+3600000).toISOString()},admin);assert.equal(await cms.publicCMSAsset(filename),false);await query("UPDATE cms_region_revisions SET publish_at=now()-interval '1 minute' WHERE id=$1",[row.id]);assert.equal(await cms.publicCMSAsset(filename),true);
 });
 await check('Arşiv geçmişi silmez ve eski yayın kendiliğinden geri gelmez',async()=>{
  const state=await cms.cmsAdmin(admin);const region=state.rows.find(row=>row.key==='hero');assert(region);await cms.saveCMS({action:'archive',id:region.regionId},admin);assert.equal((await cms.publicCMS()).regions.hero,undefined);assert((await cms.cmsHistory(admin,region.regionId)).rows.length>=4);const [page]=await cms.publicContentPages('cms-bakim','tr');await cms.saveCMS({action:'pageArchive',id:page.id},admin);assert.equal((await cms.publicContentPages('cms-bakim','tr')).length,0);assert((await query("SELECT id FROM audit_log WHERE resource IN ('cms','content')")).length>=15);
 });
 await check('Bulunmayan içerik arşivlenmiş gibi başarı yanıtı üretmez',async()=>{
  for(const action of ['archive','pageArchive'])await assert.rejects(()=>cms.saveCMS({action,id:'nonexistent-cms-record'},admin),(error:unknown)=>typeof error==='object'&&error!==null&&'status'in error&&error.status===404);
 });
 await check('İçerik SEO indeksi 30 kayıtta kesilmez; örnek, gelecek ve yayımsız sürümler sızmaz',async()=>{
  await query("INSERT INTO content_pages(id,slug,locale,title,body,status,kind,fixture) SELECT 'cms-index-'||n,'cms-index-'||n,'tr','İndeks rehberi '||n,'Güvenli rehber içeriği','published','guide',false FROM generate_series(0,1001)n");
  await query("INSERT INTO content_revisions(page_id,version,title,body,status,kind,actor_id) SELECT id,version,title,body,status,kind,$1 FROM content_pages WHERE id LIKE 'cms-index-%'",[admin.id]);
  assert.equal((await cms.publicContentIndex()).filter(row=>row.slug.startsWith('cms-index-')).length,1002);
  await query("UPDATE content_revisions SET publish_at=now()+interval '1 hour' WHERE page_id='cms-index-0'");assert(!(await cms.publicContentIndex()).some(row=>row.slug==='cms-index-0'));assert(!(await cms.publicContentIndex()).some(row=>row.slug==='rehber'));
  const {sitemapIndex,sitemapPart}=await import('../src/server/sitemaps');process.env.APP_ENV='production';try{assert((await sitemapIndex()).includes('/sitemaps/content-1'));const parts=(await sitemapPart('content'))!+(await sitemapPart('content-1'))!;assert(parts.includes('/rehber/cms-index-1001'));assert(!parts.includes('/rehber/cms-index-0<'));assert(!parts.includes('/rehber/rehber<'));assert.equal(await sitemapPart('content-2'),null);}finally{process.env.APP_ENV='test';}
  await query("UPDATE content_revisions SET publish_at=now()-interval '1 minute' WHERE page_id='cms-index-0'");assert((await cms.publicContentIndex()).some(row=>row.slug==='cms-index-0'));
 });
 console.log(`CMS integration: ${passed} checks passed.`);
}finally{await pool.end();await control.query('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1',[name]);await control.query(`DROP DATABASE "${name}"`);await control.end();}
