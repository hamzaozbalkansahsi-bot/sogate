/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/quote-integration.ts
 * Açıklama   : Toplam teklifinin yazmasızlığını ve siparişle eşitliğini bağımsız yerel veritabanında sınar.
 */
import assert from 'node:assert/strict';
import {createHash,randomBytes} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
import {seedFixtureAddressProfile} from './seed';
import type {CheckoutInput} from '../src/shared/contracts';
const source=process.env.TEST_DATABASE_URL;if(!source)throw new Error('TEST_DATABASE_URL gerekir.');
const url=new URL(source);assert(['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&url.pathname.endsWith('_test'),'Yalnız yerel test DB.');
const name=`sexsogate_${randomBytes(8).toString('hex')}_quote_test`;assert.match(name,/^sexsogate_[a-f0-9]{16}_quote_test$/);
const control=new pg.Client({connectionString:source});await control.connect();let created=false,pool:pg.Pool|undefined,passed=0;
const token=()=>randomBytes(32).toString('hex');
async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 await control.query(`CREATE DATABASE "${name}"`);created=true;url.pathname='/'+name;process.env.DATABASE_URL=url.href;process.env.APP_ENV='test';process.env.PAYMENT_PROVIDER='test';process.env.PAYMENT_WEBHOOK_SECRET=token();await migrate(url.href);
 const database=await import('../src/server/db');pool=database.pool;const {query}=database,core=await import('../src/server/commerce');const admin={id:'quote-admin',role:'admin' as const,mfa:true};
 await query("INSERT INTO categories(slug,name,name_en)VALUES('quote-fixture','İzole toplam','Isolated totals')");await query("INSERT INTO warehouses(id,name)VALUES('main','Ana Depo')");
 await query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture)VALUES('TR','Yalnız izole test ülkesi',true,true,true,true,true,true,true,1200,'TRY',true)");await seedFixtureAddressProfile(pool);
 await query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture)VALUES('TR',2000,'2026-01-01',true)");await query("INSERT INTO shipping_tax_rules(country,rate_bps,valid_from,reference,approved)VALUES('TR',2000,'2026-01-01','Yalnız izole toplam testi kaynağı',true)");
 for(const kind of ['privacy','terms']){const body='Yalnız izole toplam testi sözleşmesidir; gerçek hukuk onayı değildir.';await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture)VALUES($1,'tr',$1,$2,1,'effective',$3,now(),true)",[kind,body,createHash('sha256').update(body).digest('hex')]);}
 const [p]=await query("INSERT INTO products(slug,name,name_en,category,image,status,fixture)VALUES('quote-fixture','Ölçü ve Özellikler','Measurements and Details','quote-fixture','/media/atelier-01.svg','published',true)RETURNING id");
 const [v]=await query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor)VALUES($1,'QUOTE-FIXTURE','Bordo','Burgundy',12001,1000)RETURNING id",[p.id]);await query("INSERT INTO variant_prices(variant_id,currency,amount_minor)VALUES($1,'TRY',12001)",[v.id]);await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand)VALUES($1,'main',100)",[v.id]);await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference)VALUES($1,'main','receipt',100,'Yalnız izole toplam testi','quote-fixture:'||$1)",[v.id]);
 const {complianceAction}=await import('../src/server/compliance');await complianceAction({action:'eligibility',variantId:v.id,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole toplam testi ülke incelemesi',idempotencyKey:token()},admin);
 const input=()=>({email:'quote@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme Sokak 12',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr' as const,currency:'TRY' as const,idempotencyKey:token(),privacyAccepted:true,termsAccepted:true});
 await check('A new order requires the customer to have received a signed total quote',async()=>{const cart=token();await core.setCartItem(cart,v.id,1);await assert.rejects(()=>core.checkout(cart,input() as CheckoutInput),{code:'CHECKOUT_QUOTE_REQUIRED'});assert.equal((await query('SELECT count(*)::int n FROM orders'))[0].n,0);});
 const selection={country:'TR',locale:'tr' as const,currency:'TRY' as const};
 const tables=['carts','cart_items','orders','order_items','reservations','reservation_lots','coupon_usage','payments','jobs','inventory_balance','inventory_movements','order_agreements','audit_log'];
 async function state(){const result:Record<string,unknown>={};for(const table of tables)result[table]=(await query(`SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text),'[]'::jsonb) value FROM ${table} t`))[0].value;return result;}
 const ownCart=async(quantity=1)=>{const cart=token();await core.setCartItem(cart,v.id,quantity);return cart;};
 await check('Quote executes in a read-only snapshot and never creates a missing cart or financial records',async()=>{
  const cart=await ownCart(),before=await state(),quote=await core.quoteCheckout(cart,selection);assert.equal(quote.subtotalMinor,12001);assert.equal(quote.shippingMinor,1200);assert.equal(quote.totalMinor,13201);assert.deepEqual(await state(),before);
  await assert.rejects(()=>core.quoteCheckout(token(),selection),{code:'EMPTY_CART'});assert.deepEqual(await state(),before);
  for(const hidden of ['costMinor','cost_minor','minimum_contribution','BETTER_AUTH','email','fullName'])assert(!JSON.stringify(quote).includes(hidden));
 });
 await query("INSERT INTO coupons(code,discount_bps,minimum_minor,max_uses,minimum_contribution_minor,expires_at)VALUES('QUOTE-17',1700,0,50,0,now()+interval '1 day')");
 let replay:{cart:string;input:CheckoutInput;orderId:string}|undefined;
 await check('Mixed SKU tax, coupon and shipping totals match order and immutable item allocations exactly',async()=>{
  await query("INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,fixture)VALUES('TR','other',1000,'2026-01-01',true)");
  const [w]=await query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor,tax_class)VALUES($1,'QUOTE-OTHER','Krem','Cream',11003,1000,'other')RETURNING id",[p.id]);await query("INSERT INTO variant_prices(variant_id,currency,amount_minor)VALUES($1,'TRY',11003)",[w.id]);await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand)VALUES($1,'main',20)",[w.id]);await complianceAction({action:'eligibility',variantId:w.id,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole karma vergi sınıfı incelemesi',idempotencyKey:token()},admin);
  const cart=await ownCart(3);await core.setCartItem(cart,w.id,2);const quote=await core.quoteCheckout(cart,{...selection,couponCode:'QUOTE-17'}),data={...input(),quoteToken:quote.quoteToken,couponCode:'QUOTE-17'},order=await core.checkout(cart,data);
  assert.deepEqual([quote.subtotalMinor,quote.discountMinor,quote.shippingMinor,quote.goodsTaxMinor,quote.shippingTaxMinor,quote.taxMinor,quote.totalMinor],[58009,9862,1200,6640,200,6840,49347]);assert.equal(order.totalMinor,quote.totalMinor);
  const [saved]=await query('SELECT * FROM orders WHERE id=$1',[order.orderId]);for(const [dto,column]of [['subtotalMinor','subtotal_minor'],['discountMinor','discount_minor'],['shippingMinor','shipping_minor'],['taxMinor','tax_minor'],['totalMinor','total_minor']] as const)assert.equal(saved[column],quote[dto]);
  const lines=await query('SELECT variant_id,quantity,unit_minor,discount_minor,tax_minor,snapshot FROM order_items WHERE order_id=$1',[order.orderId]);for(const line of lines){const quoted=quote.lines.find(row=>row.variantId===line.variant_id)!;assert.equal(quoted.unitMinor,line.unit_minor);assert.equal(quoted.quantity,line.quantity);assert.equal(quoted.discountMinor,line.discount_minor);assert.equal(quoted.taxMinor,line.tax_minor);assert.equal(quoted.lineTotalMinor,line.snapshot.lineGrossMinor-line.discount_minor);}
  replay={cart,input:data,orderId:order.orderId};
 });
 await check('Price, tax, shipping, coupon and private cost changes require fresh confirmation without financial writes',async()=>{
  const changes=[
   {sql:"UPDATE variant_prices SET amount_minor=amount_minor+1 WHERE variant_id=$1 AND currency='TRY'",undo:"UPDATE variant_prices SET amount_minor=amount_minor-1 WHERE variant_id=$1 AND currency='TRY'",values:[v.id]},
   {sql:"UPDATE tax_rules SET rate_bps=rate_bps+1 WHERE country='TR' AND product_class='*'",undo:"UPDATE tax_rules SET rate_bps=rate_bps-1 WHERE country='TR' AND product_class='*'",values:[]},
   {sql:"UPDATE country_rules SET shipping_minor=shipping_minor+100 WHERE code='TR'",undo:"UPDATE country_rules SET shipping_minor=shipping_minor-100 WHERE code='TR'",values:[]},
   {sql:"UPDATE coupons SET minimum_minor=minimum_minor+1 WHERE code='QUOTE-17'",undo:"UPDATE coupons SET minimum_minor=minimum_minor-1 WHERE code='QUOTE-17'",values:[]},
   {sql:"UPDATE variants SET cost_minor=cost_minor+1 WHERE id=$1",undo:"UPDATE variants SET cost_minor=cost_minor-1 WHERE id=$1",values:[v.id]}
  ];
  for(const change of changes){const cart=await ownCart(),quote=await core.quoteCheckout(cart,{...selection,couponCode:'QUOTE-17'});await query(change.sql,change.values);try{const before=await state();await assert.rejects(()=>core.checkout(cart,{...input(),couponCode:'QUOTE-17',quoteToken:quote.quoteToken}),{code:'CHECKOUT_QUOTE_CHANGED'});assert.deepEqual(await state(),before);}finally{await query(change.undo,change.values);}}
 });
 await check('Cart quantity, copied cart tokens and forged signatures cannot authorize a new total',async()=>{
  const cart=await ownCart(),other=await ownCart(),quote=await core.quoteCheckout(cart,selection);let before=await state();await assert.rejects(()=>core.checkout(other,{...input(),quoteToken:quote.quoteToken}),{code:'CHECKOUT_QUOTE_CHANGED'});assert.deepEqual(await state(),before);
  await core.setCartItem(cart,v.id,2);before=await state();await assert.rejects(()=>core.checkout(cart,{...input(),quoteToken:quote.quoteToken}),{code:'CHECKOUT_QUOTE_CHANGED'});await assert.rejects(()=>core.checkout(cart,{...input(),quoteToken:quote.quoteToken.slice(0,-4)+'0000'}),{code:'CHECKOUT_QUOTE_INVALID'});assert.deepEqual(await state(),before);
 });
 await check('Expired quotes block new orders; existing semantic idempotent replays survive expired and refreshed tokens',async()=>{
  const {createQuoteToken}=await import('../src/server/commerce/quote-token');const cart=await ownCart(),quote=await core.quoteCheckout(cart,selection),claims=JSON.parse(Buffer.from(quote.quoteToken.split('.')[0],'base64url').toString('utf8'));const {version,issuedAt,expiresAt,...binding}=claims;assert.equal(version,1);assert(issuedAt<expiresAt);const expired=createQuoteToken(binding,Date.now()-301000).quoteToken,before=await state();await assert.rejects(()=>core.checkout(cart,{...input(),quoteToken:expired}),{code:'CHECKOUT_QUOTE_EXPIRED'});assert.deepEqual(await state(),before);
  assert(replay);const old=JSON.parse(Buffer.from(replay.input.quoteToken.split('.')[0],'base64url').toString('utf8')),oldExpired=createQuoteToken({cartId:old.cartId,cartTokenHash:old.cartTokenHash,selectionHash:old.selectionHash,evaluationHash:old.evaluationHash},Date.now()-301000).quoteToken;
  assert.equal((await core.checkout(replay.cart,{...replay.input,quoteToken:oldExpired})).orderId,replay.orderId);const fresh=await core.quoteCheckout(replay.cart,{...selection,couponCode:'QUOTE-17'});assert.equal((await core.checkout(replay.cart,{...replay.input,quoteToken:fresh.quoteToken})).orderId,replay.orderId);await assert.rejects(()=>core.checkout(replay!.cart,{...replay!.input,quoteToken:fresh.quoteToken,city:'İzmir'}),{code:'IDEMPOTENCY_CONFLICT'});
  const initialSnapshot=(await query('SELECT snapshot FROM orders WHERE id=$1',[replay.orderId]))[0].snapshot;assert.equal(initialSnapshot.checkoutQuote.evaluationHash,old.evaluationHash);const payment=await core.createTestPaymentEvent(replay.orderId,(await core.checkout(replay.cart,replay.input)).trackingToken,'succeeded');await core.handlePayment(payment.raw,payment.signature);assert.equal((await core.checkout(replay.cart,{...replay.input,quoteToken:oldExpired})).orderId,replay.orderId);assert.equal((await query('SELECT count(*)::int n FROM payments WHERE order_id=$1',[replay.orderId]))[0].n,1);assert.deepEqual((await query('SELECT snapshot FROM orders WHERE id=$1',[replay.orderId]))[0].snapshot,initialSnapshot);
 });
 await check('Two pre-issued quotes still compete atomically for the last coupon usage',async()=>{
  await query("INSERT INTO coupons(code,discount_bps,minimum_minor,max_uses,minimum_contribution_minor,expires_at)VALUES('QUOTE-LAST',1000,0,1,0,now()+interval '1 day')");const carts=[await ownCart(),await ownCart()],quotes=await Promise.all(carts.map(cart=>core.quoteCheckout(cart,{...selection,couponCode:'QUOTE-LAST'})));
  const results=await Promise.allSettled(carts.map((cart,i)=>core.checkout(cart,{...input(),quoteToken:quotes[i].quoteToken,couponCode:'QUOTE-LAST'})));assert.equal(results.filter(row=>row.status==='fulfilled').length,1);assert.equal((results.find(row=>row.status==='rejected') as PromiseRejectedResult).reason.code,'COUPON_LIMIT');
 });
 await check('Command pricing holds sorted product and SKU locks until revalidation finishes',async()=>{
  const {evaluateCheckoutPricing,pricingQuoteBinding}=await import('../src/server/commerce/checkout-pricing'),{verifyQuoteToken}=await import('../src/server/commerce/quote-token');
  for(const kind of ['product','variant']){
   const cart=await ownCart(),quote=await core.quoteCheckout(cart,selection),[record]=await query('SELECT id FROM carts WHERE token_hash=$1',[createHash('sha256').update(cart).digest('hex')]);const reader=await pool!.connect(),writer=await pool!.connect();let changing:Promise<unknown>|undefined;
   try{await reader.query('BEGIN');const priced=await evaluateCheckoutPricing(record.id,selection,reader,true),pid=Number((await writer.query('SELECT pg_backend_pid() pid')).rows[0].pid);
    changing=kind==='variant'?writer.query('UPDATE variants SET cost_minor=cost_minor+1 WHERE id=$1',[v.id]):writer.query("UPDATE products SET name=name||' X' WHERE id=$1",[p.id]);
    let blocked=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE pid=$1 AND wait_event_type='Lock'",[pid])).length){blocked=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(blocked,'Product/SKU writer must wait while the command evaluates its accepted total');
    verifyQuoteToken(quote.quoteToken,pricingQuoteBinding(record.id,createHash('sha256').update(cart).digest('hex'),selection,priced));await reader.query('ROLLBACK');await changing;
    await assert.rejects(()=>core.checkout(cart,{...input(),quoteToken:quote.quoteToken}),{code:'CHECKOUT_QUOTE_CHANGED'});
   }finally{await reader.query('ROLLBACK');if(changing)await changing;reader.release();writer.release();if(kind==='variant')await query('UPDATE variants SET cost_minor=cost_minor-1 WHERE id=$1',[v.id]);else await query("UPDATE products SET name=left(name,length(name)-2) WHERE id=$1",[p.id]);}
  }
 });
 const {mergeCustomerCart}=await import('../src/server/customer');
 await check('A stale anonymous checkout cannot create an order or replay one after the cart is claimed',async()=>{
  const principal={id:'checkout-owner-'+token().slice(0,16),role:'customer' as const,mfa:false};
  const cart=await ownCart(),quote=await core.quoteCheckout(cart,selection),data={...input(),quoteToken:quote.quoteToken};
  const [outside]=await query('SELECT user_id FROM carts WHERE token_hash=$1',[createHash('sha256').update(cart).digest('hex')]);assert.equal(outside.user_id,null);
  await mergeCustomerCart(cart,principal);const before=await state();await assert.rejects(()=>core.checkout(cart,data),{code:'CART_NOT_FOUND'});await assert.rejects(()=>core.checkout(cart,data,'different-user'),{code:'CART_NOT_FOUND'});assert.deepEqual(await state(),before);
  const own=await core.checkout(cart,data,principal.id);assert.equal((await query('SELECT user_id FROM orders WHERE id=$1',[own.orderId]))[0].user_id,principal.id);await assert.rejects(()=>core.checkout(cart,data),{code:'CART_NOT_FOUND'});assert.equal((await core.checkout(cart,data,principal.id)).orderId,own.orderId);
  const pendingCart=await ownCart(),pendingQuote=await core.quoteCheckout(pendingCart,selection),pendingInput={...input(),quoteToken:pendingQuote.quoteToken},pending=await core.checkout(pendingCart,pendingInput);const secondOwner={id:'pending-owner-'+token().slice(0,16),role:'customer' as const,mfa:false};await mergeCustomerCart(pendingCart,secondOwner);await assert.rejects(()=>core.checkout(pendingCart,pendingInput),{code:'CART_NOT_FOUND'});assert.equal((await core.checkout(pendingCart,pendingInput,secondOwner.id)).orderId,pending.orderId);
 });
 await check('An order owner remains authoritative after member merging detaches its original cart',async()=>{
  const principal={id:'detached-owner-'+token().slice(0,16),role:'customer' as const,mfa:false},original=await ownCart();await mergeCustomerCart(original,principal);
  const quote=await core.quoteCheckout(original,selection,principal.id),data={...input(),quoteToken:quote.quoteToken},order=await core.checkout(original,data,principal.id),incoming=await ownCart();await mergeCustomerCart(incoming,principal);
  assert.equal((await query('SELECT user_id FROM carts WHERE token_hash=$1',[createHash('sha256').update(original).digest('hex')]))[0].user_id,null);
  const before=await state();await assert.rejects(()=>core.checkout(original,data),{code:'CART_NOT_FOUND'});await assert.rejects(()=>core.checkout(original,data,'different-user'),{code:'CART_NOT_FOUND'});assert.deepEqual(await state(),before);assert.equal((await core.checkout(original,data,principal.id)).orderId,order.orderId);
 });
 await check('Checkout begun first keeps the cart locked until its anonymous order snapshot is committed',async()=>{
  const cart=await ownCart(),quote=await core.quoteCheckout(cart,selection),data={...input(),quoteToken:quote.quoteToken},principal={id:'blocked-merge-'+token().slice(0,16),role:'customer' as const,mfa:false},barrier=await pool!.connect();let pending:Promise<Awaited<ReturnType<typeof core.checkout>>>|undefined,merging:Promise<string>|undefined;
  try{await barrier.query('BEGIN');await barrier.query('LOCK TABLE tax_rules IN ACCESS EXCLUSIVE MODE');pending=core.checkout(cart,data);
   let waiting=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE '%FROM tax_rules t%'")).length){waiting=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(waiting,'Checkout must reach the tax query after locking the cart');
   merging=mergeCustomerCart(cart,principal);let blocked=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT * FROM carts WHERE token_hash=%FOR UPDATE'")).length){blocked=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(blocked,'Member claim must wait until checkout releases its cart row');
   await barrier.query('ROLLBACK');const order=await pending;await merging;assert.equal((await query('SELECT user_id FROM orders WHERE id=$1',[order.orderId]))[0].user_id,null);assert.equal((await query('SELECT user_id FROM carts WHERE token_hash=$1',[createHash('sha256').update(cart).digest('hex')]))[0].user_id,principal.id);await assert.rejects(()=>core.checkout(cart,data),{code:'CART_NOT_FOUND'});assert.equal((await core.checkout(cart,data,principal.id)).orderId,order.orderId);
  }finally{await barrier.query('ROLLBACK');if(pending)await pending.catch(()=>{});if(merging)await merging.catch(()=>{});barrier.release();}
 });
 async function ownerMergeFixture(label:string){
  const principal={id:'quote-owner-'+token().slice(0,16),role:'customer' as const,mfa:false};
  const [privateProduct]=await query("INSERT INTO products(slug,name,name_en,category,image,status,fixture)VALUES($1,'Üyenin sepet tercihi','Member cart preference','quote-fixture','/media/atelier-01.svg','published',true)RETURNING id",['owner-'+label+'-'+token().slice(0,12)]);
  const [privateVariant]=await query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor)VALUES($1,$2,'Özel sepet satırı','Private cart line',1000,100)RETURNING id",[privateProduct.id,'PRIVATE-'+token().slice(0,12)]);await query("INSERT INTO variant_prices(variant_id,currency,amount_minor)VALUES($1,'TRY',1000)",[privateVariant.id]);await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand)VALUES($1,'main',10)",[privateVariant.id]);
  const guest=await ownCart(),member=token();await core.setCartItem(member,privateVariant.id,1);await query('UPDATE carts SET user_id=$2 WHERE token_hash=$1',[createHash('sha256').update(member).digest('hex'),principal.id]);return {principal,guest,privateId:String(privateVariant.id)};
 }
 await check('A stale external guest precheck cannot disclose rows merged into the newly owned cart',async()=>{
  const {principal,guest,privateId}=await ownerMergeFixture('precheck');let release=()=>{},reached=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;}),checked=new Promise<void>(resolve=>{reached=resolve;});
  const pending=(async()=>{const [outside]=await query('SELECT user_id FROM carts WHERE token_hash=$1',[createHash('sha256').update(guest).digest('hex')]);assert.equal(outside.user_id,null);reached();await gate;return core.quoteCheckout(guest,selection);})();
  await checked;assert.equal(await mergeCustomerCart(guest,principal),guest);const before=await state();release();await assert.rejects(()=>pending,{code:'EMPTY_CART'});assert.deepEqual(await state(),before);
  await assert.rejects(()=>core.quoteCheckout(guest,selection,'different-owner'),{code:'EMPTY_CART'});const own=await core.quoteCheckout(guest,selection,principal.id);assert(own.lines.some(line=>line.variantId===privateId));
 });
 await check('A guest snapshot established before claim never observes later private cart rows',async()=>{
  const {principal,guest,privateId}=await ownerMergeFixture('repeatable'),barrier=await pool!.connect();let pending:Promise<Awaited<ReturnType<typeof core.quoteCheckout>>>|undefined;
  try{await barrier.query('BEGIN');await barrier.query('LOCK TABLE country_rules IN ACCESS EXCLUSIVE MODE');pending=core.quoteCheckout(guest,selection);
   let waiting=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT * FROM country_rules WHERE%'" )).length){waiting=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(waiting,'Quote must first read cart ownership, then wait at the country read barrier');
   await mergeCustomerCart(guest,principal);await barrier.query('ROLLBACK');const snapshot=await pending;assert(!snapshot.lines.some(line=>line.variantId===privateId));assert.equal(snapshot.lines.length,1);await assert.rejects(()=>core.quoteCheckout(guest,selection),{code:'EMPTY_CART'});const own=await core.quoteCheckout(guest,selection,principal.id);assert(own.lines.some(line=>line.variantId===privateId));
  }finally{await barrier.query('ROLLBACK');if(pending)await pending.catch(()=>{});barrier.release();}
 });
 console.log(`Quote integration: ${passed} checks passed.`);
}finally{await pool?.end();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
