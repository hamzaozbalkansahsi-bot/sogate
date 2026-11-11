/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/providers/contracts.ts
 * Açıklama   : Modüller arasında paylaşılan veri sözleşmeleri.
 */
import type {Currency} from '../../shared/contracts';
export interface VerifiedPayment {eventId:string;orderId:string;status:'succeeded'|'failed';amountMinor:number;currency:Currency;timestamp:number;providerReference?:string;}
export interface PaymentSession {id:string;url:string;}
export interface PaymentProvider {
 readonly name:string;
 createSession(input:{orderId:string;number:string;totalMinor:number;currency:Currency;idempotencyKey:string;returnUrl:string;cancelUrl:string}):Promise<PaymentSession>;
 verify(raw:string,signature:string):VerifiedPayment|null;
 query(reference:string):Promise<{status:'pending'|'succeeded'|'failed';amountMinor:number;currency:Currency}>;
 refund(reference:string,amountMinor:number,idempotencyKey:string):Promise<{reference:string;status:string}>;
}
export interface ShippingProvider {readonly name:string;readonly automatedLabels:boolean;track(carrier:string,trackingNumber:string):Promise<{status:string;source:string}>;}
export interface InvoiceProvider {readonly name:string;registerExternalReference(input:{orderId:string;reference:string;sellerVerified:boolean}):Promise<{reference:string}>;}
export interface StorageReadOptions {maxBytes?:number;timeoutMs?:number;}
export interface StorageProvider {put(key:string,data:Buffer,contentType:string):Promise<void>;get(key:string,options?:StorageReadOptions):Promise<Buffer>;}
export interface MarketplaceProvider {readonly channel:string;readonly enabled:boolean;publishSku():Promise<never>;}
