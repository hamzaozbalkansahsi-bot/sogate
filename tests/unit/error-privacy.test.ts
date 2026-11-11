/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/error-privacy.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {it,expect} from 'vitest';
import {HttpError,publicFailure} from '../../src/server/security';
it('sağlayıcı 4xx hatasındaki anahtar veya müşteri ayrıntısını cevaba taşımaz',()=>{
 const external=Object.assign(new Error('Invalid API Key provided: sk_test_private_fixture'),{statusCode:401,code:'authentication_error'});
 const result=publicFailure(external);expect(result.status).toBe(500);expect(JSON.stringify(result)).not.toContain('sk_test');expect(result.message).toBeUndefined();
});
it('yalnız açıkça güvenli uygulama hatasını açıklamasıyla döndürür',()=>{
 expect(publicFailure(new HttpError(409,'Stok yeterli değil.','STOCK_CONFLICT'))).toEqual({status:409,message:'Stok yeterli değil.',code:'STOCK_CONFLICT'});
});
