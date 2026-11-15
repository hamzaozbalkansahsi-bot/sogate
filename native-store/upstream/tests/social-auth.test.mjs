import test from 'node:test';
import {generateKeyPairSync} from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
const php=process.env.PHP_BINARY||'php',root=process.cwd();
const quote=value=>"'"+value.replaceAll('\\','/').replaceAll("'","\\'")+"'";
function run(body){
 const temp=mkdtempSync(path.join(os.tmpdir(),'nodeno-social-'));
 const pair=generateKeyPairSync('rsa',{modulusLength:2048}),privatePem=pair.privateKey.export({type:'pkcs8',format:'pem'}),publicJwk={...pair.publicKey.export({format:'jwk'}),kid:'fixture',use:'sig',alg:'RS256'};
 const applePair=generateKeyPairSync('ec',{namedCurve:'prime256v1'}),applePrivate=applePair.privateKey.export({type:'pkcs8',format:'pem'}),applePublic=applePair.publicKey.export({type:'spki',format:'pem'});
 const program=`<?php declare(strict_types=1);
 require ${quote(path.join(root,'hosting/account.php'))};
 require_once ${quote(path.join(root,'hosting/social-auth.php'))};
 $root=${quote(temp)}; $database=nodenoAccountDatabase($root);nodenoSocialSchema($database);
 function userFixture(PDO $db,string $id,string $email):array { $stmt=$db->prepare('INSERT INTO users(id,email,name,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?)');$stmt->execute([$id,$email,'Test User',password_hash('Test-password-2026',PASSWORD_DEFAULT),time(),time()]);$stmt=$db->prepare('SELECT * FROM users WHERE id=?');$stmt->execute([$id]);return $stmt->fetch(); }
 $fixtureAppleKey=${quote(applePrivate)};$fixtureApplePublic=${quote(applePublic)};
 $fixtureKey=${quote(privatePem)};$fixtureJwks=json_decode(${quote(JSON.stringify({keys:[publicJwk]}))},true);
 function tokenFixture(array $claims):array {global $fixtureKey,$fixtureJwks;return [Firebase\\JWT\\JWT::encode($claims,$fixtureKey,'RS256','fixture'),$fixtureJwks];}
 ${body}
 `;
 const filename=path.join(temp,'run.php');writeFileSync(filename,program);
 try{return JSON.parse(execFileSync(php,[filename],{cwd:root,encoding:'utf8',stdio:['ignore','pipe','pipe']}));}finally{assert.equal(path.dirname(path.resolve(temp)),path.resolve(os.tmpdir()));assert.ok(path.basename(temp).startsWith('nodeno-social-'));rmSync(temp,{recursive:true,force:true});}
}

test('unconfigured social providers stay unavailable without exposing any credential fields',()=>{
 const value=run(`echo json_encode(nodenoSocialPublicStatus($database,$root,null,'https://nodenohome.com'));`);
 assert.equal(value.providers.google.ready,false);assert.equal(value.providers.apple.ready,false);assert.equal(value.merge,null);
 assert.ok(!JSON.stringify(value).includes('secret'));assert.ok(!JSON.stringify(value).includes('privateKey'));
});

test('Google and Apple ID tokens require a valid pinned signature, nonce, issuer and audience',()=>{
 const value=run(`$base=['iss'=>'https://accounts.google.com','aud'=>'google-client','sub'=>'google-user','email'=>'test@example.test','email_verified'=>true,'name'=>'Test User','nonce'=>'nonce-value','iat'=>time(),'exp'=>time()+300];[$token,$jwks]=tokenFixture($base);$google=nodenoSocialVerify('google',$token,'google-client','nonce-value',$jwks);$base['iss']='https://appleid.apple.com';$base['aud']='apple-client';$base['sub']='apple-user';$base['email']='private@privaterelay.appleid.com';$base['email_verified']='true';[$token,$jwks]=tokenFixture($base);$apple=nodenoSocialVerify('apple',$token,'apple-client','nonce-value',$jwks);echo json_encode(['google'=>$google,'apple'=>$apple]);`);
 assert.equal(value.google.subject,'google-user');assert.equal(value.google.emailVerified,true);assert.equal(value.apple.email,'private@privaterelay.appleid.com');assert.equal(value.apple.emailVerified,true);
});

