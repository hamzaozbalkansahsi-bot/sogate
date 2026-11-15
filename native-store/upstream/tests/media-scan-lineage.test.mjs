import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as lineage from '../lib/media-scan-lineage.mjs';
test('cached scans require exact immutable parent receipt/report/frame/hit lineage',async()=>{
 const hash=b=>createHash('sha256').update(b).digest('hex'),key='a'.repeat(64),path=`artifacts/media-object-removal-20261102/web-supplemental/reports/${key}.json`,parent={fileSha256:key,passVersion:'old',frames:[{frame:0,background:'white',rgbSha256:'b'.repeat(64)}],hits:[{id:'old',box:[1,2,3,4]}]},body=Buffer.from(JSON.stringify(parent)),index=new Map([[key,{path,reportSha256:hash(body)}]]),child={...parent,passVersion:'new',hits:[{id:'new',box:[1,2,3,4]}],scanLineage:{path,sha256:hash(body),passVersion:'old'}};
 await lineage.verifyCombinedReport(child,index,'old',async()=>body);
 for(const changed of [{...child,hits:[]},{...child,frames:[{...parent.frames[0],rgbSha256:'c'.repeat(64)}]},{...child,scanLineage:{...child.scanLineage,sha256:'d'.repeat(64)}}])await assert.rejects(()=>lineage.verifyCombinedReport(changed,index,'old',async()=>body),/lineage/);
 await assert.rejects(()=>lineage.verifyCombinedReport(child,index,'old',async()=>Buffer.from('changed')),/lineage/);
});
