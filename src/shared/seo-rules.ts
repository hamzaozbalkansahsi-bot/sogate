/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/seo-rules.ts
 * Açıklama   : Dil bazlı genel yolları ve SEO metinlerinin güvenli biçimini tanımlar.
 */
import {z} from 'zod';
export const productSlug=z.string().min(1).max(120).regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
const plain=(min:number,max:number)=>z.string().trim().min(min).max(max).refine(value=>!/[<>\u0000-\u001f]/.test(value),'HTML veya kontrol karakteri kullanmayın.');
export const seoFields=z.object({title:plain(5,120),description:plain(20,320),alt:plain(0,250)}).strict();
export function localizedProductPath(locale:'tr'|'en',slug:string){return `${locale==='en'?'/en':''}/urun/${productSlug.parse(slug)}`;}
export function safePublicPath(value:string):string{
 if(typeof value!=='string'||value.length>350||!/^\/(?:[a-z0-9]+(?:-[a-z0-9]+)*\/?)*$/.test(value)||value.includes('//'))throw new Error('Yalnız açık genel sayfa yolu kullanılabilir.');
 const pathname=value.startsWith('/en/')?value.slice(3):value;
 if(/^\/(?:api|hesap|sepet|odeme|siparis|yonetim|favoriler|uploads|_next)(?:\/|$)/.test(pathname))throw new Error('Özel sayfa yönlendirmede kullanılamaz.');
 return value.length>1&&value.endsWith('/')?value.slice(0,-1):value;
}
