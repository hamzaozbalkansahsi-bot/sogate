/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/lot-integration.ts
 * Açıklama   : İzole veritabanında lot, FEFO, geri çağırma ve rezervasyon tutarlılığını sınar.
 */
import assert from 'node:assert/strict';
import {randomBytes,createHash} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
import {seedFixtureAddressProfile} from './seed';
const source=process.env.TEST_DATABASE_URL;if(!source)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(source);assert(['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&url.pathname.endsWith('_test'),'Yalnız yerel test ortamı.');
const name=`sexsogate_${randomBytes(8).toString('hex')}_lot_test`;assert.match(name,/^sexsogate_[a-f0-9]{16}_lot_test$/);
const control=new pg.Client({connectionString:source});await control.connect();let created=false,pool:pg.Pool|undefined,passed=0;
const token=()=>randomBytes(32).toString('hex');
const admin={id:'lot-admin',role:'admin' as const,mfa:true},warehouse={id:'lot-warehouse',role:'warehouse' as const,mfa:true};
async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 await control.query(`CREATE DATABASE "${name}"`);created=true;url.pathname='/'+name;process.env.DATABASE_URL=url.href;process.env.APP_ENV='test';process.env.PAYMENT_PROVIDER='test';process.env.PAYMENT_WEBHOOK_SECRET=randomBytes(32).toString('hex');
 await migrate(url.href);const database=await import('../src/server/db');pool=database.pool;const {query}=database;const core=await import('../src/server/commerce');const {complianceAction}=await import('../src/server/compliance');
 await query("INSERT INTO warehouses(id,name) VALUES('main','Ana Depo')");
 await query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES('TR','Türkiye',true,true,true,true,true,true,true,0,'TRY',true)");
 await seedFixtureAddressProfile(pool!);
 await query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture) VALUES('TR',2000,now()-interval '1 day',true)");
 for(const kind of ['privacy','terms']){const body='Yalnız izole lot testi sözleşmesi.';await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture) VALUES($1,'tr',$1,$2,1,'effective',$3,now(),true)",[kind,body,createHash('sha256').update(body).digest('hex')]);}
 const product=async(suffix:string)=>await core.adminAction('products',{name:`Lot doğrulama ${suffix}`,nameEn:`Lot verification ${suffix}`,slug:`lot-${suffix}`,category:'aksesuarlar',description:'Yalnız izole lot senaryosu.',descriptionEn:'Isolated lot scenario only.',sku:`LOT-${suffix}`,variantName:'Standart',variantNameEn:'Standard',priceMinor:10000,costMinor:1000,image:'/media/atelier-01.svg',warnings:'Yalnız yetişkinler için.',warningsEn:'For adults only.',care:'Etiketi izleyin.',careEn:'Follow the label.'},admin) as {id:string,variantId:string};
 const a=await product('a');
 await check('Tracking can be enabled only through an authorized empty-stock action',async()=>{
  await core.adminAction('lots',{action:'enable',variantId:a.variantId,expiryRequired:true,idempotencyKey:token(),reason:'Belgeye dayalı lot takibi kurulumu'},admin);
  assert.equal((await query('SELECT lot_tracking,expiry_required FROM variants WHERE id=$1',[a.variantId]))[0].lot_tracking,true);
  await assert.rejects(()=>core.adminAction('lots',{action:'enable',variantId:a.variantId,expiryRequired:true,idempotencyKey:token(),reason:'Yetkisiz lot takibi denemesi'},{id:'m',role:'marketing',mfa:true}));
 });
 const {variantAvailability}=await import('../src/server/commerce/catalog');
 const {recallOrders,unknownLotReturns}=await import('../src/server/commerce/lots');
 const enable=async(variantId:string,expiryRequired=true)=>core.adminAction('lots',{action:'enable',variantId,expiryRequired,idempotencyKey:token(),reason:'İzole lot takipli stok kurulumu'},admin);
 const receipt=async(variantId:string,lotNumber:string,quantity:number,expiresAt:string|null='2099-12-31',quarantined=false)=>await core.adminAction('lots',{action:'receipt',variantId,lotNumber,quantity,expiresAt,quarantined,sourceReference:'Yalnız izole test mal kabul belgesi',reason:'İzole mal kabulü kontrolü',idempotencyKey:token()},warehouse) as {lotId:string};
 const publish=async(id:string)=>{const ids=await query('SELECT id FROM variants WHERE product_id=$1 AND active UNION SELECT bc.component_variant_id id FROM bundle_components bc JOIN variants v ON v.id=bc.bundle_variant_id WHERE v.product_id=$1',[id]);for(const row of ids)await complianceAction({action:'eligibility',variantId:row.id,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole lot testi ön incelemesi',idempotencyKey:token()},admin);return core.adminAction('products',{action:'publish',id,country:'TR',reviewNote:'Yalnız izole lot testi'},admin);};
 const input=()=>({email:'lot@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme İç Giyim Ölçü ve Özellikler',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr' as const,currency:'TRY' as const,idempotencyKey:token(),privacyAccepted:true,termsAccepted:true});
 const quotedInput=async(cart:string)=>{const data=input();const quote=await core.quoteCheckout(cart,{country:data.country,currency:data.currency,locale:data.locale});return {...data,quoteToken:quote.quoteToken};};
 const buy=async(variantId:string,quantity=1)=>{const cart=token();await core.setCartItem(cart,variantId,quantity);return core.checkout(cart,await quotedInput(cart));};
 const pay=async(order:{orderId:string;trackingToken:string},status:'succeeded'|'failed'='succeeded')=>{const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,status);await core.handlePayment(event.raw,event.signature);return event;};
 let early='',late='';
 await check('Receipts are idempotent, documented, date-validated and update aggregate stock only once',async()=>{
  const request={action:'receipt',variantId:a.variantId,lotNumber:'TEST-LATE',quantity:3,expiresAt:'2099-12-31',sourceReference:'Yalnız izole mal kabul belgesi',reason:'Lot mal kabulü tekrar denetimi',idempotencyKey:token()};
  const results=await Promise.all([core.adminAction('lots',request,warehouse),core.adminAction('lots',request,warehouse)]) as {lotId:string}[];late=results[0].lotId;assert.equal(results[0].lotId,results[1].lotId);
  early=(await receipt(a.variantId,'TEST-EARLY',2,'2099-01-01')).lotId;
  await receipt(a.variantId,'TEST-EXPIRED',3,'2000-01-01',true);
  await assert.rejects(()=>core.adminAction('lots',{...request,quantity:99},warehouse),(e:unknown)=>(e as {code:string}).code==='IDEMPOTENCY_CONFLICT');
  await assert.rejects(()=>core.adminAction('lots',{...request,lotNumber:'NO-DATE',expiresAt:null,idempotencyKey:token()},warehouse));
  await assert.rejects(()=>core.adminAction('lots',{...request,lotNumber:'PAST',expiresAt:'2000-01-01',idempotencyKey:token()},warehouse));
  await assert.rejects(()=>core.adminAction('lots',{...request,expiresAt:'2098-01-01',idempotencyKey:token()},warehouse));
  const [balance]=await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[a.variantId]);assert.equal(balance.on_hand,5);assert.equal(balance.quarantine,3);
  assert.equal((await query("SELECT sum(quantity)::int n FROM inventory_movements WHERE variant_id=$1 AND type='lot_receipt'",[a.variantId]))[0].n,5);
  assert.equal(await variantAvailability(a.variantId),5);
 });
 await check('Generic stock/purchase paths cannot bypass tracking, and existing stock cannot be silently attributed',async()=>{
  await assert.rejects(()=>core.adminAction('inventory',{variantId:a.variantId,quantity:1,reason:'Lot gerektiren giriş'},warehouse));
  await assert.rejects(()=>core.adminAction('inventory',{action:'adjustment',variantId:a.variantId,quantity:9,reason:'Lot gerektiren düzeltme'},warehouse));
  const untracked=await product('untracked');await core.adminAction('inventory',{variantId:untracked.variantId,quantity:1,reason:'İzole normal stok girişi'},warehouse);
  await assert.rejects(()=>enable(untracked.variantId),(e:unknown)=>(e as {code:string}).code==='LOT_ATTRIBUTION_REQUIRED');
  const supplier=await core.adminAction('suppliers',{name:'İzole Lot Tedarikçisi',leadDays:1},admin) as {id:string};
  const purchase=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:a.variantId,quantity:2,unitCostMinor:1000}]},admin) as {id:string};
  await assert.rejects(()=>core.adminAction('purchases',{action:'receive',sourceReference:'Yalnız izole mal kabul teslimat belgesi',id:purchase.id,idempotencyKey:token(),items:[{variantId:a.variantId,quantity:1}],reason:'Lot bilgisi olmayan mal kabulü'},warehouse));
  assert.equal((await query('SELECT received FROM purchase_items WHERE purchase_id=$1',[purchase.id]))[0].received,0);
 });
 await publish(a.id);let paid:Awaited<ReturnType<typeof buy>>;
 await check('FEFO reservations span the earliest lots and payment consumes immutable allocations exactly once',async()=>{
  paid=await buy(a.variantId,3);
  const allocations=await query('SELECT rl.lot_id,rl.quantity FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.order_id=$1 ORDER BY rl.lot_id',[paid.orderId]);
  assert.equal(allocations.find(x=>x.lot_id===early)?.quantity,2);assert.equal(allocations.find(x=>x.lot_id===late)?.quantity,1);
  assert.equal(await variantAvailability(a.variantId),2);
  const event=await pay(paid);await core.handlePayment(event.raw,event.signature);
  assert.equal((await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[a.variantId]))[0].on_hand,2);
  assert.equal((await query('SELECT on_hand FROM inventory_lot_balances WHERE lot_id=$1',[early]))[0].on_hand,0);
  assert.equal((await query("SELECT sum(quantity)::int n,count(*)::int movements FROM inventory_movements WHERE variant_id=$1 AND type='sale'",[a.variantId]))[0].n,-3);
  assert.equal((await query("SELECT count(*)::int n FROM inventory_movements WHERE variant_id=$1 AND type='sale' AND lot_id IS NULL",[a.variantId]))[0].n,0);
 });
 await check('Tracked bundle components reserve and consume physical lots; unknown return lots stay separate and unsellable',async()=>{
  const bundle=await product('bundle'),part=await product('part');await core.adminAction('inventory',{variantId:part.variantId,quantity:2,reason:'İzole set bileşeni stoğu'},warehouse);
  await complianceAction({action:'eligibility',variantId:part.variantId,country:'TR',approved:true,requiredDocumentKind:null,reason:'İzole fiziksel set bileşeni ülke incelemesi',idempotencyKey:token()},admin);
  await core.adminAction('variants',{action:'bundle',id:bundle.variantId,components:[{variantId:a.variantId,quantity:2},{variantId:part.variantId,quantity:1}],reason:'Lot takipli set bileşeni kontrolü'},admin);await publish(bundle.id);
  const order=await buy(bundle.variantId);await pay(order);assert.equal(await variantAvailability(a.variantId),0);
  const r=await core.requestReturn(order.orderId,order.trackingToken,{variantId:bundle.variantId,quantity:1,reason:'Lotu doğrulanmamış kapalı set iadesi',sealIntact:true}) as {id:string};
  await core.adminAction('returns',{action:'review',id:r.id,approved:true,reason:'İzole iade incelemesi'},admin);await core.adminAction('returns',{action:'receive',id:r.id},warehouse);
  await assert.rejects(()=>core.adminAction('returns',{action:'inspect',id:r.id,restock:true,reason:'Mühür kapalı fakat lot doğrulanmadı'},warehouse));
  await assert.rejects(()=>core.adminAction('inventory',{action:'release',variantId:a.variantId,quantity:2,reason:'Lot atlatma denemesi'},warehouse));
  await core.adminAction('returns',{action:'inspect',id:r.id,restock:false,reason:'Lot doğrulanana kadar ayrı iade karantinası'},warehouse);
  assert.equal((await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[a.variantId]))[0].quarantine,5);
  assert.equal((await query('SELECT sum(quarantine)::int n FROM inventory_lot_balances b JOIN inventory_lots l ON l.id=b.lot_id WHERE l.variant_id=$1',[a.variantId]))[0].n,3);
  assert.equal((await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[bundle.variantId]))[0].on_hand,0);
  const holds=await unknownLotReturns(warehouse,{q:'LOT-a'});assert.equal(holds.total,1);assert.equal(holds.rows[0].quantity,2);assert(!JSON.stringify(holds).includes('lot@example.invalid'));
 });
 await check('The last lot cannot be oversold by concurrent checkouts and failed/expired reservations release their allocations',async()=>{
  const last=await product('last');await enable(last.variantId);await receipt(last.variantId,'LAST',1);await publish(last.id);
  const cartA=token(),cartB=token();await Promise.all([core.setCartItem(cartA,last.variantId,1),core.setCartItem(cartB,last.variantId,1)]);
  const [inputA,inputB]=await Promise.all([quotedInput(cartA),quotedInput(cartB)]);
  const results=await Promise.allSettled([core.checkout(cartA,inputA),core.checkout(cartB,inputB)]);assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
  const order=(results.find(x=>x.status==='fulfilled') as PromiseFulfilledResult<Awaited<ReturnType<typeof buy>>>).value;assert.equal(await variantAvailability(last.variantId),0);await pay(order,'failed');assert.equal(await variantAvailability(last.variantId),1);
  const expired=await buy(last.variantId);await query("UPDATE orders SET expires_at=now()-interval '1 second' WHERE id=$1",[expired.orderId]);await query("UPDATE reservations SET expires_at=now()-interval '1 second' WHERE order_id=$1",[expired.orderId]);await core.expireReservations();assert.equal(await variantAvailability(last.variantId),1);
  await pay(expired);assert.equal((await query('SELECT status FROM orders WHERE id=$1',[expired.orderId]))[0].status,'payment_exception');assert.equal(await variantAvailability(last.variantId),1);
 });
 await check('Lot expiry between checkout and payment produces an exception without consuming or moving negative stock',async()=>{
  const expiring=await product('expiring');await enable(expiring.variantId);const lot=await receipt(expiring.variantId,'EXPIRING',1);await publish(expiring.id);const order=await buy(expiring.variantId);
  await query("UPDATE inventory_lots SET expires_at=current_date-1 WHERE id=$1",[lot.lotId]);assert.equal(await variantAvailability(expiring.variantId),0);await pay(order);
  assert.equal((await query('SELECT status FROM orders WHERE id=$1',[order.orderId]))[0].status,'payment_exception');assert.equal((await query('SELECT on_hand FROM inventory_lot_balances WHERE lot_id=$1',[lot.lotId]))[0].on_hand,1);
  assert.equal((await query("SELECT details->>'reason' reason FROM order_history WHERE order_id=$1 AND to_status='payment_exception'",[order.orderId]))[0].reason,'lot_unavailable');
 });
 await check('Recall links paid orders, holds remaining physical stock and blocks shipment and release',async()=>{
  const recalled=await product('recall');await enable(recalled.variantId);const lot=await receipt(recalled.variantId,'RECALL',3);await publish(recalled.id);const order=await buy(recalled.variantId);await pay(order);
  await core.adminAction('lots',{action:'recall',lotId:lot.lotId,reference:'Yalnız izole geri çağırma kararı',reason:'İzole güvenlik incelemesi',idempotencyKey:token()},warehouse);
  assert.equal(await variantAvailability(recalled.variantId),0);const [b]=await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[recalled.variantId]);assert.equal(b.on_hand,0);assert.equal(b.quarantine,2);
  const report=await recallOrders(lot.lotId,warehouse);assert.equal(report.rows[0].id,order.orderId);assert.equal(report.rows[0].quantity,1);assert(!JSON.stringify(report).includes('lot@example.invalid'));assert(!JSON.stringify(report).includes('costMinor'));
  await assert.rejects(()=>core.adminAction('shipments',{orderId:order.orderId,carrier:'Yerel doğrulama taşıyıcısı',trackingNumber:'LOCAL-REAL-FIELD-ONLY-123'},warehouse),(e:unknown)=>(e as {code:string}).code==='LOT_SHIPMENT_BLOCKED');
  await assert.rejects(()=>core.adminAction('lots',{action:'release',lotId:lot.lotId,reason:'Geri çağırma durumu atlatılamaz',idempotencyKey:token()},warehouse));
 });
 await check('Recalling an allocated lot before payment fails closed and quarantine/release is idempotent',async()=>{
  const pending=await product('pending');await enable(pending.variantId);const lot=await receipt(pending.variantId,'PENDING',2);await publish(pending.id);const order=await buy(pending.variantId);
  await core.adminAction('lots',{action:'recall',lotId:lot.lotId,reference:'İzole ikinci geri çağırma kararı',reason:'Rezervasyon sonrası lot incelemesi',idempotencyKey:token()},warehouse);await pay(order);assert.equal((await query('SELECT status FROM orders WHERE id=$1',[order.orderId]))[0].status,'payment_exception');
  const other=await product('quarantine');await enable(other.variantId);const safe=await receipt(other.variantId,'SAFE',2);
  const move={action:'quarantine',lotId:safe.lotId,reason:'Belge incelemesi için ayırma',idempotencyKey:token()};await Promise.all([core.adminAction('lots',move,warehouse),core.adminAction('lots',move,warehouse)]);assert.equal(await variantAvailability(other.variantId),0);
  const release={action:'release',lotId:safe.lotId,reason:'İzole belge incelemesi tamamlandı',idempotencyKey:token()};await Promise.all([core.adminAction('lots',release,warehouse),core.adminAction('lots',release,warehouse)]);assert.equal(await variantAvailability(other.variantId),2);
 });
 await check('Warehouse lot reports expose no financial/PII data and generic inventory uses usable lot availability',async()=>{
  const lots=await core.adminList('lots',warehouse) as {rows:Record<string,unknown>[]};assert(lots.rows.length>0);assert(lots.rows.every(r=>!('costMinor'in r)&&!('email'in r)));
  await assert.rejects(()=>core.adminList('lots',{id:'m',role:'marketing',mfa:true}));
  const inventory=await core.adminList('inventory',warehouse,{q:'LOT-expiring'}) as {rows:Record<string,unknown>[]};assert.equal(inventory.rows[0].available,0);
  const [negative]=await query('SELECT count(*)::int n FROM inventory_lot_balances WHERE on_hand<0 OR quarantine<0');assert.equal(negative.n,0);
 });
 await check('Undated optional-expiry lots follow dated lots and SKU safety stock is applied once',async()=>{
  const optional=await product('optional');await enable(optional.variantId,false);const undated=await receipt(optional.variantId,'UNDATED',1,null);const dated=await receipt(optional.variantId,'DATED',1,'2099-01-01');await publish(optional.id);
  await query('UPDATE inventory_balance SET safety_stock=1 WHERE variant_id=$1',[optional.variantId]);assert.equal(await variantAvailability(optional.variantId),1);
  const order=await buy(optional.variantId);const rows=await query('SELECT rl.lot_id FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.order_id=$1',[order.orderId]);assert.equal(rows[0].lot_id,dated.lotId);assert.notEqual(rows[0].lot_id,undated.lotId);await pay(order);assert.equal(await variantAvailability(optional.variantId),0);
 });
 console.log(`Lot integration: ${passed} checks passed.`);
}finally{await pool?.end();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
