/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/purchase-receipts.test.ts
 * Açıklama   : Lotlu mal kabulünde kaynak, adet ve mükerrer satır sınırlarını doğrular.
 */
import {describe,expect,it} from 'vitest';
import {purchaseReceiptSchema,canonicalPurchaseReceipt} from '../../src/shared/purchase-receipts';
const input={action:'receive',id:'purchase',idempotencyKey:'isolated-receipt-key',reason:'Gerçek teslimat kontrolü',sourceReference:'Teslimat belge referansı',items:[{variantId:'variant',quantity:3,lots:[{lotNumber:'LOT-A',expiresAt:'2099-01-01',quantity:2,sourceReference:'Üretici etiketi A'},{lotNumber:'LOT-B',expiresAt:null,quantity:1,sourceReference:'Üretici etiketi B'}]}]};
describe('Purchase receipt schema',()=>{
 it('accepts explicit real lot quantities and normalizes quarantine false',()=>{const data=purchaseReceiptSchema.parse(input);expect(data.items[0].lots![0].quarantined).toBe(false);});
 it('rejects lot quantities differing from the received SKU quantity',()=>expect(()=>purchaseReceiptSchema.parse({...input,items:[{...input.items[0],quantity:4}]})).toThrow());
 it('rejects duplicate SKU rows and duplicate lot numbers within a SKU',()=>{expect(()=>purchaseReceiptSchema.parse({...input,items:[input.items[0],input.items[0]]})).toThrow();expect(()=>purchaseReceiptSchema.parse({...input,items:[{...input.items[0],quantity:4,lots:[input.items[0].lots[0],input.items[0].lots[0]]}]})).toThrow();});
 it('requires source references, bounded integers and only known fields',()=>{for(const data of [{...input,sourceReference:''},{...input,role:'admin'},{...input,items:[{variantId:'variant',quantity:0}]},{...input,items:[{variantId:'variant',quantity:1,unitCostMinor:1}]}])expect(()=>purchaseReceiptSchema.parse(data)).toThrow();});
 it('normalizes row and lot ordering for actor-bound idempotency hashes',()=>{const a=purchaseReceiptSchema.parse(input),b=purchaseReceiptSchema.parse({...input,items:[{...input.items[0],lots:[...input.items[0].lots].reverse()}]});expect(canonicalPurchaseReceipt(a)).toEqual(canonicalPurchaseReceipt(b));expect(a.items[0].lots![0].lotNumber).toBe('LOT-A');});
});
