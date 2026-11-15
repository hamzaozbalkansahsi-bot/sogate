import {readFile,realpath,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {verifyWholeObjectPublication} from './media-object-gate.mjs';
import {verifyCombinedReport} from './media-scan-lineage.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const HASH=/^[a-f0-9]{64}$/;
const extensions={'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/gif':'gif','image/avif':'avif'};
const auditPolicy=JSON.parse(await readFile(new URL('../data/media-audit-policy.json',import.meta.url),'utf8'));
const objectPolicyBytes=await readFile(new URL('../data/media-object-policy.json',import.meta.url));
const objectPolicy=JSON.parse(objectPolicyBytes),objectPolicySha=hash(objectPolicyBytes);
const knownBrandedFiles=new Set(Object.values(JSON.parse(await readFile(new URL('../data/media-brand-incidents.json',import.meta.url),'utf8')).findings).map(row=>row.sourceSha256));
export const MEDIA_FIXTURE_BYTES=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=','base64');
export const MEDIA_MIGRATION_FIXTURE_OUTPUT=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAMAAAACCAIAAAASFvFNAAAAC0lEQVR4nGNgwAQAABQAAX3+Hu4AAAAASUVORK5CYII=','base64');
export const MEDIA_MIGRATION_FIXTURE_SOURCE=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAMAAAACCAIAAAASFvFNAAAAFElEQVR4nGP8//8/AxgwQSgGBgYANgYDARtTfJEAAAAASUVORK5CYII=','base64');

export function inspectRaster(bytes,mime) {
 let dimensions=null;
 if(mime==='image/png'&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))&&bytes.length>=24) dimensions=[bytes.readUInt32BE(16),bytes.readUInt32BE(20)];
 if(mime==='image/gif'&&/^GIF8[79]a$/.test(bytes.subarray(0,6).toString('ascii'))&&bytes.length>=10) dimensions=[bytes.readUInt16LE(6),bytes.readUInt16LE(8)];
 if(mime==='image/jpeg'&&bytes[0]===255&&bytes[1]===216) {
  let offset=2;
  while(offset+4<=bytes.length) {
   if(bytes[offset++]!==255) break;
   while(bytes[offset]===255) offset++;
   const marker=bytes[offset++];
   if(marker===0xd9||marker===0xda) break;
   if(marker===0x01||(marker>=0xd0&&marker<=0xd7)) continue;
   if(offset+2>bytes.length) break;
   const length=bytes.readUInt16BE(offset);
   if(length<2||offset+length>bytes.length) break;
   if([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker)&&length>=7) {dimensions=[bytes.readUInt16BE(offset+5),bytes.readUInt16BE(offset+3)];break;}
   offset+=length;
  }
 }
 if(mime==='image/webp'&&bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WEBP') {
  const type=bytes.subarray(12,16).toString();
  if(type==='VP8X'&&bytes.length>=30) dimensions=[1+bytes.readUIntLE(24,3),1+bytes.readUIntLE(27,3)];
  else if(type==='VP8L'&&bytes.length>=25&&bytes[20]===0x2f) dimensions=[1+bytes[21]+((bytes[22]&63)<<8),1+(bytes[22]>>6)+(bytes[23]<<2)+((bytes[24]&15)<<10)];
  else if(type==='VP8 '&&bytes.length>=30&&bytes.subarray(23,26).equals(Buffer.from([0x9d,1,0x2a]))) dimensions=[bytes.readUInt16LE(26)&0x3fff,bytes.readUInt16LE(28)&0x3fff];
 }
 if(mime==='image/avif'&&bytes.subarray(4,8).toString()==='ftyp'&&bytes.subarray(8,48).includes(Buffer.from('avif'))) {
  const offset=bytes.indexOf(Buffer.from('ispe'));
  if(offset>=0&&offset+16<=bytes.length) dimensions=[bytes.readUInt32BE(offset+8),bytes.readUInt32BE(offset+12)];
 }
 if(!dimensions||dimensions.some(value=>!Number.isSafeInteger(value)||value<1||value>100000)) throw new Error('Approved image raster signature/dimensions are invalid');
 return {width:dimensions[0],height:dimensions[1]};
}

