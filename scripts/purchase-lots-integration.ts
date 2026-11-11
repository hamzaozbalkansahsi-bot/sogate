/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/purchase-lots-integration.ts
 * Açıklama   : Lotlu satın alma kabulünü yalnız benzersiz yerel test veritabanında doğrular.
 */
import assert from 'node:assert/strict';
import {randomBytes,createHash} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
const source=process.env.TEST_DATABASE_URL;if(!source)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(source);assert(['127.0.0.1','localhost','[::1]'].includes(url.hostname)&&url.pathname.endsWith('_test'),'Yalnız yerel test ortamı.');
const name=`sexsogate_${randomBytes(8).toString('hex')}_purchase_lots_test`;assert.match(name,/^sexsogate_[a-f0-9]{16}_purchase_lots_test$/);
const control=new pg.Client({connectionString:source});await control.connect();let created=false,pool:pg.Pool|undefined,passed=0;
const key=()=>randomBytes(32).toString('hex'),admin={id:'purchase-lots-admin',role:'admin' as const,mfa:true},warehouse={id:'purchase-lots-warehouse',role:'warehouse' as const,mfa:true};
async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 await control.query(`CREATE DATABASE "${name}"`);created=true;url.pathname='/'+name;process.env.DATABASE_URL=url.href;process.env.APP_ENV='test';await migrate(url.href);
 const database=await import('../src/server/db');pool=database.pool;const {query}=database,core=await import('../src/server/commerce');
 await query("INSERT INTO warehouses(id,name)VALUES('main','Ana Depo')");
 const product=async(suffix:string)=>core.adminAction('products',{name:'Lotlu kabul '+suffix,nameEn:'Lot receipt '+suffix,slug:'purchase-lot-'+suffix,category:'aksesuarlar',sku:'PURCHASE-LOT-'+suffix,variantName:'Standart',variantNameEn:'Standard',priceMinor:10000,costMinor:1000,image:'/media/atelier-01.svg',material:'Tekstil',description:'Yalnız izole mal kabul senaryosu.',descriptionEn:'Isolated goods receipt scenario only.',care:'Üretici etiketini izleyin.',careEn:'Follow the manufacturer label.',warnings:'Yalnız yetişkinler için.',warningsEn:'For adults only.'},admin) as Promise<{id:string;variantId:string}>;
 const tracked=await product('tracked'),normal=await product('normal');await core.adminAction('lots',{action:'enable',variantId:tracked.variantId,expiryRequired:true,reason:'İzole lotlu satın alma takip kurulumu',idempotencyKey:key()},admin);
 const supplier=await core.adminAction('suppliers',{name:'Yalnız izole lot tedarikçisi',leadDays:1},admin) as {id:string};
 const purchase=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:tracked.variantId,quantity:8,unitCostMinor:1000},{variantId:normal.variantId,quantity:5,unitCostMinor:1000}]},admin) as {id:string};
 const lot=(lotNumber:string,quantity:number,expiresAt:string|null='2099-01-01',quarantined=false)=>({lotNumber,quantity,expiresAt,quarantined,sourceReference:'Yalnız izole üretici lot etiketi'});
 let receiptId='',early='',late='';
 const receipt={action:'receive',id:purchase.id,idempotencyKey:key(),reason:'Fiilen teslim alınan izole karma kabul',sourceReference:'Yalnız izole teslimat belgesi',items:[{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:3,lots:[lot('EARLY',2),lot('LATE',1,'2099-12-31')]}]};
 await check('Mixed ordinary and tracked SKU receipts close PO remaining quantities and write aggregate stock once',async()=>{
  const result=await core.adminAction('purchases',receipt,warehouse) as {id:string;status:string};assert.equal(result.status,'partially_received');receiptId=result.id;early=String((await query("SELECT id FROM inventory_lots WHERE variant_id=$1 AND lot_number='EARLY'",[tracked.variantId]))[0].id);late=String((await query("SELECT id FROM inventory_lots WHERE variant_id=$1 AND lot_number='LATE'",[tracked.variantId]))[0].id);
  assert.equal((await query("SELECT on_hand FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main'",[tracked.variantId]))[0].on_hand,3);assert.equal((await query('SELECT sum(on_hand)::int n FROM inventory_lot_balances b JOIN inventory_lots l ON l.id=b.lot_id WHERE l.variant_id=$1',[tracked.variantId]))[0].n,3);assert.equal((await query('SELECT received FROM purchase_items WHERE purchase_id=$1 AND variant_id=$2',[purchase.id,tracked.variantId]))[0].received,3);
 });
 const lots=await import('../src/server/commerce/lots');
 const tables=['purchase_orders','purchase_items','purchase_receipts','purchase_receipt_items','purchase_receipt_lots','inventory_balance','inventory_lots','inventory_lot_balances','inventory_movements','lot_operations','audit_log'];
 async function state(){const data:Record<string,unknown>={};for(const table of tables)data[table]=(await query(`SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY to_jsonb(r)::text),'[]'::jsonb) rows FROM ${table} r`))[0].rows;return data;}
 const receive=(items:unknown[],extras:Record<string,unknown>={})=>core.adminAction('purchases',{...receipt,idempotencyKey:key(),items,...extras},warehouse);
 await check('Actor-bound canonical retries and concurrent duplicate receipts never write a second unit',async()=>{
  const before=await state(),reordered={...receipt,items:[...receipt.items].reverse().map(item=>({...item,...('lots'in item?{lots:[...item.lots!].reverse()}:{})}))};
  const repeated=await Promise.all([core.adminAction('purchases',receipt,warehouse),core.adminAction('purchases',reordered,warehouse)]) as {id:string;duplicate:boolean}[];assert(repeated.every(row=>row.id===receiptId&&row.duplicate));
  await assert.rejects(()=>core.adminAction('purchases',{...receipt,sourceReference:'Farklı teslimat kaynağı'},warehouse),{code:'IDEMPOTENCY_CONFLICT'});await assert.rejects(()=>core.adminAction('purchases',receipt,{...warehouse,id:'other-warehouse'}),{code:'IDEMPOTENCY_CONFLICT'});assert.deepEqual(await state(),before);
 });
 await check('Lot lineage contains actual PO and receipt references, safe paging and no costs',async()=>{
  const source=await lots.lotSources(warehouse,early);assert.equal(source.total,1);assert.equal(source.rows[0].receiptId,receiptId);assert.equal(source.rows[0].purchaseId,purchase.id);assert.equal(source.rows[0].supplierName,'Yalnız izole lot tedarikçisi');assert.equal(source.rows[0].quantity,2);assert.equal(source.rows[0].quarantineQuantity,0);
  const empty=await lots.lotSources(warehouse,early,{page:99});assert.equal(empty.total,1);assert.equal(empty.rows.length,0);assert.equal((await lots.lotSources(warehouse,early,{q:'bulunmayan kaynak'})).total,0);
  const purchases=await core.adminList('purchases',warehouse) as {rows:Record<string,unknown>[]};assert(!JSON.stringify(purchases).includes('unitCostMinor'));assert(!JSON.stringify(source).includes('cost'));const item=(purchases.rows.find(row=>row.id===purchase.id)!.items as {variantId:string;lotTracking:boolean;expiryRequired:boolean}[]).find(row=>row.variantId===tracked.variantId)!;assert(item.lotTracking&&item.expiryRequired);
  for(const role of ['support','marketing','customer'] as const)await assert.rejects(()=>lots.lotSources({id:'denied',role,mfa:true},early),{status:403});for(const page of [NaN,Infinity,0,1.5])await assert.rejects(()=>lots.lotSources(warehouse,early,{page}),{code:'INVALID_FILTER'});
 });
 await check('One invalid tracked line rolls back normal stock, lot creation and every PO counter',async()=>{
  const invalid=[
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:2,lots:[lot('BAD-SUM',1)]}],
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:1}],
   [{variantId:normal.variantId,quantity:1,lots:[lot('UNTRACKED',1)]}],
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:1,lots:[lot('NO-DATE',1,null)]}],
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:1,lots:[lot('EXPIRED-GOOD',1,'2000-01-01')]}],
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:1,lots:[lot('EARLY',1,'2098-01-01')]}],
   [{variantId:normal.variantId,quantity:1},{variantId:tracked.variantId,quantity:1,lots:[lot('EARLY',1,'2099-01-01',true)]}],
   [{variantId:tracked.variantId,quantity:6,lots:[lot('OVER',6)]}]
  ];
  for(const items of invalid){const before=await state();await assert.rejects(()=>receive(items));assert.deepEqual(await state(),before);}
  const before=await state();await assert.rejects(()=>core.adminAction('purchases',{action:'receive',id:purchase.id,idempotencyKey:key(),items:[{variantId:normal.variantId,quantity:1}],reason:'Kaynak alanı eksik yeni kabul'},warehouse),{code:'RECEIPT_SOURCE_REQUIRED'});assert.deepEqual(await state(),before);
 });
 await check('Expired goods can be physically received into quarantine and still reduce PO remaining quantity',async()=>{
  await receive([{variantId:normal.variantId,quantity:2},{variantId:tracked.variantId,quantity:2,lots:[lot('EXPIRED-HOLD',1,'2000-01-01',true),lot('MID',1,'2099-06-01')]}]);
  const balance=(await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[tracked.variantId]))[0];assert.deepEqual(balance,{on_hand:4,quarantine:1});assert.equal((await query('SELECT received FROM purchase_items WHERE purchase_id=$1 AND variant_id=$2',[purchase.id,tracked.variantId]))[0].received,5);
  const hold=await query("SELECT l.id FROM inventory_lots l WHERE variant_id=$1 AND lot_number='EXPIRED-HOLD'",[tracked.variantId]);const source=await lots.lotSources(warehouse,hold[0].id);assert.equal(source.rows[0].quantity,1);assert.equal(source.rows[0].quarantineQuantity,1);await assert.rejects(()=>core.adminAction('lots',{action:'release',lotId:hold[0].id,reason:'Tarihi geçmiş lotu açma denemesi',idempotencyKey:key()},warehouse),{code:'LOT_RELEASE_BLOCKED'});
 });
 await check('Direct and purchase receipt keys share one namespace and source types remain distinct',async()=>{
  const before=await state();await assert.rejects(()=>core.adminAction('lots',{action:'receipt',variantId:tracked.variantId,lotNumber:'DUPLICATE-PO',quantity:1,expiresAt:'2100-01-01',sourceReference:'Aynı anahtarı kullanan belge',reason:'Satın alma kabulü anahtarını tekrar kullanma',idempotencyKey:receipt.idempotencyKey},warehouse),{code:'IDEMPOTENCY_CONFLICT'});assert.deepEqual(await state(),before);
  const directKey=key(),direct=await core.adminAction('lots',{action:'receipt',variantId:tracked.variantId,lotNumber:'DIRECT',quantity:1,expiresAt:'2100-01-01',sourceReference:'PO dışı gerçek giriş referansı',reason:'İzole doğrudan belgeli lot girişi',idempotencyKey:directKey},warehouse) as {lotId:string};const directSource=await lots.lotSources(warehouse,direct.lotId);assert.equal(directSource.rows[0].kind,'direct');assert.equal(directSource.rows[0].purchaseId,null);assert.equal(directSource.rows[0].sourceReference,'PO dışı gerçek giriş referansı');
  await assert.rejects(()=>receive([{variantId:tracked.variantId,quantity:1,lots:[lot('DIRECT-AGAIN',1)]}],{idempotencyKey:directKey}),{code:'IDEMPOTENCY_CONFLICT'});
  await query("UPDATE lot_operations SET result=result-'sourceReference' WHERE idempotency_key=$1",[directKey]);assert.equal((await lots.lotSources(warehouse,direct.lotId)).rows[0].sourceReference,null);
 });
 await check('Different command keys cannot over-receive the last remaining PO unit',async()=>{
  const own=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:tracked.variantId,quantity:1,unitCostMinor:1000}]},admin) as {id:string};const before=(await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[tracked.variantId]))[0].on_hand;
  const results=await Promise.allSettled([1,2].map(index=>receive([{variantId:tracked.variantId,quantity:1,lots:[lot('LAST-'+index,1,'2101-01-01')]}],{id:own.id})));assert.equal(results.filter(row=>row.status==='fulfilled').length,1);assert(['OVER_RECEIPT','PURCHASE_NOT_RECEIVABLE'].includes((results.find(row=>row.status==='rejected') as PromiseRejectedResult).reason.code));assert.equal((await query('SELECT received FROM purchase_items WHERE purchase_id=$1',[own.id]))[0].received,1);assert.equal((await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[tracked.variantId]))[0].on_hand,before+1);
 });
 await check('Legacy v1 normal receipts replay only for their original actor and never become a new v2 receipt',async()=>{
  const own=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:normal.variantId,quantity:1,unitCostMinor:1000}]},admin) as {id:string};
  const original={action:'receive',id:own.id,idempotencyKey:key(),items:[{variantId:normal.variantId,quantity:1}],reason:'Yalnız izole eski sürüm kabul kaydı'},hash=createHash('sha256').update(JSON.stringify(original)).digest('hex');
  const [saved]=await query('INSERT INTO purchase_receipts(purchase_id,idempotency_key,request_hash,actor_id,reason)VALUES($1,$2,$3,$4,$5)RETURNING id',[own.id,original.idempotencyKey,hash,warehouse.id,original.reason]);await query('INSERT INTO purchase_receipt_items(receipt_id,variant_id,quantity)VALUES($1,$2,1)',[saved.id,normal.variantId]);await query('UPDATE purchase_items SET received=1 WHERE purchase_id=$1',[own.id]);await query("UPDATE purchase_orders SET status='received' WHERE id=$1",[own.id]);await query('UPDATE inventory_balance SET on_hand=on_hand+1 WHERE variant_id=$1',[normal.variantId]);await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference,actor_id)VALUES($1,'main','purchase_receipt',1,$2,$3,$4)",[normal.variantId,original.reason,'purchase:'+saved.id+':'+normal.variantId,warehouse.id]);
  const before=await state(),result=await core.adminAction('purchases',original,warehouse) as {id:string;duplicate:boolean};assert.equal(result.id,saved.id);assert(result.duplicate);await assert.rejects(()=>core.adminAction('purchases',original,{...warehouse,id:'different-legacy-actor'}),{code:'IDEMPOTENCY_CONFLICT'});await assert.rejects(()=>core.adminAction('purchases',{...original,sourceReference:'Eski işlemi değiştiren kaynak'},warehouse),{code:'IDEMPOTENCY_CONFLICT'});assert.deepEqual(await state(),before);
 });
 await check('Receipt-to-lot and movement foreign keys cannot link another SKU or double a movement',async()=>{
  await assert.rejects(()=>query('UPDATE purchase_receipt_lots SET variant_id=$2 WHERE receipt_id=$1 AND lot_id=$3',[receiptId,normal.variantId,early]),(error:unknown)=>(error as {code:string}).code==='23503');assert.equal((await query('SELECT variant_id FROM purchase_receipt_lots WHERE receipt_id=$1 AND lot_id=$2',[receiptId,early]))[0].variant_id,tracked.variantId);
  await assert.rejects(()=>query('UPDATE purchase_items SET received=quantity+1 WHERE purchase_id=$1',[purchase.id]),(error:unknown)=>(error as {code:string}).code==='23514');
 });
 await check('Direct versus PO concurrent use of one key makes exactly one receipt and one stock increment',async()=>{
  const shared=key(),before=(await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[tracked.variantId]))[0].on_hand;
  const requests=[()=>core.adminAction('lots',{action:'receipt',variantId:tracked.variantId,lotNumber:'CROSS-DIRECT',quantity:1,expiresAt:'2102-01-01',sourceReference:'İzole farklı yol teslimat kaynağı',reason:'İzole ortak kabul anahtarı yarışı',idempotencyKey:shared},warehouse),()=>receive([{variantId:tracked.variantId,quantity:1,lots:[lot('CROSS-PURCHASE',1,'2102-01-01')]}],{idempotencyKey:shared})];
  const results=await Promise.allSettled(requests.map(work=>work()));assert.equal(results.filter(row=>row.status==='fulfilled').length,1);assert.equal((results.find(row=>row.status==='rejected') as PromiseRejectedResult).reason.code,'IDEMPOTENCY_CONFLICT');assert.equal((await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[tracked.variantId]))[0].on_hand,before+1);
 });
 await check('Warehouse cannot create purchases, catalog or finance cannot receive, and failed roles write nothing',async()=>{
  const before=await state();await assert.rejects(()=>core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:tracked.variantId,quantity:1,unitCostMinor:1}]},warehouse),{status:403});
  for(const principal of [{id:'catalog',role:'catalog' as const,mfa:true},{id:'finance',role:'finance' as const,mfa:true},{...warehouse,mfa:false}])await assert.rejects(()=>core.adminAction('purchases',{...receipt,idempotencyKey:key()},principal),{status:403});assert.deepEqual(await state(),before);
 });
 await check('One producer lot retains every distinct PO source without rewriting its first reference',async()=>{
  const own=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:tracked.variantId,quantity:1,unitCostMinor:1000}]},admin) as {id:string};const [prior]=await query('SELECT source_reference FROM inventory_lots WHERE id=$1',[early]);
  const result=await receive([{variantId:tracked.variantId,quantity:1,lots:[{...lot('EARLY',1),sourceReference:'İkinci kabul üretici belge referansı'}]}],{id:own.id,sourceReference:'İkinci satın alma teslimat belgesi'}) as {id:string};assert.equal((await query('SELECT source_reference FROM inventory_lots WHERE id=$1',[early]))[0].source_reference,prior.source_reference);
  const sources=await lots.lotSources(warehouse,early);assert.equal(sources.total,2);const next=sources.rows.find(row=>row.receiptId===result.id)!;assert.equal(next.purchaseId,own.id);assert.equal(next.quantity,1);assert.equal(next.sourceReference,'İkinci kabul üretici belge referansı');assert.equal(next.receiptSourceReference,'İkinci satın alma teslimat belgesi');assert.equal((await lots.lotSources(warehouse,early,{q:'İkinci satın alma teslimat belgesi'})).total,1);assert(sources.rows.some(row=>row.receiptId===receiptId&&row.quantity===2));
 });
 await check('FEFO consumes PO-received lot stock and recall retains real PO/source lineage',async()=>{
  process.env.PAYMENT_PROVIDER='test';process.env.PAYMENT_WEBHOOK_SECRET=key();await query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture)VALUES('TR','Yalnız izole kabul test ülkesi',true,true,true,true,true,true,true,0,'TRY',true)");const {seedFixtureAddressProfile}=await import('./seed');await seedFixtureAddressProfile(pool!);await query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture)VALUES('TR',2000,'2026-01-01',true)");
  for(const kind of ['privacy','terms']){const body='Yalnız izole lotlu satın alma ve FEFO testinin sözleşme kaydıdır.';await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture)VALUES($1,'tr',$1,$2,1,'effective',$3,now(),true)",[kind,body,createHash('sha256').update(body).digest('hex')]);}
  await query('UPDATE products SET fixture=true WHERE id=$1',[tracked.id]);const {complianceAction}=await import('../src/server/compliance');await complianceAction({action:'eligibility',variantId:tracked.variantId,country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole kabul FEFO ülke incelemesi',idempotencyKey:key()},admin);await core.adminAction('products',{action:'publish',id:tracked.id,country:'TR',reviewNote:'Yalnız izole stok kaynağı testi'},admin);
  const cart=key();await core.setCartItem(cart,tracked.variantId,3);const quote=await core.quoteCheckout(cart,{country:'TR',currency:'TRY',locale:'tr'});const order=await core.checkout(cart,{quoteToken:quote.quoteToken,email:'receipt@example.invalid',fullName:'Hamza ÖZBALKAN',phone:'05000000000',line1:'Şişli Çeşme Sokak 12',city:'İstanbul',postalCode:'34000',country:'TR',currency:'TRY',locale:'tr',idempotencyKey:key(),privacyAccepted:true,termsAccepted:true});
  const allocations=await query('SELECT rl.lot_id,rl.quantity FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.order_id=$1',[order.orderId]);assert.deepEqual(allocations,[{lot_id:early,quantity:3}]);const payment=await core.createTestPaymentEvent(order.orderId,order.trackingToken,'succeeded');await core.handlePayment(payment.raw,payment.signature);assert.equal((await query('SELECT on_hand FROM inventory_lot_balances WHERE lot_id=$1',[early]))[0].on_hand,0);
  const source=await lots.lotSources(warehouse,early);assert.equal(source.total,2);assert(source.rows.some(row=>row.receiptId===receiptId&&row.purchaseId===purchase.id));await core.adminAction('lots',{action:'recall',lotId:early,reference:'Yalnız izole üretici geri çağırma kararı',reason:'İzole satın alma kaynak izinin korunması',idempotencyKey:key()},warehouse);assert((await lots.recallOrders(early,warehouse)).rows.some(row=>row.id===order.orderId));const before=await state();await assert.rejects(()=>receive([{variantId:tracked.variantId,quantity:1,lots:[lot('EARLY',1)]}]),{code:'LOT_RECALLED'});assert.deepEqual(await state(),before);
 });
 await check('Final physical acceptance closes every remaining PO line without altering prior lot identities',async()=>{
  const lines=await query('SELECT variant_id,quantity-received remaining FROM purchase_items WHERE purchase_id=$1',[purchase.id]);const items=lines.filter(row=>row.remaining>0).map(row=>({variantId:row.variant_id,quantity:row.remaining,...(row.variant_id===tracked.variantId?{lots:[lot('COMPLETE',row.remaining,'2103-01-01')]}:{})}));await receive(items);assert.equal((await query('SELECT status FROM purchase_orders WHERE id=$1',[purchase.id]))[0].status,'received');assert((await query('SELECT received,quantity FROM purchase_items WHERE purchase_id=$1',[purchase.id])).every(row=>row.received===row.quantity));assert.equal((await query('SELECT lot_number FROM inventory_lots WHERE id=$1',[late]))[0].lot_number,'LATE');
 });
 console.log(`Purchase lot integration: ${passed} checks passed.`);
}finally{await pool?.end();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
