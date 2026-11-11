/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/providers/stripe.ts
 * Açıklama   : Resmî Stripe SDK ile güvenli ödeme sağlayıcı adaptörü.
 */
import Stripe from 'stripe';
import type {Currency} from '../../shared/contracts';
import type {PaymentProvider,VerifiedPayment} from './contracts';
import {HttpError} from '../security';
type Config={secretKey:string;webhookSecret:string;appEnv:string;businessApproved:boolean};
const supported=new Set(['TRY','EUR','USD','GBP']);
export class StripePaymentProvider implements PaymentProvider {
  readonly name='stripe';private client:Stripe;
  constructor(private config:Config){
    if(!config.secretKey||!config.webhookSecret)throw new HttpError(503,'Stripe güvenli bağlantı ayarları eksik.');
    if(config.appEnv==='production'&&(!config.businessApproved||!config.secretKey.startsWith('sk_live_')))throw new HttpError(503,'Stripe işletme ve kategori kabulü bekleniyor.');
    if(config.appEnv!=='production'&&!config.secretKey.startsWith('sk_test_'))throw new HttpError(503,'Test ortamında yalnız Stripe test anahtarı kullanılabilir.');
    this.client=new Stripe(config.secretKey,{maxNetworkRetries:2,timeout:12000});
  }
  async createSession(input:Parameters<PaymentProvider['createSession']>[0]){
    if(!supported.has(input.currency)||!Number.isSafeInteger(input.totalMinor)||input.totalMinor<=0)throw new HttpError(400,'Bu tutar veya para birimi desteklenmiyor.');
    const session=await this.client.checkout.sessions.create({mode:'payment',client_reference_id:input.orderId,metadata:{orderId:input.orderId},payment_intent_data:{metadata:{orderId:input.orderId}},line_items:[{quantity:1,price_data:{currency:input.currency.toLowerCase(),unit_amount:input.totalMinor,product_data:{name:`SEXSOGATE sipariş ${input.number}`}}}],success_url:input.returnUrl,cancel_url:input.cancelUrl},{idempotencyKey:input.idempotencyKey});
    if(!session.url)throw new HttpError(503,'Ödeme sayfası oluşturulamadı.');return {id:session.id,url:session.url};
  }
  verify(raw:string,signature:string):VerifiedPayment|null{
    const event=this.client.webhooks.constructEvent(raw,signature,this.config.webhookSecret,300);
    if(event.livemode!==(this.config.appEnv==='production'))throw new HttpError(400,'Ödeme olayı ortamla eşleşmiyor.');
    let status:'succeeded'|'failed';let object:Stripe.Checkout.Session;
    if(['checkout.session.completed','checkout.session.async_payment_succeeded'].includes(event.type)){
      object=event.data.object as Stripe.Checkout.Session;if(object.payment_status!=='paid')return null;status='succeeded';
    }else if(['checkout.session.async_payment_failed','checkout.session.expired'].includes(event.type)){object=event.data.object as Stripe.Checkout.Session;status='failed';}
    else return null; // Disputes/refunds are durably recorded separately by the receiver.
    const currency=object.currency?.toUpperCase();const orderId=object.metadata?.orderId;
    if(!currency||!supported.has(currency)||!orderId||!Number.isSafeInteger(object.amount_total)||Number(object.amount_total)<0)throw new HttpError(400,'Ödeme olayı sipariş alanları eksik.');
    return {eventId:event.id,orderId,status,amountMinor:object.amount_total!,currency:currency as Currency,timestamp:event.created,providerReference:object.id};
  }
  async query(reference:string){const session=await this.client.checkout.sessions.retrieve(reference);const currency=session.currency?.toUpperCase();if(!currency||!supported.has(currency))throw new HttpError(503,'Ödeme para birimi doğrulanamadı.');return {status:session.payment_status==='paid'?'succeeded' as const:session.status==='expired'?'failed' as const:'pending' as const,amountMinor:session.amount_total??0,currency:currency as Currency};}
  async refund(reference:string,amountMinor:number,idempotencyKey:string){
    if(!Number.isSafeInteger(amountMinor)||amountMinor<=0)throw new HttpError(400,'İade tutarı geçersiz.');
    const session=await this.client.checkout.sessions.retrieve(reference);const paymentIntent=typeof session.payment_intent==='string'?session.payment_intent:session.payment_intent?.id;if(!paymentIntent)throw new HttpError(409,'Tahsilat kaydı henüz doğrulanmadı.');
    const result=await this.client.refunds.create({payment_intent:paymentIntent,amount:amountMinor,metadata:{sexsogate_refund_key:idempotencyKey}},{idempotencyKey});
    if(result.amount!==amountMinor||result.currency!==session.currency)throw new HttpError(409,'Sağlayıcı iade tutarı veya para birimi eşleşmiyor.');
    return {reference:result.id,status:result.status??'pending'};
  }
  async queryRefund(reference:string){const result=await this.client.refunds.retrieve(reference);const currency=result.currency.toUpperCase();if(!supported.has(currency))throw new HttpError(409,'İade para birimi desteklenmiyor.');return {reference:result.id,amountMinor:result.amount,currency:currency as Currency,status:result.status==='succeeded'?'succeeded' as const:['failed','canceled'].includes(result.status??'')?'failed' as const:'pending' as const};}
  async findRefund(sessionReference:string,refundKey:string){
    const session=await this.client.checkout.sessions.retrieve(sessionReference);const intent=typeof session.payment_intent==='string'?session.payment_intent:session.payment_intent?.id;if(!intent)return null;
    const refunds=await this.client.refunds.list({payment_intent:intent,limit:100});const found=refunds.data.find(refund=>refund.metadata?.sexsogate_refund_key===refundKey);
    return found?this.queryRefund(found.id):null;
  }
  async resumeSession(reference:string){const session=await this.client.checkout.sessions.retrieve(reference);const currency=session.currency?.toUpperCase();if(!currency||!supported.has(currency))throw new HttpError(409,'Ödeme para birimi eşleşmiyor.');return {id:session.id,orderId:session.metadata?.orderId??'',url:session.status==='open'?session.url:null,status:session.status,paymentStatus:session.payment_status,amountMinor:session.amount_total??0,currency:currency as Currency,created:session.created};}
  verifyEvent(raw:string,signature:string){return this.client.webhooks.constructEvent(raw,signature,this.config.webhookSecret,300);}
}
export function stripeProvider(){return new StripePaymentProvider({secretKey:process.env.STRIPE_SECRET_KEY??'',webhookSecret:process.env.STRIPE_WEBHOOK_SECRET??'',appEnv:process.env.APP_ENV??'development',businessApproved:process.env.STRIPE_BUSINESS_APPROVED==='true'});}
