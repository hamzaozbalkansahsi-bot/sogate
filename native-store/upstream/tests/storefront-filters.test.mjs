import test from 'node:test';
import assert from 'node:assert/strict';
import {filterProducts,priceFilterMinor,categoryNavigation} from '../web/shop-core.js';
const product=(id,price,color,modelId=id)=>({id,modelId,name:{tr:'Dolap '+id,en:'Cabinet '+id},variantColor:{tr:color,en:color==='Beyaz'?'White':'Oak'},code:id,currency:'TRY',salePriceMinor:price,categoryIds:['cabinets']});
const products=[product('white',200050,'Beyaz','family'),product('oak',190000,'Meşe','family'),product('other',400000,'Beyaz'),product('unknown',null,'Meşe')];
test('price sorting uses actual minor amounts, puts unknowns last, and never changes source order',()=>{
 const original=products.map(p=>p.id);
 assert.deepEqual(filterProducts(products,{sort:'price-asc'}).map(p=>p.id),['oak','white','other','unknown']);
 assert.deepEqual(filterProducts(products,{sort:'price-desc'}).map(p=>p.id),['other','white','oak','unknown']);
 assert.deepEqual(products.map(p=>p.id),original);
});
test('price boundaries are inclusive and colour matches the selected variant before model grouping',()=>{
 assert.deepEqual(filterProducts(products,{minPriceMinor:190000,maxPriceMinor:200050}).map(p=>p.id),['white','oak']);
 assert.deepEqual(filterProducts(products,{color:'Meşe',groupModels:true,minPriceMinor:0}).map(p=>p.id),['oak']);
 assert.deepEqual(filterProducts(products,{color:'Beyaz',query:'other',groupModels:true,maxPriceMinor:400000}).map(p=>p.id),['other']);
 assert.deepEqual(filterProducts(products,{minPriceMinor:400001,maxPriceMinor:200050}),[]);
});
test('price input converts decimal strings to exact kurus and rejects ambiguous or hostile formats',()=>{
 assert.equal(priceFilterMinor('2000.50'),200050);assert.equal(priceFilterMinor('0'),0);assert.equal(priceFilterMinor('12,4'),1240);
 for(const value of ['',null,undefined,'1e6','-1','1.234','1,000.50','Infinity',{},true])assert.equal(priceFilterMinor(value),null);
});
test('category navigation keeps roots and active lineage with direct children and is cycle safe',()=>{
 const categories=[{id:'kitchen',parentId:null},{id:'office',parentId:null},{id:'cabinets',parentId:'kitchen'},{id:'bath',parentId:'kitchen'},{id:'small',parentId:'cabinets'},{id:'chairs',parentId:'office'},{id:'cycle',parentId:'cycle'}];
 assert.deepEqual(categoryNavigation(categories,'small').map(c=>[c.id,c.depth]),[['kitchen',0],['cabinets',1],['small',2],['bath',1],['office',0]]);
 assert.deepEqual(categoryNavigation(categories,'kitchen').map(c=>c.id),['kitchen','cabinets','bath','office']);
 assert.deepEqual(categoryNavigation(categories,'missing').map(c=>c.id),['kitchen','office']);
 assert.ok(categoryNavigation(categories,'cycle').length<=categories.length);
});
