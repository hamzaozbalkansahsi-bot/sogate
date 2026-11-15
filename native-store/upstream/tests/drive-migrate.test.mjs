import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm, writeFile, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { planImages, validateSourceUrl, validateDestinationFolder, chooseResumeEntry, classifyRetry, SafeMigrationError, migrate as migrateProduction } from '../scripts/drive-migrate.mjs';
const migrate=options=>migrateProduction({...options,isolatedTestFixture:true});
test('production migration rejects synthetic approvals and test mode cannot use real network or credentials',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));try{
  await approvalFixture(dir);const api=driveBoundary(),options={catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath:join(dir,'manifest.json'),fetchImpl:api.fetchImpl};
  await assert.rejects(migrateProduction(options),e=>e.code==='MEDIA_INTEGRITY');assert.equal(api.counts.creates,0);assert.equal(api.counts.about,0);
  await assert.rejects(migrateProduction({...options,isolatedTestFixture:true,fetchImpl:globalThis.fetch}),e=>e.code==='MEDIA_INTEGRITY');
  await assert.rejects(migrateProduction({...options,isolatedTestFixture:true,getCredentials:()=>assert.fail('fixture read real credentials')}),e=>e.code==='MEDIA_INTEGRITY');
 }finally{await rm(dir,{recursive:true,force:true});}
});

test('plans every product image with stable product:index keys, including repeated media', () => {
  const catalog = { products: [{id:'42',code:'S1',images:['https://witcdn.adoremobilya.com/a.jpg','https://witcdn.adoremobilya.com/b.png']},{id:'43',images:['https://witcdn.adoremobilya.com/a.jpg']}] };
  assert.deepEqual(planImages(catalog).map(x => x.key), ['42:0','42:1','43:0']);
});

test('rejects noncatalog hosts, credentials, alternate ports and local URLs', () => {
  for (const url of ['http://witcdn.adoremobilya.com/a.jpg','https://witcdn.adoremobilya.com.evil.test/a.jpg','https://user:secret@witcdn.adoremobilya.com/a.jpg','https://witcdn.adoremobilya.com:8443/a.jpg','https://127.0.0.1/a.jpg','file:///x']) {
    assert.throws(() => validateSourceUrl(url), SafeMigrationError);
  }
  assert.equal(validateSourceUrl('https://witcdn.adoremobilya.com/a.jpg').hostname,'witcdn.adoremobilya.com');
});

test('rejects shared folders, team drives, shortcuts and folders not owned by current account', () => {
  const good = {id:'folder',mimeType:'application/vnd.google-apps.folder',ownedByMe:true,trashed:false,shared:false,capabilities:{canAddChildren:true},permissions:[{type:'user',role:'owner'}]};
  assert.equal(validateDestinationFolder(good, 'folder'), 'folder');
  for (const overrides of [{driveId:'team'},{ownedByMe:false},{shared:true},{trashed:true},{mimeType:'application/vnd.google-apps.shortcut'},{permissions:[{type:'anyone',role:'reader'}]},{permissions:undefined},{permissions:[]},{capabilities:{canAddChildren:false}}]) {
    assert.throws(() => validateDestinationFolder({...good,...overrides},'folder'), SafeMigrationError);
  }
});

test('resume reuses only verified metadata from same folder and matching content', () => {
  const entry={status:'uploaded',fileId:'driveid',folderId:'folder',sha256:'abc'};
  const file={id:'driveid',parents:['folder'],appProperties:{nodeno_sha256:'abc'},mimeType:'image/jpeg',trashed:false};
  assert.equal(chooseResumeEntry(entry,file,'folder','abc'), 'driveid');
  assert.equal(chooseResumeEntry(entry,{...file,trashed:true},'folder','abc'), null);
  assert.equal(chooseResumeEntry(entry,{...file,parents:['other']},'folder','abc'), null);
  assert.equal(chooseResumeEntry(entry,file,'folder','new-content'), null);
  assert.equal(chooseResumeEntry({...entry,folderId:'other'},file,'folder','abc'), null);
});

