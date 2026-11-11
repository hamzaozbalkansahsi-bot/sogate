/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/privacy.spec.ts
 * Açıklama   : Anonim başvuru, özel takip, hesap sahipliği ve MFA destek kuyruğunun tarayıcı sınırlarını doğrular.
 */
import {prepareMfaFixture} from './helpers/mfa';
import {test,expect,type BrowserContext} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
const origin='http://127.0.0.1:3000';
function localDatabase(){
 const url=new URL(process.env.DATABASE_URL??'');
 if(!['development','test'].includes(process.env.APP_ENV??'')||!['127.0.0.1','localhost'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname))throw new Error('Mahremiyet E2E yalnız bu projenin yerel geliştirme/test veritabanına yazılabilir.');
 return new pg.Pool({connectionString:url.href});
}
async function adult(context:BrowserContext){await context.addCookies([{name:'sexsogate_adult',value:'yes',url:origin}]);}
async function cleanup(pool:pg.Pool,cases:string[],users:string[]=[]){
 try{
  if(cases.length){await pool.query("DELETE FROM jobs WHERE dedupe_key=ANY($1::text[])",[cases.flatMap(id=>[`privacy-received:${id}`,`privacy-response:${id}`])]);await pool.query("DELETE FROM audit_log WHERE resource='privacy' AND resource_id=ANY($1::text[])",[cases]);await pool.query('DELETE FROM privacy_requests WHERE id=ANY($1::text[])',[cases]);}
  if(users.length)await pool.query('DELETE FROM "user" WHERE id=ANY($1::text[])',[users]);
 }finally{await pool.end();}
}
async function account(context:BrowserContext,pool:pg.Pool,suffix:string,role='customer'){
 const {getAuth}=await import('../../src/server/auth'),email=`privacy-${suffix}@example.invalid`,password=randomBytes(24).toString('base64url');
 const signup=await getAuth().api.signUpEmail({body:{email,password,name:'Mahremiyet Akış Testi'},returnHeaders:true});
 await context.addCookies(signup.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],i=pair.indexOf('=');return {name:pair.slice(0,i),value:pair.slice(i+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));
 await pool.query('UPDATE "user" SET role=$2 WHERE id=$1',[signup.response.user.id,role]);await adult(context);return {id:signup.response.user.id,email,password};
}
for(const locale of ['tr','en'] as const)test(`Anonymous ${locale} request preserves Turkish text and exposes only private minimal tracking`,async({page})=>{
 const pool=localDatabase(),suffix=randomBytes(6).toString('hex'),cases:string[]=[],en=locale==='en',path=(en?'/en':'')+'/veri-basvurusu';
 const summary=`Hamza ÖZBALKAN İstanbul İzmir Iğdır Şişli Çeşme İç Giyim Ölçü ve Özellikler Güvenli Alışveriş ${suffix}`;
 try{
  // Next dev overrides document Cache-Control with no-store (base-server.js); APIs must retain private, no-store.
  await adult(page.context());const documentResponse=await page.goto(path);expect(documentResponse?.status()).toBe(200);expect(documentResponse?.headers()['cache-control']).toContain('no-store');expect(documentResponse?.headers()['cache-control']).not.toMatch(/\bpublic\b|s-maxage/i);expect(documentResponse?.headers()['x-robots-tag']).toContain('noindex');await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content',/noindex/);await expect(page.locator('html')).toHaveAttribute('lang',locale);
  await expect(page.getByRole('heading',{name:en?'Data privacy request':'Veri gizliliği başvurusu',exact:true})).toBeVisible();await page.setViewportSize({width:1440,height:1000});await page.screenshot({path:`docs/screenshots/privacy-${locale}-form-desktop-${test.info().project.name}.png`,fullPage:true});
  await page.getByLabel(en?'Email address':'E-posta adresi',{exact:true}).fill(`anonymous-${suffix}@example.invalid`);await page.getByRole('combobox',{name:en?'Request topic':'Talep konusu',exact:true}).selectOption('access');await page.getByLabel(en?'Country code, if known':'Biliyorsanız ülke kodu',{exact:true}).fill('TR');await page.getByLabel(en?'Your request':'Talebiniz',{exact:true}).fill(summary);
  const responsePromise=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/privacy'&&response.request().method()==='POST');await page.getByRole('button',{name:en?'Submit request':'Başvuruyu kaydet',exact:true}).click();const response=await responsePromise;expect(response.status()).toBe(201);
  // Tam gezinmeden sonra eski document'in POST gövdesine erişilmez; gerçek hedefin yetkisi sınanır.
  await expect(page).toHaveURL(new RegExp(`${path}\\?case=`));const destination=new URL(page.url()),created={id:destination.searchParams.get('case')??'',token:destination.searchParams.get('token')??''};expect(destination.pathname).toBe(path);expect(created.id.length).toBeGreaterThan(0);expect(created.token).toMatch(/^[A-Za-z0-9_-]{43}$/);cases.push(created.id);
  const tracked=await page.request.get(`/api/privacy?case=${encodeURIComponent(created.id)}&token=${encodeURIComponent(created.token)}`);expect(tracked.ok()).toBeTruthy();expect(tracked.headers()['cache-control']).toContain('private');expect(tracked.headers()['cache-control']).toContain('no-store');expect(tracked.headers()['x-robots-tag']).toContain('noindex');const body=await tracked.json();expect(Object.keys(body).sort()).toEqual(['dueAt','id','receivedAt','reference','status'].sort());expect(body.id).toBe(created.id);expect(body.status).toBe('received');await expect(page.getByRole('heading',{name:body.reference,exact:true})).toBeVisible();await expect(page.getByText(summary,{exact:true})).toHaveCount(0);expect(new URL(page.url()).searchParams.get('token')).toBe(created.token);
  expect((await page.request.get(`/api/privacy?case=${created.id}`)).status()).toBe(404);expect((await page.request.get(`/api/privacy?case=${created.id}&token=${'A'.repeat(43)}`)).status()).toBe(404);
  const [stored]=(await pool.query('SELECT reference,email,type,country,summary,tracking_hash,locale FROM privacy_requests WHERE id=$1',[created.id])).rows;expect(stored.reference).toBe(body.reference);expect(stored.email).toBe(`anonymous-${suffix}@example.invalid`);expect(stored.type).toBe('access');expect(stored.country).toBe('TR');expect(stored.summary).toBe(summary);expect(stored.locale).toBe(locale);expect(stored.tracking_hash).not.toBe(created.token);const {createHash}=await import('node:crypto');expect(stored.tracking_hash).toBe(createHash('sha256').update(created.token).digest('hex'));
  const jobs=JSON.stringify((await pool.query('SELECT payload FROM jobs WHERE dedupe_key=$1',[`privacy-received:${created.id}`])).rows);expect(jobs).not.toContain(created.token);expect(jobs).not.toContain(`anonymous-${suffix}@example.invalid`);expect(jobs).not.toContain(summary);
  await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:`docs/screenshots/privacy-${locale}-status-mobile-${test.info().project.name}.png`,fullPage:true});
 }finally{const own=(await pool.query('SELECT id FROM privacy_requests WHERE email=$1 AND summary=$2 AND locale=$3',[`anonymous-${suffix}@example.invalid`,summary,locale])).rows;cases.push(...own.map(row=>String(row.id)));await cleanup(pool,cases);}
});

