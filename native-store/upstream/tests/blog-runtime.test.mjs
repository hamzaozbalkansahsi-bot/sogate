import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {mkdtemp,mkdir,writeFile,readFile,rm,symlink} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';

const root=fileURLToPath(new URL('../',import.meta.url));
const php=process.env.PHP_BINARY||process.env.NODENO_PHP||path.join(root,'artifacts/runtime-php/php.exe');
const now=s=>Date.parse(s)/1000;
async function fixture(t,count=10){
 const base=await mkdtemp(path.join(os.tmpdir(),'nodeno-blog-'));t.after(()=>rm(base,{recursive:true,force:true}));
 const dirs={storage:path.join(base,'storage'),private:path.join(base,'private'),public:path.join(base,'public')};
 for(const p of Object.values(dirs))await mkdir(p);await mkdir(path.join(dirs.public,'assets/blog'),{recursive:true});
 const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><rect width="100" height="100"/></svg>';
 await writeFile(path.join(dirs.public,'assets/blog/test.svg'),svg);
 const articles=Array.from({length:count},(_,i)=>({id:`blog-${i+1}`,slug:`useful-guide-${i+1}`,category:i%2?'paint':'space',title:`Özgün rehber ${i+1}`,description:'Mekânı ölçmek ve doğru kararı vermek için uygulama rehberi.',keywords:['oda ölçümü','yerleşim'],intro:'Her ölçümü çizime kaydetmek geçiş alanlarını görmenize yardım eder.',sections:[{heading:'Ölçüleri kaydedin',paragraphs:['Duvarın uzunluğunu zeminde ve mobilyanın geleceği yükseklikte ayrı ölçün. Kapı açılımını çizime ekleyin.']}],checklist:['Kapı açılımını doğruladınız mı?'],tool:'space',related:[],sources:[],image:{url:'/assets/blog/test.svg',alt:'Ölçü planı',width:1200,height:800,kind:'original-diagram',sha256:createHash('sha256').update(svg).digest('hex')},locales:{en:{title:`Useful guide ${i+1}`,description:'Measure your room before choosing furniture.',intro:'Record the opening direction before placing furniture.',sections:[{heading:'Record the dimensions',paragraphs:['Measure the wall at floor level and furniture height.']}],checklist:['Check the door swing.'],keywords:['room measurement'],imageAlt:'Room measurement plan'}}}));
 const bank={schemaVersion:1,timezone:'Europe/Istanbul',dailySlots:['09:30','18:30'],articles};
 await writeFile(path.join(dirs.private,'blog-bank.json'),JSON.stringify(bank));
 function call(input={}){const c=spawnSync(php,['tests/fixtures/blog-runtime.php'],{cwd:root,input:JSON.stringify({...dirs,now:now('2026-11-12T05:00:00Z'),...input}),encoding:'utf8'});assert.equal(c.status,0,c.stderr);const result=JSON.parse(c.stdout);assert.equal(result.available,true,'Blog worker must exist and run');return result;}
 return {...dirs,bank,call,save:async()=>writeFile(path.join(dirs.private,'blog-bank.json'),JSON.stringify(bank))};
}
test('the launch pair publishes on the first actual server day, followed by two daily Istanbul slots',async t=>{
 const f=await fixture(t,6);f.bank.launchImmediately=true;await f.save();const first=now('2026-11-12T05:00:00Z');
 assert.equal(f.call({now:first}).result.published,2);assert.equal(f.call({now:first+300}).result.published,0);
 const state=f.call({operation:'read'}).result.status;assert.equal(state.queue[0].publishedAt,'2026-11-12T05:00:00Z');assert.equal(state.queue[2].scheduledAt,'2026-11-13T06:30:00Z');
 assert.equal(f.call({now:now('2026-11-13T06:29:59Z')}).result.published,0);assert.equal(f.call({now:now('2026-11-13T06:30:00Z')}).result.published,1);assert.equal(f.call({now:now('2026-11-13T15:30:00Z')}).result.published,1);
});
test('the server worker waits for deployment and refuses a stale release pointer',async t=>{
 const f=await fixture(t,4),home=path.dirname(f.storage),runtime=path.join(home,'nodeno-runtime.php'),lock=path.join(home,'nodeno-deploy-lock'),stamp=now('2026-11-12T16:00:00Z');
 const pointer=privatePath=>`<?php return ['privateRoot'=>${JSON.stringify(privatePath.replaceAll('\\','/'))}];`;
 await writeFile(runtime,pointer(f.private));await mkdir(lock);let result=f.call({now:stamp}).result;assert.equal(result.status,'deployment_wait');assert.equal(result.published,0);
 assert.equal(path.dirname(lock),home);await rm(lock,{recursive:true,force:true});await writeFile(runtime,pointer(f.public));result=f.call({now:stamp}).result;assert.equal(result.status,'deployment_wait');assert.equal(result.published,0);
 await writeFile(runtime,pointer(f.private));assert.equal(f.call({now:stamp}).result.published,2);
});