test('retries quota and transient errors, stops on expired credential and permission failures', () => {
  assert.equal(classifyRetry(403,{error:{errors:[{reason:'userRateLimitExceeded'}]}}),true);
  assert.equal(classifyRetry(429,{}),true);
  assert.equal(classifyRetry(503,{}),true);
  assert.equal(classifyRetry(401,{}),false);
  assert.equal(classifyRetry(403,{error:{errors:[{reason:'insufficientFilePermissions'}]}}),false);
});

test('safe errors never echo upstream response, token or URL query', () => {
  const secret='secret-bearer-token';
  const err=new SafeMigrationError('AUTH_EXPIRED', {access_token:secret});
  assert.equal(String(err).includes(secret),false);
  assert.equal(err.code,'AUTH_EXPIRED');
});

const imageBytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAMAAAACCAIAAAASFvFNAAAAC0lEQVR4nGNgwAQAABQAAX3+Hu4AAAAASUVORK5CYII=','base64');
const originalBytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAMAAAACCAIAAAASFvFNAAAAFElEQVR4nGP8//8/AxgwQSgGBgYANgYDARtTfJEAAAAASUVORK5CYII=','base64');
const sha256=createHash('sha256').update(imageBytes).digest('hex');
const md5=createHash('md5').update(imageBytes).digest('hex');
const sampleCatalog={products:[{id:'42',code:'S1',images:['https://witcdn.adoremobilya.com/a.jpg']},{id:'43',code:'S2',images:['https://witcdn.adoremobilya.com/a.jpg']}]};
async function approvalFixture(directory,{catalog=sampleCatalog,state='approved_cleaned'}={}) {
  await mkdir(join(directory,'artifacts/media-originals'),{recursive:true});
  await mkdir(join(directory,'artifacts/media-cleaned'),{recursive:true});
  const references={},downloads={},images={};
  const source=state==='approved_unmodified'?imageBytes:originalBytes;
  for(const item of planImages(catalog)) {
    const key=createHash('sha256').update(item.sourceUrl).digest('hex');
    references[item.key]=key;
    const sourcePath=`artifacts/media-originals/${key}.png`,outputPath=`artifacts/media-cleaned/${key}.png`;
    await writeFile(join(directory,sourcePath),source);
    await writeFile(join(directory,outputPath),imageBytes);
    downloads[key]={status:'verified',url:item.sourceUrl,path:sourcePath,sha256:createHash('sha256').update(source).digest('hex'),bytes:source.length,width:3,height:2};
    images[key]={state,sourceSha:downloads[key].sha256,outputSha:sha256,path:outputPath,bytes:imageBytes.length,mime:'image/png',width:3,height:2};
  }
  const download={schemaVersion:1,references,images:downloads};
  const cleanup={schemaVersion:1,publicationReady:true,references,images};
  const policy=JSON.parse(await readFile(new URL('../data/media-audit-policy.json',import.meta.url),'utf8'));
  const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
  const families={};
  await mkdir(join(directory,'artifacts/media-finalization'),{recursive:true});
  for(const [name,version] of [['flame','65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d'],['small_badge',policy.smallBadgePass]]) {
    const reports=Object.entries(images).flatMap(([key,row])=>[{fileSha256:row.sourceSha,roles:[{urlSha:key,role:'source'}]},{fileSha256:row.outputSha,roles:[{urlSha:key,role:'current_output'}]}]);
    const reportBindings=[];
    const folder=name==='flame'?'media-symbol-audit':'media-physical-badge-audit';await mkdir(join(directory,'artifacts',folder,'reports'),{recursive:true});
    for(const report of reports) {
      report.path=`artifacts/${folder}/reports/${report.fileSha256}.json`;report.hits=0;
      const bytes=Buffer.from(JSON.stringify({fileSha256:report.fileSha256,passVersion:version,candidateHits:0,hits:[],frameCount:1,compositesScanned:1,frames:[{frame:0,background:'white',rgbSha256:'b'.repeat(64)}]}));await writeFile(join(directory,report.path),bytes);reportBindings.push([report.fileSha256,digest(bytes)]);
    }
    const receipt=Buffer.from(JSON.stringify({passVersion:version,referenceSha256:policy.smallBadgeReferences,allSourceUrlsScanned:true,sourceReferences:Object.keys(references).length,reports}));
    const dispositions=Buffer.from(JSON.stringify({passVersion:version,receiptSha256:digest(receipt),hits:{}}));
    const family={passVersion:version,sourceUrls:Object.keys(images).length,finalOutputUrls:Object.keys(images).length,reviewedRelevantHits:0,reportBindingsSha256:digest(JSON.stringify(reportBindings.sort()))};
    for(const [kind,bytes] of [['receipt',receipt],['dispositions',dispositions]]) {
      const filename=`artifacts/media-finalization/${name}-${kind}.json`;await writeFile(join(directory,filename),bytes);family[kind+'Path']=filename;family[kind+'Sha256']=digest(bytes);
    }
    families[name]=family;
  }
  cleanup.publicationAudit={policy:policy.policy,manifestBindingSha256:digest(JSON.stringify([Object.entries(references).sort(),Object.keys(images).sort().map(key=>[key,images[key].state,images[key].sourceSha,images[key].outputSha,null,null,null])])),requiredFamilies:families};
  const save=()=>writeFile(join(directory,'artifacts/media-cleanup.json'),JSON.stringify(cleanup));
  await writeFile(join(directory,'artifacts/media-download.json'),JSON.stringify(download));
  await save();
  return {download,cleanup,save};
}
function driveBoundary({existing=[],expire=false}={}) {
  const files=new Map(existing.map(f=>[f.id,f])); const sessions=new Map();
  const counts={creates:0,generates:0,downloads:0,reads:0,about:0,folders:0};
  const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
  const fetchImpl=async (value,options={}) => {
    const url=new URL(value); const method=options.method||'GET';
    if(url.hostname==='witcdn.adoremobilya.com') { counts.downloads++; assert.fail('raw supplier CDN download is prohibited'); }
    assert.equal(url.origin,'https://www.googleapis.com');
    assert.equal(options.headers.Authorization,'Bearer test-private-token');
    if(expire) return json({error:{message:'test-private-token',code:401}},401);
    if(url.pathname==='/drive/v3/about') {counts.about++;return json({user:{emailAddress:'new-owner@example.test'}});}
    if(url.pathname==='/drive/v3/files/folder') {counts.folders++;return json({id:'folder',mimeType:'application/vnd.google-apps.folder',ownedByMe:true,trashed:false,shared:false,capabilities:{canAddChildren:true},permissions:[{type:'user',role:'owner'}]});}
    if(url.pathname==='/drive/v3/files/generateIds') { counts.generates++; return json({ids:[`new-file-${counts.generates}`]}); }
    if(url.pathname==='/drive/v3/files') return json({files:[...files.values()],incompleteSearch:false});
    if(url.pathname.startsWith('/drive/v3/files/')) { counts.reads++; const id=url.pathname.split('/').at(-1); return files.has(id)?json(files.get(id)):json({},404); }
    if(url.pathname==='/upload/drive/v3/files' && method==='POST') {
      const meta=JSON.parse(options.body); counts.creates++; sessions.set(meta.id,meta);
      assert.equal(meta.mimeType,'image/png');
      assert.equal(meta.name,`nodeno-${sha256}.png`);
      assert.equal(meta.appProperties.nodeno_source,'approved-local-v1');
      return new Response(null,{status:200,headers:{location:`https://www.googleapis.com/upload/drive/v3/files?upload_id=${meta.id}`}});
    }
    if(url.pathname==='/upload/drive/v3/files' && method==='PUT') {
      const id=url.searchParams.get('upload_id'); const meta=sessions.get(id);
      assert.deepEqual(Buffer.from(options.body),imageBytes,'Upload must use cleaned local bytes');
      assert.notDeepEqual(Buffer.from(options.body),originalBytes);
      assert.ok(meta); const file={...meta,size:String(options.body.byteLength),md5Checksum:md5,trashed:false}; files.set(id,file); return json(file);
    }
    throw Error('Unexpected transport route');
  };
  return {files,counts,fetchImpl};
}

