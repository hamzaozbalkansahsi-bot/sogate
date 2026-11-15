import {createHash} from 'node:crypto';
import {readFile,lstat,realpath} from 'node:fs/promises';
import path from 'node:path';
const fail=()=>{throw new Error('Invalid own-store price history or discount policy.');};
const positive=value=>Number.isSafeInteger(value)&&value>0;
const time=value=>typeof value==='string'?Date.parse(value):NaN;

export function applyStoreDiscounts(catalog,history,policy,{now=Date.now()}={}){
 if(history?.schema!==1||history.origin!=='https://nodenohome.com'||history.currency!=='TRY'||!Array.isArray(history.snapshots)||!history.snapshots.length||policy?.schema!==1||!['preserve','percentage'].includes(policy.mode))fail();
 const launched=time(history.firstPricedVerifiedAt);
 if(!Number.isFinite(launched)||launched>now)fail();
 const anchor=policy.mode==='percentage'?time(policy.effectiveAt):now;
 if(!Number.isFinite(anchor)||anchor>now||policy.mode==='percentage'&&(!Number.isInteger(policy.percent)||policy.percent<1||policy.percent>99))fail();
 let last=-Infinity;
 const snapshots=history.snapshots.map(snapshot=>{
  const at=time(snapshot.at),observed=time(snapshot.observedAt),prices=new Map();
  if(!Number.isFinite(at)||at<launched||last===-Infinity&&at!==launched||at<=last||at>now||!Number.isFinite(observed)||observed<at||observed>now||!Array.isArray(snapshot.products))fail();last=at;
  for(const row of snapshot.products){
   if(typeof row.id!=='string'||prices.has(row.id)||typeof row.code!=='string'||row.currency!=='TRY'||row.priceMinor!==null&&!positive(row.priceMinor))fail();
   prices.set(row.id,row);
  }
  return{at,prices};
 }).filter(snapshot=>snapshot.at<anchor);
 const cutoff=anchor-10*86400000;
 const carry=snapshots.findLast(snapshot=>snapshot.at<=cutoff);
 const window=snapshots.filter(snapshot=>snapshot.at>cutoff);
 if(carry)window.unshift(carry);
 let discounted=0;
 for(const p of catalog.products){
  delete p.previousPriceMinor;delete p.discountPercent;
  if(p.currency!=='TRY'||!positive(p.salePriceMinor))continue;
  if(policy.mode==='percentage'){
   const amount=Number((BigInt(p.salePriceMinor)*BigInt(100-policy.percent)+50n)/100n);
   if(!positive(amount))fail();p.salePriceMinor=amount;p.salePrice=amount/100;
  }
  const values=window.map(snapshot=>snapshot.prices.get(p.id)).filter(row=>row&&row.code===p.code&&positive(row.priceMinor)).map(row=>row.priceMinor);
  if(!values.length)continue;
  const previous=Math.min(...values);
  if(previous<=p.salePriceMinor)continue;
  p.previousPriceMinor=previous;
  const numerator=BigInt(previous-p.salePriceMinor)*100n,denominator=BigInt(previous);
  let rate=numerator/denominator;
  // Allow only the half-kurus rounding needed by an actual whole-percent cut.
  if(numerator%denominator!==0n&&(rate+1n)*denominator-numerator<=50n)rate++;
  p.discountPercent=Math.min(99,Number(rate));
  discounted++;
 }
 if(catalog.meta?.pricing)catalog.meta.pricing.discountedProducts=discounted;
 return catalog;
}

export async function verifyStoreHistoryEvidence(root,history){
 const hash=body=>createHash('sha256').update(body).digest('hex');
 const launched=time(history.firstPricedVerifiedAt),now=Date.now();let last=-Infinity;
 if(!Number.isFinite(launched)||launched>now)fail();
 for(const snapshot of history.snapshots){
  const at=time(snapshot.at),observed=time(snapshot.observedAt);
  if(!Number.isFinite(at)||at<launched||last===-Infinity&&at!==launched||at<=last||!Number.isFinite(observed)||observed<at||observed>now)fail();last=at;
  if(!/^[a-f0-9]{64}$/.test(snapshot.releaseHash)||snapshot.cataloguePath!==`artifacts/price-history/${snapshot.releaseHash}/catalog.json`||snapshot.publicationPath!==`artifacts/price-history/${snapshot.releaseHash}/publication.json`)fail();
  const allowed=await realpath(path.join(root,'artifacts/price-history'));
  const read=async relative=>{const file=path.resolve(root,relative);if((await lstat(file)).isSymbolicLink()||!(await realpath(file)).startsWith(allowed+path.sep))fail();return readFile(file);};
  const bytes=await read(snapshot.cataloguePath),receipt=JSON.parse(await read(snapshot.publicationPath));
  const observationBytes=await read(`artifacts/price-history/${snapshot.releaseHash}/observation.json`),observation=JSON.parse(observationBytes);
  if(hash(observationBytes)!==receipt.observationSha256||observation.passed!==true||observation.sourceOverride!==false||observation.phase!=='live'||observation.origin!==history.origin||observation.releaseHash!==snapshot.releaseHash||observation.at!==snapshot.at||observation.pricesVerified!==snapshot.products.length||receipt.observedAt!==snapshot.observedAt)fail();
  const manifest=JSON.parse(await read(`artifacts/price-history/${snapshot.releaseHash}/release.json`));
  const fingerprint=createHash('sha256');
  for(const name of Object.keys(manifest.files).sort())fingerprint.update(name+'\0'+manifest.files[name]+'\0');
  if(hash(bytes)!==snapshot.catalogueSha256||manifest.files['private/catalog.json']!==snapshot.catalogueSha256||fingerprint.digest('hex')!==snapshot.releaseHash||receipt.origin!==history.origin||receipt.releaseHash!==snapshot.releaseHash||receipt.catalogueSha256!==snapshot.catalogueSha256||receipt.firstVerifiedAt!==snapshot.at)fail();
  const products=JSON.parse(bytes).products;
  if(products.length!==snapshot.products.length)fail();
  const actual=new Map(products.map(p=>[p.id,p]));
  for(const row of snapshot.products){const p=actual.get(row.id);if(!p||p.code!==row.code||p.salePriceMinor!==row.priceMinor||p.currency!==row.currency)fail();}
 }
}
