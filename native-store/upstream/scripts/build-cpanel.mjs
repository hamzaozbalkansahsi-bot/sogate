import {loadNativeDictionaries} from '../lib/native-locales.mjs';
import './build-date-time-regions.mjs';
import {loadSupplierCatalog} from '../lib/supplier-catalog.mjs';
import {seoPage,seoDocument} from '../lib/seo.mjs';
import {readFile,writeFile,mkdir,copyFile,readdir,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {safeMediaUrl} from '../lib/server.mjs';
import {loadMediaApprovals} from '../lib/media-approvals.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const release=path.resolve(process.env.NODENO_CPANEL_OUTPUT||path.join(root,'artifacts/cpanel-release'));
const stage=release+'.staging';
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const safeExtensions=new Set(['.html','.js','.css','.svg','.json','.webmanifest','.txt','.woff','.woff2','.ttf','.ico','.png','.jpg','.jpeg','.webp']);
function validateBlog(directory,source=false){
 const python=process.env.NODENO_PYTHON||(process.platform==='win32'?'python':'python3');
 const result=spawnSync(python,[path.join(root,'lib/blog_publication.py'),source?'--source-root':'--release',directory],{encoding:'utf8',maxBuffer:8192,windowsHide:true});
 if(result.error||result.status!==0)throw new Error('Blog publication gate: '+(result.error?'validator_unavailable':result.stderr.trim()||'validation_failed'));
}
validateBlog(root,true);
const worker=(await import(pathToFileURL(path.join(root,'dist/server/index.js')).href)).default;
if(typeof worker?.fetch!=='function') throw new Error('Run npm run build before packaging cPanel.');
const canonical={};
for(const name of ['catalog','config']) {
 const response=await worker.fetch(new Request('https://nodeno-build.invalid/api/'+name));
 if(!response.ok) throw new Error('Built Worker API is unavailable: '+name);
 canonical[name]=await response.text();
}
const catalog=JSON.parse(canonical.catalog),config=JSON.parse(canonical.config);
if(!catalog.products?.length||!catalog.meta?.releaseHash||config.checkoutEnabled!==false||config.mode!=='catalogue') throw new Error('Built Worker is not a verified catalogue release.');
const source=JSON.parse(await readFile(path.join(root,'data/catalog-source.json'),'utf8'));
const sourceById=new Map(source.products.map(product=>[String(product.id),product]));
const media={};
for(const product of catalog.products) {
 if(['door','door-profile','cabinet-front','cabinet-profile','supplier-item'].includes(product.productType))continue;
 if(!/^[A-Za-z0-9_-]+$/.test(product.id)||media[product.id]) throw new Error('Invalid catalogue product ID.');
 const original=sourceById.get(product.id);
 if(!original) throw new Error('Built Worker/source catalogue mismatch.');
 media[product.id]=(original.images||[]).filter(safeMediaUrl);
 if(product.images.length!==media[product.id].length||product.images.some((image,index)=>image!==`/media/${product.id}/${index}`)) throw new Error('Built Worker/source media indexes differ.');
 for(const url of media[product.id]) {
  if(new URL(url).hostname!=='witcdn.adoremobilya.com') throw new Error('cPanel source images must use the verified supplier CDN.');
 }
}
if(sourceById.size!==Object.keys(media).length) throw new Error('Built Worker/source product count differs.');
const approvals=await loadMediaApprovals({root,media,fixture:process.env.NODENO_MEDIA_APPROVAL_FIXTURE||false,isolatedOutput:release});
const native=await loadNativeDictionaries(root,{testOnly:approvals.testOnly});
if(!approvals.testOnly&&catalog.meta.testOnly)throw new Error('A regression fixture is not a production Worker build.');
if(!approvals.testOnly&&catalog.meta.mediaVersion!==approvals.mediaVersion) throw new Error('Built Worker media approvals differ; rebuild the Worker after completing image approvals.');
for(const target of [release,stage]) {
 if(path.dirname(target)!==path.resolve(root,'artifacts')||!path.basename(target).startsWith('cpanel-release')) throw new Error('Unsafe output directory.');
}
await rm(stage,{recursive:true,force:true});
await mkdir(path.join(stage,'public'),{recursive:true});
await mkdir(path.join(stage,'private/cache'),{recursive:true});
const hashes={};
async function output(relative,bytes) {
 const target=path.join(stage,relative);
 await mkdir(path.dirname(target),{recursive:true});
 await writeFile(target,bytes);
 hashes[relative]=sha256(bytes);
}
await output('public/index.php',await readFile(path.join(root,'hosting/index.php')));
await output('public/.htaccess',await readFile(path.join(root,'hosting/.htaccess')));
await output('private/account.php',await readFile(path.join(root,'hosting/account.php')));
for(const filename of ['social-campaigns.php','social-engine.php','social-providers.php','social-media.php','social-worker.php','social-admin.php'])await output('private/'+filename,await readFile(path.join(root,'hosting',filename)));
for(const filename of ['blog-store.php','blog-worker.php','blog-admin.php','blog-http.php','blog.php','blog-i18n.php','blog-admin.html','blog-surface.php','date-time.php'])await output('private/'+filename,await readFile(path.join(root,'hosting',filename)));
await output('private/blog-bank.json',await readFile(path.join(root,'data/blog-bank.json')));
await output('private/date-time-regions.json',await readFile(path.join(root,'data/date-time-regions.json')));
for(const name of ['blog-images.json','blog-images.bin'])await output('private/'+name,await readFile(path.join(root,'data',name)));
for(const filename of ['legal.php','payment-documents.php','membership-legal.php','localization.php'])await output('private/'+filename,await readFile(path.join(root,'hosting',filename)));
for(const locale of (approvals.testOnly?['tr','en','ru','ar']:['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']))await output('private/site-documents.'+locale+'.json',await readFile(path.join(root,'data/legal/site-documents.'+locale+'.json')));
for(const filename of ['oauth-jwt.php','social-auth.php','social-provider.php','social-http.php','collections.php','seo.php','control-store.php','control-auth.php','control-http.php','control-catalog.php','control-operations.php','control-marketing.php','control-kolaybi.php','control-analytics.php','control-indexnow.php','search-notifications.php','wholesale.php','furniture-sets.php','suppliers.php','supplier-products.php'])await output('private/'+filename,await readFile(path.join(root,'hosting',filename)));
for(const filename of ['door-commerce.php','exchange-rates.php','cabinet-fronts.php','payment-core.php','payment-store.php','payment-stripe.php','payment-admin.php','payments.php','supplier-watch.php'])await output('private/'+filename,await readFile(path.join(root,'hosting',filename)));
let supplierImageHashes={};
// The legacy raster fixture replaces only Adore image evidence. Supplier records in
// the canonical Worker still require their actual reviewed descriptions and media.
if(catalog.products.some(p=>p.productType==='supplier-item')){
 const suppliers=await loadSupplierCatalog(root);const builtSuppliers=catalog.products.filter(p=>p.productType==='supplier-item');
 if(JSON.stringify(builtSuppliers)!==JSON.stringify(suppliers.data.products))throw new Error('Supplier Worker/catalogue differs from the reviewed projection.');
 supplierImageHashes=Object.fromEntries(suppliers.data.products.flatMap(p=>p.images.map(url=>[url,url.split('/').at(-1).split('.')[0]])));
 for(const name of ['supplier-details.json','supplier-details.bin','supplier-media-approved.json'])await output('private/'+name,await readFile(path.join(root,'data',name)));
}
if(catalog.products.some(p=>['door','door-profile','cabinet-front','cabinet-profile'].includes(p.productType)))for(const name of ['door-catalog.json','cabinet-fronts.json'])await output('private/'+name,await readFile(path.join(root,'data',name)));
await output('private/supplier-catalog.json',await readFile(path.join(root,'data/supplier-catalog.json')));
for(const locale of Object.keys(native.dictionaries))for(const suffix of ['','.catalogue'])await output('private/locale.'+locale+suffix+'.json',await readFile(path.join(root,'web/locales',locale+suffix+'.json')));
await output('private/catalog.json',canonical.catalog);
await output('private/config.json',canonical.config);
await output('private/media.json',JSON.stringify(media));
await output('private/media-approved.json',JSON.stringify(approvals.manifest));
await output('private/visitor-market.php',await readFile(path.join(root,'hosting/visitor-market.php')));
const geo=JSON.parse(await readFile(path.join(root,'data/geo/geo-license.json'),'utf8'));
for(const filename of ['geo-v4.bin','geo-v6.bin']){
 const bytes=await readFile(path.join(root,'data/geo',filename));
 const recordSize=filename==='geo-v4.bin'?10:34,proof=geo.files?.[filename];
 if(!proof||proof.sha256!==sha256(bytes)||proof.bytes!==bytes.length||proof.records*recordSize!==bytes.length)throw new Error('Country database proof mismatch: '+filename);
 await output('private/'+filename,bytes);
}
await output('private/geo-license.json',JSON.stringify(geo));
async function copyWeb(directory,prefix='') {
 for(const entry of await readdir(directory,{withFileTypes:true})) {
  if(entry.name.startsWith('.')) throw new Error('Hidden web assets are not deployable.');
  if(entry.isSymbolicLink()) throw new Error('Web assets cannot contain symlinks.');
  const relative=prefix+entry.name,filename=path.join(directory,entry.name);
  if(entry.isDirectory()) {if(relative==='assets/blog')continue;await copyWeb(filename,relative+'/');continue;}
  if(!entry.isFile()||!safeExtensions.has(path.extname(entry.name).toLowerCase())) throw new Error('Unsupported public asset: '+relative);
  const bytes=await readFile(filename);
  if(relative.startsWith('assets/suppliers/')){
   if(sha256(bytes)!==supplierImageHashes['/'+relative])throw new Error('Unreviewed supplier raster: '+relative);
   await output('public/'+relative,bytes);continue;
  }
  const response=await worker.fetch(new Request('https://nodeno-build.invalid/'+(relative==='index.html'?'':relative)));
  if(!response.ok) throw new Error('Built Worker does not contain '+relative+'; rebuild it first.');
  if(relative==='index.html') {
   const html=(await response.text()).replace(/<script nonce="[a-f0-9]{32}"/g,'<script');
   const expectedHtml=seoDocument(bytes.toString('utf8'),seoPage(catalog,config,new URL('https://nodeno-build.invalid/')));
   if(html!==expectedHtml) throw new Error('Built Worker HTML differs from the reviewed SEO projection; run npm run build.');
  } else if(!bytes.equals(Buffer.from(await response.arrayBuffer()))) throw new Error('Built Worker asset differs: '+relative+'; run npm run build.');
  await output(relative==='index.html'?'private/index.html':'public/'+relative,bytes);
 }
}
await copyWeb(path.join(root,'web'));
// Validate the actual copied bytes again before replacing an existing package.
validateBlog(stage);
// Sort by code points, matching PHP ksort and the published verification contract.
const files=Object.fromEntries(Object.keys(hashes).sort().map(key=>[key,hashes[key]]));
const fingerprint=createHash('sha256');
for(const [filename,hash] of Object.entries(files)) fingerprint.update(filename+'\0'+hash+'\0');
const manifest={schema:1,runtime:'php',releaseHash:fingerprint.digest('hex'),workerReleaseHash:catalog.meta.releaseHash,products:catalog.products.length,categories:catalog.categories.length,checkoutEnabled:false,driveConnected:false,mediaSource:'approved-only',mediaVersion:approvals.mediaVersion,mediaApproved:approvals.manifest.referenceCount,mediaCounts:approvals.manifest.counts,...(approvals.testOnly?{testOnly:true}:{}),files};
await writeFile(path.join(stage,'private/release.json'),JSON.stringify(manifest,null,2)+'\n');
// Clear only the validated local build directory; deployment must preserve its own media cache.
await rm(release,{recursive:true,force:true});
await mkdir(release,{recursive:true});
async function copyStage(directory,prefix='') {
 for(const entry of await readdir(directory,{withFileTypes:true})) {
  const relative=prefix+entry.name,target=path.join(release,relative);
  if(entry.isDirectory()) {await mkdir(target,{recursive:true});await copyStage(path.join(directory,entry.name),relative+'/');}
  else await copyFile(path.join(directory,entry.name),target);
 }
}
await copyStage(stage);
await rm(stage,{recursive:true,force:true});
console.log(JSON.stringify({built:true,runtime:'php',products:manifest.products,categories:manifest.categories,releaseHash:manifest.releaseHash,output:release,driveConnected:false}));
