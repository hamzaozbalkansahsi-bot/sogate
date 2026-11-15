import test from 'node:test';
import assert from 'node:assert/strict';
import { createApplication, safeMediaUrl } from '../lib/server.mjs';

const catalog = {brand:{name:'NODENO'},categories:[],products:[{id:'7',code:'ABC-7',name:{tr:'Kitaplık'},salePrice:null,images:['/media/7/0']}],meta:{productCount:1}};
const sourceMedia = {'7':['https://witcdn.adoremobilya.com/example.jpg']};

test('product links expose selected product social metadata without scripts or untrusted host injection',async()=>{
 const html='<title>NODENO</title><meta property="og:title" content="NODENO"><meta property="og:description" content="Home"><meta property="og:type" content="website"></head>';
 const p={...catalog.products[0],modelName:{tr:'Raf <güzel> "model"'},variantColor:{tr:'Sarı'},coverIndex:0};
 const app=createApplication({...catalog,products:[p]},{'/':{body:html,type:'text/html; charset=utf-8'}},sourceMedia,{});
 const result=await(await app.fetch(new Request('https://untrusted.example/?product=7&lang=tr'))).text();
 assert.ok(result.includes('Raf &lt;güzel&gt; &quot;model&quot;'));
 assert.ok(result.includes('property="og:image" content="https://nodenohome.com/media/7/0'));
 assert.ok(result.includes('property="og:url" content="https://nodenohome.com/?lang=tr&amp;product=7"'));
 assert.ok(!result.includes('untrusted.example'));assert.ok(!result.includes('<güzel>'));
 const missing=await(await app.fetch(new Request('https://nodenohome.com/?product=unknown'))).text();assert.ok(!missing.includes('property="og:image"'));
});

test('old supplier category URLs redirect to house-brand category URLs and retain other query values',async()=>{
 const app=createApplication(catalog,{},sourceMedia,{});
 for(const [old,current] of [['adore-gaming','oyuncu-mobilyalari'],['adoregaming-tgif','tgif-serisi']]){
  const response=await app.fetch(new Request(`https://store.test/?page=catalog&category=${old}&lang=ar&q=table`));
  assert.equal(response.status,301);
  assert.equal(response.headers.get('location'),`/?page=catalog&category=${current}&lang=ar&q=table`);
 }
 for(const value of ['__proto__','constructor','toString'])assert.notEqual((await app.fetch(new Request(`https://store.test/?category=${value}`))).status,301);
});