function sourceReferences(media) {
 const references={};
 for(const id of Object.keys(media).sort()) {
  if(!/^[A-Za-z0-9_-]+$/.test(id)||!Array.isArray(media[id])) throw new Error('Invalid media reference map');
  for(let index=0;index<media[id].length;index++) {
   const url=media[id][index],parsed=new URL(url);
   if(parsed.protocol!=='https:'||parsed.hostname!=='witcdn.adoremobilya.com'||parsed.username||parsed.password||(parsed.port&&parsed.port!=='443')) throw new Error('Unsafe approved source URL');
   references[`${id}:${index}`]=hash(url);
  }
 }
 return Object.fromEntries(Object.entries(references).sort(([a],[b])=>a<b?-1:a>b?1:0));
}

function finishManifest(references,images,testOnly=false) {
 const ordered=Object.fromEntries(Object.keys(images).sort().map(key=>[key,images[key]]));
 const counts={approved_unmodified:0,approved_cleaned:0};
 for(const entry of Object.values(ordered)) counts[entry.state]++;
 const manifest={schema:1,policy:'approved-only-v1',referenceCount:Object.keys(references).length,uniqueCount:Object.keys(ordered).length,counts,references,images:ordered};
 return {manifest,mediaVersion:hash(JSON.stringify(manifest)),testOnly};
}

export async function compileMediaApprovals({media,downloads,cleanup,readArtifact,isolatedTestFixture=false}) {
 if(downloads?.schemaVersion!==1||cleanup?.schemaVersion!==1) throw new Error('Missing verified media approval manifests');
 if(cleanup.publicationReady!==true) throw new Error('Final image visual/structure publication gate is not approved');
 const references=sourceReferences(media),keys=[...new Set(Object.values(references))].sort();
 if(!keys.length||Object.keys(downloads.references||{}).length!==Object.keys(references).length||Object.keys(cleanup.references||{}).length!==Object.keys(references).length) throw new Error('Incomplete image approval reference coverage');
 for(const [reference,key] of Object.entries(references)) if(downloads.references[reference]!==key||cleanup.references[reference]!==key) throw new Error('Image approval reference/source mismatch');
 if(Object.keys(downloads.images||{}).length!==keys.length||Object.keys(cleanup.images||{}).length!==keys.length) throw new Error('Incomplete image approval image coverage');
 const images={};
 for(let start=0;start<keys.length;start+=12) await Promise.all(keys.slice(start,start+12).map(async key=>{
  const source=downloads.images[key],approval=cleanup.images[key];
  if(source?.status!=='verified'||!['approved_unmodified','approved_cleaned'].includes(approval?.state)) throw new Error('Unapproved/quarantined product image blocks publication');
  if(hash(source.url||'')!==key||!HASH.test(source.sha256||'')||approval.sourceSha!==source.sha256||!HASH.test(approval.outputSha||'')) throw new Error('Image approval source/output hash mismatch');
  if(!extensions[approval.mime]||!Number.isSafeInteger(approval.bytes)||approval.bytes<1||approval.bytes>20000000) throw new Error('Invalid approved raster metadata');
  const original=await readArtifact(source.path,'media-originals');
  if(hash(original)!==source.sha256||original.length!==source.bytes) throw new Error('Verified original image bytes changed');
  const output=await readArtifact(approval.path,'media-cleaned');
  const dimensions=inspectRaster(output,approval.mime);
  if(hash(output)!==approval.outputSha||output.length!==approval.bytes||dimensions.width!==approval.width||dimensions.height!==approval.height||approval.width!==source.width||approval.height!==source.height) throw new Error('Approved output image bytes/dimensions changed');
  if(approval.state==='approved_unmodified'&&(approval.outputSha!==approval.sourceSha||!output.equals(original))) throw new Error('Unmodified image approval changed original bytes');
  images[key]={state:approval.state,sourceSha:approval.sourceSha,outputSha:approval.outputSha,mime:approval.mime,bytes:approval.bytes,width:approval.width,height:approval.height,file:approval.state==='approved_cleaned'?`${approval.outputSha}.${extensions[approval.mime]}`:null};
 }));
 await verifyPublicationEvidence(cleanup,readArtifact,{isolatedTestFixture});
 return finishManifest(references,images,isolatedTestFixture);
}

