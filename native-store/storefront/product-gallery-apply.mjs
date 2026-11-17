/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-gallery-apply.mjs
 * Açıklama   : Onaylı ek galeri metadata ve medya erişimini türetilmiş pakete bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath}from'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||'');if(!bundle.includes('native-stage-'))throw Error('GALLERY_BUILD_SCOPE');
const data=JSON.parse(fs.readFileSync(path.join(root,'product-gallery-data.json'),'utf8')),catalog=JSON.parse(fs.readFileSync(path.join(bundle,'private/catalog.json'),'utf8'));
if(data.schema!==1||data.sourceDataset!==catalog.dataset||!data.products||Array.isArray(data.products))throw Error('GALLERY_SOURCE_DATASET_MISMATCH');
const products=new Map(catalog.products.map(p=>[p.id,p])),workCache=new Map(),bindings=[];
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
function normalizedHashes(value){if(!value||typeof value!=='object'||Array.isArray(value))throw Error('GALLERY_BASE_PROVENANCE_INVALID');const entries=Object.entries(value);if(entries.some(([key,value])=>!/^(0|[1-9][0-9]*)$/.test(key)||!hash(value)))throw Error('GALLERY_BASE_PROVENANCE_INVALID');return Object.fromEntries(entries.sort((a,b)=>Number(a[0])-Number(b[0])));}
for(const[id,row]of Object.entries(data.products)){
 if(!products.has(id)||products.get(id).code!==row.code||!/^sg_ty_[a-f0-9]{16}$/.test(id))throw Error('GALLERY_PRODUCT_IDENTITY_MISMATCH');
 const shard=id.slice('sg_ty_'.length,'sg_ty_'.length+2),file=path.join(bundle,'private/catalog-workbench',shard+'.json');if(!workCache.has(file))workCache.set(file,JSON.parse(fs.readFileSync(file,'utf8')));const work=workCache.get(file)[id],product=products.get(id);
 if(!work||!hash(work.source?.htmlSha256)||row.sourceSha256!==work.source.htmlSha256||!Array.isArray(work.media)||!Array.isArray(work.sourceImages)||!Array.isArray(product.images)||work.media.length!==product.images.length)throw Error('GALLERY_SOURCE_PROVENANCE_MISMATCH');
 const expected=Object.fromEntries(work.media.map((image,index)=>{if(!hash(image.sha256))throw Error('GALLERY_BASE_PROVENANCE_INVALID');return[String(index),image.sha256];}));if(JSON.stringify(normalizedHashes(row.baseHashes))!==JSON.stringify(expected))throw Error('GALLERY_BASE_PROVENANCE_MISMATCH');
 if(!Array.isArray(row.images))throw Error('GALLERY_IMAGE_PROVENANCE_MISMATCH');
 for(const image of row.images)if(!image||image.approved!==true||image.sourceSha256!==row.sourceSha256||!Number.isInteger(image.sourceIndex)||image.sourceIndex<0||typeof image.sourceUrl!=='string'||image.sourceUrl!==work.sourceImages[image.sourceIndex]||!hash(image.sha256)||Object.values(expected).includes(image.sha256))throw Error('GALLERY_IMAGE_PROVENANCE_MISMATCH');
 bindings.push([id,{schema:1,sourceDataset:catalog.dataset,sourceSha256:work.source.htmlSha256,baseHashes:expected,sourceImages:work.sourceImages,product}]);
}
const bindingDirectory=path.join(bundle,'private/product-gallery-bindings');fs.mkdirSync(bindingDirectory,{recursive:true});for(const[id,binding]of bindings)fs.writeFileSync(path.join(bindingDirectory,id+'.json'),JSON.stringify(binding));
for(const[from,to]of[['product-gallery.php','private/sexogate-product-gallery.php'],['product-gallery-data.json','private/sexogate-product-gallery-data.json']])fs.copyFileSync(path.join(root,from),path.join(bundle,to));
function edit(name,from,to){const file=path.join(bundle,name),text=fs.readFileSync(file,'utf8');if(text.split(from).length!==2)throw Error('GALLERY_HOOK_CHANGED:'+name);fs.writeFileSync(file,text.replace(from,to));}
edit('private/control-catalog.php',"require_once __DIR__.'/sexogate-storefront-content.php';","require_once __DIR__.'/sexogate-storefront-content.php';\nrequire_once __DIR__.'/sexogate-product-gallery.php';");
edit('private/control-catalog.php','$products[]=sexogateStorefrontProduct($p);',"$products[]=sgProductGalleryProject(sexogateStorefrontContextProduct($p),($data['extraGalleryEnabled']??true)===true);");
edit('private/sexogate-catalog.php','return $fields;',"$fields['extraGalleryEnabled']=['label'=>'İncelenmiş ek galeri fotoğraflarını göster','type'=>'boolean'];return $fields;");
edit('private/sexogate-catalog.php','function sexogateCatalogEditor(array $product,array $values,string $private):array{',"function sexogateCatalogEditor(array $product,array $values,string $private):array{\n $values['extraGalleryEnabled']=$values['extraGalleryEnabled']??true;");
edit('deploy/dispatcher.php',"if(str_starts_with($relative,'/media/sg_')", "if(preg_match('~^/media/sg_ty_[a-f0-9]{16}/gallery/~D',$relative)){require_once $private.'/sexogate-product-gallery.php';sgProductGalleryHandle($private,$relative,$_SERVER['REQUEST_METHOD']);exit;}\n if(str_starts_with($relative,'/media/sg_')");
edit('public/app.js',"const src=p.images?.[index];let imageUrl='';","const src=p.images?.[index];let imageUrl='';\n if(sgCatalogImagePath(p,src))imageUrl=src;");
const mediaImport="import {catalogImagePath as sgCatalogImagePath} from './sexogate-gallery-experience-core.js?v=storefront';\n";
for(const name of['public/app.js','public/seo-core.js']){const file=path.join(bundle,name);fs.writeFileSync(file,mediaImport+fs.readFileSync(file,'utf8'));}
const clientSeo=path.join(bundle,'public/seo-core.js');let client=fs.readFileSync(clientSeo,'utf8');
const clientImages=/function seoImages\(product,catalog\)\{[^\n]+\}/g;
if([...client.matchAll(clientImages)].length!==1)throw Error('GALLERY_CLIENT_SEO_HOOK_CHANGED');
client=client.replace(clientImages,`function seoImages(product,catalog){const version=product.productType?.startsWith('door')?catalog.meta?.doorCatalogVersion||catalog.meta?.mediaVersion:product.productType?.startsWith('cabinet')?catalog.meta?.frontCatalogVersion||catalog.meta?.mediaVersion:catalog.meta?.mediaVersion;return(product.images||[]).filter(src=>sgCatalogImagePath(product,src)||(product.productType==='supplier-item'&&typeof src==='string'&&/^\\/assets\\/suppliers\\/[a-f0-9]{64}\\.(jpg|png|webp)$/.test(src))).map(src=>(sgCatalogImagePath(product,src)?new URL(src,SEO_ORIGIN).href:SEO_ORIGIN+src)+(!src.includes('/gallery/')&&src.startsWith('/media/')&&/^[a-f0-9]{64}$/.test(version||'')?'?v='+version:''));}`);fs.writeFileSync(clientSeo,client);
edit('private/seo.php',"  elseif($type==='supplier-item'", "  elseif(preg_match('/^sg_ty_[a-f0-9]{16}$/D',(string)$product['id'])&&preg_match('~^/media/'.preg_quote((string)$product['id'],'~').'/gallery/[a-f0-9]{64}$~D',$src))$result[]=NODENO_SEO_ORIGIN.$src;\n  elseif($type==='supplier-item'");
console.log(JSON.stringify({reviewedExtraGallery:true,privateOriginalMedia:true,sourceSnapshotChanged:false,extraGalleryProducts:Object.keys(data.products).length}));
