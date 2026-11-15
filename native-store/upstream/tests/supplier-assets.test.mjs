import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash}from'node:crypto';
import {createApplication}from'../lib/server.mjs';
const bytes=new TextEncoder().encode('supplier image fixture'),sha=createHash('sha256').update(bytes).digest('hex'),url='/assets/suppliers/'+sha+'.png';
const catalog={products:[],categories:[],brand:{},meta:{}};
test('external approved image is fetched only from the NODENO host and its bytes are verified',async()=>{
 let calls=0;const app=createApplication(catalog,{[url]:{encoding:'external',url:'https://nodenohome.com'+url,sha256:sha,type:'image/png'}},{},{},async request=>{calls++;assert.equal(request.url,'https://nodenohome.com'+url);assert.equal(request.redirect,'error');return new Response(bytes);});
 const r=await app.fetch(new Request('https://preview.invalid'+url));assert.equal(r.status,200);assert.deepEqual(new Uint8Array(await r.arrayBuffer()),bytes);assert.equal(calls,1);
});
test('changed hosted bytes or an unapproved origin fail closed',async()=>{
 for(const foreign of [false,true]){
  let calls=0;const app=createApplication(catalog,{[url]:{encoding:'external',url:(foreign?'https://evil.invalid':'https://nodenohome.com')+url,sha256:sha,type:'image/png'}},{},{},async()=>{calls++;return new Response('tampered');});
  assert.equal((await app.fetch(new Request('https://preview.invalid'+url))).status,503);assert.equal(calls,foreign?0:1);
 }
});
