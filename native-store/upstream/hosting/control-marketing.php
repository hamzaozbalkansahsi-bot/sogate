<?php
declare(strict_types=1);
require_once __DIR__.'/control-kolaybi.php';

function nodenoControlRequireIntegrationVersion(?array $current,$expected):void {if(!is_int($expected)||$expected!==($current['version']??0))throw new NodenoControlHttpError(409,'integration_version_conflict');}
function nodenoControlIntegrationVerification(array $ctx,string $provider,array $verified,bool $success,array $companies):array {
 $db=$ctx['db'];$name='integration:'.$provider;
 return nodenoControlTransaction($db,static function()use($ctx,$db,$name,$provider,$verified,$success,$companies):array{
  $current=nodenoControlSetting($db,$name);
  if(!$current||($current['version']??0)!==($verified['version']??-1)||!hash_equals((string)($current['connectionId']??''),(string)($verified['connectionId']??'missing')))throw new NodenoControlHttpError(409,'integration_version_conflict');
  $current['status']=$success?'connected':'verification_failed';$current['checkedAt']=time();$current['version']++;$current['companies']=$success?$companies:[];
  nodenoControlSetSetting($db,$name,$current);
  nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'verify','integrations',$provider,['success'=>$success,'version'=>$current['version']]);
  return nodenoControlIntegration($ctx,$provider,'GET',[]);
 });
}
function nodenoControlIntegration(array $ctx,string $provider,string $method,array $body):array {
 nodenoControlRequire($ctx,'integrations.read',$method!=='GET');
 if(!in_array($provider,['kolaybi','email','sms','googleAds','metaAds'],true))throw new NodenoControlHttpError(404,'provider_unknown');
 $db=$ctx['db'];$root=$ctx['root'];$name='integration:'.$provider;$stored=nodenoControlSetting($db,$name);
 if($method==='GET')return ['provider'=>$provider,'version'=>$stored['version']??0,'connectionId'=>$stored['connectionId']??null,'status'=>$stored['status']??'not_configured','environment'=>$stored['environment']??null,'checkedAt'=>$stored['checkedAt']??null,'companies'=>$stored['companies']??[],'configuredFields'=>$stored['fields']??[]];
 if($method==='PUT')return nodenoControlTransaction($db,static function()use($ctx,$db,$root,$name,$provider,$body):array{
  $current=nodenoControlSetting($db,$name);
  nodenoControlRequireIntegrationVersion($current,$body['version']??null);
  $input=$body;unset($input['version']);$allowed=$provider==='kolaybi'?['environment','apiKey','channel']:['providerName','apiKey','sender'];
  foreach($input as $key=>$value)if(!in_array($key,$allowed,true)||!is_string($value)||strlen($value)>8000||preg_match('/[\r\n\x00]/',$value))throw new NodenoControlHttpError(422,'integration_field_invalid');
  $old=$current?json_decode(nodenoControlDecrypt($root,$current['encrypted'],$name),true):[];$new=$old;
  foreach($input as $key=>$value)if($value!=='')$new[$key]=$value;
  if($provider==='kolaybi'){
   $new['environment']=$new['environment']??'sandbox';nodenoControlKolaybiBase($new['environment']);
   if(($new['environment']??'')!==($old['environment']??'')&&(empty($input['apiKey'])||empty($input['channel'])))throw new NodenoControlHttpError(422,'environment_credentials_required');
   if(empty($new['apiKey'])||empty($new['channel']))throw new NodenoControlHttpError(422,'kolaybi_credentials_required');
  }
  ksort($new);ksort($old);$unchanged=$new===$old;
  $connectionId=$unchanged&&isset($current['connectionId'])?$current['connectionId']:bin2hex(random_bytes(16));
  $saved=['version'=>($current['version']??0)+1,'connectionId'=>$connectionId,'encrypted'=>nodenoControlEncrypt($root,json_encode($new,JSON_THROW_ON_ERROR),$name),'fields'=>array_keys(array_filter($new,static fn($v)=>$v!=='')),'environment'=>$new['environment']??null,'status'=>'configured_unverified'];
  nodenoControlSetSetting($db,$name,$saved);nodenoControlAudit($db,$root,$ctx['user']['id'],'configure','integrations',$provider,['version'=>$saved['version']]);
  return nodenoControlIntegration($ctx,$provider,'GET',[]);
 });
 if($method==='VERIFY'&&$provider==='kolaybi'){
  if(!$stored)throw new NodenoControlHttpError(422,'integration_not_configured');
  nodenoControlRequireIntegrationVersion($stored,$body['version']??null);
  $settings=json_decode(nodenoControlDecrypt($root,$stored['encrypted'],$name),true);
  try{
   $token=nodenoControlKolaybiToken($settings);$response=nodenoControlKolaybiRequest($settings,'GET','/kolaybi/v1/companies',[],$token);$companies=$response['data']??null;
   if(!is_array($companies))throw new NodenoControlHttpError(502,'provider_response_invalid');
   $safe=[];foreach($companies as $company)if(is_array($company)&&is_scalar($company['id']??null))$safe[]=['id'=>$company['id'],'name'=>implode('',array_slice(preg_split('//u',(string)($company['name']??''),-1,PREG_SPLIT_NO_EMPTY),0,200))];
  }catch(Throwable $error){nodenoControlIntegrationVerification($ctx,$provider,$stored,false,[]);throw $error;}
  return nodenoControlIntegrationVerification($ctx,$provider,$stored,true,$safe);
 }
 throw new NodenoControlHttpError(405,'method_not_allowed');
}
