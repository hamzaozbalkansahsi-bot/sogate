import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {normalizeCatalog} from './catalog.mjs';
import {applyCatalogPrices,verifyPriceEvidence} from './catalog-pricing.mjs';
import {applyStoreDiscounts,verifyStoreHistoryEvidence} from './store-discounts.mjs';
import {applyProductModels} from './product-models.mjs';
import {applyFurnitureSets} from './furniture-sets.mjs';
import {loadMediaApprovals} from './media-approvals.mjs';
import {loadDoorCatalog,appendDoorCatalog} from './door-catalog.mjs';
import {loadFrontCatalog,appendFrontCatalog} from './cabinet-fronts.mjs';
import {loadSupplierCatalog,appendSupplierCatalog} from './supplier-catalog.mjs';

const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const jsonShape=value=>JSON.parse(JSON.stringify(value));

// Use the reviewed source contracts for every catalogue family. The legacy
// supplier price list is not the price or identity authority for doors/fronts
// or the independently reviewed wood-products projection.
export async function loadArtifactExpectations(root){
 const read=name=>readFile(path.join(root,'data',name));
 const sourceBytes=await read('catalog-source.json'),source=JSON.parse(sourceBytes);
 const identityBytes=await read('catalog-identities.json'),identities=JSON.parse(identityBytes);
 assert.equal(digest(sourceBytes),identities.sourceCatalogSha256,'Catalogue identity source changed');
 const {catalog,media,report}=normalizeCatalog(source,{identities});
 const pricing=JSON.parse(await read('catalog-prices.json'));
 applyCatalogPrices(catalog,source,pricing);await verifyPriceEvidence(root,pricing);
 const history=JSON.parse(await read('price-history.json')),policy=JSON.parse(await read('discount-policy.json'));
 await verifyStoreHistoryEvidence(root,history);applyStoreDiscounts(catalog,history,policy);
 applyProductModels(catalog,source,JSON.parse(await read('product-models.json')),{sourceCatalogSha256:digest(sourceBytes),identitiesSha256:digest(identityBytes)});
 const setBytes=await read('furniture-sets.json'),sets=JSON.parse(setBytes);
 applyFurnitureSets(catalog,sets,{sourceCatalogSha256:digest(sourceBytes),identitiesSha256:digest(identityBytes),pdfSha256:digest(await readFile(path.join(root,sets.sourcePdf)))});
 catalog.meta.furnitureSetsVersion=digest(setBytes);
 const brand=JSON.parse(await read('brand.json'));catalog.brand={...catalog.brand,name:brand.name,slogan:brand.slogan,domain:brand.domain};
 assert.ok(catalog.products.length,'No verified products');assert.ok(!Object.values(report.translationPending).some(Boolean),'Technical translations incomplete');
 const approved=await loadMediaApprovals({root,media});assert.notEqual(approved.testOnly,true,'Test media cannot validate production');catalog.meta.mediaVersion=approved.mediaVersion;
 const doors=await loadDoorCatalog(root),fronts=await loadFrontCatalog(root),suppliers=await loadSupplierCatalog(root);
 appendDoorCatalog(catalog,doors.data,doors.version);appendFrontCatalog(catalog,fronts.data,fronts.version);appendSupplierCatalog(catalog,suppliers.data,suppliers.version);
 return jsonShape(catalog);
}

export function assertArtifactCatalog(actual,reviewed){
 assert.ok(actual&&reviewed&&Array.isArray(actual.products)&&Array.isArray(reviewed.products),'Catalogue required');
 assert.ok(reviewed.products.length,'Reviewed products required');
 assert.match(actual.meta?.releaseHash??'',/^[a-f0-9]{64}$/,'Invalid artifact fingerprint');
 assert.ok(actual.meta.testOnly===undefined||actual.meta.testOnly===false,'Test catalogue cannot validate production');
 const ids=new Set();
 for(const p of actual.products){assert.ok(typeof p.id==='string'&&!ids.has(p.id),'Missing or duplicate product ID');assert.ok(typeof p.code==='string'&&p.code.trim(),'Missing product code');ids.add(p.id);}
 const expected=jsonShape(reviewed);
 // Exact reviewed records preserve unknown prices, units and the deliberate
 // source-backed no-photo exception. No placeholder or fallback is invented.
 assert.equal(actual.products.length,expected.products.length,'Artifact product count differs from reviewed sources');
 for(const [index,p]of expected.products.entries())assert.deepEqual(actual.products[index],p,'Artifact product differs from reviewed sources: '+p.id);
 assert.deepEqual(actual.categories,expected.categories,'Artifact categories differ from reviewed sources');
 assert.deepEqual(actual.brand,expected.brand,'Artifact brand differs from canonical brand');
 for(const key of ['mediaVersion','doorCatalogVersion','frontCatalogVersion','supplierCatalogVersion','furnitureSetsVersion','measurementPolicyVersion'])assert.equal(actual.meta[key],expected.meta[key],'Artifact publication proof differs: '+key);
 for(const key of ['furnitureSets','doorPolicy','frontPolicy','specialDoors'])assert.deepEqual(actual[key],expected[key],'Artifact catalogue policy differs: '+key);
 return {products:actual.products.length,categories:actual.categories.length,approvedNoPhotoProducts:actual.products.filter(p=>p.images?.length===0).length};
}
