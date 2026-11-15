import test from 'node:test';
import assert from 'node:assert/strict';
import {distinctModels,filterProducts,productDisplayName,quoteData,quoteText} from '../web/shop-core.js';
const name={tr:'Duvar Rafı - Sarı 120x25x20 cm',en:'Shelf - Yellow 120x25x20 cm'},modelName={tr:'Linea 11 Duvar Rafı',en:'Linea 11 Wall Shelf'};
const yellow={id:'yellow',code:'Ndn-RAF-11-HH-1',modelId:'shelf',name,modelName,variantColor:{tr:'Sarı',en:'Yellow'},categoryIds:['shelves'],currency:'TRY',salePriceMinor:14000};
const red={...yellow,id:'red',code:'Ndn-RAF-11-KK-1',variantColor:{tr:'Kırmızı',en:'Red'},salePriceMinor:16000};
test('model listings collapse colours while exact-code and colour searches keep the matching SKU',()=>{
 assert.deepEqual(distinctModels([yellow,red]),[yellow]);assert.deepEqual(filterProducts([yellow,red],{groupModels:true}),[yellow]);
 assert.deepEqual(filterProducts([yellow,red],{groupModels:true,query:red.code}),[red]);assert.deepEqual(filterProducts([yellow,red],{groupModels:true,query:'kırmızı'}),[red]);
 assert.deepEqual(filterProducts([yellow,red],{favorites:new Set(['yellow','red'])}),[yellow,red]);
});
test('two colours remain distinct basket lines with their exact prices and colours in exported lists',()=>{
 const quote=quoteData([{id:'yellow',quantity:2},{id:'red',quantity:1}],[yellow,red],'tr');
 assert.equal(quote.items.length,2);assert.equal(quote.items[0].name,modelName.tr);assert.equal(quote.items[0].color,'Sarı');assert.equal(quote.items[1].color,'Kırmızı');assert.equal(quote.subtotalMinor,44000);
 const text=quoteText([{id:'red',quantity:1}],[yellow,red],'tr');assert.ok(text.includes('Kırmızı'));assert.ok(text.includes(red.code));assert.ok(!text.includes('120x25x20'));
});
test('legacy products without model metadata keep their existing titles and separate identity',()=>{
 const a={id:'a',name:{tr:'Eski ürün'}},b={id:'b',name:{tr:'Eski ürün'}};assert.equal(productDisplayName(a),'Eski ürün');assert.deepEqual(distinctModels([a,b]),[a,b]);
});
