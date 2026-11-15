/** Private My Drive migration of fully approved local images. Node >=22. */
import { createHash, randomUUID } from 'node:crypto';
import { open, readFile, writeFile, rename, mkdir, unlink, realpath, lstat } from 'node:fs/promises';
import { dirname, resolve, join, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { compileMediaApprovals, inspectRaster } from '../lib/media-approvals.mjs';

const SOURCE_HOSTS = new Set(['witcdn.adoremobilya.com']);
const DRIVE = 'https://www.googleapis.com/drive/v3/';
const UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files';
const MAX_BYTES = 20_000_000;
const DEFAULT_ROOT = fileURLToPath(new URL('../',import.meta.url));
const EXTENSIONS = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/gif':'gif','image/avif':'avif'};
const FILE_FIELDS = 'id,mimeType,size,md5Checksum,parents,trashed,appProperties';
const MESSAGES = {
  AUTH_MISSING:'GOOGLE_ACCESS_TOKEN ortam değişkeni gerekli.',
  AUTH_EXPIRED:'Google yetkisi geçersiz veya süresi doldu. Aynı hesap ve OAuth uygulamasıyla yeniden yetkilendirin.',
  FOLDER_MISSING:'GOOGLE_DRIVE_FOLDER_ID ortam değişkeni gerekli.',
  INVALID_FOLDER:'Hedef, hesabın sahip olduğu paylaşılmamış ve yazılabilir bir My Drive klasörü olmalı.',
  ACCOUNT_MISMATCH:'Yetkili Google hesabı, açıkça belirtilen hedef hesapla eşleşmiyor.',
  ACCOUNT_MISSING:'Hedef Google hesabını --account-email veya GOOGLE_DRIVE_ACCOUNT_EMAIL ile açıkça belirtin.',
  INVALID_SOURCE:'Görsel adresi izin verilen Adore CDN kaynağından değil.',
  INVALID_IMAGE:'Görsel türü doğrulanamadı veya 20 MB sınırını aşıyor.',
  MEDIA_PENDING:'Tüm katalog görselleri ve son yayın onayı henüz hazır değil; Drive yüklemesi kapalı.',
  MEDIA_INTEGRITY:'Onaylı yerel görsel kapsamı, dosyası, özeti veya ölçüsü doğrulanamadı; Drive yüklemesi kapalı.',
  DRIVE_FAILED:'Drive işlemi tamamlanamadı. Yetki, kota ve bağlantıyı kontrol edip aynı manifest ile yeniden deneyin.',
  INTEGRITY:'Drive dosyasının içerik doğrulaması başarısız. Manifestteki kaydı inceleyin.',
  MANIFEST_MISMATCH:'Manifest başka bir hedef klasöre ait. Hedefi doğrulayın veya ayrı manifest seçin.',
  LOCKED:'Bu manifest için aktarım zaten çalışıyor. Süreç kapalıysa kilit dosyasını kontrol edin.',
  INVALID_CATALOG:'Ürün/görsel kataloğu geçersiz veya yinelenen ürün kimliği içeriyor.',
  INPUT:'Komut seçenekleri veya yerel dosya okunamadı. --help çıktısını kontrol edin.',
};

export class SafeMigrationError extends Error {
  constructor(code) { super(MESSAGES[code] || MESSAGES.DRIVE_FAILED); this.name='SafeMigrationError'; this.code=code; }
}

export function validateSourceUrl(value) {
  let url;
  if(typeof value!=='string'||/[\x00-\x20\x7f\\]/.test(value)) throw new SafeMigrationError('INVALID_SOURCE');
  try { url=new URL(value); } catch { throw new SafeMigrationError('INVALID_SOURCE'); }
  if (url.protocol!=='https:' || !SOURCE_HOSTS.has(url.hostname) || url.username || url.password || url.hash || (url.port && url.port!=='443')) throw new SafeMigrationError('INVALID_SOURCE');
  return url;
}

export function planImages(catalog) {
  if (!catalog || !Array.isArray(catalog.products)) throw new SafeMigrationError('INVALID_CATALOG');
  const ids=new Set(); const images=[];
  for (const product of catalog.products) {
    const id=String(product.id ?? '');
    if (!/^[A-Za-z0-9_-]+$/.test(id) || ids.has(id) || !Array.isArray(product.images)) throw new SafeMigrationError('INVALID_CATALOG');
    ids.add(id);
    product.images.forEach((sourceUrl,index) => {
      validateSourceUrl(sourceUrl);
      images.push({key:`${id}:${index}`,productId:id,index,code:String(product.code || id),sourceUrl});
    });
  }
  return images;
}

export function validateDestinationFolder(folder, expectedId) {
  if (folder?.id!==expectedId || folder.mimeType!=='application/vnd.google-apps.folder' || folder.ownedByMe!==true || folder.trashed || folder.driveId || folder.shared!==false || folder.capabilities?.canAddChildren!==true || !Array.isArray(folder.permissions) || folder.permissions.length!==1 || folder.permissions.some(p => p.type!=='user' || p.role!=='owner')) throw new SafeMigrationError('INVALID_FOLDER');
  return folder.id;
}

export function chooseResumeEntry(entry,file,folderId,sha256) {
  return entry?.folderId===folderId && entry.sha256===sha256 && file?.id===entry.fileId && !file.trashed && file.parents?.includes(folderId) && file.appProperties?.nodeno_sha256===sha256 && /^image\/(jpeg|png|webp|gif|avif)$/.test(file.mimeType || '') ? file.id : null;
}

export function classifyRetry(status,body) {
  return status===429 || [500,502,503,504].includes(status) || status===403 && body?.error?.errors?.some(e => ['rateLimitExceeded','userRateLimitExceeded','backendError'].includes(e.reason));
}

const sleep=ms => new Promise(resolve => setTimeout(resolve,ms));
const hash=(algorithm,bytes) => createHash(algorithm).update(bytes).digest('hex');
const queryEscape=value => String(value).replace(/\\/g,'\\\\').replace(/'/g,"\\'");

async function approvedLocalMedia(all,workspaceRoot,isolatedTestFixture=false) {
  let approval={status:'pending',publicationReady:false,approved:0,references:all.length,verifiedImages:0};
  const fail=code=>{const error=new SafeMigrationError(code);error.approval={...approval,status:code==='MEDIA_PENDING'?'pending':'invalid',errorCode:code};throw error;};
  try {
    const root=await realpath(workspaceRoot);
    let downloads,cleanup;
    try {
      downloads=JSON.parse(await readFile(join(root,'artifacts/media-download.json'),'utf8'));
      cleanup=JSON.parse(await readFile(join(root,'artifacts/media-cleanup.json'),'utf8'));
    } catch(error) {if(error.code==='ENOENT') fail('MEDIA_PENDING');throw error;}
    approval={...approval,publicationReady:cleanup.publicationReady===true,
      approved:Object.values(cleanup.images||{}).filter(item=>['approved_cleaned','approved_unmodified'].includes(item?.state)).length};
    if(cleanup.testOnly===true||downloads.testOnly===true||cleanup.inventoryOnly===true||cleanup.apply===false) fail('MEDIA_INTEGRITY');
    if(cleanup.publicationReady!==true) fail('MEDIA_PENDING');
    const readArtifact=async(relative,folder)=>{
      if(typeof relative!=='string'||!relative.startsWith(`artifacts/${folder}/`)||relative.includes('\\')||relative.split('/').some(part=>part==='..'||part==='')) fail('MEDIA_INTEGRITY');
      const filename=resolve(root,relative),details=await lstat(filename);
      if(details.isSymbolicLink()||!details.isFile()||details.size<1||details.size>MAX_BYTES) fail('MEDIA_INTEGRITY');
      const actual=await realpath(filename);
      if(!actual.startsWith(join(root,'artifacts',folder)+sep)) fail('MEDIA_INTEGRITY');
      const bytes=await readFile(actual);
      if(bytes.length<1||bytes.length>MAX_BYTES) fail('MEDIA_INTEGRITY');
      return bytes;
    };
    const media={};
    for(const item of all) (media[item.productId]??=[])[item.index]=item.sourceUrl;
    const checked=await compileMediaApprovals({media,downloads,cleanup,readArtifact,isolatedTestFixture});
    approval={...approval,status:'verified',verifiedImages:checked.manifest.uniqueCount,...(checked.testOnly?{testOnly:true}:{})};
    return {approval,async read(item) {
      try {
        const key=hash('sha256',item.sourceUrl),entry=cleanup.images[key],proof=checked.manifest.images[key];
        const bytes=await readArtifact(entry.path,'media-cleaned');
        const dimensions=inspectRaster(bytes,proof.mime);
        if(hash('sha256',bytes)!==proof.outputSha||bytes.length!==proof.bytes||dimensions.width!==proof.width||dimensions.height!==proof.height) fail('MEDIA_INTEGRITY');
        return {bytes,mimeType:proof.mime,extension:EXTENSIONS[proof.mime],sha256:proof.outputSha,md5:hash('md5',bytes),size:bytes.length,
          localPath:entry.path,approvalState:proof.state,sourceSha:proof.sourceSha,outputSha:proof.outputSha,width:proof.width,height:proof.height};
      } catch {fail('MEDIA_INTEGRITY');}
    }};
  } catch(error) {
    if(error instanceof SafeMigrationError) throw error;
    fail('MEDIA_INTEGRITY');
  }
}

export class DriveClient {
  constructor(token,{fetchImpl=fetch,pause=sleep}={}) { this.token=token; this.fetchImpl=fetchImpl; this.pause=pause; }
  async request(url,{method='GET',body,headers={},allowed=[200],attempts=5}={}) {
    const parsed=new URL(url);
    if (parsed.origin!=='https://www.googleapis.com') throw new SafeMigrationError('DRIVE_FAILED');
    for (let attempt=0;attempt<attempts;attempt++) {
      let response;
      try { response=await this.fetchImpl(url,{method,body,headers:{...headers,Authorization:`Bearer ${this.token}`},redirect:'error',signal:AbortSignal.timeout(90000)}); }
      catch {
        if (attempt===attempts-1) throw new SafeMigrationError('DRIVE_FAILED');
        await this.pause(Math.min(32000,1000*2**attempt)+Math.random()*500); continue;
      }
      if (allowed.includes(response.status)) return response;
      let details={}; try { details=await response.json(); } catch { /* Never expose upstream bodies. */ }
      if (response.status===401) throw new SafeMigrationError('AUTH_EXPIRED');
      if (!classifyRetry(response.status,details) || attempt===attempts-1) throw new SafeMigrationError('DRIVE_FAILED');
      const retryAfter=Number(response.headers.get('retry-after'));
      await this.pause(Math.min(60000,Math.max(1000*2**attempt,Number.isFinite(retryAfter)?retryAfter*1000:0))+Math.random()*500);
    }
    throw new SafeMigrationError('DRIVE_FAILED');
  }
  async json(path,options) { const response=await this.request(new URL(path,DRIVE).href,options); return response.json(); }
  async getFile(id) {
    const response=await this.request(`${DRIVE}files/${encodeURIComponent(id)}?fields=${encodeURIComponent(FILE_FIELDS)}`,{allowed:[200,404]});
    return response.status===404 ? null : response.json();
  }
  async verifyFolder(folderId,expectedEmail) {
    if(typeof expectedEmail!=='string'||expectedEmail.length>254||!/^\S+@\S+\.\S+$/.test(expectedEmail)) throw new SafeMigrationError('ACCOUNT_MISSING');
    if (!/^[a-zA-Z0-9_-]{1,200}$/.test(folderId)) throw new SafeMigrationError('INVALID_FOLDER');
    const account=await this.json('about?fields=user(emailAddress)');
    if (account.user?.emailAddress?.toLowerCase()!==expectedEmail.toLowerCase()) throw new SafeMigrationError('ACCOUNT_MISMATCH');
    const folder=await this.json(`files/${encodeURIComponent(folderId)}?fields=id,mimeType,ownedByMe,trashed,shared,driveId,capabilities(canAddChildren),permissions(type,role)`);
    validateDestinationFolder(folder,folderId);
  }
  async findByHash(folderId,sha256) {
    const q=`'${queryEscape(folderId)}' in parents and trashed = false and appProperties has { key='nodeno_sha256' and value='${sha256}' }`;
    let pageToken; let result=null;
    do {
      const search=new URLSearchParams({q,spaces:'drive',pageSize:'100',fields:`nextPageToken,incompleteSearch,files(${FILE_FIELDS})`});
      if (pageToken) search.set('pageToken',pageToken);
      const page=await this.json(`files?${search}`);
      if (page.incompleteSearch) throw new SafeMigrationError('DRIVE_FAILED');
      for (const file of page.files ?? []) if (!result && file.appProperties?.nodeno_sha256===sha256 && file.parents?.includes(folderId)) result=file;
      pageToken=page.nextPageToken;
    } while (pageToken);
    return result;
  }
  async reserveId() {
    const data=await this.json('files/generateIds?count=1&space=drive&type=files');
    if (!/^[a-zA-Z0-9_-]+$/.test(data.ids?.[0] ?? '')) throw new SafeMigrationError('DRIVE_FAILED');
    return data.ids[0];
  }
  async uploadReserved(fileId,folderId,image) {
    const existing=await this.getFile(fileId);
    if (existing) return existing;
    const metadata={id:fileId,name:`nodeno-${image.sha256}.${image.extension}`,mimeType:image.mimeType,parents:[folderId],appProperties:{nodeno_sha256:image.sha256,nodeno_source:'approved-local-v1'}};
    // Pre-generated file IDs make a completed-but-unacknowledged create safe to retry.
    let start;
    try {
      start=await this.request(`${UPLOAD}?uploadType=resumable&fields=${encodeURIComponent(FILE_FIELDS)}&ignoreDefaultVisibility=true`,{method:'POST',body:JSON.stringify(metadata),headers:{'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Type':image.mimeType,'X-Upload-Content-Length':String(image.size)},allowed:[200,201,409]});
    } catch (error) { const recovered=await this.getFile(fileId).catch(()=>null); if (recovered) return recovered; throw error; }
    if (start.status===409) { const recovered=await this.getFile(fileId); if (recovered) return recovered; throw new SafeMigrationError('DRIVE_FAILED'); }
    const session=start.headers.get('location'); await start.body?.cancel();
    let sessionUrl;
    try { sessionUrl=new URL(session); } catch { throw new SafeMigrationError('DRIVE_FAILED'); }
    if (sessionUrl.origin!=='https://www.googleapis.com' || !sessionUrl.pathname.startsWith('/upload/drive/v3/files')) throw new SafeMigrationError('DRIVE_FAILED');
    let offset=0;
    for (let attempt=0;attempt<5;attempt++) {
      try {
        const response=await this.request(sessionUrl.href,{method:'PUT',body:image.bytes.subarray(offset),headers:{'Content-Type':image.mimeType,'Content-Length':String(image.size-offset),'Content-Range':`bytes ${offset}-${image.size-1}/${image.size}`},allowed:[200,201,308,404],attempts:1});
        if ([200,201].includes(response.status)) return response.json();
        if (response.status===404) { const recovered=await this.getFile(fileId); if (recovered) return recovered; throw new SafeMigrationError('DRIVE_FAILED'); }
        const received=response.headers.get('range')?.match(/^bytes=0-(\d+)$/); await response.body?.cancel();
        offset=received?Number(received[1])+1:0;
      } catch (error) {
        if (error.code==='AUTH_EXPIRED') throw error;
        const recovered=await this.getFile(fileId).catch(()=>null); if (recovered) return recovered;
        // Query acknowledged bytes before resending a partially received image.
        const status=await this.request(sessionUrl.href,{method:'PUT',headers:{'Content-Length':'0','Content-Range':`bytes */${image.size}`},allowed:[200,201,308,404]});
        if ([200,201].includes(status.status)) return status.json();
        if (status.status===404) throw new SafeMigrationError('DRIVE_FAILED');
        const received=status.headers.get('range')?.match(/^bytes=0-(\d+)$/); await status.body?.cancel();
        offset=received?Number(received[1])+1:0;
      }
      if (!Number.isSafeInteger(offset) || offset<0 || offset>=image.size) throw new SafeMigrationError('DRIVE_FAILED');
      await this.pause(1000*2**attempt);
    }
    throw new SafeMigrationError('DRIVE_FAILED');
  }
}

function verifyFile(file,folderId,image) {
  if (!file || file.trashed || !file.parents?.includes(folderId) || file.appProperties?.nodeno_sha256!==image.sha256 || file.mimeType!==image.mimeType || Number(file.size)!==image.size || file.md5Checksum!==image.md5) throw new SafeMigrationError('INTEGRITY');
  return file;
}

export async function migrate({catalog,manifestPath,folderId,token,expectedEmail,getCredentials,workspaceRoot=DEFAULT_ROOT,upload=false,limit=Infinity,concurrency=1,fetchImpl=fetch,onProgress=()=>{},isolatedTestFixture=false}) {
  if(isolatedTestFixture&&(!process.env.NODE_TEST_CONTEXT||resolve(workspaceRoot)===resolve(DEFAULT_ROOT)||!/^nodeno-drive-/.test(resolve(workspaceRoot).split(/[\\/]/).at(-1))||(upload&&(fetchImpl===fetch||token!=='test-private-token'||getCredentials))))throw new SafeMigrationError('MEDIA_INTEGRITY');
  const all=planImages(catalog); const planned=all.slice(0,limit);
  const summary={mode:upload?'upload':'dry-run',products:catalog.products.length,images:all.length,selected:planned.length,uploaded:0,reused:0,failed:0};
  let localMedia;
  try {localMedia=await approvedLocalMedia(all,workspaceRoot,isolatedTestFixture);summary.approval=localMedia.approval;}
  catch(error) {if(upload) throw error;return {...summary,approval:error.approval||{status:'invalid',publicationReady:false,errorCode:'MEDIA_INTEGRITY'}};}
  if (!upload) return summary;
  if(getCredentials) ({folderId,token,expectedEmail}=await getCredentials());
  if (!token) throw new SafeMigrationError('AUTH_MISSING');
  if (!folderId) throw new SafeMigrationError('FOLDER_MISSING');
  const client=new DriveClient(token,{fetchImpl});
  await client.verifyFolder(folderId,expectedEmail);
  await mkdir(dirname(manifestPath),{recursive:true});
  let lock;
  try { lock=await open(`${manifestPath}.lock`,'wx',0o600); await lock.writeFile(JSON.stringify({pid:process.pid,startedAt:new Date().toISOString()})); }
  catch { throw new SafeMigrationError('LOCKED'); }
  let state={version:1,folderId,images:{},...(isolatedTestFixture?{testOnly:true}:{})}; let saveQueue=Promise.resolve();
  const save=() => {
    const snapshot=JSON.stringify({...state,updatedAt:new Date().toISOString()},null,2)+'\n';
    saveQueue=saveQueue.then(async()=>{const temp=`${manifestPath}.${randomUUID()}.tmp`;await writeFile(temp,snapshot,{mode:0o600});await rename(temp,manifestPath);});
    return saveQueue;
  };
  try {
    try { state=JSON.parse(await readFile(manifestPath,'utf8')); }
    catch (error) { if(error.code!=='ENOENT') throw new SafeMigrationError('INPUT'); }
    if (state.version!==1 || state.folderId!==folderId || !state.images || typeof state.images!=='object') throw new SafeMigrationError('MANIFEST_MISMATCH');
    let cursor=0; let fatal=null; const hashes=new Map();
    const processImage=async item => {
      const image=await localMedia.read(item);
      const previous=state.images[item.key];
      const record={productId:item.productId,index:item.index,sourceUrl:item.sourceUrl,folderId,sha256:image.sha256,md5:image.md5,mimeType:image.mimeType,size:image.size,
        localPath:image.localPath,approvalState:image.approvalState,sourceSha:image.sourceSha,outputSha:image.outputSha,width:image.width,height:image.height,extension:image.extension};
      if (!hashes.has(image.sha256)) hashes.set(image.sha256,(async()=>{
        if (previous?.fileId && previous.sha256===image.sha256 && previous.folderId===folderId) {
          const resumed=await client.getFile(previous.fileId);
          if (chooseResumeEntry(previous,resumed,folderId,image.sha256)) { verifyFile(resumed,folderId,image); return {file:resumed,reused:true}; }
        }
        const matching=await client.findByHash(folderId,image.sha256);
        if (matching) { verifyFile(matching,folderId,image); return {file:matching,reused:true}; }
        // Save generated IDs before any create request. The same ID survives interruptions.
        const reservedId=previous?.status==='reserved' && previous.sha256===image.sha256 && previous.folderId===folderId ? previous.fileId : await client.reserveId();
        state.images[item.key]={...record,status:'reserved',fileId:reservedId}; await save();
        const file=await client.uploadReserved(reservedId,folderId,image);
        // Always read back independently; upload success alone is insufficient.
        const readback=await client.getFile(file.id); verifyFile(readback,folderId,image);
        return {file:readback,reused:false};
      })());
      const result=await hashes.get(image.sha256);
      const existingInRun=Object.values(state.images).some(e=>e.status==='uploaded' && e.fileId===result.file.id);
      state.images[item.key]={...record,status:'uploaded',fileId:result.file.id,verifiedAt:new Date().toISOString()}; await save();
      summary[result.reused||existingInRun?'reused':'uploaded']++;
    };
    const worker=async()=>{
      while (!fatal && cursor<planned.length) {
        const item=planned[cursor++];
        try { await processImage(item); }
        catch (error) {
          const safe=error instanceof SafeMigrationError?error:new SafeMigrationError('DRIVE_FAILED');
          if(safe.code==='MEDIA_INTEGRITY') {summary.approval=safe.approval;fatal=safe;}
          // Keep a reserved ID on failure: replacing it would lose idempotency after an ambiguous upload.
          const previous=state.images[item.key];
          state.images[item.key]={...previous,productId:item.productId,index:item.index,sourceUrl:item.sourceUrl,folderId,status:previous?.status==='reserved'?'reserved':'error',errorCode:safe.code};
          await save(); summary.failed++;
          if (safe.code==='AUTH_EXPIRED') fatal=safe;
        }
        onProgress({...summary,completed:summary.uploaded+summary.reused+summary.failed});
      }
    };
    await Promise.all(Array.from({length:Math.max(1,Math.min(3,concurrency))},worker));
    await saveQueue;
    if (fatal) throw fatal;
    return summary;
  } finally { await saveQueue.catch(()=>{}); await lock.close(); await unlink(`${manifestPath}.lock`).catch(()=>{}); }
}

function parseArgs(args) {
  const options={upload:false,catalog:'data/catalog-source.json',manifest:'artifacts/drive-manifest.json',concurrency:1,limit:Infinity};
  for (let i=0;i<args.length;i++) {
    const arg=args[i];
    if (arg==='--upload'||arg==='--apply') options.upload=true;
    else if (arg==='--dry-run') options.upload=false;
    else if (arg==='--help') options.help=true;
    else if (['--catalog','--manifest','--concurrency','--limit','--account-email','--folder'].includes(arg)) {
      if (!args[i+1] || args[i+1].startsWith('--')) throw new SafeMigrationError('INPUT');
      const key=arg.slice(2); const value=args[++i]; options[key]=['concurrency','limit'].includes(key)?Number(value):value;
    } else throw new SafeMigrationError('INPUT');
  }
  if (!Number.isInteger(options.concurrency) || options.concurrency<1 || options.concurrency>3 || options.limit!==Infinity && (!Number.isSafeInteger(options.limit) || options.limit<1)) throw new SafeMigrationError('INPUT');
  return options;
}

async function main() {
  try {
    const options=parseArgs(process.argv.slice(2));
    if(options.help) { console.log('NODENO approved-local private Drive migration\nnode scripts/drive-migrate.mjs [--dry-run | --upload | --apply] [--catalog PATH] [--manifest PATH] [--limit N] [--concurrency 1..3] [--account-email EMAIL] [--folder ID]\nDefault: dry-run, no network, credentials or writes.\nAll catalog media must pass artifacts/media-cleanup.json publicationReady + local SHA/dimensions before upload.\nUpload requires GOOGLE_ACCESS_TOKEN, GOOGLE_DRIVE_FOLDER_ID and explicit GOOGLE_DRIVE_ACCOUNT_EMAIL (legacy GOOGLE_EXPECTED_EMAIL accepted).\nTokens must only be supplied as environment variables.'); return; }
    const catalog=JSON.parse(await readFile(resolve(options.catalog),'utf8'));
    const summary=await migrate({catalog,manifestPath:resolve(options.manifest),getCredentials:()=>({folderId:options.folder||process.env.GOOGLE_DRIVE_FOLDER_ID,token:process.env.GOOGLE_ACCESS_TOKEN,expectedEmail:options['account-email']||process.env.GOOGLE_DRIVE_ACCOUNT_EMAIL||process.env.GOOGLE_EXPECTED_EMAIL}),upload:options.upload,limit:options.limit,concurrency:options.concurrency,onProgress:s=>{if(s.completed%25===0)console.log(JSON.stringify(s));}});
    console.log(JSON.stringify(summary)); if(summary.failed) process.exitCode=2;
  } catch (error) { const safe=error instanceof SafeMigrationError?error:new SafeMigrationError('INPUT'); console.error(JSON.stringify({code:safe.code,message:safe.message})); process.exitCode=1; }
}

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) await main();
