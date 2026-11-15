<?php
declare(strict_types=1);
// Installed only in /home/nodenoho/nodeno-social, outside public_html.
if(PHP_SAPI!=='cli')exit(1);
ini_set('display_errors','0');ini_set('log_errors','0');ini_set('zend.exception_ignore_args','1');
try {
 $runtime=require '/home/nodenoho/nodeno-runtime.php';$private=$runtime['privateRoot']??'';$storage=$runtime['storageRoot']??'';$vault=$runtime['mediaRoot']??'';
 foreach([$private,$storage,$vault] as $path)if(!is_string($path)||!str_starts_with($path,'/home/nodenoho/')||str_contains($path,'..')||str_starts_with($path,'/home/nodenoho/public_html'))throw new RuntimeException('Unsafe runner configuration');
 if(!str_starts_with($private,'/home/nodenoho/nodeno-releases/'))throw new RuntimeException('Invalid release root');
 if(!is_file($private.'/social-worker.php'))exit(0);
 require_once $private.'/social-worker.php';$activeRelease=json_decode(file_get_contents($private.'/release.json'),true)['releaseHash'];$last=is_file(__DIR__.'/heartbeat.json')?json_decode(file_get_contents(__DIR__.'/heartbeat.json'),true):[];
 if(($last['releaseHash']??null)!==$activeRelease){$db=nodenoControlDatabase($storage);nodenoControlSetSetting($db,'social:last-trend-check',0);}
 $result=nodenoStudioTick($storage,$private,$vault,'/home/nodenoho/public_html');
 $db=nodenoControlDatabase($storage);$heartbeat=nodenoControlSetting($db,'social:heartbeat',[]);$receipt=['checkedAt'=>time(),'releaseHash'=>json_decode(file_get_contents($private.'/release.json'),true)['releaseHash'],'result'=>$result,'heartbeat'=>$heartbeat,'paidEnabled'=>nodenoStudioSettings($db)['paidEnabled'],'paidReservations'=>(int)$db->query('SELECT COUNT(*) FROM social_budget')->fetchColumn(),'counts'=>$db->query('SELECT status,COUNT(*) AS count FROM social_posts GROUP BY status')->fetchAll()];
 $receipt['creativeVersion']=nodenoControlSetting($db,'social:creative-policy');$active=$db->query("SELECT product_id,platform,locale,format,payload_json,status FROM social_posts WHERE substr(id,1,5)='auto_' AND status!='cancelled' ORDER BY scheduled_at,id")->fetchAll();$segments=[];$samples=[];foreach($active as $post){$payload=json_decode($post['payload_json'],true);$segment=$payload['segment']??'legacy';$segments[$segment]=($segments[$segment]??0)+1;if(count($samples)<7)$samples[]=['productId'=>$post['product_id'],'platform'=>$post['platform'],'locale'=>$post['locale'],'format'=>$post['format'],'title'=>$payload['title']??'','theme'=>$payload['theme']??null,'status'=>$post['status']];}$receipt['activeAutomaticSegments']=$segments;$receipt['activeAutomaticSamples']=$samples;
 $receipt['trendSources']=nodenoControlSetting($db,'social:trend-sources',[]);$receipt['trendCount']=(int)$db->query('SELECT COUNT(*) FROM social_trends')->fetchColumn();
 file_put_contents(__DIR__.'/heartbeat.json',json_encode($receipt,JSON_THROW_ON_ERROR),LOCK_EX);chmod(__DIR__.'/heartbeat.json',0600);
}catch(Throwable $e){file_put_contents(__DIR__.'/heartbeat.json',json_encode(['checkedAt'=>time(),'status'=>'failed','reason'=>'runner_action_failed']),LOCK_EX);exit(1);}
