import test from 'node:test';
import assert from 'node:assert/strict';
import {measurementLines,mergeMeasurementCart,measurementSummary,demoRows} from '../web/measurement-core.js';
import {doorOptions,doorPrice,doorLineKey} from '../web/door-core.js';
import {applyDoorMeasurementPolicy} from '../lib/door-catalog.mjs';
const front={id:'front-1',productType:'cabinet-front',salePriceMinor:255500,front:{material:'pvc'}};
const door={id:'door-1',modelId:'model-1',productType:'door',salePriceMinor:696500,door:{glassAvailable:true,charges:{depth:{17:18000,19:30000,21:45500},glazing:99000}}};
const glass={id:'door-glass-1',modelId:'model-1',productType:'door',salePriceMinor:null,door:{kind:'glazed'}};
const dimensions={heightMm:2070,leafWidthMm:770,frameWidthMm:115};
test('one front form creates all requested sizes and applications with exact areas and mixed quote totals',()=>{
 const rows=[{quantity:2,options:{heightMm:1975,widthMm:225,application:'solid'}},{quantity:2,options:{heightMm:1914,widthMm:255,application:'glazed'}},{quantity:3,options:{heightMm:247,widthMm:597,application:'drawer'}}];
 const lines=measurementLines(front,rows,[front]);assert.equal(lines.length,3);assert.equal(new Set(lines.map(x=>x.key)).size,3);
 const s=measurementSummary(lines,[front]);assert.equal(s.areaMm2,1975*225*2+1914*255*2+247*597*3);assert.equal(s.quoteLines,1);assert.equal(s.totalMinor,null);assert.ok(s.knownMinor>0);
});
test('door widths use exact confirmed frame dimensions, updated fees and standard 770/870 leaves',()=>{
 for(const frameWidthMm of [95,115,145,165])assert.equal(doorPrice(door,{...dimensions,frameWidthMm}).unitPriceMinor,696500);
 assert.equal(doorPrice(door,{...dimensions,frameWidthMm:185}).unitPriceMinor,726500);
 assert.equal(doorPrice(door,{...dimensions,frameWidthMm:215}).unitPriceMinor,742000);
 assert.equal(doorPrice(door,{...dimensions,heightMm:2071}).requiresQuote,true);
 for(const input of [{...dimensions,frameWidthMm:110},{...dimensions,leafWidthMm:900},{...dimensions,heightMm:2070.5}])assert.throws(()=>doorOptions(input,door));
 const a=doorOptions(dimensions,door),b=doorOptions({...dimensions,leafWidthMm:870},door);assert.notEqual(doorLineKey(door.id,a),doorLineKey(door.id,b));
});
test('a glazed row needs a real same-model glass choice and keeps its own count and price',()=>{
 const rows=[{quantity:2,options:dimensions},{quantity:2,options:{...dimensions,leafWidthMm:870,frameWidthMm:145}},{quantity:1,options:{...dimensions,leafWidthMm:870,glazed:true,glassModelId:glass.id}}];
 const lines=measurementLines(door,rows,[door,glass]);assert.equal(lines.length,3);assert.equal(measurementSummary(lines,[door,glass]).quantity,5);assert.equal(measurementSummary(lines,[door,glass]).totalMinor,696500*5+99000);
 for(const id of ['',front.id,'door-unknown'])assert.throws(()=>measurementLines(door,[{quantity:1,options:{...dimensions,glazed:true,glassModelId:id}}],[door,glass,front]));
});
test('batch addition is atomic, combines identical configurations and refuses overflow instead of truncating',()=>{
 const rows=[{quantity:2,options:dimensions},{quantity:3,options:dimensions}],lines=measurementLines(door,rows,[door]);const original=[{...lines[0],quantity:1}];
 const next=mergeMeasurementCart(original,lines);assert.equal(next.length,1);assert.equal(next[0].quantity,6);assert.equal(original[0].quantity,1);
 assert.throws(()=>mergeMeasurementCart([{...lines[0],quantity:9999}],lines));assert.equal(original[0].quantity,1);
 assert.throws(()=>measurementLines(front,[{quantity:1,options:{widthMm:500,heightMm:1000}},{quantity:2,options:{heightMm:0,widthMm:225}}],[front]));
 assert.throws(()=>mergeMeasurementCart(Array.from({length:100},(_,i)=>({id:'other-'+i,quantity:1})),lines));
});
test('a repeated front measurement uses the same whole-line rounding before and after cart merging',()=>{
 const p={...front,salePriceMinor:273500},rows=[{quantity:1,options:{heightMm:777,widthMm:333}},{quantity:1,options:{heightMm:777,widthMm:333}}];
 const lines=measurementLines(p,rows,[p]),before=measurementSummary(lines,[p]),after=measurementSummary(mergeMeasurementCart([],lines),[p]);
 assert.equal(before.totalMinor,141531);assert.equal(before.totalMinor,after.totalMinor);assert.equal(before.quantity,2);
});
test('demos are detached examples with current frame widths and cannot edit the product or previous example',()=>{
 const a=demoRows('door'),b=demoRows('door');a[0].options.heightMm=3000;assert.equal(b[0].options.heightMm,2070);assert.deepEqual(b.map(r=>r.options.frameWidthMm),[115,145,115]);
 assert.deepEqual(demoRows('cabinet-front').map(r=>r.quantity),[2,2,3]);
});
test('the owner correction updates customer descriptions in four languages while retaining immutable source facts and prices',()=>{
 const p={...door,door:{...door.door,baseFrameDepthMaxCm:15},description:{tr:'15 cm’ye kadar',en:'up to 15 cm',ru:'до 15 см',ar:'حتى 15 سم'}};
 const catalog=applyDoorMeasurementPolicy({products:[p,front],meta:{},doorPolicy:{}});
 assert.equal(p.door.baseFrameDepthMaxCm,15);assert.equal(p.description.en,'up to 15 cm');assert.equal(catalog.products[0].door.baseFrameDepthMaxCm,17);assert.equal(catalog.products[0].salePriceMinor,p.salePriceMinor);
 assert.equal(catalog.products[0].description.en,'up to 17 cm');assert.equal(catalog.products[0].description.ar,'حتى 17 سم');assert.deepEqual(catalog.products[1],front);
});
