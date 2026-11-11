/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/cms.ts
 * Açıklama   : Vitrin bölgelerini ve mevcut içerik sürümlerini yetki, yayın ve hak denetimiyle yönetir.
 */
import {z} from 'zod';
import {cache} from 'react';
import {query,transaction,type Connection} from './db';
import {assertPermission,requireCondition,DomainError} from './commerce/rules';
import {audit} from './commerce/admin';
import {getProduct} from './commerce/catalog';
import type {Principal,Locale,Currency} from '../shared/contracts';
import type {CMSPayload,CMSRevision,CMSPage,PublicCMS,PublicCollection} from '../shared/cms-types';
const plain=(max:number)=>z.string().trim().min(1).max(max).refine(value=>!/[<>\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value));
const link=z.object({label:plain(90),href:z.string().min(1).max(600)}).strict();
const image=z.string().regex(/^\/(?:brand\/[a-z0-9-]+\.svg|media\/atelier-0[1-6]\.svg|uploads\/[a-f0-9-]+\.webp)$/).max(200);
const payloadSchema=z.discriminatedUnion('kind',[
 z.object({kind:z.literal('hero'),eyebrow:plain(100),title:plain(100),italic:z.string().trim().max(100).refine(v=>!/[<>]/.test(v)),description:plain(600),cta:link,image:image.optional()}).strict(),
 z.object({kind:z.literal('navigation'),links:z.array(link).min(1).max(6),categoryLinks:z.array(link).max(8)}).strict(),
 z.object({kind:z.literal('footer'),description:plain(400),columns:z.array(z.object({title:plain(70),links:z.array(link).min(1).max(8)}).strict()).min(1).max(2)}).strict(),
 z.object({kind:z.literal('collection'),title:plain(120),description:plain(600),image,productIds:z.array(z.string().min(1).max(100)).min(1).max(100).refine(ids=>new Set(ids).size===ids.length),featured:z.boolean()}).strict()
]);
function parse<T>(schema:z.ZodType<T>,input:unknown):T{const value=schema.safeParse(input);requireCondition(value.success,'INVALID_CMS','İçerik alanlarını ve biçimlerini kontrol edin.');return value.data;}
export function parseCMSPayload(input:unknown):CMSPayload{return parse(payloadSchema,input);}
export function publicContentHref(input:string,origin=process.env.APP_URL??'http://127.0.0.1:3000'){
 requireCondition(!/[\\\u0000-\u0020]/.test(input)&&!input.startsWith('//')&&!/%(?:2f|5c|2e)/i.test(input),'INVALID_CMS_LINK','Yalnız mağazanın genel sayfalarına bağlantı verilebilir.');
 let url:URL;try{url=new URL(input,origin);}catch{throw new DomainError('INVALID_CMS_LINK','Geçerli bir mağaza bağlantısı girin.');}
 requireCondition(url.origin===new URL(origin).origin&&!url.username&&!url.password,'INVALID_CMS_LINK','Bağlantı mağazayla aynı adreste olmalıdır.');
 const path=url.pathname.replace(/^\/en(?=\/|$)/,'')||'/';
 requireCondition(/^\/$|^\/(?:urunler|koleksiyonlar|rehber|sss|iletisim)\/?$|^\/(?:urun|rehber|yasal)\/[a-z0-9]+(?:-[a-z0-9]+)*\/?$/.test(path),'INVALID_CMS_LINK','Bu sayfaya içerik bağlantısı verilemez.');
 const allowed=new Set(path==='/urunler'?['q','category','min','max','material','available','sort','page']:path==='/koleksiyonlar'?['collection']:[]);
 requireCondition([...url.searchParams.keys()].every(key=>allowed.has(key)),'INVALID_CMS_LINK','Bağlantı sorgusu desteklenmiyor.');
 return path+url.search+url.hash;
}
const local=()=>['development','test'].includes(process.env.APP_ENV??'');
const localeSchema=z.enum(['tr','en']);const keySchema=z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(100);
const iso=z.string().datetime({offset:true});
type RevisionRow={id:string;region_id:string;key:string;locale:Locale;kind:CMSPayload['kind'];version:number;status:CMSRevision['status'];publish_at:Date|null;created_at:Date;fixture:boolean;active:boolean;payload:CMSPayload};
const regionColumns='r.id region_id,r.key,r.locale,r.kind,r.fixture,r.active,v.id,v.version,v.status,v.publish_at,v.created_at,v.payload';
function revision(row:RevisionRow):CMSRevision{return {id:row.id,regionId:row.region_id,key:row.key,locale:row.locale,kind:row.kind,version:row.version,status:row.status,publishAt:row.publish_at?.toISOString()??null,createdAt:row.created_at.toISOString(),fixture:row.fixture,active:row.active,payload:row.payload};}
async function verifyImage(value:string|undefined,fixture:boolean,connection:Connection){
 if(!value)return;
 if(['/brand/hero-silk.svg','/brand/symbol.svg'].includes(value))return;
 if(/^\/media\/atelier-0[1-6]\.svg$/.test(value)){requireCondition(fixture&&local(),'CMS_MEDIA_RIGHTS','Yerel örnek görseller gerçek içerik olarak yayımlanamaz.',409);return;}
 const rows=await query("SELECT id FROM media_assets WHERE split_part(object_key,'/',2)=$1 AND length(trim(coalesce(rights_reference,'')))>=5",[value.replace('/uploads/','')],connection);
 requireCondition(rows.length===1,'CMS_MEDIA_RIGHTS','Kullanım hakkı doğrulanmış medya kaydı seçin.',409);
}
async function verifyPayload(payload:CMSPayload,locale:Locale,fixture:boolean,connection:Connection,publish=false){
 const links=payload.kind==='hero'?[payload.cta]:payload.kind==='navigation'?[...payload.links,...payload.categoryLinks]:payload.kind==='footer'?payload.columns.flatMap(column=>column.links):[];
 for(const item of links){item.href=publicContentHref(item.href);if(publish&&item.href.startsWith('/urun/'))requireCondition(await getProduct(item.href.split('?')[0].split('#')[0].slice(6),locale),'CMS_PRODUCT_UNAVAILABLE','Bağlantıdaki ürün bu dilde yayında değil.',409);}
 if('image'in payload&&publish)await verifyImage(payload.image,fixture,connection);
 if(payload.kind==='collection'&&publish){const rows=await query("SELECT p.id FROM products p WHERE p.id=ANY($1::text[]) AND p.status='published' AND EXISTS(SELECT 1 FROM variants v WHERE v.product_id=p.id AND v.active=true) AND EXISTS(SELECT 1 FROM categories c WHERE c.slug=p.category AND c.active=true) AND ($2 OR p.fixture=false) AND($3='tr' OR(length(trim(p.name_en))>0 AND length(trim(p.description_en))>0))",[payload.productIds,local(),locale],connection);requireCondition(rows.length===payload.productIds.length,'CMS_PRODUCT_UNAVAILABLE','Koleksiyondaki tüm ürünler bu dilde yayıma uygun olmalıdır.',409);}
 return payload;
}
export async function cmsAdmin(principal:Principal,filter:{locale?:string;page?:number;q?:string}={}){
 assertPermission(principal,'content','write');const locale=parse(localeSchema,filter.locale??'tr'),page=filter.page??1;requireCondition(Number.isInteger(page)&&page>0&&page<=100000,'INVALID_PAGE','Sayfa numarası geçersiz.');
 const search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const rows=await query<RevisionRow>(`SELECT ${regionColumns} FROM cms_regions r JOIN LATERAL(SELECT * FROM cms_region_revisions WHERE region_id=r.id ORDER BY version DESC LIMIT 1)v ON true WHERE r.locale=$1 AND sg_search_normalize(r.key) LIKE sg_search_normalize($2) ORDER BY r.kind,r.key LIMIT 25 OFFSET $3`,[locale,search,(page-1)*25]);
 const pages=await query("SELECT p.id,p.slug,p.locale,p.fixture,v.kind,v.version,v.status,v.title,v.body,v.publish_at FROM content_pages p JOIN LATERAL(SELECT * FROM content_revisions WHERE page_id=p.id ORDER BY version DESC LIMIT 1)v ON true WHERE p.locale=$1 AND(sg_search_normalize(v.title) LIKE sg_search_normalize($2) OR sg_search_normalize(p.slug) LIKE sg_search_normalize($2)) ORDER BY p.updated_at DESC LIMIT 25 OFFSET $3",[locale,search,(page-1)*25]);
 return {rows:rows.map(revision),pages:pages.map(row=>({id:row.id,slug:row.slug,locale:row.locale,fixture:row.fixture,kind:row.kind,version:row.version,status:row.status,title:row.title,body:row.body,publishAt:row.publish_at?.toISOString()??null})),total:Number((await query('SELECT count(*) n FROM cms_regions WHERE locale=$1',[locale]))[0].n),page};
}
export async function cmsHistory(principal:Principal,id:string,page=false){
 assertPermission(principal,'content','write');if(page)return {rows:await query('SELECT id,page_id,version,title,body,kind,status,publish_at,created_at FROM content_revisions WHERE page_id=$1 ORDER BY version DESC LIMIT 100',[id])};
 return {rows:(await query<RevisionRow>(`SELECT ${regionColumns} FROM cms_regions r JOIN cms_region_revisions v ON v.region_id=r.id WHERE r.id=$1 ORDER BY v.version DESC LIMIT 100`,[id])).map(revision)};
}
export async function cmsPreview(principal:Principal,id:string,page=false){
 assertPermission(principal,'content','write');if(page){const rows=await query('SELECT p.slug,p.locale,p.fixture,r.* FROM content_pages p JOIN content_revisions r ON r.page_id=p.id WHERE r.id=$1',[id]);requireCondition(rows[0],'NOT_FOUND','Sürüm bulunamadı.',404);return {page:rows[0]};}
 const rows=await query<RevisionRow>(`SELECT ${regionColumns} FROM cms_regions r JOIN cms_region_revisions v ON v.region_id=r.id WHERE v.id=$1`,[id]);requireCondition(rows[0],'NOT_FOUND','Sürüm bulunamadı.',404);return {revision:revision(rows[0])};
}
export async function saveCMS(input:unknown,principal:Principal):Promise<{id:string;version?:number;publishAt?:string}>{
 assertPermission(principal,'content','write');const base=parse(z.object({action:z.enum(['draft','publish','archive','pageDraft','pagePublish','pageArchive'])}).passthrough(),input);
 if(base.action==='draft'){
  const data=parse(z.object({action:z.literal('draft'),key:keySchema,locale:localeSchema,payload:payloadSchema,fixture:z.boolean().default(false)}).strict(),input);
  requireCondition(data.payload.kind==='collection'||data.key===data.payload.kind,'INVALID_CMS_KEY','Bölge anahtarı türüyle aynı olmalıdır.');requireCondition(!data.fixture||local(),'FIXTURE_DISABLED','Örnek içerik bu ortamda kullanılamaz.',409);
  return transaction(async client=>{await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',[`cms:${data.locale}:${data.key}`]);let [region]=await query('SELECT * FROM cms_regions WHERE key=$1 AND locale=$2 FOR UPDATE',[data.key,data.locale],client);if(!region)[region]=await query('INSERT INTO cms_regions(key,locale,kind,fixture) VALUES($1,$2,$3,$4) RETURNING *',[data.key,data.locale,data.payload.kind,data.fixture],client);requireCondition(region.kind===data.payload.kind&&region.fixture===data.fixture,'CMS_KIND_LOCKED','İçerik türü ve örnek veri işareti sonradan değiştirilemez.');const payload=await verifyPayload(data.payload,data.locale,data.fixture,client);const [row]=await query("INSERT INTO cms_region_revisions(region_id,version,payload,actor_id) SELECT $1,coalesce(max(version),0)+1,$2,$3 FROM cms_region_revisions WHERE region_id=$1 RETURNING id,version",[region.id,JSON.stringify(payload),principal.id],client);await audit(principal,'draft','cms',region.id,{version:row.version},client);return {id:String(row.id),version:Number(row.version)};});
 }
 if(base.action==='pageDraft'){
  const data=parse(z.object({action:z.literal('pageDraft'),slug:keySchema,locale:localeSchema,title:plain(200),body:plain(50000),kind:z.enum(['guide','faq','campaign','page']),fixture:z.boolean().default(false)}).strict(),input);requireCondition(!data.fixture||local(),'FIXTURE_DISABLED','Örnek içerik bu ortamda kullanılamaz.',409);
  return transaction(async client=>{await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',[`page:${data.locale}:${data.slug}`]);let [page]=await query('SELECT * FROM content_pages WHERE slug=$1 AND locale=$2 FOR UPDATE',[data.slug,data.locale],client);if(!page)[page]=await query("INSERT INTO content_pages(slug,locale,title,body,status,kind,fixture,version) VALUES($1,$2,$3,$4,'draft',$5,$6,0) RETURNING *",[data.slug,data.locale,data.title,data.body,data.kind,data.fixture],client);requireCondition(page.fixture===data.fixture,'CMS_KIND_LOCKED','Örnek veri işareti sonradan değiştirilemez.');const [row]=await query("INSERT INTO content_revisions(page_id,version,title,body,actor_id,kind,status) SELECT $1,greatest($2,coalesce(max(version),0))+1,$3,$4,$5,$6,'draft' FROM content_revisions WHERE page_id=$1 RETURNING id,version",[page.id,page.version,data.title,data.body,principal.id,data.kind],client);await query('UPDATE content_pages SET version=$2,updated_at=now() WHERE id=$1',[page.id,row.version],client);await audit(principal,'draft','content',page.id,{version:row.version},client);return {id:String(row.id),version:Number(row.version)};});
 }
 if(base.action==='publish'||base.action==='pagePublish'){
  const data=parse(z.object({action:z.enum(['publish','pagePublish']),id:z.string().min(1).max(100),publishAt:iso.optional()}).strict(),input),page=data.action==='pagePublish';
  return transaction(async client=>{const rows=await query(page?'SELECT r.*,p.fixture,p.locale,p.id parent_id FROM content_revisions r JOIN content_pages p ON p.id=r.page_id WHERE r.id=$1 FOR UPDATE OF p,r':'SELECT v.*,r.fixture,r.locale,r.id parent_id FROM cms_region_revisions v JOIN cms_regions r ON r.id=v.region_id WHERE v.id=$1 FOR UPDATE OF r,v',[data.id],client);const row=rows[0];requireCondition(row,'NOT_FOUND','Sürüm bulunamadı.',404);requireCondition(!row.fixture||local(),'FIXTURE_DISABLED','Örnek içerik bu ortamda yayımlanamaz.',409);requireCondition(row.status==='draft','CMS_NOT_DRAFT','Yalnız taslak sürüm yayımlanabilir.',409);const at=data.publishAt?new Date(data.publishAt):new Date();requireCondition(at.getTime()<=Date.now()+366*86400000,'CMS_SCHEDULE','Yayın zamanı en fazla bir yıl ileriye ayarlanabilir.');
   if(page){parse(plain(200),row.title);parse(plain(50000),row.body);await query("UPDATE content_revisions SET status='published',publish_at=$2,published_by=$3 WHERE id=$1",[row.id,at,principal.id],client);if(at.getTime()<=Date.now())await query("UPDATE content_pages SET title=$2,body=$3,kind=$4,status='published',publish_at=$5,updated_at=now() WHERE id=$1",[row.parent_id,row.title,row.body,row.kind,at],client);}
   else{await verifyPayload(parseCMSPayload(row.payload),row.locale,row.fixture,client,true);await query("UPDATE cms_region_revisions SET status='published',publish_at=$2,published_by=$3 WHERE id=$1",[row.id,at,principal.id],client);await query('UPDATE cms_regions SET active=true WHERE id=$1',[row.parent_id],client);}
   await audit(principal,'publish',page?'content':'cms',row.parent_id,{version:row.version,publishAt:at.toISOString()},client);return {id:row.id,version:row.version,publishAt:at.toISOString()};});
 }
 const data=parse(z.object({action:z.enum(['archive','pageArchive']),id:z.string().min(1).max(100)}).strict(),input);
 return transaction(async client=>{let found;if(data.action==='pageArchive'){await query("UPDATE content_revisions SET status='archived' WHERE page_id=$1 AND status='published'",[data.id],client);found=await query("UPDATE content_pages SET status='draft',updated_at=now() WHERE id=$1 RETURNING id",[data.id],client);}else found=await query('UPDATE cms_regions SET active=false WHERE id=$1 RETURNING id',[data.id],client);requireCondition(found.length===1,'NOT_FOUND','İçerik bulunamadı.',404);await audit(principal,'archive',data.action==='pageArchive'?'content':'cms',data.id,{},client);return {id:data.id};});
}
const effectiveContentJoin="JOIN LATERAL(SELECT * FROM content_revisions WHERE page_id=p.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)r ON true";
const guideKinds=new Set(['guide','page']);
const reservedPageSlugs=new Set(['sss','iletisim','home-campaign','gizlilik','mesafeli-satis','cerezler','iade']);
export async function publicContentPages(slug:string|null,locale:Locale,connection?:Connection):Promise<CMSPage[]>{
 const rows=await query(`SELECT p.id,p.slug,p.locale,p.fixture,r.id revision_id,r.title,r.body,r.kind,r.version,r.status,r.publish_at FROM content_pages p ${effectiveContentJoin} WHERE p.locale=$1 AND($2::text IS NULL OR p.slug=$2) AND($3 OR p.fixture=false) ORDER BY r.created_at DESC LIMIT 30`,[locale,slug,local()],connection);
 return rows.map(row=>({id:row.id,slug:row.slug,locale:row.locale,title:row.title,body:row.body,kind:row.kind,version:row.version,status:row.status,publishAt:row.publish_at?.toISOString()??null,fixture:row.fixture,revisionId:row.revision_id}));
}
export async function publicGuidePage(slug:string,locale:Locale,connection?:Connection):Promise<CMSPage|null>{
 if(reservedPageSlugs.has(slug))return null;const [page]=await publicContentPages(slug,locale,connection);return page&&guideKinds.has(page.kind)?page:null;
}
export const publicGuideForRender=cache((slug:string,locale:Locale)=>publicGuidePage(slug,locale));
export async function publicContentIndex():Promise<{slug:string;locale:Locale;updatedAt:Date}[]>{
 const rows=await query(`SELECT p.slug,p.locale,greatest(r.created_at,coalesce(r.publish_at,r.created_at)) updated_at FROM content_pages p ${effectiveContentJoin} WHERE p.fixture=false AND p.locale IN('tr','en') AND r.kind IN('guide','page') AND NOT(p.slug=ANY($1::text[])) ORDER BY p.locale,p.slug`,[[...reservedPageSlugs]]);
 return rows.map(row=>({slug:row.slug,locale:row.locale,updatedAt:row.updated_at}));
}
export async function publicCMS(locale:Locale='tr',currency:Currency='TRY',collectionKey?:string,page=1):Promise<PublicCMS>{
 requireCondition(Number.isSafeInteger(page)&&page>=1&&page<=100000,'INVALID_PAGE','Sayfa numarası geçersiz.');
 const rows=await query<RevisionRow>(`SELECT ${regionColumns} FROM cms_regions r JOIN LATERAL(SELECT * FROM cms_region_revisions WHERE region_id=r.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)v ON true WHERE r.active=true AND r.locale=$1 AND($2 OR r.fixture=false) ORDER BY r.key LIMIT 100`,[locale,local()]);
 const result:PublicCMS={regions:{},collections:[]};
 for(const row of rows){const parsed=payloadSchema.safeParse(row.payload);if(!parsed.success)continue;const payload=parsed.data;if(payload.kind==='collection'){const available=await query("SELECT p.id FROM products p WHERE p.id=ANY($1::text[]) AND p.status='published' AND EXISTS(SELECT 1 FROM categories c WHERE c.slug=p.category AND c.active=true) AND EXISTS(SELECT 1 FROM variants v WHERE v.product_id=p.id AND v.active=true) AND($2 OR p.fixture=false) AND($3='tr' OR(length(trim(p.name_en))>0 AND length(trim(p.description_en))>0))",[payload.productIds,local(),locale]);const ids=new Set(available.map(p=>p.id));const item:PublicCollection={...payload,key:row.key,productIds:payload.productIds.filter(id=>ids.has(id))};if(item.productIds.length)result.collections.push(item);}else if(payload.kind==='hero')result.regions.hero=payload;else if(payload.kind==='navigation')result.regions.navigation=payload;else result.regions.footer=payload;}
 if(collectionKey){result.collection=result.collections.find(item=>item.key===collectionKey)??null;result.products=[];result.page=page;result.total=result.collection?.productIds.length??0;if(result.collection){const ids=result.collection.productIds.slice((page-1)*24,page*24),slugs=await query('SELECT id,slug FROM products WHERE id=ANY($1::text[])',[ids]),byId=new Map(slugs.map(row=>[row.id,row.slug]));for(const id of ids){const product=await getProduct(byId.get(id),locale,currency);if(product)result.products.push(product);}}}
 return result;
}
export async function publicCMSAsset(filename:string):Promise<boolean>{
 if(!/^[a-f0-9-]+\.webp$/.test(filename))return false;
 const rows=await query("SELECT r.id FROM cms_regions r JOIN LATERAL(SELECT payload FROM cms_region_revisions WHERE region_id=r.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)v ON true WHERE r.active=true AND($2 OR r.fixture=false) AND v.payload->>'image'=$1 LIMIT 1",[`/uploads/${filename}`,local()]);
 return rows.length>0;
}
// Aynı HTML yanıtındaki layout ve ana sayfa tek yayın snapshot'ını paylaşır; istekler arası önbellek yoktur.
export const publicCMSForRender=cache((locale:Locale,currency:Currency)=>publicCMS(locale,currency));