test('manual publication respects the persistent deployment fence',async t=>{
 const f=await fixture(t,2);f.call();
 const home=path.dirname(f.storage),runtime=path.join(home,'nodeno-runtime.php'),lock=path.join(home,'nodeno-deploy-lock');
 const pointer=privatePath=>`<?php return ['privateRoot'=>${JSON.stringify(privatePath.replaceAll('\\','/'))}];`;
 const request={operation:'admin',user:true,permissions:['marketing.read','marketing.write'],route:'blog/publish',method:'POST',body:{id:'blog-1'}};
 await writeFile(runtime,pointer(f.private));await mkdir(lock);
 assert.equal(f.call(request).code,'blog_deployment_in_progress');
 await rm(lock,{recursive:true});await writeFile(runtime,pointer(f.public));
 assert.equal(f.call(request).code,'blog_deployment_in_progress');
 assert.equal(f.call({operation:'read'}).result.published.total,0);
 await writeFile(runtime,pointer(f.private));assert.equal(f.call(request).result.published,true);
});

test('health rejects missing frozen historic article media even when the current bank no longer contains it',async t=>{
 const f=await fixture(t,2),home=path.dirname(f.storage),storage=path.join(home,'nodeno-data');await mkdir(storage);
 const historic=path.join(f.public,'assets/blog/historic.svg'),translated=path.join(f.public,'assets/blog/historic-en.svg');
 const svg=await readFile(path.join(f.public,'assets/blog/test.svg'));await writeFile(historic,svg);await writeFile(translated,svg);
 f.bank.articles[0].image.url='/assets/blog/historic.svg';f.bank.articles[0].locales.en.image={...f.bank.articles[0].image,url:'/assets/blog/historic-en.svg'};await f.save();
 assert.equal(f.call({storage,now:now('2026-11-12T06:30:00Z')}).result.published,1);
 f.bank.articles.shift();await f.save();await writeFile(path.join(f.public,'assets/blog/test.svg'),'Unpublished draft media is not public history');
 const vault=await mkdtemp(path.join(os.tmpdir(),'nodeno-blog-health-vault-'));t.after(()=>rm(vault,{recursive:true,force:true}));
 const raster=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=','base64'),sha=value=>createHash('sha256').update(value).digest('hex');
 const imageHash=sha(raster),url='https://witcdn.adoremobilya.com/test.png',source=sha(url);
 await writeFile(path.join(vault,imageHash+'.png'),raster);await mkdir(path.join(f.private,'cache'));
 await writeFile(path.join(home,'nodeno-runtime.php'),`<?php return ['mediaRoot'=>${JSON.stringify(vault.replaceAll('\\','/'))}];`);
 const approved=JSON.stringify({schema:1,policy:'approved-only-v1',references:{'sample:0':source},images:{[source]:{state:'approved_unmodified',sourceSha:imageHash,outputSha:imageHash,mime:'image/png',bytes:raster.length,width:1,height:1,file:null}},referenceCount:1,uniqueCount:1,counts:{approved_unmodified:1,approved_cleaned:0}});
 for(const [name,body] of Object.entries({'media.json':JSON.stringify({sample:[url]}),'media-approved.json':approved,'catalog.json':JSON.stringify({products:[],categories:[]}),'config.json':JSON.stringify({checkoutEnabled:false})}))await writeFile(path.join(f.private,name),body);
 for(const name of ['blog-worker.php','blog-store.php'])await writeFile(path.join(f.private,name),await readFile(path.join(root,'hosting',name)));
 const entry=await readFile(path.join(root,'hosting/index.php'));await writeFile(path.join(f.public,'index.php'),entry);
 const files={'public/index.php':sha(entry)},fingerprint=sha(`public/index.php\0${sha(entry)}\0`);
 await writeFile(path.join(f.private,'release.json'),JSON.stringify({runtime:'php',files,releaseHash:fingerprint,products:0,categories:0,mediaApproved:1,mediaVersion:sha(approved)}));
 const health=()=>f.call({operation:'http-health'}).result;
 assert.equal(health().status,200,'A complete release with historic blog media starts healthy');
 for(const image of [translated,historic]){
  await rm(image);const failed=health();assert.equal(failed.status,503,'Missing historic image must reject health');assert.deepEqual(failed.body,{error:'temporarily_unavailable'});
  await writeFile(image,svg);assert.equal(health().status,200,'Restoring the exact approved bytes repairs health');
 }
 assert.equal(health().body.blogPublished,1);assert.equal(health().body.blogMediaReady,true);
});

