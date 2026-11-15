import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createApplication} from '../lib/server.mjs';

const raster=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=','base64');
const digest=createHash('sha256').update(raster).digest('hex');
const catalog={products:[{id:'p'}],categories:[],meta:{mediaVersion:'reviewed-version'}};
const media={p:['https://witcdn.adoremobilya.com/original.jpg']};
const brand={domain:'nodenohome.com',website:'https://nodenohome.com'};
const request=new Request('https://preview.invalid/media/p/0?v=old');

test('reviewed preview media uses the canonical cleaned host and verifies exact approved bytes',async()=>{
 const calls=[];
 const app=createApplication(catalog,{},media,{},async(url,options)=>{
  calls.push({url,options});return new Response(raster,{headers:{'content-type':'image/png'}});
 },brand,{'p:0':digest});
 const response=await app.fetch(request);
 assert.equal(response.status,200);
 assert.deepEqual(Buffer.from(await response.arrayBuffer()),raster);
 assert.equal(calls.length,1);
 assert.equal(new URL(calls[0].url).origin,'https://nodenohome.com');
 assert.equal(new URL(calls[0].url).searchParams.get('v'),'reviewed-version');
 assert.equal(calls[0].options.redirect,'error');
});

test('reviewed media never falls back to a supplier image after a hash mismatch',async()=>{
 const calls=[];
 const app=createApplication(catalog,{},media,{},async url=>{
  calls.push(url);return new Response('unreviewed image',{headers:{'content-type':'image/jpeg'}});
 },brand,{'p:0':digest});
 assert.equal((await app.fetch(request)).status,502);
 assert.equal(calls.length,1);
 assert.ok(calls.every(url=>new URL(url).hostname==='nodenohome.com'));
});

test('missing approvals and recursive canonical-host proxies fail without any network request',async()=>{
 const never=()=>{throw new Error('Unexpected image fetch');};
 assert.equal((await createApplication(catalog,{},media,{},never,brand).fetch(request)).status,503);
 const app=createApplication(catalog,{},media,{},never,brand,{'p:0':digest});
 assert.equal((await app.fetch(new Request('https://nodenohome.com/media/p/0'))).status,503);
});

test('reviewed media enforces actual streamed bytes when the upstream length header is false',async()=>{
 let cancelled=false;
 const stream=new ReadableStream({start(controller){controller.enqueue(new Uint8Array(20000001));},cancel(){cancelled=true;}});
 const app=createApplication(catalog,{},media,{},async()=>new Response(stream,{headers:{'content-type':'image/jpeg','content-length':'1'}}),brand,{'p:0':digest});
 assert.equal((await app.fetch(request)).status,502);
 assert.equal(cancelled,true);
});
