const locales=['tr','en','ru','ar'];
const number='\\d+(?:[.,]\\d+)?(?:\\s*-\\s*\\d+(?:[.,]\\d+)?)?';
const dimensions=new RegExp('(?:'+number+'\\s*[x×]\\s*){2}'+number+'\\s*(?:cm|см|سم)?','gi');
const escape=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const fail=message=>{throw new Error('Invalid product model mapping: '+message);};
export const productColor=p=>p.specs.find(s=>/ren[kg]/iu.test(s.label.tr))?.value;
function dimensionKey(p){return(p.specs.find(s=>/ölç/iu.test(s.label.tr))?.value.tr||'').split('(')[0].match(/\d+(?:[.,]\d+)?/g)?.join('|').replaceAll(',','.')||'';}
function stem(code){const m=code.match(/^(.+)-([^-]+)-(\d+)$/);return m?m[1]+'-v'+m[3]:code.match(/^([A-Z]+\d+)[A-Z]+$/)?.[1]||code;}
function material(title){return/s\.?\s*deri|suni deri/iu.test(title)?'leather':/kumaş/iu.test(title)?'fabric':'';}
function shape(title){return(title.toLocaleLowerCase('tr-TR').match(/\d+\s*(?:kapaklı|çekmeceli|bölmeli|kişilik)/gu)||[]).join('|');}
function shortName(value,colors){
 let s=value.replace(dimensions,'').replace(/\([^)]*(?:GxYxD|GXYXD|W[×x]H[×x]D|Ш[×x]В[×x]Г|العرض[×x]الارتفاع[×x]العمق)[^)]*\)/giu,'').replace(new RegExp('\\b'+number+'\\s*(?:cm|см|سم)\\b','gi'),'');
 const parts=s.split(/\s+[-—]\s*/u);if(parts.length>1&&colors.some(c=>parts.at(-1).toLocaleLowerCase().includes(c.toLocaleLowerCase())))s=parts.slice(0,-1).join(' - ');
 for(const color of [...colors].sort((a,b)=>b.length-a.length))s=s.replace(new RegExp('\\s+'+escape(color)+'\\s*$','iu'),'');
 return s.replace(/\s+/gu,' ').replace(/^[\s\-—.,;]+|[\s\-—.,;]+$/gu,'')||value;
}
export function applyProductModels(catalog,source,mapping,hashes){
 if(mapping?.schema!==1||!hashes||mapping.sourceCatalogSha256!==hashes.sourceCatalogSha256||mapping.identitiesSha256!==hashes.identitiesSha256||!Array.isArray(mapping.models))fail('stale source or identity hash');
 const byId=new Map(catalog.products.map(p=>[p.id,p])),raw=new Map(source.products.map(p=>[String(p.id),p])),seen=new Set(),modelIds=new Set();
 const pendingColors=new Set();for(const item of mapping.colorReview||[]){const r=raw.get(item.id);if(!r||r.code!==item.sourceCode||r.title!==item.sourceTitle||pendingColors.has(item.id))fail('invalid colour review');pendingColors.add(item.id);}
 const colors=Object.fromEntries(locales.map(lang=>[lang,[...new Set(catalog.products.map(p=>productColor(p)?.[lang]).filter(Boolean))]]));
 const pending=[];
 for(const model of mapping.models){
  if(!/^model-[A-Za-z0-9_-]+$/.test(model.id)||modelIds.has(model.id)||!Array.isArray(model.productIds)||!model.productIds.length)fail('duplicate or empty model');modelIds.add(model.id);
  const members=model.productIds.map(id=>{const p=byId.get(id);if(!p||seen.has(id))fail('missing or duplicate variant '+id);seen.add(id);return p;});
  const basis=members.find(p=>p.id===model.evidence?.nameSourceProductId);if(!basis)fail('name reference');
  for(const lang of locales)if(typeof model.name?.[lang]!=='string'||!model.name[lang]||/[<>\u0000-\u001f]/u.test(model.name[lang])||model.name[lang]!==shortName(basis.name[lang],colors[lang]))fail('unverified name '+basis.id+'/'+lang);
  if(members.length>1){
   const first=members[0],firstRaw=raw.get(first.id),labels=new Set(),size=dimensionKey(first);if(!size)fail('missing model dimensions');
   for(const p of members){const r=raw.get(p.id),color=productColor(p),label=color?.tr.toLocaleLowerCase('tr-TR');
    if(!r||!label||labels.has(label)||locales.some(lang=>!color[lang])||stem(r.code)!==model.evidence.sourceStem||dimensionKey(p)!==size||material(r.title)!==material(firstRaw.title)||shape(r.title)!==shape(firstRaw.title)||JSON.stringify(p.scopeNote)!==JSON.stringify(first.scopeNote))fail('incompatible or ambiguous variant '+p.id);
    labels.add(label);
   }
  }
  if(members.length>1&&members.some(p=>pendingColors.has(p.id)))fail('unresolved colour model');
  for(const p of members)pending.push([p,{modelId:model.id,modelName:{...model.name},...(pendingColors.has(p.id)?{colorReviewPending:true}:productColor(p)?{variantColor:{...productColor(p)}}:{})}]);
 }
 if(seen.size!==catalog.products.length)fail('incomplete SKU coverage');
 for(const [p,fields] of pending)Object.assign(p,fields);
 catalog.meta.modelCount=modelIds.size;
}
