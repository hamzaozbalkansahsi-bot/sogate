/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/runtime-catalog-build.mjs
 * Açıklama   : Donmuş kaynağa dokunmadan küçük sıkıştırılmış çalışma kataloğunu türetilmiş pakete bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import zlib from 'node:zlib';import {fileURLToPath}from'node:url';
const source=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||'');
if(path.basename(bundle)!=='bundle'||!path.basename(path.dirname(bundle)).startsWith('native-stage-'))throw Error('RUNTIME_CATALOG_BUILD_SCOPE');
const file=path.join(bundle,'private/catalog.json'),bytes=fs.readFileSync(file),catalog=JSON.parse(bytes),sha=value=>crypto.createHash('sha256').update(value).digest('hex');
if(catalog.catalogOrigin!=='sexogate-catalog-v2'||!Array.isArray(catalog.products)||catalog.products.length!==3152||!/^[a-f0-9]{32}$/.test(catalog.dataset))throw Error('RUNTIME_CATALOG_SOURCE_INVALID');
const active=catalog.products.filter(p=>p.catalogOrigin==='sexogate-marketplaces-v1');
if(active.length!==958||active.some(p=>!/^sg_ty_[a-f0-9]{16}$/.test(p.id)||typeof p.code!=='string'||!p.code)||new Set(catalog.products.map(p=>p.id)).size!==3152||catalog.products.slice(2194).some((p,i)=>p!==active[i])||catalog.products.slice(0,2194).some(p=>p.catalogOrigin!=='sexogate-suppliers-v1'))throw Error('RUNTIME_CATALOG_IDENTITY_INVALID');
const raw=Buffer.from(JSON.stringify({...catalog,products:active})),gzip=zlib.gzipSync(raw,{level:9,mtime:0});
if(gzip.readUInt32LE(4)!==0||raw.length>32000000||gzip.length>25000000)throw Error('RUNTIME_CATALOG_GZIP_INVALID');
const meta={schema:1,dataset:catalog.dataset,sourceCount:3152,activeCount:958,sourceSha256:sha(bytes),sourceBytes:bytes.length,rawSha256:sha(raw),rawBytes:raw.length,gzipSha256:sha(gzip),gzipBytes:gzip.length,identitySha256:sha(JSON.stringify(active.map(p=>[p.id,p.code])))};
const entryPath=path.join(bundle,'public/index.php');let entry=fs.readFileSync(entryPath,'utf8');const head='function nodenoStoreContext(string $private):array',start=entry.indexOf(head),end=entry.indexOf('\nfunction ',start+head.length),load="$catalog=json_decode(nodenoPrivateFile($private,'catalog.json'),true,512,JSON_THROW_ON_ERROR);";
if(start<0||end<0||entry.indexOf(head,start+1)!==-1)throw Error('RUNTIME_CATALOG_CONTEXT_HOOK_CHANGED');
let context=entry.slice(start,end);if(context.split(load).length!==2)throw Error('RUNTIME_CATALOG_LOAD_HOOK_CHANGED');
context=context.replace(load,"require_once $private.'/sexogate-runtime-catalog.php';$catalog=sexogateRuntimeCatalogLoad($private);");entry=entry.slice(0,start)+context+entry.slice(end);
const controlPath=path.join(bundle,'private/control-catalog.php'),control=fs.readFileSync(controlPath,'utf8'),controlHook="require_once __DIR__.'/sexogate-storefront-content.php';";
if(control.split(controlHook).length!==2)throw Error('RUNTIME_CATALOG_CONTROL_HOOK_CHANGED');
fs.writeFileSync(path.join(bundle,'private/catalog-active.json.gz'),gzip);fs.writeFileSync(path.join(bundle,'private/catalog-active.meta.json'),JSON.stringify(meta));fs.copyFileSync(path.join(source,'runtime-catalog.php'),path.join(bundle,'private/sexogate-runtime-catalog.php'));fs.writeFileSync(entryPath,entry);
fs.writeFileSync(controlPath,control.replace(controlHook,"require_once __DIR__.'/sexogate-runtime-catalog.php';\n"+controlHook));
if(sha(fs.readFileSync(file))!==meta.sourceSha256)throw Error('RUNTIME_CATALOG_SOURCE_CHANGED');
console.log(JSON.stringify({runtimeCatalog:true,sourceCount:3152,activeCount:958,gzipBytes:gzip.length,sourcePreserved:true}));
