import {readdir,readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const assetTypes={
 '.html':['text/html; charset=utf-8',false],
 '.js':['text/javascript; charset=utf-8',false],
 '.css':['text/css; charset=utf-8',false],
 '.svg':['image/svg+xml',false],
 '.json':['application/json; charset=utf-8',false],
 '.webmanifest':['application/manifest+json; charset=utf-8',false],
 '.txt':['text/plain; charset=utf-8',false],
 '.woff':['font/woff',true],'.woff2':['font/woff2',true],'.ttf':['font/ttf',true],
 '.ico':['image/x-icon',true],'.png':['image/png',true],'.jpg':['image/jpeg',true],'.jpeg':['image/jpeg',true],'.webp':['image/webp',true],
};

export async function packWebAssets(directory,{externalAssets={}}={}) {
 if(!externalAssets||typeof externalAssets!=='object'||Array.isArray(externalAssets))throw new Error('External supplier asset approval mismatch');
 const approved=Object.entries(externalAssets),seenExternal=new Set(),assets={};
 for(const [key,hash]of approved)if(!/^\/assets\/suppliers\/[a-f0-9]{64}\.(jpg|png|webp)$/.test(key)||typeof hash!=='string'||!/^[a-f0-9]{64}$/.test(hash)||key.split('/').at(-1).split('.')[0]!==hash)throw new Error('External supplier asset approval mismatch');
 async function walk(folder,relative='') {
  for(const entry of await readdir(folder,{withFileTypes:true})) {
   if(entry.name.startsWith('.')) continue;
   if(entry.isSymbolicLink()) throw new Error('Web assets cannot contain symbolic links');
   const filename=path.join(folder,entry.name),key=relative+'/'+entry.name;
   if(entry.isDirectory()){await walk(filename,key);continue;}
   if(key.startsWith('/assets/suppliers/')&&!Object.hasOwn(externalAssets,key))throw new Error('Supplier asset approval required: '+key);
   const definition=assetTypes[path.extname(entry.name).toLowerCase()];
   if(!entry.isFile()||!definition) continue;
   const [type,binary]=definition,bytes=await readFile(filename);
   if(!bytes.length) throw new Error('Empty web asset: '+key);
   if(Object.hasOwn(externalAssets,key)){
    const hash=createHash('sha256').update(bytes).digest('hex');
    if(!/^\/assets\/suppliers\/[a-f0-9]{64}\.(jpg|png|webp)$/.test(key)||externalAssets[key]!==hash||!key.includes(hash))throw new Error('External supplier asset approval mismatch');
    seenExternal.add(key);assets[key]={type,encoding:'external',url:'https://nodenohome.com'+key,sha256:hash};continue;
   }
   assets[key==='/index.html'?'/':key]={body:bytes.toString(binary?'base64':'utf8'),type,encoding:binary?'base64':'utf8'};
  }
 }
 await walk(path.resolve(directory));
 for(const [key]of approved)if(!seenExternal.has(key))throw new Error('Approved supplier asset missing: '+key);
 return assets;
}
