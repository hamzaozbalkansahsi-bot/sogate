/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/privacy-detail-race.spec.ts
 * Açıklama   : Geç dönen başvuru detayının başka başvurunun ekranına karışmasını gerçek API yanıtlarıyla sınar.
 */
import {prepareMfaFixture} from './helpers/mfa';
import {test,expect} from '@playwright/test';
import pg from 'pg';
import {randomBytes} from 'node:crypto';

const origin='http://127.0.0.1:3000';
test.use({actionTimeout:15000});

test('a late A detail response never replaces the visible B privacy response',async({page})=>{
 test.setTimeout(60000);
 test.skip(!['development','test'].includes(process.env.APP_ENV??''),'Yalnız bu projenin yerel geliştirme/test verisi');
 const databaseUrl=new URL(process.env.DATABASE_URL??'');
 if(!['127.0.0.1','localhost'].includes(databaseUrl.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(databaseUrl.pathname))throw new Error('Gizlilik detay testi yalnız bu projenin yerel veritabanında çalışabilir.');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL}),suffix=randomBytes(7).toString('hex'),cases:{id:string;reference:string;summary:string;response:string}[]=[];
 let userId='',releaseA=()=>{},heldStatus=0,heldBody:unknown;
 const held=new Promise<void>(resolve=>{releaseA=resolve;});
 try{
  const {getAuth}=await import('../../src/server/auth'),password=randomBytes(24).toString('base64url');
  const signup=await getAuth().api.signUpEmail({body:{email:`privacy-race-${suffix}@example.invalid`,password,name:'Detay Sırası Destek Testi'},returnHeaders:true});userId=signup.response.user.id;
  await page.context().addCookies(signup.headers.getSetCookie().map(cookie=>{
   const pair=cookie.split(';')[0],separator=pair.indexOf('=');
   return {name:pair.slice(0,separator),value:pair.slice(separator+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};
  }));
  await pool.query('UPDATE "user" SET role=\'support\' WHERE id=$1',[userId]);
  const verified=await prepareMfaFixture(page.context(),password);expect(verified.ok()).toBeTruthy();
  // Ortak kimlik veya süre politikası değiştirilmez; yalnız bu teste ait iki kapanmış başvuru okunur.
  for(const label of ['A','B']){
   const summary=`${label} başvurusunun özel özeti ${suffix}`,response=`YALNIZ-${label}-${suffix}: Bu yanıt sadece ilgili başvurunun kendi ekranında gösterilir.`;
   const row=(await pool.query("INSERT INTO privacy_requests(email,type,summary,country,locale,tracking_hash,identity_status,status) VALUES($1,'access',$2,'TR','tr',$3,'verified','responded') RETURNING id,reference",[`privacy-${label.toLowerCase()}-${suffix}@example.invalid`,summary,randomBytes(32).toString('hex')])).rows[0];
   cases.push({id:row.id,reference:row.reference,summary,response});
   await pool.query("INSERT INTO privacy_responses(request_id,actor_id,body,outcome,external_reference) VALUES($1,$2,$3,'fulfilled',$4)",[row.id,userId,response,`Yalnız yerel detay testi teslim referansı ${label}-${suffix}`]);
  }
  const [a,b]=cases;
  await page.route(url=>url.pathname==='/api/admin/privacy'&&url.searchParams.get('id')===a.id,async route=>{
   const response=await route.fetch();heldStatus=response.status();heldBody=await response.json();
   await held;await route.fulfill({response});
  });
  await page.goto('/yonetim/privacy');
  await expect(page.getByRole('heading',{name:'Kişisel veri başvuruları',exact:true})).toBeVisible();
  const search=page.getByLabel('Gizlilik başvurularında ara',{exact:true});
  await search.fill(a.reference);await page.getByRole('button',{name:'Ara',exact:true}).click();
  await page.getByRole('row').filter({hasText:a.reference}).getByRole('button',{name:'Başvuruyu aç',exact:true}).click();
  let modal=page.getByRole('dialog',{name:'Gizlilik başvurusu',exact:true});
  await expect(modal.getByText(a.summary,{exact:true})).toBeVisible();
  await expect.poll(()=>heldStatus).toBe(200);
  expect(JSON.stringify(heldBody).includes(a.response)).toBe(true);
  await modal.getByRole('button',{name:'Kapat / Close',exact:true}).click();
  await expect(modal).not.toBeVisible();
  await search.fill(b.reference);await page.getByRole('button',{name:'Ara',exact:true}).click();
  await page.getByRole('row').filter({hasText:b.reference}).getByRole('button',{name:'Başvuruyu aç',exact:true}).click();
  modal=page.getByRole('dialog',{name:'Gizlilik başvurusu',exact:true});
  await expect(modal.getByText(b.summary,{exact:true})).toBeVisible();
  await expect(modal.getByText(b.response,{exact:true})).toBeVisible();
  // Son durumun yanında, A cevabı teslim edilirken oluşabilecek kısa DOM sızıntısını da izler.
  await page.evaluate(response=>{
   const dialog=document.querySelector('dialog[open]');if(!dialog)throw new Error('Başvuru ekranı açık olmalıdır.');
   const state={leaked:false,observer:null as MutationObserver|null};
   const inspect=()=>{if((dialog.textContent??'').includes(response))state.leaked=true;};
   state.observer=new MutationObserver(inspect);state.observer.observe(dialog,{subtree:true,childList:true,characterData:true});inspect();
   (window as Window&{__privacyRaceObservation?:typeof state}).__privacyRaceObservation=state;
  },a.response);
  const delivered=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/admin/privacy'&&new URL(response.url()).searchParams.get('id')===a.id);
  releaseA();const lateResponse=await delivered;expect(lateResponse.status()).toBe(200);await lateResponse.finished();
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  await expect(modal.getByText(b.summary,{exact:true})).toBeVisible();
  await expect(modal.getByText(b.response,{exact:true})).toBeVisible();
  await expect(modal.getByText(a.response,{exact:true})).toHaveCount(0);
  const leaked=await page.evaluate(()=>Boolean((window as Window&{__privacyRaceObservation?:{leaked:boolean}}).__privacyRaceObservation?.leaked));expect(leaked).toBe(false);
 }finally{
  releaseA();await page.unrouteAll({behavior:'wait'}).catch(()=>{});
  await page.evaluate(()=>{
   const browser=window as Window&{__privacyRaceObservation?:{observer:MutationObserver|null}};browser.__privacyRaceObservation?.observer?.disconnect();delete browser.__privacyRaceObservation;
  }).catch(()=>{});
  if(cases.length)await pool.query('DELETE FROM privacy_requests WHERE id=ANY($1::text[])',[cases.map(value=>value.id)]);
  if(userId)await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);await pool.end();
 }
});
