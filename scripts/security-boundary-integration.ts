/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/security-boundary-integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import assert from 'node:assert/strict';
import {randomBytes,createHash} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';

const base=process.env.TEST_DATABASE_URL;
if(!base)throw new Error('TEST_DATABASE_URL gereklidir.');
const parsed=new URL(base);
if(!['127.0.0.1','localhost','[::1]'].includes(parsed.hostname)||!parsed.pathname.endsWith('_test'))throw new Error('Güvenlik testi yalnız yerel izole test veritabanında çalışır.');
const databaseName=`sexsogate_${randomBytes(8).toString('hex')}_boundary_test`;
assert.match(databaseName,/^sexsogate_[a-f0-9]{16}_boundary_test$/);
const control=new pg.Client({connectionString:base});await control.connect();
let created=false,closePool:(()=>Promise<void>)|undefined,passed=0;
async function check(name:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${name}`);}
try {
 await control.query(`CREATE DATABASE "${databaseName}"`);created=true;
 parsed.pathname='/'+databaseName;
 process.env.DATABASE_URL=parsed.toString();process.env.APP_ENV='test';
 await migrate(process.env.DATABASE_URL);
 const {pool,query}=await import('../src/server/db');closePool=()=>pool.end();
 const {enforceCheckoutNetworkQuota,checkoutNetworkPolicy}=await import('../src/server/abuse');
 const {resolveCartOwner,newToken,mergeCustomerCart}=await import('../src/server/customer');
 const {getCart,setCartItem}=await import('../src/server/commerce');
 const request=(ip:string)=>new Request('https://example.invalid/api/checkout',{method:'POST',headers:{'x-real-ip':ip,cookie:`sg_cart=${newToken()}`}});
 const originalSecret=process.env.BETTER_AUTH_SECRET;
 process.env.BETTER_AUTH_SECRET=randomBytes(32).toString('hex');
 process.env.APP_ENV='production';process.env.TRUSTED_PROXY_ENABLED='true';process.env.TRUSTED_CLIENT_IP_HEADER='x-real-ip';
 await check('11 simultaneous new-cookie requests share one trusted network budget:10 accept,1 reject',async()=>{
  const outcomes=await Promise.allSettled(Array.from({length:11},()=>enforceCheckoutNetworkQuota(request('192.0.2.31'))));
  assert.equal(outcomes.filter(x=>x.status==='fulfilled').length,10);
  const rejected=outcomes.filter(x=>x.status==='rejected') as PromiseRejectedResult[];
  assert.equal(rejected.length,1);assert.equal(rejected[0].reason.status,429);
  const rows=await query('SELECT key,count FROM request_limits');assert.equal(rows.length,1);assert.equal(rows[0].count,11);
  assert.match(rows[0].key,/^checkout-network:[a-f0-9]{64}$/);assert(!rows[0].key.includes('192.0.2.31'));
 });
 await check('IPv6 lower64 rotation and mapped IPv4 spelling cannot create new budget',async()=>{
  await assert.rejects(()=>enforceCheckoutNetworkQuota(request('::ffff:192.0.2.31')),(error:unknown)=>(error as {status:number}).status===429);
  const outcomes=await Promise.allSettled(Array.from({length:11},(_,i)=>enforceCheckoutNetworkQuota(request(`2001:db8:1234:5678::${i+1}`))));
  assert.equal(outcomes.filter(x=>x.status==='fulfilled').length,10);assert.equal(outcomes.filter(x=>x.status==='rejected').length,1);
  await enforceCheckoutNetworkQuota(request('2001:db8:1234:5679::1'));
 });
 await check('Missing production boundary fails503 before creating a quota row; expired window resets',async()=>{
  const before=Number((await query('SELECT count(*)::int n FROM request_limits'))[0].n);
  process.env.TRUSTED_PROXY_ENABLED='false';
  await assert.rejects(()=>enforceCheckoutNetworkQuota(request('203.0.113.1')),(error:unknown)=>(error as {status:number}).status===503);
  assert.equal(Number((await query('SELECT count(*)::int n FROM request_limits'))[0].n),before);
  process.env.TRUSTED_PROXY_ENABLED='true';
  const {key}=checkoutNetworkPolicy(request('192.0.2.31'));
  await query("UPDATE request_limits SET window_start=now()-interval '2 minutes' WHERE key=$1",[key]);
  await enforceCheckoutNetworkQuota(request('192.0.2.31'));
  assert.equal((await query('SELECT count FROM request_limits WHERE key=$1',[key]))[0].count,1);
 });
 await check('Price-summary traffic has a separate60 request bucket and does not spend the10 payment attempts',async()=>{
  const req=request('192.0.2.90'),payment=checkoutNetworkPolicy(req),quote=checkoutNetworkPolicy(req,undefined,'quote');
  assert.notEqual(quote.key,payment.key);
  for(let i=0;i<60;i++)await enforceCheckoutNetworkQuota(req,'quote');
  await assert.rejects(()=>enforceCheckoutNetworkQuota(req,'quote'),{status:429,code:'QUOTE_RATE_LIMIT'});
  assert.equal((await query('SELECT count(*)::int n FROM request_limits WHERE key=$1',[payment.key]))[0].n,0);
  const outcomes=await Promise.allSettled(Array.from({length:11},()=>enforceCheckoutNetworkQuota(req)));
  assert.equal(outcomes.filter(outcome=>outcome.status==='fulfilled').length,10);assert.equal(outcomes.filter(outcome=>outcome.status==='rejected').length,1);
 });
 process.env.APP_ENV='test';
 // Build just enough local catalog without loading fixture seed into a nonstandard DB name.
 await query("INSERT INTO categories(slug,name,name_en) VALUES('aksesuarlar','Aksesuarlar','Accessories')");
 await query("INSERT INTO warehouses(id,name) VALUES('main','Test Deposu')");
 const [p]=await query("INSERT INTO products(slug,name,name_en,category,image,status) VALUES('boundary-product','Ölçü ve Özellikler','Measurements and details','aksesuarlar','/media/atelier-01.svg','published') RETURNING id");
 const [v]=await query("INSERT INTO variants(product_id,sku,name,price_minor) VALUES($1,'BOUNDARY-ONLY','Bordo',10001) RETURNING id",[p.id]);
 await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',3)",[v.id]);
 await check('CustomerA keeps own cart; customerB and guest get empty fresh capabilities',async()=>{
  const original=newToken();await setCartItem(original,v.id,1);const originalCart=await getCart(original);
  await query("UPDATE carts SET user_id='customer-A' WHERE id=$1",[originalCart.id]);
  const a={id:'customer-A',role:'customer' as const,mfa:false},b={id:'customer-B',role:'customer' as const,mfa:false};
  assert.equal(await resolveCartOwner(original,a),original);
  const forB=await resolveCartOwner(original,b),forGuest=await resolveCartOwner(original,null);
  assert.notEqual(forB,original);assert.notEqual(forGuest,original);assert.notEqual(forB,forGuest);
  assert.equal((await getCart(forB)).items.length,0);assert.equal((await getCart(forGuest)).items.length,0);
  assert.equal((await getCart(original,'TRY',a.id)).items.length,1);
  assert.equal((await query('SELECT user_id FROM carts WHERE id=$1',[originalCart.id]))[0].user_id,'customer-A');
 });
 const [privateProduct]=await query("INSERT INTO products(slug,name,name_en,category,image,status) VALUES('boundary-private','Üyenin özel sepet tercihi','Member private preference','aksesuarlar','/media/atelier-01.svg','published') RETURNING id");
 const [privateVariant]=await query("INSERT INTO variants(product_id,sku,name,price_minor) VALUES($1,'BOUNDARY-PRIVATE','Özel satır',20001) RETURNING id",[privateProduct.id]);
 await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',20)",[privateVariant.id]);
 async function ownershipRace(){
  const principal={id:'boundary-owner-'+newToken(),role:'customer' as const,mfa:false},guest=newToken(),member=newToken();
  await setCartItem(guest,v.id,1);await setCartItem(member,privateVariant.id,1);
  await query('UPDATE carts SET user_id=$2 WHERE token_hash=$1',[createHash('sha256').update(member).digest('hex'),principal.id]);
  assert.equal(await resolveCartOwner(guest,null),guest);
  return {principal,guest};
 }
 await check('A completed member merge invalidates a stale anonymous cart read before private rows are returned',async()=>{
  const {principal,guest}=await ownershipRace();await mergeCustomerCart(guest,principal);
  await assert.rejects(()=>getCart(guest),{code:'CART_NOT_FOUND'});
  await assert.rejects(()=>getCart(guest,'TRY','different-user'),{code:'CART_NOT_FOUND'});
  const own=await getCart(guest,'TRY',principal.id);assert(own.items.some(item=>item.variantId===privateVariant.id));
 });
 await check('Stale anonymous updates and quantity-zero deletion cannot mutate a newly owned cart',async()=>{
  for(const quantity of [2,0]){const {principal,guest}=await ownershipRace();await mergeCustomerCart(guest,principal);const before=await getCart(guest,'TRY',principal.id);
   await assert.rejects(()=>setCartItem(guest,v.id,quantity),{code:'CART_NOT_FOUND'});assert.deepEqual(await getCart(guest,'TRY',principal.id),before);
   await assert.rejects(()=>setCartItem(guest,privateVariant.id,quantity,'different-user'),{code:'CART_NOT_FOUND'});assert.deepEqual(await getCart(guest,'TRY',principal.id),before);
  }
 });
 await check('A cart read snapshot begun before merge contains only the original anonymous rows',async()=>{
  const {principal,guest}=await ownershipRace(),barrier=await pool.connect();let pending:Promise<Awaited<ReturnType<typeof getCart>>>|undefined;
  try{await barrier.query('BEGIN');await barrier.query('LOCK TABLE variant_prices IN ACCESS EXCLUSIVE MODE');pending=getCart(guest);
   let waiting=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT ci.variant_id,ci.quantity,%'")).length){waiting=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(waiting,'The cart read must reach its item query after the ownership snapshot');
   await mergeCustomerCart(guest,principal);await barrier.query('ROLLBACK');const snapshot=await pending;assert.deepEqual(snapshot.items.map(item=>item.variantId),[v.id]);
   await assert.rejects(()=>getCart(guest),{code:'CART_NOT_FOUND'});assert.equal((await getCart(guest,'TRY',principal.id)).items.length,2);
  }finally{await barrier.query('ROLLBACK');if(pending)await pending.catch(()=>{});barrier.release();}
 });
 await check('Updates and deletion begun first hold the cart lock through their response and serialize the member merge',async()=>{
  for(const quantity of [2,0]){const {principal,guest}=await ownershipRace(),barrier=await pool.connect();let writing:Promise<Awaited<ReturnType<typeof setCartItem>>>|undefined,merging:Promise<string>|undefined;
   try{await barrier.query('BEGIN');await barrier.query('LOCK TABLE variant_prices IN ACCESS EXCLUSIVE MODE');writing=setCartItem(guest,v.id,quantity);
    let waiting=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT ci.variant_id,ci.quantity,%'")).length){waiting=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(waiting,'Cart update must pause in its response projection');
    merging=mergeCustomerCart(guest,principal);let blocked=false;for(let attempt=0;attempt<100;attempt++){if((await query("SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT * FROM carts WHERE token_hash=%FOR UPDATE'")).length){blocked=true;break;}await new Promise(resolve=>setTimeout(resolve,20));}assert(blocked,'Member merge must wait on the writing cart row');
    await barrier.query('ROLLBACK');const result=await writing;assert(!result.items.some(item=>item.variantId===privateVariant.id));assert.equal(result.items.find(item=>item.variantId===v.id)?.quantity??0,quantity);await merging;
    await assert.rejects(()=>getCart(guest),{code:'CART_NOT_FOUND'});assert((await getCart(guest,'TRY',principal.id)).items.some(item=>item.variantId===privateVariant.id));
   }finally{await barrier.query('ROLLBACK');if(writing)await writing.catch(()=>{});if(merging)await merging.catch(()=>{});barrier.release();}
  }
 });
 await check('Competing member claims serialize and never transfer a cart owned by the first member',async()=>{
  const guest=newToken();await setCartItem(guest,v.id,1);const first={id:'first-'+newToken(),role:'customer' as const,mfa:false},second={id:'second-'+newToken(),role:'customer' as const,mfa:false};
  const outcomes=await Promise.all([mergeCustomerCart(guest,first),mergeCustomerCart(guest,second)]);assert.equal(outcomes.filter(value=>value===guest).length,1);
  const [cart]=await query('SELECT user_id FROM carts WHERE token_hash=$1',[createHash('sha256').update(guest).digest('hex')]);assert([first.id,second.id].includes(cart.user_id));
  const winner=cart.user_id===first.id?first:second,loser=cart.user_id===first.id?second:first;assert.equal((await getCart(guest,'TRY',winner.id)).items.length,1);await assert.rejects(()=>getCart(guest,'TRY',loser.id),{code:'CART_NOT_FOUND'});
 });
 process.env.BETTER_AUTH_SECRET=originalSecret;
 console.log(`Security boundary integration: ${passed} checks passed.`);
} finally {
 if(closePool)await closePool();
 if(created)await control.query(`DROP DATABASE "${databaseName}"`);
 await control.end();
}
