/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-experience-core.js
 * Açıklama   : Ürün bilgilerini ve gerçek katalogdan ilişkili keşif gruplarını seçer.
 */
export const factOrder=['materials','dimensions','diameter','weight','volume','sizes','colors','battery','ingredients','package','origin','manufacturer'];
export function localText(value,locale='tr'){
 const item=typeof value==='string'?value:value?.[locale]??value?.en??value?.tr??'';
 return typeof item==='string'?item.trim():'';
}
const clean=value=>typeof value==='string'?value.replace(/\s+/gu,' ').trim():'';
const lines=value=>Array.isArray(value)?value.map(v=>localText(v)).filter(Boolean):[];
const key=p=>String(p.modelId||p.id);
export function visibleProducts(products=[]){
 const seen=new Set();return products.filter(p=>p&&p.id&&p.published!==false&&!p.hidden&&Array.isArray(p.images)&&p.images.length&&!seen.has(key(p))&&seen.add(key(p)));
}
export function productFacts(product,locale='tr',labels={}){
 const result=[],seen=new Set(),keys=new Set();const add=(id,label,value)=>{label=clean(label);value=clean(value);const identity=label.toLocaleLowerCase('tr-TR');if(!label||!value||value.length>600||seen.has(identity)||keys.has(id))return;seen.add(identity);keys.add(id);result.push({id,label,value});};
 for(const row of product.storefrontStory?.[locale]?.fields||[])if(row.key!=='productCode')add(row.key,row.title,row.value);
 for(const id of factOrder){const value=localText(product.storefrontFacts?.[id],locale);if(value)add(id,labels[id]||id,value);}
 for(const [index,row] of (product.specs||[]).entries())add('spec-'+index,localText(row.label,locale),localText(row.value,locale));
 return result;
}
export function productStory(product,locale='tr'){
 const story=product.storefrontStory?.[locale]||product.storefrontStory?.en||product.storefrontStory?.tr||{};
 const body=localText(product.description,locale).split(/\n\s*\n/u).map(v=>v.trim()).filter(Boolean);
 const intro=localText(story.intro,locale)||body.shift()||localText(product.name,locale);
 const paragraphs=lines(story.paragraphs).length?lines(story.paragraphs):body;
 const unique=new Set([clean(intro)]);const rest=paragraphs.filter(v=>{const text=clean(v);if(!text||unique.has(text))return false;unique.add(text);return true;});
 return {intro,paragraphs:rest,bullets:lines(story.bullets),packageContents:lines(story.packageContents),care:localText(story.care,locale),safety:localText(story.safety,locale)};
}
export function categoryFamily(categories,id){
 const result=new Set([id]);let changed=true;while(changed){changed=false;for(const row of categories)if(result.has(row.parentId)&&!result.has(row.id)){result.add(row.id);changed=true;}}
 return result;
}
export function categoryMembers(products,categories,id){const family=categoryFamily(categories,id);return products.filter(p=>(p.categoryIds||[]).some(v=>family.has(v)));}
export function productDiscovery(product,catalog={},config={},recentIds=[]){
 const products=visibleProducts(catalog.products),categories=Array.isArray(catalog.categories)?catalog.categories:[],others=products.filter(p=>key(p)!==key(product)),byId=new Map(products.map(p=>[p.id,p]));
 const currentIds=new Set(product.categoryIds||[]),map=new Map(categories.map(c=>[c.id,c]));
 const roots=new Set();for(const id of currentIds){let at=id;const visited=new Set();while(map.get(at)?.parentId&&!visited.has(at)){visited.add(at);at=map.get(at).parentId;}roots.add(at);}
 const similar=others.filter(p=>(p.categoryIds||[]).some(id=>currentIds.has(id)&&map.get(id)?.parentId));
 const similarKeys=new Set(similar.map(key));const complementary=others.filter(p=>!similarKeys.has(key(p))&&[...roots].some(id=>categoryMembers([p],categories,id).length));
 const familyPool=[...similar,...complementary,...others],chosen=new Set();const selection=familyPool.filter(p=>!chosen.has(key(p))&&chosen.add(key(p))).slice(0,12);
 const popularity=config.productPopularity;const counts=popularity?.source==='fulfilled-order-lines'&&typeof popularity.asOf==='string'&&Number.isFinite(Date.parse(popularity.asOf))&&popularity.counts&&typeof popularity.counts==='object'?popularity.counts:null;
 const popular=counts?others.filter(p=>Number.isSafeInteger(counts[p.id])&&counts[p.id]>0).sort((a,b)=>counts[b.id]-counts[a.id]||a.id.localeCompare(b.id)).slice(0,12):[];
 const collections=[],collectionTargets=new Set();
 for(const row of config.collections||[]){if(row?.data?.enabled!==true)continue;const ids=Array.isArray(row.data.productIds)?row.data.productIds:String(row.data.productIds||'').split(',').map(v=>v.trim());const members=visibleProducts(ids.map(id=>byId.get(id)).filter(Boolean));if(members.length<3)continue;const title=row.data.title||Object.fromEntries(Object.entries(row.data).filter(([k])=>k.startsWith('title_')).map(([k,v])=>[k.slice(6),v]));if(!localText(title))continue;collections.push({id:String(row.id),title,products:members.slice(0,3),count:members.length,params:{collection:String(row.id)}});collectionTargets.add('collection:'+row.id);if(collections.length===6)break;}
 const ordered=[...categories.filter(c=>currentIds.has(c.id)),...categories.filter(c=>currentIds.has(c.parentId)),...categories.filter(c=>roots.has(c.id)),...categories];
 for(const category of ordered){if(collections.length===6)break;if(collectionTargets.has('category:'+category.id))continue;const members=categoryMembers(products,categories,category.id);if(members.length<3)continue;collectionTargets.add('category:'+category.id);collections.push({id:category.id,title:category.name,products:members.slice(0,3),count:members.length,params:{category:category.id}});}
 const links=[],linkTargets=new Set();for(const c of ordered){if(links.length===9)break;if(linkTargets.has(c.id)||!categoryMembers(products,categories,c.id).length)continue;linkTargets.add(c.id);links.push({title:c.name,params:{category:c.id}});}
 const brand=clean(product.brand||product.productBrand);if(brand&&products.filter(p=>clean(p.brand||p.productBrand)===brand).length>1)links.push({title:brand,params:{brand}});
 return {similar:similar.slice(0,12),complementary:complementary.slice(0,12),selection,popular,hasPopularity:popular.length>0,collections,links,recent:visibleProducts(recentIds.map(id=>byId.get(String(id))).filter(Boolean)).filter(p=>key(p)!==key(product)).slice(0,12)};
}
