import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

test('Stripe claimable sandbox keys work only in test configuration and stay encrypted',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-sandbox-key-'));
 const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',`require 'hosting/control-auth.php';require 'hosting/payment-admin.php';$root=$argv[1];$key='rkcs_test_fixture0000000000000000';$hook='whsec_fixture0000000000000000';$matches=[];foreach([['test',$key],['live',$key],['live','rkcs_live_fixture0000000000000000'],['test','rkcs_test_short'],['live','rk_live_fixture0000000000000000']]as $case)$matches[]=nodenoPaymentCredentialsMatch(['mode'=>$case[0],'credentials'=>['secretKey'=>$case[1],'webhookSecret'=>$hook]]);$db=nodenoControlDatabase($root);$_SESSION=['elevatedAt'=>time()];$ctx=['db'=>$db,'root'=>$root,'user'=>['id'=>'owner'],'permissions'=>['*']];$seller=['name'=>'QA Seller','address'=>'QA Address','email'=>'qa@example.test','taxConfirmed'=>false,'authorityConfirmed'=>false,'termsVersion'=>'test','terms'=>array_fill_keys(['tr','en','ru','ar'],''),'returns'=>array_fill_keys(['tr','en','ru','ar'],'')];$accepted=false;try{$v=nodenoPaymentAdmin($ctx,'payments','PUT',['version'=>0,'enabled'=>false,'mode'=>'test','accountId'=>'acct_fixture','secretKey'=>$key,'webhookSecret'=>$hook,'seller'=>$seller]);$accepted=$v['keyConfigured']===true;}catch(NodenoControlHttpError $e){}$saved=nodenoControlSetting($db,'payment:stripe',[]);echo json_encode([$matches,$accepted,!str_contains(json_encode($saved),$key)]);`,root],{encoding:'utf8'});
 assert.equal(r.status,0,r.stderr||r.stdout);assert.deepEqual(JSON.parse(r.stdout),[[true,false,false,false,true],true,true]);
});
