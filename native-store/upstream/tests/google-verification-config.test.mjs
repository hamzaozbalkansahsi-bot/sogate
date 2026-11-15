import test from 'node:test';
import assert from 'node:assert/strict';
import {createApplication}from'../lib/server.mjs';

const token='g-D7xs3HsOx8puu2-bjYyR6ZynC9XHZlWtWFAYB1jMs';
const catalog={brand:{name:'NODENO'},products:[],categories:[],meta:{}};
const assets={'/':{body:'<!doctype html><html><head><title>NODENO</title></head><body><main id="page"></main></body></html>',type:'text/html; charset=utf-8',encoding:'utf8'}};
const app=seo=>createApplication(catalog,assets,{}, {}, undefined,{name:'NODENO',seo});
const config=async application=>(await application.fetch(new Request('https://nodenohome.com/api/config'))).json();

test('only the public Google ownership token is exposed from brand SEO settings',async()=>{
 const result=await config(app({googleVerification:token,bingVerification:'not-public',oauthSecret:'must-not-copy',homeTitle_en:'not-persisted-by-this-allowlist'}));
 assert.deepEqual(result.seo,{googleVerification:token});assert.equal(result.brand.seo,undefined);assert.ok(!JSON.stringify(result).includes('must-not-copy'));assert.ok(!JSON.stringify(result).includes('not-public'));
});

test('brand ownership token survives four-language server rendering as one verification meta tag',async()=>{
 const application=app({googleVerification:token});
 for(const lang of ['tr','en','ru','ar']){
  const r=await application.fetch(new Request('https://nodenohome.com/?lang='+lang));assert.equal(r.status,200);const html=await r.text();assert.equal((html.match(/name="google-site-verification"/g)||[]).length,1);assert.ok(html.includes('name="google-site-verification" content="'+token+'"'));
 }
});

test('missing or malformed ownership tokens leave the prior public config shape unchanged',async()=>{
 const baseline=await config(app(undefined));assert.equal(baseline.seo,undefined);
 for(const invalid of [null,false,42,{},[], '', '   ', '<meta name="google-site-verification">', 'bad token']){
  const application=app({googleVerification:invalid,oauthSecret:'must-not-copy'});assert.deepEqual(await config(application),baseline);const html=await(await application.fetch(new Request('https://nodenohome.com/?lang=en'))).text();assert.ok(!html.includes('name="google-site-verification"'));
 }
});
