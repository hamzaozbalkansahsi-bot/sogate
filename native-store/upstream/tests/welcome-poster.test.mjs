import test from 'node:test';
import assert from 'node:assert/strict';
import {welcomeCountries,welcomeCopy,welcomeEligible,createWelcomeMemory,WELCOME_TIMEOUT,WELCOME_KEY} from '../web/welcome-poster.js';
import {welcomeMapData} from '../web/welcome-map-data.js';

test('the poster contains exactly the ten markets confirmed by the owner in every storefront language',()=>{
 assert.deepEqual(welcomeCountries.map(c=>c.code),['DE','GB','AZ','KZ','TM','UZ','KG','IQ','IR','SY']);
 for(const locale of ['tr','en','ru','ar']){
  assert.ok(welcomeCopy[locale].title&&welcomeCopy[locale].close&&welcomeCopy[locale].countries&&welcomeCopy[locale].dontShow);
  assert.ok(welcomeCountries.every(c=>typeof c[locale]==='string'&&c[locale].length>1));
 }
 assert.equal(WELCOME_TIMEOUT,30_000);
});
test('only an explicit do-not-show choice hides the poster across visits',()=>{
 const values=new Map();const storage={getItem:key=>values.get(key)||null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)};
 const memory=createWelcomeMemory(storage);
 assert.equal(memory.hidden(),false);
 assert.equal(createWelcomeMemory(storage).hidden(),false);
 assert.equal(memory.setHidden(true),true);
 assert.equal(createWelcomeMemory(storage).hidden(),true);
 assert.deepEqual([...values.values()],['1']);
 assert.equal(memory.setHidden(false),true);
 assert.equal(createWelcomeMemory(storage).hidden(),false);
});
test('legacy automatic seen flags are ignored and corrupt values never count as consent',()=>{
 const values=new Map([['nodeno.international-welcome.seen','1']]);
 const storage={getItem:key=>values.get(key)||null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)};
 assert.equal(createWelcomeMemory(storage).hidden(),false);
 values.set(WELCOME_KEY,'broken');assert.equal(createWelcomeMemory(storage).hidden(),false);
});
test('blocked storage allows the greeting and honestly reports an unsaved preference',()=>{
 const blocked={getItem(){throw Error('disabled');},setItem(){throw Error('disabled');}};
 assert.equal(createWelcomeMemory(blocked).hidden(),false);
 assert.equal(createWelcomeMemory(blocked).setHidden(true),false);
 assert.equal(createWelcomeMemory(null).hidden(),false);
});
test('checkout and account flows are never interrupted by the welcome poster',()=>{
 for(const page of ['cart','checkout','login','register','account','orders','shipping','help','unknown'])assert.equal(welcomeEligible(page),false,page);
 for(const page of ['home','catalog','product','sets','wholesale','categories'])assert.equal(welcomeEligible(page),true,page);
});
test('the map contains real individually addressable geometry and localized names',()=>{
 assert.equal(new Set(welcomeMapData.regions.map(r=>r.id)).size,welcomeMapData.regions.length);
 for(const code of [...welcomeCountries.map(c=>c.code),'TR','FR'])assert.ok(welcomeMapData.regions.some(r=>r.code===code),code);
 for(const region of welcomeMapData.regions){
  assert.match(region.path,/^M[0-9,.-]+/);
  assert.ok(!/[<>"'{};]/.test(region.path));
  for(const lang of ['tr','en','ru','ar'])assert.ok(typeof region.names[lang]==='string'&&region.names[lang].length>0);
 }
});
