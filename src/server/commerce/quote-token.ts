/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/quote-token.ts
 * Açıklama   : Kısa ömürlü toplam teklifini sepete bağlar; özel hesap izini HMAC ile korur.
 */
import {createHmac,timingSafeEqual} from 'node:crypto';
import {z} from 'zod';
import {requireCondition} from './rules';
const ttl=300;
export interface QuoteBinding{cartId:string;cartTokenHash:string;selectionHash:string;evaluationHash:string;}
const hash=z.string().regex(/^[a-f0-9]{64}$/),claimsSchema=z.object({version:z.literal(1),cartId:z.string().min(1).max(300),cartTokenHash:hash,selectionHash:hash,evaluationHash:hash,issuedAt:z.number().int().positive(),expiresAt:z.number().int().positive()}).strict();
function secret(){const value=process.env.BETTER_AUTH_SECRET;requireCondition(value&&value.length>=32,'SECRET_NOT_CONFIGURED','Güvenli toplam teklifi yapılandırılmadı.',503);return value;}
function canonical(value:unknown):unknown{
 if(value===null||typeof value!=='object')return value;
 if(value instanceof Date)return value.toISOString();
 if(Array.isArray(value))return value.map(canonical);
 return Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b,'en')).map(([key,item])=>[key,canonical(item)]));
}
export function quoteFingerprint(value:unknown){return createHmac('sha256',secret()).update('checkout-quote:fingerprint:v1\0').update(JSON.stringify(canonical(value))).digest('hex');}
const signature=(payload:string)=>createHmac('sha256',secret()).update('checkout-quote:token:v1\0').update(payload).digest('hex');
export function createQuoteToken(binding:QuoteBinding,now=Date.now()){
 const issuedAt=Math.floor(now/1000),claims=claimsSchema.parse({...binding,version:1,issuedAt,expiresAt:issuedAt+ttl}),payload=Buffer.from(JSON.stringify(claims)).toString('base64url');
 return {quoteToken:`${payload}.${signature(payload)}`,expiresAt:new Date(claims.expiresAt*1000).toISOString()};
}
export function verifyQuoteToken(value:string,binding:QuoteBinding,now=Date.now()){
 requireCondition(typeof value==='string'&&value.length>0,'CHECKOUT_QUOTE_REQUIRED','Ödeme öncesinde güncel sipariş toplamını inceleyin.',409);
 requireCondition(value.length<=2048&&/^[A-Za-z0-9_-]+\.[a-f0-9]{64}$/.test(value),'CHECKOUT_QUOTE_INVALID','Sipariş toplamı doğrulanamadı. Özeti yenileyin.',409);
 const [payload,provided]=value.split('.'),expected=signature(payload);requireCondition(timingSafeEqual(Buffer.from(provided,'hex'),Buffer.from(expected,'hex')),'CHECKOUT_QUOTE_INVALID','Sipariş toplamı doğrulanamadı. Özeti yenileyin.',409);
 let raw:unknown;try{raw=JSON.parse(Buffer.from(payload,'base64url').toString('utf8'));}catch{raw=null;}
 const result=claimsSchema.safeParse(raw);requireCondition(result.success,'CHECKOUT_QUOTE_INVALID','Sipariş toplamı doğrulanamadı. Özeti yenileyin.',409);const claims=result.data,seconds=Math.floor(now/1000);
 requireCondition(claims.issuedAt<=seconds&&claims.expiresAt-claims.issuedAt===ttl,'CHECKOUT_QUOTE_INVALID','Sipariş toplamı doğrulanamadı. Özeti yenileyin.',409);
 requireCondition(claims.expiresAt>seconds,'CHECKOUT_QUOTE_EXPIRED','Sipariş toplamının süresi doldu. Özeti yenileyip tekrar inceleyin.',409);
 requireCondition(claims.cartId===binding.cartId&&claims.cartTokenHash===binding.cartTokenHash&&claims.selectionHash===binding.selectionHash&&claims.evaluationHash===binding.evaluationHash,'CHECKOUT_QUOTE_CHANGED','Sipariş tutarı veya koşulları değişti. Güncel özeti inceleyin.',409);
 return claims;
}