test('media health before the first publication does not create a queue database',async t=>{
 const f=await fixture(t);assert.deepEqual(f.call({operation:'media-health'}).result,{blogPublished:0,blogMediaReady:true});
 await assert.rejects(readFile(path.join(f.storage,'blog.sqlite')),{code:'ENOENT'});
});

test('Istanbul slots persist through restarts and publish only when due exactly once',async t=>{
 const f=await fixture(t);let r=f.call();assert.equal(r.result.published,0);
 r=f.call({operation:'read',slug:'useful-guide-1'});assert.equal(r.result.article,null);assert.equal(r.result.published.total,0);assert.equal(r.result.status.next[0].scheduledAt,'2026-11-12T06:30:00Z');assert.equal(r.result.status.next[1].scheduledAt,'2026-11-12T15:30:00Z');
 r=f.call({now:now('2026-11-12T06:30:00Z')});assert.equal(r.result.published,1);
 r=f.call({now:now('2026-11-12T06:30:00Z')});assert.equal(r.result.published,0);
 r=f.call({operation:'read',slug:'useful-guide-1',locale:'en'});assert.equal(r.result.published.total,1);assert.equal(r.result.article.title,'Useful guide 1');assert.equal(r.result.article.publishedAt,'2026-11-12T06:30:00Z');
 r=f.call({now:now('2026-11-12T15:30:00Z')});assert.equal(r.result.published,1);
 r=f.call({operation:'read'});assert.equal(r.result.published.total,2);assert.equal(r.result.status.counts.scheduled,8);assert.equal(r.result.status.next[0].scheduledAt,'2026-11-13T06:30:00Z');
});

test('pause/resume survives new worker processes and catchup remains bounded',async t=>{
 const f=await fixture(t,20);f.call();f.call({operation:'command',action:'pause'});
 let r=f.call({now:now('2026-11-20T20:00:00Z')});assert.equal(r.result.published,0);assert.equal(r.result.status,'paused');
 f.call({operation:'command',action:'resume'});r=f.call({now:now('2026-11-20T20:00:00Z')});assert.equal(r.result.published,4);
 r=f.call({operation:'read'});assert.equal(r.result.published.total,4);assert.ok(r.result.status.logs.some(x=>x.event==='pause'));assert.ok(r.result.status.logs.some(x=>x.event==='resume'));
});

test('tampered media retries with backoff then dead letters and can be repaired explicitly',async t=>{
 const f=await fixture(t);f.call();await writeFile(path.join(f.public,'assets/blog/test.svg'),'tampered');
 let stamp=now('2026-11-12T06:30:00Z');let r=f.call({now:stamp});assert.equal(r.result.failed,1);
 r=f.call({now:stamp+1});assert.equal(r.result.failed,0);
 let state=f.call({operation:'read'}).result.status;assert.equal(state.counts.retry,1);assert.equal(state.logs[0].error,'image_integrity_failed');
 for(let i=0;i<4;i++){stamp+=86400;r=f.call({now:stamp});}
 state=f.call({operation:'read'}).result.status;assert.ok(state.counts.dead>=1);assert.equal(f.call({operation:'read',slug:'useful-guide-1'}).result.article,null);
 const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><rect width="100" height="100"/></svg>';await writeFile(path.join(f.public,'assets/blog/test.svg'),svg);
 f.call({operation:'command',action:'retry',body:{id:'blog-1'},now:stamp});r=f.call({now:stamp});assert.ok(r.result.published>=1);
});

