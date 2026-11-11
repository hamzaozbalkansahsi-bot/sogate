/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/providers/operations.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import type {ShippingProvider,InvoiceProvider,MarketplaceProvider} from './contracts';
import {HttpError} from '../security';
export class ManualShipping implements ShippingProvider {readonly name='manual';readonly automatedLabels=false;async track(carrier:string,trackingNumber:string){if(!carrier.trim()||!trackingNumber.trim())throw new HttpError(400,'Gerçek taşıyıcı ve takip numarası gerekir.');return {status:'manual_reference',source:'Taşıyıcıdan otomatik sorgulama bağlı değil'};}}
export class ExternalInvoice implements InvoiceProvider {readonly name='external-reference';async registerExternalReference(input:{orderId:string;reference:string;sellerVerified:boolean}){if(!input.sellerVerified||!input.reference.trim())throw new HttpError(409,'Doğrulanmış satıcı ve dış sistem belge referansı gerekir.');return {reference:input.reference};}}
export class BlockedMarketplace implements MarketplaceProvider {readonly enabled=false;constructor(readonly channel:string){}async publishSku():Promise<never>{throw new HttpError(503,'Kanal kategori kabulü ve API erişimi henüz doğrulanmadı.');}}
