/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/security.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { describe, it, expect } from 'vitest';
import { enforceSameOrigin, guardPaymentConfiguration, validateRaster, safeObjectKey } from '../../src/server/security';

describe('HTTP ve ortam sınırları', () => {
  it('aynı kökenden olmayan mutasyonu reddeder', () => {
    expect(() => enforceSameOrigin(new Request('http://localhost:3000/api/cart', {method:'POST',headers:{origin:'https://attacker.invalid'}}),'http://localhost:3000')).toThrow();
    expect(() => enforceSameOrigin(new Request('http://localhost:3000/api/cart', {method:'POST',headers:{origin:'http://localhost:3000'}}),'http://localhost:3000')).not.toThrow();
  });
  it('production test adaptörünü ve onaysız Stripe canlı tahsilatını reddeder', () => {
    expect(() => guardPaymentConfiguration({appEnv:'production',provider:'test',liveEnabled:false,stripeApproved:false})).toThrow();
    expect(() => guardPaymentConfiguration({appEnv:'production',provider:'stripe',liveEnabled:true,stripeApproved:false})).toThrow();
    expect(() => guardPaymentConfiguration({appEnv:'development',provider:'test',liveEnabled:false,stripeApproved:false})).not.toThrow();
  });
  it('yüklenen SVG/HTML içeriğini ve sahte raster türünü reddeder', () => {
    expect(() => validateRaster(Buffer.from('<svg onload="evil()"/>'),'image/svg+xml')).toThrow();
    expect(() => validateRaster(Buffer.from('<html>'),'image/png')).toThrow();
    expect(validateRaster(Buffer.from([137,80,78,71,13,10,26,10]),'image/png')).toBe('png');
  });
  it('dosya anahtarından dizin kaçışını ve kontrol karakterini engeller', () => {
    for (const key of ['../../secret','/etc/passwd','a\\b','x\u0000y']) expect(() => safeObjectKey(key)).toThrow();
    expect(safeObjectKey('products/guvenli-urun.png')).toBe('products/guvenli-urun.png');
  });
});
