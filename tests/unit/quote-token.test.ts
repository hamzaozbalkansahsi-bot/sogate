/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/quote-token.test.ts
 * Açıklama   : Sepete bağlı toplam teklifinin imza, gizlilik ve süre sınırlarını doğrular.
 */
import {afterEach,beforeEach,describe,expect,it} from 'vitest';
import {createQuoteToken,verifyQuoteToken,quoteFingerprint} from '../../src/server/commerce/quote-token';
const prior=process.env.BETTER_AUTH_SECRET,now=1800000000000;
const binding={cartId:'own-cart',cartTokenHash:'a'.repeat(64),selectionHash:'b'.repeat(64),evaluationHash:'c'.repeat(64)};
beforeEach(()=>{process.env.BETTER_AUTH_SECRET='isolated-quote-unit-secret-'.repeat(3);});
afterEach(()=>{if(prior===undefined)delete process.env.BETTER_AUTH_SECRET;else process.env.BETTER_AUTH_SECRET=prior;});
describe('Checkout quote token',()=>{
 it('validates its own cart-bound short-lived signature',()=>{const result=createQuoteToken(binding,now);expect(()=>verifyQuoteToken(result.quoteToken,binding,now+1000)).not.toThrow();expect(Date.parse(result.expiresAt)-now).toBe(300000);});
 it('rejects modified payloads or signatures',()=>{const result=createQuoteToken(binding,now),parts=result.quoteToken.split('.');parts[0]=Buffer.from(JSON.stringify({...binding,version:1,issuedAt:now/1000,expiresAt:now/1000+99999})).toString('base64url');expect(()=>verifyQuoteToken(parts.join('.'),binding,now)).toThrow();expect(()=>verifyQuoteToken(result.quoteToken.slice(0,-4)+'0000',binding,now)).toThrow();});
 it('rejects another cart, selection and evaluation without accepting client totals',()=>{const {quoteToken}=createQuoteToken(binding,now);for(const changed of [{cartId:'other'},{cartTokenHash:'d'.repeat(64)},{selectionHash:'e'.repeat(64)},{evaluationHash:'f'.repeat(64)}])expect(()=>verifyQuoteToken(quoteToken,{...binding,...changed},now)).toThrow();});
 it('expires at the precise boundary and rejects future-issued tokens',()=>{const {quoteToken}=createQuoteToken(binding,now);expect(()=>verifyQuoteToken(quoteToken,binding,now+299999)).not.toThrow();expect(()=>verifyQuoteToken(quoteToken,binding,now+300000)).toThrow();expect(()=>verifyQuoteToken(quoteToken,binding,now-1000)).toThrow();});
 it('hashes object keys deterministically without changing caller arrays',()=>{const array=['b','a'];expect(quoteFingerprint({b:2,a:{z:3,c:array}})).toBe(quoteFingerprint({a:{c:['b','a'],z:3},b:2}));expect(array).toEqual(['b','a']);expect(quoteFingerprint({a:1})).not.toBe(quoteFingerprint({a:2}));});
 it('keys private evaluation fingerprints with the server secret',()=>{const first=quoteFingerprint({privateCostMinor:12345});process.env.BETTER_AUTH_SECRET='different-isolated-quote-secret-'.repeat(3);expect(quoteFingerprint({privateCostMinor:12345})).not.toBe(first);});
 it('fails closed when the server signing secret is missing',()=>{delete process.env.BETTER_AUTH_SECRET;expect(()=>createQuoteToken(binding,now)).toThrow();expect(()=>quoteFingerprint({a:1})).toThrow();});
});
