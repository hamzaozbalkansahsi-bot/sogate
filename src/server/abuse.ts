/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/abuse.ts
 * Açıklama   : Ödeme ve sipariş özeti isteklerini güvenilir ağ kotasıyla sınırlar.
 */
import {createHmac} from 'node:crypto';
import {isIP} from 'node:net';
import {pool} from './db';
import {HttpError} from './security';

export interface CheckoutNetworkConfig {
 appEnv:string;trustedProxyEnabled:boolean;clientIpHeader:string;secret:string;
}
function configuration():CheckoutNetworkConfig {
 return {appEnv:process.env.APP_ENV??'',trustedProxyEnabled:process.env.TRUSTED_PROXY_ENABLED==='true',clientIpHeader:process.env.TRUSTED_CLIENT_IP_HEADER??'',secret:process.env.BETTER_AUTH_SECRET??''};
}
function ipv6Words(ip:string):number[] {
 // WHATWG canonicalizes embedded IPv4 and equivalent compressed IPv6 spellings.
 const canonical=new URL(`http://[${ip}]/`).hostname.slice(1,-1);
 const halves=canonical.split('::');
 const left=halves[0]?halves[0].split(':'):[];
 const right=halves.length>1&&halves[1]?halves[1].split(':'):[];
 const words=halves.length===1?left:[...left,...Array(8-left.length-right.length).fill('0'),...right];
 return words.map(word=>Number.parseInt(word,16));
}
function networkIdentity(ip:string):string {
 if(isIP(ip)===4)return `ipv4:${ip}`;
 const words=ipv6Words(ip);
 // Mapped IPv4 must share the same quota as the plain IPv4 representation.
 if(words.slice(0,5).every(word=>word===0)&&words[5]===0xffff) {
  return `ipv4:${words[6]>>8}.${words[6]&255}.${words[7]>>8}.${words[7]&255}`;
 }
 return `ipv6:${words.slice(0,4).map(word=>word.toString(16).padStart(4,'0')).join('')}/64`;
}
/** Header authenticity depends on the deployed proxy, firewall and header stripping. */
export function checkoutNetworkPolicy(request:Request,config=configuration(),purpose:'checkout'|'quote'='checkout'):{key:string;max:number} {
 if(config.secret.length<32)throw new HttpError(503,'İstek güvenlik sınırı henüz yapılandırılmadı.','NETWORK_BOUNDARY_REQUIRED');
 let identity:string,max:number;
 if(config.appEnv==='development'||config.appEnv==='test') {
  identity='local-loopback-aggregate';max=100;
 } else {
  if(!['production','staging'].includes(config.appEnv)||!config.trustedProxyEnabled||config.clientIpHeader!=='x-real-ip') {
   throw new HttpError(503,'Güvenilir ağ sınırı doğrulanmadan ödeme başlatılamaz.','NETWORK_BOUNDARY_REQUIRED');
  }
  const ip=request.headers.get('x-real-ip');
  if(!ip||ip!==ip.trim()||ip.includes('%')||!isIP(ip)) {
   throw new HttpError(503,'Güvenilir istemci bağlantısı doğrulanamadı.','NETWORK_IDENTITY_REQUIRED');
  }
  identity=networkIdentity(ip);max=10;
 }
 // Never store or log the IP or subnet. Prefix separates this quota from cart keys.
 const namespace=purpose==='quote'?'checkout-quote-network':'checkout-network';
 const digest=createHmac('sha256',config.secret).update(`${namespace}:v1:${identity}`).digest('hex');
 return {key:`${namespace}:${digest}`,max:purpose==='quote'?max*6:max};
}
export async function enforceCheckoutNetworkQuota(request:Request,purpose:'checkout'|'quote'='checkout'):Promise<void> {
 const {key,max}=checkoutNetworkPolicy(request,configuration(),purpose);
 const result=await pool.query<{count:number}>(`INSERT INTO request_limits(key,count,window_start,expires_at)
  VALUES($1,1,now(),now()+interval '2 minutes')
  ON CONFLICT(key) DO UPDATE SET
   count=CASE WHEN request_limits.window_start<=now()-interval '1 minute' THEN 1 ELSE request_limits.count+1 END,
   window_start=CASE WHEN request_limits.window_start<=now()-interval '1 minute' THEN now() ELSE request_limits.window_start END,
   expires_at=now()+interval '2 minutes'
  RETURNING count`,[key]);
 if(result.rows[0].count>max)throw new HttpError(429,purpose==='quote'?'Çok fazla sipariş özeti isteği alındı. Bir dakika sonra yeniden deneyin.':'Çok fazla ödeme isteği alındı. Bir dakika sonra yeniden deneyin.',purpose==='quote'?'QUOTE_RATE_LIMIT':'CHECKOUT_RATE_LIMIT');
}