test('worker lock excludes a second process and published snapshots remain immutable across releases',async t=>{
 const f=await fixture(t);f.call();let r=f.call({operation:'lock',now:now('2026-11-12T06:30:00Z')});assert.equal(r.result.status,'busy');
 f.call({now:now('2026-11-12T06:30:00Z')});f.bank.articles[0].title='Tampered title';await f.save();f.call();r=f.call({operation:'read',slug:'useful-guide-1'});assert.equal(r.result.article.title,'Özgün rehber 1');assert.equal(r.result.published.total,1);
});

test('admin requires authentication and marketing write permission before changes',async t=>{
 const f=await fixture(t);f.call();
 let r=f.call({operation:'admin'});assert.equal(r.code,'authentication_required');
 r=f.call({operation:'admin',user:true,permissions:['marketing.read']});assert.equal(r.result.total,10);
 r=f.call({operation:'admin',user:true,permissions:['marketing.read'],route:'blog/pause',method:'POST'});assert.equal(r.code,'permission_denied');
 r=f.call({operation:'admin',user:true,permissions:['marketing.read','marketing.write'],route:'blog/pause',method:'POST'});assert.equal(r.result.paused,true);
});

test('unsafe paths and invalid article identities stop before publishing',async t=>{
 const f=await fixture(t);f.bank.articles[0].slug='../escape';await f.save();assert.equal(f.call().code,'bank_article_identity_invalid');
 f.bank.articles[0].slug='useful-guide-1';f.bank.articles[0].image.url='/assets/blog/../private.svg';await f.save();let r=f.call({now:now('2026-11-12T06:30:00Z')});assert.equal(r.result.published,0);assert.equal(r.result.failed,1);
});

test('manual publication validates the selected article, leaves other queued articles alone and is idempotent',async t=>{
 const f=await fixture(t);f.call();const request={operation:'admin',user:true,permissions:['marketing.read','marketing.write'],route:'blog/publish',method:'POST',body:{id:'blog-7'}};
 let r=f.call(request);assert.equal(r.result.published,true);r=f.call(request);assert.equal(r.result.alreadyPublished,true);
 const state=f.call({operation:'read',slug:'useful-guide-7'}).result;assert.equal(state.published.total,1);assert.equal(state.article.id,'blog-7');assert.equal(state.status.counts.scheduled,9);assert.equal(state.status.logs.filter(x=>x.event==='published_manual').length,1);
 await writeFile(path.join(f.public,'assets/blog/test.svg'),'bad');r=f.call({...request,body:{id:'blog-8'}});assert.equal(r.code,'image_integrity_failed');
});

test('new content appends after existing slots and public search never exposes missing translations',async t=>{
 const f=await fixture(t,6);f.call();f.call({now:now('2026-11-12T15:30:00Z')});
 let r=f.call({operation:'read',locale:'ar',slug:'useful-guide-1'});assert.equal(r.result.published.total,0);assert.equal(r.result.article,null);
 r=f.call({operation:'read',locale:'en',options:{q:'Useful guide 2',perPage:1}});assert.equal(r.result.published.total,1);assert.equal(r.result.published.items[0].id,'blog-2');
 const added=structuredClone(f.bank.articles[0]);added.id='blog-7';added.slug='useful-guide-7';added.title='Yeni plan';f.bank.articles.unshift(added);await f.save();f.call({now:now('2026-11-13T05:00:00Z')});
 r=f.call({operation:'read'});assert.equal(r.result.status.next[0].scheduledAt,'2026-11-13T06:30:00Z');assert.equal(r.result.status.next.find(x=>x.id==='blog-7').scheduledAt,'2026-11-15T06:30:00Z');assert.equal(r.result.published.total,2);
});

test('cron with an empty DOCUMENT_ROOT can run from the hosting home directory',async t=>{
 const f=await fixture(t);const r=f.call({workingDirectory:path.dirname(f.storage)});assert.equal(r.code,undefined);assert.equal(r.result.seeded,10);
});

