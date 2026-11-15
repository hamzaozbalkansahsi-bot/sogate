import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
async function scenario(code){
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-campaign-'));
 const setup=`require 'hosting/control-http.php';$root=$argv[1];$db=nodenoControlDatabase($root);$_SESSION=['elevatedAt'=>time()];$ctx=['db'=>$db,'root'=>$root,'user'=>['id'=>'operator'],'permissions'=>['*']];$catalog=['products'=>[['id'=>'2395','code'=>'Ndn-2395','name'=>['tr'=>'Gerçek ürün'],'currency'=>'TRY','salePriceMinor'=>10001,'images'=>['/media/2395/0']]],'categories'=>[],'meta'=>[]];$data=['title'=>'Kasım kampanyası','productIds'=>'2395','percent'=>25,'startsAt'=>time()-60,'endsAt'=>time()+3600,'enabled'=>true];`;
 const result=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',setup+code,root],{encoding:'utf8'});assert.equal(result.status,0,result.stderr||result.stdout);return JSON.parse(result.stdout);
}
test('one save-publish command publishes the entered campaign and its exact discounted price, including retries',async()=>{
 const r=await scenario(`$body=['version'=>0,'data'=>$data,'idempotencyKey'=>'campaign-save-publish-20261103'];$a=nodenoControlDispatch($ctx,'campaigns/new/save-publish','POST',$body,$catalog,[]);$b=nodenoControlDispatch($ctx,'campaigns/new/save-publish','POST',$body,$catalog,[]);$p=nodenoControlPublicState($db,$catalog,[])['catalog']['products'][0];echo json_encode([$a['data']['version'],$a['data']['publishedVersion'],$b['data']['version'],$p['salePriceMinor'],isset($p['previousPriceMinor']),(int)$db->query('SELECT COUNT(*) FROM control_record_versions')->fetchColumn()]);`);
 assert.deepEqual(r,[2,2,2,7501,false,2]);
});
test('save-publish uses current form edits and rejects stale versions without partial saves',async()=>{
 const r=await scenario(`nodenoControlResource($ctx,'campaigns','sale','PUT',['version'=>0,'data'=>$data],$catalog);$data['percent']=30;$a=nodenoControlDispatch($ctx,'campaigns/sale/save-publish','POST',['version'=>1,'data'=>$data],$catalog,[]);$data['percent']=80;$error='';try{nodenoControlDispatch($ctx,'campaigns/sale/save-publish','POST',['version'=>1,'data'=>$data],$catalog,[]);}catch(NodenoControlHttpError $e){$error=$e->errorCode;}$row=nodenoControlRead($db,'campaigns','sale');echo json_encode([$a['data']['publishedVersion'],$row['data']['percent'],$error,nodenoControlPublicState($db,$catalog,[])['catalog']['products'][0]['salePriceMinor']]);`);
 assert.deepEqual(r,[3,30,'version_conflict',7001]);
});
test('campaign publication requires actual products and recent authentication before saving anything',async()=>{
 const r=await scenario(`$errors=[];$_SESSION['elevatedAt']=time()-400;try{nodenoControlDispatch($ctx,'campaigns/unsafe/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);}catch(NodenoControlHttpError $e){$errors[]=$e->errorCode;}$_SESSION['elevatedAt']=time();$data['productIds']='';try{nodenoControlDispatch($ctx,'campaigns/empty/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);}catch(NodenoControlHttpError $e){$errors[]=$e->errorCode;}echo json_encode([$errors,(int)$db->query("SELECT COUNT(*) FROM control_records WHERE resource='campaigns'")->fetchColumn()]);`);
 assert.deepEqual(r,[['reauthentication_required','required_productIds'],0]);
});
test('a saved draft remains separate from its live campaign and activity reports the actual published dates',async()=>{
 const r=await scenario(`$a=nodenoControlDispatch($ctx,'campaigns/sale/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);$data['percent']=40;$data['startsAt']=time()+1800;$data['endsAt']=time()+7200;nodenoControlResource($ctx,'campaigns','sale','PUT',['version'=>2,'data'=>$data],$catalog);$row=nodenoControlResource($ctx,'campaigns','sale','GET',[],$catalog)['data'];echo json_encode([$row['data']['percent'],$row['publishedData']['percent'],$row['activity']['status'],$row['activity']['appliedProducts'],$row['activity']['products'][0]['priceMinor']]);`);
 assert.deepEqual(r,[40,25,'active',1,7501]);
});
test('dashboard shows real unpublished work and campaign state while respecting the current role',async()=>{
 const r=await scenario(`nodenoControlResource($ctx,'campaigns','sale','PUT',['version'=>0,'data'=>$data],$catalog);$a=nodenoControlDispatch($ctx,'dashboard','GET',[],$catalog,[]);$ctx['permissions']=nodenoControlPermissions('analyst');$b=nodenoControlDispatch($ctx,'dashboard','GET',[],$catalog,[]);echo json_encode([$a['publicationQueue'][0]['pending'],$a['publicationQueue'][0]['resource'],$a['campaigns'][0]['activity']['status'],$b['publicationQueue'],$b['campaigns']]);`);
 assert.deepEqual(r,[1,'campaigns','draft',[],[]]);
});
test('all catalogue products can be selected, duplicates normalize and delimiter-only lists are rejected',async()=>{
 const r=await scenario(`$catalog['products']=[];for($i=0;$i<667;$i++)$catalog['products'][]=['id'=>(string)(2000+$i),'salePriceMinor'=>10000];$data['productIds']=implode(',',array_column($catalog['products'],'id'));$all=nodenoControlValidate('campaigns',$data,$catalog);$data['productIds']='2000, 2000,2001';$unique=nodenoControlValidate('campaigns',$data,$catalog);$data['productIds']=' , , ';$error='';try{nodenoControlValidate('campaigns',$data,$catalog);}catch(NodenoControlHttpError $e){$error=$e->errorCode;}echo json_encode([count(explode(',',$all['productIds'])),$unique['productIds'],$error]);`);
 assert.deepEqual(r,[667,'2000,2001','required_productIds']);
});
test('campaign activity distinguishes a stronger overlapping offer and counts equal winning rates',async()=>{
 const r=await scenario(`nodenoControlDispatch($ctx,'campaigns/low/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);$data['percent']=40;nodenoControlDispatch($ctx,'campaigns/high/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);nodenoControlDispatch($ctx,'campaigns/tie/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);$rows=nodenoControlResource($ctx,'campaigns','','GET',[],$catalog)['data'];$out=[];foreach($rows as $r)$out[$r['id']]=[$r['activity']['eligibleProducts'],$r['activity']['appliedProducts'],$r['activity']['overriddenProducts']];echo json_encode($out);`);
 assert.deepEqual(r.low,[1,0,1]);assert.deepEqual(r.high,[1,1,0]);assert.deepEqual(r.tie,[1,1,0]);
});
test('publication cannot turn a positive catalogue price into zero through rounding',async()=>{
 const r=await scenario(`$catalog['products'][0]['salePriceMinor']=1;$data['percent']=90;$error='';try{nodenoControlDispatch($ctx,'campaigns/tiny/save-publish','POST',['version'=>0,'data'=>$data],$catalog,[]);}catch(NodenoControlHttpError $e){$error=$e->errorCode;}echo json_encode([$error,(int)$db->query("SELECT COUNT(*) FROM control_records")->fetchColumn()]);`);
 assert.deepEqual(r,['campaign_zero_price',0]);
});