test('invalid identity claims and signature tampering cannot authenticate an account',()=>{
 const value=run(`$base=['iss'=>'https://accounts.google.com','aud'=>'client','sub'=>'subject','email'=>'test@example.test','email_verified'=>true,'nonce'=>'expected','iat'=>time(),'exp'=>time()+300];$rejected=[];foreach(['nonce','aud','iss','exp','email_verified'] as $field){$claims=$base;$claims[$field]=['nonce'=>'wrong','aud'=>'wrong','iss'=>'https://attacker.example','exp'=>time()-120,'email_verified'=>false][$field];[$token,$jwks]=tokenFixture($claims);try{nodenoSocialVerify('google',$token,'client','expected',$jwks);$rejected[$field]=false;}catch(NodenoAccountHttpError $e){$rejected[$field]=true;}}[$token,$jwks]=tokenFixture($base);$parts=explode('.',$token);$parts[2]=str_repeat('A',strlen($parts[2]));try{nodenoSocialVerify('google',implode('.',$parts),'client','expected',$jwks);$rejected['signature']=false;}catch(NodenoAccountHttpError $e){$rejected['signature']=true;}echo json_encode($rejected);`);
 assert.deepEqual(value,{nonce:true,aud:true,iss:true,exp:true,email_verified:true,signature:true});
});

test('a matching email never silently links an existing local account',()=>{
 const value=run(`$target=userFixture($database,'target','existing@example.test');$identity=['provider'=>'google','subject'=>'new-subject','email'=>'existing@example.test','emailVerified'=>true,'name'=>'Test User'];$code='';try{nodenoSocialResolveIdentity($database,$identity,null,'login');}catch(NodenoAccountHttpError $e){$code=$e->errorCode;}$before=(int)$database->query('SELECT COUNT(*) FROM provider_identities')->fetchColumn();$result=nodenoSocialResolveIdentity($database,$identity,$target,'link');echo json_encode(['error'=>$code,'before'=>$before,'after'=>(int)$database->query('SELECT COUNT(*) FROM provider_identities')->fetchColumn(),'userId'=>$result['user']['id']]);`);
 assert.equal(value.error,'social_existing_account');assert.equal(value.before,0);assert.equal(value.after,1);assert.equal(value.userId,'target');
});

test('a new verified social account has no usable generated password',()=>{
 const value=run(`$identity=['provider'=>'apple','subject'=>'new-apple','email'=>'private@privaterelay.appleid.com','emailVerified'=>true,'name'=>'Test User'];$result=nodenoSocialResolveIdentity($database,$identity,null,'login');$u=$result['user'];echo json_encode(['passwordConfigured'=>(bool)$u['password_configured'],'verified'=>(bool)$u['email_verified'],'email'=>$u['email'],'hash'=>$u['password_hash'],'users'=>(int)$database->query('SELECT COUNT(*) FROM users')->fetchColumn()]);`);
 assert.equal(value.passwordConfigured,false);assert.equal(value.verified,true);assert.equal(value.email,'private@privaterelay.appleid.com');assert.equal(value.users,1);assert.ok(value.hash.length>40);
});