export function isPublicationReportPath(family,filename) {
 const pattern=family==='whole_object_supplemental'?/^artifacts\/media-object-removal-20261102\/web-supplemental(?:-v2)?\/reports\/[a-f0-9]{64}\.json$/:/^artifacts\/(media-symbol-audit|media-physical-badge-audit|media-complete-badge-audit)\/reports\/[a-f0-9]{64}\.json$/;
 return typeof filename==='string'&&pattern.test(filename);
}

export async function verifyPublicationEvidence(cleanup,readArtifact,{isolatedTestFixture=false}={}) {
 const fixtureHashes=new Set([MEDIA_FIXTURE_BYTES,MEDIA_MIGRATION_FIXTURE_SOURCE,MEDIA_MIGRATION_FIXTURE_OUTPUT].map(hash)),fixtureRows=Object.values(cleanup.images||{}),fixtureRefs=Object.keys(cleanup.references||{}).length;
 const fixtureAllowed=isolatedTestFixture===true&&!!process.env.NODE_TEST_CONTEXT&&fixtureRefs>=1&&fixtureRefs<=2&&fixtureRows.length===1&&fixtureRows.every(r=>((r.width===1&&r.height===1)||(r.width===3&&r.height===2))&&fixtureHashes.has(r.sourceSha)&&fixtureHashes.has(r.outputSha));
 if(isolatedTestFixture&&!fixtureAllowed)throw new Error('Isolated test publication fixture is restricted');
 if(!fixtureAllowed)await verifyWholeObjectPublication(cleanup,objectPolicy,objectPolicySha,readArtifact);
 const audit=cleanup.publicationAudit;
 const binding=hash(JSON.stringify([Object.entries(cleanup.references).sort(([a],[b])=>a<b?-1:a>b?1:0),Object.keys(cleanup.images).sort().map(key=>{const row=cleanup.images[key];return [key,row.state,row.sourceSha,row.outputSha,row.finalReview?.candidateReceiptSha??null,row.finalReview?.selectionReceiptSha??null,row.finalReview?.selection?.candidateSha??null];})]));
 if(audit?.policy!==auditPolicy.policy||audit.manifestBindingSha256!==binding) throw new Error('Current physical badge publication evidence/hash binding is required');
 for(const row of Object.values(cleanup.images)) if(knownBrandedFiles.has(row.outputSha)) throw new Error('Known reported brand image blocks publication');
 const requiredFamilies=[['flame','65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d'],['small_badge',auditPolicy.smallBadgePass]];
 if(objectPolicy.supplementalPass&&!fixtureAllowed)requiredFamilies.push(['whole_object_supplemental',objectPolicy.supplementalPass]);
 for(const [name,version] of requiredFamilies) {
  const family=audit.requiredFamilies?.[name],count=Object.keys(cleanup.images).length;
  if(family?.passVersion!==version||family.sourceUrls!==count||family.finalOutputUrls!==count) throw new Error('Incomplete physical badge publication evidence');
  const documents={};
  for(const kind of ['receipt','dispositions']) {
   const filename=family[kind+'Path'],expected=family[kind+'Sha256'];
   if(typeof filename!=='string'||!filename.startsWith('artifacts/media-finalization/')||!HASH.test(expected||'')) throw new Error('Invalid publication evidence path/hash');
   const bytes=await readArtifact(filename,'media-finalization');
   if(hash(bytes)!==expected) throw new Error('Publication evidence bytes/hash changed');
   documents[kind]=JSON.parse(bytes);
  }
  const {receipt,dispositions}=documents;
  if(receipt.passVersion!==version||dispositions.passVersion!==version||dispositions.receiptSha256!==family.receiptSha256||receipt.allSourceUrlsScanned!==true||receipt.sourceReferences!==Object.keys(cleanup.references).length) throw new Error('Publication evidence receipt mismatch');
  const calibration=name==='small_badge'?auditPolicy.smallBadgeReferences:name==='whole_object_supplemental'?objectPolicy.supplementalReferences:null;
  if(calibration&&JSON.stringify(Object.entries(receipt.referenceSha256||{}).sort())!==JSON.stringify(Object.entries(calibration).sort())) throw new Error('Physical badge calibration references changed');
  const sources=new Set(),outputs=new Set(),seenHits=new Set(),reportBindings=[];
  let parentIndex=null;
  if(name==='whole_object_supplemental'&&objectPolicy.supplementalParentPass){
   if(!/^artifacts\/media-finalization\/[a-zA-Z0-9-]+\.json$/.test(receipt.parentReceiptPath||''))throw new Error('Invalid supplemental parent lineage receipt');
   const bytes=await readArtifact(receipt.parentReceiptPath,'media-finalization');
   if(hash(bytes)!==receipt.parentReceiptSha256)throw new Error('Supplemental parent lineage receipt bytes changed');
   const parent=JSON.parse(bytes);
   if(parent.passVersion!==objectPolicy.supplementalParentPass||parent.allSourceAndOutputFilesAndFramesScanned!==true)throw new Error('Supplemental parent lineage receipt differs');
   parentIndex=new Map(parent.reports.map(r=>[r.fileSha256,r]));
  }
  let reviewedHits=0;
  for(const reference of receipt.reports||[]) {
   if(!HASH.test(reference.fileSha256||'')||!isPublicationReportPath(name,reference.path)) throw new Error('Invalid publication report path/hash');
   const bytes=await readArtifact(reference.path,reference.path.split('/')[1]),reportSha=hash(bytes),report=JSON.parse(bytes);
   reportBindings.push([reference.fileSha256,reportSha]);
   if(report.fileSha256!==reference.fileSha256||report.passVersion!==version||!Array.isArray(report.hits)||report.candidateHits!==report.hits.length||reference.hits!==report.hits.length||!Array.isArray(report.frames)||!report.frames.length||report.compositesScanned!==report.frames.length) throw new Error('Publication report identity/count/frame mismatch');
   if(parentIndex)await verifyCombinedReport(report,parentIndex,objectPolicy.supplementalParentPass,readArtifact);
   const frames=new Set();
   for(const frame of report.frames) {
    const identity=frame.frame+':'+frame.background;
    if(!Number.isSafeInteger(frame.frame)||frame.frame<0||!['white','black'].includes(frame.background)||!HASH.test(frame.rgbSha256||'')||frames.has(identity)) throw new Error('Invalid publication report frame coverage');
    frames.add(identity);
   }
   if(report.frameCount!==new Set(report.frames.map(frame=>frame.frame)).size) throw new Error('Incomplete publication report frame count');
   const sourceKeys=[],outputKeys=[];
   for(const role of reference.roles||[]) {
    const row=cleanup.images[role.urlSha];
    if(!row) throw new Error('Unknown publication evidence image');
    if(role.role==='source'&&reference.fileSha256===row.sourceSha) {sources.add(role.urlSha);sourceKeys.push(role.urlSha);}
    if(['current_output','final_output','review_candidate'].includes(role.role)&&reference.fileSha256===row.outputSha) {outputs.add(role.urlSha);outputKeys.push(role.urlSha);}
   }
   for(const hit of report.hits) {
    if(!HASH.test(hit.id||'')||seenHits.has(hit.id)||!frames.has(hit.frame+':'+hit.background)) throw new Error('Invalid/duplicate publication report hit');
    seenHits.add(hit.id);
    if(!sourceKeys.length&&!outputKeys.length) continue;
    reviewedHits++;
    const decision=dispositions.hits?.[hit.id];
    if(decision?.fileSha256!==reference.fileSha256||decision.reportSha256!==reportSha||decision.visualReview!==true||!['reviewer','notes'].every(field=>typeof decision[field]==='string'&&decision[field].trim())) throw new Error('Exact visual hit disposition required');
    if(decision.disposition==='false_positive') continue;
    const expected=Object.fromEntries(sourceKeys.sort().map(key=>[key,cleanup.images[key].outputSha]));
    if(decision.disposition!=='true_brand_cleaned'||outputKeys.length||!sourceKeys.length||sourceKeys.some(key=>cleanup.images[key].state!=='approved_cleaned'||cleanup.images[key].outputSha===reference.fileSha256)||JSON.stringify(Object.entries(decision.cleanedOutputs||{}).sort())!==JSON.stringify(Object.entries(expected).sort())) throw new Error('Unresolved final output brand hit blocks publication');
   }
  }
  if(hash(JSON.stringify(reportBindings.sort(([a,b],[c,d])=>a<c?-1:a>c?1:b<d?-1:b>d?1:0)))!==family.reportBindingsSha256||reviewedHits!==family.reviewedRelevantHits) throw new Error('Publication report hash bindings changed');
  if(Object.keys(dispositions.hits||{}).some(id=>!seenHits.has(id))) throw new Error('Unknown visual hit disposition');
  if(sources.size!==count||outputs.size!==count) throw new Error('Publication evidence does not cover current source/output hashes');
 }
}