test('dry-run plans full media without credentials, network, local manifest or writes',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-dry-run-'));
  try {
    const manifestPath=join(dir,'manifest.json');
    const report=await migrate({catalog:sampleCatalog,workspaceRoot:dir,manifestPath,upload:false,getCredentials:()=>assert.fail('dry run read credentials'),fetchImpl:()=>assert.fail('dry run used network')});
    assert.equal(report.images,2); assert.equal(report.uploaded,0); assert.equal(report.mode,'dry-run');
    assert.equal(report.approval.status,'pending');
    assert.equal(report.approval.publicationReady,false);
    await assert.rejects(readFile(manifestPath),{code:'ENOENT'});
    assert.deepEqual(await readdir(dir),[],'Dry run must leave its empty workspace unchanged');
  } finally {await rm(dir,{recursive:true,force:true});}
});

test('equal media uploads once, saves verified mappings, and second execution creates no duplicate',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    const api=driveBoundary(); const manifestPath=join(dir,'manifest.json');
    await approvalFixture(dir);
    const settings={catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath,concurrency:2,fetchImpl:api.fetchImpl};
    const first=await migrate(settings);
    assert.equal(first.uploaded,1); assert.equal(first.reused,1); assert.equal(first.failed,0);
    assert.equal(api.counts.creates,1);
    assert.equal(api.counts.downloads,0);
    const saved=JSON.parse(await readFile(manifestPath,'utf8'));
    assert.equal(saved.images['42:0'].fileId,saved.images['43:0'].fileId);
    assert.equal(saved.images['42:0'].md5,md5);
    assert.equal(saved.images['42:0'].mimeType,'image/png');
    assert.equal(saved.images['42:0'].outputSha,sha256);
    assert.equal(saved.images['42:0'].width,3);
    assert.equal(JSON.stringify(saved).includes('test-private-token'),false);
    const second=await migrate(settings);
    assert.equal(second.uploaded,0); assert.equal(second.reused,2); assert.equal(second.failed,0);
    assert.equal(api.counts.creates,1);
  } finally { await rm(dir,{recursive:true,force:true}); }
});

