import test from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolveFurnitureSet,mergeFurnitureSetCart} from '../web/furniture-set-core.js';
import {applyFurnitureSets} from '../lib/furniture-sets.mjs';
const product=(id,price=10000,extra={})=>({id,code:'Ndn-'+id,modelId:'model-'+id,name:{tr:id},salePriceMinor:price,currency:'TRY',images:['/media/'+id+'/0'],...extra});
const catalog={products:[product('wardrobe',100000),product('nightstand',20000),product('dresser',50000),product('bed',80000),product('foreign')],furnitureSets:[{id:'bedroom',title:{tr:'Yatak odası'},members:[{productId:'wardrobe'},{productId:'nightstand'},{productId:'dresser'},{productId:'bed'}]}]};
test('custom set contains only explicitly chosen parts and multiplies two nightstands correctly',()=>{
 const r=resolveFurnitureSet(catalog,'bedroom',[{productId:'wardrobe',quantity:1},{productId:'nightstand',quantity:2},{productId:'dresser',quantity:1}],10);
 assert.deepEqual(r.items.map(i=>({id:i.id,quantity:i.quantity})),[{id:'dresser',quantity:10},{id:'nightstand',quantity:20},{id:'wardrobe',quantity:10}]);assert.equal(r.totalQuantity,40);assert.equal(r.totalMinor,1900000);assert.ok(!r.items.some(i=>i.id==='bed'));
});
test('set selection rejects foreign, hidden, duplicate, empty, stale and unsafe component quantities',()=>{
 for(const input of [[],[{productId:'foreign',quantity:1}],[{productId:'nightstand',quantity:0}],[{productId:'nightstand',quantity:1.5}],[{productId:'nightstand',quantity:1},{productId:'nightstand',quantity:1}]])assert.throws(()=>resolveFurnitureSet(catalog,'bedroom',input));
 assert.throws(()=>resolveFurnitureSet(catalog,'missing',[{productId:'nightstand',quantity:1}]));assert.throws(()=>resolveFurnitureSet({...catalog,products:catalog.products.filter(p=>p.id!=='nightstand')},'bedroom',[{productId:'nightstand',quantity:1}]));
 assert.throws(()=>resolveFurnitureSet(catalog,'bedroom',[{productId:'nightstand',quantity:99}],10000000));
});
test('retail batch adds all components atomically and never clamps an existing line above 99',()=>{
 const r=resolveFurnitureSet(catalog,'bedroom',[{productId:'nightstand',quantity:2},{productId:'dresser',quantity:1}]);const original=[{id:'nightstand',quantity:98}];assert.throws(()=>mergeFurnitureSetCart(original,r.items,catalog.products));assert.deepEqual(original,[{id:'nightstand',quantity:98}]);assert.deepEqual(mergeFurnitureSetCart([{id:'nightstand',quantity:1}],r.items,catalog.products),[{id:'nightstand',quantity:3},{id:'dresser',quantity:1}]);
 const unknown=catalog.products.map(p=>p.id==='nightstand'?{...p,salePriceMinor:null}:p);assert.throws(()=>mergeFurnitureSetCart([],r.items,unknown));const full=Array.from({length:100},(_,i)=>product('p'+i));assert.throws(()=>mergeFurnitureSetCart(full.map(p=>({id:p.id,quantity:1})),r.items,[...full,...catalog.products]));
});
test('PDF verified catalogue defines seventeen editable rooms and preserves fixed-SKU sets without fabricating missing items',async()=>{
 const mapping=JSON.parse(await readFile('data/furniture-sets.json','utf8'));assert.equal(mapping.sets.length,17);assert.deepEqual(mapping.sets.find(s=>s.id==='bohera-bedroom').members.map(m=>m.productId).sort(),['4907','4910','4911','4915']);assert.equal(new Set(mapping.unmatched.map(v=>v.code)).size,5);assert.ok(mapping.fixedSetProducts.some(p=>p.productId==='4883'));
 const actual=JSON.parse(await readFile('artifacts/cpanel-release/private/catalog.json','utf8'));const hashes={sourceCatalogSha256:mapping.sourceCatalogSha256,identitiesSha256:mapping.identitiesSha256,pdfSha256:mapping.pdfSha256};applyFurnitureSets(actual,mapping,hashes);assert.equal(actual.products.find(p=>p.id==='4883').saleUnit,'set');assert.equal(actual.products.find(p=>p.id==='4911').saleUnit,'piece');assert.equal(actual.furnitureSets.length,17);assert.throws(()=>applyFurnitureSets(actual,mapping,{...hashes,pdfSha256:'0'.repeat(64)}));
});
