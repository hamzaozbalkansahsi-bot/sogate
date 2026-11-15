import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {normalizeCatalog} from '../lib/catalog.mjs';

const sourceBytes=await readFile(new URL('../data/catalog-source.json',import.meta.url));
const source=JSON.parse(sourceBytes);
const identities=JSON.parse(await readFile(new URL('../data/catalog-identities.json',import.meta.url),'utf8'));
const build=map=>normalizeCatalog(source,{identities:map});

test('all exact PDF matches use the catalogue code and reviewed name in four languages',()=>{
 const {catalog,report}=build(identities),byId=new Map(catalog.products.map(p=>[p.id,p]));
 assert.equal(identities.sourceCatalogSha256,createHash('sha256').update(sourceBytes).digest('hex'));
 assert.equal(report.catalogueIdentities,667);
 for(const entry of identities.products){
  const p=byId.get(entry.id);
  assert.equal(p.code,entry.code);
  assert.deepEqual(p.name,identities.names[entry.name]);
  for(const lang of ['tr','en','ru','ar']){
   assert.ok(p.description[lang].includes(entry.code));
   assert.ok(p.description[lang].includes(p.name[lang]));
  }
 }
 assert.deepEqual(catalog.meta.translationPending,{en:0,ru:0,ar:0});
});

test('renaming preserves every identity, media reference, technical fact and unmatched product',()=>{
 const before=JSON.stringify(source),baseline=normalizeCatalog(source),updated=build(identities);
 const mapped=new Set(identities.products.map(p=>p.id));
 assert.deepEqual(updated.media,baseline.media);
 assert.deepEqual(updated.catalog.categories,baseline.catalog.categories);
 assert.equal(updated.catalog.products.length,667);
 assert.equal(new Set(updated.catalog.products.map(p=>p.code)).size,667);
 for(let i=0;i<baseline.catalog.products.length;i++){
  const old=baseline.catalog.products[i],next=updated.catalog.products[i];
  assert.equal(next.id,old.id);
  for(const key of ['specs','images','coverIndex','categoryIds','salePrice','availability']) assert.deepEqual(next[key],old[key],`${old.id}/${key}`);
  if(!mapped.has(old.id))assert.deepEqual(next,old);
 }
 assert.equal(JSON.stringify(source),before);
});

test('catalogue names cannot hide optional modules or excluded wardrobe parts',()=>{
 const {catalog}=build(identities);
 for(const id of ['3659','4755','4756','4757','4758','4759','4760','4761','4762','4763']){
  const entry=identities.products.find(p=>p.id===id),p=catalog.products.find(p=>p.id===id);
  assert.deepEqual(p.scopeNote,entry.notes);
  for(const lang of ['tr','en','ru','ar'])assert.ok(p.description[lang].includes(entry.notes[lang]));
 }
});

test('stale, ambiguous, incomplete or colliding mappings stop publication',()=>{
 const changed=mutation=>{const m=structuredClone(identities);mutation(m);return m;};
 for(const mutation of [
  m=>{m.products[0].sourceCode='WRONG';},
  m=>{m.products[0].sourceName='Wrong title';},
  m=>{m.products[0].id='nonexistent';},
  m=>{m.products.push(m.products[0]);},
  m=>{m.products[1].code=m.products[0].code;},
  m=>{delete m.names[m.products[0].name].ar;},
  m=>{m.products[0].code='invented';},
  m=>{m.products.pop();},
  m=>{m.websiteOnly.push({id:source.products[0].id,code:source.products[0].code,name:source.products[0].title});},
 ])assert.throws(()=>build(changed(mutation)),/catalogue|identity|mapping|code|name|coverage/i);
});
