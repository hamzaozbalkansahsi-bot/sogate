/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/helpers/mfa.ts
 * Açıklama   : Yalnız yerel E2E hazırlığında resmi MFA enable ve gerçek HTTP TOTP doğrulaması.
 */
import {createHmac} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';
import {parseSetCookieHeader} from 'better-auth/cookies';
import type {APIRequestContext,APIResponse,BrowserContext} from '@playwright/test';
const origin='http://127.0.0.1:3000';
type MfaEndpoint='/api/auth/two-factor/enable'|'/api/auth/two-factor/verify-totp';
function fixtureEnvironment(){
 const url=new URL(process.env.DATABASE_URL??'http://invalid');
 if(!['development','test'].includes(process.env.APP_ENV??'')||!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!['/sexsogate_dev','/sexsogate_test'].includes(url.pathname))throw new Error('MFA_FIXTURE_ENVIRONMENT');
}
function totp(secret:string){
 const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';let bits='';
 for(const character of secret.toUpperCase().replace(/=+$/,'')){const value=alphabet.indexOf(character);if(value<0)throw new Error('MFA_FIXTURE_SECRET_FORMAT');bits+=value.toString(2).padStart(5,'0');}
 const bytes=[];for(let index=0;index+8<=bits.length;index+=8)bytes.push(parseInt(bits.slice(index,index+8),2));
 const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));
 const digest=createHmac('sha1',Buffer.from(bytes)).update(counter).digest(),offset=digest[19]&15;
 return ((digest.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0');
}
// A legitimate HTTP 429 is honored once, never reset or disabled. Regenerate
// the body after waiting so a TOTP does not belong to a previous time period.
export async function postMfaHttp(request:APIRequestContext,path:MfaEndpoint,body:()=>Record<string,unknown>):Promise<APIResponse>{
 fixtureEnvironment();const response=await request.post(path,{headers:{origin},data:body()});if(response.status()!==429)return response;
 const value=response.headers()['x-retry-after']??response.headers()['retry-after'];
 if(typeof value!=='string'||!/^\d{1,2}$/.test(value)||Number(value)>10)throw new Error('MFA_RETRY_WINDOW_INVALID');
 await response.dispose();await delay(Number(value)*1000+150);
 return request.post(path,{headers:{origin},data:body()});
}
export async function prepareMfaFixture(context:Pick<BrowserContext,'request'|'addCookies'>,password:string):Promise<APIResponse>{
 const request=context.request;
 fixtureEnvironment();const state=await request.storageState(),host=new URL(origin).hostname;
 const cookie=state.cookies.filter(value=>value.domain.replace(/^\./,'')===host&&'/api/auth/two-factor/enable'.startsWith(value.path)).map(value=>`${value.name}=${value.value}`).join('; ');
 if(!cookie)throw new Error('MFA_FIXTURE_SESSION_REQUIRED');
 const {getAuth}=await import('../../../src/server/auth');
 // Official server API keeps password/session checks. Only the unrelated fixture
 // enable transport is removed; verification and its session-MFA hook remain HTTP.
 const result=await getAuth().api.enableTwoFactor({headers:new Headers({origin,cookie}),body:{password,method:'totp'},returnHeaders:true});
 const received:Parameters<BrowserContext['addCookies']>[0][number][]=[];
 for(const header of result.headers.getSetCookie())for(const [name,attributes]of parseSetCookieHeader(header)){
  if(attributes.domain&&attributes.domain.replace(/^\./,'')!==host)throw new Error('MFA_FIXTURE_COOKIE_SCOPE');
  const expires=attributes['max-age']!==undefined?(attributes['max-age']<=0?0:Math.floor(Date.now()/1000)+attributes['max-age']):attributes.expires?Math.floor(attributes.expires.getTime()/1000):undefined;
  received.push({name,value:attributes.value,domain:attributes.domain??host,path:attributes.path??'/',httpOnly:attributes.httponly??false,secure:attributes.secure??false,sameSite:({lax:'Lax',strict:'Strict',none:'None'} as const)[attributes.samesite??'lax'],...(expires===undefined?{}:{expires})});
 }
 if(received.length)await context.addCookies(received);
 const enabled=result.response;
 const uri='totpURI'in enabled?enabled.totpURI:undefined;
 if(typeof uri!=='string')throw new Error('MFA_FIXTURE_ENABLE_FAILED');
 let secret:string|null;try{secret=new URL(uri).searchParams.get('secret');}catch{throw new Error('MFA_FIXTURE_URI_INVALID');}if(!secret)throw new Error('MFA_FIXTURE_SECRET_REQUIRED');
 return postMfaHttp(request,'/api/auth/two-factor/verify-totp',()=>({code:totp(secret),trustDevice:false}));
}
