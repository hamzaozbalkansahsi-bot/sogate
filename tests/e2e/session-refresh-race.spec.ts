/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/session-refresh-race.spec.ts
 * Açıklama   : İlk oturum yanıtı gecikse de yeni giriş yapan hesabın kimliğinin korunmasını sınar.
 */
import {test,expect} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {submitSignIn} from './helpers/sign-in';
const origin='http://127.0.0.1:3000';
test('an older session response cannot replace a newer account after sign-in',async({page})=>{
 test.setTimeout(90000);const url=new URL(process.env.DATABASE_URL??'http://invalid');
 if(!['development','test'].includes(process.env.APP_ENV??'')||!['localhost','127.0.0.1'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname))throw new Error('Yalnız bu projenin yerel test verisi kullanılabilir.');
 const pool=new pg.Pool({connectionString:url.href}),suffix=randomBytes(7).toString('hex'),users:string[]=[];let release=()=>{},completed=()=>{},captured=false,handlerError:unknown;
 const gate=new Promise<void>(resolve=>{release=resolve;}),done=new Promise<void>(resolve=>{completed=resolve;});
 try{
  const {getAuth}=await import('../../src/server/auth');
  async function account(label:string){const password=randomBytes(24).toString('base64url');const result=await getAuth().api.signUpEmail({body:{email:`session-${label}-${suffix}@example.invalid`,password,name:`Özel Hesap ${label} ${suffix}`},returnHeaders:true});users.push(result.response.user.id);return {...result,password};}
  const a=await account('A'),b=await account('B');
  await page.context().addCookies(a.headers.getSetCookie().map(cookie=>{const pair=cookie.split(';')[0],at=pair.indexOf('=');return {name:pair.slice(0,at),value:pair.slice(at+1),url:origin,httpOnly:/;\s*httponly(?:;|$)/i.test(cookie),secure:/;\s*secure(?:;|$)/i.test(cookie),sameSite:'Lax' as const};}));
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',url:origin}]);
  await page.route(url=>url.pathname==='/api/session',async route=>{
   if(captured){await route.continue();return;}captured=true;
   try{const response=await route.fetch();expect(response.status()).toBe(200);expect((await response.json()).user.id).toBe(a.response.user.id);await gate;await route.fulfill({response}).catch(error=>{if(!/cancel|abort|invalid interception|loading finished|no resource with given|target.*closed/i.test(String(error)))throw error;});}
   catch(error){handlerError=error;}finally{completed();}
  });
  await page.goto('/hesap');await expect.poll(()=>captured).toBe(true);const form=page.locator('.auth-card');await expect(form).toBeVisible();
  await form.getByRole('textbox',{name:'E-posta',exact:true}).fill(b.response.user.email);await form.getByLabel('Parola',{exact:true}).fill(b.password);await submitSignIn(page,form.getByRole('button',{name:'Giriş yap',exact:true}));
  await expect(page.getByText(b.response.user.name,{exact:true})).toBeVisible();release();await done;expect(handlerError).toBeUndefined();await page.unrouteAll({behavior:'wait'});
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));await page.waitForLoadState('networkidle');
  await expect(page.getByText(b.response.user.name,{exact:true})).toBeVisible();await expect(page.getByText(a.response.user.name,{exact:true})).toHaveCount(0);
  const session=await page.request.get('/api/session');expect((await session.json()).user.id).toBe(b.response.user.id);
 }finally{
  release();await page.unrouteAll({behavior:'wait'}).catch(()=>{});
  if(users.length){await pool.query('DELETE FROM jobs WHERE payload->>\'userId\'=ANY($1::text[])',[users]);await pool.query('DELETE FROM audit_log WHERE actor_id=ANY($1::text[])',[users]);await pool.query('DELETE FROM carts c WHERE c.user_id=ANY($1::text[]) AND NOT EXISTS(SELECT 1 FROM cart_items i WHERE i.cart_id=c.id) AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=c.id)',[users]);await pool.query('DELETE FROM "user" WHERE id=ANY($1::text[])',[users]);}
  await pool.end();
 }
});
