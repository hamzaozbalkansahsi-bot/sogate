/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/operations-integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import assert from 'node:assert/strict';
import {randomBytes,createHash} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
import {seedFixtureAddressProfile} from './seed';
const source=process.env.TEST_DATABASE_URL;
if(!source)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(source);if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('Yalnız yerel izole test ortamına izin verilir.');
const name=`sexsogate_${randomBytes(8).toString('hex')}_operations_test`;assert.match(name,/^sexsogate_[a-f0-9]{16}_operations_test$/);
const control=new pg.Client({connectionString:source});await control.connect();let created=false,close:(()=>Promise<void>)|undefined,passed=0;
async function check(name:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${name}`);}
const token=()=>randomBytes(32).toString('hex');
try {
 await control.query(`CREATE DATABASE "${name}"`);created=true;url.pathname='/'+name;
 process.env.DATABASE_URL=url.toString();process.env.APP_ENV='test';process.env.PAYMENT_PROVIDER='test';process.env.PAYMENT_WEBHOOK_SECRET=randomBytes(32).toString('hex');
 await migrate(process.env.DATABASE_URL);
 const {pool,query}=await import('../src/server/db');close=()=>pool.end();
 const core=await import('../src/server/commerce');const {complianceAction}=await import('../src/server/compliance');
 const admin={id:'operations-admin',role:'admin' as const,mfa:true};
 await query("INSERT INTO warehouses(id,name) VALUES('main','Ana Depo')");
 const createdProduct=await core.adminAction('products',{name:'İç Giyim Ölçü ve Özellikler',nameEn:'Lingerie measurements and details',slug:'ic-giyim-olcu',category:'aksesuarlar',brand:'',description:'Türkçe ürün açıklaması',descriptionEn:'English product description',sku:'OPS-BASE',variantName:'Bordo',variantNameEn:'Burgundy',priceMinor:10001,costMinor:3000,material:'Tekstil',image:'/media/atelier-01.svg',warnings:'Yalnız yetişkinler için.',warningsEn:'For adults only.',care:'Bakım etiketini izleyin.',careEn:'Follow the care label.'},admin) as {id:string,variantId:string};
 let variantId=createdProduct.variantId;
 const checkoutInput=()=>({email:'ops@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme İç Giyim Ölçü ve Özellikler',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr' as const,currency:'TRY' as const,idempotencyKey:token(),privacyAccepted:true,termsAccepted:true});
 const quotedInput=async(cart:string,extra:{locale?:'tr'|'en';couponCode?:string}={})=>{const input={...checkoutInput(),...extra};const quote=await core.quoteCheckout(cart,{country:input.country,currency:input.currency,locale:input.locale,...(input.couponCode?{couponCode:input.couponCode}:{})});return {...input,quoteToken:quote.quoteToken};};
 await query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES('TR','Türkiye',true,true,true,true,true,true,true,0,'TRY',true)");
 await seedFixtureAddressProfile(pool!);
 await query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture) VALUES('TR',2000,now()-interval '1 day',true)");
 for(const locale of ['tr','en'])for(const kind of ['privacy','terms']){const body=locale==='tr'?'İzole operasyon testi sözleşmesi. Güvenli Alışveriş.':'Isolated operations agreement. Private shopping.';await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture) VALUES($1,$2,$1,$3,1,'effective',$4,now(),true)",[kind,locale,body,createHash('sha256').update(body).digest('hex')]);}
 async function createProduct(suffix:string,priceMinor=10001,costMinor=3000){return await core.adminAction('products',{name:`Operasyon ${suffix}`,nameEn:`Operations ${suffix}`,slug:`ops-${suffix}`,category:'aksesuarlar',brand:'',description:'Üretici bilgileri için içerik alanı.',descriptionEn:'Product information for the operation test.',sku:`OPS-${suffix.toUpperCase()}`,variantName:'Bordo',variantNameEn:'Burgundy',priceMinor,costMinor,material:'Tekstil',image:'/media/atelier-01.svg',warnings:'Yalnız yetişkinler için.',warningsEn:'For adults only.',care:'Bakım etiketini izleyin.',careEn:'Follow the care label.'},admin) as {id:string,variantId:string};}
 const publish=async(id:string)=>{const ids=await query('SELECT id FROM variants WHERE product_id=$1 AND active UNION SELECT bc.component_variant_id id FROM bundle_components bc JOIN variants v ON v.id=bc.bundle_variant_id WHERE v.product_id=$1',[id]);for(const row of ids)await complianceAction({action:'eligibility',variantId:row.id,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole operasyon testi ön incelemesi',idempotencyKey:token()},admin);return core.adminAction('products',{action:'publish',id,country:'TR',reviewNote:'Yalnız izole operasyon testi'},admin);};
 await check('Category and brand editing/archive persist Turkish names and deny warehouse writes',async()=>{
  await core.adminAction('categories',{action:'create',slug:'ozel-koleksiyon',name:'Özel Koleksiyon',nameEn:'Special Collection'},admin);
  await core.adminAction('brands',{action:'create',slug:'atelier',name:'Atelier',nameEn:'Atelier'},admin);
  await core.adminAction('categories',{action:'update',slug:'ozel-koleksiyon',name:'İstanbul Çeşme',nameEn:'Istanbul Cesme'},admin);
  const categories=await core.adminList('categories',admin) as {rows:Record<string,unknown>[]};assert(categories.rows.some(r=>r.name==='İstanbul Çeşme'));
  const filtered=await core.adminList('categories',admin,{q:'istanbul çeşme'}) as {rows:Record<string,unknown>[]};assert(filtered.rows.some(r=>r.name==='İstanbul Çeşme'),'Türkçe büyük/küçük harf admin aramasında korunmalıdır');
  await assert.rejects(()=>core.adminAction('brands',{action:'archive',slug:'atelier'},{id:'w',role:'warehouse',mfa:true}));
  await core.adminAction('brands',{action:'archive',slug:'atelier'},admin);
  assert.equal((await query("SELECT active FROM brands WHERE slug='atelier'"))[0].active,false);
 });
 await check('Variants have distinct SKU, translations and audited atomic multi-currency prices',async()=>{
  const variant=await core.adminAction('variants',{action:'create',productId:createdProduct.id,sku:'OPS-SECOND',name:'Krem · M',nameEn:'Cream · M',priceMinor:12500,costMinor:4000,color:'Krem',size:'M',weightGrams:120},admin) as {id:string};
  variantId=variant.id;
  await assert.rejects(()=>core.adminAction('variants',{action:'create',productId:createdProduct.id,sku:'OPS-SECOND',name:'Tekrar',nameEn:'Duplicate',priceMinor:12500},admin));
  await core.adminAction('variants',{action:'prices',id:variant.id,prices:[{currency:'TRY',amountMinor:15999},{currency:'EUR',amountMinor:1299}],reason:'Doğrulanmış sabit fiyat listesi'},admin);
  assert.equal((await query('SELECT price_minor FROM variants WHERE id=$1',[variant.id]))[0].price_minor,15999);
  assert.equal((await query('SELECT amount_minor FROM variant_prices WHERE variant_id=$1 AND currency=\'EUR\'',[variant.id]))[0].amount_minor,1299);
  const rows=await core.adminList('variants',{id:'w',role:'warehouse',mfa:true}) as {rows:Record<string,unknown>[]};assert(rows.rows.every(r=>!('costMinor'in r)));
  assert.equal((await query("SELECT count(*)::int n FROM audit_log WHERE resource='variants' AND action='prices' AND resource_id=$1",[variant.id]))[0].n,1);
 });
 await check('Purchase receipt creates own-depot stock exactly once and cannot over-receive',async()=>{
  const supplier=await core.adminAction('suppliers',{name:'İzole Tedarikçi',leadDays:5},admin) as {id:string};
  const purchase=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId,quantity:3,unitCostMinor:4000}]},admin) as {id:string};
  const receipt={action:'receive',sourceReference:'Yalnız izole mal kabul teslimat belgesi',id:purchase.id,idempotencyKey:token(),items:[{variantId,quantity:2}],reason:'Barkodla doğrulanan mal kabulü'};
  const results=await Promise.all([core.adminAction('purchases',receipt,admin),core.adminAction('purchases',receipt,admin)]) as {id:string,duplicate?:boolean}[];
  assert.equal(results[0].id,results[1].id);assert.equal((await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[variantId]))[0].on_hand,2);
  await assert.rejects(()=>core.adminAction('purchases',{...receipt,idempotencyKey:token(),items:[{variantId,quantity:2}]},admin));
  await core.adminAction('purchases',{...receipt,idempotencyKey:token(),items:[{variantId,quantity:1}]},admin);
  assert.equal((await query('SELECT status FROM purchase_orders WHERE id=$1',[purchase.id]))[0].status,'received');
 });
 await check('Campaign admin validates limits and financial margin; marketing cannot read invoice details',async()=>{
  await assert.rejects(()=>core.adminAction('campaigns',{action:'create',code:'INVALID',discountBps:10001,minimumMinor:0,maxUses:1,minimumContributionMinor:0,expiresAt:new Date(Date.now()+86400000).toISOString(),active:true},admin));
  const campaign=await core.adminAction('campaigns',{action:'create',code:'LOCAL-17',discountBps:1700,minimumMinor:100,maxUses:3,minimumContributionMinor:0,expiresAt:new Date(Date.now()+86400000).toISOString(),active:true},admin) as {id:string};
  await core.adminAction('campaigns',{action:'archive',id:campaign.id},admin);assert.equal((await query('SELECT active FROM coupons WHERE id=$1',[campaign.id]))[0].active,false);
  await assert.rejects(()=>core.adminList('invoices',{id:'m',role:'marketing',mfa:true}));
 });
 await check('Reports keep currencies separate and never combine TRY and EUR under one label',async()=>{
  await query("INSERT INTO carts(token_hash) VALUES('ops-report-cart')");
  const cart=(await query("SELECT id FROM carts WHERE token_hash='ops-report-cart'"))[0].id;
  for(const [currency,total]of [['TRY',10000],['EUR',2000]] as const)await query("INSERT INTO orders(cart_id,idempotency_key,request_hash,tracking_hash,currency,subtotal_minor,shipping_minor,tax_minor,total_minor,email,address,snapshot,expires_at,status,payment_status) VALUES($1,$2,'x','x',$2,$3,0,0,$3,'report@example.invalid','{}','{}',now(),'confirmed','succeeded')",[cart,currency,total]);
  const report=await core.adminList('reports',admin) as {rows:Record<string,unknown>[]};
  assert(report.rows.some(r=>r.metric==='Tahsilat toplamı'&&r.currency==='TRY'&&r.value===10000));
  assert(report.rows.some(r=>r.metric==='Tahsilat toplamı'&&r.currency==='EUR'&&r.value===2000));
  assert(!report.rows.some(r=>r.metric==='Tahsilat toplamı'&&r.value===12000));
 });
 await check('Two-component bundle reserves atomically and last unit cannot be sold twice',async()=>{
  const a=await createProduct('component-a'),b=await createProduct('component-b'),bundle=await createProduct('bundle',30000,9000);
  await core.adminAction('inventory',{variantId:a.variantId,quantity:2,reason:'İlk bileşen mal kabulü'},admin);await core.adminAction('inventory',{variantId:b.variantId,quantity:1,reason:'İkinci bileşen mal kabulü'},admin);
  await core.adminAction('variants',{action:'bundle',id:bundle.variantId,components:[{variantId:a.variantId,quantity:2},{variantId:b.variantId,quantity:1}],reason:'İki bileşenli set eşlemesi'},admin);
  await publish(a.id);await publish(b.id);await publish(bundle.id);
  assert.equal((await core.getProduct('ops-bundle'))?.variants[0].available,1);
  const cartA=token(),cartB=token();await core.setCartItem(cartA,bundle.variantId,1);await core.setCartItem(cartB,bundle.variantId,1);
  const [inputA,inputB]=await Promise.all([quotedInput(cartA),quotedInput(cartB)]);
  const results=await Promise.allSettled([core.checkout(cartA,inputA),core.checkout(cartB,inputB)]);assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
  const order=(results.find(r=>r.status==='fulfilled') as PromiseFulfilledResult<Awaited<ReturnType<typeof core.checkout>>>).value;
  const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);await core.handlePayment(event.raw,event.signature);
  const balances=await query('SELECT on_hand FROM inventory_balance WHERE variant_id=ANY($1::text[])',[[a.variantId,b.variantId,bundle.variantId]]);assert(balances.every(x=>x.on_hand===0));
 });
 await check('Restricted battery/liquid SKU blocks checkout and shipment without reviewed carrier permission',async()=>{
  const item=await createProduct('restricted');await core.adminAction('inventory',{variantId:item.variantId,quantity:3,reason:'Kısıtlı ürün stok testi'},admin);
  await core.adminAction('variants',{action:'update',id:item.variantId,batteryType:'lithium-ion',liquid:true},admin);
  await publish(item.id);
  const cart=token();await core.setCartItem(cart,item.variantId,1);
  await core.adminAction('variants',{action:'shippingApproval',id:item.variantId,carrier:'Onaylı Taşıyıcı',country:'TR',accepted:true,reference:'Teklif öncesi izole test kabul referansı'},admin);
  const beforeRevocation=await quotedInput(cart);
  await core.adminAction('variants',{action:'shippingApproval',id:item.variantId,carrier:'Onaylı Taşıyıcı',country:'TR',accepted:false,reference:'Teklif sonrası izole kabul iptali'},admin);
  await assert.rejects(()=>core.checkout(cart,beforeRevocation),(error:unknown)=>(error as {code:string}).code==='CARRIER_ACCEPTANCE_REQUIRED');
  await core.adminAction('variants',{action:'shippingApproval',id:item.variantId,carrier:'Onaylı Taşıyıcı',country:'TR',accepted:true,reference:'Yalnız izole test kabul referansı'},admin);
  const order=await core.checkout(cart,await quotedInput(cart));const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);
  await assert.rejects(()=>core.adminAction('shipments',{orderId:order.orderId,carrier:'Başka Taşıyıcı',trackingNumber:'OPS-RESTRICTED-WRONG'},admin));
  await core.adminAction('shipments',{orderId:order.orderId,carrier:'Onaylı Taşıyıcı',trackingNumber:'OPS-RESTRICTED-OK'},admin);
 });
 await check('Bundle return uses sold snapshot components after set definition changes; quarantine cannot be bypassed',async()=>{
  const a=await createProduct('return-component-a'),b=await createProduct('return-component-b'),bundle=await createProduct('return-bundle',30000,6000);
  await core.adminAction('inventory',{variantId:a.variantId,quantity:2,reason:'Satış bileşeni mal kabulü'},admin);await core.adminAction('inventory',{variantId:b.variantId,quantity:2,reason:'Sonraki set bileşeni mal kabulü'},admin);
  await core.adminAction('variants',{action:'bundle',id:bundle.variantId,components:[{variantId:a.variantId,quantity:2}],reason:'Satış anındaki set tanımı'},admin);await publish(a.id);await publish(b.id);await publish(bundle.id);
  const cart=token();await core.setCartItem(cart,bundle.variantId,1);const order=await core.checkout(cart,await quotedInput(cart));const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);
  await core.adminAction('variants',{action:'bundle',id:bundle.variantId,expectedVersion:1,components:[{variantId:b.variantId,quantity:2}],reason:'Sipariş sonrası değişen set tanımı'},admin);
  const r=await core.requestReturn(order.orderId,order.trackingToken,{variantId:bundle.variantId,quantity:1,reason:'Set ölçüsü uygun bulunmadı',sealIntact:true}) as {id:string};await core.adminAction('returns',{action:'review',id:r.id,approved:true,reason:'Set iade incelemesi tamamlandı'},admin);await core.adminAction('returns',{action:'receive',id:r.id},admin);
  const balance=async(id:string)=>(await query("SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main'",[id]))[0];
  assert.equal((await balance(a.variantId)).quarantine,2);assert.equal((await balance(bundle.variantId)).quarantine,0);assert.equal((await balance(b.variantId)).on_hand,2);assert.equal((await balance(b.variantId)).quarantine,0);
  await assert.rejects(()=>core.adminAction('inventory',{action:'release',variantId:a.variantId,quantity:2,reason:'Set iadesini genel stoktan açma denemesi'},admin));
  await core.adminAction('returns',{action:'inspect',id:r.id,restock:true,reason:'Mühür ve tüm bileşen kontrolleri uygun'},admin);
  assert.equal((await balance(a.variantId)).on_hand,2);assert.equal((await balance(a.variantId)).quarantine,0);assert.equal((await balance(bundle.variantId)).on_hand,0);assert.equal((await balance(b.variantId)).on_hand,2);
 });
 await check('Partial refunds preserve original discount/tax allocation and external invoice requires seller setup',async()=>{
  const item=await createProduct('refund');await core.adminAction('inventory',{variantId:item.variantId,quantity:3,reason:'Kısmi iade stoğu'},admin);await publish(item.id);
  await core.adminAction('campaigns',{action:'create',code:'REFUND-17',discountBps:1700,minimumMinor:100,maxUses:1,minimumContributionMinor:0,expiresAt:new Date(Date.now()+86400000).toISOString(),active:true},admin);
  const cart=token();await core.setCartItem(cart,item.variantId,3);const order=await core.checkout(cart,await quotedInput(cart,{couponCode:'REFUND-17'}));const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);
  const [line]=await query('SELECT unit_minor,quantity,tax_minor,discount_minor FROM order_items WHERE order_id=$1',[order.orderId]);
  await core.adminAction('variants',{action:'prices',id:item.variantId,prices:[{currency:'TRY',amountMinor:99999}],reason:'Sipariş sonrası fiyat değişikliği testi'},admin);
  for(const quantity of [1,2]){const r=await core.requestReturn(order.orderId,order.trackingToken,{variantId:item.variantId,quantity,reason:'Ölçü uyumsuzluğu bildirimi',sealIntact:true}) as {id:string};await core.adminAction('returns',{action:'review',id:r.id,approved:true,reason:'Operasyon testi incelemesi'},admin);await core.adminAction('returns',{action:'receive',id:r.id},admin);await core.adminAction('returns',{action:'inspect',id:r.id,restock:true,reason:'Mühür ve bakım kontrolü uygun'},admin);await core.adminAction('returns',{action:'refund',id:r.id},admin);}
  const [refund]=await query("SELECT sum(r.amount_minor)::bigint amount,sum(r.tax_minor)::bigint tax,sum(r.discount_minor)::bigint discount FROM refunds r JOIN payments p ON p.id=r.payment_id WHERE p.order_id=$1 AND r.status='succeeded'",[order.orderId]);
  assert.equal(refund.amount,Number(line.unit_minor)*line.quantity-Number(line.discount_minor));assert.equal(refund.tax,line.tax_minor);assert.equal(refund.discount,line.discount_minor);
  const invoice={action:'register',orderId:order.orderId,provider:'Manuel dış sistem',reference:'OPS-EXTERNAL-INVOICE',documentKind:'e_archive',note:'Yetkili dış sistemde oluşturulan belge referansı'};
  await assert.rejects(()=>core.adminAction('invoices',invoice,admin));
  for(const key of ['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone'])await query('INSERT INTO settings(key,value) VALUES($1,$2)',[key,JSON.stringify(`İzole test ${key}`)]);
  const first=await core.adminAction('invoices',invoice,admin) as {id:string,fiscalDocumentGenerated:boolean};const repeat=await core.adminAction('invoices',invoice,admin) as {id:string};assert.equal(first.id,repeat.id);assert.equal(first.fiscalDocumentGenerated,false);
 });
 await check('English checkout snapshots English product,variant,care/warnings and matching agreements',async()=>{
  const item=await createProduct('english');await core.adminAction('inventory',{variantId:item.variantId,quantity:1,reason:'İngilizce akış testi'},admin);await publish(item.id);
  const cart=token();await core.setCartItem(cart,item.variantId,1);
  const cartRecord=await core.getCart(cart);assert.equal((cartRecord.items[0] as typeof cartRecord.items[0]&{productNameEn:string}).productNameEn,'Operations english');
  const order=await core.checkout(cart,await quotedInput(cart,{locale:'en'}));
  const [line]=await query('SELECT name,snapshot FROM order_items WHERE order_id=$1',[order.orderId]);assert.equal(line.name,'Operations english');assert.equal(line.snapshot.variantName,'Burgundy');assert.equal(line.snapshot.care,'Follow the care label.');assert.equal(line.snapshot.warnings,'For adults only.');
  const agreements=await query('SELECT locale FROM order_agreements WHERE order_id=$1',[order.orderId]);assert.equal(agreements.length,2);assert(agreements.every(a=>a.locale==='en'));
 });
 await check('Real-provider refund stays pending until verified success; duplicate finalize cannot refund twice',async()=>{
  const item=await createProduct('stripe-refund');await core.adminAction('inventory',{variantId:item.variantId,quantity:2,reason:'Sağlayıcı iade durumu testi'},admin);await publish(item.id);
  const cart=token();await core.setCartItem(cart,item.variantId,2);const order=await core.checkout(cart,await quotedInput(cart));const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(event.raw,event.signature);
  // Verified-provider callback simulation only; no external request or real charge.
  await query("UPDATE payments SET provider='stripe',provider_reference='cs_ops_refund' WHERE order_id=$1",[order.orderId]);
  const r=await core.requestReturn(order.orderId,order.trackingToken,{variantId:item.variantId,quantity:1,reason:'Sağlayıcı iade iş akışı',sealIntact:true}) as {id:string};
  await core.adminAction('returns',{action:'review',id:r.id,approved:true,reason:'İade kontrolü uygun bulundu'},admin);await core.adminAction('returns',{action:'receive',id:r.id},admin);await core.adminAction('returns',{action:'inspect',id:r.id,restock:false,reason:'Ayrı karantina incelemesi sürüyor'},admin);
  const requested=await core.adminAction('returns',{action:'refund',id:r.id},admin) as {refundId:string,status:string};assert.equal(requested.status,'refund_pending');assert(requested.refundId);
  assert.equal((await query('SELECT refunded_minor FROM payments WHERE order_id=$1',[order.orderId]))[0].refunded_minor,0);
  assert.equal((await query('SELECT status FROM refunds WHERE id=$1',[requested.refundId]))[0].status,'pending');
  await assert.rejects(()=>core.adminAction('inventory',{action:'release',variantId:item.variantId,quantity:1,reason:'Bekleyen para iadesi karantina bypass'},admin));
  assert.equal((await query("SELECT count(*)::int n FROM jobs WHERE type='refund.stripe' AND dedupe_key=$1",[`refund:${requested.refundId}`]))[0].n,1);
  await core.finalizeProviderRefund(requested.refundId,'re_ops_refund','pending');assert.equal((await query('SELECT refunded_minor FROM payments WHERE order_id=$1',[order.orderId]))[0].refunded_minor,0);
  await assert.rejects(()=>core.finalizeProviderRefund(requested.refundId,'re_other','succeeded'));
  await core.finalizeProviderRefund(requested.refundId,'re_ops_refund','succeeded');const repeat=await core.finalizeProviderRefund(requested.refundId,'re_ops_refund','succeeded');assert.equal(repeat.duplicate,true);
  assert.equal((await query('SELECT refunded_minor FROM payments WHERE order_id=$1',[order.orderId]))[0].refunded_minor,10001);
  assert.equal((await query('SELECT status FROM returns WHERE id=$1',[r.id]))[0].status,'refunded');
 });
 await check('Editing published safety content forces review and revokes eligibility until republished',async()=>{
  const item=await createProduct('review-edit');await core.adminAction('inventory',{variantId:item.variantId,quantity:2,reason:'Yayın sonrası içerik kontrolü'},admin);await publish(item.id);assert(await core.getProduct('ops-review-edit'));
  await core.adminAction('products',{action:'update',id:item.id,care:''},admin);
  assert.equal((await query('SELECT status FROM products WHERE id=$1',[item.id]))[0].status,'review');assert.equal(await core.getProduct('ops-review-edit'),null);
  assert.equal((await query("SELECT approved FROM product_eligibility WHERE variant_id=$1 AND country='TR'",[item.variantId]))[0].approved,false);
  await assert.rejects(()=>publish(item.id));
  await core.adminAction('products',{action:'update',id:item.id,care:'Bakım etiketi doğrulandı.',careEn:'Care label verified.'},admin);assert.equal(await core.getProduct('ops-review-edit'),null);
  await publish(item.id);assert(await core.getProduct('ops-review-edit'));
 });
 await check('Technical variant edits require review while price-only changes preserve publication',async()=>{
  const item=await createProduct('variant-review');await core.adminAction('inventory',{variantId:item.variantId,quantity:2,reason:'Varyant inceleme testi'},admin);await publish(item.id);
  await core.adminAction('variants',{action:'shippingApproval',id:item.variantId,carrier:'Onaylı Taşıyıcı',country:'TR',accepted:true,reference:'Değişiklik öncesi kabul referansı'},admin);
  await core.adminAction('variants',{action:'prices',id:item.variantId,prices:[{currency:'TRY',amountMinor:12500}],reason:'Yalnız fiyat listesi değişikliği'},admin);assert(await core.getProduct('ops-variant-review'));
  await core.adminAction('variants',{action:'update',id:item.variantId,sku:'OPS-NEW-MODEL',name:'Yeni model',nameEn:'New model'},admin);
  assert.equal((await query('SELECT status FROM products WHERE id=$1',[item.id]))[0].status,'review');assert.equal(await core.getProduct('ops-variant-review'),null);
  assert.equal((await query("SELECT approved FROM product_eligibility WHERE variant_id=$1 AND country='TR'",[item.variantId]))[0].approved,false);
  assert.equal((await query('SELECT accepted FROM shipping_approvals WHERE variant_id=$1',[item.variantId]))[0].accepted,false);
  await publish(item.id);
  await core.adminAction('variants',{action:'create',productId:item.id,sku:'OPS-CREATED-MODEL',name:'Ek seçenek',nameEn:'Additional option',priceMinor:15000},admin);
  assert.equal(await core.getProduct('ops-variant-review'),null);
 });
 await check('Production runtime never lists, opens or adds fixture products',async()=>{
  const item=await createProduct('fixture');await core.adminAction('inventory',{variantId:item.variantId,quantity:1,reason:'Yerel örnek testi'},admin);await publish(item.id);await query('UPDATE products SET fixture=true WHERE id=$1',[item.id]);
  process.env.APP_ENV='production';assert.equal(await core.getProduct('ops-fixture'),null);assert(!(await core.listProducts({})).some(p=>p.id===item.id));await assert.rejects(()=>core.setCartItem(token(),item.variantId,1));process.env.APP_ENV='test';
 });
 await check('Bundle component country approval and SKU documents cannot be bypassed through the parent SKU',async()=>{
  const component=await createProduct('document-component'),bundle=await createProduct('document-bundle',30000,6000);
  await core.adminAction('inventory',{variantId:component.variantId,quantity:4,reason:'İzole belge kontrolü bileşen stoğu'},admin);
  await core.adminAction('variants',{action:'bundle',id:bundle.variantId,components:[{variantId:component.variantId,quantity:1}],reason:'Belge kontrolü için fiziksel set tanımı'},admin);await publish(bundle.id);
  const cart=token();await core.setCartItem(cart,bundle.variantId,1);
  const validInput=await quotedInput(cart),checkoutExistingQuote=()=>core.checkout(cart,{...checkoutInput(),quoteToken:validInput.quoteToken});
  await query("DELETE FROM product_eligibility WHERE variant_id=$1 AND country='TR'",[component.variantId]);
  await assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='PRODUCT_NOT_ELIGIBLE');
  await query("INSERT INTO product_eligibility(variant_id,country,approved)VALUES($1,'TR',true)",[component.variantId]);await assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='PRODUCT_NOT_ELIGIBLE');await query("DELETE FROM product_eligibility WHERE variant_id=$1 AND country='TR'",[component.variantId]);
  await query("INSERT INTO product_eligibility(variant_id,country,approved,required_document_kind,review_note,approved_by) VALUES($1,'TR',true,'safety','Yalnız izole bileşen belge testi',$2)",[component.variantId,admin.id]);
  const deniedDocument=()=>assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='DOCUMENT_REQUIRED');
  await deniedDocument();
  await query("INSERT INTO product_documents(variant_id,country,kind,reference,valid_from,valid_until,reviewed) VALUES($1,'TR','safety','Yanlış SKU için izole test belgesi','2000-01-01','2099-12-31',true)",[bundle.variantId]);await deniedDocument();
  const [document]=await query("INSERT INTO product_documents(variant_id,country,kind,reference,valid_from,valid_until,reviewed,reviewed_by) VALUES($1,'TR','safety','Doğru SKU izole test belgesi','2000-01-01','2001-01-01',true,$2) RETURNING id",[component.variantId,admin.id]);await deniedDocument();
  await query("UPDATE product_documents SET valid_until='2099-12-31',reviewed=false WHERE id=$1",[document.id]);await deniedDocument();
  await query("UPDATE product_documents SET reviewed=true,country='GB' WHERE id=$1",[document.id]);await deniedDocument();
  await query("UPDATE product_documents SET country='TR',valid_from='2099-01-01' WHERE id=$1",[document.id]);await deniedDocument();
  await query("UPDATE product_documents SET valid_from='2000-01-01',reference='' WHERE id=$1",[document.id]);await deniedDocument();
  await query("UPDATE product_documents SET reference='Doğru SKU izole test belgesi' WHERE id=$1",[document.id]);
  await query('UPDATE product_documents SET reviewed_by=NULL WHERE id=$1',[document.id]);await deniedDocument();await query('UPDATE product_documents SET reviewed_by=$2 WHERE id=$1',[document.id,admin.id]);
  assert.equal((await query('SELECT status FROM products WHERE id=$1',[component.id]))[0].status,'draft');
  const order=await checkoutExistingQuote();assert.equal((await query('SELECT quantity FROM reservations WHERE order_id=$1 AND variant_id=$2',[order.orderId,component.variantId]))[0].quantity,1);
  await core.adminAction('orders',{action:'cancel',id:order.orderId,reason:'İzole belge akışı sonrasında rezervasyon bırakma'},admin);
  await query('UPDATE variants SET active=false WHERE id=$1',[component.variantId]);await assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='BUNDLE_COMPONENT_UNAVAILABLE');await query('UPDATE variants SET active=true WHERE id=$1',[component.variantId]);
  await query("UPDATE product_eligibility SET approved=false WHERE variant_id=$1 AND country='TR'",[component.variantId]);await assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='PRODUCT_NOT_ELIGIBLE');await query("UPDATE product_eligibility SET approved=true WHERE variant_id=$1 AND country='TR'",[component.variantId]);
  const nested=await createProduct('nested-document-component');await query('INSERT INTO bundle_components(bundle_variant_id,component_variant_id,quantity) VALUES($1,$2,1)',[component.variantId,nested.variantId]);await assert.rejects(checkoutExistingQuote,(error:unknown)=>(error as {code:string}).code==='NESTED_BUNDLE_DISABLED');
  assert.equal((await query('SELECT count(*)::int n FROM orders WHERE cart_id=(SELECT cart_id FROM orders WHERE id=$1)',[order.orderId]))[0].n,1);
 });
 await check('Production rejects a fixture hidden inside a non-fixture approved bundle before creating an order',async()=>{
  const component=await createProduct('production-component'),bundle=await createProduct('production-bundle',30000,6000);
  await core.adminAction('inventory',{variantId:component.variantId,quantity:2,reason:'İzole production guard bileşen stoğu'},admin);await core.adminAction('variants',{action:'bundle',id:bundle.variantId,components:[{variantId:component.variantId,quantity:1}],reason:'Production fixture sınırı testi'},admin);await publish(bundle.id);
  const cart=token();await core.setCartItem(cart,bundle.variantId,1);
  // All records below exist only inside this disposable local operations_test DB.
  for(const key of ['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone','seller.bankAccount'])await query('INSERT INTO settings(key,value) VALUES($1,$2) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[key,JSON.stringify('Yalnız izole guard testi')]);
  for(const key of ['launch.backupVerified','launch.securityReviewed','launch.legalApproved','launch.catalogVerified','launch.providerApproved'])await query("INSERT INTO settings(key,value) VALUES($1,'true'::jsonb) ON CONFLICT(key) DO UPDATE SET value=excluded.value",[key]);
  await query("UPDATE country_rules SET fixture=false WHERE code='TR'");
  const [controller]=await query("INSERT INTO privacy_controllers(version,legal_name,address,email,evidence,status,fixture,created_by) VALUES(1,'Yalnız izole veri sorumlusu','Yalnız izole adres','guard@example.invalid','Yalnız bu geçici DB testi için kanıt','approved',false,$1) RETURNING id",[admin.id]);
  await query("INSERT INTO privacy_policies(controller_id,country,version,unit,period_count,time_zone,source,evidence,retention_note,approved,fixture,approved_by) VALUES($1,'TR',1,'days',30,'Europe/Istanbul','https://example.invalid/guard','Yalnız izole test kanıtı','Bu kayıt gerçek hukuk politikası değildir.',true,false,$2)",[controller.id,admin.id]);
  const previous={appEnv:process.env.APP_ENV,provider:process.env.PAYMENT_PROVIDER,live:process.env.LIVE_SALES_ENABLED};
  try{
   process.env.APP_ENV='production';process.env.PAYMENT_PROVIDER='stripe';process.env.LIVE_SALES_ENABLED='true';
   const {manageAddressProfile}=await import('../src/server/address-profiles');const fields=(await query("SELECT fields FROM country_address_profiles WHERE country='TR' AND status='approved'"))[0].fields;const profile=await manageAddressProfile({action:'create',country:'TR',fields,reference:'Yalnız izole production sınır testi adres alanı kanıtı'},admin);await manageAddressProfile({action:'approve',id:profile.id,reason:'Yalnız izole production sınır testi profil onayı'},admin);
   await query('UPDATE tax_rules SET fixture=false');for(const tax of await query('SELECT id FROM tax_rules'))await query('INSERT INTO settings(key,value)VALUES($1,$2)',[`tax.source.${tax.id}`,JSON.stringify('Yalnız izole production sınır testi vergi kaynağı')]);await query('UPDATE legal_documents SET fixture=false');await query("INSERT INTO shipping_tax_rules(country,rate_bps,reference,valid_from,approved)VALUES('TR',0,'Yalnız izole production sınır testi kargo kaynağı',now()-interval '1 day',true)");
   const beforeFixtureChange=await quotedInput(cart);await query('UPDATE products SET fixture=true WHERE id=$1',[component.id]);
   await assert.rejects(()=>core.checkout(cart,beforeFixtureChange),(error:unknown)=>(error as {code:string}).code==='FIXTURE_NOT_ALLOWED');
  }
  finally{process.env.APP_ENV=previous.appEnv;process.env.PAYMENT_PROVIDER=previous.provider;if(previous.live===undefined)delete process.env.LIVE_SALES_ENABLED;else process.env.LIVE_SALES_ENABLED=previous.live;}
  assert.equal((await query('SELECT count(*)::int n FROM orders WHERE cart_id=(SELECT id FROM carts WHERE token_hash=$1)',[createHash('sha256').update(cart).digest('hex')]))[0].n,0);
 });
 console.log(`Operations integration: ${passed} checks passed.`);
} finally {if(close)await close();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
