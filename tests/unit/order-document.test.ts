/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/order-document.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {it,expect} from 'vitest';
import {makeOrderDocument} from '../../src/server/order-document';
import type {OrderSummary} from '../../src/shared/contracts';
it('gerçek sipariş özetini Türkçe fontla PDF üretir; mali belge yerine geçmez',async()=>{
 const order:OrderSummary={id:'local',number:'SG-LOCAL',status:'confirmed',paymentStatus:'succeeded',fulfillmentStatus:'unfulfilled',currency:'TRY',subtotalMinor:12345,shippingMinor:1000,taxMinor:2058,discountMinor:0,totalMinor:13345,createdAt:'2026-11-10T12:00:00Z',items:[{variantId:'v',name:'İç Giyim · Ölçü ve Özellikler',sku:'LOCAL',quantity:1,unitMinor:12345}],shipments:[]};
 const pdf=await makeOrderDocument(order,[{title:'Güvenli Alışveriş',body:'Hamza ÖZBALKAN · İstanbul · İzmir · Iğdır · Şişli · Çeşme. ı İ i I ş Ş ğ Ğ ü Ü ö Ö ç Ç.',version:1,bodyHash:'a'.repeat(64),acceptedAt:'2026-11-10T12:00:00Z'}]);
 expect(pdf.subarray(0,5).toString()).toBe('%PDF-');expect(pdf.length).toBeGreaterThan(5000);
});
