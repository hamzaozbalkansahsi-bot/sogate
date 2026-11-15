/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/apply-store-theme.mjs
 * Açıklama   : Ortak alışveriş motoruna yalnız SEXOGATE metinleri ve yetişkin giriş katmanını uygular.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),bundle=path.resolve(process.argv[2]),version=process.argv[3];
if(!bundle.includes('native-stage-')||!version)throw new Error('THEME_BUILD_SCOPE_INVALID');
const data=JSON.parse(fs.readFileSync(path.join(root,'native-store/theme/store-copy.json'),'utf8'));
const entryPath=path.join(bundle,'private/index.html');let entry=fs.readFileSync(entryPath,'utf8');
entry=entry.replaceAll('İyi tasarım. Kolay yaşam.',data.tr.slogan).replaceAll('SEXOGATE mobilya koleksiyonu. Ürünleri keşfedin, teknik detayları inceleyin, kendi listenizi oluşturun.','SEXOGATE yetişkin ürünleri, iç giyim, aksesuar ve hediye koleksiyonları. Ürün bilgilerini ve bakım uyarılarını inceleyin.').replaceAll('Furniture for everyday living. Discover SEXOGATE.',data.en.body).replace(/<a[^>]*data-(?:furniture|wholesale)-nav[^>]*>[\s\S]*?<\/a>/g,'');fs.writeFileSync(entryPath,entry);
const fields={slogan:'slogan',announcement:'collection',collection:'collection',heroEyebrow:'collection',heroTitle:'slogan',heroBody:'body',heroNote:'headline',roomsTitle:'headline',roomsBody:'body',catalogTitle:'collection',storyTitle:'headline',storyBody:'body',storySmall:'slogan',footerIntro:'slogan',shipping:'shipping',shippingTitle:'shipping',shippingBody:'delivery',support:'care',livingSpaces:'collection',forHome:'collection',contactBody:'contact',helpChoose:'choose',helpCart:'basket',helpCartBody:'basket',collectionEntry:'accessories',collectionWork:'couples',collectionLiving:'care',collectionYouth:'gifts',hallwayCampaignTitle:'accessories',kidsCampaignTitle:'gifts',storageIdeas:'headline',workspaceIdeas:'body',questionIntro:'choose',questionAssembly:'care',faqAssembly:'care',assemblyCare:'care',assemblyCareBody:'choose',specGroupAssembly:'care',deliveryGuide:'delivery',fitNote:'choose',faqShippingBody:'delivery',helpShippingBody:'delivery'};
const values=Object.fromEntries(Object.entries(data).map(([locale,copy])=>[locale,Object.fromEntries(Object.entries(fields).map(([field,key])=>[field,copy[key]]))]));
const baseValues=Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,values[locale]]));
for(const [file,name]of [['i18n.js','copy'],['shop-i18n.js','shopCopy'],['shopping-i18n.js','shoppingCopy']]){
 const p=path.join(bundle,'public',file);fs.appendFileSync(p,'\n/* SEXOGATE presentation copy; commerce rules remain unchanged. */\n'+`for(const [sexogateLocale,sexogateOverrides]of Object.entries(${JSON.stringify(baseValues)}))Object.assign(${name}[sexogateLocale],sexogateOverrides);\n`);
}
for(const locale of ['de','az','kk','tk','uz','ky','fa']){
 const p=path.join(bundle,'public/locales',locale+'.json'),dictionary=JSON.parse(fs.readFileSync(p,'utf8'));
 for(const field of Object.keys(fields))dictionary.translations[values.en[field]]=values[locale][field];
 const raw=JSON.stringify(dictionary);fs.writeFileSync(p,raw);fs.writeFileSync(path.join(bundle,'private','locale.'+locale+'.json'),raw);
}
fs.writeFileSync(path.join(bundle,'public/welcome-poster.js'),`/* SEXOGATE: age confirmation is mounted by the common brand layer. */\nexport function mountWelcomePoster(){return {dismiss(){}};}\n`);
fs.appendFileSync(path.join(bundle,'public/sexogate-branding.js'),'\n'+fs.readFileSync(path.join(root,'native-store/theme/age-gate.js'),'utf8'));
fs.appendFileSync(path.join(bundle,'public/sexogate.css'),'\n'+fs.readFileSync(path.join(root,'native-store/theme/age-gate.css'),'utf8'));
fs.writeFileSync(path.join(bundle,'private/sexogate-store-copy.json'),JSON.stringify(data));
const php=path.join(bundle,'private/blog-i18n.php');let source=fs.readFileSync(php,'utf8');
source=source.replace('return $copy;',`$brand=json_decode((string)file_get_contents(__DIR__.'/sexogate-store-copy.json'),true);$theme=$brand[$locale]??$brand['en'];$copy['title']=$theme['headline'];$copy['intro']=$theme['choose'];$copy['shop']=$theme['collection'];$copy['care']=$theme['care'];$copy['planning']=$theme['privacy'];return $copy;`);fs.writeFileSync(php,source);
for(const name of ['blog.php','blog-http.php']){const p=path.join(bundle,'private',name);fs.writeFileSync(p,fs.readFileSync(p,'utf8').replaceAll("['small-spaces','entryway','living','bedroom','work','care','planning','color','paint-math','surfaces','application','renewal']","['care','planning']"));}
const blogPath=path.join(bundle,'private/blog.php');let blog=fs.readFileSync(blogPath,'utf8');
let removedTools=0;blog=blog.replace(/<a(?: class="blog-inline-tool")? href="[^"\n]*\['tool'=>'(?:space|paint)'\][^"\n]*">[^<]*<\/a>/g,()=>{removedTools++;return '';});
if(removedTools!==3)throw new Error('FURNITURE_TOOL_LINKS_NOT_REMOVED');
blog=blog.replace(/function nodenoBlogToolForm\(string \$kind,string \$locale\):string \{[\s\S]*?(?=function nodenoBlogCard)/,"function nodenoBlogToolForm(string $kind,string $locale):string {return '';}\n");fs.writeFileSync(blogPath,blog);
const blogHttpPath=path.join(bundle,'private/blog-http.php');fs.writeFileSync(blogHttpPath,fs.readFileSync(blogHttpPath,'utf8').replace("if(isset($query['tool'])&&!in_array($query['tool'],['paint','space','palette','surface'],true))","if(isset($query['tool']))").replace('Özgün SEXOGATE yaşam alanı ve yenileme rehberleri','SEXOGATE ürün seçimi, bakım ve mahremiyet rehberleri'));
const seoPath=path.join(bundle,'private/seo.php');let seo=fs.readFileSync(seoPath,'utf8');
const phpJson=value=>`json_decode('${JSON.stringify(value).replaceAll('\\','\\\\').replaceAll("'","\\'")}',true,512,JSON_THROW_ON_ERROR)`;
const seoCopy=Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,{catalogue:data[locale].collection,about:data[locale].body}]));
seo=seo.replace('];return nodenoLocaleCopy($copy,$locale);',`];foreach(${phpJson(seoCopy)} as $code=>$theme)$copy[$code]=array_replace($copy[$code],$theme);return nodenoLocaleCopy($copy,$locale);`);
const seoInfo=Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,{help:[data[locale].care,data[locale].choose],shipping:[data[locale].shipping,data[locale].delivery]}]));
seo=seo.replace('return nodenoLocaleCopy($copy,$locale)[$kind];',`$copy=${phpJson(seoInfo)};return nodenoLocaleCopy($copy,$locale)[$kind];`);
const homeTitle="['tr'=>'Mobilya ve ahşap ürünler','en'=>'Furniture and wooden components','ru'=>'Мебель и деревянные комплектующие','ar'=>'أثاث ومكونات خشبية']";
if(!seo.includes(homeTitle))throw new Error('SEO_HOME_TITLE_SOURCE_CHANGED');
seo=seo.replace(homeTitle,phpJson(Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,data[locale].slogan]))));fs.writeFileSync(seoPath,seo);
const clientSeoPath=path.join(bundle,'public/seo-core.js');let clientSeo=fs.readFileSync(clientSeoPath,'utf8'),clientChanges=0;
clientSeo=clientSeo.replace(/const SEO_INFO=localeCopy\(\{[\s\S]*?\n\}\);/,()=>{clientChanges++;return `const SEO_INFO=localeCopy(${JSON.stringify(seoInfo)});`;});
const clientCopy=Object.fromEntries(Object.entries(seoCopy).map(([locale,copy])=>[locale,{...copy,collections:data[locale].collection}]));
clientSeo=clientSeo.replace(/const SEO_COPY=localeCopy\((\{[\s\S]*?\n\})\);/,(_,literal)=>{clientChanges++;return `const SEO_COPY=localeCopy(Object.fromEntries(Object.entries(${literal}).map(([locale,copy])=>[locale,{...copy,...(${JSON.stringify(clientCopy)})[locale]}])));`;});
const clientHomeTitle="{tr:'Mobilya ve ahşap ürünler',en:'Furniture and wooden components',ru:'Мебель и деревянные комплектующие',ar:'أثاث ومكونات خشبية'}";
if(clientChanges!==2||!clientSeo.includes(clientHomeTitle))throw new Error('CLIENT_SEO_SOURCE_CHANGED');
clientSeo=clientSeo.replace(clientHomeTitle,JSON.stringify(Object.fromEntries(['tr','en','ru','ar'].map(locale=>[locale,data[locale].slogan]))));fs.writeFileSync(clientSeoPath,clientSeo);
// Her yeni tema, mevcut iPhone/PWA oturumlarının eski modüllerini kullanmasını önler.
function visit(folder){for(const item of fs.readdirSync(folder,{withFileTypes:true})){const p=path.join(folder,item.name);if(item.isDirectory())visit(p);else if(/\.(?:js|css|html|php|json)$/.test(p)){let text=fs.readFileSync(p,'utf8');text=text.replace(/\?v=[A-Za-z0-9_.-]+/g,'?v=sexogate-'+version).replace(/const defaultRevision='[^']+'/,"const defaultRevision='sexogate-"+version+"'");fs.writeFileSync(p,text);}}}
visit(path.join(bundle,'public'));visit(path.join(bundle,'private'));
for(const name of ['index.html','admin.html','blog-admin.html'])for(const folder of ['public','private']){const p=path.join(bundle,folder,name);if(fs.existsSync(p))fs.writeFileSync(p,fs.readFileSync(p,'utf8').replaceAll('/sexogate.css"','/sexogate.css?v=sexogate-'+version+'"').replaceAll('/sexogate-branding.js"','/sexogate-branding.js?v=sexogate-'+version+'"'));}
for(const [file,name]of [['i18n.js','copy'],['shop-i18n.js','shopCopy'],['shopping-i18n.js','shoppingCopy']]){const module=await import(pathToFileURL(path.join(bundle,'public',file)));if(module[name].tr.heroTitle!==data.tr.slogan||module[name].en.shipping!==data.en.shipping)throw new Error('ADULT_COPY_INITIALIZATION_FAILED');}
const clientSeoModule=await import(pathToFileURL(clientSeoPath)),catalog=JSON.parse(fs.readFileSync(path.join(bundle,'private/catalog.json'),'utf8')),config=JSON.parse(fs.readFileSync(path.join(bundle,'private/config.json'),'utf8'));
for(const locale of ['tr','en','ru','ar']){const page=clientSeoModule.seoPage(catalog,config,new URL('https://sexogate.com/?lang='+locale));if(!page.title.startsWith(data[locale].slogan+' |')||page.description!==data[locale].body)throw new Error('CLIENT_ADULT_METADATA_FAILED');}
console.log(JSON.stringify({adultTheme:true,ageGate:true,worldMap:false,copyLocales:Object.keys(data).length,assetVersion:version}));
