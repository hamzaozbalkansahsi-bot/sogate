import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, readdir, stat, mkdtemp, mkdir, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';

const root=fileURLToPath(new URL('../',import.meta.url));
await mkdir(path.join(root,'artifacts'),{recursive:true});
const release=await mkdtemp(path.join(root,'artifacts/cpanel-release-test-'));
const buildOptions={cwd:root,encoding:'utf8',env:{...process.env,NODENO_CPANEL_OUTPUT:release,NODENO_MEDIA_APPROVAL_FIXTURE:'raster-test-v1'}};
test.after(async()=>{
 for(const directory of [release,release+'.staging']) {
  if(path.dirname(directory)!==path.resolve(root,'artifacts')||!path.basename(directory).startsWith('cpanel-release-test-')) throw new Error('Unsafe test cleanup path');
  await rm(directory,{recursive:true,force:true});
 }
});
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
async function files(directory,prefix='') {
 const result=[];
 for(const entry of await readdir(directory,{withFileTypes:true})) {
  const relative=prefix+entry.name;
  if(entry.isDirectory()) result.push(...await files(path.join(directory,entry.name),relative+'/'));
  else result.push(relative);
 }
 return result.sort();
}

test('cPanel build packages canonical Worker API responses and byte-exact web assets outside the private boundary',async()=>{
 const build=spawnSync(process.execPath,['scripts/build-cpanel.mjs'],buildOptions);
 assert.equal(build.status,0,build.stderr||build.stdout);
 const worker=(await import(pathToFileURL(path.join(root,'dist/server/index.js')).href)).default;
 for(const endpoint of ['catalog','config']) {
  const response=await worker.fetch(new Request('https://store.invalid/api/'+endpoint));
  assert.equal(await readFile(path.join(release,'private',endpoint+'.json'),'utf8'),await response.text());
 }
 const catalog=JSON.parse(await readFile(path.join(release,'private/catalog.json'),'utf8'));
 const source=JSON.parse(await readFile(path.join(root,'data/catalog-source.json'),'utf8'));
 const media=JSON.parse(await readFile(path.join(release,'private/media.json'),'utf8'));
 const sourceIds=new Set(source.products.map(p=>String(p.id)));
 const projection=JSON.parse(await readFile(path.join(root,'data/supplier-storefront.json'),'utf8'));
 const supplierById=new Map(projection.products.map(p=>[p.id,p]));
 const supplierMedia=JSON.parse(await readFile(path.join(release,'private/supplier-media-approved.json'),'utf8'));
 assert.equal(supplierMedia.publicationReady,true);assert.equal(supplierMedia.testOnly,false);
 assert.equal(catalog.products.filter(p=>p.productType==='supplier-item').length,supplierById.size);
 assert.equal(catalog.products.filter(p=>sourceIds.has(p.id)).length,source.products.length);
 for(const product of catalog.products) {
  if(product.productType==='supplier-item'){
   assert.deepEqual(product,supplierById.get(product.id),'Supplier rows must match the reviewed projection');
   for(const [index,image]of product.images.entries()){
    assert.equal(supplierMedia.references[product.id+':'+index],image);
    const row=supplierMedia.images[image];assert.equal(row.visualReview,true);
    assert.equal(digest(await readFile(path.join(release,'public',image))),row.outputSha256);
   }
   continue;
  }
  if(!sourceIds.has(product.id)){assert.ok(['door','door-profile','cabinet-front','cabinet-profile'].includes(product.productType));assert.ok(product.images.length);for(const [index,image]of product.images.entries())if(image!==`/media/${product.id}/${index}`)assert.match(image,/^\/assets\/(doors|fronts)\/[a-f0-9]{64}\.(jpg|png|webp)$/);continue;}
  const original=source.products.find(item=>String(item.id)===product.id);
  assert.equal(media[product.id].length,product.images.length);
  for(let i=0;i<product.images.length;i++) {
   assert.equal(product.images[i],`/media/${product.id}/${i}`);
   assert.equal(media[product.id][i],original.images[i]);
   assert.equal(new URL(media[product.id][i]).hostname,'witcdn.adoremobilya.com');
  }
 }
 const publicFiles=await files(path.join(release,'public'));
 assert.ok(publicFiles.includes('index.php'));
 assert.ok(publicFiles.includes('.htaccess'));
 for(const forbidden of ['index.html','catalog.json','config.json','media.json','release.json','cache','private']) assert.ok(!publicFiles.some(file=>file===forbidden||file.startsWith(forbidden+'/')),forbidden);
 for(const file of await files(path.join(root,'web'))) {
  const sourceBytes=await readFile(path.join(root,'web',file));
  const packaged=await readFile(path.join(release,file==='index.html'?'private/index.html':'public/'+file));
  assert.deepEqual(packaged,sourceBytes,file);
 }
 assert.ok((await stat(path.join(release,'private/cache'))).isDirectory());
 const config=JSON.parse(await readFile(path.join(release,'private/config.json'),'utf8'));
 assert.equal(config.checkoutEnabled,false);
 assert.equal(config.mode,'catalogue');
});

