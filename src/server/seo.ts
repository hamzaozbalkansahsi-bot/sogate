/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/seo.ts
 * Açıklama   : Sayfalı katalog üzerinden dil, metaveri, görsel ve temel schema tutarlılığını denetler.
 */
import {query} from './db';
import {access} from 'node:fs/promises';
import path from 'node:path';
import type {Principal,Locale} from '../shared/contracts';
import {authorizeSEO} from './seo-management';
import {localizedProductPath} from '../shared/seo-rules';
import {PUBLIC_PRODUCT_SQL,ENGLISH_PRODUCT_SQL} from './public-catalog';
import {HttpError} from './security';
export async function seoReport(principal:Principal,filter:{locale?:Locale;page?:number;q?:string}={}){
 authorizeSEO(principal);const locale=filter.locale??'tr',page=filter.page??1,limit=25;
 if(!Number.isSafeInteger(page)||page<1||page>100000)throw new HttpError(400,'Geçerli bir sayfa numarası girin.');
 const search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const values=[locale,search,limit,(page-1)*limit];
 const products=await query(`WITH catalog AS(
  SELECT p.*,r.slug route_slug,(${PUBLIC_PRODUCT_SQL} AND($1='tr' OR(${ENGLISH_PRODUCT_SQL}))) publicly_available,coalesce(p.seo->$1::text->>'title',CASE WHEN $1='en' THEN p.name_en ELSE p.name END) effective_title,
   count(*) OVER(PARTITION BY lower(coalesce(p.seo->$1::text->>'title',CASE WHEN $1='en' THEN p.name_en ELSE p.name END))) duplicate_title,
   count(*) OVER(PARTITION BY nullif(p.seo->$1::text->>'description','')) duplicate_description
  FROM products p JOIN product_routes r ON r.product_id=p.id AND r.locale=$1 WHERE p.status<>'archived')
  SELECT *,count(*) OVER() total FROM catalog WHERE sg_search_normalize(name) LIKE sg_search_normalize($2) OR sg_search_normalize(name_en) LIKE sg_search_normalize($2)
  ORDER BY updated_at DESC,id LIMIT $3 OFFSET $4`,values);
 const rows=[];
 for(const p of products){
  const issues:string[]=[];const metadata=p.seo?.[locale]??{},url=localizedProductPath(locale,p.route_slug);
  if(!String(locale==='en'?p.description_en:p.description).trim())issues.push('Seçili dilde ürün açıklaması eksik');
  if(!p.name_en||!p.description_en)issues.push('İngilizce ürün çevirisi eksik');
  if(!metadata.title||!metadata.description)issues.push('Özgün SEO başlığı veya açıklaması eksik');
  if(!metadata.alt)issues.push('Açıklayıcı görsel alt metni eksik');
  if(Number(p.duplicate_title)>1)issues.push('Bu dilde yinelenen başlık');
  if(metadata.description&&Number(p.duplicate_description)>1)issues.push('Bu dilde yinelenen meta açıklaması');
  if(!p.image?.startsWith('/')||p.image.includes('..'))issues.push('Güvenli görsel kaydı eksik');
  else if(p.image.startsWith('/uploads/')){
   const media=await query('SELECT object_key FROM media_assets WHERE object_key=$1',[`products/${p.image.split('/').pop()}`]);
   if(!media.length)issues.push('Medya kaydı bulunamadı');
   else if(process.env.STORAGE_PROVIDER==='s3')issues.push('Uzak görsel dosyasının varlık kontrolü bekliyor');
   else try{await access(path.resolve(process.env.STORAGE_LOCAL_PATH??'.local/media',media[0].object_key));}catch{issues.push('Medya dosyası bulunamadı');}
  }else try{await access(path.join(process.cwd(),'public',p.image));}catch{issues.push('Görsel dosyası bulunamadı');}
  if(p.fixture)issues.push('Yerel örnek; indeks ve sitemap dışında');
  if(p.status!=='published')issues.push('Yayımlanmamış ürün; sitemap dışında');
  const [variants]=await query('SELECT count(*) total,count(*) FILTER(WHERE price_minor>0 AND currency=ANY($2::text[])) valid FROM variants WHERE product_id=$1 AND active=true',[p.id,['TRY','EUR','USD','GBP']]);
  if(!Number(variants.total))issues.push('Aktif varyant yok; Product/Offer üretilemez');
  else if(Number(variants.valid)!==Number(variants.total))issues.push('Fiyat/para birimi eksik; Offer verisi geçersiz');
  rows.push({id:p.id,name:locale==='en'?p.name_en:p.name,url,slug:p.route_slug,locale,status:p.status,metadata:{title:metadata.title??'',description:metadata.description??'',alt:metadata.alt??''},issues,eligibleForSitemap:p.publicly_available&&!p.fixture,updatedAt:p.updated_at});
 }
 return {rows,total:Number(products[0]?.total??0),page,summary:{products:Number(products[0]?.total??0),issues:rows.reduce((sum,row)=>sum+row.issues.length,0),eligible:rows.filter(row=>row.eligibleForSitemap).length},note:'İçerik bulguları ve sitemap sayısı bu sayfadaki kayıtları kapsar. Teknik denetimdir; arama sıralaması veya indekslenme puanı değildir.'};
}
