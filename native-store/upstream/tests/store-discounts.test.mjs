import test from 'node:test';
import assert from 'node:assert/strict';
import {applyStoreDiscounts,verifyStoreHistoryEvidence} from '../lib/store-discounts.mjs';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import os from 'node:os';
const now=Date.parse('2026-10-31T20:00:00Z');
const policy={schema:1,mode:'preserve'};
const product={id:'1',code:'Ndn-A-1',salePriceMinor:1133895,salePrice:11338.95,currency:'TRY'};
const history={schema:1,origin:'https://nodenohome.com',currency:'TRY',firstPricedVerifiedAt:'2026-10-31T19:35:27Z',snapshots:[{at:'2026-10-31T19:35:27Z',observedAt:'2026-10-31T19:35:27Z',products:[{id:'1',code:'Ndn-A-1',priceMinor:1133895,currency:'TRY'}]}]};
const run=(p=policy,h=history,item=product)=>{const catalog={products:[structuredClone(item)],meta:{pricing:{}}};applyStoreDiscounts(catalog,h,p,{now});return catalog.products[0];};
test('unchanged actual prices never become invented struck-through prices',()=>{
 const p=run();assert.equal(p.salePriceMinor,1133895);assert.equal(p.previousPriceMinor,undefined);assert.equal(p.discountPercent,undefined);
});
test('a deliberate percentage reduction uses the actual published baseline and exact kurus',()=>{
 const p=run({schema:1,mode:'percentage',percent:10,effectiveAt:'2026-10-31T19:55:00Z'});
 assert.equal(p.salePriceMinor,1020506);assert.equal(p.salePrice,10205.06);assert.equal(p.previousPriceMinor,1133895);assert.equal(p.discountPercent,10);
 assert.equal(product.salePriceMinor,1133895);
});
test('the reference is the ten-day minimum, including a price carried into the window',()=>{
 const h={...history,firstPricedVerifiedAt:'2026-10-15T10:00:00Z',snapshots:[{at:'2026-10-15T10:00:00Z',observedAt:'2026-10-15T10:00:00Z',products:[{...history.snapshots[0].products[0],priceMinor:10000}]},{at:'2026-10-25T10:00:00Z',observedAt:'2026-10-25T10:00:00Z',products:[{...history.snapshots[0].products[0],priceMinor:15000}]}]};
 const p=run(policy,h,{...product,salePriceMinor:9000,salePrice:90});assert.equal(p.previousPriceMinor,10000);assert.equal(p.discountPercent,10);
 const unchanged=run(policy,h,{...product,salePriceMinor:12000,salePrice:120});assert.equal(unchanged.previousPriceMinor,undefined);
});
test('new products, unknown prices and mismatched identities have no old-price claim',()=>{
 for(const item of [{...product,id:'new'},{...product,code:'Ndn-OTHER'},{...product,salePriceMinor:null,salePrice:null}])assert.equal(run(policy,history,item).previousPriceMinor,undefined);
});
test('campaign reference excludes its own later discounted publication',()=>{
 const p={schema:1,mode:'percentage',percent:10,effectiveAt:'2026-10-31T19:45:00Z'};
 const h=structuredClone(history);h.snapshots.push({at:'2026-10-31T19:50:00Z',observedAt:'2026-10-31T19:50:00Z',products:[{...h.snapshots[0].products[0],priceMinor:1020506}]});
 assert.equal(run(p,h).previousPriceMinor,1133895);
});
test('invalid policies and fabricated future or duplicate history stop the build',()=>{
 for(const p of [{schema:1,mode:'invented'},{schema:1,mode:'percentage',percent:0,effectiveAt:'2026-10-31T19:45:00Z'},{schema:1,mode:'percentage',percent:10,effectiveAt:'2026-11-02T00:00:00Z'}])assert.throws(()=>run(p),/discount|history/i);
 const h=structuredClone(history);h.snapshots.push(h.snapshots[0]);assert.throws(()=>run(policy,h),/history/i);
});

test('a higher made-up reference cannot replace the price in a published package',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-history-'));
 try{
  const bytes=JSON.stringify({products:[product]});
  const catalogueSha256=createHash('sha256').update(bytes).digest('hex');
  const files={'private/catalog.json':catalogueSha256};
  const releaseHash=createHash('sha256').update('private/catalog.json\0'+catalogueSha256+'\0').digest('hex');
  const prefix=`artifacts/price-history/${releaseHash}`;
  await mkdir(path.join(root,prefix),{recursive:true});
  await writeFile(path.join(root,prefix,'catalog.json'),bytes);
  await writeFile(path.join(root,prefix,'release.json'),JSON.stringify({releaseHash,files}));
  const snapshot={...structuredClone(history.snapshots[0]),releaseHash,catalogueSha256,cataloguePath:prefix+'/catalog.json',publicationPath:prefix+'/publication.json'};
  const observation=JSON.stringify({passed:true,sourceOverride:false,phase:'live',origin:history.origin,releaseHash,at:snapshot.at,pricesVerified:1});
  await writeFile(path.join(root,prefix,'observation.json'),observation);
  const receipt={origin:history.origin,releaseHash,catalogueSha256,firstVerifiedAt:snapshot.at,observedAt:snapshot.observedAt,observationSha256:createHash('sha256').update(observation).digest('hex')};
  await writeFile(path.join(root,snapshot.publicationPath),JSON.stringify(receipt));
  const h={...history,snapshots:[snapshot]};
  await verifyStoreHistoryEvidence(root,h);
  snapshot.products[0].priceMinor*=2;
  await assert.rejects(verifyStoreHistoryEvidence(root,h),/history/i);
  snapshot.products[0].priceMinor=product.salePriceMinor;
  await verifyStoreHistoryEvidence(root,h);
  snapshot.at='2026-10-01T00:00:00Z';receipt.firstVerifiedAt=snapshot.at;
  await writeFile(path.join(root,snapshot.publicationPath),JSON.stringify(receipt));
  await assert.rejects(verifyStoreHistoryEvidence(root,h),/history/i);
  await assert.rejects(verifyStoreHistoryEvidence(root,{...h,firstPricedVerifiedAt:snapshot.at}),/history/i);
  snapshot.at=history.snapshots[0].at;receipt.firstVerifiedAt=snapshot.at;
  await writeFile(path.join(root,snapshot.publicationPath),JSON.stringify(receipt));
  await verifyStoreHistoryEvidence(root,h);
  await writeFile(path.join(root,prefix,'catalog.json'),JSON.stringify({products:[{...product,salePriceMinor:product.salePriceMinor*2}]}));
  await assert.rejects(verifyStoreHistoryEvidence(root,h),/history/i);
 }finally{
  assert.equal(path.dirname(root),path.resolve(os.tmpdir()));assert.ok(path.basename(root).startsWith('nodeno-history-'));
  await rm(root,{recursive:true,force:true});
 }
});

test('whole-percent labels cannot turn an arbitrary 9.5 or 5.6 percent reduction into a larger claim',()=>{
 const h=structuredClone(history);h.snapshots[0].products[0].priceMinor=10000;
 assert.equal(run(policy,h,{...product,salePriceMinor:9050,salePrice:90.5}).discountPercent,9);
 assert.equal(run(policy,h,{...product,salePriceMinor:9440,salePrice:94.4}).discountPercent,5);
});