test('Account ownership, status capabilities and MFA support/depot roles restrict private case fields',async({page,browser})=>{
 const pool=localDatabase(),suffix=randomBytes(6).toString('hex'),users:string[]=[],cases:string[]=[],other=await browser.newContext({baseURL:origin}),staff=await browser.newContext({baseURL:origin});
 const privateSummary=`Yalnız hesap sahibi için İstanbul Şişli Çeşme başvuru açıklaması ${suffix}`;
 try{
  const before=(await pool.query('SELECT (SELECT count(*)::int FROM privacy_controllers) controllers,(SELECT count(*)::int FROM privacy_policies) policies')).rows[0];
  const a=await account(page.context(),pool,`${suffix}-a`);users.push(a.id);const b=await account(other,pool,`${suffix}-b`);users.push(b.id);const support=await account(staff,pool,`${suffix}-support`,'support');users.push(support.id);
  const createdResponse=await page.request.post('/api/privacy',{headers:{origin},data:{email:a.email,type:'erasure',summary:privateSummary,locale:'tr'}});expect(createdResponse.status(),await createdResponse.text()).toBe(201);const aCase=await createdResponse.json() as {id:string;reference:string;token:string};cases.push(aCase.id);
  const bResponse=await other.request.post('/api/privacy',{headers:{origin},data:{email:b.email,type:'access',summary:'Başka hesabın kendine özel izole erişim başvurusu.',locale:'en'}});expect(bResponse.status()).toBe(201);const bCase=await bResponse.json() as {id:string};cases.push(bCase.id);
  const owned=await page.request.get(`/api/privacy?case=${aCase.id}`);expect(owned.ok()).toBeTruthy();const ownedBody=await owned.json();expect(ownedBody.summary).toBe(privateSummary);expect(ownedBody.responses).toEqual([]);expect((await other.request.get(`/api/privacy?case=${aCase.id}`)).status()).toBe(404);
  const capability=await other.request.get(`/api/privacy?case=${aCase.id}&token=${aCase.token}`);expect(capability.ok()).toBeTruthy();expect(Object.keys(await capability.json()).sort()).toEqual(['dueAt','id','receivedAt','reference','status'].sort());
  const mine=await (await page.request.get('/api/privacy')).json();expect(mine.requests.some((item:{id:string})=>item.id===aCase.id)).toBe(true);expect(mine.requests.some((item:{id:string})=>item.id===bCase.id)).toBe(false);expect((await page.request.post('/api/privacy',{headers:{origin},data:{email:b.email,type:'access',summary:privateSummary,locale:'tr'}})).status()).toBe(400);
  await page.goto('/hesap');await page.getByRole('button',{name:'Veri başvuruları',exact:true}).click();await expect(page.getByRole('link',{name:new RegExp(aCase.reference)})).toBeVisible();await page.getByRole('link',{name:new RegExp(aCase.reference)}).click();await expect(page.getByText(privateSummary,{exact:true})).toBeVisible();
  expect((await staff.request.get('/api/admin/privacy')).status()).toBe(403);
  const verified=await prepareMfaFixture(staff,support.password);expect(verified.ok()).toBeTruthy();
  const queue=await staff.request.get(`/api/admin/privacy?q=${encodeURIComponent(aCase.reference)}`);expect(queue.ok(),await queue.text()).toBeTruthy();expect(queue.headers()['cache-control']).toContain('no-store');expect((await queue.json()).rows[0].summary).toBe(privateSummary);expect((await staff.request.post('/api/admin/privacy',{headers:{origin},data:{action:'controller'}})).status()).toBe(403);
  expect((await staff.request.post('/api/admin/privacy',{headers:{origin},data:{action:'respond',id:aCase.id,response:'Kimlik incelemesi olmadan özel veri açıklanmamalıdır.',reference:'İzole yetkisiz geçiş kontrol referansı',outcome:'fulfilled'}})).status()).toBe(409);
  const staffPage=await staff.newPage();await staffPage.goto('/yonetim/privacy');await expect(staffPage.getByRole('heading',{name:'Kişisel veri başvuruları',exact:true})).toBeVisible();await staffPage.getByLabel('Gizlilik başvurularında ara',{exact:true}).fill(aCase.reference);await staffPage.getByRole('button',{name:'Ara',exact:true}).click();await staffPage.getByRole('row').filter({hasText:aCase.reference}).getByRole('button',{name:'Başvuruyu aç',exact:true}).click();const modal=staffPage.getByRole('dialog',{name:'Gizlilik başvurusu',exact:true});await expect(modal.getByText(privateSummary,{exact:true})).toBeVisible();await modal.getByLabel('İnceleme / güvenli teslim referansı',{exact:true}).fill('Yalnız yerel E2E güvenli kanal inceleme kaydı');await modal.getByRole('button',{name:'İşlemi kaydet',exact:true}).click();await expect(modal).not.toBeVisible();expect((await pool.query('SELECT identity_status FROM privacy_requests WHERE id=$1',[aCase.id])).rows[0].identity_status).toBe('verified');
  await staffPage.setViewportSize({width:1440,height:1000});await staffPage.screenshot({path:`docs/screenshots/privacy-support-desktop-${test.info().project.name}.png`,fullPage:true});await staffPage.setViewportSize({width:390,height:844});expect(await staffPage.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await staffPage.screenshot({path:`docs/screenshots/privacy-support-mobile-${test.info().project.name}.png`,fullPage:true});
  await pool.query("UPDATE \"user\" SET role='warehouse' WHERE id=$1",[support.id]);const denied=await staff.request.get(`/api/admin/privacy?id=${aCase.id}`);expect(denied.status()).toBe(403);expect(await denied.text()).not.toContain(privateSummary);expect((await staff.request.post('/api/admin/privacy',{headers:{origin},data:{action:'verify',id:aCase.id,method:'secure_channel',reference:'Depo rolünün ret edilmesi sınaması'}})).status()).toBe(403);await staffPage.reload();await expect(staffPage.getByText('Bu gizlilik işlemi için yetkiniz yok.',{exact:true})).toBeVisible();await expect(staffPage.getByText(privateSummary,{exact:true})).toHaveCount(0);
  expect((await pool.query('SELECT (SELECT count(*)::int FROM privacy_controllers) controllers,(SELECT count(*)::int FROM privacy_policies) policies')).rows[0]).toEqual(before);
 }finally{await other.close();await staff.close();await cleanup(pool,cases,users);}
});
