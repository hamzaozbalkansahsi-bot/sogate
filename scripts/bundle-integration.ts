/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/bundle-integration.ts
 * Açıklama   : Sürümlü set düzenleme, stok ve onay sınırlarını benzersiz yerel veritabanında doğrular.
 */
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
import type {Connection} from '../src/server/db';
const source=process.env.TEST_DATABASE_URL;if(!source)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(source);assert(['127.0.0.1','localhost','[::1]'].includes(url.hostname)&&url.pathname.endsWith('_test'),'Yalnız yerel test ortamı.');
const name=`sexsogate_${randomBytes(8).toString('hex')}_bundle_test`;assert.match(name,/^sexsogate_[a-f0-9]{16}_bundle_test$/);
const control=new pg.Client({connectionString:source});await control.connect();let created=false,pool:pg.Pool|undefined,passed=0;
const admin={id:'bundle-admin',role:'admin' as const,mfa:true},catalog={id:'bundle-catalog',role:'catalog' as const,mfa:true};
async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 await control.query(`CREATE DATABASE "${name}"`);created=true;url.pathname='/'+name;process.env.DATABASE_URL=url.href;process.env.APP_ENV='test';await migrate(url.href);
 const database=await import('../src/server/db');pool=database.pool;const {query}=database,core=await import('../src/server/commerce');const {complianceAction}=await import('../src/server/compliance');
 await query("INSERT INTO categories(slug,name,name_en) VALUES('bundle-fixture','İzole Set','Isolated Set')");await query("INSERT INTO warehouses(id,name) VALUES('main','Ana Depo')");await query("INSERT INTO country_rules(code,name) VALUES('TR','Türkiye')");
 async function fixture(suffix:string,quantity=0,published=false){
  const [product]=await query("INSERT INTO products(slug,name,name_en,description,description_en,category,image,status,fixture) VALUES($1,$2,$3,'Yalnız izole set testi.','Isolated bundle test only.','bundle-fixture','/media/atelier-01.svg',$4,true) RETURNING id",['bundle-'+suffix,'Set doğrulama '+suffix,'Bundle verification '+suffix,published?'published':'draft']);
  const [variant]=await query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor) VALUES($1,$2,'Standart','Standard',10000,1000) RETURNING id",[product.id,'BUNDLE-'+suffix]);
  await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',$2)",[variant.id,quantity]);if(quantity)await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference) VALUES($1,'main','receipt',$2,'İzole set testi mal kabulü',$3)",[variant.id,quantity,'bundle-fixture:'+variant.id]);
  return {id:product.id,variantId:variant.id};
 }
 const parent=await fixture('parent',0,true),a=await fixture('a',3),b=await fixture('b',4);
 for(const item of [parent,a,b])await complianceAction({action:'eligibility',variantId:item.variantId,country:'TR',approved:true,requiredDocumentKind:null,reason:'İzole set başlangıç ülke incelemesi',idempotencyKey:randomBytes(32).toString('hex')},admin);
 const [parentDocument]=await query("INSERT INTO product_documents(variant_id,country,kind,reference,valid_from,reviewed,created_by,reviewed_by,reviewed_at) VALUES($1,'TR','safety','Yalnız izole üst set belgesi','2000-01-01',true,$2,$2,now()) RETURNING id",[parent.variantId,admin.id]);
 const [componentDocument]=await query("INSERT INTO product_documents(variant_id,country,kind,reference,valid_from,reviewed,created_by,reviewed_by,reviewed_at) VALUES($1,'TR','safety','Yalnız izole fiziksel bileşen belgesi','2000-01-01',true,$2,$2,now()) RETURNING id",[a.variantId,admin.id]);
 await query("INSERT INTO shipping_approvals(variant_id,carrier,country,accepted,reviewed_by,reference) VALUES($1,'local','TR',true,$2,'İzole üst set taşıma incelemesi')",[parent.variantId,admin.id]);
 type View=import('../src/shared/bundle-management').BundleEditorData;
 type Preview=import('../src/shared/bundle-management').BundlePreview;
 const view=()=>core.adminList('variants',catalog,{view:'bundle',id:parent.variantId}) as Promise<View>;
 const change=(components:{variantId:string;quantity:number}[],expectedVersion?:number)=>({action:'bundle',id:parent.variantId,components,reason:'İzole sürümlü set tanımı incelemesi',...(expectedVersion===undefined?{}:{expectedVersion})});
 await check('Changing a published set definition requires a fresh publication and country review',async()=>{
  await core.adminAction('variants',{action:'bundle',id:parent.variantId,components:[{variantId:a.variantId,quantity:1}],reason:'Yeni fiziksel set içeriği incelemesi'},catalog);
  assert.equal((await query('SELECT status FROM products WHERE id=$1',[parent.id]))[0].status,'review');
  assert.equal((await query("SELECT approved FROM product_eligibility WHERE variant_id=$1 AND country='TR'",[parent.variantId]))[0].approved,false);
  assert.equal((await query('SELECT reviewed FROM product_documents WHERE id=$1',[parentDocument.id]))[0].reviewed,false);assert.equal((await query('SELECT reviewed FROM product_documents WHERE id=$1',[componentDocument.id]))[0].reviewed,true);
  assert.equal((await query('SELECT accepted FROM shipping_approvals WHERE variant_id=$1',[parent.variantId]))[0].accepted,false);
  assert.equal((await query('SELECT cost_minor,price_minor,bundle_version FROM variants WHERE id=$1',[parent.variantId]))[0].cost_minor,1000);assert.equal((await view()).version,1);
 });
 await check('Current composition and physical SKU search expose no costs to catalog or warehouse',async()=>{
  const data=await view();assert.equal(data.components[0].variantId,a.variantId);assert.equal(data.components[0].available,3);assert.equal(data.capacity,3);assert(data.canWrite);assert.equal(data.history.length,1);
  const warehouse=await core.adminList('variants',{id:'w',role:'warehouse',mfa:true},{view:'bundle',id:parent.variantId}) as View;assert(!warehouse.canWrite);assert(!JSON.stringify(warehouse).includes('costMinor'));
  const candidates=await core.adminList('variants',catalog,{view:'bundleCandidates',exclude:parent.variantId,q:'BUNDLE-b'}) as {rows:Record<string,unknown>[],total:number};assert.equal(candidates.total,1);assert.equal(candidates.rows[0].id,b.variantId);assert(!JSON.stringify(candidates).includes('costMinor'));
  await assert.rejects(()=>core.adminList('variants',{id:'m',role:'marketing',mfa:true},{view:'bundle',id:parent.variantId}));
 });
 await check('Preview validates the real difference and capacity without writing stock, history, price or approvals',async()=>{
  const balances=JSON.stringify(await query('SELECT * FROM inventory_balance ORDER BY variant_id')),before=(await view()).history.length;
  await assert.rejects(()=>core.adminAction('variants',{...change([{variantId:b.variantId,quantity:2}],1),action:'bundlePreview'},catalog),(error:unknown)=>(error as {code:string}).code==='INVALID_BUNDLE');
  const preview=await core.adminAction('variants',{action:'bundlePreview',id:parent.variantId,expectedVersion:1,components:[{variantId:b.variantId,quantity:2}]},catalog) as Preview;
  assert.equal(preview.capacityBefore,3);assert.equal(preview.capacityAfter,2);assert.equal(preview.changes.length,2);assert(preview.hasChanges);
  assert.equal((await view()).version,1);assert.equal((await view()).history.length,before);assert.equal(JSON.stringify(await query('SELECT * FROM inventory_balance ORDER BY variant_id')),balances);
 });
 await check('Save records a versioned before/after history and rejects stale or omitted later versions',async()=>{
  const data=await core.adminAction('variants',change([{variantId:b.variantId,quantity:2}],1),catalog) as {version:number};assert.equal(data.version,2);
  const latest=await view();assert.equal(latest.components[0].variantId,b.variantId);assert.equal(latest.history[0].before[0].variantId,a.variantId);assert.equal(latest.history[0].after[0].quantity,2);
  await assert.rejects(()=>core.adminAction('variants',change([{variantId:a.variantId,quantity:1}],1),catalog),(e:unknown)=>(e as {code:string}).code==='BUNDLE_VERSION_CONFLICT');
  await assert.rejects(()=>core.adminAction('variants',change([{variantId:a.variantId,quantity:1}]),catalog),(e:unknown)=>(e as {code:string}).code==='BUNDLE_VERSION_CONFLICT');
  await assert.rejects(()=>core.adminAction('variants',change([{variantId:b.variantId,quantity:2}],2),catalog),(e:unknown)=>(e as {code:string}).code==='NO_BUNDLE_CHANGES');
 });
 await check('Concurrent editors cannot overwrite the same expected version',async()=>{
  const results=await Promise.allSettled([core.adminAction('variants',change([{variantId:a.variantId,quantity:2}],2),catalog),core.adminAction('variants',change([{variantId:b.variantId,quantity:3}],2),catalog)]);
  assert.equal(results.filter(result=>result.status==='fulfilled').length,1);assert.equal((results.find(result=>result.status==='rejected') as PromiseRejectedResult).reason.code,'BUNDLE_VERSION_CONFLICT');
  assert.equal((await view()).version,3);assert.equal((await query('SELECT count(*)::int n FROM bundle_changes WHERE variant_id=$1',[parent.variantId]))[0].n,3);
 });
 await check('Physical parent stock, quarantine and lot tracking cannot be concealed by conversion into a set',async()=>{
  const physical=await fixture('physical-parent',1),request={action:'bundle',id:physical.variantId,components:[{variantId:b.variantId,quantity:1}],reason:'İzole fiziksel stok dönüşüm sınırı'};
  await assert.rejects(()=>core.adminAction('variants',request,admin),(e:unknown)=>(e as {code:string}).code==='BUNDLE_PARENT_STOCK');
  await core.adminAction('inventory',{action:'quarantine',variantId:physical.variantId,quantity:1,reason:'İzole karantina stok dönüşüm sınırı'},admin);await assert.rejects(()=>core.adminAction('variants',request,admin),(e:unknown)=>(e as {code:string}).code==='BUNDLE_PARENT_STOCK');
  await core.adminAction('inventory',{action:'release',variantId:physical.variantId,quantity:1,reason:'İzole kontrol sonrası karantina açma'},admin);await core.adminAction('inventory',{action:'adjustment',variantId:physical.variantId,quantity:-1,reason:'İzole sayımda fiziksel çıkış kaydı'},admin);
  await core.adminAction('lots',{action:'enable',variantId:physical.variantId,expiryRequired:false,idempotencyKey:randomBytes(32).toString('hex'),reason:'İzole lot takipli fiziksel stok kurulumu'},admin);
  await assert.rejects(()=>core.adminAction('variants',request,admin),(e:unknown)=>(e as {code:string}).code==='BUNDLE_LOT_TRACKING_DISABLED');
 });
 await check('Nested, inactive, self, duplicate and invalid quantity components are rejected by the API',async()=>{
  const logical=await fixture('logical'),physical=await fixture('nested-physical');await core.adminAction('variants',{action:'bundle',id:logical.variantId,components:[{variantId:physical.variantId,quantity:1}],reason:'İzole başka set tanımı'},admin);
  await assert.rejects(()=>core.adminAction('variants',change([{variantId:logical.variantId,quantity:1}],3),catalog),(e:unknown)=>(e as {code:string}).code==='NESTED_BUNDLE_DISABLED');
  await assert.rejects(()=>core.adminAction('variants',{action:'bundle',id:physical.variantId,components:[{variantId:b.variantId,quantity:1}],reason:'İzole iç içe set ters ilişki denemesi'},admin),(e:unknown)=>(e as {code:string}).code==='NESTED_BUNDLE_DISABLED');
  const inactive=await fixture('inactive');await core.adminAction('variants',{action:'archive',id:inactive.variantId},admin);await assert.rejects(()=>core.adminAction('variants',change([{variantId:inactive.variantId,quantity:1}],3),catalog),(e:unknown)=>(e as {code:string}).code==='BUNDLE_COMPONENT_UNAVAILABLE');
  for(const components of [[{variantId:parent.variantId,quantity:1}],[{variantId:a.variantId,quantity:1},{variantId:a.variantId,quantity:2}],[{variantId:a.variantId,quantity:0}],[]])await assert.rejects(()=>core.adminAction('variants',change(components,3),catalog));
 });
 async function pendingOrder(items:View['components'],connection:Connection=pool!){
  const marker=randomBytes(16).toString('hex'),[cart]=await query('INSERT INTO carts(token_hash) VALUES($1) RETURNING id',[marker],connection);
  const snapshot={bundleComponents:items.map(({variantId,quantity})=>({variantId,quantity})),marker};
  const [order]=await query("INSERT INTO orders(cart_id,idempotency_key,request_hash,tracking_hash,currency,subtotal_minor,shipping_minor,tax_minor,total_minor,email,address,snapshot,expires_at) VALUES($1,$2,$2,$2,'TRY',10000,0,0,10000,'bundle-pending@example.invalid','{}','{}',now()+interval '15 minutes') RETURNING id",[cart.id,marker],connection);
  await query("INSERT INTO order_items(order_id,variant_id,name,sku,quantity,unit_minor,cost_minor,snapshot) VALUES($1,$2,'İzole set siparişi','BUNDLE-parent',1,10000,1000,$3)",[order.id,parent.variantId,JSON.stringify(snapshot)],connection);
  for(const item of items)await query("INSERT INTO reservations(order_id,variant_id,warehouse_id,quantity,expires_at) VALUES($1,$2,'main',$3,now()+interval '15 minutes')",[order.id,item.variantId,item.quantity],connection);
  await query("INSERT INTO payments(order_id,provider,amount_minor,currency) VALUES($1,'test',10000,'TRY')",[order.id],connection);return {id:order.id,snapshot};
 }
 await check('Active reservations block definition changes; later edits preserve original order snapshots and allocations',async()=>{
  const current=await view(),pending=await pendingOrder(current.components),before=JSON.stringify(await query('SELECT * FROM reservations WHERE order_id=$1',[pending.id]));
  const next=current.components[0].variantId===a.variantId?b:a;
  await assert.rejects(()=>core.adminAction('variants',change([{variantId:next.variantId,quantity:1}],current.version),catalog),(e:unknown)=>(e as {code:string}).code==='BUNDLE_RESERVED');assert.equal(JSON.stringify(await query('SELECT * FROM reservations WHERE order_id=$1',[pending.id])),before);
  await core.adminAction('orders',{action:'cancel',id:pending.id,reason:'İzole rezervasyonun yetkili iptali'},admin);const afterCancel=JSON.stringify(await query('SELECT * FROM reservations WHERE order_id=$1',[pending.id]));
  await core.adminAction('variants',change([{variantId:next.variantId,quantity:1}],current.version),catalog);assert.deepEqual((await query('SELECT snapshot FROM order_items WHERE order_id=$1',[pending.id]))[0].snapshot,pending.snapshot);assert.equal(JSON.stringify(await query('SELECT * FROM reservations WHERE order_id=$1',[pending.id])),afterCancel);
 });
 await check('An in-flight checkout locks the old removed component before the editor tests active reservations',async()=>{
  const current=await view(),next=current.components[0].variantId===a.variantId?b:a,blocker=await pool!.connect();let attempt:Promise<{error?:unknown}>|undefined,pending:{id:string}|undefined;
  try{
   await blocker.query('BEGIN');await blocker.query('SELECT p.id FROM products p JOIN variants v ON v.product_id=p.id WHERE v.id=ANY($1::text[]) ORDER BY p.id,v.id FOR SHARE OF p,v',[current.components.map(row=>row.variantId)]);
   attempt=core.adminAction('variants',change([{variantId:next.variantId,quantity:1}],current.version),catalog).then(()=>({}),error=>({error}));
   let blocked=false;for(let count=0;count<100;count++){if(Number((await query("SELECT count(*)::int n FROM pg_stat_activity WHERE datname=current_database() AND wait_event='transactionid'"))[0].n)>0){blocked=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(blocked,'Edit should wait for the existing physical component');
   pending=await pendingOrder(current.components,blocker);await blocker.query('COMMIT');const result=await attempt;assert.equal((result.error as {code:string})?.code,'BUNDLE_RESERVED');assert.equal((await view()).version,current.version);
  }finally{await blocker.query('ROLLBACK');blocker.release();if(attempt)await attempt;}
  if(pending)await core.adminAction('orders',{action:'cancel',id:pending.id,reason:'İzole eşzamanlı siparişin yetkili iptali'},admin);
 });
 await check('Finance, warehouse and unverified catalog sessions cannot change or preview a bundle',async()=>{
  const current=await view();for(const principal of [{id:'f',role:'finance' as const,mfa:true},{id:'w',role:'warehouse' as const,mfa:true},{...catalog,mfa:false}])for(const action of ['bundle','bundlePreview'])await assert.rejects(()=>core.adminAction('variants',action==='bundle'?change([{variantId:a.variantId,quantity:1}],current.version):{action,id:parent.variantId,expectedVersion:current.version,components:[{variantId:a.variantId,quantity:1}]},principal));
  assert.equal((await view()).version,current.version);
 });
 await check('A logical bundle parent cannot receive, adjust, quarantine or release physical stock',async()=>{
  const balance=await query('SELECT * FROM inventory_balance WHERE variant_id=$1',[parent.variantId]),movements=await query('SELECT * FROM inventory_movements WHERE variant_id=$1',[parent.variantId]);
  for(const action of ['receipt','adjustment','quarantine','release'])await assert.rejects(()=>core.adminAction('inventory',{action,variantId:parent.variantId,quantity:1,reason:'İzole mantıksal set üst koduna fiziksel stok denemesi'},admin),(error:unknown)=>(error as {code:string}).code==='BUNDLE_PHYSICAL_STOCK_DISABLED');
  assert.deepEqual(await query('SELECT * FROM inventory_balance WHERE variant_id=$1',[parent.variantId]),balance);assert.deepEqual(await query('SELECT * FROM inventory_movements WHERE variant_id=$1',[parent.variantId]),movements);
 });
 await check('A mixed purchase receipt containing a logical parent rolls back every line and receipt record',async()=>{
  const supplier=await core.adminAction('suppliers',{name:'İzole set tedarikçi kaydı',leadDays:1},admin) as {id:string};
  const purchase=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:parent.variantId,quantity:1,unitCostMinor:1000},{variantId:b.variantId,quantity:1,unitCostMinor:1000}]},admin) as {id:string};
  const before=await query('SELECT * FROM inventory_balance WHERE variant_id=ANY($1::text[]) ORDER BY variant_id',[[parent.variantId,b.variantId]]),movements=await query('SELECT * FROM inventory_movements WHERE variant_id=ANY($1::text[]) ORDER BY id',[[parent.variantId,b.variantId]]);
  await assert.rejects(()=>core.adminAction('purchases',{action:'receive',sourceReference:'Yalnız izole mal kabul teslimat belgesi',id:purchase.id,idempotencyKey:randomBytes(32).toString('hex'),items:[{variantId:parent.variantId,quantity:1},{variantId:b.variantId,quantity:1}],reason:'İzole karma satın alma stok sınırı testi'},admin),(error:unknown)=>(error as {code:string}).code==='BUNDLE_PHYSICAL_STOCK_DISABLED');
  assert.deepEqual(await query('SELECT * FROM inventory_balance WHERE variant_id=ANY($1::text[]) ORDER BY variant_id',[[parent.variantId,b.variantId]]),before);assert.deepEqual(await query('SELECT * FROM inventory_movements WHERE variant_id=ANY($1::text[]) ORDER BY id',[[parent.variantId,b.variantId]]),movements);
  assert((await query('SELECT received FROM purchase_items WHERE purchase_id=$1',[purchase.id])).every(row=>row.received===0));assert.equal((await query('SELECT status FROM purchase_orders WHERE id=$1',[purchase.id]))[0].status,'ordered');assert.equal((await query('SELECT count(*)::int n FROM purchase_receipts WHERE purchase_id=$1',[purchase.id]))[0].n,0);
 });
 await check('Concurrent conversion and direct receipt cannot both succeed or mix logical and physical stock',async()=>{
  for(const reverse of [false,true]){
   const target=await fixture('stock-race-'+reverse),convert=()=>core.adminAction('variants',{action:'bundle',id:target.variantId,components:[{variantId:b.variantId,quantity:1}],reason:'İzole set ve mal kabulü eşzamanlılık sınırı'},admin),receive=()=>core.adminAction('inventory',{variantId:target.variantId,quantity:1,reason:'İzole set dönüşümüyle yarışan mal kabulü'},admin);
   const results=await Promise.allSettled((reverse?[receive,convert]:[convert,receive]).map(work=>work()));assert.equal(results.filter(row=>row.status==='fulfilled').length,1);
   const error=(results.find(row=>row.status==='rejected') as PromiseRejectedResult).reason;assert(['BUNDLE_PARENT_STOCK','BUNDLE_PHYSICAL_STOCK_DISABLED'].includes(error.code));
   const definition=(await query('SELECT count(*)::int n FROM bundle_components WHERE bundle_variant_id=$1',[target.variantId]))[0].n,stock=(await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[target.variantId]))[0],ledger=(await query('SELECT count(*)::int n FROM inventory_movements WHERE variant_id=$1',[target.variantId]))[0].n;
   assert.deepEqual([definition,stock.on_hand,stock.quarantine,ledger],definition?[1,0,0,0]:[0,1,0,1]);
  }
 });
 await check('Concurrent conversion and purchase receipt cannot both succeed or partially receive a purchase',async()=>{
  const supplier=await core.adminAction('suppliers',{name:'İzole set yarışı tedarikçisi',leadDays:1},admin) as {id:string};
  for(const reverse of [false,true]){
   const target=await fixture('purchase-race-'+reverse),purchase=await core.adminAction('purchases',{action:'create',supplierId:supplier.id,currency:'TRY',items:[{variantId:target.variantId,quantity:1,unitCostMinor:1000}]},admin) as {id:string};
   const convert=()=>core.adminAction('variants',{action:'bundle',id:target.variantId,components:[{variantId:b.variantId,quantity:1}],reason:'İzole set ve satın alma kabulü yarış kontrolü'},admin),receive=()=>core.adminAction('purchases',{action:'receive',sourceReference:'Yalnız izole mal kabul teslimat belgesi',id:purchase.id,idempotencyKey:randomBytes(32).toString('hex'),items:[{variantId:target.variantId,quantity:1}],reason:'İzole eşzamanlı satın alma mal kabulü'},admin);
   const results=await Promise.allSettled((reverse?[receive,convert]:[convert,receive]).map(work=>work()));assert.equal(results.filter(row=>row.status==='fulfilled').length,1);
   const error=(results.find(row=>row.status==='rejected') as PromiseRejectedResult).reason;assert(['BUNDLE_PARENT_STOCK','BUNDLE_PHYSICAL_STOCK_DISABLED'].includes(error.code));
   const definition=(await query('SELECT count(*)::int n FROM bundle_components WHERE bundle_variant_id=$1',[target.variantId]))[0].n,stock=(await query('SELECT on_hand FROM inventory_balance WHERE variant_id=$1',[target.variantId]))[0].on_hand,received=(await query('SELECT received FROM purchase_items WHERE purchase_id=$1',[purchase.id]))[0].received,receipts=(await query('SELECT count(*)::int n FROM purchase_receipts WHERE purchase_id=$1',[purchase.id]))[0].n;
   assert.deepEqual([definition,stock,received,receipts],definition?[1,0,0,0]:[0,1,1,1]);
  }
 });
 async function historicalOrder(variantId:string,snapshot:Record<string,unknown>={}){
  const marker=randomBytes(16).toString('hex'),[cart]=await query('INSERT INTO carts(token_hash)VALUES($1)RETURNING id',[marker]);
  const [order]=await query("INSERT INTO orders(cart_id,idempotency_key,request_hash,tracking_hash,status,payment_status,currency,subtotal_minor,shipping_minor,tax_minor,total_minor,email,address,snapshot,expires_at)VALUES($1,$2,$2,$2,'confirmed','succeeded','TRY',10000,0,0,10000,'bundle-history@example.invalid','{}','{}',now()-interval '1 day')RETURNING id",[cart.id,marker]);
  await query("INSERT INTO order_items(order_id,variant_id,name,sku,quantity,unit_minor,cost_minor,snapshot)VALUES($1,$2,'İzole geçmiş satış','BUNDLE-HISTORY',1,10000,1000,$3)",[order.id,variantId,JSON.stringify(snapshot)]);await query("INSERT INTO payments(order_id,provider,status,amount_minor,currency)VALUES($1,'test','succeeded',10000,'TRY')",[order.id]);return String(order.id);
 }
 await check('Historical physical sales and removed sold components cannot turn into logical parent codes',async()=>{
  const normal=await fixture('history-physical',1);await historicalOrder(normal.variantId);await query('UPDATE inventory_balance SET on_hand=0 WHERE variant_id=$1',[normal.variantId]);await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference)VALUES($1,'main','sale',-1,'İzole geçmiş fiziksel satış',$2)",[normal.variantId,'bundle-history:'+normal.variantId]);
  const convert=(variantId:string)=>core.adminAction('variants',{action:'bundle',id:variantId,components:[{variantId:b.variantId,quantity:1}],reason:'Geçmiş fiziksel satış sonrası dönüşüm denemesi'},admin);
  await assert.rejects(()=>convert(normal.variantId),(error:unknown)=>(error as {code:string}).code==='BUNDLE_PHYSICAL_HISTORY');
  const oldSet=await fixture('history-old-set'),part=await fixture('history-part',1);await core.adminAction('variants',{action:'bundle',id:oldSet.variantId,components:[{variantId:part.variantId,quantity:1}],reason:'İzole eski set satış bileşeni'},admin);const original={bundleComponents:[{variantId:part.variantId,quantity:1}]},orderId=await historicalOrder(oldSet.variantId,original);
  await query('UPDATE inventory_balance SET on_hand=0 WHERE variant_id=$1',[part.variantId]);await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference)VALUES($1,'main','sale',-1,'İzole geçmiş set bileşeni satışı',$2)",[part.variantId,'bundle-history:'+part.variantId]);
  await core.adminAction('variants',{action:'bundle',id:oldSet.variantId,expectedVersion:1,components:[{variantId:b.variantId,quantity:1}],reason:'Eski setin yeni fiziksel bileşen tanımı'},admin);
  await assert.rejects(()=>convert(part.variantId),(error:unknown)=>(error as {code:string}).code==='BUNDLE_PHYSICAL_HISTORY');assert.deepEqual((await query('SELECT snapshot FROM order_items WHERE order_id=$1',[orderId]))[0].snapshot,original);
  for(const variantId of [normal.variantId,part.variantId]){assert.equal((await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1',[variantId]))[0].on_hand,0);assert.equal((await query('SELECT count(*)::int n FROM bundle_components WHERE bundle_variant_id=$1',[variantId]))[0].n,0);}
 });
 await check('A legacy inconsistent logical-parent return fails closed without quarantine or stock-line writes',async()=>{
  const orderId=await historicalOrder(parent.variantId),request=await core.adminAction('returns',{action:'request',orderId,variantId:parent.variantId,quantity:1,reason:'İzole eski hatalı fiziksel satış iadesi',sealIntact:true},admin) as {id:string};
  await core.adminAction('returns',{action:'review',id:request.id,approved:true,reason:'İzole eski kayıt incelemesi'},admin);const balance=await query('SELECT * FROM inventory_balance WHERE variant_id=$1',[parent.variantId]),movements=await query('SELECT * FROM inventory_movements WHERE variant_id=$1',[parent.variantId]);
  await assert.rejects(()=>core.adminAction('returns',{action:'receive',id:request.id},admin),(error:unknown)=>(error as {code:string}).code==='BUNDLE_PHYSICAL_STOCK_DISABLED');assert.equal((await query('SELECT status FROM returns WHERE id=$1',[request.id]))[0].status,'approved');assert.equal((await query('SELECT count(*)::int n FROM return_stock_lines WHERE return_id=$1',[request.id]))[0].n,0);assert.deepEqual(await query('SELECT * FROM inventory_balance WHERE variant_id=$1',[parent.variantId]),balance);assert.deepEqual(await query('SELECT * FROM inventory_movements WHERE variant_id=$1',[parent.variantId]),movements);
 });
 console.log(`Bundle management integration: ${passed} checks passed.`);
}finally{await pool?.end();if(created)await control.query(`DROP DATABASE "${name}"`);await control.end();}
