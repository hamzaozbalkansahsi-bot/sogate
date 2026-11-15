/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/variants.js
 * Açıklama   : Seçilen beden ve rengi doğrular, sepet satırlarını seçimlerine göre ayırır.
 */
export const requiresSelection=p=>p?.variantSelection?.required===true;
export function selectionLine(product,item){
 const schema=product?.variantSelection,choices=item?.options?.selection;
 if(!requiresSelection(product)||!schema.axes?.length||schema.blocked||!choices||typeof choices!=='object'||Array.isArray(choices))throw Error('variant_selection_required');
 if(item.id!==product.id||!Number.isInteger(item.quantity)||item.quantity<1||item.quantity>99||Object.keys(item).some(k=>!['id','quantity','key','options'].includes(k))||Object.keys(item.options).some(k=>k!=='selection')||Object.keys(choices).length!==schema.axes.length)throw Error('variant_selection_invalid');
 const selection={};
 for(const axis of schema.axes){if(typeof choices[axis.id]!=='string'||!axis.values.some(v=>v.id===choices[axis.id]))throw Error('variant_selection_invalid');selection[axis.id]=choices[axis.id];}
 if(schema.mode==='matrix'&&!schema.variants.some(v=>v.active&&schema.axes.every(a=>v.values[a.id]===selection[a.id])))throw Error('variant_combination_unavailable');
 const key=product.id+'~'+schema.axes.map(a=>selection[a.id]).join('.');
 if(item.key!==undefined&&item.key!==key)throw Error('variant_key_invalid');
 return{id:product.id,quantity:item.quantity,key,options:{selection}};
}
export function selectionDescription(product,item,locale='tr',copy={}){
 try{const clean=selectionLine(product,item);return product.variantSelection.axes.map(a=>(copy[a.id]||a.label)+': '+a.values.find(v=>v.id===clean.options.selection[a.id]).label).join(' · ');}catch{return copy.required||(locale==='tr'?'Beden ve renk seçin':'Choose product options');}
}
export function normalizeSelectionCart(value,products,legacy){
 if(!Array.isArray(value))return[];const known=new Map(products.map(p=>[p.id,p])),merged=new Map();
 for(const row of value){const product=known.get(row?.id);if(!requiresSelection(product)){for(const line of legacy([row],products)){const key=line.key||line.id,old=merged.get(key);merged.set(key,old?legacy([old,line],products)[0]:line);}continue;}
  if(!Number.isInteger(row?.quantity)||row.quantity<1||row.quantity>99)continue;
  let line;try{line=selectionLine(product,row);}catch{line={id:product.id,quantity:row.quantity,pendingSelection:true};}
  const key=line.key||line.id,old=merged.get(key);merged.set(key,{...line,quantity:Math.min(99,line.quantity+(old?.quantity||0))});
 }return [...merged.values()];
}
export function mergeSelectionLine(cart,line,replaceKey=null){
 const rows=cart.filter(row=>(row.key||row.id)!==replaceKey).map(row=>({...row})),existing=rows.find(row=>(row.key||row.id)===line.key);
 if(existing){if(existing.quantity+line.quantity>99)throw Error('variant_quantity_limit');existing.quantity+=line.quantity;}else{if(rows.length>=100)throw Error('cart_limit');rows.push(line);}return rows;
}
export async function selectCartItems(ids,add,allowed=()=>true){
 let added=0;for(const id of [...new Set(ids)]){if(!allowed()||await add(id)!==true)return{added,complete:false};added++;}return{added,complete:true};
}
