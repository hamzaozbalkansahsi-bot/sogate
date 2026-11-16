/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/home-core.js
 * Açıklama   : Ana sayfa raflarını gerçek katalogdan dengeli ve tekrarsız olarak seçer.
 */
const identity=p=>String(p.modelId||p.id);
export function uniqueHomeProducts(products){const seen=new Set();return products.filter(p=>p&&p.published!==false&&!p.hidden&&p.images?.length&&!seen.has(identity(p))&&seen.add(identity(p)));}
export function categoryMembers(products,categories,id){
 const family=new Set([id]);let changed=true;while(changed){changed=false;for(const c of categories)if(family.has(c.parentId)&&!family.has(c.id)){family.add(c.id);changed=true;}}
 return products.filter(p=>(p.categoryIds||[]).some(id=>family.has(id)));
}
export function balancedHomeProducts(products,categories,roots,limit=8,excluded=[]){
 const queues=roots.map(c=>categoryMembers(products,categories,c.id)),seen=new Set(excluded.map(identity)),result=[];let position=0;
 while(result.length<limit&&queues.some(q=>position<q.length)){for(const queue of queues){const p=queue[position];if(p&&!seen.has(identity(p))){seen.add(identity(p));result.push(p);if(result.length===limit)break;}}position++;}
 for(const p of products)if(result.length<limit&&!seen.has(identity(p))){seen.add(identity(p));result.push(p);}
 return result;
}
export function homeModel(catalog,{category='',featuredId='',recentIds=[]}={}){
 const products=uniqueHomeProducts(catalog.products||[]),categories=catalog.categories||[],members=id=>categoryMembers(products,categories,id),roots=categories.filter(c=>!c.parentId&&members(c.id).length);
 const rootIds=new Set(roots.map(c=>c.id)),shortcuts=[...roots,...categories.filter(c=>rootIds.has(c.parentId)&&members(c.id).length)].slice(0,10),selection=balancedHomeProducts(products,categories,roots),selected=roots.find(c=>c.id===category)||null;
 const lingerie=roots.find(c=>c.id==='sg_lingerie'),lingeriePool=lingerie?members(lingerie.id):[],unused=lingeriePool.filter(p=>!selection.some(v=>identity(v)===identity(p))),lingerieProducts=(unused.length>=8?unused:lingeriePool).slice(0,8);
 const featured=products.find(p=>p.id===featuredId),campaigns=[...(featured?[{product:featured,category:null}]:[]),...roots.slice(0,featured?3:4).map(c=>({category:c,product:members(c.id)[0]}))];
 const discovery=selected?members(selected.id).slice(0,8):balancedHomeProducts(products,categories,roots,8,[...selection,...lingerieProducts]);
 return {products,roots,shortcuts,selection,lingerie,lingerieProducts,campaigns,selected,discovery,recent:[...new Set(recentIds)].map(id=>products.find(p=>p.id===id)).filter(Boolean).slice(0,8),photo:id=>members(id)[0]};
}