test('confirmed account merge preserves carts, favourites, identities, addresses and orders',()=>{
 const value=run(`$target=userFixture($database,'target','target@example.test');$source=userFixture($database,'source','source@example.test');$insert=$database->prepare('INSERT INTO account_state VALUES (?,?,?,?)');$insert->execute(['target',json_encode([['id'=>'1','quantity'=>2]]),json_encode(['1']),1]);$insert->execute(['source',json_encode([['id'=>'1','quantity'=>3],['id'=>'2','quantity'=>1]]),json_encode(['2']),1]);$database->exec("INSERT INTO addresses VALUES ('addr','source','{}',1,1,1); INSERT INTO orders VALUES ('order','source','test','TRY',100,'[]',1);INSERT INTO provider_identities(provider,subject,user_id,email,created_at) VALUES ('google','sub','source','source@example.test',1)");$merged=nodenoSocialMerge($database,$target,$source,['products'=>[['id'=>'1'],['id'=>'2']]]);echo json_encode(['user'=>$merged['id'],'version'=>$merged['auth_version'],'state'=>$database->query("SELECT cart_json,favorites_json FROM account_state WHERE user_id='target'")->fetch(),'address'=>$database->query("SELECT user_id FROM addresses WHERE id='addr'")->fetchColumn(),'order'=>$database->query("SELECT user_id FROM orders WHERE id='order'")->fetchColumn(),'identity'=>$database->query("SELECT user_id FROM provider_identities WHERE subject='sub'")->fetchColumn(),'users'=>(int)$database->query('SELECT COUNT(*) FROM users')->fetchColumn()]);`);
 assert.equal(value.user,'target');assert.equal(value.version,2);assert.deepEqual(JSON.parse(value.state.cart_json),[{id:'1',quantity:5},{id:'2',quantity:1}]);assert.deepEqual(JSON.parse(value.state.favorites_json),['1','2']);assert.equal(value.address,'target');assert.equal(value.order,'target');assert.equal(value.identity,'target');assert.equal(value.users,1);
});

test('an over-limit merge rolls back instead of silently dropping customer data',()=>{
 const value=run(`$target=userFixture($database,'target','target@example.test');$source=userFixture($database,'source','source@example.test');$insert=$database->prepare('INSERT INTO account_state VALUES (?,?,?,?)');$insert->execute(['target',json_encode([['id'=>'1','quantity'=>70]]),'[]',1]);$insert->execute(['source',json_encode([['id'=>'1','quantity'=>40]]),'[]',1]);$code='';try{nodenoSocialMerge($database,$target,$source,['products'=>[['id'=>'1']]]);}catch(NodenoAccountHttpError $e){$code=$e->errorCode;}echo json_encode(['error'=>$code,'users'=>(int)$database->query('SELECT COUNT(*) FROM users')->fetchColumn(),'target'=>$database->query("SELECT cart_json FROM account_state WHERE user_id='target'")->fetchColumn(),'source'=>$database->query("SELECT cart_json FROM account_state WHERE user_id='source'")->fetchColumn()]);`);
 assert.equal(value.error,'social_merge_cart_limit');assert.equal(value.users,2);assert.deepEqual(JSON.parse(value.target),[{id:'1',quantity:70}]);assert.deepEqual(JSON.parse(value.source),[{id:'1',quantity:40}]);
});

