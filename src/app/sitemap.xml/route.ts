/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/sitemap.xml/route.ts
 * Açıklama   : Ürün ve içerik sitemap bölümlerinin XML dizinini sunar.
 */
import {sitemapIndex} from '@/server/sitemaps';
export const dynamic='force-dynamic';
export async function GET(){return new Response(await sitemapIndex(),{headers:{'Content-Type':'application/xml; charset=utf-8','Cache-Control':'public, max-age=300'}});}