test('public catalog does not turn source retail prices into sale prices', async()=>{
 const app=createApplication(catalog,{},sourceMedia,{});
 const res=await app.fetch(new Request('https://store.test/api/catalog'),{});
 assert.equal(res.status,200);
 const body=await res.json();
 assert.equal(body.products[0].salePrice,null);
 assert.equal(body.products[0].sourceUrl,undefined);
});
test('checkout is unavailable until merchant settings exist',async()=>{
 const app=createApplication(catalog,{},sourceMedia,{});
 const config=await (await app.fetch(new Request('https://store.test/api/config'),{})).json();
 assert.equal(config.checkoutEnabled,false);
 assert.equal(config.contactEmail,null);
 assert.equal((await app.fetch(new Request('https://store.test/api/checkout',{method:'POST'}),{})).status,405);
});
test('media route rejects unknown products and malformed indexes without a network request',async()=>{
 const app=createApplication(catalog,{},sourceMedia,{});
 for (const path of ['/media/8/0','/media/7/-1','/media/7/1','/media/7/0.5','/media/7/0/extra']) {
  assert.equal((await app.fetch(new Request('https://store.test'+path),{})).status,404,path);
 }
});
test('source media allowlist rejects lookalikes credentials and insecure URLs',()=>{
 for (const u of ['http://witcdn.adoremobilya.com/a.jpg','https://witcdn.adoremobilya.com.evil.test/a.jpg','https://user:pass@witcdn.adoremobilya.com/a.jpg','https://127.0.0.1/a.jpg','https://witcdn.adoremobilya.com:8080/a.jpg']) assert.equal(safeMediaUrl(u),false,u);
 assert.equal(safeMediaUrl('https://witcdn.adoremobilya.com/a.jpg'),true);
});
test('media rejects an upstream HTML response rather than serving active content',async()=>{
 const app=createApplication(catalog,{},sourceMedia,{},async()=>new Response('<script>bad()</script>',{headers:{'content-type':'text/html'}}));
 const r=await app.fetch(new Request('https://store.test/media/7/0'),{});
 assert.equal(r.status,502);
 assert.match(r.headers.get('content-type'),/json/);
});
test('media redirects cannot escape the source allowlist',async()=>{
 let calls=0;
 const app=createApplication(catalog,{},sourceMedia,{},async()=>{calls++;return new Response(null,{status:302,headers:{location:'https://evil.test/private'}})});
 assert.equal((await app.fetch(new Request('https://store.test/media/7/0'),{})).status,502);
 assert.equal(calls,1);
});
test('successful media is inline raster with privacy and nosniff headers',async()=>{
 const app=createApplication(catalog,{},sourceMedia,{},async()=>new Response(new Uint8Array([255,216,255]),{headers:{'content-type':'image/jpeg'}}));
 const res=await app.fetch(new Request('https://store.test/media/7/0'),{});
 assert.equal(res.status,200);
 assert.equal(res.headers.get('x-content-type-options'),'nosniff');
 assert.equal(res.headers.get('content-disposition'),'inline');
 assert.equal(res.headers.get('access-control-allow-origin'),null);
});
test('HTML and missing assets have correct status and security headers',async()=>{
 const app=createApplication(catalog,{'/':{body:'<!doctype html><title>NODENO</title>',type:'text/html; charset=utf-8'}},sourceMedia,{});
 const r=await app.fetch(new Request('https://store.test/?lang=ar&product=7'),{});
 assert.equal(r.status,200);
 assert.match(r.headers.get('content-security-policy'),/frame-ancestors 'none'/);
 assert.equal((await app.fetch(new Request('https://store.test/nonexistent.js'),{})).status,404);
 assert.equal((await app.fetch(new Request('https://store.test/api/catalog',{method:'PUT'}),{})).status,405);
});
test('isolated Workers serve images without accessing the disabled default cache',async()=>{
 const previous=Object.getOwnPropertyDescriptor(globalThis,'caches');let defaultAccessed=false;
 Object.defineProperty(globalThis,'caches',{configurable:true,value:{get default(){defaultAccessed=true;throw new Error('Default cache disabled in isolated dispatch');},async open(){return {async match(){return undefined;},async put(){}};}}});
 try {
  const app=createApplication(catalog,{},sourceMedia,{},async()=>new Response(new Uint8Array([255,216,255]),{headers:{'content-type':'image/jpeg'}}));
  assert.equal((await app.fetch(new Request('https://store.test/media/7/0'),{},{waitUntil(){}})).status,200);
  assert.equal(defaultAccessed,false);
 } finally {if(previous)Object.defineProperty(globalThis,'caches',previous);else delete globalThis.caches;}
});
test('an unavailable cache cannot turn a successful upstream image into a failure',async()=>{
 const previous=Object.getOwnPropertyDescriptor(globalThis,'caches');
 Object.defineProperty(globalThis,'caches',{configurable:true,value:{async open(){throw new Error('Cache unavailable');},get default(){throw new Error('Cache unavailable');}}});
 try {
  const app=createApplication(catalog,{},sourceMedia,{},async()=>new Response(new Uint8Array([255,216,255]),{headers:{'content-type':'image/jpeg'}}));
  assert.equal((await app.fetch(new Request('https://store.test/media/7/0'),{})).status,200);
 } finally {if(previous)Object.defineProperty(globalThis,'caches',previous);else delete globalThis.caches;}
});
test('each HTML response has a fresh nonce that permits the hosting security script without unsafe-inline',async()=>{
 const app=createApplication(catalog,{'/':{body:'<!doctype html><script type="module" src="/app.js"></script>',type:'text/html; charset=utf-8'}},sourceMedia,{});
 const first=await app.fetch(new Request('https://store.test/'),{});
 const second=await app.fetch(new Request('https://store.test/'),{});
 const policy=first.headers.get('content-security-policy');
 const nonce=/\x27nonce-([a-f0-9]{32})\x27/.exec(policy)?.[1];
 assert.ok(nonce);
 assert.ok((await first.text()).includes(`nonce="${nonce}"`));
 assert.notEqual(policy,second.headers.get('content-security-policy'));
 assert.doesNotMatch(policy,/unsafe-inline/);
 assert.equal(first.headers.get('cache-control'),'no-store');
});
test('supplied contact details and brand slogans are exposed without enabling checkout or inventing a legal entity',async()=>{
 const brand={name:'NODENO',domain:'nodenohome.com',website:'https://nodenohome.com',contact:{email:'info@nodenohome.com',phone:'0850 305 84 78',phoneE164:'+908503058478'},socialHandle:'nodenohome',socials:[{id:'instagram',label:'Instagram',url:'https://www.instagram.com/nodenohome/'}],slogan:{tr:'İyi tasarım. Kolay yaşam.',en:'Good design. Easy living.',ru:'Продуманный дизайн. Простая жизнь.',ar:'تصميم متقن. حياة أسهل.'}};
 const app=createApplication(catalog,{},sourceMedia,{},fetch,brand);
 const config=await(await app.fetch(new Request('https://store.test/api/config'),{})).json();
 assert.equal(config.contactEmail,'info@nodenohome.com');
 assert.equal(config.contactPhoneUri,'tel:+908503058478');
 assert.equal(config.domain,'nodenohome.com');
 assert.equal(config.socials[0].url,'https://www.instagram.com/nodenohome/');
 assert.equal(config.brand.slogan.ru,'Продуманный дизайн. Простая жизнь.');
 assert.equal(config.legalName,null);
 assert.equal(config.checkoutEnabled,false);
});
test('bundled binary brand resources are decoded without UTF-8 corruption',async()=>{
 const app=createApplication(catalog,{'/assets/fonts/test.woff':{body:'AP+ASAA=',encoding:'base64',type:'font/woff'}},sourceMedia,{});
 const res=await app.fetch(new Request('https://store.test/assets/fonts/test.woff'),{});
 assert.equal(res.status,200);
 assert.equal(res.headers.get('content-type'),'font/woff');
 assert.deepEqual([...new Uint8Array(await res.arrayBuffer())],[0,255,128,72,0]);
});
