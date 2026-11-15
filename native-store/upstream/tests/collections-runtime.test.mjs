import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
const root=process.cwd(),php=process.env.PHP_BINARY||'php';
const available=spawnSync(php,['-r','exit(extension_loaded("pdo_sqlite")?0:1);']).status===0;
const catalog={products:[{id:'1'},{id:'2'},{id:'3'}]};
let directory,server,origin;
const quote=value=>"'"+value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'";
before(async()=>{if(!available)return;directory=await mkdtemp(path.join(os.tmpdir(),'nodeno-collections-test-'));await mkdir(path.join(directory,'storage'));const router=path.join(directory,'router.php');
 await writeFile(router,`<?php $_SERVER['HTTPS']='on';function nodenoRespond(string $body,int $status=200,string $type='application/json; charset=utf-8',array $headers=[]):void{http_response_code($status);header('Content-Type: '.$type);foreach($headers as $key=>$value)header($key.': '.$value);echo $body;}require ${quote(path.join(root,'hosting/account.php'))};nodenoHandleAccountRequest(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH),$_SERVER['REQUEST_METHOD'],json_decode(${quote(JSON.stringify(catalog))},true),${quote(path.join(directory,'storage'))});`);
 const portServer=net.createServer();await new Promise(resolve=>portServer.listen(0,'127.0.0.1',resolve));const port=portServer.address().port;await new Promise(resolve=>portServer.close(resolve));origin=`http://127.0.0.1:${port}`;
 server=spawn(php,['-d','display_errors=0','-S',`127.0.0.1:${port}`,router],{cwd:root,stdio:['ignore','ignore','ignore']});for(let i=0;i<80;i++){try{await fetch(origin+'/api/account');return;}catch{await new Promise(resolve=>setTimeout(resolve,50));}}throw new Error('Collection test server unavailable');
});
after(async()=>{if(server){const stopped=new Promise(resolve=>server.once('exit',resolve));server.kill();await stopped;}if(directory){assert.equal(path.dirname(path.resolve(directory)),path.resolve(os.tmpdir()));assert.ok(path.basename(directory).startsWith('nodeno-collections-test-'));await rm(directory,{recursive:true,force:true});}});
function client(){let cookie='',token='';return{async request(route='',method='GET',body,csrf=true){const headers={Origin:origin.replace('http:','https:'),Connection:'close'};if(cookie)headers.Cookie=cookie;if(method!=='GET'){headers['Content-Type']='application/json';if(csrf)headers['X-CSRF-Token']=token;}const response=await fetch(origin+'/api/account'+route,{method,headers,body:method==='GET'?undefined:JSON.stringify(body??{})});const set=response.headers.get('set-cookie');if(set)cookie=/NODENOSESSID=[^;]+/.exec(set)?.[0]||cookie;const data=await response.json();if(data.csrfToken)token=data.csrfToken;return{status:response.status,data};}};}
async function register(account,email){await account.request();const terms=await account.request('/membership-terms?lang=tr');assert.equal(terms.status,200);const reply=await account.request('/register','POST',{name:'Collection Tester',email,password:'Nodeno-collection-test-123',acceptMembership:true,membershipVersion:terms.data.version,membershipHash:terms.data.hash,membershipLocale:terms.data.locale});assert.equal(reply.status,201,JSON.stringify(reply.data));return reply.data.user;}
test('collections have account ownership, CSRF protection, optimistic versions and bounded real product IDs',{skip:!available},async()=>{
 const alice=client(),bob=client(),anonymous=client();await register(alice,'collections-alice@example.invalid');await register(bob,'collections-bob@example.invalid');await anonymous.request();
 assert.equal((await anonymous.request('/collections')).status,401);
 assert.equal((await alice.request('/collections','PUT',{version:0,collections:[]},false)).status,403);
 assert.deepEqual((await alice.request('/collections')).data,{version:0,collections:[]});
 const entry={id:'a'.repeat(32),name:'Salon',items:['1','2']};
 const saved=await alice.request('/collections','PUT',{version:0,collections:[entry]});assert.equal(saved.status,200);assert.equal(saved.data.version,1);
 assert.deepEqual((await bob.request('/collections')).data,{version:0,collections:[]});
 assert.equal((await alice.request('/collections','PUT',{version:0,collections:[]})).status,409);
 assert.deepEqual((await alice.request('/collections')).data,saved.data);
 assert.equal((await alice.request('/collections','PUT',{version:1,collections:[{...entry,items:['not-real']}]})).status,422);
 assert.equal((await alice.request('/collections','PUT',{version:1,collections:[{...entry,name:' '}]})).status,422);
 assert.equal((await alice.request('/collections','PUT',{version:1,collections:Array.from({length:21},(_,i)=>({...entry,id:i.toString(16).padStart(32,'0')}))})).status,422);
 assert.deepEqual((await alice.request('/collections')).data,saved.data);
 const guest={...entry,name:'Guest original name',items:['2','3']};
 const merged=await alice.request('/collections/merge','POST',{collections:[guest]});assert.equal(merged.status,200);assert.deepEqual(merged.data.collections,[{...entry,items:['1','2','3']}]);
 const repeated=await alice.request('/collections/merge','POST',{collections:[guest]});assert.equal(repeated.status,200);assert.deepEqual(repeated.data.collections,merged.data.collections);
 assert.equal((await alice.request('/collections','PUT',{version:repeated.data.version,collections:[]})).status,200);assert.deepEqual((await alice.request('/collections')).data.collections,[]);
});
test('social account merging preserves collections and rolls back cart and identities when collection capacity is exceeded',{skip:!available},()=>{
 const program=`require ${quote(path.join(root,'hosting/account.php'))};$db=nodenoAccountDatabase(${quote(path.join(directory,'storage'))});$catalog=json_decode(${quote(JSON.stringify(catalog))},true);$users=[];foreach(['c','d'] as $letter){$id=str_repeat($letter,32);$db->prepare('INSERT INTO users(id,email,name,password_hash,created_at,updated_at) VALUES(?,?,?,?,?,?)')->execute([$id,$letter.'@collections.invalid','Fixture',password_hash('Fixture-only-password',PASSWORD_DEFAULT),time(),time()]);$read=$db->prepare('SELECT * FROM users WHERE id=?');$read->execute([$id]);$users[]=$read->fetch();$db->prepare('INSERT INTO account_state VALUES(?,?,?,?)')->execute([$id,json_encode([['id'=>'1','quantity'=>1]]),'[]',time()]);}$target=[];for($i=0;$i<20;$i++)$target[]=['id'=>str_pad(dechex($i),32,'0',STR_PAD_LEFT),'name'=>'List '.$i,'items'=>['1']];$source=[['id'=>str_repeat('f',32),'name'=>'Source','items'=>['2']]];nodenoCollectionsStore($db,$users[0]['id'],$target,1);nodenoCollectionsStore($db,$users[1]['id'],$source,1);$blocked=false;try{nodenoSocialMerge($db,$users[0],$users[1],$catalog);}catch(NodenoAccountHttpError $e){$blocked=$e->errorCode==='social_merge_collections_limit';}$read=$db->prepare('SELECT cart_json FROM account_state WHERE user_id=?');$read->execute([$users[0]['id']]);$before=json_decode($read->fetchColumn(),true);$sourceExists=$db->query("SELECT COUNT(*) FROM users WHERE id='".$users[1]['id']."'")->fetchColumn();nodenoCollectionsStore($db,$users[0]['id'],[$target[0]],2);$merged=nodenoSocialMerge($db,$users[0],$users[1],$catalog);$state=nodenoCollectionsRead($db,$merged['id'],$catalog);$read->execute([$merged['id']]);echo json_encode(['blocked'=>$blocked,'before'=>$before,'sourceExistedAfterFailure'=>(int)$sourceExists,'collections'=>$state['collections'],'cart'=>json_decode($read->fetchColumn(),true),'sourceRows'=>(int)$db->query("SELECT COUNT(*) FROM collection_state WHERE user_id='".$users[1]['id']."'")->fetchColumn()]);`;
 const run=spawnSync(php,['-r',program],{encoding:'utf8'});assert.equal(run.status,0,run.stderr);const result=JSON.parse(run.stdout);assert.equal(result.blocked,true);assert.equal(result.sourceExistedAfterFailure,1);assert.deepEqual(result.before,[{id:'1',quantity:1}]);assert.equal(result.collections.length,2);assert.deepEqual(result.cart,[{id:'1',quantity:2}]);assert.equal(result.sourceRows,0);
});
