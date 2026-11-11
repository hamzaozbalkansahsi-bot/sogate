/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/sitemaps/[part]/route.ts
 * Açıklama   : Gerçek yayın kaydına uygun sayfalı sitemap bölümünü sunar.
 */
import {sitemapPart} from '@/server/sitemaps';
export const dynamic='force-dynamic';
export async function GET(_request:Request,{params}:{params:Promise<{part:string}>}){
 const result=await sitemapPart((await params).part);return new Response(result??'Sitemap bölümü bulunamadı.',{status:result?200:404,headers:{'Content-Type':result?'application/xml; charset=utf-8':'text/plain; charset=utf-8','Cache-Control':'public, max-age=300'}});
}
