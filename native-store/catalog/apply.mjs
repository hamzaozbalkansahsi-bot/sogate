/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/catalog/apply.mjs
 * Açıklama   : Kaynak snapshot'ını değiştirmeden katalog alanlarını ve yönetim yüklemesini derlemeye bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import{fileURLToPath}from'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]);if(!bundle.includes('native-stage-'))throw Error('CATALOG_BUILD_SCOPE');
const templates=JSON.parse(fs.readFileSync(path.join(root,'seo-copy.json'),'utf8'));fs.copyFileSync(path.join(root,'seo-copy.json'),path.join(bundle,'private/catalog-seo-copy.json'));
for(const [source,target]of [['catalog.php','private/sexogate-catalog.php'],['admin-catalog.js','public/sexogate-catalog.js'],['admin-catalog.css','public/sexogate-catalog.css']])fs.copyFileSync(path.join(root,source),path.join(bundle,target));
function edit(file,from,to){const p=path.join(bundle,'private',file),source=fs.readFileSync(p,'utf8');if(source.split(from).length!==2)throw Error('CATALOG_HOOK_CHANGED:'+file);fs.writeFileSync(p,source.replace(from,to));}
edit('control-catalog.php',"require_once __DIR__.'/suppliers.php';","require_once __DIR__.'/suppliers.php';\nrequire_once __DIR__.'/sexogate-catalog.php';");
edit('control-catalog.php','return array_merge($definitions,nodenoWholesaleDefinitions($f));','return sexogateCatalogDefinitions(array_merge($definitions,nodenoWholesaleDefinitions($f)));');
edit('control-catalog.php',"$data=$overrides[$p['id']]??[];","$data=$overrides[$p['id']]??[];$p=sexogateCatalogProjection($p,$data);if(sexogateCatalogManaged($p)&&!$p['published'])continue;");
edit('control-catalog.php',"$json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);","sexogateCatalogValidate($resource,$id,$data,$catalog,$ctx['db']);$json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);");
edit('control-catalog.php',"if($published)nodenoControlNativePublication($resource,$old['data']);","if($published){sexogateCatalogValidate($resource,$id,$old['data'],$catalog,$ctx['db']);nodenoControlNativePublication($resource,$old['data']);}");
edit('control-catalog.php',"return ['record'=>$record,'values'=>$values,'inheritedFields'=>$inherited];","if($resource==='products')$values=sexogateCatalogEditor($product,$values,__DIR__);return ['record'=>$record,'values'=>$values,'inheritedFields'=>$inherited];");
edit('control-http.php',"if($result===null)$result=nodenoControlDispatch($ctx,$route,$method,$body,$catalog,$config);","if($result===null)$result=sexogateCatalogAdmin($ctx,$route,$method,$body,$catalog,$config);if($result===null)$result=nodenoControlDispatch($ctx,$route,$method,$body,$catalog,$config);");
edit('control-http.php',"'sourcePriceMinor'=>$p['salePriceMinor']??null","'sourcePriceMinor'=>$p['privateRetailReference']??$p['salePriceMinor']??null");
const html=path.join(bundle,'public/admin.html');fs.writeFileSync(html,fs.readFileSync(html,'utf8').replace('</head>','<link rel="stylesheet" href="/sexogate-catalog.css"><script defer src="/sexogate-catalog.js"></script></head>'));
const seoPath=path.join(bundle,'private/seo.php');let seo=fs.readFileSync(seoPath,'utf8');const intro=/\$intro=nodenoLocaleCopy\(\['tr'=>'SEXOGATE '\.[^\n]+\);/;
if(!intro.test(seo))throw Error('CATEGORY_SEO_HOOK_CHANGED');seo=seo.replace(intro,"$templates=json_decode((string)file_get_contents(__DIR__.'/catalog-seo-copy.json'),true,32,JSON_THROW_ON_ERROR);$intro=strtr($templates[$locale],['{title}'=>$title,'{count}'=>(string)$count]);");
const productBrand="$description=nodenoSeoDescription($product,$locale,$catalog);";const productFunction=seo.indexOf('function nodenoSeoProductData');const descriptionAt=seo.indexOf(productBrand,productFunction);if(descriptionAt<0)throw Error('PRODUCT_BRAND_HOOK_CHANGED');seo=seo.slice(0,descriptionAt)+"if(($product['catalogOrigin']??'')==='sexogate-suppliers-v1'){if(!empty($product['brand']))$data['brand']=['@type'=>'Brand','name'=>$product['brand']];else unset($data['brand']);}"+seo.slice(descriptionAt);fs.writeFileSync(seoPath,seo);
const clientPath=path.join(bundle,'public/seo-core.js');let client=fs.readFileSync(clientPath,'utf8');const clientIntro=/const intro=localeCopy\(\{tr:'(?:NODENO|SEXOGATE) '\+title[^\n]+?\}\)\[locale\];/;if(!clientIntro.test(client))throw Error('CLIENT_CATEGORY_SEO_HOOK_CHANGED');client=client.replace(clientIntro,'const intro='+JSON.stringify(templates)+"[locale].replaceAll('{title}',title).replaceAll('{count}',String(listingProducts.length));");
const dataEnd=client.indexOf('\n',client.indexOf("const data={'@type':'Product'"));if(dataEnd<0)throw Error('CLIENT_PRODUCT_BRAND_HOOK_CHANGED');client=client.slice(0,dataEnd)+"\n if(product.catalogOrigin==='sexogate-suppliers-v1'){if(product.brand)data.brand={'@type':'Brand',name:product.brand};else delete data.brand;}"+client.slice(dataEnd);fs.writeFileSync(clientPath,client);
const entryPath=path.join(bundle,'public/index.php');let entry=fs.readFileSync(entryPath,'utf8');const rawCatalog="$state['revision']>0||($path==='/api/config'";if(!entry.includes(rawCatalog))throw Error('CATALOG_PRIVACY_HOOK_CHANGED');entry=entry.replace(rawCatalog,"$state['revision']>0||($path==='/api/catalog'&&($state['sourceCatalog']['catalogOrigin']??'')==='sexogate-suppliers-v1')||($path==='/api/config'");fs.writeFileSync(entryPath,entry);
console.log(JSON.stringify({catalogHooks:true,upstreamSnapshotChanged:false}));
