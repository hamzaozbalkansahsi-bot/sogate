import {unitPriceMinor} from './shop-core.js?v=storefront-recovery-20261112-r1';
import {cartLineKey} from './door-core.js?v=storefront-recovery-20261112-r1';
export function resolveFurnitureSet(catalog,setId,components,multiplier=1){
 const fail=()=>{throw new Error('set_selection_invalid');},definition=catalog.furnitureSets?.find(s=>s.id===setId);
 if(!definition||!Array.isArray(components)||!components.length||components.length>50||!Number.isSafeInteger(multiplier)||multiplier<1||multiplier>10000)fail();
 const allowed=new Set(definition.members.map(m=>m.productId)),byId=new Map(catalog.products.map(p=>[p.id,p])),seen=new Set();let totalQuantity=0,totalMinor=0,priced=true;
 const items=components.map(c=>{const p=byId.get(c.productId);if(!p||p.hidden===true||p.published===false||!allowed.has(p.id)||seen.has(p.id)||!Number.isInteger(c.quantity)||c.quantity<1||c.quantity>99)fail();seen.add(p.id);const quantity=c.quantity*multiplier,unit=unitPriceMinor(p);if(quantity>10000000)fail();totalQuantity+=quantity;if(unit===null)priced=false;else totalMinor+=unit*quantity;return {id:p.id,quantity,perSet:c.quantity,unitPriceMinor:unit,lineTotalMinor:unit===null?null:unit*quantity};}).sort((a,b)=>a.id.localeCompare(b.id));
 if(totalQuantity>10000000||!Number.isSafeInteger(totalMinor))fail();return {setId,title:definition.title,multiplier,items,totalQuantity,totalMinor:priced?totalMinor:null};
}
export function mergeFurnitureSetCart(cart,selection,products){
 const byId=new Map(products.map(p=>[p.id,p])),next=new Map();if(!Array.isArray(cart)||!Array.isArray(selection)||!selection.length)throw new Error('set_selection_invalid');
 for(const row of cart){const key=cartLineKey(row);if(!byId.has(row.id)||!Number.isInteger(row.quantity)||row.quantity<1||row.quantity>(['door','cabinet-front'].includes(byId.get(row.id)?.productType)?10000:99)||next.has(key))throw new Error('cart_limit');next.set(key,{...row});}
 for(const row of selection){const p=byId.get(row.id);if(!p||p.hidden===true||p.published===false||unitPriceMinor(p)===null)throw new Error('set_price_unavailable');const quantity=(next.get(row.id)?.quantity||0)+row.quantity;if(!Number.isInteger(row.quantity)||row.quantity<1||quantity>99||next.size>=100&&!next.has(row.id))throw new Error('cart_limit');next.set(row.id,{id:row.id,quantity});}
 return [...next.values()];
}
