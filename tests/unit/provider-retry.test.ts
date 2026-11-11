/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/provider-retry.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {it,expect} from 'vitest';
import {assertRefundCreationWindow,choosePaymentAction} from '../../src/server/providers/retry-policy';
it('sonucu bilinmeyen 24 saatlik iadeyi yeni Stripe POST isteğine çeviremez',()=>{
 expect(()=>assertRefundCreationWindow('2026-11-10T00:00:00Z',Date.parse('2026-11-11T00:00:00Z'))).toThrow();
 expect(()=>assertRefundCreationWindow('2026-11-10T12:00:00Z',Date.parse('2026-11-10T12:01:00Z'))).not.toThrow();
});
it('ödenmiş veya süresi geçmiş sipariş için yeni tahsilat oturumu oluşturmaz',()=>{
 const now=Date.parse('2026-11-10T12:00:00Z');const base={orderStatus:'awaiting_payment',paymentStatus:'pending',expiresAt:'2026-11-10T12:15:00Z',providerReference:null};
 expect(choosePaymentAction({...base,paymentStatus:'succeeded',orderStatus:'confirmed'},now)).toBe('order');
 expect(choosePaymentAction({...base,expiresAt:'2026-11-09T12:15:00Z'},now)).toBe('order');
 expect(choosePaymentAction({...base,providerReference:'cs_saved'},now)).toBe('resume');expect(choosePaymentAction(base,now)).toBe('create');
});
