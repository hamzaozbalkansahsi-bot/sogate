/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/orders.ts
 * Açıklama   : Sipariş, rezervasyon ve doğrulanmış ödeme durum geçişleri.
 */
import { createHmac, randomUUID } from "node:crypto";
import { z } from "zod";
import {addressValueSchema} from "../../shared/address-fields";
import {validateCountryAddress} from "../address-profiles";
import {assertSkuCountryEligibility as assertCountryEligibility} from "../compliance";
import { query, transaction, type Connection } from "../db";
import type { CheckoutInput, CheckoutResult, Currency, OrderSummary } from "../../shared/contracts";
import { assertCartOwner,lockCallerCart,tokenHash } from "./catalog";
import { assertTestEnvironment, DomainError, requireCondition, signPayment, validatePaymentEnvelope, type PaymentEvent } from "./rules";
import {evaluateCheckoutPricing,pricingQuoteBinding} from './checkout-pricing';
import {verifyQuoteToken} from './quote-token';
import {trackedAvailable,reserveLots,paymentLotsAvailable,consumeReservationLots} from './lots';

const checkoutSchema=addressValueSchema.extend({quoteToken:z.string().max(2048).default(''),email:z.email().max(254),locale:z.enum(["tr","en"]),currency:z.enum(["TRY","EUR","USD","GBP"]),idempotencyKey:z.string().min(16).max(128),privacyAccepted:z.literal(true),termsAccepted:z.literal(true),couponCode:z.string().trim().min(1).max(60).optional()}).strict();
function parseCheckout(input:unknown):CheckoutInput&{couponCode?:string} {const parsed=checkoutSchema.safeParse(input);requireCondition(parsed.success,"INVALID_CHECKOUT","Adres ve onay alanlarını kontrol edin.");return parsed.data;}
function trackingToken(cartToken:string,idempotencyKey:string) {
 const secret=process.env.BETTER_AUTH_SECRET;
 requireCondition(secret&&secret.length>=32,"SECRET_NOT_CONFIGURED","Güvenli sipariş bağlantısı yapılandırılmadı.",503);
 return createHmac("sha256",secret).update(`tracking:${cartToken}:${idempotencyKey}`).digest("hex");
}
export async function assertLiveReady(connection?:Connection) {
 if(process.env.APP_ENV==="development"||process.env.APP_ENV==="test")return;
 requireCondition(process.env.APP_ENV==="production"&&process.env.LIVE_SALES_ENABLED==="true","LIVE_SALES_CLOSED","Satış hazırlığı tamamlanmadığı için ödeme kapalıdır.",503);
 requireCondition(process.env.PAYMENT_PROVIDER&&process.env.PAYMENT_PROVIDER!=="test","TEST_PROVIDER_DISABLED","Gerçek ödeme sağlayıcısı yapılandırılmalıdır.",503);
 const rows=await query("SELECT key,value FROM settings",[],connection);const settings=new Map(rows.map(r=>[r.key,r.value]));
 for(const key of ["seller.name","seller.taxNumber","seller.address","seller.supportEmail","seller.phone","seller.bankAccount"])requireCondition(typeof settings.get(key)==="string"&&String(settings.get(key)).trim(),"SELLER_NOT_CONFIGURED","Satıcı bilgileri tamamlanmadı.",503);
 for(const key of ["launch.backupVerified","launch.securityReviewed","launch.legalApproved","launch.catalogVerified","launch.providerApproved"])requireCondition(settings.get(key)===true,"LAUNCH_NOT_APPROVED","Canlı satış onayları tamamlanmadı.",503);
 const {assertPrivacyLaunchReady}=await import('../privacy');await assertPrivacyLaunchReady(connection);
}
async function enqueue(type:string,payload:Record<string,unknown>,key:string,connection:Connection) {await query("INSERT INTO jobs(type,payload,dedupe_key) VALUES($1,$2,$3) ON CONFLICT(dedupe_key) DO NOTHING",[type,JSON.stringify(payload),key],connection);}
export async function checkout(token:string,untrustedInput:CheckoutInput&{couponCode?:string},callerUserId:string|null=null):Promise<CheckoutResult> {
 const input=parseCheckout(untrustedInput);
 const {quoteToken,...semanticInput}=input;
 const requestHash=tokenHash(JSON.stringify(semanticInput));
 const track=trackingToken(token,input.idempotencyKey);
 const order=await transaction(async connection=>{
  await assertLiveReady(connection);
  const cart=await lockCallerCart(token,callerUserId,connection);
  const existing=await query("SELECT * FROM orders WHERE cart_id=$1 AND idempotency_key=$2",[cart.id,input.idempotencyKey],connection);
  if(existing.length){assertCartOwner(existing[0],callerUserId);requireCondition(existing[0].request_hash===requestHash,"IDEMPOTENCY_CONFLICT","Aynı işlem anahtarı farklı bilgilerle kullanılamaz.",409);return existing[0];}
  requireCondition(quoteToken.length>0,'CHECKOUT_QUOTE_REQUIRED','Ödeme öncesinde güncel sipariş toplamını inceleyin.',409);
  const pending=await query("SELECT id FROM orders WHERE cart_id=$1 AND status='awaiting_payment' AND expires_at>now()",[cart.id],connection);
  requireCondition(!pending.length,"PAYMENT_ALREADY_PENDING","Bu sepet için devam eden bir ödeme var. Güvenli sipariş bağlantınızdan devam edin.",409);
  const pricing=await evaluateCheckoutPricing(cart.id,input,connection,true);
  const {country,items,allComponents,stock,taxRules,agreements,productTaxes,costMinor,coupon,shippingTaxRule,totals}=pricing;
  const {fullName,phone,line1,city,region,district,postalCode,country:deliveryCountry}=input;
  const delivery=await validateCountryAddress({fullName,phone,line1,city,region,district,postalCode,country:deliveryCountry},connection,input.locale);
  for(const item of items){await assertCountryEligibility(item.id,input.country,connection);for(const part of allComponents.filter(row=>row.bundle_variant_id===item.id))await assertCountryEligibility(part.component_variant_id,input.country,connection);}
  // Lock all component rows in stable order before calculating available stock.
  const ids=[...stock.keys()].sort();
  const balances=await query("SELECT * FROM inventory_balance WHERE variant_id=ANY($1::text[]) AND warehouse_id='main' ORDER BY variant_id FOR UPDATE",[ids],connection);
  requireCondition(balances.length===ids.length,"INSUFFICIENT_STOCK","Sepetteki bir ürünün depo stoğu yok.",409);
  for(const [id,quantity]of stock) {
   const balance=balances.find(b=>b.variant_id===id);
   const [held]=await query("SELECT coalesce(sum(quantity),0)::int qty FROM reservations WHERE variant_id=$1 AND warehouse_id='main' AND status='active' AND expires_at>now()",[id],connection);
   requireCondition(balance&&balance.on_hand-balance.safety_stock-held.qty>=quantity,"INSUFFICIENT_STOCK","Sevkiyat deposunda yeterli stok kalmadı.",409);
   const lotStock=await trackedAvailable(id,'main',connection);requireCondition(lotStock===null||lotStock>=quantity,'LOT_STOCK_UNAVAILABLE','Uygun son kullanma tarihli lot stoğu kalmadı.',409);
  }
  const acceptedQuote=verifyQuoteToken(quoteToken,pricingQuoteBinding(cart.id,tokenHash(token),input,pricing));
  const address={...delivery.values,profileVersion:delivery.profileVersion};
  const commonTaxRule=taxRules.size===1?[...taxRules.values()][0]:null;
  const snapshot={checkoutQuote:{version:acceptedQuote.version,issuedAt:acceptedQuote.issuedAt,expiresAt:acceptedQuote.expiresAt,evaluationHash:acceptedQuote.evaluationHash},taxRuleId:commonTaxRule?.id??null,taxBps:commonTaxRule?.rateBps??null,goodsTaxMinor:totals.goodsTaxMinor,productTaxRules:items.map(item=>({variantId:item.id,...item.tax_rule})),taxPriceBasis:'inclusive',deliveryTerm:country.delivery_term,shippingTaxRule,shippingTaxMinor:totals.shippingTaxMinor,priceSource:"fixed-price-list",currency:input.currency,commissionRule:null,coupon:coupon?{id:coupon.id,discountBps:coupon.discount_bps}:null};
  const rows=await query(`INSERT INTO orders(cart_id,user_id,idempotency_key,request_hash,tracking_hash,currency,subtotal_minor,discount_minor,shipping_minor,tax_minor,total_minor,cost_minor,email,address,locale,snapshot,address_profile_id,expires_at)
   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,now()+interval '15 minutes') RETURNING *`,[cart.id,cart.user_id,input.idempotencyKey,requestHash,tokenHash(track),input.currency,totals.subtotalMinor,totals.discountMinor,totals.shippingMinor,totals.taxMinor,totals.totalMinor,costMinor,input.email,JSON.stringify(address),input.locale,JSON.stringify(snapshot),delivery.profileId],connection);
  const order=rows[0];
  for(const [i,item]of items.entries()){
   const allocation=productTaxes.lines[i];
   await query("INSERT INTO order_items(order_id,variant_id,name,sku,quantity,unit_minor,cost_minor,tax_minor,discount_minor,snapshot) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",[order.id,item.id,item.product_name,item.sku,item.quantity,item.price_minor,item.cost_minor,allocation.taxMinor,allocation.discountMinor,JSON.stringify({name:item.product_name,variantName:item.variant_display_name,locale:input.locale,description:item.description,image:item.image,material:item.material,warnings:item.warnings,care:item.care,manufacturer:item.manufacturer,priceMinor:item.price_minor,taxClass:item.tax_rule.productClass,taxRuleId:item.tax_rule.id,taxBps:item.tax_rule.rateBps,taxPriceBasis:'inclusive',taxSource:item.tax_rule.source,taxValidFrom:item.tax_rule.validFrom,taxValidUntil:item.tax_rule.validUntil,lineGrossMinor:allocation.grossMinor,lineDiscountMinor:allocation.discountMinor,lineTaxMinor:allocation.taxMinor,lineNetMinor:allocation.netMinor,bundleComponents:item.bundle_components})],connection);
  }
  if(coupon)await query("INSERT INTO coupon_usage(coupon_id,order_id) VALUES($1,$2)",[coupon.id,order.id],connection);
  for(const [variantId,quantity]of stock){const [reservation]=await query("INSERT INTO reservations(order_id,variant_id,warehouse_id,quantity,expires_at) VALUES($1,$2,'main',$3,$4) RETURNING id",[order.id,variantId,quantity,order.expires_at],connection);await reserveLots(reservation.id,variantId,quantity,'main',connection);}
  await query("INSERT INTO payments(order_id,provider,amount_minor,currency) VALUES($1,$2,$3,$4)",[order.id,process.env.PAYMENT_PROVIDER??"unconfigured",totals.totalMinor,input.currency],connection);
  for(const a of agreements)await query("INSERT INTO order_agreements(order_id,document_id,kind,version,locale,title,body,body_hash,accepted_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,now())",[order.id,a.id,a.kind,a.version,a.locale,a.title,a.body,a.body_hash],connection);
  await query("INSERT INTO order_history(order_id,type,to_status) VALUES($1,'order','awaiting_payment')",[order.id],connection);
  await enqueue("reservation.expire",{orderId:order.id},`reservation:${order.id}`,connection);
  await query("UPDATE jobs SET available_at=$2 WHERE dedupe_key=$1",[`reservation:${order.id}`,order.expires_at],connection);
  return order;
 });
 return {orderId:order.id,number:order.number,totalMinor:Number(order.total_minor),currency:order.currency as Currency,trackingToken:track,paymentUrl:process.env.PAYMENT_PROVIDER==="test"?`/odeme/test?order=${encodeURIComponent(order.id)}&token=${encodeURIComponent(track)}`:"",};
}
export async function getOrder(id:string,tracking:string|null,userId?:string):Promise<OrderSummary|null> {
 const rows=await query("SELECT * FROM orders WHERE id=$1 AND(($2::text IS NOT NULL AND tracking_hash=$2) OR($3::text IS NOT NULL AND user_id=$3))",[id,tracking?tokenHash(tracking):null,userId??null]);
 if(!rows.length)return null;const order=rows[0];
 const items=await query("SELECT name,sku,quantity,unit_minor,variant_id FROM order_items WHERE order_id=$1 ORDER BY id",[id]);
 const shipments=await query("SELECT carrier,tracking_number,status FROM shipments WHERE order_id=$1 ORDER BY created_at",[id]);
 return {id:order.id,number:order.number,status:order.status,paymentStatus:order.payment_status,fulfillmentStatus:order.fulfillment_status,currency:order.currency,subtotalMinor:Number(order.subtotal_minor),shippingMinor:Number(order.shipping_minor),taxMinor:Number(order.tax_minor),discountMinor:Number(order.discount_minor),totalMinor:Number(order.total_minor),createdAt:order.created_at.toISOString(),items:items.map(i=>({variantId:i.variant_id,name:i.name,sku:i.sku,quantity:i.quantity,unitMinor:Number(i.unit_minor)})),shipments:shipments.map(s=>({carrier:s.carrier,trackingNumber:s.tracking_number,status:s.status}))};
}
export async function createTestPaymentEvent(orderId:string,tracking:string,outcome:"succeeded"|"failed") {
 assertTestEnvironment();requireCondition(process.env.PAYMENT_PROVIDER==="test","TEST_PROVIDER_DISABLED","Test ödeme sağlayıcısı etkin değil.",503);
 const order=await getOrder(orderId,tracking);requireCondition(order,"ORDER_NOT_FOUND","Sipariş bulunamadı.",404);
 const event:PaymentEvent={id:`test-${randomUUID()}`,orderId,amountMinor:order.totalMinor,currency:order.currency,status:outcome,timestamp:Math.floor(Date.now()/1000)};
 const raw=JSON.stringify(event);const secret=process.env.PAYMENT_WEBHOOK_SECRET;
 requireCondition(secret&&secret.length>=32,"PAYMENT_NOT_CONFIGURED","Ödeme bildirim anahtarı yapılandırılmadı.",503);
 return {raw,signature:signPayment(raw,secret)};
}
export async function handlePayment(raw:string,signature:string) {
 assertTestEnvironment();requireCondition(process.env.PAYMENT_PROVIDER==="test","TEST_PROVIDER_DISABLED","Test ödeme sağlayıcısı etkin değil.",503);
 const event=validatePaymentEnvelope(raw,signature,process.env.PAYMENT_WEBHOOK_SECRET??"");
 return settleVerifiedPayment(event,"test",tokenHash(raw));
}
export interface VerifiedPayment {eventId:string;orderId:string;status:"succeeded"|"failed";amountMinor:number;currency:Currency;timestamp:number;providerReference?:string;}
/** Caller must validate the provider's official signature against the untouched raw body. */
export async function settleVerifiedPayment(input:VerifiedPayment|PaymentEvent,provider:string,payloadHash?:string):Promise<{duplicate:boolean}> {
 const providerReference="providerReference" in input?input.providerReference:undefined;
 const event:PaymentEvent="eventId" in input?{id:input.eventId,orderId:input.orderId,status:input.status,amountMinor:input.amountMinor,currency:input.currency,timestamp:input.timestamp}:input;
 const hash=payloadHash??tokenHash(JSON.stringify(input));
 return transaction(async connection=>{
  const orders=await query("SELECT * FROM orders WHERE id=$1 FOR UPDATE",[event.orderId],connection);
  requireCondition(orders.length,"ORDER_NOT_FOUND","Ödeme siparişi bulunamadı.",404);const order=orders[0];
  const payments=await query("SELECT * FROM payments WHERE order_id=$1 FOR UPDATE",[order.id],connection);const payment=payments[0];
  requireCondition(payment&&payment.provider===provider,"PROVIDER_MISMATCH","Ödeme sağlayıcısı siparişle eşleşmiyor.",409);
  if(provider!=="test")requireCondition(providerReference&&(!payment.provider_reference||payment.provider_reference===providerReference),"PAYMENT_REFERENCE_MISMATCH","Ödeme oturumu siparişle eşleşmiyor.",409);
  requireCondition(Number(payment.amount_minor)===event.amountMinor&&payment.currency===event.currency,"PAYMENT_MISMATCH","Ödeme tutarı veya para birimi siparişle eşleşmiyor.",409);
  const previous=await query("SELECT payload_hash FROM payment_events WHERE id=$1",[event.id],connection);
  if(previous.length){requireCondition(previous[0].payload_hash===hash,"EVENT_CONFLICT","Aynı ödeme olayı farklı içerikle kullanılamaz.",409);return {duplicate:true};}
  await query("INSERT INTO payment_events(id,payment_id,payload_hash,status) VALUES($1,$2,$3,$4)",[event.id,payment.id,hash,event.status],connection);
  if(payment.status==="succeeded"||payment.status==="partially_refunded"||payment.status==="refunded")return {duplicate:false};
  const reservations=await query<{id:string;order_id:string;variant_id:string;warehouse_id:string;quantity:number;status:string;expires_at:Date}>("SELECT * FROM reservations WHERE order_id=$1 ORDER BY variant_id FOR UPDATE",[order.id],connection);
  if(event.status==="failed") {
   await query("UPDATE reservations SET status='released' WHERE order_id=$1 AND status='active'",[order.id],connection);
   await query("UPDATE payments SET status='failed',updated_at=now() WHERE id=$1",[payment.id],connection);
   await query("UPDATE orders SET status='cancelled',payment_status='failed',updated_at=now() WHERE id=$1",[order.id],connection);
   await query("UPDATE coupon_usage SET status='released' WHERE order_id=$1 AND status='reserved'",[order.id],connection);
   await query("INSERT INTO order_history(order_id,type,from_status,to_status) VALUES($1,'payment',$2,'failed')",[order.id,payment.status],connection);
   return {duplicate:false};
  }
  const late=order.status!=="awaiting_payment"||new Date(order.expires_at).getTime()<=Date.now()||!reservations.length||reservations.some(r=>r.status!=="active"||new Date(r.expires_at).getTime()<=Date.now());
  const balances=await query("SELECT * FROM inventory_balance WHERE variant_id=ANY($1::text[]) AND warehouse_id='main' ORDER BY variant_id FOR UPDATE",[reservations.map(r=>r.variant_id)],connection);
  const balanceMap=new Map(balances.map(b=>[b.variant_id,b]));
  const lotStockAvailable=await paymentLotsAvailable(order.id,connection);
  const stockMissing=reservations.some(r=>(balanceMap.get(r.variant_id)?.on_hand??0)<r.quantity)||!lotStockAvailable;
  await query("UPDATE payments SET status='succeeded',provider_reference=coalesce(provider_reference,$2),updated_at=now() WHERE id=$1",[payment.id,providerReference??null],connection);
  if(late||stockMissing) {
   await query("UPDATE reservations SET status='released' WHERE order_id=$1 AND status='active'",[order.id],connection);
   await query("UPDATE orders SET status='payment_exception',payment_status='succeeded',updated_at=now() WHERE id=$1",[order.id],connection);
   await query("UPDATE coupon_usage SET status='released' WHERE order_id=$1 AND status='reserved'",[order.id],connection);
   await query("INSERT INTO order_history(order_id,type,from_status,to_status,details) VALUES($1,'payment',$2,'payment_exception',$3)",[order.id,order.status,JSON.stringify({reason:late?"reservation_expired":!lotStockAvailable?"lot_unavailable":"stock_missing"})],connection);
   await enqueue("payment.exception",{orderId:order.id},`exception:${order.id}`,connection);
   return {duplicate:false};
  }
  for(const reservation of reservations) {
   const updated=await query("UPDATE inventory_balance SET on_hand=on_hand-$2 WHERE variant_id=$1 AND warehouse_id=$3 AND on_hand>=$2 RETURNING variant_id",[reservation.variant_id,reservation.quantity,reservation.warehouse_id],connection);
   requireCondition(updated.length,"STOCK_CONFLICT","Ödeme stoğu ayrıştırılamadı.",409);
   const tracked=await consumeReservationLots(reservation,connection);
   if(!tracked)await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference) VALUES($1,$2,'sale',$3,'Doğrulanmış ödeme',$4)",[reservation.variant_id,reservation.warehouse_id,-reservation.quantity,`payment:${order.id}:${reservation.variant_id}`],connection);
  }
  await query("UPDATE reservations SET status='consumed' WHERE order_id=$1 AND status='active'",[order.id],connection);
  await query("UPDATE orders SET status='confirmed',payment_status='succeeded',updated_at=now() WHERE id=$1",[order.id],connection);
  const couponUsage=await query("UPDATE coupon_usage SET status='consumed' WHERE order_id=$1 AND status='reserved' RETURNING coupon_id",[order.id],connection);
  if(couponUsage.length)await query("UPDATE coupons SET used_count=used_count+1 WHERE id=$1",[couponUsage[0].coupon_id],connection);
  await query("DELETE FROM cart_items WHERE cart_id=$1",[order.cart_id],connection);
  await query("INSERT INTO order_history(order_id,type,from_status,to_status) VALUES($1,'payment',$2,'succeeded')",[order.id,payment.status],connection);
  await enqueue("order.confirmation",{orderId:order.id},`confirmation:${order.id}`,connection);
  return {duplicate:false};
 });
}
export async function expireReservations():Promise<number> {
 return transaction(async connection=>{
  const orders=await query("SELECT id FROM orders WHERE status='awaiting_payment' AND expires_at<=now() ORDER BY id FOR UPDATE SKIP LOCKED",[],connection);
  for(const order of orders) {
   await query("UPDATE reservations SET status='expired' WHERE order_id=$1 AND status='active'",[order.id],connection);
   await query("UPDATE orders SET status='cancelled',updated_at=now() WHERE id=$1",[order.id],connection);
   await query("UPDATE coupon_usage SET status='released' WHERE order_id=$1 AND status='reserved'",[order.id],connection);
   await query("INSERT INTO order_history(order_id,type,from_status,to_status,details) VALUES($1,'order','awaiting_payment','cancelled','{\"reason\":\"reservation_expired\"}')",[order.id],connection);
  }
  return orders.length;
 });
}
export async function setPaymentReference(orderId:string,provider:string,reference:string) {
 await query("UPDATE payments SET provider_reference=$3 WHERE order_id=$1 AND provider=$2 AND status='pending'",[orderId,provider,reference]);
}
export { DomainError };