test('PHP release fingerprint covers executable, web bytes and private data deterministically',async()=>{
 const manifest=JSON.parse(await readFile(path.join(release,'private/release.json'),'utf8'));
 assert.equal(manifest.runtime,'php');
 assert.match(manifest.releaseHash,/^[a-f0-9]{64}$/);
 assert.equal(manifest.testOnly,true);
 const expectedPaths=[...(await files(path.join(release,'public'))).map(file=>'public/'+file),...['supplier-details.json','supplier-details.bin','supplier-media-approved.json','door-catalog.json','cabinet-fronts.json','legal.php','payment-documents.php','membership-legal.php','site-documents.tr.json','site-documents.en.json','site-documents.ru.json','site-documents.ar.json','catalog.json','config.json','media.json','media-approved.json','index.html','account.php','oauth-jwt.php','social-auth.php','social-provider.php','social-http.php','collections.php','seo.php','control-store.php','control-auth.php','control-http.php','control-catalog.php','control-operations.php','control-marketing.php','control-kolaybi.php','control-analytics.php','control-indexnow.php','wholesale.php','furniture-sets.php','suppliers.php','supplier-products.php','supplier-catalog.json','door-commerce.php','exchange-rates.php','cabinet-fronts.php','payment-core.php','payment-store.php','payment-stripe.php','payment-admin.php','payments.php','visitor-market.php','geo-v4.bin','geo-v6.bin','geo-license.json','social-campaigns.php','social-engine.php','social-providers.php','social-media.php','social-worker.php','social-admin.php'].map(file=>'private/'+file)].sort();
 const nativePaths=['de','az','kk','tk','uz','ky','fa'].flatMap(locale=>['private/locale.'+locale+'.json','private/locale.'+locale+'.catalogue.json']);
 expectedPaths.push('private/localization.php',...nativePaths);expectedPaths.sort();
 assert.deepEqual(Object.keys(manifest.files),expectedPaths);
 const hash=createHash('sha256');
 for(const file of expectedPaths) {
  const sha256=digest(await readFile(path.join(release,file)));
  assert.equal(manifest.files[file],sha256,file);
  hash.update(file+'\0'+sha256+'\0');
 }
 assert.equal(hash.digest('hex'),manifest.releaseHash);
 assert.notEqual(manifest.releaseHash,manifest.workerReleaseHash);
 const previous=await readFile(path.join(release,'private/release.json'),'utf8');
 const rebuild=spawnSync(process.execPath,['scripts/build-cpanel.mjs'],buildOptions);
 assert.equal(rebuild.status,0,rebuild.stderr);
 assert.equal(await readFile(path.join(release,'private/release.json'),'utf8'),previous);
});
