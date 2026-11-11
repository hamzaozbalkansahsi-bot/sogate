/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/security.spec.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {postMfaHttp} from './helpers/mfa';
import {test,expect,request as requests} from '@playwright/test';
import pg from 'pg';
import {randomBytes,createHmac} from 'node:crypto';
const base='http://127.0.0.1:3000';
const headers={origin:base};
function totp(secret:string){const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';let bits='';for(const c of secret.toUpperCase().replace(/=+$/,''))bits+=alphabet.indexOf(c).toString(2).padStart(5,'0');const bytes=[];for(let i=0;i+8<=bits.length;i+=8)bytes.push(parseInt(bits.slice(i,i+8),2));const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const digest=createHmac('sha1',Buffer.from(bytes)).update(counter).digest();const offset=digest[19]&15;return ((digest.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0');}
test('MFA kurulmadan açılan ikinci oturum yönetici erişimi kazanamaz',async()=>{
 test.skip(!['test','development'].includes(process.env.APP_ENV??''),'Yalnız izole yerel/test ortamı');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL});const a=await requests.newContext({baseURL:base,extraHTTPHeaders:headers});const b=await requests.newContext({baseURL:base,extraHTTPHeaders:headers});
 const email=`mfa-${randomBytes(8).toString('hex')}@example.test`;const password=randomBytes(24).toString('base64url');let id='';
 try{
  const signup=await a.post('/api/auth/sign-up/email',{data:{email,password,name:'Güvenli Oturum Testi'}});expect(signup.ok()).toBeTruthy();id=(await signup.json()).user.id;await pool.query('UPDATE "user" SET role=\'admin\' WHERE id=$1',[id]);
  const signin=await b.post('/api/auth/sign-in/email',{data:{email,password}});expect(signin.ok()).toBeTruthy();
  const enable=await postMfaHttp(a,'/api/auth/two-factor/enable',()=>({password}));expect(enable.ok()).toBeTruthy();const data=await enable.json();expect(data.totpURI).toBeTruthy();
  const secret=new URL(data.totpURI).searchParams.get('secret')!;
  const verify=await postMfaHttp(a,'/api/auth/two-factor/verify-totp',()=>({code:totp(secret),trustDevice:false}));expect(verify.ok()).toBeTruthy();
  expect((await a.get('/api/admin/settings')).status()).toBe(200);
  expect([401,403]).toContain((await b.get('/api/admin/settings')).status());
 }finally{await a.dispose();await b.dispose();if(id)await pool.query('DELETE FROM "user" WHERE id=$1',[id]);await pool.end();}
});
test('anonim istekte Content-Length olmadan büyük JSON reddedilir ve cevap cache dışıdır',async({request})=>{
 const response=await request.post('/api/cart',{headers:{origin:base},data:{variantId:'x',quantity:1,extra:'x'.repeat(100000)}});expect(response.status()).toBe(413);expect(response.headers()['cache-control']).toContain('no-store');
});
test('hesaptan çıkış sonrası saklanan sepet tokenı önceki kullanıcıya sipariş oluşturamaz',async()=>{
 test.skip(!['test','development'].includes(process.env.APP_ENV??''),'Yalnız yerel/test ortamı');
 const pool=new pg.Pool({connectionString:process.env.DATABASE_URL});const a=await requests.newContext({baseURL:base,extraHTTPHeaders:headers});let userId='';
 try{
  // Bu test sepet sahipliğini sınar; fixture hazırlığı herkese açık kayıt kotasını tüketmez.
  const {getAuth}=await import('../../src/server/auth');
  const signup=await getAuth().api.signUpEmail({body:{email:`cart-${randomBytes(8).toString('hex')}@example.test`,password:randomBytes(24).toString('base64url'),name:'Sepet Sahipliği Testi'},returnHeaders:true});userId=signup.response.user.id;
  const sessionCookie=signup.headers.getSetCookie().map(cookie=>cookie.split(';')[0]).join('; ');
  await a.get('/api/cart',{headers:{cookie:sessionCookie}});const cartCookies=(await a.storageState()).cookies.map(cookie=>`${cookie.name}=${cookie.value}`).join('; ');
  const catalog=await a.get('/api/catalog');const products=(await catalog.json()).products;const variant=products.flatMap((p:{variants:{id:string;available:number}[]})=>p.variants).find((v:{available:number})=>v.available>0);expect(variant).toBeTruthy();
  expect((await a.post('/api/cart',{headers:{cookie:`${sessionCookie}; ${cartCookies}`},data:{variantId:variant.id,quantity:1}})).ok()).toBeTruthy();
  const quoteResponse=await a.post('/api/checkout/quote',{headers:{cookie:`${sessionCookie}; ${cartCookies}`},data:{country:'TR',locale:'tr',currency:'TRY'}});expect(quoteResponse.ok()).toBeTruthy();const acceptedQuote=await quoteResponse.json();expect(typeof acceptedQuote.quoteToken).toBe('string');
  const state=await a.storageState();
  const isolated=await requests.newContext({baseURL:base,extraHTTPHeaders:headers,storageState:{cookies:state.cookies.filter(c=>c.name==='sg_cart'),origins:[]}});
  try{const checkout=await isolated.post('/api/checkout',{data:{quoteToken:acceptedQuote.quoteToken,email:'guest@example.test',fullName:'Hamza ÖZBALKAN',phone:'05550001122',line1:'Güvenli Alışveriş Sokak 12',city:'İstanbul',postalCode:'34000',country:'TR',locale:'tr',currency:'TRY',idempotencyKey:randomBytes(20).toString('hex'),privacyAccepted:true,termsAccepted:true}});expect([400,409]).toContain(checkout.status());expect(Number((await pool.query('SELECT count(*) n FROM orders WHERE user_id=$1',[userId])).rows[0].n)).toBe(0);}finally{await isolated.dispose();}
 }finally{await a.dispose();if(userId)await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);await pool.end();}
});
