/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import type {CheckoutInput} from "../src/shared/contracts";

const url=process.env.TEST_DATABASE_URL;
if(!url || !new URL(url).pathname.endsWith("_test")) throw new Error("TEST_DATABASE_URL must name an isolated database ending _test");
process.env.APP_ENV="test";
process.env.DATABASE_URL=url;
process.env.PAYMENT_PROVIDER="test";
process.env.PAYMENT_WEBHOOK_SECRET=randomBytes(32).toString("hex");
const {migrate}=await import("./migrate");
const {pool,query}=await import("../src/server/db");
const core=await import("../src/server/commerce/index");
const admin={id:"integration-admin",role:"admin" as const,mfa:true};
let passed=0;
async function check(name:string,work:()=>Promise<void>) {
 await work();passed++;console.log(`PASS ${passed}: ${name}`);
}
const token=()=>randomBytes(32).toString("hex");
const input=(key=token())=>({email:"test@example.invalid",fullName:"Hamza ÖZBALKAN",phone:"05000000000",line1:"Şişli Çeşme İç Giyim Ölçü ve Özellikler",city:"İstanbul",postalCode:"34000",country:"TR",locale:"tr" as const,currency:"TRY" as const,idempotencyKey:key,privacyAccepted:true,termsAccepted:true});
const quoted=async(cart:string,data:Omit<CheckoutInput,"quoteToken">)=>({...data,quoteToken:(await core.quoteCheckout(cart,{country:data.country,currency:data.currency,locale:data.locale,...(data.couponCode?{couponCode:data.couponCode}:{})})).quoteToken});
const checkout=async(cart:string,data:Omit<CheckoutInput,"quoteToken">)=>core.checkout(cart,await quoted(cart,data));
const suiteLock=await pool.connect();
try {
 await suiteLock.query("SELECT pg_advisory_lock(8401102027)");
 await pool.query("DROP SCHEMA public CASCADE; CREATE SCHEMA public");
 await migrate(url);await migrate(url);
 const {seed}=await import("./seed");await seed(url);
 let products=await core.listProducts({});
 assert(products.length>=1);
 let variant=products[0].variants[0];
 await check("Product → stock receipt → publication → guest checkout → signed payment",async()=>{
  const created=await core.adminAction("products",{name:"Ölçü ve Özellikler",nameEn:"Measurements and details",slug:"olcu-ve-ozellikler",category:"aksesuarlar",brand:"",description:"Güvenli Alışveriş",descriptionEn:"Private shopping",sku:"INTEGRATION-SKU",variantName:"Bordo",variantNameEn:'Burgundy',priceMinor:10001,costMinor:3000,material:"Tekstil",image:"/media/atelier-01.svg",warnings:"Yetişkin kullanımı içindir.",warningsEn:'For adults only.',care:"Etiketteki adımları izleyin.",careEn:'Follow the care label.'},admin) as {id:string,variantId:string};
  await core.adminAction("inventory",{variantId:created.variantId,quantity:3,reason:"İzole test mal kabulü"},admin);
  const {complianceAction}=await import("../src/server/compliance");await complianceAction({action:"eligibility",variantId:created.variantId,country:"TR",approved:true,reason:"Yalnız izole test için ayrı yönetici SKU incelemesi",idempotencyKey:token()},admin);
  await core.adminAction("products",{action:"publish",id:created.id,country:"TR",reviewNote:"Yalnız izole test ürünü"},admin);
  const found=await core.getProduct("olcu-ve-ozellikler");assert(found);assert.equal(found.name,"Ölçü ve Özellikler");
  products=await core.listProducts({q:"olcu"});assert(products.some(p=>p.id===created.id));
  variant=found.variants[0];
  const cart=token();await core.setCartItem(cart,variant.id,1);
  const order=await checkout(cart,input());
  const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,"succeeded");
  await core.handlePayment(event.raw,event.signature);
  assert.equal((await core.getOrder(order.orderId,order.trackingToken))?.status,"confirmed");
 });
 await check("Last unit cannot be oversold by concurrent checkouts",async()=>{
  const balance=await query("SELECT on_hand FROM inventory_balance WHERE variant_id=$1",[variant.id]);
  await core.adminAction("inventory",{action:"adjustment",variantId:variant.id,quantity:1-Number(balance[0].on_hand),reason:"Son adet yarışı"},admin);
  const one=token(),two=token();await core.setCartItem(one,variant.id,1);await core.setCartItem(two,variant.id,1);
  const oneInput=await quoted(one,input()),twoInput=await quoted(two,input());
  const results=await Promise.allSettled([core.checkout(one,oneInput),core.checkout(two,twoInput)]);
  assert.equal(results.filter(r=>r.status==="fulfilled").length,1);
  const result=results.find(r=>r.status==="fulfilled") as PromiseFulfilledResult<Awaited<ReturnType<typeof core.checkout>>>;
  const event=await core.createTestPaymentEvent(result.value.orderId,result.value.trackingToken,"succeeded");
  await core.handlePayment(event.raw,event.signature);await core.handlePayment(event.raw,event.signature);
  const movements=await query("SELECT count(*)::int AS n FROM inventory_movements WHERE reference=$1",[`payment:${result.value.orderId}:${variant.id}`]);
  assert.equal(movements[0].n,1);assert.equal((await query("SELECT on_hand FROM inventory_balance WHERE variant_id=$1",[variant.id]))[0].on_hand,0);
 });
 await check("Unsigned, changed amount/currency and replay-content mismatch rejected",async()=>{
  await core.adminAction("inventory",{variantId:variant.id,quantity:6,reason:"Ödeme doğrulama"},admin);
  const cart=token();await core.setCartItem(cart,variant.id,1);const order=await checkout(cart,input());
  const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,"succeeded");
  await assert.rejects(()=>core.handlePayment(event.raw,""));
  const {signPayment}=await import("../src/server/commerce/rules");
  for(const patch of [{amountMinor:1},{currency:"EUR"}]){
   const raw=JSON.stringify({...JSON.parse(event.raw),...patch});
   await assert.rejects(()=>core.handlePayment(raw,signPayment(raw,process.env.PAYMENT_WEBHOOK_SECRET!)));
  }
  await core.handlePayment(event.raw,event.signature);
  const changed=JSON.stringify({...JSON.parse(event.raw),status:"failed"});
  await assert.rejects(()=>core.handlePayment(changed,signPayment(changed,process.env.PAYMENT_WEBHOOK_SECRET!)));
 });
 await check("Failed and expired payments release stock; late success raises exception",async()=>{
  const cart=token();await core.setCartItem(cart,variant.id,1);const order=await checkout(cart,input());
  const fail=await core.createTestPaymentEvent(order.orderId,order.trackingToken,"failed");await core.handlePayment(fail.raw,fail.signature);
  assert.equal((await core.getOrder(order.orderId,order.trackingToken))?.paymentStatus,"failed");
  const cart2=token();await core.setCartItem(cart2,variant.id,1);const late=await checkout(cart2,input());
  await query("UPDATE orders SET expires_at=now()-interval '1 minute' WHERE id=$1",[late.orderId]);
  await query("UPDATE reservations SET expires_at=now()-interval '1 minute' WHERE order_id=$1",[late.orderId]);
  await core.expireReservations();
  const success=await core.createTestPaymentEvent(late.orderId,late.trackingToken,"succeeded");await core.handlePayment(success.raw,success.signature);
  assert.equal((await core.getOrder(late.orderId,late.trackingToken))?.status,"payment_exception");
 });
 await check("Idempotency remains bound to cart and immutable input; tracking ownership protected",async()=>{
  const a=token(),b=token();await core.setCartItem(a,variant.id,1);await core.setCartItem(b,variant.id,1);const data=await quoted(a,input());
  const first=await core.checkout(a,data),repeat=await core.checkout(a,data);assert.equal(first.orderId,repeat.orderId);assert.equal(first.trackingToken,repeat.trackingToken);
  await assert.rejects(()=>core.checkout(a,{...data,city:"İzmir"}));
  assert.equal(await core.getOrder(first.orderId,token()),null);
  assert.equal(await core.getOrder(first.orderId,null,"different-user"),null);
  assert.equal((await checkout(b,data)).orderId===first.orderId,false);
 });
 await check("Blocked country and missing eligibility or document stop checkout",async()=>{
  const cart=token();await core.setCartItem(cart,variant.id,1);const guardedInput=await quoted(cart,input());
  await assert.rejects(()=>core.checkout(cart,{...guardedInput,country:"DE"}));
  await query("UPDATE product_eligibility SET approved=false WHERE variant_id=$1",[variant.id]);
  await assert.rejects(()=>core.checkout(cart,guardedInput));
  await query("UPDATE product_eligibility SET approved=true WHERE variant_id=$1",[variant.id]);
  await query("UPDATE product_eligibility SET required_document_kind='transport' WHERE variant_id=$1",[variant.id]);
  await assert.rejects(()=>core.checkout(cart,guardedInput));
  await query("UPDATE product_eligibility SET required_document_kind=null WHERE variant_id=$1",[variant.id]);
 });
 await check("Warehouse cannot see costs, marketing cannot export customers, MFA enforced",async()=>{
  const data=await core.adminList("products",{id:"warehouse",role:"warehouse",mfa:true}) as {rows:Record<string,unknown>[]};
  assert(data.rows.every(row=>!("costMinor" in row)));
  await assert.rejects(()=>core.adminList("reports",{id:"warehouse",role:"warehouse",mfa:true}));
  await assert.rejects(()=>core.adminList("customers",{id:"marketer",role:"marketing",mfa:true}));
  await assert.rejects(()=>core.adminAction("settings",{key:"seller.name",value:"x"},{id:"admin",role:"admin",mfa:false}));
 });
 await check("Production test adapter and fixture checkout are blocked",async()=>{
  const cart=token();await core.setCartItem(cart,variant.id,1);const productionInput=await quoted(cart,input());
  process.env.APP_ENV="production";
  await assert.rejects(()=>core.createTestPaymentEvent("unknown",token(),"succeeded"));
  await assert.rejects(()=>core.checkout(cart,productionInput));
  process.env.APP_ENV="test";
 });
 await check("Legal snapshot preserves Turkish text, hash and version",async()=>{
  const cart=token();await core.setCartItem(cart,variant.id,1);const order=await checkout(cart,input());
  const contracts=await query("SELECT body,body_hash,version FROM order_agreements WHERE order_id=$1",[order.orderId]);
  assert(contracts.length>=2);assert(contracts.every(x=>x.body_hash.length===64 && x.version===1));
  assert(contracts.some(x=>x.body.includes("Güvenli Alışveriş")));
 });
 await check("Partial shipment and return quarantine cannot exceed ordered quantities or open seal",async()=>{
  await core.adminAction("inventory",{variantId:variant.id,quantity:10,reason:"İade ve sevk testi"},admin);
  const cart=token();await core.setCartItem(cart,variant.id,2);const order=await checkout(cart,input());
  const event=await core.createTestPaymentEvent(order.orderId,order.trackingToken,"succeeded");await core.handlePayment(event.raw,event.signature);
  await core.adminAction("shipments",{orderId:order.orderId,carrier:"Manuel taşıyıcı",trackingNumber:"LOCAL-INTEGRATION-1",items:[{variantId:variant.id,quantity:1}]},admin);
  assert.equal((await core.getOrder(order.orderId,order.trackingToken))?.status,"partially_shipped");
  await assert.rejects(()=>core.adminAction("shipments",{orderId:order.orderId,carrier:"Manuel taşıyıcı",trackingNumber:"LOCAL-INTEGRATION-OVER",items:[{variantId:variant.id,quantity:2}]},admin));
  const balanceBefore=(await query("SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1",[variant.id]))[0];
  const request=await core.requestReturn(order.orderId,order.trackingToken,{variantId:variant.id,quantity:1,reason:"Ölçü uyumsuzluğu bildirimi",sealIntact:false}) as {id:string};
  await core.adminAction("returns",{action:"review",id:request.id,approved:true,reason:"Başvuru incelemesi tamamlandı"},admin);
  await core.adminAction("returns",{action:"receive",id:request.id},admin);
  const balanceAfter=(await query("SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1",[variant.id]))[0];
  assert.equal(balanceBefore.on_hand,balanceAfter.on_hand);assert.equal(balanceAfter.quarantine,balanceBefore.quarantine+1);
  await assert.rejects(()=>core.adminAction("returns",{action:"inspect",id:request.id,restock:true,reason:"Mühür kontrolü gereklidir"},admin));
  await core.adminAction("returns",{action:"inspect",id:request.id,restock:false,reason:"Açık mühür karantinada kalır"},admin);
  await assert.rejects(()=>core.adminAction("inventory",{action:"release",variantId:variant.id,quantity:1,reason:"Genel stok ekranından iade bypass"},admin));
  await core.adminAction("returns",{action:"refund",id:request.id},admin);
  await assert.rejects(()=>core.adminAction("returns",{action:"refund",id:request.id},admin));
  await assert.rejects(()=>core.requestReturn(order.orderId,token(),{variantId:variant.id,quantity:1,reason:"Yetkisiz iade başvurusu",sealIntact:true}));
  const shipment=await core.adminAction("shipments",{orderId:order.orderId,carrier:"Manuel taşıyıcı",trackingNumber:"LOCAL-INTEGRATION-2",items:[{variantId:variant.id,quantity:1}]},admin) as {id:string};
  const repeated=await core.adminAction("shipments",{orderId:order.orderId,carrier:"Manuel taşıyıcı",trackingNumber:"LOCAL-INTEGRATION-2",items:[{variantId:variant.id,quantity:1}]},admin) as {id:string,duplicate:boolean};
  assert.equal(shipment.id,repeated.id);assert.equal(repeated.duplicate,true);
 });
 await check("Official provider session reference preserved; wrong session rejected",async()=>{
  const cart=token();await core.setCartItem(cart,variant.id,1);
  process.env.PAYMENT_PROVIDER="stripe";
  const order=await checkout(cart,input());
  await core.setPaymentReference(order.orderId,"stripe","cs_fixture_owned_session");
  const event={eventId:"evt_provider_reference",orderId:order.orderId,status:"succeeded" as const,amountMinor:order.totalMinor,currency:order.currency,timestamp:Math.floor(Date.now()/1000),providerReference:"cs_different_session"};
  await assert.rejects(()=>core.settleVerifiedPayment(event,"stripe"));
  await core.settleVerifiedPayment({...event,providerReference:"cs_fixture_owned_session"},"stripe");
  assert.equal((await query("SELECT provider_reference FROM payments WHERE order_id=$1",[order.orderId]))[0].provider_reference,"cs_fixture_owned_session");
  process.env.PAYMENT_PROVIDER="test";
 });
 await check("Persistent queue retries unavailable handlers and completes idempotent handlers",async()=>{
  await query("INSERT INTO jobs(type,payload,dedupe_key) VALUES('integration.handler','{}','integration-job-1'),('integration.unavailable','{}','integration-job-2')");
  let calls=0;await core.processJobsOnce({"integration.handler":async()=>{calls++;}});
  assert.equal(calls,1);
  const rows=await query("SELECT type,status,attempts,last_error FROM jobs WHERE dedupe_key LIKE 'integration-job-%' ORDER BY type");
  assert.equal(rows[0].status,"completed");assert.equal(rows[1].status,"pending");assert.equal(rows[1].last_error,"HANDLER_NOT_CONFIGURED");
  await core.processJobsOnce({"integration.handler":async()=>{calls++;}});assert.equal(calls,1);
 });
 await check("Coupon usage is reserved atomically and failed payment releases usage",async()=>{
  await core.adminAction("inventory",{variantId:variant.id,quantity:10,reason:"Kupon yarışı stoğu"},admin);
  await query("INSERT INTO coupons(code,discount_bps,minimum_minor,max_uses,expires_at) VALUES('ONCE',1700,100,1,now()+interval '1 day')");
  const a=token(),b=token();await core.setCartItem(a,variant.id,1);await core.setCartItem(b,variant.id,1);
  const dataA=await quoted(a,{...input(),couponCode:"ONCE"}),dataB=await quoted(b,{...input(),couponCode:"ONCE"});
  const results=await Promise.allSettled([core.checkout(a,dataA),core.checkout(b,dataB)]);
  assert.equal(results.filter(r=>r.status==="fulfilled").length,1);
  const winner=(results.find(r=>r.status==="fulfilled") as PromiseFulfilledResult<Awaited<ReturnType<typeof core.checkout>>>).value;
  const summary=await core.getOrder(winner.orderId,winner.trackingToken);assert(summary);assert.equal(summary.discountMinor,1700);
  const failed=await core.createTestPaymentEvent(winner.orderId,winner.trackingToken,"failed");await core.handlePayment(failed.raw,failed.signature);
  const loser=results[0].status==="rejected"?a:b;const retried=await checkout(loser,{...input(),couponCode:"ONCE"});assert(retried.orderId);
 });
 await check("Reservation is allocated only from the locked fulfillment warehouse",async()=>{
  await query("UPDATE orders SET expires_at=now()-interval '1 minute' WHERE status='awaiting_payment'");
  await query("UPDATE reservations SET expires_at=now()-interval '1 minute' WHERE status='active'");await core.expireReservations();
  await query("INSERT INTO warehouses(id,name) VALUES('secondary','İkinci test deposu')");
  await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'secondary',100)",[variant.id]);
  await query("UPDATE inventory_balance SET on_hand=1 WHERE variant_id=$1 AND warehouse_id='main'",[variant.id]);
  const cart=token();await core.setCartItem(cart,variant.id,1);const warehouseInput=await quoted(cart,input());
  await query("UPDATE inventory_balance SET on_hand=0 WHERE variant_id=$1 AND warehouse_id='main'",[variant.id]);
  await assert.rejects(()=>core.setCartItem(token(),variant.id,1),{code:'INSUFFICIENT_STOCK'});
  await assert.rejects(()=>core.checkout(cart,warehouseInput),{code:'INSUFFICIENT_STOCK'});
 });
 await check("Order address and profile version survive later policy and address-book edits",async()=>{
  await core.adminAction('inventory',{variantId:variant.id,quantity:3,reason:'Adres sürümü izole kontrol stoğu'},admin);
  const cart=token();await core.setCartItem(cart,variant.id,1);const data=await quoted(cart,input());const order=await core.checkout(cart,data);
  const [before]=await query('SELECT address,address_profile_id FROM orders WHERE id=$1',[order.orderId]);assert(before.address_profile_id);assert.equal(before.address.profileVersion,1);
  const {manageAddressProfile}=await import('../src/server/address-profiles');
  const [profile]=await query('SELECT fields FROM country_address_profiles WHERE id=$1',[before.address_profile_id]);
  const draft=await manageAddressProfile({action:'create',country:'TR',fields:profile.fields.map((field:{id:string;label:{tr:string;en:string}})=>field.id==='city'?{...field,label:{tr:'İl veya şehir',en:'Town or city'}}:field),reference:'İzole test için ikinci alan etiketi incelemesi'},admin);
  await manageAddressProfile({action:'approve',id:draft.id,reason:'İzole yeni sürüm onayı; gerçek ülke onayı değildir'},admin);
  const {addresses}=await import('../src/server/customer');const owner={id:'address-snapshot-owner',role:'customer' as const,mfa:false};
  const bare={fullName:data.fullName,phone:data.phone,line1:data.line1,city:data.city,postalCode:data.postalCode,country:data.country};
  const created=await addresses(owner,{...bare,label:'Önceki adres'});await addresses(owner,{...bare,action:'update',id:created.addresses[0].id,label:'Yeni adres',city:'İzmir'});
  const [after]=await query('SELECT address,address_profile_id FROM orders WHERE id=$1',[order.orderId]);assert.deepEqual(after,before);
  const repeated=await core.checkout(cart,data);assert.equal(repeated.orderId,order.orderId);
  const second=token();await core.setCartItem(second,variant.id,1);const latest=await checkout(second,input());assert.equal((await query('SELECT address_profile_id FROM orders WHERE id=$1',[latest.orderId]))[0].address_profile_id,draft.id);
 });
 console.log(`Integration checks: ${passed} passed, 0 failed`);
} finally {await suiteLock.query("SELECT pg_advisory_unlock(8401102027)");suiteLock.release();await pool.end();}
