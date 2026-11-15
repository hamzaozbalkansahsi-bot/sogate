export function applyFurnitureSets(catalog,mapping,hashes){
 const fail=()=>{throw new Error('Furniture set evidence mismatch');};
 if(mapping?.schema!==1||!Array.isArray(mapping.sets)||['sourceCatalogSha256','identitiesSha256','pdfSha256'].some(key=>!hashes?.[key]||mapping[key]!==hashes[key]))fail();
 const products=new Map(catalog.products.map(p=>[p.id,p])),ids=new Set(),sets=[];
 for(const set of mapping.sets){if(!/^[a-z0-9-]+$/.test(set.id)||ids.has(set.id)||!set.members?.length||['tr','en','ru','ar'].some(l=>typeof set.title?.[l]!=='string'||!set.title[l]||/[<>\x00-\x1f]/.test(set.title[l])))fail();ids.add(set.id);const members=[],seen=new Set();
  for(const member of set.members){const p=products.get(member.productId);if(!p||p.code.toLowerCase()!==member.code.toLowerCase()||seen.has(p.id)||!member.pages?.every(n=>Number.isInteger(n)&&n>=1&&n<=86))fail();seen.add(p.id);members.push({productId:p.id,kind:member.kind});}
  sets.push({id:set.id,title:set.title,room:set.room,members});
 }
 for(const p of catalog.products)p.saleUnit='piece';
 for(const fixed of mapping.fixedSetProducts){const p=products.get(fixed.productId);if(!p||p.code!=='Ndn-'+fixed.sourceCode)fail();p.saleUnit='set';}
 catalog.furnitureSets=sets;catalog.meta.furnitureSetCount=sets.length;
}
