import {createHash} from 'node:crypto';
const sha=b=>createHash('sha256').update(b).digest('hex');
export async function verifyCombinedReport(report,parentIndex,parentPass,readArtifact){
 const lineage=report.scanLineage,ref=parentIndex.get(report.fileSha256);
 if(!ref||lineage?.passVersion!==parentPass||lineage.path!==ref.path||lineage.sha256!==ref.reportSha256||!/^artifacts\/media-object-removal-20261102\/web-supplemental\/reports\/[a-f0-9]{64}\.json$/.test(ref.path))throw new Error('Combined scan lineage binding differs');
 const bytes=await readArtifact(ref.path,ref.path.split('/')[1]);
 if(sha(bytes)!==ref.reportSha256)throw new Error('Combined scan lineage parent bytes changed');
 const parent=JSON.parse(bytes),frames=r=>r.frames.map(f=>[f.frame,f.background,f.rgbSha256]);
 if(parent.fileSha256!==report.fileSha256||parent.passVersion!==parentPass||JSON.stringify(frames(parent))!==JSON.stringify(frames(report)))throw new Error('Combined scan lineage parent identity/decoded frames differ');
 const hit=h=>JSON.stringify(Object.entries(h).filter(([k])=>k!=='id').sort(([a],[b])=>a<b?-1:a>b?1:0)),current=new Set(report.hits.map(hit));
 if(parent.hits.some(h=>!current.has(hit(h))))throw new Error('Combined scan lineage dropped a parent detection');
}
