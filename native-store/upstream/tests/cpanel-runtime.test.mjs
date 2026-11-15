import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdtemp,mkdir,rm,rename} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import {fileURLToPath} from 'node:url';

const root=fileURLToPath(new URL('../',import.meta.url));
const php=process.env.PHP_BINARY||'php';
const probe=spawnSync(php,['--version'],{encoding:'utf8'});
const missing=probe.status!==0?'PHP runtime unavailable; PHP integration has not been verified':false;
async function fetchAndDrain(url,options) {
 const response=await fetch(url,options);
 // Status/header-only assertions must still release the HTTP response stream.
 // PHP closes these connections; an unread large body leaves Undici paused.
 await response.arrayBuffer();
 return response;
}
async function removeTestDirectory(directory,parent,prefix) {
 if(path.dirname(path.resolve(directory))!==path.resolve(parent)||!path.basename(directory).startsWith(prefix)) throw new Error('Unsafe test cleanup path');
 await rm(directory,{recursive:true,force:true});
}
test('PHP adapter executes real MIME, media bounds, redirects and cache validation', {skip:missing},async()=>{
 const cache=await mkdtemp(path.join(os.tmpdir(),'nodeno-media-'));
 try {
  const run=spawnSync(php,['hosting/runtime-checks.php',cache],{cwd:root,encoding:'utf8'});
  assert.equal(run.status,0,run.stderr||run.stdout);
  assert.equal(JSON.parse(run.stdout).checks,'passed');
 } finally {await removeTestDirectory(cache,os.tmpdir(),'nodeno-media-');}
});

