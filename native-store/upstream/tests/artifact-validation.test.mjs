import test from 'node:test';
import assert from 'node:assert/strict';
import {assertArtifactCatalog} from '../lib/artifact-validation.mjs';

const localized=text=>Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,text]));
const product=(id,productType,price,images=['/reviewed.png'])=>({id,code:'reviewed-code-'+id,productType,name:localized(id),description:localized(id+' specification'),salePriceMinor:price,currency:'TRY',images});
const expected={products:[product('original','furniture',1100),product('door','door',2400),product('front','cabinet-front',null),product('supplier','supplier-item',3600),product('approved-no-photo','supplier-item',800,[])],categories:[{id:'category',name:localized('Category')}],brand:{name:'NODENO'},meta:{mediaVersion:'a'.repeat(64),doorCatalogVersion:'doors-proof',frontCatalogVersion:'fronts-proof',supplierCatalogVersion:'supplier-proof',furnitureSetsVersion:'sets-proof'}};
const artifact=()=>({...structuredClone(expected),meta:{...expected.meta,releaseHash:'b'.repeat(64)}});

test('expanded catalogue validates against reviewed product sources without a legacy-only code or count rule',()=>{
 const value=assertArtifactCatalog(artifact(),expected);assert.equal(value.products,5);assert.equal(value.approvedNoPhotoProducts,1);
});
test('source-approved door variants retain a shared model code while their SKU identities remain separate',()=>{
 const reviewed=structuredClone(expected);reviewed.products.push({...product('door-glazed','door',3200),code:reviewed.products[1].code});const actual={...structuredClone(reviewed),meta:{...reviewed.meta,releaseHash:'b'.repeat(64)}};
 assert.doesNotThrow(()=>assertArtifactCatalog(actual,reviewed));actual.products.at(-1).id='door';assert.throws(()=>assertArtifactCatalog(actual,reviewed));
});
test('changed known or unknown prices, quantity units and technical selections fail across every product source',()=>{
 for(const index of [0,1,2,3]){const actual=artifact();actual.products[index].salePriceMinor=999;assert.throws(()=>assertArtifactCatalog(actual,expected));}
 for(const change of [p=>{p.saleUnit='meter';},p=>{p.code='wrong-code';},p=>{p.description.ar='invented';}]){const actual=artifact();change(actual.products[3]);assert.throws(()=>assertArtifactCatalog(actual,expected));}
});
test('missing, duplicate or extra records cannot hide a source catalogue loss',()=>{
 for(const change of [rows=>rows.pop(),rows=>rows.push({...rows[0]}),rows=>rows.push(product('extra','supplier-item',1))]){const actual=artifact();change(actual.products);assert.throws(()=>assertArtifactCatalog(actual,expected));}
});
test('only the approved no-photo record may keep no image; fake replacements or newly hidden images fail',()=>{
 const allowed=artifact();assert.doesNotThrow(()=>assertArtifactCatalog(allowed,expected));
 const replaced=artifact();replaced.products[4].images=['/unreviewed-placeholder.png'];assert.throws(()=>assertArtifactCatalog(replaced,expected));
 const hidden=artifact();hidden.products[3].images=[];assert.throws(()=>assertArtifactCatalog(hidden,expected));
});
test('test fixtures, changed publication proofs, brand and categories are not production artifacts',()=>{
 for(const change of [a=>{a.meta.testOnly=true;},a=>{a.meta.supplierCatalogVersion='unreviewed';},a=>{a.meta.releaseHash='bad';},a=>{a.brand.name='Wrong';},a=>{a.categories=[];}]){const actual=artifact();change(actual);assert.throws(()=>assertArtifactCatalog(actual,expected));}
});