test('an interrupted create keeps its pre-generated file ID rather than reserving another',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    const api=driveBoundary(); const manifestPath=join(dir,'manifest.json');
    await approvalFixture(dir,{catalog:{products:[sampleCatalog.products[0]]}});
    await writeFile(manifestPath,JSON.stringify({version:1,folderId:'folder',images:{'42:0':{status:'reserved',fileId:'known-reserved',folderId:'folder',sha256}}}));
    const result=await migrate({catalog:{products:[sampleCatalog.products[0]]},workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath,fetchImpl:api.fetchImpl});
    assert.equal(result.uploaded,1); assert.equal(api.counts.generates,0);
    const saved=JSON.parse(await readFile(manifestPath,'utf8')); assert.equal(saved.images['42:0'].fileId,'known-reserved');
  } finally { await rm(dir,{recursive:true,force:true}); }
});

test('an expired token stops before source transfer and hides upstream secret text',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    await approvalFixture(dir);
    const api=driveBoundary({expire:true});
    await assert.rejects(migrate({catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath:join(dir,'unused.json'),fetchImpl:api.fetchImpl}),error=>error.code==='AUTH_EXPIRED'&&!String(error).includes('test-private-token'));
    assert.equal(api.counts.downloads,0); assert.equal(api.counts.creates,0);
  } finally {await rm(dir,{recursive:true,force:true});}
});

test('unmodified approved local images are uploaded without a supplier fetch',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    await approvalFixture(dir,{state:'approved_unmodified'});
    const api=driveBoundary();
    const result=await migrate({catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath:join(dir,'manifest.json'),fetchImpl:api.fetchImpl});
    assert.equal(result.failed,0);assert.equal(api.counts.creates,1);assert.equal(api.counts.downloads,0);
  } finally {await rm(dir,{recursive:true,force:true});}
});

