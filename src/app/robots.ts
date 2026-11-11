/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/robots.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import type {MetadataRoute} from 'next';
export default function robots():MetadataRoute.Robots{
 if(process.env.APP_ENV!=='production')return {rules:{userAgent:'*',disallow:'/'}};
 return {rules:{userAgent:'*',allow:'/',disallow:['/api/',...['hesap','sepet','odeme','siparis','yonetim','favoriler','veri-basvurusu'].flatMap(section=>[`/${section}`,`/en/${section}`])]},sitemap:`${process.env.APP_URL}/sitemap.xml`};
}