test('all five-minute ticks across an Istanbul day publish only at the two configured slots',async t=>{
 const f=await fixture(t);f.call();const start=now('2026-11-11T21:00:00Z');const times=Array.from({length:288},(_,i)=>start+i*300);
 let r=f.call({operation:'series',times});assert.deepEqual(r.result.filter(x=>x.published).map(x=>[x.checkedAt,x.published]),[['2026-11-12T06:30:00Z',1],['2026-11-12T15:30:00Z',1]]);
 r=f.call({operation:'series',times});assert.equal(r.result.reduce((n,x)=>n+x.published,0),0);assert.equal(f.call({operation:'read'}).result.published.total,2);
});

test('separate PHP processes cannot publish a locked queue and concurrent ticks publish each article once',async t=>{
 const f=await fixture(t);f.call();
 const owner=spawn(php,['-r','$f=fopen($argv[1],"c");flock($f,LOCK_EX);echo "locked\\n";fflush(STDOUT);fgets(STDIN);flock($f,LOCK_UN);fclose($f);',path.join(f.storage,'blog-worker.lock')],{stdio:['pipe','pipe','pipe']});
 t.after(()=>owner.kill());await new Promise((resolve,reject)=>{owner.stdout.once('data',data=>String(data).includes('locked')?resolve():reject(new Error('Lock handshake failed')));owner.once('error',reject);});
 let r=f.call({now:now('2026-11-12T15:30:00Z')});assert.equal(r.result.status,'busy');assert.equal(f.call({operation:'read'}).result.published.total,0);
 const closed=new Promise(resolve=>owner.once('exit',resolve));owner.stdin.end('release\n');await closed;
 const jobs=Array.from({length:8},()=>new Promise((resolve,reject)=>{const child=spawn(php,['tests/fixtures/blog-runtime.php'],{cwd:root,stdio:['pipe','pipe','pipe']});let stdout='',stderr='';child.stdout.on('data',data=>stdout+=data);child.stderr.on('data',data=>stderr+=data);child.once('error',reject);child.once('exit',code=>{try{assert.equal(code,0,stderr);const value=JSON.parse(stdout);assert.equal(value.code,undefined);resolve(value.result);}catch(e){reject(e);}});child.stdin.end(JSON.stringify({storage:f.storage,private:f.private,public:f.public,now:now('2026-11-12T15:30:00Z')}));}));
 const results=await Promise.all(jobs);assert.equal(results.reduce((n,x)=>n+x.published,0),2);r=f.call({operation:'read'});assert.equal(r.result.published.total,2);assert.equal(r.result.status.logs.filter(x=>x.event==='published').length,2);
});

test('one failed article leaves another due article publishable and a corrected bank retains retry backoff',async t=>{
 const f=await fixture(t);f.bank.articles[0].image.sha256='a'.repeat(64);await f.save();f.call();let r=f.call({now:now('2026-11-12T15:30:00Z')});assert.equal(r.result.published,1);assert.equal(r.result.failed,1);
 let state=f.call({operation:'read'}).result;assert.equal(state.status.counts.retry,1);assert.equal(state.published.items[0].id,'blog-2');const retryAt=state.status.next.find(x=>x.id==='blog-1').nextAttemptAt;
 f.bank.articles[0].image.sha256=f.bank.articles[1].image.sha256;await f.save();r=f.call({now:now('2026-11-12T15:30:01Z')});assert.equal(r.result.published,0);state=f.call({operation:'read'}).result;assert.equal(state.status.next.find(x=>x.id==='blog-1').nextAttemptAt,retryAt);
 r=f.call({now:now(retryAt)});assert.equal(r.result.published,1);assert.equal(f.call({operation:'read'}).result.published.total,2);
});

test('a stale bank cannot manually publish after a newer scheduled revision has been seeded',async t=>{
 const f=await fixture(t);f.call();const old=structuredClone(f.bank);f.bank.articles[0].title='Yeni inceleme';await f.save();f.call();
 const r=f.call({operation:'stale-bank',bank:old,id:'blog-1'});assert.equal(r.code,'blog_content_integrity_failed');assert.equal(f.call({operation:'read'}).result.published.total,0);
});

