import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
test('a corrupt translated illustration prevents the whole multilingual article from publishing',()=>{
 const root=mkdtempSync(path.join(tmpdir(),'nodeno-blog-localized-'));try{
  mkdirSync(path.join(root,'assets/blog'),{recursive:true});const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"></svg>';writeFileSync(path.join(root,'assets/blog/a.svg'),svg);writeFileSync(path.join(root,'assets/blog/a-en.svg'),svg);
  const image={url:'/assets/blog/a.svg',kind:'original-diagram',sha256:createHash('sha256').update(svg).digest('hex'),alt:'A',width:1200,height:800};const article={image,locales:{en:{image:{...image,url:'/assets/blog/a-en.svg',sha256:'0'.repeat(64)}}}};writeFileSync(path.join(root,'a.json'),JSON.stringify(article));
  const source=`<?php require ${JSON.stringify(path.resolve('hosting/blog-worker.php').replaceAll('\\','/'))};try{nodenoBlogPublishable(json_decode(file_get_contents(__DIR__.'/a.json'),true),__DIR__);echo 'accepted';}catch(Throwable $e){echo $e->getMessage();}`;writeFileSync(path.join(root,'check.php'),source);const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),[path.join(root,'check.php')],{encoding:'utf8'});assert.equal(r.status,0,r.stdout+r.stderr);assert.equal(r.stdout,'image_integrity_failed');
 }finally{rmSync(root,{recursive:true,force:true});}
});
test('approved editorial illustrations can publish from a private bundle with no public file',()=>{
 const root=mkdtempSync(path.join(tmpdir(),'nodeno-blog-bundle-'));try{
  const privateDir=path.join(root,'private'),publicDir=path.join(root,'public');mkdirSync(privateDir);mkdirSync(publicDir);const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><title>Özgün çizim</title></svg>';const bytes=Buffer.from(svg);const sha=createHash('sha256').update(bytes).digest('hex');writeFileSync(path.join(privateDir,'blog-images.bin'),bytes);
  writeFileSync(path.join(privateDir,'blog-images.json'),JSON.stringify({schema:1,files:{'/assets/blog/private-only.svg':{offset:0,length:bytes.length,sha256:sha,mime:'image/svg+xml'}}}));
  const image={url:'/assets/blog/private-only.svg',storage:'private-bundle',kind:'original-diagram',sha256:sha,alt:'Özgün çizim',width:1200,height:800};writeFileSync(path.join(root,'a.json'),JSON.stringify({image}));
  const source=`<?php require ${JSON.stringify(path.resolve('hosting/blog-worker.php').replaceAll('\\','/'))};try{nodenoBlogPublishable(json_decode(file_get_contents(__DIR__.'/a.json'),true),__DIR__.'/public',__DIR__.'/private');echo 'accepted';}catch(Throwable $e){echo $e->getMessage();}`;writeFileSync(path.join(root,'check.php'),source);const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),[path.join(root,'check.php')],{encoding:'utf8'});assert.equal(r.status,0,r.stdout+r.stderr);assert.equal(r.stdout,'accepted');
 }finally{assert.ok(root.startsWith(path.resolve(tmpdir())+path.sep));rmSync(root,{recursive:true,force:true});}
});
