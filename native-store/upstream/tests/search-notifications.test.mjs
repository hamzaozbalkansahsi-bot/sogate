import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
const root=process.cwd(),php=path.join(root,'artifacts/runtime-php/php.exe');
function run(code){const s=spawnSync(php,['-r',`require 'hosting/search-notifications.php';${code}`],{cwd:root,encoding:'utf8'});assert.equal(s.status,0,s.stderr||s.stdout);return JSON.parse(s.stdout);}
const db=`$db=new PDO('sqlite::memory:',null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);$db->exec('CREATE TABLE control_jobs(id TEXT PRIMARY KEY,type TEXT,status TEXT,request_json TEXT,result_json TEXT,attempts INTEGER DEFAULT 0,next_attempt_at INTEGER,created_at INTEGER,updated_at INTEGER,idempotency_key TEXT UNIQUE)');nodenoSearchSchema($db);$u='https://nodenohome.com/?lang=tr&product=42';$a=hash('sha256','a');$b=hash('sha256','b');`;
test('publication changes, rollback to earlier content, removal and unchanged ticks are distinct',()=>{
 const r=run(db+`$r=[];foreach([[$u=>$a],[$u=>$a],[$u=>$b],[$u=>$a],[]]as $s)$r[]=nodenoSearchScan($db,$s,[],100)['queued'];echo json_encode($r);`);assert.deepEqual(r,[1,0,1,1,1]);
});
test('previously accepted URLs initialize without duplicate delivery; newly published URLs queue',()=>{
 const r=run(db+`echo json_encode(nodenoSearchScan($db,[$u=>$a,'https://nodenohome.com/blog/real-post'=>$a],[$u],100));`);assert.equal(r.queued,1);assert.equal(r.tracked,2);
});
test('private, login, foreign host and credential-bearing URLs never reach the transport',()=>{
 const r=run(`echo json_encode(array_map('nodenoSearchUrl',['https://nodenohome.com/?lang=tr&product=42','https://nodenohome.com/blog/test?lang=ar','https://nodenohome.com/api/admin','https://nodenohome.com/?lang=tr&page=cart','https://evil.example/?lang=tr','https://user@nodenohome.com/?lang=tr','https://nodenohome.com:8443/?lang=tr','https://nodenohome.com/blog/test?lang=xx']));`);assert.deepEqual(r,[true,true,false,false,false,false,false,false]);
});
test('202 remains pending; 403 backs off; 429 honors the engine; only 200 is successful',()=>{
 const r=run(`echo json_encode([nodenoSearchRetry(202,1,null,100),nodenoSearchRetry(403,1,null,100),nodenoSearchRetry(429,1,'3600',100),nodenoSearchRetry(200,1,null,100),nodenoSearchRetry(422,1,null,100)]);`);assert.deepEqual(r.map(x=>x.status),['pending_verification','retry','retry','submitted','dead']);assert.equal(r[0].next,400);assert.equal(r[1].next,1000);assert.equal(r[2].next,3700);
});
test('delivery ledger survives a pending verification and succeeds only after the due retry',()=>{
 const r=run(db+`nodenoSearchScan($db,[$u=>$a],[],100);$calls=0;$send=static function($urls,$key,$endpoint)use(&$calls){$calls++;return ['httpStatus'=>$calls===1?202:200];};$x=nodenoSearchDrain($db,100,'abcdefgh','https://yandex.com/indexnow',$send);$mid=$db->query('SELECT status FROM control_jobs')->fetchColumn();nodenoSearchDrain($db,200,'abcdefgh','https://yandex.com/indexnow',$send);$y=nodenoSearchDrain($db,401,'abcdefgh','https://yandex.com/indexnow',$send);echo json_encode([$mid,$calls,$db->query('SELECT status FROM control_jobs')->fetchColumn(),$x,$y]);`);assert.equal(r[0],'pending_verification');assert.equal(r[1],2);assert.equal(r[2],'submitted');assert.equal(r[3].ownershipVerified,false);assert.equal(r[4].ownershipVerified,true);
});
test('a crashed delivery lease is retried and malformed queued URLs are quarantined',()=>{
 const r=run(db+`nodenoSearchScan($db,[$u=>$a],[],100);$db->exec("UPDATE control_jobs SET status='processing'");$calls=0;$send=static function()use(&$calls){$calls++;return ['httpStatus'=>200];};nodenoSearchDrain($db,500,'abcdefgh','https://yandex.com/indexnow',$send);nodenoSearchDrain($db,800,'abcdefgh','https://yandex.com/indexnow',$send);$db->prepare('UPDATE control_jobs SET status=?,request_json=?')->execute(['queued',json_encode(['https://evil.example/'])]);nodenoSearchDrain($db,900,'abcdefgh','https://yandex.com/indexnow',$send);echo json_encode([$calls,$db->query('SELECT status FROM control_jobs')->fetchColumn()]);`);assert.deepEqual(r,[1,'dead']);
});
