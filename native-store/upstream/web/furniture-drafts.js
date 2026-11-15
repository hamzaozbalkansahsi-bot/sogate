const STORAGE_KEY='nodeno.furniture-drafts.v1';
const modes=new Set(['retail','wholesale']);
const validOwner=owner=>typeof owner==='string'&&owner.length>0&&owner.length<=100;

function normalize(catalog,input,prune=false){
 if(!input||!modes.has(input.mode)||!Number.isInteger(input.repeat)||input.repeat<1||input.repeat>(input.mode==='retail'?99:10000)||!Array.isArray(input.components)||input.components.length>100||!Array.isArray(input.variants)||input.variants.length>100)return null;
 const set=catalog.furnitureSets?.find(s=>s.id===input.setId);if(!set)return null;
 const members=new Set(set.members.map(m=>m.productId));
 const products=new Map(catalog.products.filter(p=>members.has(p.id)&&p.hidden!==true&&p.published!==false).map(p=>[p.id,p]));
 const components=[],selectedModels=new Set(),variants=new Map();
 for(const part of input.components){
  if(!part||typeof part.productId!=='string'||!Number.isInteger(part.quantity)||part.quantity<1||part.quantity>99)return null;
  const p=products.get(part.productId);if(!p){if(prune)continue;return null;}
  const model=p.modelId||p.id;if(selectedModels.has(model))return null;selectedModels.add(model);
  components.push({productId:p.id,quantity:part.quantity});
 }
 for(const id of input.variants){
  if(typeof id!=='string')return null;const p=products.get(id);if(!p){if(prune)continue;return null;}
  variants.set(p.modelId||p.id,p.id);
 }
 for(const part of components){const p=products.get(part.productId);variants.set(p.modelId||p.id,p.id);}
 return {setId:set.id,mode:input.mode,repeat:input.repeat,components,variants:[...variants.values()]};
}

/** Tab-scoped product selections only. Never retain contact details, prices or consent. */
export function createFurnitureDraftStore(storage){
 function read(owner){
  const empty={schema:1,owner,entries:[]};
  try{const raw=storage?.getItem(STORAGE_KEY);if(!raw||raw.length>65536)return empty;const value=JSON.parse(raw);return value?.schema===1&&value.owner===owner&&Array.isArray(value.entries)&&value.entries.length<=34?value:empty;}catch{return empty;}
 }
 function write(value){try{if(!storage)return false;storage.setItem(STORAGE_KEY,JSON.stringify(value));return true;}catch{return false;}}
 return {
  load(catalog,setId,mode,owner){
   if(!validOwner(owner)||!modes.has(mode))return null;
   const entry=read(owner).entries.find(e=>e?.setId===setId&&e.mode===mode);if(!entry)return null;const normalized=normalize(catalog,entry,true);return normalized?{...normalized,adjusted:entry.components.length!==normalized.components.length||entry.variants.some(id=>!normalized.variants.includes(id))}:null;
  },
  save(catalog,input){
   if(!validOwner(input?.owner))return false;const entry=normalize(catalog,input);if(!entry)return false;
   const record=read(input.owner);record.entries=record.entries.filter(e=>e?.setId!==entry.setId||e.mode!==entry.mode);record.entries.push(entry);record.entries=record.entries.slice(-34);return write(record);
  },
  clear(setId,mode,owner){
   if(!validOwner(owner)||!modes.has(mode))return;
   const record=read(owner);record.entries=record.entries.filter(e=>e?.setId!==setId||e.mode!==mode);write(record);
  }
 };
}
