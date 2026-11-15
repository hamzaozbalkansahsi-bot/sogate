import test from 'node:test';
import assert from 'node:assert/strict';
import {applyCatalogPrices,markedUpMinor,verifyPriceEvidence} from '../lib/catalog-pricing.mjs';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import os from 'node:os';

const at='2026-10-31T19:00:00Z';
const source={products:[{id:'1',code:'ABC-1'}]};
const catalog={products:[{id:'1',code:'Ndn-ABC-1',salePrice:null,availability:'unknown'}],meta:{}};
const record={productId:'1',sourceCode:'ABC-1',matchedSku:'ABC-1',matchedProductId:'1',sourceUrl:'https://www.adoremobilya.com/real',finalUrl:'https://www.adoremobilya.com/real',fetchedAt:at,status:'verified',currency:'TRY',sourcePriceMinor:809925,salePriceMinor:1052903,sourceDocumentSha256:'a'.repeat(64),displayPriceVerified:true};
const priceData={schema:1,supplier:'https://www.adoremobilya.com',currency:'TRY',pricingRule:{multiplier:'1.30',rounding:'ROUND_HALF_UP',minorUnit:100,conditionalPaymentDiscountsExcluded:true},products:[record]};
const run=data=>{const result=structuredClone(catalog);applyCatalogPrices(result,source,data,{now:Date.parse(at)});return result;};
test('authorized 30 percent markup uses exact integer kurus and half-up rounding',()=>{
 assert.equal(markedUpMinor(809925),1052903);
 assert.equal(markedUpMinor(43222),56189);
 assert.equal(markedUpMinor(1),1);
 assert.equal(markedUpMinor(2),3);
 assert.equal(markedUpMinor(1087667),1413967);
 const result=run(priceData),p=result.products[0];
 assert.equal(p.salePriceMinor,1052903);assert.equal(p.salePrice,10529.03);assert.equal(p.currency,'TRY');
 assert.equal(p.availability,'unknown');assert.equal(p.sourcePriceMinor,undefined);
 assert.equal(catalog.products[0].salePrice,null);
});
test('stale, unmatched, wrong currency, conditional or tampered prices fail closed',()=>{
 for(const change of [
  r=>{r.sourceCode='DIFFERENT';},r=>{r.matchedSku='DIFFERENT';},r=>{r.matchedProductId='2';},
  r=>{r.currency='USD';},r=>{r.salePriceMinor++;},r=>{r.sourcePriceMinor=0;},
  r=>{r.sourceUrl='https://untrusted.example/real';},r=>{r.finalUrl='http://www.adoremobilya.com/real';},
  r=>{r.fetchedAt='2026-10-20T00:00:00Z';},r=>{r.displayPriceVerified=false;},
 ]){const data=structuredClone(priceData);change(data.products[0]);assert.throws(()=>run(data),/price|pricing/i);}
 assert.throws(()=>run({...priceData,products:[]}),/price|pricing/i);
 assert.throws(()=>run({...priceData,products:[record,record]}),/price|pricing/i);
});
test('unverified prices remain unknown and supplier stock never becomes merchant stock',()=>{
 const data=structuredClone(priceData);data.products[0]={productId:'1',sourceCode:'ABC-1',status:'unavailable'};
 const p=run(data).products[0];assert.equal(p.salePrice,null);assert.equal(p.salePriceMinor,null);assert.equal(p.availability,'unknown');
});
test('the approved repricing snapshot carries the epoch that supersedes old price overrides',()=>{
 const data=structuredClone(priceData);data.generatedAt='2026-10-31T19:00:00Z';
 assert.deepEqual(run(data).meta.priceRefresh,{effectiveAt:1793473200,productIds:['1']});
});

test('price evidence binds the exact offer amount, SKU and product ID rather than only its document hash',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-pricing-'));
 try{
  const relative='artifacts/catalog-expansion/price-pages/a.html',file=path.join(root,relative);
  await mkdir(path.dirname(file),{recursive:true});
  const body='<script type="application/ld+json">'+JSON.stringify({'@graph':[{'@type':'Product',sku:'ABC-1',productID:'1',offers:{price:'8099.25',priceCurrency:'TRY',priceValidUntil:'2026-12-01',priceSpecification:{price:'99999.00'}}}]})+'</script>';
  await writeFile(file,body);
  const data=structuredClone(priceData),entry=data.products[0];
  entry.sourceDocumentFile=relative;entry.sourceDocumentSha256=createHash('sha256').update(body).digest('hex');entry.priceValidUntil='2026-12-01';
  await verifyPriceEvidence(root,data);
  entry.sourcePriceMinor=100;entry.salePriceMinor=markedUpMinor(100);
  assert.equal(run(data).products[0].salePriceMinor,130);
  await assert.rejects(verifyPriceEvidence(root,data),/pricing/i);
 }finally{
  assert.equal(path.dirname(root),path.resolve(os.tmpdir()));assert.ok(path.basename(root).startsWith('nodeno-pricing-'));
  await rm(root,{recursive:true,force:true});
 }
});
