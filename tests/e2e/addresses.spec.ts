/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/addresses.spec.ts
 * Açıklama   : Ülkeye özel adres alanlarını, hesap sahipliğini ve geciken liste yanıtına karşı kayıt korunmasını sınar.
 */
import {test,expect} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import type {AddressField} from '../../src/shared/address-fields';
const origin='http://127.0.0.1:3000';
test('country fields and address editing preserve Unicode and a late initial list cannot hide a saved address',async({page},testInfo)=>{
 test.setTimeout(75000);
 const url=new URL(process.env.DATABASE_URL??'');
 if(!['development','test'].includes(process.env.APP_ENV??'')||!['localhost','127.0.0.1'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname))throw new Error('Yalnız bu projenin izole yerel verisi kullanılabilir.');
 const pool=new pg.Pool({connectionString:url.toString()}),suffix=randomBytes(6).toString('hex');
 let country='',userId='',release=()=>{};
 try{
  const codes=['XZ','XW','XV'];const own=await pool.query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) SELECT candidate.code,$2,true,true,true,true,true,true,true,500,'TRY',true FROM unnest($1::text[]) AS candidate(code) WHERE NOT EXISTS(SELECT 1 FROM country_rules c WHERE c.code=candidate.code) LIMIT 1 ON CONFLICT DO NOTHING RETURNING code",[codes,`Address fixture ${suffix}`]);
  country=own.rows[0]?.code;if(!country)throw new Error('Bağımsız test ülke kodu bulunamadı.');
  const fields:AddressField[]=[
   {id:'fullName',label:{tr:'Ad soyad',en:'Full name'},required:true,minLength:2,maxLength:120,format:'text'},
   {id:'line1',label:{tr:'Adres',en:'Address'},required:true,minLength:5,maxLength:300,format:'text'},
   {id:'city',label:{tr:'Şehir',en:'City'},required:true,minLength:2,maxLength:100,format:'text'},
   {id:'region',label:{tr:'Bölge',en:'Region'},required:true,minLength:2,maxLength:100,format:'text'},
  ];
  await pool.query("INSERT INTO country_address_profiles(country,version,fields,status,fixture,reference,created_by,approved_by,approved_at) VALUES($1,1,$2,'approved',true,'İzole tarayıcı alan tanımı; gerçek ülke onayı değildir',$3,$3,now())",[country,JSON.stringify(fields),`address-e2e-${suffix}`]);
  const {getAuth}=await import('../../src/server/auth');
  const signup=await getAuth().api.signUpEmail({body:{email:`address-${suffix}@example.invalid`,password:randomBytes(24).toString('base64url'),name:'Hamza ÖZBALKAN'},returnHeaders:true});userId=signup.response.user.id;
  await page.context().addCookies(signup.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],at=pair.indexOf('=');return {name:pair.slice(0,at),value:pair.slice(at+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',url:origin},{name:'sexsogate_country',value:country,url:origin}]);
  const ready=await page.request.get('/api/address-profile?country='+country);expect(ready.status()).toBe(200);const metadata=await ready.json();expect(metadata.fields.map((field:AddressField)=>field.id)).toEqual(['fullName','line1','city','region']);expect(JSON.stringify(metadata)).not.toContain('address-e2e');
  const invalid=await page.request.post('/api/addresses',{headers:{Origin:origin},data:{label:'Missing region',country,fullName:'Hamza ÖZBALKAN',line1:'Şişli Çeşme Sokak 12',city:'İstanbul'}});expect(invalid.status()).toBe(400);
  const gate=new Promise<void>(resolve=>{release=resolve;});let captured=false;
  await page.route(url=>url.pathname==='/api/addresses',async route=>{
   if(route.request().method()==='GET'&&!captured){captured=true;const response=await route.fetch();await gate;await route.fulfill({response});}else await route.continue();
  });
  await page.goto('/en/hesap');await page.locator('.account-nav').getByRole('button',{name:'My addresses',exact:true}).click();await expect.poll(()=>captured).toBe(true);
  await page.getByRole('button',{name:'Add an address',exact:true}).click();const form=page.getByRole('form',{name:'Address details'});
  await form.getByLabel('Address label',{exact:true}).fill('Şişli — Ev');await form.getByLabel('Full name',{exact:true}).fill('Hamza ÖZBALKAN');await form.getByLabel('Address',{exact:true}).fill('Çeşme Sokak, Şişli 12');await form.getByLabel('City',{exact:true}).fill('İstanbul');await form.getByLabel('Region',{exact:true}).fill('Iğdır · العربية · Москва');
  await expect(form.getByLabel('Postal code',{exact:true})).toHaveCount(0);await expect(form.getByLabel('Phone',{exact:true})).toHaveCount(0);
  await form.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByRole('heading',{name:'Şişli — Ev',exact:true})).toBeVisible();release();await page.unrouteAll({behavior:'wait'});await expect(page.getByRole('heading',{name:'Şişli — Ev',exact:true})).toBeVisible();
  const list=await page.request.get('/api/addresses');const id=(await list.json()).addresses[0].id;
  await page.getByRole('button',{name:'Edit',exact:true}).click();await form.getByLabel('City',{exact:true}).fill('İzmir');await form.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByText('İzmir · Iğdır · العربية · Москва',{exact:true})).toBeVisible();
  await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`docs/screenshots/address-book-mobile-${testInfo.project.name}.png`,fullPage:true});
  await page.getByRole('button',{name:'Remove',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('button',{name:'Remove address',exact:true}).click();await expect(page.getByRole('heading',{name:'Şişli — Ev',exact:true})).toHaveCount(0);
  expect((await page.request.get('/api/addresses')).status()).toBe(200);expect((await pool.query('SELECT id FROM customer_addresses WHERE id=$1',[id])).rows.length).toBe(0);
 }finally{
  release();await page.unrouteAll({behavior:'wait'});
  if(userId){await pool.query('DELETE FROM customer_addresses WHERE user_id=$1',[userId]);await pool.query('DELETE FROM audit_log WHERE actor_id=$1',[userId]);await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);}
  if(country){await pool.query('DELETE FROM country_address_events WHERE profile_id IN(SELECT id FROM country_address_profiles WHERE country=$1)',[country]);await pool.query('DELETE FROM country_address_profiles WHERE country=$1',[country]);await pool.query('DELETE FROM country_rules WHERE code=$1',[country]);}
  await pool.end();
 }
});
