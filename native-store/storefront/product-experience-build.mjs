/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-experience-build.mjs
 * Açıklama   : Ürün deneyimini korunmuş kaynağın yalnız türetilmiş yayın kopyasına bağlar.
 */
import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||'');
if(!bundle.includes('native-stage-')||!fs.statSync(path.join(bundle,'public')).isDirectory()||!fs.statSync(path.join(bundle,'private')).isDirectory())throw Error('PRODUCT_EXPERIENCE_BUILD_SCOPE');
for(const file of ['product-experience-core.js','product-experience-renderers.js','product-experience-ui.js'])fs.copyFileSync(path.join(root,file),path.join(bundle,'public',file));
fs.copyFileSync(path.join(root,'product-experience.php'),path.join(bundle,'private/sexogate-product-experience.php'));
const copy=JSON.parse(fs.readFileSync(path.join(root,'product-experience-copy.json'),'utf8'));
for(const locale of ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'])if(!copy[locale]||Object.values(copy[locale]).some(v=>typeof v!=='string'||!v.trim()))throw Error('PRODUCT_EXPERIENCE_COPY_INVALID:'+locale);
fs.copyFileSync(path.join(root,'product-experience-copy.json'),path.join(bundle,'private/sexogate-product-experience-copy.json'));
fs.writeFileSync(path.join(bundle,'public/product-experience-copy.js'),'export const productExperienceCopy='+JSON.stringify(copy)+';\n');
const policy=JSON.parse(fs.readFileSync(path.join(root,'product-return-policy.json'),'utf8'));
for(const locale of ['tr','en'])if(!policy[locale]||!Array.isArray(policy[locale].paragraphs)||!Array.isArray(policy[locale].items))throw Error('PRODUCT_RETURN_POLICY_INVALID:'+locale);
fs.copyFileSync(path.join(root,'product-return-policy.json'),path.join(bundle,'private/sexogate-product-return-policy.json'));
fs.writeFileSync(path.join(bundle,'public/sexogate-product-return-policy.js'),'export const returnPolicy='+JSON.stringify(policy)+';\n');
fs.appendFileSync(path.join(bundle,'public/sexogate-storefront.css'),fs.readFileSync(path.join(root,'product-experience.css'),'utf8'));
fs.appendFileSync(path.join(bundle,'public/sexogate-storefront.js'),"\nimport './product-experience-ui.js?v=storefront';\n");
const app=path.join(bundle,'public/app.js');let source=fs.readFileSync(app,'utf8');
function replaceFunction(name,body){
 const tree=ts.createSourceFile('app.js',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),found=[];
 function visit(n){if(ts.isFunctionDeclaration(n)&&n.name?.text===name)found.push(n);ts.forEachChild(n,visit);}visit(tree);
 if(found.length!==1)throw Error('PRODUCT_EXPERIENCE_HOOK_CHANGED:'+name);const node=found[0];source=source.slice(0,node.getStart(tree))+body+source.slice(node.end);
}
replaceFunction('productSpecOverview','function productSpecOverview(p){return renderProductHighlights(p,sexogateProductExperienceContext());}');
replaceFunction('productAboutMarkup','function productAboutMarkup(p){return renderProductStory(p,sexogateProductExperienceContext());}');
replaceFunction('productSpecifications','function productSpecifications(p){return renderProductFeatures(p,sexogateProductExperienceContext());}');
replaceFunction('productExtraSections','function productExtraSections(p){return renderProductExplore(p,sexogateProductExperienceContext());}');
const nav=/<nav class="product-section-nav">[\s\S]*?<\/nav>/g;
if([...source.matchAll(nav)].length!==1)throw Error('PRODUCT_SECTION_NAV_HOOK_CHANGED');
source=source.replace(nav,'${renderProductNavigation(p,sexogateProductExperienceContext())}');
const about='<section class="detail-section" id="product-information"><h2>${esc(t(\'details\'))}</h2>';
if(source.split(about).length!==2)throw Error('PRODUCT_INFORMATION_TITLE_HOOK_CHANGED');
source=source.replace(about,'<section class="detail-section" id="product-information"><h2>${esc(sexogateProductExperienceContext().copy.information)}</h2>');
const crumb='<bdi dir="ltr">${esc(p.code)}</bdi></nav>';
if(source.split(crumb).length!==2)throw Error('PRODUCT_BREADCRUMB_HOOK_CHANGED');
source=source.replace(crumb,'<span aria-current="page">${esc(productName(p))}</span></nav>');
const displayName='const productName=p=>withoutColorSuffix(productDisplayName(p,locale),loc(p.variantColor));';
if(source.split(displayName).length!==2)throw Error('PRODUCT_DISPLAY_NAME_HOOK_CHANGED');
source=source.replace(displayName,'const productName=p=>loc(p.name)||withoutColorSuffix(productDisplayName(p,locale),loc(p.variantColor));');
source="import {renderProductHighlights,renderProductStory,renderProductFeatures,renderProductExplore,renderProductNavigation} from './product-experience-renderers.js?v=storefront';\nimport {productExperienceCopy} from './product-experience-copy.js?v=storefront';\nimport {returnPolicy as sexogateProductReturnPolicy} from './sexogate-product-return-policy.js?v=storefront';\n"+source+`\nfunction sexogateProductExperienceContext(){return {catalog,config,locale,esc,t,href,image,productName,productHref,productCard,productShelf,recent,factLabels:sexogateCopy[locale]||sexogateCopy.en,copy:productExperienceCopy[locale]||productExperienceCopy.en,returnPolicy:sexogateProductReturnPolicy[locale]||sexogateProductReturnPolicy.en};}\n`;
fs.writeFileSync(app,source);
const seo=path.join(bundle,'private/seo.php');let php=fs.readFileSync(seo,'utf8');
const strict='declare(strict_types=1);',call='$body=nodenoSeoProductBody($product,$catalog,$locale,$variants);';
if(php.split(strict).length!==2||php.split(call).length!==2)throw Error('PRODUCT_EXPERIENCE_SSR_HOOK_CHANGED');
php=php.replace(strict,strict+"\nrequire_once __DIR__.'/sexogate-product-experience.php';").replace(call,'$body=sexogateProductBody($product,$catalog,$locale,$variants,$config);');fs.writeFileSync(seo,php);
const control=path.join(bundle,'private/control-catalog.php');let catalogPhp=fs.readFileSync(control,'utf8').replace(/\r\n/g,'\n');
const eager="require_once __DIR__.'/seo.php';$position=0;",foundCategory="if(!$category)continue;\n   $family=nodenoSeoFamily";
if(catalogPhp.split(eager).length!==2||catalogPhp.split(foundCategory).length!==2)throw Error('COLLECTION_SEO_LAZY_HOOK_CHANGED');
catalogPhp=catalogPhp.replace(eager,'$position=0;').replace(foundCategory,"if(!$category)continue;\n   require_once __DIR__.'/seo.php';$family=nodenoSeoFamily");fs.writeFileSync(control,catalogPhp);
const entryFile=path.join(bundle,'public/index.php');let entry=fs.readFileSync(entryFile,'utf8');
const adminCall="if(nodenoControlHandle($path,$method,$state['sourceCatalog'],$state['config'],$state['storage'])";
if(entry.split(adminCall).length!==2)throw Error('ADMIN_UNUSED_PROJECTION_HOOK_CHANGED');
entry=entry.replace(adminCall,"if(str_starts_with($path,'/api/admin/'))unset($state['catalog']);\n            "+adminCall);fs.writeFileSync(entryFile,entry);
console.log(JSON.stringify({productExperience:true,inlineReturns:true,realCollectionMosaics:true,sourceSnapshotChanged:false}));
