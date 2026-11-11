/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/social-assets.ts
 * Açıklama   : Gerçek katalog ve içerikten hak kaydı doğrulanmış, düzenlenebilir sosyal SVG üretir.
 */
import {z} from 'zod';
import {createHash} from 'node:crypto';
import path from 'node:path';
import PDFDocument from 'pdfkit';
import {query} from './db';
import {HttpError,validateRaster} from './security';
import {storage,readConfinedFile} from './providers/storage';
import {publicGuidePage,parseCMSPayload} from './cms';
import {formatMinorAmount} from '../shared/money';
import type {Currency,Locale,Principal} from '../shared/contracts';

export const socialSizes={post:{width:1080,height:1350},story:{width:1080,height:1920},profile:{width:1080,height:1080},cover:{width:1640,height:624},product:{width:1080,height:1350},collection:{width:1080,height:1350},information:{width:1080,height:1350}} as const;
export type SocialTemplate=keyof typeof socialSizes;
export type SocialTheme='light'|'dark';
const common={theme:z.enum(['light','dark']),locale:z.enum(['tr','en'])};
const product={...common,productId:z.string().min(1).max(100),variantId:z.string().min(1).max(100),currency:z.enum(['TRY','EUR','USD','GBP'])};
const schema=z.discriminatedUnion('template',[
 z.object({...product,template:z.literal('post')}).strict(),z.object({...product,template:z.literal('story')}).strict(),z.object({...product,template:z.literal('product')}).strict(),
 z.object({...common,template:z.literal('collection'),collectionKey:z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(100)}).strict(),
 z.object({...common,template:z.literal('information'),articleSlug:z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(100)}).strict(),
 z.object({...common,template:z.literal('profile')}).strict(),z.object({...common,template:z.literal('cover')}).strict()
]);
export type SocialInput=z.infer<typeof schema>;
type ImageSnapshot={dataUri:string;sha256:string;rightsReference:string;source:string;raster:boolean};
export interface SocialSnapshot {template:SocialTemplate;theme:SocialTheme;locale:Locale;title:string;subtitle:string;generatedAt:string;fixture:boolean;source:{kind:'product'|'collection'|'information'|'brand';id:string;variantId?:string;version?:number};sku?:string;variantName?:string;priceMinor?:number;currency?:Currency;image?:ImageSnapshot;}
const local=()=>['development','test'].includes(process.env.APP_ENV??'');
const digest=(value:Buffer|string)=>createHash('sha256').update(value).digest('hex');
function requireValue(condition:unknown,message:string,status=409):asserts condition{if(!condition)throw new HttpError(status,message,'SOCIAL_ASSET_REJECTED');}
function authorize(principal:Principal){requireValue(principal.id&&principal.mfa&&['admin','catalog','marketing'].includes(principal.role),'Sosyal tasarım için yetkili ve iki adımlı doğrulanmış oturum gerekir.',403);}
export function parseSocialInput(input:unknown):SocialInput{const result=schema.safeParse(input);requireValue(result.success,'Şablon alanlarını ve seçimlerinizi kontrol edin.',400);return result.data;}
export function verifyMediaBytes(bytes:Buffer,reference:{sizeBytes:number;sha256:string}){requireValue(bytes.length===reference.sizeBytes&&digest(bytes)===reference.sha256,'Görsel bütünlüğü kaynak kaydıyla eşleşmiyor.');}
function xml(value:string){requireValue(!/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffe\uffff\p{Surrogate}]/u.test(value),'Metinde desteklenmeyen kontrol karakteri var.');return value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]!));}
async function imageSnapshot(url:string,fixture:boolean):Promise<ImageSnapshot>{
 if(/^\/media\/atelier-0[1-6]\.svg$/.test(url)){
  requireValue(fixture&&local(),'Yerel örnek illüstrasyon gerçek ürün fotoğrafı yerine kullanılamaz.');
  const bytes=await readConfinedFile(path.resolve('public/media'),url.slice('/media/'.length),{maxBytes:200000});
  return {dataUri:`data:image/svg+xml;base64,${bytes.toString('base64')}`,sha256:digest(bytes),rightsReference:'Projenin özgün yerel geliştirme illüstrasyonu; gerçek ürün fotoğrafı değildir.',source:url,raster:false};
 }
 requireValue(/^\/uploads\/[a-f0-9-]{36}\.webp$/.test(url),'Kullanım hakkı kayıtlı ürün görseli seçin.');
 const filename=url.slice('/uploads/'.length),[row]=await query<{object_key:string;size_bytes:number;sha256:string;rights_reference:string;mime_type:string}>('SELECT object_key,size_bytes,sha256,rights_reference,mime_type FROM media_assets WHERE object_key=$1',[`products/${filename}`]);
 requireValue(row&&row.mime_type==='image/webp'&&row.rights_reference?.trim().length>=5&&row.size_bytes>0&&row.size_bytes<=8*1024*1024,'Görselin kullanım hakkı veya boyut kaydı eksik.');
 const bytes=await storage().get(row.object_key,{maxBytes:8*1024*1024,timeoutMs:5000});verifyMediaBytes(bytes,{sizeBytes:row.size_bytes,sha256:row.sha256});validateRaster(bytes,row.mime_type);
 return {dataUri:`data:image/webp;base64,${bytes.toString('base64')}`,sha256:row.sha256,rightsReference:row.rights_reference,source:url,raster:true};
}
type ProductSource={product_id:string;variant_id:string;name:string;name_en:string;variant_name:string;variant_name_en:string;sku:string;image:string;fixture:boolean;amount_minor:number|null};
export async function socialSnapshot(input:SocialInput,principal:Principal):Promise<SocialSnapshot>{
 authorize(principal);const common={template:input.template,theme:input.theme,locale:input.locale,generatedAt:new Date().toISOString()};
 if(input.template==='profile'||input.template==='cover')return {...common,title:'SEXSOGATE',subtitle:'Tutkunu Keşfet.',fixture:false,source:{kind:'brand',id:'sexsogate-geometric-redraw'}};
 if('productId'in input){
  const [row]=await query<ProductSource>("SELECT p.id product_id,v.id variant_id,p.name,p.name_en,v.name variant_name,v.name_en variant_name_en,v.sku,p.image,p.fixture,vp.amount_minor FROM products p JOIN categories c ON c.slug=p.category AND c.active=true JOIN variants v ON v.product_id=p.id AND v.active=true LEFT JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=$3 AND vp.amount_minor>0 AND vp.valid_from<=now() AND(vp.valid_until IS NULL OR vp.valid_until>now()) WHERE p.id=$1 AND v.id=$2 AND p.status='published' AND($4='tr' OR length(trim(p.description_en))>0)",[input.productId,input.variantId,input.currency,input.locale]);
  requireValue(row,'Ürün ve seçenek aynı yayımlanmış kayda ait olmalıdır.',404);requireValue(!row.fixture||local(),'Örnek ürün canlı ortamda dışa aktarılamaz.');
  requireValue(row.amount_minor!==null&&Number.isSafeInteger(Number(row.amount_minor))&&Number(row.amount_minor)>0,'Seçilen para biriminde güncel fiyat kaydı yok.');
  requireValue(input.locale==='tr'||(row.name_en?.trim()&&row.variant_name_en?.trim()),'Seçilen dilde ürün ve seçenek metni tamamlanmalı.');
  const title=input.locale==='en'?row.name_en:row.name,variantName=input.locale==='en'?row.variant_name_en:row.variant_name;
  return {...common,title,subtitle:input.locale==='en'?'Discover at your own pace.':'Kendi ritminizde keşfedin.',fixture:row.fixture,source:{kind:'product',id:row.product_id,variantId:row.variant_id},variantName,sku:row.sku,priceMinor:Number(row.amount_minor),currency:input.currency,image:await imageSnapshot(row.image,row.fixture)};
 }
 if(input.template==='collection'){
  const [row]=await query("SELECT r.id,r.fixture,v.version,v.payload FROM cms_regions r JOIN LATERAL(SELECT version,payload FROM cms_region_revisions WHERE region_id=r.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)v ON true WHERE r.key=$1 AND r.locale=$2 AND r.kind='collection' AND r.active=true",[input.collectionKey,input.locale]);
  requireValue(row,'Bu dilde yayımlanmış koleksiyon bulunamadı.',404);requireValue(!row.fixture||local(),'Örnek koleksiyon canlı ortamda dışa aktarılamaz.');
  const content=parseCMSPayload(row.payload);requireValue(content.kind==='collection','Koleksiyon içeriği geçersiz.');
  const members=await query("SELECT p.id,p.fixture FROM products p WHERE p.id=ANY($1::text[]) AND p.status='published' AND EXISTS(SELECT 1 FROM categories c WHERE c.slug=p.category AND c.active=true) AND EXISTS(SELECT 1 FROM variants v WHERE v.product_id=p.id AND v.active=true) AND($2 OR p.fixture=false) AND($3='tr' OR(length(trim(p.name_en))>0 AND length(trim(p.description_en))>0))",[content.productIds,local(),input.locale]);
  requireValue(members.length,'Koleksiyonda bu dilde yayıma uygun ürün bulunmuyor.');
  const fixture=row.fixture||members.some(value=>value.fixture);
  return {...common,title:content.title,subtitle:content.description,fixture,source:{kind:'collection',id:row.id,version:row.version},image:await imageSnapshot(content.image,fixture)};
 }
 const page=await publicGuidePage(input.articleSlug,input.locale);requireValue(page,'Bu dilde yayımlanmış rehber bulunamadı.',404);
 return {...common,title:page.title,subtitle:page.body.replace(/^#+\s*/gm,'').replace(/\s+/g,' ').trim(),fixture:page.fixture,source:{kind:'information',id:page.id,version:page.version}};
}

type Assets={body:Buffer;display:Buffer;licenses:string;lightLogo:string;darkLogo:string;symbol:string};let assetsPromise:Promise<Assets>|undefined;
async function assets():Promise<Assets>{
 return assetsPromise??=Promise.all([
  readConfinedFile(path.resolve('assets/fonts'),'SexsogateBody-Regular.ttf',{maxBytes:1000000}),readConfinedFile(path.resolve('assets/fonts'),'SexsogateDisplay-Regular.ttf',{maxBytes:1000000}),
  readConfinedFile(path.resolve('assets/fonts'),'Montserrat-OFL.txt',{maxBytes:20000}),readConfinedFile(path.resolve('assets/fonts'),'PlayfairDisplay-OFL.txt',{maxBytes:20000}),
  readConfinedFile(path.resolve('public/brand'),'logo-horizontal-light.svg',{maxBytes:100000}),readConfinedFile(path.resolve('public/brand'),'logo-horizontal.svg',{maxBytes:100000}),readConfinedFile(path.resolve('public/brand'),'symbol.svg',{maxBytes:100000})
 ]).then(([body,display,bodyLicense,displayLicense,lightLogo,darkLogo,symbol])=>({body,display,licenses:bodyLicense.toString('utf8')+'\n'+displayLicense.toString('utf8'),lightLogo:lightLogo.toString('utf8'),darkLogo:darkLogo.toString('utf8'),symbol:symbol.toString('utf8')})).catch(error=>{assetsPromise=undefined;throw error;});
}
function fragment(source:string,prefix:string,x:number,y:number,width:number,height:number,viewBox:string){
 requireValue(!/<(?:script|foreignObject|image)\b|<!DOCTYPE|(?:href|src)\s*=/i.test(source),'Marka vektörünün güvenli kaynak geometrisi doğrulanamadı.');
 const inner=source.replace(/^<svg\b[^>]*>/,'').replace(/<\/svg>\s*$/,'').replace(/\bid="([^"]+)"/g,(_,id:string)=>`id="${prefix}-${id}"`).replace(/url\(#([^)]+)\)/g,(_,id:string)=>`url(#${prefix}-${id})`).replace(/aria-labelledby="[^"]*"/g,'');
 return `<svg x="${x}" y="${y}" width="${width}" height="${height}" viewBox="${viewBox}" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
}
function fitText(document:PDFKit.PDFDocument,text:string,font:'body'|'display',width:number,maxLines:number,maxSize:number,minSize:number){
 requireValue(text.length<=5000,'Şablon metni çok uzun.');xml(text);
 for(let size=maxSize;size>=minSize;size-=2){
  document.font(font).fontSize(size);const words=text.trim().split(/\s+/),lines:string[]=[];let line='';
  for(const word of words){if(document.widthOfString(word)>width){if(line){lines.push(line);line='';}const parts=Array.from(new Intl.Segmenter('tr',{granularity:'grapheme'}).segment(word),part=>part.segment);for(const part of parts){if(document.widthOfString(line+part)>width&&line){lines.push(line);line='';}line+=part;}continue;}
   const candidate=line?line+' '+word:word;if(document.widthOfString(candidate)<=width)line=candidate;else{lines.push(line);line=word;}}
  if(line)lines.push(line);if(lines.length<=maxLines)return {lines,size};
 }
 throw new HttpError(409,'Kaynak metin okunabilir boyutta şablona sığmıyor. Katalog veya içerik başlığını düzenleyin.');
}
function textBlock(document:PDFKit.PDFDocument,value:string,font:'body'|'display',x:number,y:number,width:number,maxLines:number,maxSize:number,minSize:number,color:string,field:string){
 const fit=fitText(document,value,font,width,maxLines,maxSize,minSize),leading=Math.ceil(fit.size*1.22);
 return {height:fit.lines.length*leading,svg:`<text data-field="${field}" x="${x}" y="${y}" fill="${color}" font-family="${font==='body'?'SexsogateBody':'SexsogateDisplay'}" font-size="${fit.size}">${fit.lines.map((line,index)=>`<tspan x="${x}" dy="${index?leading:0}">${xml(line)}</tspan>`).join('')}</text>`};
}
export async function renderSocialSVG(snapshot:SocialSnapshot):Promise<string>{
 requireValue(!snapshot.fixture||local(),'Örnek çıktı canlı ortamda üretilemez.');
 if(snapshot.image)requireValue(/^data:image\/(?:webp|svg\+xml);base64,[A-Za-z0-9+/]+={0,2}$/.test(snapshot.image.dataUri)&&snapshot.image.dataUri.length<=12*1024*1024,'Şablon görseli yalnız doğrulanmış, gömülü kaynak olabilir.');
 const media=await assets(),{width,height}=socialSizes[snapshot.template],dark=snapshot.theme==='dark',background=dark?'#5A0A20':'#FBF4EF',foreground=dark?'#FBF4EF':'#5A0A20',secondary=dark?'#E7B4BD':'#716168';
 const document=new PDFDocument({autoFirstPage:false});document.registerFont('body',media.body);document.registerFont('display',media.display);
 try{
  const metadata={brand:'SEXSOGATE',generatedAt:snapshot.generatedAt,source:snapshot.source,fixture:snapshot.fixture,sku:snapshot.sku,variantName:snapshot.variantName,priceMinor:snapshot.priceMinor,currency:snapshot.currency,image:snapshot.image?{sha256:snapshot.image.sha256,rightsReference:snapshot.image.rightsReference,source:snapshot.image.source,raster:snapshot.image.raster}:undefined,brandSource:'Kullanıcı raster referansının geometrik yeniden yorumu; özgün kaynak vektör teslimi değildir.',fontLicenses:media.licenses};
  const fontCSS=`@font-face{font-family:SexsogateBody;src:url(data:font/ttf;base64,${media.body.toString('base64')}) format('truetype')}@font-face{font-family:SexsogateDisplay;src:url(data:font/ttf;base64,${media.display.toString('base64')}) format('truetype')}`;
  let content=`<rect width="${width}" height="${height}" fill="${background}"/><path d="M${width-230} ${height}V250a160 160 0 0 0-320 0v${height-250}" fill="none" stroke="${dark?'#8E0F38':'#E6D8DC'}" stroke-width="2"/>`;
  if(snapshot.template==='profile'){content+=fragment(media.symbol,'profile',240,150,600,650,'0 0 240 260');content+=textBlock(document,'Tutkunu Keşfet.','display',240,935,600,1,56,36,foreground,'slogan').svg;}
  else if(snapshot.template==='cover'){
   content+=fragment(dark?media.lightLogo:media.darkLogo,'logo',80,90,690,114,'0 0 690 114');
   content+=textBlock(document,'Tutkunu Keşfet.','display',88,350,1000,1,86,44,foreground,'slogan').svg;
   content+=fragment(media.symbol,'cover',1250,130,240,300,'0 0 240 260');
  }else{
   content+=fragment(dark?media.lightLogo:media.darkLogo,'logo',80,65,580,96,'0 0 690 114');
   const story=snapshot.template==='story',imageY=story?260:220,imageHeight=story?800:560;
   if(snapshot.image)content+=`<rect x="80" y="${imageY}" width="920" height="${imageHeight}" rx="24" fill="#FFFFFF"/><image data-field="product-image" href="${snapshot.image.dataUri}" x="108" y="${imageY+28}" width="864" height="${imageHeight-56}" preserveAspectRatio="xMidYMid meet"/>`;
   else content+=fragment(media.symbol,'editorial',420,240,240,260,'0 0 240 260');
   const start=snapshot.image?imageY+imageHeight+95:620;
   const title=textBlock(document,snapshot.title,'display',80,start,920,3,66,34,foreground,'title');content+=title.svg;
   let cursor=start+title.height+20;
   if(snapshot.variantName){const variant=textBlock(document,snapshot.variantName,'body',82,cursor,900,2,27,20,secondary,'variant');content+=variant.svg;cursor+=variant.height+20;}
   if(snapshot.priceMinor!==undefined&&snapshot.currency){const price=formatMinorAmount(snapshot.priceMinor,snapshot.currency,2,snapshot.locale==='tr'?'tr-TR':'en-GB');content+=textBlock(document,price,'body',80,cursor+20,900,1,48,30,foreground,'price').svg;cursor+=80;}
   else{const parts=Array.from(new Intl.Segmenter(snapshot.locale,{granularity:'grapheme'}).segment(snapshot.subtitle),part=>part.segment),limit=snapshot.template==='information'?360:160,excerpt=parts.slice(0,limit).join('')+(parts.length>limit?'…':'');const subtitle=textBlock(document,excerpt,'body',82,cursor,900,snapshot.template==='information'?7:3,29,22,secondary,'description');content+=subtitle.svg;cursor+=subtitle.height;}
   requireValue(cursor<height-95,'Kaynak metin şablonun güvenli alanını aşıyor.');
   const footer=snapshot.sku?`SKU ${snapshot.sku}`:snapshot.locale==='tr'?'Tutkunu Keşfet.':'Discover your desire.';
   content+=textBlock(document,footer,'body',82,height-55,900,1,20,16,secondary,'reference').svg;
  }
  const output=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="social-title"><title id="social-title">${xml(snapshot.title)}</title><metadata>${xml(JSON.stringify(metadata))}</metadata><style>${fontCSS}</style>${content}</svg>`;
  requireValue(Buffer.byteLength(output,'utf8')<=16*1024*1024,'Şablon dosyası güvenli çıktı boyutunu aşıyor.');return output;
 }finally{document.destroy();}
}
export async function generateSocialAsset(input:unknown,principal:Principal){
 authorize(principal);const value=parseSocialInput(input),snapshot=await socialSnapshot(value,principal),svg=await renderSocialSVG(snapshot),sha256=digest(svg);
 await query("INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,'download','social',$2,$3)",[principal.id,snapshot.source.id,JSON.stringify({template:value.template,theme:value.theme,locale:value.locale,source:snapshot.source,sku:snapshot.sku,priceMinor:snapshot.priceMinor,currency:snapshot.currency,fixture:snapshot.fixture,sha256,generatedAt:snapshot.generatedAt})]);
 return {svg,sha256,snapshot,filename:`sexsogate-${value.template}-${value.locale}-${value.theme}-${sha256.slice(0,10)}.svg`};
}
export async function socialSources(principal:Principal,filter:{view?:string;locale?:string;currency?:string;q?:string;page?:number;productId?:string}){
 authorize(principal);const data=z.object({view:z.enum(['products','variants','collections','information']).default('products'),locale:z.enum(['tr','en']).default('tr'),currency:z.enum(['TRY','EUR','USD','GBP']).default('TRY'),q:z.string().max(100).default(''),page:z.number().int().min(1).max(100000).default(1),productId:z.string().max(100).optional()}).strict().safeParse(filter);requireValue(data.success,'Kaynak arama seçeneklerini kontrol edin.',400);
 const f=data.data,search=`%${f.q.replace(/[\\%_]/g,'\\$&')}%`,offset=(f.page-1)*25;let sourceSQL:string,values:unknown[];let ordering='id';
 if(f.view==='products'){
  sourceSQL="SELECT p.id,CASE WHEN $3='en' THEN p.name_en ELSE p.name END name,p.fixture FROM products p JOIN categories c ON c.slug=p.category AND c.active=true WHERE p.status='published' AND($4 OR p.fixture=false) AND($3='tr' OR(length(trim(p.name_en))>0 AND length(trim(p.description_en))>0)) AND sg_search_normalize(p.name||' '||p.name_en) LIKE sg_search_normalize($1)";
  values=[search,offset,f.locale,local()];ordering='name,id';
 }else if(f.view==='variants'){
  sourceSQL="SELECT v.id,v.sku,CASE WHEN $3='en' THEN v.name_en ELSE v.name END name,vp.amount_minor price_minor FROM variants v JOIN products p ON p.id=v.product_id JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=$4 AND vp.amount_minor>0 AND vp.valid_from<=now() AND(vp.valid_until IS NULL OR vp.valid_until>now()) WHERE v.product_id=$5 AND v.active=true AND p.status='published' AND($6 OR p.fixture=false) AND($3='tr' OR length(trim(v.name_en))>0) AND sg_search_normalize(v.sku||' '||v.name||' '||v.name_en) LIKE sg_search_normalize($1)";
  values=[search,offset,f.locale,f.currency,f.productId??'',local()];ordering='sku,id';
 }else if(f.view==='collections'){
  sourceSQL="SELECT r.key id,v.payload->>'title' name,r.fixture FROM cms_regions r JOIN LATERAL(SELECT payload FROM cms_region_revisions WHERE region_id=r.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)v ON true WHERE r.kind='collection' AND r.active=true AND r.locale=$3 AND($4 OR r.fixture=false) AND sg_search_normalize(v.payload->>'title') LIKE sg_search_normalize($1)";
  values=[search,offset,f.locale,local()];
 }else{
  sourceSQL="SELECT p.slug id,r.title name,p.fixture FROM content_pages p JOIN LATERAL(SELECT title,kind FROM content_revisions WHERE page_id=p.id AND status='published' AND(publish_at IS NULL OR publish_at<=now()) ORDER BY version DESC LIMIT 1)r ON true WHERE p.locale=$3 AND r.kind IN('guide','page') AND p.slug NOT IN('sss','iletisim','home-campaign','gizlilik','mesafeli-satis','cerezler','iade') AND($4 OR p.fixture=false) AND sg_search_normalize(r.title) LIKE sg_search_normalize($1)";
  values=[search,offset,f.locale,local()];
 }
 // Kaynak ve toplam tek SQL snapshot'ını paylaşır; boş bir sayfa toplamı silmez.
 const [result]=await query<{rows:Record<string,unknown>[];total:number}>(`WITH source AS MATERIALIZED(${sourceSQL}),page AS(SELECT * FROM source ORDER BY ${ordering} LIMIT 25 OFFSET $2) SELECT coalesce((SELECT jsonb_agg(to_jsonb(page) ORDER BY ${ordering}) FROM page),'[]'::jsonb) rows,(SELECT count(*) FROM source) total`,values);
 return {rows:result.rows,total:Number(result.total),page:f.page};
}
