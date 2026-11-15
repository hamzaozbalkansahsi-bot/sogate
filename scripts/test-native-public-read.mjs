/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-public-read.mjs
 * Açıklama   : Katalog okumasında süre sınırını, tek tekrarı ve yazma isteği yasağını sınar.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readStorefrontJson} from '../native-store/storefront/public-read.js';

test('UTF-8 JSON and original cache option survive a successful GET',async()=>{
 let calls=0;
 const fetcher=async(url,init)=>{calls++;assert.equal(url,'/test/api/catalog');assert.equal(init.method,'GET');assert.equal(init.cache,'no-cache');return{ok:true,json:async()=>({name:'İç Giyim · Iğdır'})};};
 assert.deepEqual(await readStorefrontJson('/test/api/catalog',{cache:'no-cache'},{fetcher}),{name:'İç Giyim · Iğdır'});
 assert.equal(calls,1);
});
test('a connection reset is retried once',async()=>{
 let calls=0;
 const fetcher=async()=>{if(++calls===1)throw new TypeError('connection reset');return{ok:true,json:async()=>({products:[]})};};
 assert.deepEqual(await readStorefrontJson('/api/catalog',{}, {fetcher}),{products:[]});assert.equal(calls,2);
});
test('the deadline covers a response whose JSON body never finishes',async()=>{
 let calls=0,aborted=false;
 const fetcher=async(url,{signal})=>({ok:true,json:()=>++calls===1?new Promise((resolve,reject)=>signal.addEventListener('abort',()=>{aborted=true;reject(signal.reason);},{once:true})):Promise.resolve({loaded:true})});
 assert.deepEqual(await readStorefrontJson('/api/catalog',{}, {fetcher,timeoutMs:20}),{loaded:true});assert.equal(calls,2);assert.equal(aborted,true);
});
test('two stalled attempts fail instead of waiting forever',async()=>{
 let calls=0;
 const fetcher=(url,{signal})=>{calls++;return new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));};
 await assert.rejects(readStorefrontJson('/api/config',{}, {fetcher,timeoutMs:20}),{name:'AbortError'});assert.equal(calls,2);
});
for(const status of [403,429,503])test('HTTP '+status+' is not retried',async()=>{
 let calls=0;const fetcher=async()=>{calls++;return{ok:false,status};};
 await assert.rejects(readStorefrontJson('/api/catalog',{}, {fetcher}),/public_read_failed/);assert.equal(calls,1);
});
test('invalid JSON is not accepted or silently replaced',async()=>{
 let calls=0;const fetcher=async()=>{calls++;return{ok:true,json:async()=>{throw new SyntaxError('invalid JSON');}};};
 await assert.rejects(readStorefrontJson('/api/config',{}, {fetcher}),SyntaxError);assert.equal(calls,1);
});
test('payment, write and external requests cannot use this retry helper',async()=>{
 let calls=0;const fetcher=async()=>{calls++;};
 for(const[url,init]of [['/api/catalog',{method:'POST'}],['/api/payments/quote',{}],['https://other.invalid/api/catalog',{}]])await assert.rejects(readStorefrontJson(url,init,{fetcher}),/public_read_scope/);
 assert.equal(calls,0);
});
