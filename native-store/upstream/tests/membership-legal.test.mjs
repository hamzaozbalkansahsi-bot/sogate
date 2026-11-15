import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {mkdtemp,mkdir} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';

const root=process.cwd(),php=path.resolve('artifacts/runtime-php/php.exe');
function inspect(storage,code){const result=spawnSync(php,['-r',`require 'hosting/account.php';$db=nodenoAccountDatabase($argv[1]);${code}`,storage],{encoding:'utf8'});assert.equal(result.status,0,result.stderr||result.stdout);return JSON.parse(result.stdout);}

test('membership acceptance is current, explicit and recorded atomically with the exact private document snapshot',async()=>{
 const directory=await mkdtemp(path.join(os.tmpdir(),'nodeno-membership-')),storage=path.join(directory,'private'),pub=path.join(directory,'public');await mkdir(storage);await mkdir(pub);
 const listener=net.createServer();await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
 const origin='http://127.0.0.1:'+port,server=spawn(php,['-d','display_errors=0','-S','127.0.0.1:'+port,'-t',pub,path.resolve('tests/fixtures/control-runtime.php')],{cwd:root,env:{...process.env,NODENO_CONTROL_TEST:'isolated-only',NODENO_CONTROL_TEST_ROOT:storage},stdio:['ignore','ignore','ignore']}),stopped=new Promise(resolve=>server.once('exit',resolve));
 let cookie='',csrf='';async function request(route,body){const method=body?'POST':'GET',response=await fetch(origin+'/api/account'+route,{method,headers:{...(cookie?{Cookie:cookie}:{}),...(body?{Origin:origin,'Content-Type':'application/json','X-CSRF-Token':csrf}:{}),Connection:'close'},...(body?{body:JSON.stringify(body)}:{})});const set=response.headers.get('set-cookie');if(set)cookie=set.split(';')[0];const value=await response.json();if(value.csrfToken)csrf=value.csrfToken;return{status:response.status,body:value};}
 try{
  for(let i=0;i<70;i++){try{await request('');break;}catch{await new Promise(resolve=>setTimeout(resolve,30));}}
  const contract=await request('/membership-terms?lang=tr');assert.equal(contract.status,200);assert.equal(contract.body.version,'2026-11-10.3');assert.equal(contract.body.locale,'tr');assert.match(contract.body.hash,/^[a-f0-9]{64}$/);assert.equal(contract.body.url,'/legal/membership?lang=tr');
  const registration={name:'Member Example',email:'member@example.test',password:'Membership-password-2026'};
  for(const fields of [{},{acceptMembership:false},{acceptMembership:true,membershipVersion:'old',membershipHash:'0'.repeat(64),membershipLocale:'tr'}]){
   const rejected=await request('/register',{...registration,...fields});assert.ok([409,422].includes(rejected.status));assert.equal(inspect(storage,"echo json_encode((int)$db->query('SELECT COUNT(*) FROM users')->fetchColumn());"),0);
  }
  const accepted={acceptMembership:true,membershipVersion:contract.body.version,membershipHash:contract.body.hash,membershipLocale:'tr'},reply=await request('/register',{...registration,...accepted});assert.equal(reply.status,201);const userId=reply.body.user.id;
  const saved=inspect(storage,"$row=$db->query('SELECT * FROM membership_acceptances')->fetch();echo json_encode($row);");assert.equal(saved.user_id,userId);assert.equal(saved.document_hash,contract.body.hash);assert.equal(saved.version,'2026-11-10.3');assert.equal(saved.locale,'tr');assert.ok(saved.accepted_at>0);assert.ok(saved.document_json.includes('PTYS'));assert.ok(!saved.document_json.includes('member@example.test'));assert.ok(!JSON.stringify(saved).includes(registration.password));
  assert.equal((await request('/membership-terms?lang=xx')).status,422);
  const en=await request('/membership-terms?lang=en');assert.notEqual(en.body.hash,contract.body.hash);
  inspect(storage,"$db->exec(\"CREATE TRIGGER reject_membership BEFORE INSERT ON membership_acceptances BEGIN SELECT RAISE(ABORT,'test-only insertion failure');END\");echo 'true';");
  const failed=await request('/register',{...registration,email:'atomic@example.test',...accepted});assert.equal(failed.status,503);assert.equal(inspect(storage,"echo json_encode((int)$db->query('SELECT COUNT(*) FROM users')->fetchColumn());"),1);
  assert.deepEqual(inspect(storage,"echo json_encode($db->query('SELECT document_hash,document_json FROM membership_acceptances')->fetch());"),{document_hash:saved.document_hash,document_json:saved.document_json});
 }finally{server.kill();await stopped;}
});
