import test from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {frontOptions,frontLineKey,frontPrice,frontCartStatus} from '../web/cabinet-front-core.js';
const pvc={id:'front-739-pvc',productType:'cabinet-front',salePriceMinor:257500,front:{material:'pvc'}};

test('cabinet fronts and complementary parts never become colour variants of each other after brand prefix replacement',async()=>{
 const data=JSON.parse(await readFile(new URL('../data/cabinet-fronts.json',import.meta.url))),types=new Map();
 for(const p of data.products){if(types.has(p.modelId))assert.equal(types.get(p.modelId),p.productType,p.code);types.set(p.modelId,p.productType);}
});
test('custom front dimensions use exact square millimetres and round each complete line once',()=>{
 const o=frontOptions({widthMm:500,heightMm:1000});const price=frontPrice(pvc,o,10);
 assert.equal(price.areaMm2,5000000);assert.equal(price.unitPriceMinor,128750);assert.equal(price.lineTotalMinor,1287500);
 const small=frontPrice({...pvc,salePriceMinor:349500},{widthMm:333,heightMm:777},3);
 assert.equal(small.lineTotalMinor,Number((349500n*333n*777n*3n+500000n)/1000000n));
});
test('Türkiye five square metres and international ten square metres count mixed fronts but exclude doors',()=>{
 const products=[pvc,{...pvc,id:'front-lake',front:{material:'lacquer'}},{id:'door-1',productType:'door'}];
 const items=[{id:pvc.id,quantity:5,options:{widthMm:500,heightMm:1000}},{id:'front-lake',quantity:5,options:{widthMm:500,heightMm:1000}},{id:'door-1',quantity:100}];
 assert.equal(frontCartStatus(items,products,'TR').eligible,true);assert.equal(frontCartStatus(items,products,'DE').missingAreaMm2,5000000);
 items[0].quantity=4;assert.equal(frontCartStatus(items,products,'TR').eligible,false);
});
test('measurements are mandatory, variants remain distinct, unknown prices and glazing require a quote',()=>{
 for(const o of [{},{widthMm:-1,heightMm:500},{widthMm:500.5,heightMm:1000},{widthMm:500,heightMm:1000,price:1}])assert.throws(()=>frontOptions(o));
 assert.notEqual(frontLineKey(pvc.id,frontOptions({widthMm:500,heightMm:1000})),frontLineKey(pvc.id,frontOptions({widthMm:501,heightMm:1000})));
 assert.equal(frontPrice(pvc,{widthMm:500,heightMm:1000,application:'glazed'},1).requiresQuote,true);
 assert.equal(frontPrice({...pvc,salePriceMinor:null},{widthMm:500,heightMm:1000},1).lineTotalMinor,null);
});
