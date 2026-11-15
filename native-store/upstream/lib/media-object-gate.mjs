import {createHash} from 'node:crypto';
const sha=body=>createHash('sha256').update(body).digest('hex');
export function validateWholeObjectEvidence(cleanup,policy,receipt) {
 if(policy?.version!=='whole-object-v1'||receipt?.version!==policy.version) throw new Error('Missing whole object evidence version');
 if(policy.sourceSetSha256&&sha(JSON.stringify(Object.keys(cleanup.images).sort().map(k=>[k,cleanup.images[k].sourceSha])))!==policy.sourceSetSha256)throw new Error('Complete whole object source set changed');
 if(policy.referenceSetSha256&&sha(JSON.stringify(Object.entries(cleanup.references||{}).sort(([a],[b])=>a<b?-1:a>b?1:0)))!==policy.referenceSetSha256)throw new Error('Complete whole object reference set changed');
 if(Object.entries(cleanup.images).some(([k,r])=>r.state==='approved_cleaned'&&!(k in policy.required)))throw new Error('uncovered whole object cleaned image');
 const rejected=new Set(policy.rejectedOutputSha256);
 for(const row of Object.values(cleanup.images))if(rejected.has(row.outputSha))throw new Error('Known retained physical sticker output cannot publish');
 for(const [key,requirement]of Object.entries(policy.required)){
  const current=cleanup.images[key],review=receipt.images?.[key];
  if(!current||!review)throw new Error('Missing whole object source coverage');
  if(requirement.sourceSha256!==current.sourceSha||review.sourceSha256!==current.sourceSha||review.outputSha256!==current.outputSha)throw new Error('Whole object source/output hash mismatch');
  if(requirement.acceptedOutputSha256!==undefined&&requirement.acceptedOutputSha256!==current.outputSha)throw new Error('Output differs from actually accepted whole object bytes');
  for(const name of ['outputRgbaSha256','maskPath','maskSha256','timeline'])if(name in requirement&&JSON.stringify(review[name])!==JSON.stringify(requirement[name]))throw new Error('Whole object decoded pixels, mask or frame timeline differ');
  if(review.width!==current.width||review.height!==current.height)throw new Error('Whole object dimensions mismatch');
  if(typeof review.reviewer!=='string'||!review.reviewer.trim())throw new Error('Missing whole object visual reviewer');
  const fields=review.fields||[],expected=requirement.fields;
  if(JSON.stringify(fields.map(f=>f.id).sort((a,b)=>a-b))!==JSON.stringify(expected.map(f=>f.id).sort((a,b)=>a-b)))throw new Error('Whole object field coverage mismatch');
  const byId=new Map(fields.map(f=>[f.id,f]));
  for(const field of expected){
   const proof=byId.get(field.id);
   for(const name of ['sourceFrame','durationMs','outputRgbaSha256','maskPath','maskSha256'])if(name in field&&proof[name]!==field[name])throw new Error('Whole object decoded frame, pixel or mask binding differs');
   if(proof.visualReview!==true)throw new Error('Incomplete whole object visual acceptance');
   if(field.kind==='already_removed_print'){
    if(proof.noPhysicalObjectRemains!==true)throw new Error('Incomplete whole object print acceptance');
    continue;
   }
   if(['wholeObjectRemoved','rimAndShadowRemoved','surfaceContinuous','edgesContinuous'].some(flag=>proof[flag]!==true))throw new Error('Incomplete whole object surface and edge acceptance');
   const box=proof.maskBox||[],[x0,y0,x1,y1]=field.box,{width:w,height:h}=current;
   if(box.length!==4||box.some(v=>!Number.isSafeInteger(v))||!(0<=box[0]&&box[0]<box[2]&&box[2]<=w&&0<=box[1]&&box[1]<box[3]&&box[3]<=h)||box[0]>Math.max(0,x0-2)||box[1]>Math.max(0,y0-2)||box[2]<Math.min(w,x1+2)||box[3]<Math.min(h,y1+2))throw new Error('Ink-only or invalid physical object footprint');
  }
 }
 return true;
}

export async function verifyWholeObjectPublication(cleanup,policy,policySha256,readArtifact){
 const audit=cleanup.wholeObjectAudit;
 if(!audit)throw new Error('Missing whole object publication evidence');
 if(audit.policySha256!==policySha256)throw new Error('Canonical whole object policy hash changed');
 if(typeof audit.receiptPath!=='string'||!/^artifacts\/media-finalization\/[a-zA-Z0-9-]+\.json$/.test(audit.receiptPath))throw new Error('Invalid whole object receipt path');
 const bytes=await readArtifact(audit.receiptPath,'media-finalization');
 if(sha(bytes)!==audit.receiptSha256)throw new Error('Whole object receipt hash changed');
 const receipt=JSON.parse(bytes);validateWholeObjectEvidence(cleanup,policy,receipt);
 if(policy.supplementalPass){
  const family=cleanup.publicationAudit?.requiredFamilies?.whole_object_supplemental,count=Object.keys(cleanup.images).length;
  if(family?.passVersion!==policy.supplementalPass||family.sourceUrls!==count||family.finalOutputUrls!==count)throw new Error('Complete whole object supplemental source/output coverage required');
 }
 const masks=new Map();
 for(const r of Object.values(policy.required))for(const f of [r,...r.fields])if(f.maskPath){
  if(!/^artifacts\/[a-zA-Z0-9-]+\/[a-zA-Z0-9/._-]+\.png$/.test(f.maskPath)||f.maskPath.split('/').includes('..')||!/^[a-f0-9]{64}$/.test(f.maskSha256||''))throw new Error('Invalid whole object mask binding');
  if(masks.has(f.maskPath)&&masks.get(f.maskPath)!==f.maskSha256)throw new Error('Conflicting whole object mask binding');masks.set(f.maskPath,f.maskSha256);
 }
 const entries=[...masks];
 for(let i=0;i<entries.length;i+=12)await Promise.all(entries.slice(i,i+12).map(async([p,h])=>{if(sha(await readArtifact(p,p.split('/')[1]))!==h)throw new Error('Whole object actual mask bytes changed');}));
 return true;
}
