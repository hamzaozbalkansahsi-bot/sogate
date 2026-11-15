/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/apply.mjs
 * Açıklama   : Korunmuş kaynağa dokunmadan yetişkin mağazası bileşenlerini yayın kopyasına bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import ts from 'typescript';import{fileURLToPath,pathToFileURL}from'node:url';import{execFileSync}from'node:child_process';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]);if(!bundle.includes('native-stage-'))throw Error('STOREFRONT_BUILD_SCOPE');
const copy=JSON.parse(fs.readFileSync(path.join(root,'copy.json'),'utf8'));
for(const [source,target]of [['content.php','private/sexogate-storefront-content.php'],['copy.json','private/sexogate-storefront-copy.json'],['renderers.js','public/sexogate-storefront-renderers.js'],['ui.js','public/sexogate-storefront.js'],['storefront.css','public/sexogate-storefront.css']])fs.copyFileSync(path.join(root,source),path.join(bundle,target));
fs.writeFileSync(path.join(bundle,'public/sexogate-storefront-copy.js'),'export const storefrontCopy='+JSON.stringify(copy)+';\n');
fs.copyFileSync(path.join(root,'home.php'),path.join(bundle,'private/sexogate-storefront-home.php'));
const dictionaries=await Promise.all(['i18n.js','shop-i18n.js','shopping-i18n.js'].map(name=>import(pathToFileURL(path.join(bundle,'public',name)).href)));
const uiKeys=['allProducts','add','favorites','compare','addCollection'],uiCopy={};
for(const locale of ['tr','en','ru','ar']){const dictionary={...dictionaries[0].copy[locale],...dictionaries[1].shopCopy[locale],...dictionaries[2].shoppingCopy[locale]};uiCopy[locale]=Object.fromEntries(uiKeys.map(key=>{if(typeof dictionary[key]!=='string')throw Error('SSR_LABEL_MISSING:'+locale+':'+key);return[key,dictionary[key]];}));}
for(const locale of ['de','az','kk','tk','uz','ky','fa']){const dictionary=JSON.parse(fs.readFileSync(path.join(bundle,'public/locales',locale+'.json'),'utf8')).translations;uiCopy[locale]=Object.fromEntries(uiKeys.map(key=>{const value=dictionary[uiCopy.en[key]];if(typeof value!=='string')throw Error('SSR_TRANSLATION_MISSING:'+locale+':'+key);return[key,value];}));}
fs.writeFileSync(path.join(bundle,'private/sexogate-storefront-ui-copy.json'),JSON.stringify(uiCopy));
function fileEdit(folder,file,from,to){const p=path.join(bundle,folder,file),source=fs.readFileSync(p,'utf8');if(source.split(from).length!==2)throw Error('STOREFRONT_HOOK_CHANGED:'+file);fs.writeFileSync(p,source.replace(from,to));}
function functionEdit(file,name,replacement){const p=path.join(bundle,'public',file),source=fs.readFileSync(p,'utf8'),tree=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),found=[];function walk(node){if(ts.isFunctionDeclaration(node)&&node.name?.text===name)found.push(node);ts.forEachChild(node,walk);}walk(tree);if(found.length!==1)throw Error('STOREFRONT_FUNCTION_CHANGED:'+name);const node=found[0];fs.writeFileSync(p,source.slice(0,node.getStart(tree))+replacement+source.slice(node.end));}
const app=path.join(bundle,'public/app.js');fs.writeFileSync(app,"import {renderSexogateHome,renderSexogateStory,renderSexogateFeatures,renderSexogateShelf} from './sexogate-storefront-renderers.js?v=storefront';\nimport {storefrontCopy as sexogateCopy} from './sexogate-storefront-copy.js?v=storefront';\n"+fs.readFileSync(app,'utf8'));
functionEdit('app.js','renderHome',"function renderHome(){return renderSexogateHome({catalog,config,locale,esc,t,image,href,productLink,productName,priceMarkup,byId,rootCategories,categoryCount,categoryPhoto,productShelf,homeCollections,recent,recommendedIds,experience});}");
functionEdit('app.js','productAboutMarkup',"function productAboutMarkup(p){return renderSexogateStory(p,{locale,esc,image});}");
functionEdit('app.js','productSpecifications',"function productSpecifications(p){return renderSexogateFeatures(p,{locale,esc});}");
functionEdit('app.js','productSpecOverview',"function productSpecOverview(){return '';}");
functionEdit('app.js','productServicePanel',"function productServicePanel(){return '';}");
functionEdit('app.js','dimensionFilterMarkup',"function dimensionFilterMarkup(){return '';}");
functionEdit('app.js','productShelf',"function productShelf(title,products,params={}){return renderSexogateShelf({title:title==='homeSelection'?sexogateCopy[locale].selection:t(title),products:distinctModels(products),esc,link:navLink('catalog','more','text-link',params),card:productCard});}");
functionEdit('app.js','productExtraSections',"function productExtraSections(p){const suggestions=productSuggestions(p,catalog.products,catalog.categories,recent);if(recommendedIds.length)suggestions.similar=distinctModels([...recommendedIds.map(byId).filter(v=>v&&(v.modelId||v.id)!==(p.modelId||p.id)),...suggestions.similar]).slice(0,12);return productShelf('productSimilar',suggestions.similar)+productShelf('productComplementary',suggestions.complementary)+productShelf('recent',suggestions.recent);}");
let source=fs.readFileSync(app,'utf8');const pending=/<p class="product-payment-note"[^>]*>[\s\S]*?<\/p>/g,delivery=/<div class="delivery-preview">[\s\S]*?<\/div><\/div>/g;
if(!pending.test(source)||!delivery.test(source))throw Error('PRODUCT_NOTE_HOOK_CHANGED');source=source.replace(pending,'').replace(delivery,'');source=source.replaceAll("t('specifications')","sexogateCopy[locale].features");
source=source.replace('<a href="#product-reviews">${esc(t(\'reviews\'))}</a>','');
const tax=/<small class="price-tax-note">[^\n]*?<\/small>/;if(!tax.test(source))throw Error('PRICE_TAX_HOOK_CHANGED');source=source.replace(tax,match=>'${p.taxTreatment===\'unverified\'?\'\':`'+match+'`}');
let buyCount=0;source=source.replace(/<button[^>]*data-product-buy="\$\{esc\(p\.id\)\}"[^>]*>[\s\S]*?<\/button>/g,match=>{buyCount++;return '${config.checkoutEnabled?`'+match+'`:\'\'}';});if(buyCount!==2)throw Error('PURCHASE_BUTTON_HOOK_CHANGED');fs.writeFileSync(app,source);
for(const name of ['collectionsBody','collectionsStart'])fileEdit('public','shopping-ui.js',"t('"+name+"')",'sexogateCopy[state().locale].'+name);
const shopping=path.join(bundle,'public/shopping-ui.js');fs.writeFileSync(shopping,"import {storefrontCopy as sexogateCopy} from './sexogate-storefront-copy.js?v=storefront';\n"+fs.readFileSync(shopping,'utf8'));
functionEdit('shopping-ui.js','productTools','function productTools(p){return `<div class="product-shopping-tools">${selectionButton(p)}<button type="button" data-collect="${esc(p.id)}">${icon(\'bookmark\')}${esc(t(\'addCollection\'))}</button></div>`;}');
functionEdit('shopping-ui.js','guide','function guide(){const c=sexogateCopy[state().locale];return `<section class="shopping-guide"><div><p class="eyebrow">SEXOGATE</p><h2>${esc(c.guideTitle)}</h2></div>${[[\'heart\',\'favorites\'],[\'compare\',\'compare\'],[\'bookmark\',\'collections\']].map(([ico,key])=>`<a href="${esc(href(key))}" data-nav><span class="guide-icon">${icon(ico)}</span><div><h3>${esc(t(key))}</h3></div></a>`).join(\'\')}</section>`;}');
let recent=fs.readFileSync(shopping,'utf8');const recentStart=recent.indexOf('function renderRecent()'),recentEnd=recent.indexOf('\n',recentStart);if(recentStart<0)throw Error('RECENT_HOOK_CHANGED');const oldRecent=recent.slice(recentStart,recentEnd),newRecent=oldRecent.replace('class="product-grid"','class="product-row"');if(newRecent===oldRecent)throw Error('RECENT_GRID_HOOK_CHANGED');fs.writeFileSync(shopping,recent.slice(0,recentStart)+newRecent+recent.slice(recentEnd));
fs.writeFileSync(path.join(bundle,'public/home-vitrine.js'),"import {renderSexogateHero} from './sexogate-storefront-renderers.js?v=storefront';\nexport const renderHomeVitrine=renderSexogateHero;\nexport function mountHomeVitrine(){return ()=>{};}\n");
fileEdit('private','control-catalog.php',"require_once __DIR__.'/suppliers.php';","require_once __DIR__.'/suppliers.php';\nrequire_once __DIR__.'/sexogate-storefront-content.php';");
fileEdit('private','control-catalog.php','$products[]=$p;','$products[]=sexogateStorefrontProduct($p);');
fileEdit('private','seo.php',"return ['verification'=>$config['seo']??[]", "if($kind==='home'){require_once __DIR__.'/sexogate-storefront-content.php';require_once __DIR__.'/sexogate-storefront-home.php';$body=sexogateStorefrontHome($catalog,$config,$locale);}\n return ['verification'=>$config['seo']??[]");
execFileSync(process.execPath,[path.join(root,'variant-apply.mjs'),bundle],{stdio:'inherit'});
console.log(JSON.stringify({storefrontComponents:true,automaticFurnitureScenes:false,roomFitTools:false,sourceSnapshotChanged:false}));
