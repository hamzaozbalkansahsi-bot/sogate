import {readFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export function supplierBoundPrice(p,binding){
 if(!binding)throw new Error('supplier_price_binding_missing');
 const percent=binding.markupPercent??20;
 if(![20,30].includes(percent)||(percent===30&&(!/^paint-ty-[0-9]+$/.test(p.id)||binding.platform!=='trendyol'||!/^https:\/\/www\.trendyol\.com\/[^?#]+-p-[0-9]+\?merchantId=[0-9]+$/.test(binding.sourceUrl||''))))throw new Error('supplier_markup_not_approved');
 if(binding.sourcePriceMinor===null)return null;
 if(!Number.isSafeInteger(binding.sourcePriceMinor)||binding.sourcePriceMinor<=0)throw new Error('supplier_source_price_invalid');
 return Math.floor((binding.sourcePriceMinor*(100+percent)+50)/100);
}
export async function loadSupplierCatalog(root){
 let bytes;try{bytes=await readFile(path.join(root,'data/supplier-storefront.json'));}catch(error){if(error.code==='ENOENT')throw new Error('Published supplier catalogue projection is required before a production build.');throw error;}
 const data=JSON.parse(bytes);
 if(data.schema!==1||data.publicationReady!==true||data.testOnly||!data.products?.length||!data.review?.contactSheetsInspected)throw new Error('supplier_publication_review_required');
 for(const proof of data.review.files){if(sha(await readFile(path.join(root,proof.path)))!==proof.sha256)throw new Error('supplier_review_changed');}
 const mediaBytes=await readFile(path.join(root,'data/supplier-media-approved.json')),media=JSON.parse(mediaBytes),indexBytes=await readFile(path.join(root,'data/supplier-details.json')),index=JSON.parse(indexBytes),blob=await readFile(path.join(root,'data/supplier-details.bin'));
 if(!media.publicationReady||media.testOnly||data.mediaSha256!==sha(mediaBytes)||data.detailIndexSha256!==sha(indexBytes)||data.detailBlobSha256!==sha(blob))throw new Error('supplier_private_data_changed');
 for(const [url,row]of Object.entries(media.images)){
  if(!/^\/assets\/suppliers\/[a-f0-9]{64}\.(jpg|png|webp)$/.test(url)||!row.visualReview||!url.includes(row.outputSha256))throw new Error('supplier_media_not_approved');
  const file=path.join(root,'web',url);if((await lstat(file)).isSymbolicLink()||sha(await readFile(file))!==row.outputSha256)throw new Error('supplier_asset_hash_changed');
 }
 const detailAssets={};const ids=new Set(),codes=new Set(),references={};
 for(const p of data.products){
  if(p.productType!=='supplier-item'||ids.has(p.id)||codes.has(p.code)||!p.code.startsWith('ND-')||['tr','en','ru','ar'].some(l=>!p.name[l]||!p.description[l]))throw new Error('supplier_product_invalid');ids.add(p.id);codes.add(p.code);
  const q=p.quantityPolicy;if(!q||!Number.isSafeInteger(q.minimum)||!Number.isSafeInteger(q.step)||q.minimum<1||q.minimum>99||q.step<1)throw new Error('supplier_unit_invalid');
  const binding=data.priceBindings[p.id];if(p.salePriceMinor!==supplierBoundPrice(p,binding))throw new Error('supplier_price_binding_changed');
  for(const [i,url]of p.images.entries()){if(!media.images[url])throw new Error('supplier_image_unreviewed');references[p.id+':'+i]=url;}
  const entry=index.products[p.id];if(!entry||entry.bytes>262144||entry.offset<0||entry.offset+entry.bytes>blob.length)throw new Error('supplier_description_invalid');
  const body=blob.subarray(entry.offset,entry.offset+entry.bytes);if(sha(body)!==entry.sha256||entry.sha256!==p.supplierDetailsHash)throw new Error('supplier_description_hash_changed');
  const details=JSON.parse(body);if(details.id!==p.id||['tr','en','ru','ar'].some(l=>!details.description[l]))throw new Error('supplier_description_locale_missing');
  detailAssets['/api/supplier-products/'+p.id]={body:JSON.stringify({...details,sha256:entry.sha256}),type:'application/json; charset=utf-8',encoding:'utf8'};
 }
 if(JSON.stringify(references)!==JSON.stringify(media.references))throw new Error('supplier_media_references_changed');
 return{data,version:sha(bytes),detailAssets};
}
export function appendSupplierCatalog(catalog,data,version){
 const ids=new Set(catalog.products.map(p=>p.id)),codes=new Set(catalog.products.map(p=>p.code)),categories=new Set(catalog.categories.map(c=>c.id));
 if(data.products.some(p=>ids.has(p.id)||codes.has(p.code))||data.categories.some(c=>categories.has(c.id)))throw new Error('supplier_catalogue_collision');
 catalog.products.push(...data.products);catalog.categories.push(...data.categories);catalog.meta.supplierCatalogVersion=version;catalog.meta.productCount=catalog.products.length;catalog.meta.categoryCount=catalog.categories.length;return catalog;
}
