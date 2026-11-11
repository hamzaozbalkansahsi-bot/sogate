/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/shipping-tax-integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import pg from 'pg';
import {randomBytes,createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {migrate} from './migrate';
import {seedFixtureAddressProfile} from './seed';
const original=new URL(process.env.TEST_DATABASE_URL??'');if(!['127.0.0.1','localhost'].includes(original.hostname)||!original.pathname.endsWith('_test'))throw new Error('Yalnız yerel test veritabanı.');
const name=`sexsogate_${randomBytes(6).toString('hex')}_shipping_test`;assert.match(name,/^sexsogate_[a-f0-9]{12}_shipping_test$/);const controlUrl=new URL(original);controlUrl.pathname='/postgres';const control=new pg.Client({connectionString:controlUrl.href});await control.connect();
let pool:pg.Pool|undefined;let created=false;
try{
 await control.query(`CREATE DATABASE "${name}" ENCODING 'UTF8' TEMPLATE template0`);created=true;original.pathname='/'+name;process.env.DATABASE_URL=original.href;process.env.APP_ENV='test';await migrate(original.href);
 const database=await import('../src/server/db');pool=database.pool;const {resolveShippingTaxRule,manageTax,applyShippingTax}=await import('../src/server/shipping-tax');
 await pool.query("INSERT INTO country_rules(code,name) VALUES('TR','Türkiye'),('GB','Birleşik Krallık')");
 await assert.rejects(()=>resolveShippingTaxRule('TR',false),/vergi/);
 const principal={id:'tax-test',role:'finance' as const,mfa:true};
 await assert.rejects(()=>manageTax({kind:'shipping',country:'TR',rateBps:2000,reference:'Yerel vergi kontrol kaynağı'}, {id:'warehouse',role:'warehouse',mfa:true}));
 await manageTax({kind:'shipping',country:'TR',rateBps:2000,reference:'Yalnız izole vergi kontrol kaynağı',effectiveFrom:'2026-01-01T00:00:00Z'},principal);
 const rule=await resolveShippingTaxRule('TR',false);assert.equal(rule.rateBps,2000);
 const result=applyShippingTax({subtotalMinor:10000,discountMinor:0,shippingMinor:1200,taxMinor:1667,totalMinor:11200},rule);assert.equal(result.taxMinor,1867);assert.equal(result.goodsTaxMinor,1667);assert.equal(result.shippingTaxMinor,200);assert.equal(result.totalMinor,11200);
 await manageTax({kind:'shipping',country:'GB',rateBps:1000,reference:'Yalnız gelecekteki test kuralı',effectiveFrom:'2099-01-01T00:00:00Z'},principal);
 await assert.rejects(()=>resolveShippingTaxRule('GB',false));
 const fixture=await resolveShippingTaxRule('GB',true);assert.equal(fixture.rateBps,0);
 const core=await import('../src/server/commerce');const query=database.query;const {complianceAction}=await import('../src/server/compliance');
 const admin={id:'mixed-tax-admin',role:'admin' as const,mfa:true};
 process.env.PAYMENT_PROVIDER='test';process.env.PAYMENT_WEBHOOK_SECRET=randomBytes(32).toString('hex');
 await query("UPDATE country_rules SET enabled=true,product_approved=true,age_approved=true,payment_approved=true,shipping_approved=true,tax_approved=true,legal_approved=true,shipping_minor=1200,currency='TRY',fixture=true WHERE code='TR'");
 await seedFixtureAddressProfile(pool);
 await query("INSERT INTO warehouses(id,name) VALUES('main','Ana Depo')");
 for(const kind of ['privacy','terms']){const body='Yalnız izole vergi testi sözleşmesi. Güvenli Alışveriş.';await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture) VALUES($1,'tr',$1,$2,1,'effective',$3,now(),true)",[kind,body,createHash('sha256').update(body).digest('hex')]);}
 for(const [productClass,rateBps]of [['*',0],['textile-20',2000],['accessory-10',1000]] as const)await manageTax({kind:'product',country:'TR',productClass,rateBps,reference:'Yalnız izole sınıf kaynağı '+productClass,effectiveFrom:'2026-01-01T00:00:00Z'},admin);
 async function product(suffix:string,priceMinor:number,taxClass:string){
  const p=await core.adminAction('products',{name:'Vergi testi '+suffix,nameEn:'Tax test '+suffix,slug:'tax-'+suffix,category:'aksesuarlar',brand:'',description:'İzole sınıf vergi senaryosu.',descriptionEn:'Isolated tax class scenario.',sku:'TAX-'+suffix,variantName:'Bordo',variantNameEn:'Burgundy',priceMinor,costMinor:1000,material:'Tekstil',image:'/media/atelier-01.svg',warnings:'Yalnız yetişkinler için.',warningsEn:'For adults only.',care:'Bakım etiketini izleyin.',careEn:'Follow the care label.'},admin) as {id:string,variantId:string};
  await query('UPDATE variants SET tax_class=$2 WHERE id=$1',[p.variantId,taxClass]);
  await core.adminAction('inventory',{variantId:p.variantId,quantity:20,reason:'İzole vergi testi stoğu'},admin);
  await complianceAction({action:'eligibility',variantId:p.variantId,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole karma vergi testi ülke onayı',idempotencyKey:randomBytes(32).toString('hex')},admin);
  await core.adminAction('products',{action:'publish',id:p.id,country:'TR',reviewNote:'Yalnız izole vergi testi incelemesi'},admin);return p;
 }
 const a=await product('a',12001,'textile-20'),b=await product('b',11003,'accessory-10');
 const token=()=>randomBytes(32).toString('hex');
 const checkoutInput=()=>({email:'tax@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme İç Giyim Ölçü ve Özellikler',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr' as const,currency:'TRY' as const,idempotencyKey:token(),privacyAccepted:true,termsAccepted:true});
 await core.adminAction('campaigns',{action:'create',code:'TAX-17',discountBps:1700,minimumMinor:1,maxUses:20,minimumContributionMinor:0,expiresAt:new Date(Date.now()+86400000).toISOString(),active:true},admin);
 const cart=token();await core.setCartItem(cart,a.variantId,3);await core.setCartItem(cart,b.variantId,2);
 const quote=await core.quoteCheckout(cart,{country:'TR',currency:'TRY',locale:'tr',couponCode:'TAX-17'});const order=await core.checkout(cart,{...checkoutInput(),couponCode:'TAX-17',quoteToken:quote.quoteToken});
 const [saved]=await query('SELECT subtotal_minor,discount_minor,shipping_minor,tax_minor,total_minor,snapshot FROM orders WHERE id=$1',[order.orderId]);
 assert.equal(saved.subtotal_minor,58009);assert.equal(saved.discount_minor,9862);assert.equal(saved.shipping_minor,1200);assert.equal(saved.total_minor,49347);
 assert.equal(saved.tax_minor,6840);assert.equal(saved.snapshot.goodsTaxMinor,6640);assert.equal(saved.snapshot.shippingTaxMinor,200);
 const lines=await query('SELECT variant_id,unit_minor,discount_minor,tax_minor,snapshot FROM order_items WHERE order_id=$1',[order.orderId]);
 const lineA=lines.find(l=>l.variant_id===a.variantId)!,lineB=lines.find(l=>l.variant_id===b.variantId)!;
 assert.equal(lineA.unit_minor,12001);assert.equal(lineB.unit_minor,11003);
 assert.equal(lineA.discount_minor,6121);assert.equal(lineB.discount_minor,3741);assert.equal(lineA.tax_minor,4980);assert.equal(lineB.tax_minor,1660);
 assert.equal(lineA.snapshot.taxClass,'textile-20');assert.equal(lineB.snapshot.taxClass,'accessory-10');
 assert.equal(lineA.snapshot.taxBps,2000);assert.equal(lineB.snapshot.taxBps,1000);
 assert(lineA.snapshot.taxRuleId&&lineB.snapshot.taxRuleId&&lineA.snapshot.taxRuleId!==lineB.snapshot.taxRuleId);
 console.log('PASS: mixed class coupon allocation and immutable tax snapshots');
 await core.adminAction('campaigns',{action:'create',code:'MARGIN-17',discountBps:1700,minimumMinor:1,maxUses:2,minimumContributionMinor:0,expiresAt:new Date(Date.now()+86400000).toISOString(),active:true},admin);
 const marginCart=token();await core.setCartItem(marginCart,a.variantId,3);await core.setCartItem(marginCart,b.variantId,2);
 const marginQuote=await core.quoteCheckout(marginCart,{country:'TR',currency:'TRY',locale:'tr',couponCode:'MARGIN-17'});await query("UPDATE coupons SET minimum_contribution_minor=40000 WHERE code='MARGIN-17'");
 await assert.rejects(()=>core.checkout(marginCart,{...checkoutInput(),couponCode:'MARGIN-17',quoteToken:marginQuote.quoteToken}),(error:unknown)=>(error as {code:string}).code==='COUPON_MARGIN');
 console.log('PASS: coupon margin uses mixed class net contribution');
 const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);
 await query("UPDATE tax_rules SET rate_bps=2500 WHERE country='TR' AND product_class='textile-20'");
 await query("UPDATE variants SET tax_class='changed-after-order',price_minor=99999 WHERE id=$1",[a.variantId]);
 for(const quantity of [1,2]){
  const r=await core.requestReturn(order.orderId,order.trackingToken,{variantId:a.variantId,quantity,reason:'İzole kısmi iade vergi senaryosu',sealIntact:true}) as {id:string};
  await core.adminAction('returns',{action:'review',id:r.id,approved:true,reason:'İade incelemesi tamamlandı'},admin);await core.adminAction('returns',{action:'receive',id:r.id},admin);await core.adminAction('returns',{action:'inspect',id:r.id,restock:false,reason:'Satışa geri açılmadan kontrol'},admin);await core.adminAction('returns',{action:'refund',id:r.id},admin);
 }
 const [refunded]=await query("SELECT sum(r.amount_minor)::bigint amount,sum(r.tax_minor)::bigint tax,sum(r.discount_minor)::bigint discount FROM refunds r JOIN payments p ON p.id=r.payment_id WHERE p.order_id=$1 AND r.status='succeeded'",[order.orderId]);
 assert.equal(refunded.amount,29882);assert.equal(refunded.tax,4980);assert.equal(refunded.discount,6121);
 const [unchanged]=await query('SELECT tax_minor,snapshot FROM order_items WHERE order_id=$1 AND variant_id=$2',[order.orderId,a.variantId]);assert.equal(unchanged.tax_minor,4980);assert.equal(unchanged.snapshot.taxBps,2000);
 console.log('PASS: partial refunds preserve original class/discount/tax after later rule changes');
 const missing=await product('missing',10001,'*'),missingCart=token();await core.setCartItem(missingCart,missing.variantId,1);const missingQuote=await core.quoteCheckout(missingCart,{country:'TR',currency:'TRY',locale:'tr'});await query("UPDATE variants SET tax_class='missing-class' WHERE id=$1",[missing.variantId]);
 const before=Number((await query('SELECT count(*)::int n FROM orders'))[0].n);
 await assert.rejects(()=>core.checkout(missingCart,{...checkoutInput(),quoteToken:missingQuote.quoteToken}),(error:unknown)=>(error as {code:string}).code==='PRODUCT_TAX_NOT_CONFIGURED');
 assert.equal(Number((await query('SELECT count(*)::int n FROM orders'))[0].n),before);
 console.log('PASS: missing exact class does not fall back to configured wildcard');
 const overlapCart=token();await core.setCartItem(overlapCart,b.variantId,1);const overlapQuote=await core.quoteCheckout(overlapCart,{country:'TR',currency:'TRY',locale:'tr'});
 await query("INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,fixture) VALUES('TR','accessory-10',2000,'2026-02-01',false)");
 await assert.rejects(()=>core.checkout(overlapCart,{...checkoutInput(),quoteToken:overlapQuote.quoteToken}),(error:unknown)=>(error as {code:string}).code==='PRODUCT_TAX_AMBIGUOUS');
 await query("DELETE FROM tax_rules WHERE country='TR' AND product_class='accessory-10' AND valid_from='2026-02-01'");
 const raceRule={kind:'product',country:'TR',productClass:'race-class',rateBps:1000,reference:'İzole çakışma yarışı testi',effectiveFrom:'2026-01-01T00:00:00Z'};
 const results=await Promise.allSettled([manageTax(raceRule,admin),manageTax(raceRule,admin)]);assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
 console.log('PASS: ambiguity fails closed and concurrent overlapping rule creation is serialized');
 const {resolveProductTaxRule}=await import('../src/server/shipping-tax');
 await manageTax({kind:'product',country:'TR',productClass:'future-class',rateBps:1000,reference:'Yalnız gelecekteki ürün sınıfı',effectiveFrom:'2099-01-01T00:00:00Z'},admin);
 await manageTax({kind:'product',country:'TR',productClass:'expired-class',rateBps:1000,reference:'Yalnız süresi geçmiş ürün sınıfı',effectiveFrom:'2025-01-01T00:00:00Z',effectiveUntil:'2025-02-01T00:00:00Z'},admin);
 await assert.rejects(()=>resolveProductTaxRule('TR','future-class'));await assert.rejects(()=>resolveProductTaxRule('TR','expired-class'));
 await query("INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,fixture) VALUES('TR','fixture-class',2000,'2026-01-01',true)");
 process.env.APP_ENV='production';await assert.rejects(()=>resolveProductTaxRule('TR','fixture-class'));assert.equal((await resolveProductTaxRule('TR','accessory-10')).rateBps,1000);process.env.APP_ENV='test';
 console.log('PASS: rule dates and production fixture restriction are enforced');
 console.log('Shipping tax integration: 11 checks passed (base5, mixed6).');
}finally{if(pool)await pool.end();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
