import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {normalizeCatalog} from '../lib/catalog.mjs';
import {applyProductModels} from '../lib/product-models.mjs';
const bytes=await readFile(new URL('../data/catalog-source.json',import.meta.url));
const identityBytes=await readFile(new URL('../data/catalog-identities.json',import.meta.url));
const source=JSON.parse(bytes),identities=JSON.parse(identityBytes),mapping=JSON.parse(await readFile(new URL('../data/product-models.json',import.meta.url),'utf8'));
const hashes={sourceCatalogSha256:createHash('sha256').update(bytes).digest('hex'),identitiesSha256:createHash('sha256').update(identityBytes).digest('hex')};
const build=()=>normalizeCatalog(source,{identities}).catalog;
test('667 SKU records keep every original fact while 392 models get concise names',()=>{
 const catalog=build(),before=structuredClone(catalog.products);applyProductModels(catalog,source,mapping,hashes);
 assert.equal(catalog.meta.modelCount,392);
 for(let i=0;i<before.length;i++){const {modelId,modelName,variantColor,colorReviewPending,...original}=catalog.products[i];assert.deepEqual(original,before[i]);assert.ok(modelId);for(const lang of ['tr','en','ru','ar']){assert.ok(modelName[lang]);assert.doesNotMatch(modelName[lang],/\d\s*[x×]\s*\d|GxYxD|W×H×D|Ш×В×Г/i);}}
});
test('all thirteen Linea 11 shelf colours form one model, with yellow retaining its own SKU',()=>{
 const catalog=build();applyProductModels(catalog,source,mapping,hashes);const yellow=catalog.products.find(p=>p.id==='2769'),family=catalog.products.filter(p=>p.modelId===yellow.modelId);
 assert.equal(family.length,13);assert.equal(yellow.modelName.tr,'Linea 11 Duvar Rafı');assert.equal(yellow.variantColor.tr,'Sarı');assert.equal(yellow.code,'Ndn-RAF-11-HH-1');assert.equal(new Set(family.map(p=>p.variantColor.tr)).size,13);
});
test('different shelf sizes, chair materials and conflicting colour records stay apart',()=>{
 const catalog=build();applyProductModels(catalog,source,mapping,hashes);const byId=id=>catalog.products.find(p=>p.id===id);
 assert.notEqual(byId('2769').modelId,byId('2747').modelId);assert.notEqual(byId('4653').modelId,byId('4651').modelId);assert.notEqual(byId('4787').modelId,byId('4788').modelId);assert.notEqual(byId('4865').modelId,byId('4870').modelId);
 assert.equal(byId('5039').modelId,byId('5043').modelId);
 assert.equal(byId('4725').colorReviewPending,true);assert.equal(byId('4788').variantColor,undefined);
});
test('stale, incomplete, duplicate, renamed or physically incompatible model mappings stop builds',()=>{
 for(const mutate of [m=>m.sourceCatalogSha256='0'.repeat(64),m=>m.identitiesSha256='0'.repeat(64),m=>m.models.pop(),m=>m.models[0].productIds.push(m.models[1].productIds[0]),m=>m.models[0].name.tr='Uydurma ürün',m=>m.models.find(m=>m.productIds.includes('2769')).productIds.push('2747')]){
  const copy=structuredClone(mapping);mutate(copy);assert.throws(()=>applyProductModels(build(),source,copy,hashes),/model|variant|mapping/i);
 }
});