test('authorization flow binds state to the browser and session, uses Google PKCE and consumes proof once',()=>{
 const value=run(`$flow=nodenoSocialCreateFlow($database,'google',['clientId'=>'client.apps.googleusercontent.com','callback'=>'https://nodenohome.com/api/account/oauth/google/callback'],['sessionId'=>'initial-session','browser'=>'browser-proof','intent'=>'login','locale'=>'tr','next'=>'checkout','user'=>null]);parse_str(parse_url($flow['url'],PHP_URL_QUERY),$query);$wrong=false;try{nodenoSocialClaimFlow($database,$flow['state'],'google','wrong-browser');}catch(NodenoAccountHttpError $e){$wrong=true;}$pending=nodenoSocialClaimFlow($database,$flow['state'],'google','browser-proof');$replay=false;try{nodenoSocialClaimFlow($database,$flow['state'],'google','browser-proof');}catch(NodenoAccountHttpError $e){$replay=true;}nodenoSocialSaveVerified($database,$flow['state'],$pending,['provider'=>'google','subject'=>'verified','email'=>'test@example.test','emailVerified'=>true,'name'=>'Test']);$sessionMismatch=false;try{nodenoSocialCompleteFlow($database,$flow['state'],'browser-proof','another-session');}catch(NodenoAccountHttpError $e){$sessionMismatch=true;}$complete=nodenoSocialCompleteFlow($database,$flow['state'],'browser-proof','initial-session');$second=false;try{nodenoSocialCompleteFlow($database,$flow['state'],'browser-proof','initial-session');}catch(NodenoAccountHttpError $e){$second=true;}echo json_encode(['query'=>$query,'wrong'=>$wrong,'replay'=>$replay,'sessionMismatch'=>$sessionMismatch,'complete'=>$complete,'second'=>$second,'challengeMatches'=>$query['code_challenge']===rtrim(strtr(base64_encode(hash('sha256',$pending['verifier'],true)),'+/','-_'),'=')]);`);
 assert.equal(value.query.code_challenge_method,'S256');assert.equal(value.query.scope,'openid email profile');assert.equal(value.query.redirect_uri,'https://nodenohome.com/api/account/oauth/google/callback');assert.equal(value.challengeMatches,true);assert.equal(value.wrong,true);assert.equal(value.replay,true);assert.equal(value.sessionMismatch,true);assert.equal(value.second,true);assert.equal(value.complete.identity.subject,'verified');assert.equal(value.complete.next,'checkout');assert.equal(value.complete.verifier,undefined);
});

test('Apple uses its POST callback and expired or untrusted return targets are rejected',()=>{
 const value=run(`$configuration=['clientId'=>'com.nodeno.web','callback'=>'https://nodenohome.com/api/account/oauth/apple/callback'];$context=['sessionId'=>'session','browser'=>'browser','intent'=>'login','locale'=>'ar','next'=>'https://attacker.example','user'=>null];$flow=nodenoSocialCreateFlow($database,'apple',$configuration,$context);parse_str(parse_url($flow['url'],PHP_URL_QUERY),$query);$database->exec('UPDATE oauth_flows SET expires_at=1');$expired=false;try{nodenoSocialClaimFlow($database,$flow['state'],'apple','browser');}catch(NodenoAccountHttpError $e){$expired=true;}$configuration['callback']='https://attacker.example/callback';$host=false;try{nodenoSocialCreateFlow($database,'apple',$configuration,$context);}catch(NodenoAccountHttpError $e){$host=true;}echo json_encode(['query'=>$query,'expired'=>$expired,'host'=>$host]);`);
 assert.equal(value.query.response_mode,'form_post');assert.equal(value.query.redirect_uri,'https://nodenohome.com/api/account/oauth/apple/callback');assert.equal(value.expired,true);assert.equal(value.host,true);
});

test('Apple requires a valid P-256 private key and signs a short-lived ES256 client assertion',()=>{
 const value=run(`file_put_contents($root.'/apple-signin.p8',$fixtureAppleKey);chmod($root.'/apple-signin.p8',0600);$configuration=['apple'=>['enabled'=>true,'clientId'=>'com.nodenohome.signin','teamId'=>'TEAM123456','keyId'=>'KEY1234567','redirectUris'=>['https://nodenohome.com/api/account/oauth/apple/callback']]];$provider=nodenoSocialProvider($configuration,$root,'apple','https://nodenohome.com');$secret=nodenoSocialAppleSecret($provider);$claims=(array)Firebase\\JWT\\JWT::decode($secret,new Firebase\\JWT\\Key($fixtureApplePublic,'ES256'));file_put_contents($root.'/apple-signin.p8','invalid key');$invalid=nodenoSocialProvider($configuration,$root,'apple','https://nodenohome.com');echo json_encode(['issuer'=>$claims['iss'],'subject'=>$claims['sub'],'audience'=>$claims['aud'],'lifetime'=>$claims['exp']-$claims['iat'],'invalidRejected'=>$invalid===null]);`);
 assert.deepEqual(value,{issuer:'TEAM123456',subject:'com.nodenohome.signin',audience:'https://appleid.apple.com',lifetime:300,invalidRejected:true});
});
