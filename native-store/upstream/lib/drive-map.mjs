export function selectDriveMappings(manifest,media) {
 const result={};
 for(const [key,value] of Object.entries(manifest?.images||{})) {
  const match=/^([A-Za-z0-9_-]+):(0|[1-9]\d*)$/.exec(key);
  if(!match || !value || value.status!=='uploaded' || !Number.isFinite(Date.parse(value.verifiedAt))) continue;
  if(!/^[A-Za-z0-9_-]{8,180}$/.test(value.fileId)||!/^[A-Za-z0-9_-]{8,180}$/.test(value.folderId)) continue;
  if(!/^[a-f0-9]{64}$/i.test(value.sha256)||!/^[a-f0-9]{32}$/i.test(value.md5)) continue;
  if(!['image/jpeg','image/png','image/webp','image/avif','image/gif'].includes(value.mimeType)||!Number.isSafeInteger(value.size)||value.size<=0||value.size>20000000) continue;
  if(media[match[1]]?.[Number(match[2])]!==value.sourceUrl) continue;
  result[key]={fileId:value.fileId};
 }
 return result;
}
