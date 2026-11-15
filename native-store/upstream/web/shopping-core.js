import {localized} from './i18n.js?v=storefront-recovery-20261112-r1';
import {numericDimensions,summarizeSpecs,groupSpecs} from './product-specs.js?v=storefront-recovery-20261112-r1';
import {unitPriceMinor,formatMoney} from './shop-core.js?v=storefront-recovery-20261112-r1';
import {cartLineKey} from './door-core.js?v=storefront-recovery-20261112-r1';

export function parseSpaceMeasure(value){if(typeof value!=='string'||!/^\d{1,5}(?:[.,]\d{1,2})?$/.test(value.trim()))return null;const number=Number(value.trim().replace(',','.'));return number>0&&number<=10000?number:null;}
export function fitAssessment(product,space){
 const dimensions=numericDimensions(product?.specs),axes=['width','height','depth'].map(axis=>{const bounds=dimensions[axis],available=space?.[axis];return{axis,bounds,available,status:!bounds||!Number.isFinite(available)||available<=0?'unknown':available<bounds.min?'tooLarge':available>=bounds.max?'fits':'check'};});
 return{status:['tooLarge','unknown','check','fits'].find(status=>axes.some(axis=>axis.status===status)),axes};
}
export function comparisonIds(value,products){const known=new Set(products.map(p=>p.id)),input=Array.isArray(value)?value:typeof value==='string'?value.slice(0,1024).split(','):[];return[...new Set(input.filter(id=>typeof id==='string'&&known.has(id)))].slice(0,4);}
export function comparisonRows(products,locale='tr'){
 const facts=products.map(p=>summarizeSpecs(p.specs,locale)),groups=products.map(p=>groupSpecs(p.specs));
 const definitions=[['price','unitPrice',p=>unitPriceMinor(p)===null?null:formatMoney(unitPriceMinor(p),locale)],['code','code',p=>p.code||null],['color','productColor',p=>p.colorReviewPending?null:localized(p.variantColor,locale)||null],...['width','height','depth'].map(axis=>[axis,'dimension'+axis[0].toUpperCase()+axis.slice(1),(p,i)=>facts[i].find(f=>f.key===axis)?.value||null]),['material','productMaterial',(p,i)=>groups[i].materials.map(row=>localized(row.spec.value,locale)).filter(Boolean).join('\n')||null],['scope','productScope',p=>localized(p.scopeNote,locale)||null],['features','specGroupFeatures',(p,i)=>groups[i].features.map(row=>localized(row.spec.value,locale)).filter(Boolean).join('\n')||null]];
 return definitions.map(([key,labelKey,get])=>{const values=products.map(get);return{key,labelKey,values,different:new Set(values.map(value=>value?.trim().replace(/\s+/gu,' ')??'')).size>1};});
}
function canonicalCart(cart,products){const known=new Map(products.map(p=>[p.id,p])),seen=new Set();if(!Array.isArray(cart)||cart.length>100)throw new Error('cart_limit');for(const line of cart){const key=cartLineKey(line);if(!known.has(line.id)||seen.has(key)||!Number.isInteger(line.quantity)||line.quantity<1||line.quantity>(['door','cabinet-front'].includes(known.get(line.id).productType)?10000:99))throw new Error('invalid_cart');seen.add(key);}return cart.map(line=>({...line}));}
export function replaceCartVariant(cart,sourceId,targetId,products,selected=new Set()){
 const next=canonicalCart(cart,products),source=products.find(p=>p.id===sourceId),target=products.find(p=>p.id===targetId),line=next.find(item=>item.id===sourceId);if(!source||!target||!line||sourceId!==targetId&&(!source.modelId||source.modelId!==target.modelId))throw new Error('invalid_variant');
 if(sourceId===targetId)return{cart:next,selected:new Set(selected)};
 const existing=next.find(item=>item.id===targetId),quantity=line.quantity+(existing?.quantity||0);if(quantity>99)throw new Error('quantity_limit');
 const output=next.filter(item=>item.id!==sourceId&&item.id!==targetId),index=Math.min(next.findIndex(item=>item.id===sourceId),output.length);output.splice(index,0,{id:targetId,quantity});
 const selection=new Set(selected);const chosen=selection.has(sourceId)||selection.has(targetId);selection.delete(sourceId);if(chosen)selection.add(targetId);return{cart:output,selected:selection};
}
export function favoritesToCart(cart,ids,products){const result=canonicalCart(cart,products),known=new Set(products.map(p=>p.id)),present=new Set(result.map(line=>line.id));for(const id of new Set(ids)){if(!known.has(id))throw new Error('invalid_product');if(products.find(p=>p.id===id)?.productType==='cabinet-front')throw new Error('configuration_required');if(!present.has(id)){if(result.length===100)throw new Error('cart_limit');result.push({id,quantity:1});present.add(id);}}return result;}
export const collectionLimits={collections:20,perCollection:100,total:1000};
export function validateCollections(value,products){
 if(!Array.isArray(value)||value.length>collectionLimits.collections)throw new Error('collections_limit');const known=new Set(products.map(p=>p.id)),seen=new Set();let total=0;
 return value.map(row=>{if(!row||typeof row.id!=='string'||!/^[a-f0-9]{32}$/u.test(row.id)||seen.has(row.id)||!Array.isArray(row.items))throw new Error('invalid_collection');seen.add(row.id);const name=typeof row.name==='string'?row.name.trim():'';if(!name||[...name].length>60||/[\u0000-\u001f\u007f]/u.test(name))throw new Error('invalid_collection_name');if(row.items.length>collectionLimits.perCollection)throw new Error('collections_limit');const items=[...new Set(row.items)];if(items.some(id=>typeof id!=='string'||!known.has(id)))throw new Error('invalid_product');total+=items.length;if(total>collectionLimits.total)throw new Error('collections_limit');return{id:row.id,name,items};});
}
export function mergeCollectionLists(target,incoming,products){
 const result=validateCollections(target,products),source=validateCollections(incoming,products);
 for(const row of source){const existing=result.find(item=>item.id===row.id);if(existing)existing.items=[...new Set([...existing.items,...row.items])];else result.push({...row,items:[...row.items]});}
 return validateCollections(result,products);
}