test('storage junctions and images resolving outside the public tree are rejected',async t=>{
 const f=await fixture(t);const alias=path.join(path.dirname(f.storage),'linked-storage');await symlink(f.storage,alias,'junction');let r=f.call({storage:alias});assert.equal(r.code,'blog_storage_unsafe');
 const outside=path.join(path.dirname(f.storage),'outside-images');await mkdir(outside);await writeFile(path.join(outside,'test.svg'),await readFile(path.join(f.public,'assets/blog/test.svg')));await rm(path.join(f.public,'assets/blog'),{recursive:true});await symlink(outside,path.join(f.public,'assets/blog'),'junction');
 r=f.call({now:now('2026-11-12T06:30:00Z')});assert.equal(r.result.published,0);assert.equal(r.result.failed,1);
});

test('a rejected seed transaction cannot partially append content or change existing schedule slots',async t=>{
 const f=await fixture(t,6);f.call();const original=structuredClone(f.bank);const added=structuredClone(f.bank.articles[0]);added.id='blog-7';added.slug='useful-guide-7';f.bank.articles.unshift(added);f.bank.articles[2].slug='changed-existing-slug';await f.save();
 let r=f.call();assert.equal(r.code,'blog_article_slug_changed');r=f.call({operation:'read'});assert.equal(r.result.status.total,6);assert.equal(r.result.status.next[0].scheduledAt,'2026-11-12T06:30:00Z');
 f.bank.articles=original.articles;await f.save();r=f.call();assert.equal(r.result.seeded,0);assert.equal(f.call({operation:'read'}).result.status.total,6);
});

test('a private bank directory junction is rejected before content can be seeded',async t=>{
 const f=await fixture(t);const alias=path.join(path.dirname(f.private),'linked-private');await symlink(f.private,alias,'junction');const r=f.call({private:alias});assert.equal(r.code,'blog_bank_unavailable');
});

test('admin queue includes published rows beyond the next-page limit and reports finite automated runway',async t=>{
 const f=await fixture(t,120);f.call();f.call({now:now('2026-11-12T15:30:00Z')});let r=f.call({operation:'admin',user:true,permissions:['marketing.read']});assert.equal(r.code,undefined);const state=r.result;
 assert.equal(state.queue.length,120);assert.equal(state.next.length,100);assert.equal(state.queue.filter(x=>x.status==='published').length,2);assert.equal(state.queueTruncated,false);assert.equal(state.queue[0].category,'space');assert.equal(state.queue[0].tool,'space');assert.equal(state.queue[0].sourceCount,0);assert.deepEqual(state.queue[0].availableLocales,['tr','en']);assert.equal(state.queue[0].sections,undefined);
 assert.equal(state.daysRemaining,59);assert.equal(state.readyRemaining,118);assert.equal(state.lastScheduledAt,'2027-01-10T15:30:00Z');assert.equal(state.lowBankWarning,false);
 const small=await fixture(t,8);small.call();small.call({operation:'command',action:'hold',body:{id:'blog-1'}});small.call({operation:'command',action:'hold',body:{id:'blog-2'}});r=small.call({operation:'read'});assert.equal(r.result.status.readyRemaining,6);assert.equal(r.result.status.daysRemaining,3);assert.equal(r.result.status.lowBankWarning,true);
});

test('private article previews require marketing access and leave scheduled articles invisible publicly',async t=>{
 const f=await fixture(t);f.call();const preview={operation:'admin',route:'blog/articles/blog-3'};
 let r=f.call(preview);assert.equal(r.code,'authentication_required');r=f.call({...preview,user:true,permissions:['dashboard.read']});assert.equal(r.code,'permission_denied');
 r=f.call({...preview,user:true,permissions:['marketing.read']});assert.equal(r.code,undefined);assert.equal(r.result.article.id,'blog-3');assert.equal(r.result.article.sections[0].heading,'Ölçüleri kaydedin');assert.equal(r.result.publication.status,'scheduled');assert.equal(f.call({operation:'read',slug:'useful-guide-3'}).result.article,null);
 r=f.call({...preview,user:true,permissions:['marketing.read'],route:'blog/articles/missing'});assert.equal(r.code,'not_found');
});
