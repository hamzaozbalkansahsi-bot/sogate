/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/legal-drafts-integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import assert from 'node:assert/strict';
import { createHash, randomBytes } from 'node:crypto';
import pg from 'pg';
import { migrate } from './migrate';
import { readLegalDrafts,seedLegalDrafts } from './legal-drafts';
import { seedFixtureAddressProfile } from './seed';

const drafts=await readLegalDrafts();
assert.equal(drafts.length,13);assert(drafts.every(draft=>draft.locale==='tr'&&draft.body.includes('{{')));
assert.equal(new Set(drafts.map(draft=>draft.kind)).size,13);
const base=process.env.TEST_DATABASE_URL;if(!base)throw new Error('TEST_DATABASE_URL gereklidir.');
const url=new URL(base);
if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('Yalnız yerel izole test DB kullanılabilir.');
const name=`sexsogate_${randomBytes(5).toString('hex')}_legal_test`,control=new pg.Client({connectionString:base});
await control.connect();await control.query(`CREATE DATABASE "${name}"`);url.pathname='/'+name;
process.env.APP_ENV='test';process.env.DATABASE_URL=url.toString();process.env.PAYMENT_PROVIDER='test';
process.env.BETTER_AUTH_SECRET=randomBytes(32).toString('hex');
const {pool,query}=await import('../src/server/db');
const core=await import('../src/server/commerce/index');
const admin={id:'legal-test-admin',role:'admin' as const,mfa:true};
let passed=0;async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try {
  await migrate(process.env.DATABASE_URL);
  // This freshly created DB is not a normal dev/test seed target. Its minimal
  // fixture is explicit and stays inside this test; seed.ts guards are preserved.
  await query("INSERT INTO categories(slug,name,name_en) VALUES('aksesuarlar','İzole test aksesuarı','Isolated test accessory')");
  await query("INSERT INTO warehouses(id,name) VALUES('main','İzole Test Deposu')");
  await query("INSERT INTO products(id,slug,name,name_en,category,image,material,status,fixture) VALUES('legal-product','legal-test-product','İzole Sözleşme Ürünü','Isolated agreement item','aksesuarlar','/media/atelier-01.svg','Test tekstili','published',true)");
  await query("INSERT INTO variants(id,product_id,sku,name,price_minor,cost_minor) VALUES('legal-variant','legal-product','LEGAL-FIXTURE','Standart',10001,1000)");
  await query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES('legal-variant','TRY',10001)");
  await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES('legal-variant','main',20)");
  await query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES('TR','İzole test ülkesi',true,true,true,true,true,true,true,100,'TRY',true)");
  await seedFixtureAddressProfile(pool);
  await query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture) VALUES('TR',2000,now()-interval '1 day',true)");
  const {complianceAction}=await import('../src/server/compliance');
  await complianceAction({action:'eligibility',variantId:'legal-variant',country:'TR',approved:true,requiredDocumentKind:null,reason:'Yalnız izole hukuk snapshot testi ülke onayı',idempotencyKey:randomBytes(32).toString('hex')},admin);
  for(const kind of ['privacy','terms']) {
    const body='Bu metin yalnız izole sözleşme snapshot testinin örnek verisidir. Gerçek hukuk onayı değildir.';
    await query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture) VALUES($1,'tr',$2,$3,1,'effective',$4,now(),true)",[kind,'İzole test '+kind,body,createHash('sha256').update(body).digest('hex')]);
  }
  const effective=await query('SELECT id,kind,body,version,status,body_hash FROM legal_documents WHERE status=\'effective\' ORDER BY id');
  await check('Thirteen real drafts stay admin-only, unapproved and separate from effective fixtures',async()=>{
    const result=await seedLegalDrafts(process.env.DATABASE_URL);assert.equal(result.created,13);
    const rows=await query('SELECT * FROM legal_documents WHERE fixture=false');assert.equal(rows.length,13);
    assert(rows.every(row=>row.status==='draft'&&row.approved_by===null&&row.approved_at===null&&row.effective_at===null));
    const adminView=await core.adminList('legal',admin) as {rows:Record<string,unknown>[]};
    assert(adminView.rows.some(row=>row.status==='draft'&&String(row.body).includes('{{')));
    const supportView=await core.adminList('legal',{id:'legal-test-support',role:'support',mfa:true}) as {rows:Record<string,unknown>[]};
    assert(supportView.rows.every(row=>row.status==='effective'));
    assert.deepEqual(await query('SELECT id,kind,body,version,status,body_hash FROM legal_documents WHERE status=\'effective\' ORDER BY id'),effective);
  });
  await check('Repeating draft load is idempotent and never overwrites a document',async()=>{
    const result=await seedLegalDrafts(process.env.DATABASE_URL);assert.equal(result.created,0);assert.equal(result.skipped,13);
    assert.equal((await query('SELECT count(*)::int AS n FROM legal_documents WHERE fixture=false'))[0].n,13);
  });
  await check('Placeholder text cannot be approved or activated',async()=>{
    const [draft]=await query('SELECT id FROM legal_documents WHERE fixture=false AND kind=\'privacy\'');
    await assert.rejects(()=>core.adminAction('legal',{action:'approve',id:draft.id,note:'İzole testte eksik alan denetimi'},admin));
    assert.equal((await query('SELECT status FROM legal_documents WHERE id=$1',[draft.id]))[0].status,'draft');
  });
  await check('A filled but approved text still cannot activate without real seller setup',async()=>{
    const body='Bu metin yalnız izole testte satıcı eksikliği kapısını doğrulamak için oluşturulmuştur. Gerçek hukuk onayı değildir.';
    const result=await core.adminAction('legal',{action:'create',kind:'privacy',locale:'tr',title:'İzole satıcı kapısı',body,version:99},admin) as {id:string};
    await core.adminAction('legal',{action:'approve',id:result.id,note:'Yalnız izole test durum geçişi'},admin);
    await assert.rejects(()=>core.adminAction('legal',{action:'activate',id:result.id,note:'Eksik satıcı nedeniyle reddedilmeli'},admin));
    assert.equal((await query('SELECT status FROM legal_documents WHERE id=$1',[result.id]))[0].status,'approved');
    assert.deepEqual(await query('SELECT id,kind,body,version,status,body_hash FROM legal_documents WHERE status=\'effective\' ORDER BY id'),effective);
  });
  await check('Production mode refuses draft seeding',async()=>{
    process.env.APP_ENV='production';await assert.rejects(()=>seedLegalDrafts(process.env.DATABASE_URL));process.env.APP_ENV='test';
  });
  await check('Later source-document edits cannot change accepted order agreement snapshots',async()=>{
    const product=(await core.listProducts({}))[0],variant=product.variants[0],token=randomBytes(32).toString('hex');
    await core.setCartItem(token,variant.id,1);
    const quote=await core.quoteCheckout(token,{country:'TR',currency:'TRY',locale:'tr'});
    const order=await core.checkout(token,{quoteToken:quote.quoteToken,email:'legal-test@example.invalid',fullName:'Yerel Sözleşme Testi',phone:'05000000000',line1:'İzole deneme adresi 12',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr',currency:'TRY',idempotencyKey:randomBytes(24).toString('hex'),privacyAccepted:true,termsAccepted:true});
    const original=await query('SELECT kind,version,locale,title,body,body_hash,accepted_at FROM order_agreements WHERE order_id=$1 ORDER BY kind',[order.orderId]);
    assert.equal(original.length,2);
    const changed='Kaynak belge siparişten sonra değiştirildi; geçmiş anlaşma aynı kalmalıdır.';
    await query('UPDATE legal_documents SET body=$1,body_hash=$2,title=$3 WHERE id IN(SELECT document_id FROM order_agreements WHERE order_id=$4)',[changed,createHash('sha256').update(changed).digest('hex'),'Sonraki kaynak değişikliği',order.orderId]);
    assert.deepEqual(await query('SELECT kind,version,locale,title,body,body_hash,accepted_at FROM order_agreements WHERE order_id=$1 ORDER BY kind',[order.orderId]),original);
  });
  console.log(`Legal integration: ${passed} checks passed.`);
} finally {
  await pool.end();await control.query(`DROP DATABASE "${name}"`);await control.end();
}
