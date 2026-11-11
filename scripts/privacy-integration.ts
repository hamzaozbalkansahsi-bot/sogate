/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/privacy-integration.ts
 * Açıklama   : Veri sorumlusu, başvuru sahipliği ve sürümlü yanıt sürelerini izole veritabanında sınar.
 */
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
const base=process.env.TEST_DATABASE_URL;if(!base)throw new Error('TEST_DATABASE_URL gerekir.');
const url=new URL(base);if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('Yalnız izole yerel test DB kullanılabilir.');
const name=`sexsogate_${randomBytes(5).toString('hex')}_privacy_test`,control=new pg.Client({connectionString:base});await control.connect();await control.query(`CREATE DATABASE "${name}"`);url.pathname='/'+name;
process.env.DATABASE_URL=url.toString();process.env.APP_ENV='test';process.env.BETTER_AUTH_SECRET=randomBytes(48).toString('hex');
const {pool,query}=await import('../src/server/db');
let passed=0;async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
try{
 const privacy=await import('../src/server/privacy');await migrate(process.env.DATABASE_URL);
 const admin={id:'privacy-admin',role:'admin' as const,mfa:true},support={id:'privacy-support',role:'support' as const,mfa:true},a={id:'privacy-a',role:'customer' as const,mfa:false},b={id:'privacy-b',role:'customer' as const,mfa:false};
 await query('INSERT INTO "user"(id,name,email,"emailVerified",role) VALUES($1,$2,$3,true,\'customer\'),($4,$5,$6,true,\'customer\')',[a.id,'Hamza ÖZBALKAN','a@example.test',b.id,'Başka Kişi','b@example.test']);
 const summary='İstanbul, İzmir, Iğdır, Şişli ve Çeşme kayıtları için erişim başvurusu.';
 const anon=await privacy.createPrivacyRequest({email:'guest@example.test',type:'access',summary,country:'TR',locale:'tr'},null);
 const own=await privacy.createPrivacyRequest({email:'a@example.test',type:'erasure',summary,country:'TR',locale:'tr'},a);
 await check('Açık kural yokken başvuru kaybolmaz; token yalnız hash, e-posta işi şifreli saklanır',async()=>{
  const [row]=await query('SELECT * FROM privacy_requests WHERE id=$1',[anon.id]);assert.equal(row.status,'received');assert.equal(row.due_at,null);assert.notEqual(row.tracking_hash,anon.token);assert.equal(row.summary,summary);
  const jobs=JSON.stringify(await query("SELECT payload FROM jobs WHERE type='email.privacy'"));assert(!jobs.includes('guest@example.test'));assert(!jobs.includes(anon.token));
 });
 await check('Hesap sahipliği ve anonim takip yalnız asgari durum bilgisi döndürür',async()=>{
  assert.equal((await privacy.getPrivacyRequest(own.id,null,a)).id,own.id);await assert.rejects(()=>privacy.getPrivacyRequest(own.id,null,b));await assert.rejects(()=>privacy.getPrivacyRequest(own.id,null,null));
  const tracked=await privacy.getPrivacyRequest(anon.id,anon.token,null);assert(!('email' in tracked));assert(!('summary' in tracked));assert(!('responses' in tracked));
  await assert.rejects(()=>privacy.createPrivacyRequest({email:'b@example.test',type:'access',summary,locale:'tr'},a));
 });
 await check('Veri sorumlusu satıcı/geliştiriciden türetilmez; rol/MFA ve kanıt onayı gerekir',async()=>{
  await assert.rejects(()=>privacy.saveController({action:'controller',legalName:'Test Veri Sorumlusu',address:'İstanbul test adresi',email:'controller@example.test',evidence:'İzole test kanıtı',approve:true},support));
  await assert.rejects(()=>privacy.saveController({action:'controller',legalName:'Test Veri Sorumlusu',address:'İstanbul test adresi',email:'controller@example.test',evidence:'İzole test kanıtı',approve:true},{...admin,mfa:false}));
  await privacy.saveController({action:'controller',legalName:'Test Veri Sorumlusu',address:'İstanbul test adresi',email:'controller@example.test',evidence:'Yalnız izole test için incelenmiş kimlik kaydı',approve:true},admin);
  assert.equal((await query("SELECT count(*) n FROM settings WHERE key='seller.name'"))[0].n,0);
 });
 await check('Onaylı süre kuralı ilk alım anından hesaplanır; önceki başvuruya sessiz süre uzatmaz',async()=>{
  await query("UPDATE privacy_requests SET received_at='2028-01-31T10:30:00Z' WHERE id=$1",[anon.id]);
  await privacy.savePrivacyPolicy({action:'policy',country:'TR',unit:'months',count:1,timeZone:'Europe/Istanbul',source:'https://www.kvkk.gov.tr/',evidence:'Yalnız izole test; hukuki süre kabulü değildir',retentionNote:'Mali kayıtlar ayrı yasal saklama incelemesine tabidir.',approve:true},admin);
  const [row]=await query('SELECT due_at,policy_id FROM privacy_requests WHERE id=$1',[anon.id]);assert.equal(row.due_at.toISOString(),'2028-02-29T10:30:00.000Z');
  await privacy.savePrivacyPolicy({action:'policy',country:'TR',unit:'days',count:10,timeZone:'Europe/Istanbul',source:'https://www.kvkk.gov.tr/',evidence:'Yeni izole test politika sürümü için kanıt',retentionNote:'Mali kayıtlar ayrı yasal saklama incelemesine tabidir.',approve:true},admin);
  assert.equal((await query('SELECT due_at FROM privacy_requests WHERE id=$1',[anon.id]))[0].due_at.toISOString(),row.due_at.toISOString());
 });
 await check('Kimlik doğrulanmadan veya dış işlem kanıtı olmadan yanıt tamamlandı sayılamaz',async()=>{
  await assert.rejects(()=>privacy.privacyAction({action:'respond',id:own.id,response:'Talebiniz değerlendirildi ve güvenli kanaldan yanıtlandı.',reference:'Dış süreç teslim kaydı',outcome:'fulfilled'},support));
  await privacy.privacyAction({action:'verify',id:own.id,method:'secure_channel',reference:'İzole güvenli kanal doğrulama kaydı'},support);
  await privacy.privacyAction({action:'start',id:own.id},support);
  await privacy.privacyAction({action:'respond',id:own.id,response:'Mali kayıtların saklanması ayrı değerlendirildi; dış süreçte yanıt teslim edildi.',reference:'İzole dış süreç imzalı teslim kaydı',outcome:'partially_fulfilled'},support);
  const detailed=await privacy.getPrivacyRequest(own.id,null,a);assert.equal(detailed.status,'responded');assert('responses' in detailed&&detailed.responses.length===1);
  assert.equal((await query('SELECT count(*) n FROM "user" WHERE id=$1',[a.id]))[0].n,1);
 });
 await check('Depo/pazarlama talepleri göremez; audit ve anonim takip özel metni sızdırmaz',async()=>{
  assert.equal((await privacy.privacyAdmin(support,{})).rows.length,2);
  await assert.rejects(()=>privacy.privacyAdmin({role:'warehouse',id:'w',mfa:true},{}));
  await assert.rejects(()=>privacy.privacyAdmin({role:'marketing',id:'m',mfa:true},{}));
  const audit=JSON.stringify(await query("SELECT details FROM audit_log WHERE resource='privacy'"));assert(!audit.includes('guest@example.test'));assert(!audit.includes(summary));
  const publicResult=await privacy.getPrivacyRequest(own.id,own.token,null);assert(!JSON.stringify(publicResult).includes('Mali kayıtların'));
 });
 await check('Ülke değişiminden sonra yeni kural geçmiş son yanıt zamanını uzatmaz',async()=>{
  const item=await privacy.createPrivacyRequest({email:'route@example.test',type:'access',summary,country:'TR',locale:'en'},null);
  const [before]=await query('SELECT due_at FROM privacy_requests WHERE id=$1',[item.id]);
  await privacy.privacyAction({action:'route',id:item.id,country:'GB',reference:'Test ülke incelemesi için kanıt'},support);
  await privacy.savePrivacyPolicy({action:'policy',country:'GB',unit:'days',count:30,timeZone:'Europe/London',source:'https://ico.org.uk/',evidence:'Yalnız izole test için kural kanıtı',retentionNote:'Bu süre gerçek hukuk kararı değildir; saklama ayrı değerlendirilir.',approve:true},admin);
  const [after]=await query('SELECT due_at,policy_id FROM privacy_requests WHERE id=$1',[item.id]);assert(after.policy_id);assert.equal(after.due_at.toISOString(),before.due_at.toISOString());
 });
 await check('Eşzamanlı kural onayı ve başvuru alımı aynı ülke kilidiyle tutarlı kalır',async()=>{
  const blocker=await pool.connect();
  async function waitForBlocked(count:number){for(let i=0;i<100;i++){const [row]=await query("SELECT count(*) n FROM pg_stat_activity WHERE datname=current_database() AND wait_event='advisory'");if(Number(row.n)>=count)return;await new Promise(resolve=>setTimeout(resolve,20));}assert.fail('Beklenen ülke kilidi alınmadı');}
  try{
   await blocker.query('BEGIN');await blocker.query("SELECT pg_advisory_xact_lock(hashtext('privacy-policy:FR'))");
   const approval=privacy.savePrivacyPolicy({action:'policy',country:'FR',unit:'days',count:12,timeZone:'Europe/Paris',source:'https://www.cnil.fr/',evidence:'Yalnız izole eşzamanlılık test kanıtı',retentionNote:'Bu süre gerçek hukuk kararı değildir; saklama ayrı değerlendirilir.',approve:true},admin);
   await waitForBlocked(1);
   const creation=privacy.createPrivacyRequest({email:'race@example.test',type:'access',summary,country:'FR',locale:'en'},null);await waitForBlocked(2);
   await blocker.query('COMMIT');const [policy,item]=await Promise.all([approval,creation]);
   const [row]=await query('SELECT due_at,policy_id FROM privacy_requests WHERE id=$1',[item.id]);assert.equal(row.policy_id,policy.id);assert(row.due_at);
  }finally{await blocker.query('ROLLBACK');blocker.release();}
 });
 await check('Doğrulanmamış hesap eşleşmesi reddedilir; kimlik eksikliği gerekçeli ayrı kapanır',async()=>{
  const item=await privacy.createPrivacyRequest({email:'b@example.test',type:'access',summary,country:'TR',locale:'en'},b);
  await query('UPDATE "user" SET "emailVerified"=false WHERE id=$1',[b.id]);
  await assert.rejects(()=>privacy.privacyAction({action:'verify',id:item.id,method:'authenticated_account',reference:'Doğrulanmamış hesap eşleştirme testi'},support));
  await privacy.privacyAction({action:'identity_rejection',id:item.id,response:'Kimlik eşleştirmesi güvenli biçimde tamamlanamadı; özel veri açıklanmadan gerekçe iletildi.',reference:'İzole testte gerekçeli güvenli teslim kaydı'},support);
  const [row]=await query('SELECT status,identity_status FROM privacy_requests WHERE id=$1',[item.id]);assert.equal(row.status,'rejected');assert.equal(row.identity_status,'pending');
  await assert.rejects(()=>privacy.privacyAction({action:'start',id:item.id},support));
 });
 await check('Production yerel kimlik/kural fixture kaydını kullanmaz; saat dilimi doğrulanır',async()=>{
  await assert.rejects(()=>privacy.savePrivacyPolicy({action:'policy',country:'TR',unit:'days',count:5,timeZone:'Invalid/Zone',source:'https://www.kvkk.gov.tr/',evidence:'İzole hatalı saat dilimi testi kanıtı',retentionNote:'Mali kayıtların saklama koşulu ayrıca değerlendirilir.',approve:false},admin));
  process.env.APP_ENV='production';try{
   const item=await privacy.createPrivacyRequest({email:'production@example.test',type:'access',summary,country:'TR',locale:'tr'},null);
   const [row]=await query('SELECT due_at,policy_id FROM privacy_requests WHERE id=$1',[item.id]);assert.equal(row.policy_id,null);assert.equal(row.due_at,null);
  }finally{process.env.APP_ENV='test';}
 });
 await check('İletişim formundaki veri başvurusu aynı iş akışına girer; sabit hukuki süre üretilmez',async()=>{
  const {contact}=await import('../src/server/customer');const result=await contact({email:'contact@example.test',kind:'privacy',message:summary,locale:'en'},null);assert('privacy' in result&&result.privacy);
  assert.equal((await query('SELECT count(*) n FROM contact_requests WHERE id=$1',[result.id]))[0].n,0);
  const [row]=await query('SELECT due_at,locale FROM privacy_requests WHERE id=$1',[result.id]);assert.equal(row.due_at,null);assert.equal(row.locale,'en');
  const tracked=await privacy.getPrivacyRequest(own.id,own.token,b);assert(!('responses' in tracked));
 });
 await check('Canlı hazırlık yerel veri sorumlusu ve ülke kuralını gerçek onay yerine kullanmaz',async()=>{
  await assert.rejects(()=>privacy.assertPrivacyLaunchReady());
  await query("UPDATE privacy_controllers SET fixture=false WHERE status='approved'");
  await query("INSERT INTO country_rules(code,name,enabled,fixture) VALUES('TR','Türkiye',true,false) ON CONFLICT(code) DO UPDATE SET enabled=true,fixture=false");
  await assert.rejects(()=>privacy.assertPrivacyLaunchReady());
  await query("UPDATE privacy_policies SET fixture=false WHERE country='TR' AND approved=true");await privacy.assertPrivacyLaunchReady();
  await privacy.saveController({action:'controller',legalName:'Yeni Test Veri Sorumlusu',address:'İzmir test adresi',email:'new-controller@example.test',evidence:'Yeni izole test kimliği; gerçekte kullanılmaz',approve:true},admin);
  assert.equal((await query('SELECT count(*) n FROM privacy_policies WHERE approved=true'))[0].n,0);await assert.rejects(()=>privacy.assertPrivacyLaunchReady());
  // Önceden kabul edilen başvuru kendi onaylı sürümünü korur.
  const [oldCase]=await query("SELECT id FROM privacy_requests WHERE identity_status='pending' AND policy_id IS NOT NULL AND status='received' LIMIT 1");
  await privacy.privacyAction({action:'verify',id:oldCase.id,method:'secure_channel',reference:'Eski sürüme bağlı izole test incelemesi'},support);await privacy.privacyAction({action:'start',id:oldCase.id},support);
 });
 await check('Boş ileri sayfa gerçek toplamı sıfırlamaz',async()=>{
  const result=await privacy.privacyAdmin(support,{page:999});assert.equal(result.rows.length,0);assert.equal(result.total,7);
 });
 console.log(`Privacy integration: ${passed} checks passed.`);
}finally{await pool.end();await control.query('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1',[name]);await control.query(`DROP DATABASE "${name}"`);await control.end();}
