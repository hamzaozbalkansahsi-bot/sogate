import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {readFile} from 'node:fs/promises';
import {compileMediaApprovals,loadMediaApprovals,MEDIA_FIXTURE_BYTES,verifyPublicationEvidence as verifyProductionPublicationEvidence} from '../lib/media-approvals.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const url='https://witcdn.adoremobilya.com/fixture.png',key=hash(url),imageSha=hash(MEDIA_FIXTURE_BYTES);
const verifyPublicationEvidence=(cleanup,readArtifact)=>verifyProductionPublicationEvidence(cleanup,readArtifact,{isolatedTestFixture:true});
const policy=JSON.parse(await readFile(new URL('../data/media-audit-policy.json',import.meta.url),'utf8'));
function input(state='approved_unmodified') {
 const source={status:'verified',url,sha256:imageSha,bytes:MEDIA_FIXTURE_BYTES.length,width:1,height:1,path:`artifacts/media-originals/${key}.png`};
 const approved={state,sourceSha:imageSha,outputSha:imageSha,mime:'image/png',bytes:MEDIA_FIXTURE_BYTES.length,width:1,height:1,path:`artifacts/media-cleaned/${key}.png`};
 const cleanup={schemaVersion:1,publicationReady:true,references:{'7:0':key},images:{[key]:approved}};
 const archives=new Map(),families={};
 for(const [name,version] of [['flame','65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d'],['small_badge',policy.smallBadgePass]]) {
  const reportPath=`artifacts/${name==='flame'?'media-symbol-audit':'media-physical-badge-audit'}/reports/${imageSha}.json`;
  const report=Buffer.from(JSON.stringify({fileSha256:imageSha,passVersion:version,candidateHits:0,hits:[],frameCount:1,compositesScanned:1,frames:[{frame:0,background:'white',rgbSha256:'b'.repeat(64)}]}));archives.set(reportPath,report);
  const receipt=Buffer.from(JSON.stringify({passVersion:version,allSourceUrlsScanned:true,sourceReferences:1,referenceSha256:policy.smallBadgeReferences,reports:[{fileSha256:imageSha,path:reportPath,hits:0,roles:[{urlSha:key,role:'source'},{urlSha:key,role:'current_output'}]}]}));
  const dispositions=Buffer.from(JSON.stringify({passVersion:version,receiptSha256:hash(receipt),hits:{}}));
  const family={passVersion:version,sourceUrls:1,finalOutputUrls:1,reviewedRelevantHits:0,reportBindingsSha256:hash(JSON.stringify([[imageSha,hash(report)]]))};
  for(const [kind,bytes] of [['receipt',receipt],['dispositions',dispositions]]) {const filename=`artifacts/media-finalization/${name}-${kind}.json`;archives.set(filename,bytes);family[kind+'Path']=filename;family[kind+'Sha256']=hash(bytes);}
  families[name]=family;
 }
 cleanup.publicationAudit={policy:policy.policy,manifestBindingSha256:hash(JSON.stringify([[['7:0',key]],[[key,state,imageSha,imageSha,null,null,null]]])),requiredFamilies:families};
 return {isolatedTestFixture:true,media:{7:[url]},downloads:{schemaVersion:1,references:{'7:0':key},images:{[key]:source}},cleanup,archives,readArtifact:async filename=>archives.get(filename)||MEDIA_FIXTURE_BYTES};
}
test('clean media manifest is deterministic, contains every reference and excludes local paths/timestamps',async()=>{
 const first=await compileMediaApprovals(input());
 const changed=input();changed.cleanup.updatedAt='different';changed.cleanup.images[key].report='private-report';
 const second=await compileMediaApprovals(changed);
 assert.deepEqual(first,second);
 assert.equal(first.manifest.referenceCount,1);
 assert.equal(first.manifest.images[key].sourceSha,imageSha);
 assert.equal(first.manifest.images[key].file,null);
 assert.doesNotMatch(JSON.stringify(first.manifest),/artifacts|updatedAt|report/);
 const cleaned=await compileMediaApprovals(input('approved_cleaned'));
 assert.equal(cleaned.manifest.images[key].file,imageSha+'.png');
});
test('pending, failed, review and missing image approvals block publication',async()=>{
 const provisional=input();provisional.cleanup.publicationReady=false;
 await assert.rejects(()=>compileMediaApprovals(provisional),/publication gate/);
 for(const state of ['pending','review_required','failed','approved']) await assert.rejects(()=>compileMediaApprovals(input(state)),/Unapproved/);
 const missing=input();delete missing.cleanup.references['7:0'];
 await assert.rejects(()=>compileMediaApprovals(missing),/coverage/);
 const wrong=input();wrong.cleanup.references['7:0']='a'.repeat(64);
 await assert.rejects(()=>compileMediaApprovals(wrong),/mismatch/);
});
test('changed source bytes, output bytes, metadata and MIME cannot reuse an approval',async()=>{
 for(const field of ['sourceSha','outputSha']) {
  const changed=input();changed.cleanup.images[key][field]='a'.repeat(64);
  await assert.rejects(()=>compileMediaApprovals(changed),/hash|bytes/);
 }
 const changed=input();changed.readArtifact=async()=>Buffer.from('unapproved source');
 await assert.rejects(()=>compileMediaApprovals(changed),/original image bytes changed/);
 const resized=input();resized.cleanup.images[key].width=2;
 await assert.rejects(()=>compileMediaApprovals(resized),/dimensions changed/);
 const spoof=input();spoof.cleanup.images[key].mime='image/jpeg';
 await assert.rejects(()=>compileMediaApprovals(spoof),/raster signature/);
});
test('synthetic media approvals are confined to explicit isolated Node test output',async()=>{
 await assert.rejects(()=>loadMediaApprovals({root,media:{7:[url]},fixture:'raster-test-v1',isolatedOutput:path.join(root,'artifacts/cpanel-release')}),/restricted/);
 const approved=await loadMediaApprovals({root,media:{7:[url]},fixture:'raster-test-v1',isolatedOutput:path.join(root,'artifacts/cpanel-release-clean-test-fixture')});
 assert.equal(approved.testOnly,true);
 assert.equal(approved.manifest.images[key].outputSha,imageSha);
});

