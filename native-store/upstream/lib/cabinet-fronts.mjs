import {readFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function loadFrontCatalog(root){
 const bytes=await readFile(path.join(root,'data/cabinet-fronts.json')),data=JSON.parse(bytes);
 if(data.schema!==1||data.publicationReady!==true||data.reviewRequired!==false||!data.review?.contactSheetsInspected||!data.review?.ocrInspected||!data.products.length)throw new Error('front_media_review_required');
 for(const [hash,a]of Object.entries(data.assets)){
  if(!/^[a-f0-9]{64}$/.test(hash)||a.sha256!==hash||!/^\/assets\/fronts\/[a-f0-9]{64}\.png$/.test(a.path)||!a.nativePdfProductRegion||a.reviewRequired!==false)throw new Error('front_asset_identity_invalid');
  const file=path.join(root,'web',a.path);if((await lstat(file)).isSymbolicLink()||sha(await readFile(file))!==hash)throw new Error('front_asset_hash_changed');
 }
 const ids=new Set(),types=new Map();for(const p of data.products){if(ids.has(p.id)||!/^front-[a-f0-9]{16}$/.test(p.id)||!p.assetHashes.length||p.assetHashes.some(h=>!data.assets[h])||['tr','en','ru','ar'].some(lang=>!p.name[lang]||!p.description[lang]))throw new Error('front_product_invalid');if(types.has(p.modelId)&&types.get(p.modelId)!==p.productType)throw new Error('front_accessory_model_collision');types.set(p.modelId,p.productType);ids.add(p.id);}
 return {data,version:sha(bytes)};
}
export function appendFrontCatalog(catalog,data,version){
 const ids=new Set(catalog.products.map(p=>p.id));if(data.products.some(p=>ids.has(p.id)))throw new Error('front_product_collision');
 catalog.products.push(...data.products.map(p=>{const {sourceEvidence,sourceCode,assetHashes,...publicProduct}=p;const {supplierFreightIncluded,...front}=publicProduct.front;return {...publicProduct,front};}));
 catalog.categories.unshift(...data.categories);catalog.meta.productCount=catalog.products.length;catalog.meta.categoryCount=catalog.categories.length;
 catalog.meta.modelCount=new Set(catalog.products.map(p=>p.modelId||p.id)).size;catalog.meta.frontCatalogVersion=version;
 const {supplierFreightIncluded,...policy}=data.policy;catalog.frontPolicy=policy;return catalog;
}
