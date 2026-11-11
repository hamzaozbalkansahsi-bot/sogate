/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/seo-management.ts
 * Açıklama   : Dil bazlı ürün metaverisini ve açık sayfa yönlendirmelerini denetlenebilir biçimde yönetir.
 */
import {z} from 'zod';
import {pool,query,transaction,type Connection} from './db';
import {HttpError} from './security';
import type {Principal,Locale} from '../shared/contracts';
import {localizedProductPath,productSlug,safePublicPath,seoFields} from '../shared/seo-rules';
import {PUBLIC_PRODUCT_SQL,ENGLISH_PRODUCT_SQL} from './public-catalog';

export function authorizeSEO(principal:Principal){
 if(!principal.mfa||!['admin','catalog','marketing'].includes(principal.role))throw new HttpError(403,'Bu SEO işlemi için yetkiniz yok.');
}
function parse<T>(schema:z.ZodType<T>,value:unknown):T{
 const result=schema.safeParse(value);if(!result.success)throw new HttpError(400,'SEO alanlarını ve bağlantı biçimini kontrol edin.');return result.data;
}
async function audit(principal:Principal,action:string,id:string,details:Record<string,unknown>,connection:Connection){
 await query('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,$2,\'seo\',$3,$4)',[principal.id,action,id,JSON.stringify(details)],connection);
}
export async function productSEO(productId:string,locale:Locale){
 const [row]=await query('SELECT p.seo,r.slug FROM products p JOIN product_routes r ON r.product_id=p.id AND r.locale=$2 WHERE p.id=$1',[productId,locale]);
 return row?{slug:row.slug,title:String(row.seo?.[locale]?.title??''),description:String(row.seo?.[locale]?.description??''),alt:String(row.seo?.[locale]?.alt??'')}:null;
}
export async function saveProductSEO(input:unknown,principal:Principal){
 authorizeSEO(principal);
 const value=parse(seoFields.extend({action:z.literal('product'),productId:z.string().min(1).max(100),locale:z.enum(['tr','en']),slug:productSlug}),input);
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock(hashtext('sexsogate-public-routes'))",[],connection);
  const [product]=await query('SELECT p.id,r.slug FROM products p JOIN product_routes r ON r.product_id=p.id AND r.locale=$2 WHERE p.id=$1 FOR UPDATE OF p,r',[value.productId,value.locale],connection);
  if(!product)throw new HttpError(404,'Ürün bulunamadı.');
  const collision=await query('SELECT product_id FROM product_routes WHERE locale=$1 AND slug=$2 AND product_id<>$3',[value.locale,value.slug,value.productId],connection);
  if(collision.length)throw new HttpError(409,'Bu dilde bağlantı başka bir üründe kullanılıyor.');
  const oldPath=localizedProductPath(value.locale,product.slug),newPath=localizedProductPath(value.locale,value.slug);
  if(oldPath!==newPath){
   const [prior]=await query('SELECT to_path FROM public_redirects WHERE from_path=$1 AND active=true',[newPath],connection);
   if(prior&&prior.to_path!==oldPath)throw new HttpError(409,'Yeni bağlantı mevcut bir yönlendirmeyle çakışıyor.');
   await query('UPDATE public_redirects SET active=false,updated_at=now() WHERE from_path=$1',[newPath],connection);
   await query('UPDATE product_routes SET slug=$3,updated_at=now() WHERE product_id=$1 AND locale=$2',[value.productId,value.locale,value.slug],connection);
   await query('UPDATE public_redirects SET to_path=$2,updated_at=now() WHERE to_path=$1 AND active=true',[oldPath,newPath],connection);
   await query("INSERT INTO public_redirects(from_path,to_path,reason,created_by) VALUES($1,$2,'Aynı ürünün dil bazlı bağlantısı güncellendi.',$3) ON CONFLICT(from_path) DO UPDATE SET to_path=excluded.to_path,active=true,reason=excluded.reason,updated_at=now()",[oldPath,newPath,principal.id],connection);
  }
  const fields={title:value.title,description:value.description,alt:value.alt};
  await query('UPDATE products SET seo=jsonb_set(seo,ARRAY[$2]::text[],$3::jsonb,true),updated_at=now() WHERE id=$1',[value.productId,value.locale,JSON.stringify(fields)],connection);
  await audit(principal,'product_metadata_updated',value.productId,{locale:value.locale,oldPath,newPath},connection);
  return {ok:true,path:newPath};
 });
}
function publicPath(value:string){try{return safePublicPath(value);}catch{throw new HttpError(400,'Yalnız açık, güvenli site içi yol kullanılabilir.');}}
async function activeProductPath(path:string,connection:Connection=pool){
 const match=/^(\/en)?\/urun\/([a-z0-9-]+)$/.exec(path);if(!match)return false;
 return (await query(`SELECT r.product_id FROM product_routes r JOIN products p ON p.id=r.product_id WHERE r.locale=$1 AND r.slug=$2 AND ${PUBLIC_PRODUCT_SQL} AND($1='tr' OR(${ENGLISH_PRODUCT_SQL})) AND(p.fixture=false OR $3=true)`,[match[1]?'en':'tr',match[2],['development','test'].includes(process.env.APP_ENV??'')],connection)).length>0;
}
async function validDestination(path:string,connection:Connection){
 if(await activeProductPath(path,connection))return true;
 if(['/', '/en','/urunler','/en/urunler','/koleksiyonlar','/en/koleksiyonlar','/rehber','/en/rehber','/sss','/en/sss','/iletisim','/en/iletisim'].includes(path))return true;
 const match=/^(\/en)?\/rehber\/([a-z0-9-]+)$/.exec(path);
 if(match){const {publicGuidePage}=await import('./cms');return !!await publicGuidePage(match[2],match[1]?'en':'tr',connection);}
 return false;
}
export async function manageRedirect(input:unknown,principal:Principal){
 authorizeSEO(principal);
 const data=parse(z.object({action:z.literal('redirect'),from:z.string(),to:z.string(),reason:z.string().trim().min(10).max(1000),active:z.boolean().default(true)}).strict(),input);
 const from=publicPath(data.from),to=publicPath(data.to);
 if(from===to)throw new HttpError(400,'Kaynak ve hedef aynı olamaz.');
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock(hashtext('sexsogate-public-routes'))",[],connection);
  if(await activeProductPath(from,connection))throw new HttpError(409,'Yayındaki ürün yolunu ürün SEO düzenleyicisinden değiştirin.');
  if(data.active){
   if(!await validDestination(to,connection))throw new HttpError(400,'Hedef, mevcut ve açık bir sayfa olmalıdır.');
   const outgoing=await query('SELECT id FROM public_redirects WHERE from_path=$1 AND active=true',[to],connection);
   if(outgoing.length)throw new HttpError(409,'Zincir veya döngü yerine doğrudan son sayfayı seçin.');
   const incoming=await query('SELECT id FROM public_redirects WHERE to_path=$1 AND active=true',[from],connection);
   if(incoming.length)throw new HttpError(409,'Bu kaynak başka yönlendirmelerin hedefi. Önce onları son hedefe güncelleyin.');
  }
  const [row]=await query('INSERT INTO public_redirects(from_path,to_path,reason,created_by,active) VALUES($1,$2,$3,$4,$5) ON CONFLICT(from_path) DO UPDATE SET to_path=excluded.to_path,reason=excluded.reason,active=excluded.active,updated_at=now() RETURNING id',[from,to,data.reason,principal.id,data.active],connection);
  await audit(principal,data.active?'redirect_saved':'redirect_disabled',row.id,{from,to,reason:data.reason},connection);return {id:row.id};
 });
}
export async function redirects(principal:Principal){authorizeSEO(principal);return query('SELECT id,from_path,to_path,reason,active,updated_at FROM public_redirects ORDER BY updated_at DESC LIMIT 100');}
export async function publicRedirect(pathname:string){
 let from:string;try{from=safePublicPath(pathname);}catch{return null;}
 const [row]=await query('SELECT to_path FROM public_redirects WHERE from_path=$1 AND active=true',[from]);
 if(!row||await activeProductPath(from)||!await validDestination(row.to_path,pool))return null;
 try{return safePublicPath(row.to_path);}catch{return null;}
}