test('a legacy publication boolean without the new physical-plaque evidence cannot publish',async()=>{
 const legacy=input();delete legacy.cleanup.publicationAudit;
 await assert.rejects(()=>compileMediaApprovals(legacy),/physical.*badge|publication.*evidence/i);
});

test('publication proof cannot be carried to another output or changed evidence bytes',async()=>{
 const changed=input();changed.cleanup.images[key].outputSha='a'.repeat(64);
 await assert.rejects(()=>verifyPublicationEvidence(changed.cleanup,changed.readArtifact),/hash binding|Isolated test publication fixture is restricted/);
 const corrupt=input();
 await assert.rejects(()=>verifyPublicationEvidence(corrupt.cleanup,async()=>Buffer.from('{}')),/evidence bytes\/hash changed/);
 const old=input();old.cleanup.publicationAudit.requiredFamilies.small_badge.passVersion='b5f2f3ed18e09a9d94a1de57d564204cf68b1aa0d437525ddb49420da814c117';
 await assert.rejects(()=>verifyPublicationEvidence(old.cleanup,old.readArtifact),/Incomplete/);
});

test('a final-output hit without its exact visual disposition blocks the Node publication path',async()=>{
 const f=input(),family=f.cleanup.publicationAudit.requiredFamilies.small_badge;
 const receipt=JSON.parse(f.archives.get(family.receiptPath));receipt.reports[0].hits=1;
 const reportPath=receipt.reports[0].path,report=JSON.parse(f.archives.get(reportPath));
 report.candidateHits=1;report.hits=[{id:'c'.repeat(64),frame:0,background:'white',box:[0,0,1,1]}];
 const reportBytes=Buffer.from(JSON.stringify(report));f.archives.set(reportPath,reportBytes);family.reportBindingsSha256=hash(JSON.stringify([[imageSha,hash(reportBytes)]]));family.reviewedRelevantHits=1;
 const bytes=Buffer.from(JSON.stringify(receipt));f.archives.set(family.receiptPath,bytes);family.receiptSha256=hash(bytes);
 const decisions=Buffer.from(JSON.stringify({passVersion:family.passVersion,receiptSha256:hash(bytes),hits:{}}));f.archives.set(family.dispositionsPath,decisions);family.dispositionsSha256=hash(decisions);
 await assert.rejects(()=>verifyPublicationEvidence(f.cleanup,f.readArtifact),/report|disposition/i);
});