export async function loadMediaApprovals({root,media,fixture=false,isolatedOutput=null}) {
 if(fixture) {
  const base=path.basename(isolatedOutput||'');
  if(fixture!=='raster-test-v1'||!process.env.NODE_TEST_CONTEXT||path.dirname(path.resolve(isolatedOutput||'.'))!==path.resolve(root,'artifacts')||!/^cpanel-release-(?:test-|runtime-test-|clean-test-)/.test(base)) throw new Error('Media approval fixture is restricted to isolated Node tests');
  const references=sourceReferences(media),images={};
  for(const key of new Set(Object.values(references))) images[key]={state:'approved_unmodified',sourceSha:hash(MEDIA_FIXTURE_BYTES),outputSha:hash(MEDIA_FIXTURE_BYTES),mime:'image/png',bytes:MEDIA_FIXTURE_BYTES.length,width:1,height:1,file:null};
  return finishManifest(references,images,true);
 }
 const canonicalRoot=await realpath(root);
 const readArtifact=async(relative,folder)=>{
  if(typeof relative!=='string'||!relative.startsWith(`artifacts/${folder}/`)||relative.includes('\\')||relative.split('/').some(part=>part==='..'||part==='')) throw new Error('Unsafe media approval artifact path');
  const filename=path.resolve(canonicalRoot,relative);
  if((await lstat(filename)).isSymbolicLink()) throw new Error('Media approval symlink rejected');
  const actual=await realpath(filename),allowed=path.join(canonicalRoot,'artifacts',folder)+path.sep;
  if(!actual.startsWith(allowed)) throw new Error('Media approval artifact escapes private artifacts');
  return readFile(actual);
 };
 const downloads=JSON.parse(await readFile(path.join(root,'artifacts/media-download.json'),'utf8'));
 const cleanup=JSON.parse(await readFile(path.join(root,'artifacts/media-cleanup.json'),'utf8'));
 return compileMediaApprovals({media,downloads,cleanup,readArtifact});
}
