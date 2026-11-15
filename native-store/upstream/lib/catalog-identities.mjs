const locales=['tr','en','ru','ar'];
const hash=/^[a-f0-9]{64}$/;
const code=/^Ndn-[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const text=value=>typeof value==='string'&&value.trim()===value&&value.length>0&&!/[\u0000-\u001f\u007f<>]/u.test(value);
const fail=()=>{throw new Error('Invalid catalogue identity mapping or source coverage; review the PDF match before publication.');};

// Identities are a presentation overlay. Supplier IDs, archive and media never
// change, so existing product links, favourites and baskets remain valid.
export function resolveCatalogIdentities(source,mapping) {
 const result=new Map();
 if(mapping===undefined)return result;
 if(mapping?.schema!==1||!hash.test(mapping.sourceCatalogSha256)||!hash.test(mapping.sourcePdf?.sha256)||!text(mapping.sourcePdf?.file)||!Number.isSafeInteger(mapping.sourcePdf?.pages)||mapping.sourcePdf.pages<1||!Array.isArray(mapping.products)||!Array.isArray(mapping.websiteOnly)||!Array.isArray(mapping.pdfOnly)||!mapping.names)fail();
 const originals=new Map((source.products||[]).map(p=>[String(p.id),p]));
 const counts=mapping.counts;
 if(originals.size!==(source.products||[]).length||counts?.source!==originals.size||counts.matched!==mapping.products.length||counts.websiteOnly!==mapping.websiteOnly.length||counts.pdfOnly!==mapping.pdfOnly.length||counts.pdf!==counts.matched+counts.pdfOnly||counts.source!==counts.matched+counts.websiteOnly)fail();
 const codes=new Set();
 for(const entry of mapping.products){
  const original=originals.get(entry.id);
  if(!original||result.has(entry.id)||entry.sourceCode!==original.code||entry.sourceName!==original.title||entry.code!=='Ndn-'+entry.sourceCode||!code.test(entry.code)||codes.has(entry.code)||!text(entry.name)||!Object.hasOwn(mapping.names,entry.name))fail();
  const name=mapping.names[entry.name];
  if(name.tr!==entry.name||locales.some(lang=>!text(name[lang])))fail();
  if(entry.notes&&locales.some(lang=>!text(entry.notes[lang])))fail();
  if([entry.cataloguePage,entry.indexPage].some(page=>!Number.isSafeInteger(page)||page<1||page>mapping.sourcePdf.pages))fail();
  codes.add(entry.code);
  result.set(entry.id,{...entry,name:{...name}});
 }
 const accounted=new Set(result.keys());
 for(const entry of mapping.websiteOnly){
  const original=originals.get(entry.id);
  if(!original||accounted.has(entry.id)||entry.code!==original.code||entry.name!==original.title)fail();
  accounted.add(entry.id);
 }
 if(accounted.size!==originals.size)fail();
 const publicCodes=new Set();
 for(const original of originals.values()){
  const value=result.get(String(original.id))?.code||original.code;
  if(!value||publicCodes.has(value))fail();
  publicCodes.add(value);
 }
 return result;
}
