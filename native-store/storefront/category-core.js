/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/category-core.js
 * Açıklama   : Katalog filtrelerini gerçek ürün seçenekleri ve aktif varyant birleşimleriyle eşler.
 */
const text=value=>typeof value==='string'?value.normalize('NFC').trim():'';
const key=value=>text(value).toLocaleLowerCase('tr-TR');
export const facetKeys=['brand','color','size','material'];
export function facetValues(product,field){
 if(field==='brand')return text(product.brand)?[text(product.brand)]:[];
 if(field==='material'){
  const material=text(product.facts?.materials);
  return material&&material.length<=60&&!/[.!?:\n]/u.test(material)?[material]:[];
 }
 const schema=product.variantSelection,axis=schema?.axes?.find(a=>a.id===field);
 if(axis){
  const active=schema.mode==='matrix'?new Set(schema.variants.filter(v=>v.active).map(v=>v.values[field])):null;
  return axis.values.filter(v=>!active||active.has(v.id)).map(v=>text(v.label)).filter(Boolean);
 }
 return field==='color'&&!product.colorReviewPending&&text(product.variantColor?.tr)?[text(product.variantColor.tr)]:[];
}
export function matchesFacets(product,selected={}){
 if(facetKeys.some(field=>selected[field]&&!facetValues(product,field).some(value=>key(value)===key(selected[field]))))return false;
 const schema=product.variantSelection;
 // Tek tek mevcut beden ve renk, matriste birlikte satılabilir olmayabilir.
 if(schema?.mode==='matrix'&&(selected.color||selected.size))return schema.variants.some(v=>v.active&&['color','size'].every(field=>!selected[field]||schema.axes.find(a=>a.id===field)?.values.some(a=>a.id===v.values[field]&&key(a.label)===key(selected[field]))));
 return true;
}
export function catalogFacets(products,locale='tr',selected={}){
 return Object.fromEntries(facetKeys.map(field=>{
  const values=new Map();
  for(const product of products)for(const label of facetValues(product,field)){
   if(!matchesFacets(product,{...selected,[field]:label}))continue;
   const normalized=key(label);if(!values.has(normalized))values.set(normalized,{value:label,models:new Set()});
   values.get(normalized).models.add(product.modelId||product.id);
  }
  return [field,[...values.values()].map(v=>({value:v.value,count:v.models.size})).sort((a,b)=>a.value.localeCompare(b.value,locale,{numeric:true}))];
 }));
}
export function appliedFacetCount(route){return facetKeys.filter(k=>route[k]).length+(route.minPrice||route.maxPrice?1:0);}
