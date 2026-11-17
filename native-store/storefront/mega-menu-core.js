/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/mega-menu-core.js
 * Açıklama   : Mega menü kategorilerini yalnız mevcut kamu kataloğunun gerçek ürün ailelerinden seçer.
 */
export function megaCategoryFamily(categories,id){
 const family=new Set([id]),pending=[id];for(let i=0;i<pending.length;i++)for(const category of categories)if(category.parentId===pending[i]&&!family.has(category.id)){family.add(category.id);pending.push(category.id);}return family;
}
export function megaPublicProducts(catalog){return(catalog.products||[]).filter(product=>typeof product.id==='string'&&!product.hidden&&product.published!==false&&product.visible!==false);}
export function megaPhotoIndex(product){const valid=index=>typeof product.images?.[index]==='string'&&product.images[index].trim();return Number.isInteger(product.coverIndex)&&valid(product.coverIndex)?product.coverIndex:Math.max(0,(product.images||[]).findIndex((_,index)=>valid(index)));}
export function megaMenuModel(catalog,{roots,active,categoryPhoto}={}){
 const categories=catalog.categories||[],products=megaPublicProducts(catalog),byId=new Map(categories.map(category=>[category.id,category])),cache=new Map();
 const entry=category=>{
  if(cache.has(category.id))return cache.get(category.id);const family=megaCategoryFamily(categories,category.id),members=products.filter(product=>(product.categoryIds||[]).some(id=>family.has(id))),photos=members.filter(product=>Array.isArray(product.images)&&product.images.some(src=>typeof src==='string'&&src.trim())),preferred=categoryPhoto?.(category.id),photo=photos.find(product=>product.id===preferred?.id)||photos[0]||null;
  const result={category,count:new Set(members.map(product=>product.modelId||product.id)).size,photo};cache.set(category.id,result);return result;
 };
 const candidates=roots||categories.filter(category=>category.parentId==null||!byId.has(category.parentId)),seen=new Set(),publicRoots=[];
 for(const candidate of candidates){const category=byId.get(candidate.id);if(!category||seen.has(category.id))continue;seen.add(category.id);const value=entry(category);if(value.count>0)publicRoots.push(value);}
 const activeId=typeof active==='string'?active:active?.id,selected=publicRoots.find(root=>root.category.id===activeId)||publicRoots[0]||null;
 if(!selected)return {roots:publicRoots,active:null,cards:[]};
 const children=categories.filter(category=>category.parentId===selected.category.id&&entry(category).count>0),cards=[],cardIds=new Set();
 const add=(category,parent=null)=>{if(cardIds.has(category.id))return;const value=entry(category);if(!value.count)return;cardIds.add(category.id);cards.push({...value,parent});};
 if(!children.length)add(selected.category);else for(const child of children){add(child);for(const grandchild of categories)if(grandchild.parentId===child.id)add(grandchild,child);}
 return {roots:publicRoots,active:selected,cards};
}
