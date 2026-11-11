/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/sitemaps.ts
 * Açıklama   : Yayımlanmış gerçek içerikten dil eşleriyle bölünmüş sitemap XML üretir.
 */
import {query} from './db';
import {localizedProductPath} from '../shared/seo-rules';
import {PUBLIC_PRODUCT_SQL} from './public-catalog';
import {publicContentIndex} from './cms';
const namespace='xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"';
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]!));
const absolute=(path:string)=>new URL(path,process.env.APP_URL??'http://127.0.0.1:3000').href;
const live=()=>process.env.APP_ENV==='production';
const header='<?xml version="1.0" encoding="UTF-8"?>';
const openSet=`${header}<urlset ${namespace} xmlns:xhtml="http://www.w3.org/1999/xhtml">`;
export async function sitemapIndex(){
 const entries:string[]=[];
 if(live()){
  const content=await publicContentIndex();
  for(let page=0;page<Math.max(1,Math.ceil(content.length/1000));page++)entries.push(absolute(page?`/sitemaps/content-${page}`:'/sitemaps/content'));
  const [count]=await query(`SELECT count(*) n FROM products p WHERE ${PUBLIC_PRODUCT_SQL} AND p.fixture=false`);
  for(let page=0;page<Math.ceil(Number(count.n)/1000);page++)entries.push(absolute(`/sitemaps/products-${page}`));
 }
 return `${header}<sitemapindex ${namespace}>${entries.map(url=>`<sitemap><loc>${escape(url)}</loc></sitemap>`).join('')}</sitemapindex>`;
}
function entry(url:string,updatedAt?:Date,alternates?:Partial<Record<'tr'|'en',string>>){
 const lastmod=updatedAt?`<lastmod>${updatedAt.toISOString()}</lastmod>`:'';
 const languages=alternates?Object.entries({...alternates,'x-default':alternates.tr??alternates.en}).filter(([,href])=>href).map(([language,href])=>`<xhtml:link rel="alternate" hreflang="${language==='tr'?'tr-TR':language}" href="${escape(absolute(href!))}"/>`).join(''):'';
 return `<url><loc>${escape(absolute(url))}</loc>${lastmod}${languages}</url>`;
}
export async function sitemapPart(part:string):Promise<string|null>{
 if(part!=='content'&&!/^content-[1-9]\d{0,7}$/.test(part)&&!/^products-\d{1,8}$/.test(part))return null;
 if(!live())return `${openSet}</urlset>`;
 const entries:string[]=[];
 if(part==='content'||part.startsWith('content-')){
  const offset=part==='content'?0:Number(part.slice(8));
  if(offset===0)for(const pathname of ['/','/urunler','/koleksiyonlar','/rehber','/sss','/iletisim']){
   const tr=pathname,en=pathname==='/'?'/en':`/en${pathname}`;entries.push(entry(tr,undefined,{tr,en}),entry(en,undefined,{tr,en}));
  }
  const pages=await publicContentIndex(),selected=pages.slice(offset*1000,(offset+1)*1000);
  if(offset>0&&!selected.length)return null;
  const pairs=new Map<string,Partial<Record<'tr'|'en',string>>>();for(const page of pages)pairs.set(page.slug,{...pairs.get(page.slug),[page.locale]:`${page.locale==='en'?'/en':''}/rehber/${page.slug}`});
  for(const page of selected)entries.push(entry(`${page.locale==='en'?'/en':''}/rehber/${page.slug}`,page.updatedAt,pairs.get(page.slug)));
 }else{
  const page=Number(part.slice(9));
  const rows=await query(`SELECT p.id,p.name_en,p.description_en,p.updated_at,
   max(r.slug) FILTER(WHERE r.locale='tr') tr_slug,max(r.slug) FILTER(WHERE r.locale='en') en_slug
   FROM products p JOIN product_routes r ON r.product_id=p.id WHERE ${PUBLIC_PRODUCT_SQL} AND p.fixture=false
   GROUP BY p.id ORDER BY p.id LIMIT 1000 OFFSET $1`,[page*1000]);
  if(!rows.length)return null;
  for(const row of rows){
   const tr=localizedProductPath('tr',row.tr_slug),en=row.name_en?.trim()&&row.description_en?.trim()?localizedProductPath('en',row.en_slug):undefined;
   entries.push(entry(tr,row.updated_at,{tr,en}));if(en)entries.push(entry(en,row.updated_at,{tr,en}));
  }
 }
 return `${openSet}${entries.join('')}</urlset>`;
}
