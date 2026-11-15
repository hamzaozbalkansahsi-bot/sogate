import {createHash} from 'node:crypto';
import {readFile,lstat,realpath} from 'node:fs/promises';
import path from 'node:path';

const fail=()=>{throw new Error('Invalid or unverified supplier pricing; publication stopped.');};
const integer=value=>Number.isSafeInteger(value)&&value>0&&value<100_000_000_000;
export function markedUpMinor(sourceMinor){
 if(!integer(sourceMinor))fail();
 const result=Number((BigInt(sourceMinor)*130n+50n)/100n);
 if(!integer(result))fail();return result;
}
function officialUrl(value){try{const u=new URL(value);return u.protocol==='https:'&&u.hostname==='www.adoremobilya.com'&&!u.username&&!u.password&&!u.port&&!u.hash;}catch{return false;}}

export function applyCatalogPrices(catalog,source,pricing,{now=Date.now()}={}){
 if(pricing?.schema!==1||pricing.supplier!=='https://www.adoremobilya.com'||pricing.currency!=='TRY'||pricing.pricingRule?.multiplier!=='1.30'||pricing.pricingRule.rounding!=='ROUND_HALF_UP'||pricing.pricingRule.minorUnit!==100||pricing.pricingRule.conditionalPaymentDiscountsExcluded!==true||!Array.isArray(pricing.products))fail();
 const original=new Map(source.products.map(p=>[String(p.id),p])),records=new Map();
 for(const entry of pricing.products){
  if(!original.has(entry.productId)||records.has(entry.productId)||entry.sourceCode!==original.get(entry.productId).code)fail();
  if(entry.status==='verified'){
   const age=now-Date.parse(entry.fetchedAt);
   if(!Number.isFinite(age)||age< -600_000||age>86_400_000||!officialUrl(entry.sourceUrl)||!officialUrl(entry.finalUrl)||entry.matchedSku!==entry.sourceCode||entry.matchedProductId!==entry.productId||entry.currency!=='TRY'||entry.displayPriceVerified!==true||!/^[a-f0-9]{64}$/.test(entry.sourceDocumentSha256)||markedUpMinor(entry.sourcePriceMinor)!==entry.salePriceMinor)fail();
  }else if(entry.status!=='unavailable')fail();
  records.set(entry.productId,entry);
 }
 if(records.size!==original.size)fail();
 let verified=0;
 for(const product of catalog.products){
  const entry=records.get(product.id);
  if(!entry)fail();
  product.salePrice=null;product.salePriceMinor=null;
  delete product.currency;delete product.priceUpdatedAt;
  if(entry.status==='verified'){
   product.salePriceMinor=entry.salePriceMinor;product.salePrice=entry.salePriceMinor/100;
   product.currency='TRY';product.priceUpdatedAt=entry.fetchedAt;verified++;
  }
 }
 catalog.meta.pricing={currency:'TRY',pricedProducts:verified,unpricedProducts:catalog.products.length-verified};
 if(Number.isFinite(Date.parse(pricing.generatedAt)))catalog.meta.priceRefresh={effectiveAt:Math.floor(Date.parse(pricing.generatedAt)/1000),productIds:[...original.keys()]};
 return catalog;
}

export async function verifyPriceEvidence(root,pricing){
 const allowed=path.resolve(root,'artifacts/catalog-expansion/price-pages');
 for(const entry of pricing.products){
  if(entry.status!=='verified')continue;
  if(typeof entry.sourceDocumentFile!=='string'||!/^artifacts\/catalog-expansion\/price-pages\/[a-f0-9]+\.html$/.test(entry.sourceDocumentFile))fail();
  const filename=path.resolve(root,entry.sourceDocumentFile);
  if((await lstat(filename)).isSymbolicLink()||!((await realpath(filename)).startsWith((await realpath(allowed))+path.sep)))fail();
  const body=await readFile(filename);
  if(createHash('sha256').update(body).digest('hex')!==entry.sourceDocumentSha256)fail();
  const nodes=[];
  const collect=value=>{if(Array.isArray(value))value.forEach(collect);else if(value&&typeof value==='object'){nodes.push(value);if(value['@graph'])collect(value['@graph']);}};
  for(const match of body.toString('utf8').matchAll(/<script\b[^>]*\btype\s*=\s*(["'])application\/ld\+json\1[^>]*>([\s\S]*?)<\/script\s*>/gi)){
   try{collect(JSON.parse(match[2]));}catch{fail();}
  }
  const products=nodes.filter(value=>(Array.isArray(value['@type'])?value['@type']:[value['@type']]).includes('Product')&&value.sku===entry.sourceCode&&String(value.productID)===entry.productId);
  if(products.length!==1)fail();
  const offers=Array.isArray(products[0].offers)?products[0].offers:[products[0].offers];
  if(offers.length!==1||offers[0]?.priceCurrency!=='TRY')fail();
  const offer=offers[0],amount=String(offer.price);
  if(!/^\d+(?:\.\d{1,2})?$/.test(amount))fail();
  const [whole,fraction='']=amount.split('.');
  const minor=Number(BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0')));
  if(!integer(minor)||minor!==entry.sourcePriceMinor||offer.priceValidUntil!==entry.priceValidUntil)fail();
 }
}