test('full approval gate rejects pending, incomplete, changed, missing and test-only media before credentials or Google calls',async t=>{
  const cases={
    pending:async f=>{f.cleanup.publicationReady=false;await f.save();},
    unapproved:async f=>{Object.values(f.cleanup.images)[0].state='review_required';await f.save();},
    incomplete:async f=>{delete f.cleanup.references['43:0'];await f.save();},
    changed:async(f,dir)=>{await writeFile(join(dir,Object.values(f.cleanup.images)[0].path),originalBytes);},
    missing:async(f,dir)=>{await rm(join(dir,Object.values(f.cleanup.images)[0].path));},
    dimensions:async f=>{Object.values(f.cleanup.images)[0].width=4;await f.save();},
    outside:async f=>{Object.values(f.cleanup.images)[0].path='data/catalog-source.json';await f.save();},
    testOnly:async f=>{f.cleanup.testOnly=true;await f.save();},
  };
  for(const [name,mutate] of Object.entries(cases)) await t.test(name,async()=>{
    const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
    try {
      const fixture=await approvalFixture(dir);await mutate(fixture,dir);
      const settings={catalog:sampleCatalog,workspaceRoot:dir,upload:true,limit:1,manifestPath:join(dir,'manifest.json'),getCredentials:()=>assert.fail('gate read credentials'),fetchImpl:()=>assert.fail('gate called Google/CDN')};
      await assert.rejects(migrate(settings),error=>['MEDIA_PENDING','MEDIA_INTEGRITY'].includes(error.code));
      await assert.rejects(readFile(settings.manifestPath),{code:'ENOENT'});
      const dry=await migrate({...settings,upload:false});
      assert.notEqual(dry.approval.status,'verified');
    } finally {await rm(dir,{recursive:true,force:true});}
  });
});

test('a verified dry run needs no credentials or Google account',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    await approvalFixture(dir);
    const result=await migrate({catalog:sampleCatalog,workspaceRoot:dir,getCredentials:()=>assert.fail('dry run read credentials'),fetchImpl:()=>assert.fail('dry run called Google')});
    assert.equal(result.approval.status,'verified');assert.equal(result.approval.publicationReady,true);
    assert.equal(result.approval.verifiedImages,1);assert.equal(result.images,2);assert.equal(result.uploaded,0);
  } finally {await rm(dir,{recursive:true,force:true});}
});

test('explicit target account is required and wrong token account cannot inspect target folder or create files',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    await approvalFixture(dir);
    const settings={catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',manifestPath:join(dir,'manifest.json')};
    await assert.rejects(migrate({...settings,fetchImpl:()=>assert.fail('missing account performed network')}),error=>error.code==='ACCOUNT_MISSING');
    const api=driveBoundary();
    await assert.rejects(migrate({...settings,expectedEmail:'different-owner@example.test',fetchImpl:api.fetchImpl}),error=>error.code==='ACCOUNT_MISMATCH');
    assert.equal(api.counts.about,1);assert.equal(api.counts.folders,0);assert.equal(api.counts.creates,0);assert.equal(api.counts.generates,0);
    await assert.rejects(readFile(settings.manifestPath),{code:'ENOENT'});
  } finally {await rm(dir,{recursive:true,force:true});}
});

test('local output changed after preflight is rechecked before any upload and has no CDN fallback',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'nodeno-drive-'));
  try {
    const fixture=await approvalFixture(dir),api=driveBoundary();
    const fetchImpl=async(value,options)=>{
      if(new URL(value).pathname==='/drive/v3/about') await writeFile(join(dir,Object.values(fixture.cleanup.images)[0].path),originalBytes);
      return api.fetchImpl(value,options);
    };
    await assert.rejects(migrate({catalog:sampleCatalog,workspaceRoot:dir,upload:true,folderId:'folder',token:'test-private-token',expectedEmail:'new-owner@example.test',manifestPath:join(dir,'manifest.json'),fetchImpl}),error=>error.code==='MEDIA_INTEGRITY');
    assert.equal(api.counts.creates,0);assert.equal(api.counts.generates,0);assert.equal(api.counts.downloads,0);
  } finally {await rm(dir,{recursive:true,force:true});}
});
