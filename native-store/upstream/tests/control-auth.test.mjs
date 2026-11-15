import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {mkdtemp,mkdir,writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import {randomBytes,createHash,createHmac} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const ROOT=fileURLToPath(new URL('../',import.meta.url)),PHP=process.env.PHP_BINARY||path.join(ROOT,'artifacts/runtime-php/php.exe');
const quote=value=>"'"+value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'";
function php(program,args=[]){const r=spawnSync(PHP,['-r',program,...args],{encoding:'utf8'});assert.equal(r.status,0,r.stderr||r.stdout);return r.stdout;}
function totp(secret,time=Date.now()/1000){const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';let bits='';for(const c of secret)bits+=alphabet.indexOf(c).toString(2).padStart(5,'0');const key=Buffer.from(bits.match(/.{8}/g).map(x=>parseInt(x,2)));const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(time/30)));const hash=createHmac('sha1',key).update(counter).digest(),offset=hash[19]&15;return String((hash.readUInt32BE(offset)&0x7fffffff)%1000000).padStart(6,'0');}

test('control TOTP follows RFC vectors, rejects replay and protects stored secrets with authenticated encryption',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-control-crypto-'));
 const result=JSON.parse(php(`require ${quote(path.join(ROOT,'hosting/control-auth.php'))};$root=$argv[1];$s='GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ';$c=nodenoControlEncrypt($root,$s,'owner');$failed=false;try{nodenoControlDecrypt($root,$c,'other');}catch(Throwable $e){$failed=true;}echo json_encode([nodenoControlTotp($s,59,8),nodenoControlTotp($s,59),nodenoControlTotpCounter($s,'287082',59,-1),nodenoControlTotpCounter($s,'287082',59,1),$c,nodenoControlDecrypt($root,$c,'owner'),$failed]);`,[root]));
 assert.deepEqual(result.slice(0,4),['94287082','287082',1,null]);assert.ok(!result[4].includes('GEZDGNBV'));assert.equal(result[5],'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ');assert.equal(result[6],true);
});

test('control HTTP separates customers, bootstraps one MFA owner and enforces live role/session/CSRF state',async t=>{
 const temp=await mkdtemp(path.join(os.tmpdir(),'nodeno-control-http-')),storage=path.join(temp,'persistent'),pub=path.join(temp,'public');await mkdir(storage);await mkdir(pub);
 const token=randomBytes(32).toString('hex'),email='owner@example.test',password='Owner-correct-password-2026';await writeFile(path.join(storage,'admin-bootstrap.json'),JSON.stringify({schema:1,email,tokenHash:createHash('sha256').update(token).digest('hex'),expiresAt:Math.floor(Date.now()/1000)+1800}));
 const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));const origin='http://127.0.0.1:'+port;
 let server,exit,output='';
 async function start(){server=spawn(PHP,['-d','display_errors=0','-S','127.0.0.1:'+port,'-t',pub,path.join(ROOT,'tests/fixtures/control-runtime.php')],{env:{...process.env,NODENO_CONTROL_TEST:'isolated-only',NODENO_CONTROL_TEST_ROOT:storage}});exit=new Promise(r=>server.once('exit',r));server.stderr.on('data',v=>output+=v);for(let i=0;i<100;i++){try{const r=await fetch(origin+'/api/admin/session');if(r.status===200)return;}catch{}await new Promise(r=>setTimeout(r,30));}assert.fail(output);}
 async function stop(){if(server){server.kill();await exit;server=null;}}
 const client=()=>({cookie:'',csrf:''});
 async function request(jar,route,method='GET',body={},headers={}){const write=!['GET','HEAD'].includes(method);const r=await fetch(origin+route,{method,headers:{...(jar.cookie?{Cookie:jar.cookie}:{}),...(write?{Origin:origin,'Content-Type':'application/json','X-CSRF-Token':jar.csrf}:{}),...headers},...(write?{body:JSON.stringify(body)}:{})});const cookie=r.headers.get('set-cookie');if(cookie)jar.cookie=cookie.split(';')[0];const text=await r.text();let data;try{data=JSON.parse(text);}catch{assert.fail('Non-JSON control response: '+r.status+' '+text.slice(0,250)+' '+output.slice(-500));}if(data.csrfToken)jar.csrf=data.csrfToken;return{status:r.status,data,headers:r.headers};}
 try{
  await start();const owner=client(),second=client(),customer=client();
  const session=await request(owner,'/api/admin/session');assert.equal(session.data.user,null);assert.equal(session.data.bootstrapAvailable,true);assert.ok(!JSON.stringify(session.data).includes(email));assert.match(session.headers.get('set-cookie'),/Secure/i);assert.match(session.headers.get('set-cookie'),/HttpOnly/i);assert.match(session.headers.get('set-cookie'),/SameSite=Strict/i);
  assert.equal((await request(owner,'/api/admin/orders')).status,401);
  await request(customer,'/api/account');const membership=await request(customer,'/api/account/membership-terms?lang=tr');assert.equal(membership.status,200);assert.equal((await request(customer,'/api/account/register','POST',{name:'Customer',email,password:'Customer-correct-password-2026',acceptMembership:true,membershipVersion:membership.data.version,membershipHash:membership.data.hash,membershipLocale:membership.data.locale})).status,201);assert.equal((await request(customer,'/api/admin/orders')).status,401);
  const setup={email,password,token};assert.equal((await request(owner,'/api/admin/bootstrap/start','POST',setup,{Origin:'https://attacker.invalid'})).status,403);assert.equal((await request(owner,'/api/admin/bootstrap/start','POST',setup,{'X-CSRF-Token':''})).status,403);
  assert.equal((await request(owner,'/api/admin/bootstrap/start','POST',{...setup,token:'0'.repeat(64)})).status,403);
  const first=await request(owner,'/api/admin/bootstrap/start','POST',setup);assert.equal(first.status,200);assert.match(first.data.totpSecret,/^[A-Z2-7]{32}$/);const secret=first.data.totpSecret;
  await request(second,'/api/admin/session');const competing=await request(second,'/api/admin/bootstrap/start','POST',setup);assert.equal(competing.status,200);
  const setupCode=totp(secret);const completed=await request(owner,'/api/admin/bootstrap/complete','POST',{code:setupCode});assert.equal(completed.status,201);assert.equal(completed.data.user.role,'owner');assert.equal(completed.data.recoveryCodes.length,10);
  assert.equal((await request(second,'/api/admin/bootstrap/complete','POST',{code:totp(competing.data.totpSecret)})).status,409);
  const privateCommand={version:0,priceRevision:0,idempotencyKey:'fresh-session-demotion-replay-1234',data:{title:'Private order',email:'buyer@example.test',country:'TR',address:'Private address',status:'draft',items:[{productId:'p1',quantity:1}]}};assert.equal((await request(owner,'/api/admin/orders','PUT',privateCommand)).status,200);
  const ownerId=completed.data.user.id;const team=await request(owner,'/api/admin/team');assert.equal(team.status,200);assert.equal(team.data.data.length,1);assert.ok(!JSON.stringify(team.data).includes('totpSecret'));assert.ok(!JSON.stringify(team.data).includes('password_hash'));
  const oldCookie=owner.cookie;assert.equal((await request(owner,'/api/admin/logout','POST')).status,200);const stale={cookie:oldCookie,csrf:owner.csrf};assert.equal((await request(stale,'/api/admin/team')).status,401);
  const login=await request(owner,'/api/admin/login','POST',{email,password});assert.equal(login.status,200);assert.equal(login.data.authStage,'mfa');assert.equal((await request(owner,'/api/admin/team')).status,401);
  // Reuse the consumed value: generating it again can cross a 30-second
  // boundary and accidentally test a fresh, legitimately accepted code.
  assert.equal((await request(owner,'/api/admin/login/verify','POST',{code:setupCode})).status,401,'Consumed setup OTP must not authenticate again');
  const recovered=await request(owner,'/api/admin/login/verify','POST',{recoveryCode:completed.data.recoveryCodes[0]});assert.equal(recovered.status,200);assert.notEqual(owner.cookie,oldCookie);
  await stop();await start();assert.equal((await request(owner,'/api/admin/session')).data.user.id,ownerId);
  php(`require ${quote(path.join(ROOT,'hosting/control-store.php'))};$db=nodenoControlDatabase($argv[1]);$db->prepare('UPDATE control_users SET role=?,auth_version=auth_version+1 WHERE id=?')->execute(['analyst',$argv[2]]);`,[storage,ownerId]);assert.equal((await request(owner,'/api/admin/team')).status,401,'Role revocation invalidates existing sessions');
  assert.equal((await request(owner,'/api/admin/login','POST',{email,password})).status,200);assert.equal((await request(owner,'/api/admin/login/verify','POST',{recoveryCode:completed.data.recoveryCodes[1]})).status,200);assert.equal((await request(owner,'/api/admin/team')).status,403);
  assert.equal((await request(owner,'/api/admin/orders','PUT',privateCommand)).status,403,'Freshly authenticated analyst cannot replay a former operation response');
  const dbBytes=await readFile(path.join(storage,'accounts.sqlite'));assert.ok(!dbBytes.includes(Buffer.from(secret)));assert.ok(!dbBytes.includes(Buffer.from(password)));
 }finally{await stop();}
});
