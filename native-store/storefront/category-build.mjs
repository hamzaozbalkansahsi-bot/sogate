/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/category-build.mjs
 * Açıklama   : Kategori deneyimini yalnız türetilmiş yayın kopyasına bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import ts from 'typescript';import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]);
if(!bundle.includes('native-stage-'))throw Error('CATEGORY_BUILD_SCOPE');
for(const file of ['category-core.js','category-renderers.js','category-ui.js','category.css'])fs.copyFileSync(path.join(root,file),path.join(bundle,'public','sexogate-'+file));
const copy=JSON.parse(fs.readFileSync(path.join(root,'category-copy.json'),'utf8'));
fs.writeFileSync(path.join(bundle,'public/sexogate-category-copy.js'),'export const categoryCopy='+JSON.stringify(copy)+';\n');
fs.appendFileSync(path.join(bundle,'public/sexogate-storefront.js'),"\nimport './sexogate-category-ui.js?v=storefront';\n");
fs.appendFileSync(path.join(bundle,'public/sexogate-storefront.css'),fs.readFileSync(path.join(root,'category.css'),'utf8'));
const oldFacets="['q','sort','minPrice','maxPrice','color','maxWidth','maxHeight','maxDepth','collection']",newFacets="['q','sort','minPrice','maxPrice','color','maxWidth','maxHeight','maxDepth','collection','brand','size','material','section']";
for(const relative of ['private/seo.php','public/seo-core.js']){const file=path.join(bundle,relative),value=fs.readFileSync(file,'utf8');if(value.split(oldFacets).length!==2)throw Error('CATEGORY_SEO_HOOK_CHANGED:'+relative);fs.writeFileSync(file,value.replace(oldFacets,newFacets));}
fs.copyFileSync(path.join(root,'categories.php'),path.join(bundle,'private/sexogate-categories.php'));
fs.copyFileSync(path.join(root,'category-copy.json'),path.join(bundle,'private/sexogate-category-copy.json'));
const seo=path.join(bundle,'private/seo.php'),seoSource=fs.readFileSync(seo,'utf8'),hook="return ['verification'=>$config['seo']??[]";if(seoSource.split(hook).length!==2)throw Error('CATEGORY_SSR_HOOK_CHANGED');fs.writeFileSync(seo,seoSource.replace(hook,"if($kind==='categories'){require_once __DIR__.'/sexogate-categories.php';$body=sexogateCategoryBody($catalog,$locale,$query);}"+hook));
const app=path.join(bundle,'public/app.js');let source=fs.readFileSync(app,'utf8');
function edit(name,transform){const tree=ts.createSourceFile('app.js',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),nodes=[];function visit(n){if(ts.isFunctionDeclaration(n)&&n.name?.text===name)nodes.push(n);ts.forEachChild(n,visit);}visit(tree);if(nodes.length!==1)throw Error('CATEGORY_HOOK_CHANGED:'+name);const n=nodes[0],old=source.slice(n.getStart(tree),n.end),next=transform(old);if(old===next)throw Error('CATEGORY_HOOK_UNUSED:'+name);source=source.slice(0,n.getStart(tree))+next+source.slice(n.end);}
edit('currentRoute',s=>s.replace("step:p.get('step')||''","step:p.get('step')||'',brand:p.get('brand')||'',size:p.get('size')||'',material:p.get('material')||'',section:p.get('section')||''"));
edit('catalogParams',()=>"function catalogParams(overrides={}){const {category,q,sort,minPrice,maxPrice,color,brand,size,material,collection}=currentRoute();return{category,q,sort,minPrice,maxPrice,color,brand,size,material,collection,...overrides};}");
edit('renderCategories',()=>"function renderCategories(){return renderSexogateCategories(sexogateCategoryContext());}");
edit('filterMarkup',()=>"function filterMarkup(category,sort,options={}){return renderSexogateFilters(sexogateCategoryContext(),sexogateCatalogFacets(),options);}");
edit('submitCatalogFilters',()=>`function submitCatalogFilters(form){const data=new FormData(form),min=String(data.get('minPrice')||''),max=String(data.get('maxPrice')||''),low=priceFilterMinor(min),high=priceFilterMinor(max),upper=form.elements.namedItem('maxPrice');upper.setCustomValidity(low!==null&&high!==null&&low>high?t('priceRangeError'):'');if(!form.reportValidity())return;navigate(href('catalog',catalogParams({minPrice:low===null?'':String(low/100),maxPrice:high===null?'':String(high/100),...Object.fromEntries(['brand','color','size','material'].map(k=>[k,String(data.get(k)||'')])),sort:String(data.get('sort')||currentRoute().sort),pg:''})));}`);
edit('activeFilterMarkup',()=>`function activeFilterMarkup(){const route=currentRoute(),c=sexogateCategoryCopy[locale],entries=[];for(const key of ['brand','color','size','material'])if(route[key])entries.push([c[key]+': '+route[key],{[key]:''}]);for(const [key,label] of [['minPrice','minimumPrice'],['maxPrice','maximumPrice']]){const value=priceFilterMinor(route[key]);if(value!==null)entries.push([t(label)+': '+formatMoney(value,locale),{[key]:''}]);}return entries.length?\`<div class="active-filters" aria-label="\${esc(t('activeFilters'))}">\${entries.map(([label,reset])=>\`<a href="\${esc(href('catalog',catalogParams({...reset,pg:''})))}" data-nav aria-label="\${esc(t('removeFilter')+': '+label)}">\${esc(label)}\${icon('close')}</a>\`).join('')}</div>\`:'';}`);
edit('renderCatalog',s=>s.replace('function renderCatalog(','function sexogateOriginalCatalog(').replace('list=filterProducts(','list=sexogateFilterProducts(').replace("color:favorites?'':route.color,","color:favorites?'':route.color,brand:favorites?'':route.brand,size:favorites?'':route.size,material:favorites?'':route.material,"));
source=`import {renderCategories as renderSexogateCategories,renderFilters as renderSexogateFilters,renderFilterBar as renderSexogateFilterBar,categorySearch as sexogateCategorySearch} from './sexogate-category-renderers.js?v=storefront';
import {catalogFacets as sexogateFacets,matchesFacets as sexogateMatchesFacets} from './sexogate-category-core.js?v=storefront';
import {categoryCopy as sexogateCategoryCopy} from './sexogate-category-copy.js?v=storefront';
`+source+`
function sexogateCategoryContext(){return {catalog,route:currentRoute(),locale,esc,t,href,loc,icon,categoryCount,categoryPhoto,image,rootCategories,productCard,sortOptions,categoryNavigation,productsIn:id=>distinctModels(familyProducts(id))};}
function sexogateCatalogFacets(){const route=currentRoute(),collection=(config.collections||[]).find(v=>v.id===route.collection&&v.data.enabled),ids=collection?new Set((collection.data.productIds||'').split(',').map(v=>v.trim())):null;return sexogateFacets(filterProducts(ids?catalog.products.filter(p=>ids.has(p.id)):catalog.products,{query:route.q,category:route.category,categories:catalog.categories,locale,minPriceMinor:priceFilterMinor(route.minPrice),maxPriceMinor:priceFilterMinor(route.maxPrice)}),locale,route);}
function sexogateFilterProducts(products,options){const rows=filterProducts(products,{...options,color:'',groupModels:false}).filter(p=>sexogateMatchesFacets(p,options));return options.groupModels?distinctModels(rows):rows;}
function renderCatalog(options={}){const html=sexogateOriginalCatalog(options);if(options.favorites)return html;const context=sexogateCategoryContext(),route=context.route,category=categoryById(route.category);return html.replace('<div class="wrap listing-page">','<div class="wrap listing-page sg-listing-page">'+sexogateCategorySearch(context,category?loc(category.name):'',category?.parentId||category?.id||'')).replace('<div class="catalog-toolbar">',renderSexogateFilterBar(context,sexogateCatalogFacets())+'<div class="catalog-toolbar">');}
`;
fs.writeFileSync(app,source);
console.log(JSON.stringify({categoryExplorer:true,variantAwareFacets:true,marketplaceSellerBlocks:false,upstreamChanged:false}));
