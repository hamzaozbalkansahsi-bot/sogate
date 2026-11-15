import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {packWebAssets} from '../lib/assets.mjs';
import {createHash}from'node:crypto';

test('nested font and icon assets preserve exact bytes and their MIME types',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'nodeno-brand-assets-'));
 try {
  await mkdir(path.join(root,'assets/fonts'),{recursive:true});
  const bytes=new Uint8Array([0,255,128,72,0,15]);
  await writeFile(path.join(root,'assets/fonts/brand.woff'),bytes);
  await writeFile(path.join(root,'favicon.ico'),bytes);
  await writeFile(path.join(root,'index.html'),'<!doctype html><title>NODENO</title>');
  await writeFile(path.join(root,'private.env'),'private key must not be published');
  const assets=await packWebAssets(root);
  assert.equal(assets['/assets/fonts/brand.woff'].type,'font/woff');
  assert.equal(assets['/assets/fonts/brand.woff'].encoding,'base64');
  assert.deepEqual(Buffer.from(assets['/assets/fonts/brand.woff'].body,'base64'),Buffer.from(bytes));
  assert.equal(assets['/favicon.ico'].type,'image/x-icon');
  assert.equal(assets['/'].body,'<!doctype html><title>NODENO</title>');
  assert.equal(assets['/private.env'],undefined);
 } finally {if(!path.basename(root).startsWith('nodeno-brand-assets-'))throw Error('Unexpected cleanup target');await rm(root,{recursive:true,force:true});}
});

test('large supplier raster packing keeps only a verified hosted reference',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'nodeno-brand-assets-'));const bytes=Buffer.from('test-only supplier raster');const hash=createHash('sha256').update(bytes).digest('hex');const key='/assets/suppliers/'+hash+'.png';
 try{
  await mkdir(path.join(root,'assets/suppliers'),{recursive:true});await writeFile(path.join(root,key),bytes);
  const assets=await packWebAssets(root,{externalAssets:{[key]:hash}});assert.equal(assets[key].encoding,'external');assert.equal(assets[key].body,undefined);assert.equal(assets[key].sha256,hash);assert.equal(assets[key].url,'https://nodenohome.com'+key);
  await assert.rejects(packWebAssets(root,{externalAssets:{[key]:'0'.repeat(64)}}),/approval mismatch/);
 }finally{if(!path.basename(root).startsWith('nodeno-brand-assets-'))throw Error('Unexpected cleanup target');await rm(root,{recursive:true,force:true});}
});

test('the reserved supplier namespace cannot embed an unapproved raster',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'nodeno-brand-assets-'));const bytes=Buffer.from('unapproved fixture raster');const hash=createHash('sha256').update(bytes).digest('hex');const key='/assets/suppliers/'+hash+'.png';
 try{
  await mkdir(path.join(root,'assets/suppliers'),{recursive:true});await writeFile(path.join(root,key),bytes);
  await assert.rejects(packWebAssets(root),/Supplier asset approval required/);
  await assert.rejects(packWebAssets(root,{externalAssets:{}}),/Supplier asset approval required/);
 }finally{if(!path.basename(root).startsWith('nodeno-brand-assets-'))throw Error('Unexpected cleanup target');await rm(root,{recursive:true,force:true});}
});

test('a referenced approved supplier asset must exist instead of silently disappearing from the package',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'nodeno-brand-assets-'));const hash=createHash('sha256').update('missing fixture raster').digest('hex');const key='/assets/suppliers/'+hash+'.png';
 try{
  await writeFile(path.join(root,'index.html'),'<!doctype html><title>NODENO</title>');
  await assert.rejects(packWebAssets(root,{externalAssets:{[key]:hash}}),/Approved supplier asset missing/);
 }finally{if(!path.basename(root).startsWith('nodeno-brand-assets-'))throw Error('Unexpected cleanup target');await rm(root,{recursive:true,force:true});}
});

test('supplier approvals remain bound to the exact filename and reserved origin path',async()=>{
 const root=await mkdtemp(path.join(tmpdir(),'nodeno-brand-assets-'));const bytes=Buffer.from('bound supplier raster');const hash=createHash('sha256').update(bytes).digest('hex');const wrong='/assets/suppliers/'+'0'.repeat(64)+'.png';
 try{
  await mkdir(path.join(root,'assets/suppliers'),{recursive:true});await writeFile(path.join(root,wrong),bytes);
  await assert.rejects(packWebAssets(root,{externalAssets:{[wrong]:hash}}),/approval mismatch/);
  await assert.rejects(packWebAssets(root,{externalAssets:{['https://evil.invalid/assets/suppliers/'+hash+'.png']:hash}}),/approval mismatch/);
 }finally{if(!path.basename(root).startsWith('nodeno-brand-assets-'))throw Error('Unexpected cleanup target');await rm(root,{recursive:true,force:true});}
});