test('PHP HTTP API, nonce HTML, aliases, private storage and integrity match the release contract',{skip:missing},async t=>{
 await mkdir(path.join(root,'artifacts'),{recursive:true});
 const releaseRoot=await mkdtemp(path.join(root,'artifacts/cpanel-release-runtime-test-'));
 const mediaRoot=await mkdtemp(path.join(root,'artifacts/cpanel-media-runtime-test-'));
 t.after(async()=>{
  await removeTestDirectory(releaseRoot,path.join(root,'artifacts'),'cpanel-release-runtime-test-');
  await removeTestDirectory(releaseRoot+'.staging',path.join(root,'artifacts'),'cpanel-release-runtime-test-');
  await removeTestDirectory(mediaRoot,path.join(root,'artifacts'),'cpanel-media-runtime-test-');
 });
 const build=spawnSync(process.execPath,['scripts/build-cpanel.mjs'],{cwd:root,encoding:'utf8',env:{...process.env,NODENO_CPANEL_OUTPUT:releaseRoot,NODENO_MEDIA_APPROVAL_FIXTURE:'raster-test-v1'}});
 assert.equal(build.status,0,build.stderr||build.stdout);
 const publicRoot=path.join(releaseRoot,'public');
 const phpQuoted=value=>"'"+value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'";
 const runtimeConfig=path.join(releaseRoot,'nodeno-runtime.php');
 await writeFile(runtimeConfig,`<?php return ['mediaRoot' => ${phpQuoted(mediaRoot)}];`);
 const listener=net.createServer();
 await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));
 const port=listener.address().port;
 await new Promise(resolve=>listener.close(resolve));
 const origin=`http://127.0.0.1:${port}`;
 const server=spawn(php,['-d','display_errors=0','-d','opcache.enable_cli=1','-d','opcache.file_update_protection=0','-d','opcache.revalidate_freq=60','-S',`127.0.0.1:${port}`,'-t',publicRoot,path.join(root,'hosting/dev-router.php')],{cwd:root,env:{...process.env,NODENO_TEST_PUBLIC:publicRoot},stdio:['ignore','pipe','pipe']});
 const stopped=new Promise(resolve=>server.once('exit',resolve));
 let output='';
 server.stderr.on('data',chunk=>{output+=chunk;});
 try {
  for(let tries=0;tries<50;tries++) {
   try {await fetchAndDrain(origin+'/api/health');break;} catch {await new Promise(resolve=>setTimeout(resolve,100));}
  }
  for(const endpoint of ['catalog','config']) {
   const response=await fetch(origin+'/api/'+endpoint);
   assert.equal(response.status,200,output);
   assert.equal(await response.text(),await readFile(path.join(releaseRoot,'private',endpoint+'.json'),'utf8'));
   const head=await fetch(origin+'/api/'+endpoint,{method:'HEAD'});
   assert.equal(head.status,200);
   assert.equal(await head.text(),'');
  }
  const html=await fetch(origin+'/?lang=ar&product=2393',{headers:{Host:'nodenohome.com'}});
  assert.equal(html.status,200);
  assert.equal(html.headers.get('location'),null);
  const body=await html.text(),policy=html.headers.get('content-security-policy');
  const nonce=/'nonce-([a-f0-9]{32})'/.exec(policy)?.[1];
  assert.ok(nonce);
  assert.ok(body.includes(`nonce="${nonce}"`));
  assert.doesNotMatch(policy,/unsafe-inline/);
  assert.match(policy,/font-src 'self'/);
  const alias=await fetchAndDrain(origin+'/',{headers:{Host:'nodenohome.com.tr'}});
  assert.equal(alias.status,200);
  assert.notEqual(alias.headers.get('content-security-policy'),policy);
  for(const resource of ['/private/catalog.json','/catalog.json','/.env','/.htaccess','/hosting/index.php','/media/unknown/0','/media/2393/-1','/media/2393/00','/media/2393/9999','/media/2393/0/extra']) {
   assert.equal((await fetchAndDrain(origin+resource)).status,404,resource);
  }
  assert.equal((await fetchAndDrain(origin+'/api/catalog',{method:'POST'})).status,405);
  assert.equal((await fetchAndDrain(origin+'/api/checkout',{method:'POST'})).status,405);
  assert.equal((await fetchAndDrain(origin+'/api/checkout')).status,404);
  const media=JSON.parse(await readFile(path.join(releaseRoot,'private/media.json'),'utf8'));
  const raster=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=','base64');
  const cacheKey=createHash('sha256').update(raster).digest('hex');
  await writeFile(path.join(releaseRoot,'private/cache','approved-'+cacheKey+'.bin'),raster);
  assert.equal((await fetchAndDrain(origin+'/media/2393/0')).status,502,'A legacy cache cannot replace a missing hosted original');
  assert.equal((await fetchAndDrain(origin+'/api/health')).status,503,'Health must reject missing hosted originals');
  await writeFile(path.join(mediaRoot,cacheKey+'.png'),raster);
  const cachedImage=await fetch(origin+'/media/2393/0?url=https://evil.invalid/');
  assert.equal(cachedImage.status,200);
  assert.equal(cachedImage.headers.get('content-type'),'image/png');
  assert.equal(cachedImage.headers.get('content-disposition'),'inline');
  assert.equal(cachedImage.headers.get('cross-origin-resource-policy'),'same-origin');
  assert.deepEqual(Buffer.from(await cachedImage.arrayBuffer()),raster);
  const imageHead=await fetch(origin+'/media/2393/0',{method:'HEAD'});
  assert.equal(imageHead.status,200);
  assert.equal(await imageHead.text(),'');
  assert.equal(imageHead.headers.get('content-length'),String(raster.length));
  const font=await fetch(origin+'/assets/fonts/NODENOSans-Regular.woff');
  assert.deepEqual(Buffer.from(await font.arrayBuffer()),await readFile(path.join(root,'web/assets/fonts/NODENOSans-Regular.woff')));
  const health=await (await fetch(origin+'/api/health')).json();
  const release=JSON.parse(await readFile(path.join(releaseRoot,'private/release.json'),'utf8'));
  assert.equal(health.status,'ok');
  assert.equal(health.runtime,'php');
  assert.equal(health.releaseHash,release.releaseHash);
  assert.equal(health.driveConnected,false);
  assert.equal(health.mediaReady,true);
  assert.equal(health.mediaApproved,5129);
  const catalogue=JSON.parse(await readFile(path.join(releaseRoot,'private/catalog.json'),'utf8'));
  const suppliers=catalogue.products.filter(p=>p.productType==='supplier-item');assert.equal(health.supplierProducts,suppliers.length);assert.ok(health.supplierMediaApproved>0);
  const supplier=suppliers.find(p=>p.images.length),details=await fetch(origin+'/api/supplier-products/'+supplier.id);assert.equal(details.status,200);assert.equal((await details.json()).sha256,supplier.supplierDetailsHash);
  const supplierImage=path.join(publicRoot,supplier.images[0]);const originalSupplierImage=await readFile(supplierImage);
  try{
   await writeFile(supplierImage,Buffer.concat([originalSupplierImage,Buffer.from('tampered')]));
   assert.equal((await fetchAndDrain(origin+'/api/health')).status,503,'An altered supplier image must fail integrity even in a legacy-image fixture');
  }finally{await writeFile(supplierImage,originalSupplierImage);}
  const privateRoot=path.join(releaseRoot,'private'),otherPrivateRoot=path.join(releaseRoot,'other-private');
  if(path.dirname(privateRoot)!==releaseRoot||path.dirname(otherPrivateRoot)!==releaseRoot) throw new Error('Unsafe test move');
  await rename(privateRoot,otherPrivateRoot);
  try {
   await writeFile(runtimeConfig,`<?php return ['privateRoot' => ${phpQuoted(otherPrivateRoot)}, 'mediaRoot' => ${phpQuoted(mediaRoot)}];`);
   const relocated=await fetch(origin+'/api/health');
   assert.equal(relocated.status,200,'Protected config must support an external private root: '+await relocated.text()+' '+output.slice(-2000));
   assert.equal((await fetchAndDrain(origin+'/api/catalog')).status,200);
   await writeFile(runtimeConfig,`<?php return ['privateRoot' => ${phpQuoted(publicRoot)}];`);
   assert.equal((await fetchAndDrain(origin+'/api/health')).status,503,'Private data inside document root must fail closed');
  } finally {
   await writeFile(runtimeConfig,`<?php return ['mediaRoot' => ${phpQuoted(mediaRoot)}];`);
   await rename(otherPrivateRoot,privateRoot);
  }
  const template=path.join(releaseRoot,'private/index.html'),original=await readFile(template);
  try {
   await writeFile(template,Buffer.concat([original,Buffer.from('<!-- modified -->')]));
   assert.equal((await fetchAndDrain(origin+'/api/health')).status,503,'Changed installed bytes must fail health integrity');
  } finally {await writeFile(template,original);}
 } finally {
  server.kill();
  await stopped;
 }
});
