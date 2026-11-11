/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/purchase-receipts.ts
 * Açıklama   : Lotlu satın alma kabulünün sınırlı girdi ve maliyetsiz kaynak sözleşmesini tanımlar.
 */
import {z} from 'zod';
const text=z.string().trim().min(1).max(300),reference=z.string().trim().min(5).max(1000),quantity=z.number().int().min(1).max(1000000);
export const purchaseReceiptLotSchema=z.object({lotNumber:text,expiresAt:z.iso.date().nullable().default(null),quantity,quarantined:z.boolean().default(false),sourceReference:reference}).strict();
export const purchaseReceiptSchema=z.object({action:z.literal('receive'),id:text,idempotencyKey:z.string().min(16).max(128),items:z.array(z.object({variantId:text,quantity,lots:z.array(purchaseReceiptLotSchema).min(1).max(50).optional()}).strict()).min(1).max(100),reason:z.string().trim().min(5).max(500),sourceReference:reference}).strict().superRefine((data,context)=>{
 if(new Set(data.items.map(row=>row.variantId)).size!==data.items.length)context.addIssue({code:'custom',message:'Aynı stok kodu bir kez seçilmelidir.'});
 let lotCount=0;
 for(const row of data.items)if(row.lots){lotCount+=row.lots.length;if(new Set(row.lots.map(lot=>lot.lotNumber)).size!==row.lots.length)context.addIssue({code:'custom',message:'Aynı SKU lotu bir kabul satırında yinelenemez.'});if(row.lots.reduce((sum,lot)=>sum+lot.quantity,0)!==row.quantity)context.addIssue({code:'custom',message:'Lot adetleri toplamı kabul adediyle aynı olmalıdır.'});}
 if(lotCount>200)context.addIssue({code:'custom',message:'Bir kabulde en fazla 200 lot satırı kullanılabilir.'});
});
export type PurchaseReceiptInput=z.infer<typeof purchaseReceiptSchema>;
export type PurchaseReceiptLotInput=z.infer<typeof purchaseReceiptLotSchema>;
const receiptId=z.string().trim().min(1).max(300),receiptStatus=z.enum(['received','partially_received']);
export const purchaseReceiptResultSchema=z.union([
 z.object({id:receiptId,status:receiptStatus,duplicate:z.literal(false).optional()}).strict(),
 z.object({id:receiptId,duplicate:z.literal(true),status:receiptStatus.optional()}).strict()
]);
export type PurchaseReceiptResult=z.infer<typeof purchaseReceiptResultSchema>;
export interface PurchaseLotSource{id:string;kind:'purchase'|'direct';purchaseId:string|null;receiptId:string|null;supplierName:string|null;lotId:string;variantId:string;quantity:number;quarantineQuantity:number;sourceReference:string|null;receiptSourceReference:string|null;receivedAt:string;}
export interface PurchaseLotSources{rows:PurchaseLotSource[];total:number;page:number;pageSize:25;}
export function canonicalPurchaseReceipt(input:PurchaseReceiptInput):PurchaseReceiptInput{
 return {...input,items:[...input.items].sort((a,b)=>a.variantId<b.variantId?-1:a.variantId>b.variantId?1:0).map(row=>({...row,...(row.lots?{lots:[...row.lots].sort((a,b)=>a.lotNumber<b.lotNumber?-1:a.lotNumber>b.lotNumber?1:0)}:{})}))};
}
