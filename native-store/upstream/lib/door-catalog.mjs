import {readFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function loadDoorCatalog(root){
 const bytes=await readFile(path.join(root,'data/door-catalog.json')),data=JSON.parse(bytes);
 if(data.schema!==1||data.publicationReady!==true||data.reviewRequired!==false||!data.review?.contactSheetsInspected||data.products.length!==95||!data.assets)throw new Error('door_media_review_required');
 for(const [hash,asset]of Object.entries(data.assets)){
  if(!/^[a-f0-9]{64}$/.test(hash)||asset.sha256!==hash||!/^\/assets\/doors\/[a-f0-9]{64}\.(jpg|png|webp)$/.test(asset.path)||asset.unchangedEmbeddedImage!==true)throw new Error('door_asset_identity_invalid');
  const file=path.join(root,'web',asset.path);if((await lstat(file)).isSymbolicLink()||sha(await readFile(file))!==hash)throw new Error('door_asset_hash_changed');
 }
 const ids=new Set();for(const p of data.products){if(ids.has(p.id)||!/^door-[a-z0-9-]+$/.test(p.id)||!p.assetHashes.length||p.assetHashes.some(h=>!data.assets[h])||['tr','en','ru','ar'].some(lang=>!p.name[lang]||!p.description[lang]))throw new Error('door_product_invalid');ids.add(p.id);}
 return {data,version:sha(bytes)};
}
export function appendDoorCatalog(catalog,data,version){
 const existing=new Set(catalog.products.map(p=>p.id));if(data.products.some(p=>existing.has(p.id)))throw new Error('door_product_collision');
 const products=data.products.map(p=>{const {sourceEvidence,sourcePrice,assetHashes,...visible}=p;return visible;});
 catalog.products.push(...products);catalog.categories.unshift(...data.categories);
 catalog.meta.productCount=catalog.products.length;catalog.meta.categoryCount=catalog.categories.length;catalog.meta.modelCount=new Set(catalog.products.map(p=>p.modelId||p.id)).size;
 catalog.meta.doorCatalogVersion=version;catalog.doorPolicy=data.policy;catalog.specialDoors=data.specialDoors;
 return applyDoorMeasurementPolicy(catalog);
}
// The original PDF manifest remains immutable. This explicit owner correction
// is applied only to the customer catalogue, including crawlable descriptions.
export function applyDoorMeasurementPolicy(catalog){
 catalog.products=catalog.products.map(p=>p.productType!=='door'?p:{...p,door:{...p.door,...(p.door?.baseFrameDepthMaxCm===15?{baseFrameDepthMaxCm:17}:{})},description:Object.fromEntries(Object.entries(p.description||{}).map(([locale,text])=>[locale,text.replace(/\b15 (cm|см|سم)/gu,'17 $1')]))});
 catalog.doorPolicy={...catalog.doorPolicy,frameWidthsMm:[95,115,145,165,185,215],leafWidthsMm:[770,870],standardFrameWidthMaxMm:170};
 catalog.meta={...catalog.meta,measurementPolicyVersion:'2026-11-10-owner-170mm'};return catalog;
}
