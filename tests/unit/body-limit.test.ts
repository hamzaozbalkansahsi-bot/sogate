/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/body-limit.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {it,expect} from 'vitest';
import {readJsonLimited} from '../../src/server/security';
it('Content-Length verilmeden de gövde kotasını uygulayarak rezervasyon isteğini reddeder',async()=>{
 const request=new Request('http://localhost/api/checkout',{method:'POST',body:JSON.stringify({data:'x'.repeat(2000)})});
 expect(request.headers.get('content-length')).toBeNull();
 await expect(readJsonLimited(request,100)).rejects.toThrow('boyutu');
});
it('Türkçe JSON gövdesini özgün karakterleriyle çözer',async()=>{
 const request=new Request('http://localhost/api/checkout',{method:'POST',body:JSON.stringify({name:'Hamza ÖZBALKAN',city:'Iğdır',label:'İç Giyim · Ölçü ve Özellikler'})});
 expect(await readJsonLimited(request,1000)).toEqual({name:'Hamza ÖZBALKAN',city:'Iğdır',label:'İç Giyim · Ölçü ve Özellikler'});
});
