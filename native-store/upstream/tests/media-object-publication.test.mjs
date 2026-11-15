import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as gate from '../lib/media-object-gate.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
test('a changed production reference count cannot bypass all whole-object evidence',async()=>{
 const cleanup={references:{a:'x'},images:{x:{state:'approved_cleaned'}},publicationReady:true};
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,{referenceCount:5129},'a'.repeat(64),async()=>{throw new Error('unexpected read');}),/whole.object/i);
});
test('production reference coverage cannot omit whole-object evidence',async()=>{
 const cleanup={references:{a:'x'},images:{},publicationReady:true};const policy={version:'whole-object-v1',referenceCount:1,required:{},rejectedOutputSha256:[]};
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,policy,'a'.repeat(64),async()=>Buffer.from('{}')),/whole.object/i);
});
test('whole object publication also requires the full supplemental source/output family',async()=>{
 const policy={version:'whole-object-v1',referenceCount:1,required:{},rejectedOutputSha256:[],supplementalPass:'observed-specimens'};const body=Buffer.from(JSON.stringify({version:'whole-object-v1',images:{}}));const cleanup={references:{a:'x'},images:{},wholeObjectAudit:{policySha256:'a'.repeat(64),receiptPath:'artifacts/media-finalization/whole-object.json',receiptSha256:sha(body)}};
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,policy,'a'.repeat(64),async()=>body),/supplemental/);
});
test('current receipt, canonical policy hash and actual mask bytes all bind publication',async()=>{
 const mask=Buffer.from('reviewed mask'),receipt={version:'whole-object-v1',images:{x:{sourceSha256:'a'.repeat(64),outputSha256:'b'.repeat(64),outputRgbaSha256:'c'.repeat(64),width:10,height:10,reviewer:'actual review',fields:[],maskPath:'artifacts/media-object-review/mask.png',maskSha256:sha(mask)}}};
 const body=Buffer.from(JSON.stringify(receipt)),policySha='d'.repeat(64),policy={version:'whole-object-v1',referenceCount:1,rejectedOutputSha256:[],required:{x:{sourceSha256:'a'.repeat(64),acceptedOutputSha256:'b'.repeat(64),outputRgbaSha256:'c'.repeat(64),fields:[],maskPath:'artifacts/media-object-review/mask.png',maskSha256:sha(mask)}}};
 const cleanup={references:{a:'x'},images:{x:{sourceSha:'a'.repeat(64),outputSha:'b'.repeat(64),width:10,height:10}},wholeObjectAudit:{policySha256:policySha,receiptPath:'artifacts/media-finalization/whole-object.json',receiptSha256:sha(body)}};
 const read=async p=>p.endsWith('.json')?body:mask;
 await gate.verifyWholeObjectPublication(cleanup,policy,policySha,read);
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,policy,policySha,async p=>p.endsWith('.json')?body:Buffer.from('changed')),/mask/);
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,policy,'e'.repeat(64),read),/policy/);
 await assert.rejects(()=>gate.verifyWholeObjectPublication(cleanup,policy,policySha,async()=>Buffer.from('{}')),/receipt/);
});
