/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/account-privacy.spec.ts
 * Açıklama   : Aynı hesap ekranında çıkış ve yeni giriş sonrası önceki kişinin verisi ile MFA taslağının temizlendiğini sınar.
 */
import {test,expect,type BrowserContext} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {submitSignIn} from './helpers/sign-in';

const origin='http://127.0.0.1:3000';
test.use({actionTimeout:15000});
async function fixtureAccount(context:BrowserContext,suffix:string,installCookies:boolean){
 const {getAuth}=await import('../../src/server/auth');
 const email=`account-owner-${suffix}@example.invalid`,password=randomBytes(24).toString('base64url');
 const signup=await getAuth().api.signUpEmail({body:{email,password,name:`Hesap Sahibi ${suffix}`},returnHeaders:true});
 if(installCookies)await context.addCookies(signup.headers.getSetCookie().map(cookie=>{
  const pair=cookie.split(';')[0],separator=pair.indexOf('=');
  return {name:pair.slice(0,separator),value:pair.slice(separator+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};
 }));
 return {id:signup.response.user.id,email,password,name:signup.response.user.name};
}

test('logout and sign-in on the same page never expose the previous owner while new data is delayed',async({page})=>{
 test.setTimeout(90000);
 test.skip(!['development','test'].includes(process.env.APP_ENV??''),'Yalnız bu projenin yerel geliştirme/test verisi');
 const databaseUrl=new URL(process.env.DATABASE_URL??'');
 if(!['127.0.0.1','localhost'].includes(databaseUrl.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(databaseUrl.pathname))throw new Error('Hesap mahremiyeti testi yalnız bu projenin yerel veritabanında çalışabilir.');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL}),suffix=randomBytes(7).toString('hex'),users:string[]=[];
 const addressMarker=`A-PRIVATE-${suffix} özel adres`,orderMarker=`OWNER-A-${suffix}`;
 let orderId='',cartId='',releaseResponses=()=>{};
 try{
  const a=await fixtureAccount(page.context(),`${suffix}-a`,true);users.push(a.id);
  const b=await fixtureAccount(page.context(),`${suffix}-b`,false);users.push(b.id);
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',url:origin}]);
  cartId=(await pool.query('INSERT INTO carts(token_hash,user_id) VALUES($1,$2) RETURNING id',[randomBytes(32).toString('hex'),a.id])).rows[0].id;
  const address={fullName:'Yerel A Hesabı',line1:addressMarker,city:'İstanbul',postalCode:'34000',country:'TR',phone:'05000000000'};
  await pool.query('INSERT INTO customer_addresses(user_id,label,address) VALUES($1,$2,$3)',[a.id,'Yalnız A hesabı',JSON.stringify(address)]);
  orderId=(await pool.query("INSERT INTO orders(cart_id,user_id,number,idempotency_key,request_hash,tracking_hash,status,payment_status,currency,subtotal_minor,shipping_minor,tax_minor,total_minor,email,address,snapshot,expires_at) VALUES($1,$2,$3,$4,$4,$4,'confirmed','succeeded','TRY',12345,0,0,12345,$5,$6,'{}',now()+interval '15 minutes') RETURNING id",[cartId,a.id,orderMarker,`owner-fixture-${suffix}`,a.email,JSON.stringify(address)])).rows[0].id;

  await page.goto('/hesap');
  await expect(page.getByText(a.name,{exact:true})).toBeVisible();
  await expect(page.getByText(orderMarker,{exact:true})).toBeVisible();
  await page.locator('.account-nav').getByRole('button',{name:'Adreslerim',exact:true}).click();
  await expect(page.getByText(addressMarker,{exact:true})).toBeVisible();
  await page.locator('.account-nav').getByRole('button',{name:'Hesap güvenliği',exact:true}).click();
  await page.getByLabel('Parola',{exact:true}).fill(a.password);
  await page.getByRole('button',{name:'İki adımlı doğrulama',exact:true}).click();
  const uriField=page.getByRole('textbox',{name:'Authenticator URI',exact:true});
  await expect(uriField).toBeVisible();
  const privateUri=await uriField.inputValue();expect(privateUri.startsWith('otpauth://')).toBe(true);
  await page.getByText('Kurtarma kodları',{exact:true}).click();
  const privateRecovery=await page.locator('pre.secret-display').innerText();expect(privateRecovery.length>20).toBe(true);

  // Gerçek B API yanıtlarını alır; gövdeyi değiştirmeden tarayıcıya teslimini bekletir.
  const gate=new Promise<void>(resolve=>{releaseResponses=resolve;}),pending=new Map<string,{status:number;body:unknown}>();
  await page.route(url=>url.pathname==='/api/orders'||url.pathname==='/api/addresses',async route=>{
   const response=await route.fetch();pending.set(new URL(route.request().url()).pathname,{status:response.status(),body:await response.json()});
   await gate;await route.fulfill({response});
  });
  await page.locator('.account-nav').getByRole('button',{name:'Çıkış yap',exact:true}).click();
  await expect(page.locator('.auth-card')).toBeVisible();
  await expect(uriField).toHaveCount(0);await expect(page.locator('pre.secret-display')).toHaveCount(0);
  await page.locator('.auth-card').getByLabel('E-posta',{exact:true}).fill(b.email);
  await page.locator('.auth-card').getByLabel('Parola',{exact:true}).fill(b.password);
  await submitSignIn(page,page.locator('.auth-card').getByRole('button',{name:'Giriş yap',exact:true}));
  await expect(page.getByText(b.name,{exact:true})).toBeVisible();
  await expect.poll(()=>pending.size).toBe(1);
  expect(pending.has('/api/orders')).toBe(true);
  expect(pending.has('/api/addresses')).toBe(false);
  expect([...pending.values()].every(value=>value.status===200)).toBe(true);
  expect([...pending.values()].some(value=>JSON.stringify(value.body).includes(addressMarker)||JSON.stringify(value.body).includes(orderMarker))).toBe(false);
  expect(new URL(page.url()).pathname).toBe('/hesap');
  await expect(page.getByText(orderMarker,{exact:true})).toHaveCount(0);
  await expect(uriField).toHaveCount(0);await expect(page.locator('pre.secret-display')).toHaveCount(0);
  await page.locator('.account-nav').getByRole('button',{name:'Adreslerim',exact:true}).click();
  await expect.poll(()=>pending.size).toBe(2);
  expect(pending.get('/api/addresses')?.status).toBe(200);
  expect([...pending.values()].some(value=>JSON.stringify(value.body).includes(addressMarker)||JSON.stringify(value.body).includes(orderMarker))).toBe(false);
  await expect(page.getByText(addressMarker,{exact:true})).toHaveCount(0);
  await page.locator('.account-nav').getByRole('button',{name:'Siparişlerim',exact:true}).click();
  await expect(page.getByText(orderMarker,{exact:true})).toHaveCount(0);
  await page.locator('.account-nav').getByRole('button',{name:'Hesap güvenliği',exact:true}).click();
  await expect(page.getByLabel('Parola',{exact:true})).toBeVisible();
  const leaked=await page.evaluate(({uri,recovery})=>Array.from(document.querySelectorAll('textarea')).some(element=>element.value===uri)||(document.body.textContent??'').includes(recovery),{uri:privateUri,recovery:privateRecovery});
  expect(leaked).toBe(false);
  releaseResponses();await page.unrouteAll({behavior:'wait'});
  await page.locator('.account-nav').getByRole('button',{name:'Adreslerim',exact:true}).click();
  await expect(page.getByText(addressMarker,{exact:true})).toHaveCount(0);
  await page.locator('.account-nav').getByRole('button',{name:'Siparişlerim',exact:true}).click();
  await expect(page.getByText(orderMarker,{exact:true})).toHaveCount(0);
 }finally{
  releaseResponses();await page.unrouteAll({behavior:'wait'}).catch(()=>{});
  if(orderId)await pool.query('DELETE FROM orders WHERE id=$1 AND user_id=ANY($2::text[])',[orderId,users]);
  if(users.length){await pool.query('DELETE FROM customer_addresses WHERE user_id=ANY($1::text[])',[users]);await pool.query('DELETE FROM cart_items WHERE cart_id IN(SELECT id FROM carts WHERE user_id=ANY($1::text[]))',[users]);await pool.query('DELETE FROM carts WHERE user_id=ANY($1::text[])',[users]);await pool.query('DELETE FROM "user" WHERE id=ANY($1::text[])',[users]);}
  if(cartId)await pool.query('DELETE FROM carts WHERE id=$1',[cartId]);await pool.end();
 }
});
