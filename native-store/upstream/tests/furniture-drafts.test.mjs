import test from 'node:test';
import assert from 'node:assert/strict';
import {createFurnitureDraftStore} from '../web/furniture-drafts.js';
const product=(id,modelId=id,extra={})=>({id,modelId,...extra});
const catalog={products:[product('wardrobe'),product('nightstand-oak','nightstand'),product('nightstand-white','nightstand'),product('bed'),product('foreign')],furnitureSets:[{id:'room',members:['wardrobe','nightstand-oak','nightstand-white','bed'].map(productId=>({productId}))}]};
const draft={setId:'room',mode:'retail',owner:'guest',repeat:1,components:[{productId:'wardrobe',quantity:1},{productId:'nightstand-oak',quantity:2}],variants:['wardrobe','nightstand-oak','bed']};
const storage=()=>{const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};};
// Catches losing real quantities/colours after component recreation, or persisting contact/price data.
test('recreated draft store restores exact pieces without storing prices or customer fields',()=>{
 const s=storage();assert.equal(createFurnitureDraftStore(s).save(catalog,{...draft,email:'private@example.test',price:1}),true);
 const saved=createFurnitureDraftStore(s).load(catalog,'room','retail','guest');assert.deepEqual(saved.components,[{productId:'wardrobe',quantity:1},{productId:'nightstand-oak',quantity:2}]);assert.equal(saved.repeat,1);assert.ok(!saved.components.some(c=>c.productId==='bed'));assert.deepEqual(saved.variants,['wardrobe','nightstand-oak','bed']);assert.ok(!JSON.stringify(s.getItem('nodeno.furniture-drafts.v1')).includes('private@example.test'));
});
// Catches sharing a wholesale multiplier or a prior customer's selections with another scope.
test('retail and wholesale quantities are isolated and a new owner cannot restore a previous draft',()=>{
 const store=createFurnitureDraftStore(storage());store.save(catalog,draft);store.save(catalog,{...draft,mode:'wholesale',repeat:1000});assert.equal(store.load(catalog,'room','retail','guest').repeat,1);assert.equal(store.load(catalog,'room','wholesale','guest').repeat,1000);assert.equal(store.load(catalog,'room','retail','different-user'),null);store.save(catalog,{...draft,owner:'different-user',repeat:2});assert.equal(store.load(catalog,'room','retail','guest'),null);
});
// Catches restoring products that were removed or hidden after the previous visit.
test('restore revalidates current membership and drops unavailable parts without substituting another SKU',()=>{
 const store=createFurnitureDraftStore(storage());store.save(catalog,draft);const current={...catalog,products:catalog.products.map(p=>p.id==='nightstand-oak'?{...p,hidden:true}:p)};const loaded=store.load(current,'room','retail','guest');assert.deepEqual(loaded.components,[{productId:'wardrobe',quantity:1}]);assert.equal(loaded.adjusted,true);assert.ok(!loaded.variants.includes('nightstand-oak'));assert.ok(!loaded.components.some(c=>c.productId==='nightstand-white'));
});
// Catches blank input overwriting the last valid selection and accepting impossible/foreign parts.
test('invalid edits do not overwrite the last valid draft and clear removes the requested scope',()=>{
 const store=createFurnitureDraftStore(storage());store.save(catalog,draft);for(const changed of [{repeat:0},{repeat:100},{components:[{productId:'foreign',quantity:1}]},{components:[{productId:'bed',quantity:0}]},{components:[{productId:'nightstand-oak',quantity:1},{productId:'nightstand-white',quantity:2}]}])assert.equal(store.save(catalog,{...draft,...changed}),false);assert.deepEqual(store.load(catalog,'room','retail','guest').components,draft.components);store.save(catalog,{...draft,mode:'wholesale',repeat:10});store.clear('room','retail','guest');assert.equal(store.load(catalog,'room','retail','guest'),null);assert.equal(store.load(catalog,'room','wholesale','guest').repeat,10);
});
// Catches a disabled, full or corrupted browser store breaking normal shopping.
test('blocked or corrupted browser storage never throws or invents a selection',()=>{
 const broken=createFurnitureDraftStore({getItem(){throw new Error('blocked');},setItem(){throw new Error('full');},removeItem(){throw new Error('blocked');}});assert.equal(broken.save(catalog,draft),false);assert.equal(broken.load(catalog,'room','retail','guest'),null);assert.doesNotThrow(()=>broken.clear('room','retail','guest'));const s=storage();s.setItem('nodeno.furniture-drafts.v1','not-json');assert.equal(createFurnitureDraftStore(s).load(catalog,'room','retail','guest'),null);
});
