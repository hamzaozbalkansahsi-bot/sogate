<?php
declare(strict_types=1);
// Uploaded only outside public_html. This is a CLI maintenance job, never an HTTP route.
function nodenoPrivateMaintenance(PDO $db,string $root,array $job,?callable $provider=null):array {
 if(($job['schema']??null)!==1||!is_string($job['nonce']??null)||!preg_match('/^[a-f0-9]{64}$/D',$job['nonce'])||!is_int($job['expiresAt']??null)||$job['expiresAt']<time()||$job['expiresAt']>time()+1800)throw new InvalidArgumentException('maintenance_job_invalid');
 $common=['schema','nonce','action','expiresAt'];
 if(in_array($job['action']??'',['install-sale-documents','activate-payments','update-sale-documents'],true)){
  $activating=$job['action']==='activate-payments';$updating=$job['action']==='update-sale-documents';
  if($activating){
   $decision=$job['billingDecision']??null;$expected=['invoiceCountry'=>'US','dispatchCountry'=>'TR','furnitureVatRate'=>10,'doorsAndFrontsVatRate'=>20,'approvalSource'=>'explicit_owner_instruction'];
   if(!is_array($decision)||count($decision)!==count($expected))throw new InvalidArgumentException('maintenance_billing_decision_required');
   foreach($expected as $field=>$value)if(($decision[$field]??null)!==$value)throw new InvalidArgumentException('maintenance_billing_decision_required');
  }
  if(array_diff(array_keys($job),[...$common,'expectedVersion','documents',...($activating?['billingDecision']:[])])||!is_int($job['expectedVersion']??null)||!is_array($job['documents']??null))throw new InvalidArgumentException('maintenance_documents_invalid');
  $documents=$job['documents'];$languages=['tr','en','ru','ar'];
  $versionPattern=($activating||$updating)?'/^\d{4}-\d{2}-\d{2}\.[1-9][0-9]*$/D':'/^\d{4}-\d{2}-\d{2}\.[1-9][0-9]*-draft$/D';
  if(array_diff(array_keys($documents),['termsVersion','terms','returns'])||!is_string($documents['termsVersion']??null)||!preg_match($versionPattern,$documents['termsVersion']))throw new InvalidArgumentException('maintenance_documents_invalid');
  $hashInput=[$documents['termsVersion']];
  foreach(['terms','returns']as $kind){
   if(!is_array($documents[$kind]??null)||array_diff(array_keys($documents[$kind]),$languages))throw new InvalidArgumentException('maintenance_documents_invalid');
   foreach($languages as $lang){$text=$documents[$kind][$lang]??null;if(!is_string($text)||strlen(trim($text))<20||strlen($text)>12000||!preg_match('//u',$text)||preg_match('/[<>\x00-\x08\x0b-\x1f]/u',$text))throw new InvalidArgumentException('maintenance_documents_invalid');$hashInput[]=$text;}
  }
  $documentsHash=hash('sha256',implode("\0",$hashInput));
  $activeCredentials=null;
  if($activating){
   $current=nodenoPaymentConfiguration($db,$root);
   if(($current['version']??0)!==$job['expectedVersion'])throw new InvalidArgumentException('maintenance_version_conflict');
   if(($current['accountId']??'')!=='acct_1UaASFLFNjlPPKTy'||($current['mode']??'')!=='live'||empty($current['verifiedAt'])||empty($current['webhookVerifiedAt'])||!nodenoPaymentCredentialsMatch($current)||($current['seller']['authorityConfirmed']??false)!==true||($current['seller']['name']??'')!=='PTYS Technologies L.L.C.')throw new InvalidArgumentException('maintenance_payment_verification_required');
   $activeCredentials=$current['credentials'];
   $account=($provider??'nodenoPaymentStripe')($activeCredentials,'GET','/v1/account');
   if(($account['id']??'')!==$current['accountId']||empty($account['charges_enabled'])||($account['capabilities']['card_payments']??'')!=='active')throw new InvalidArgumentException('maintenance_stripe_account_not_ready');
  }
  return nodenoControlTransaction($db,static function()use($db,$root,$job,$documents,$documentsHash,$languages,$activating,$updating,$activeCredentials):array{
   $cfg=nodenoControlSetting($db,'payment:stripe',[]);
   if(($cfg['version']??0)!==$job['expectedVersion'])throw new InvalidArgumentException('maintenance_version_conflict');
   if(!$updating&&($cfg['enabled']??false)!==false)throw new InvalidArgumentException('maintenance_checkout_active');
   if($updating&&($cfg['seller']['termsVersion']??'')===$documents['termsVersion'])throw new InvalidArgumentException('maintenance_document_version_unchanged');
   if(($cfg['accountId']??'')!=='acct_1UaASFLFNjlPPKTy'||($cfg['mode']??'')!=='live'||!is_array($cfg['seller']??null))throw new InvalidArgumentException('maintenance_existing_account_protected');
   $saved=$cfg;$saved['version']=$job['expectedVersion']+1;
   foreach(['termsVersion','terms','returns']as $field)$saved['seller'][$field]=$documents[$field];
   if($activating){
    // This records the owner's commercial/tax-price instructions, not a government registration check.
    $saved['seller']['taxConfirmed']=true;$saved['enabled']=true;$saved['verifiedAt']=time();
    $saved['billingDecision']=$job['billingDecision']+['governmentTaxRegistrationVerified'=>false,'approvedAt'=>time()];
    $ready=$saved;$ready['credentials']=$activeCredentials;if(!nodenoPaymentReady($ready))throw new InvalidArgumentException('maintenance_payment_verification_required');
   }
   nodenoPaymentSaveConfiguration($db,$saved,$job['expectedVersion']);
   nodenoControlAudit($db,$root,'maintenance:cpanel',$activating?'activate':($updating?'update-documents':'save-draft'),'payments',$activating?'stripe':'sale-documents',['jobHash'=>hash('sha256',$job['nonce']),'documentsHash'=>$documentsHash,'termsVersion'=>$documents['termsVersion'],'enabled'=>$saved['enabled'],...($activating?['billingDecision'=>$saved['billingDecision']]:[])]);
   return ['status'=>$activating?'payments_activated':'sale_documents_saved','version'=>$saved['version'],'termsVersion'=>$documents['termsVersion'],'documentsHash'=>$documentsHash,'languages'=>$languages,'documentsPopulated'=>true,'checkoutEnabled'=>$saved['enabled'],'taxConfirmed'=>$saved['seller']['taxConfirmed']??false,'credentialsPreserved'=>true,...($activating?['ownerBillingApproved'=>true,'governmentTaxRegistrationVerified'=>false]:[])];
  });
 }
 if(($job['action']??'')==='inspect-stripe'){
  if(array_diff(array_keys($job),$common))throw new InvalidArgumentException('maintenance_job_invalid');$cfg=nodenoPaymentConfiguration($db,$root);$key=!empty($cfg['credentials']['secretKey']);$hook=!empty($cfg['credentials']['webhookSecret']);$accountVerified=!empty($cfg['verifiedAt']);$webhookVerified=!empty($cfg['webhookVerifiedAt']);
  return ['status'=>'stripe_status','connected'=>$key&&$hook&&$accountVerified&&$webhookVerified,'accountId'=>$cfg['accountId']??null,'mode'=>$cfg['mode']??null,'keyConfigured'=>$key,'webhookConfigured'=>$hook,'accountVerified'=>$accountVerified,'webhookVerified'=>$webhookVerified,'version'=>$cfg['version']??0,'checkoutEnabled'=>nodenoPaymentReady($cfg),'taxConfirmed'=>$cfg['seller']['taxConfirmed']??false,'saleDocumentsReady'=>nodenoPaymentSellerReady($cfg['seller']??[])];
 }
 if(($job['action']??'')==='recover-password'){
  if(array_diff(array_keys($job),[...$common,'passwordHash'])||!is_string($job['passwordHash']??null))throw new InvalidArgumentException('maintenance_job_invalid');
  $info=password_get_info($job['passwordHash']);if(($info['algoName']??'')!=='bcrypt'||($info['options']['cost']??0)<12)throw new InvalidArgumentException('maintenance_hash_invalid');
  return nodenoControlTransaction($db,static function()use($db,$root,$job):array{
   $s=$db->prepare("SELECT id,role,active FROM control_users WHERE email=?");$s->execute(['hamzaozbalkan@gmail.com']);$owner=$s->fetch();if(!$owner||$owner['role']!=='owner'||!(bool)$owner['active'])throw new InvalidArgumentException('maintenance_owner_not_found');
   $db->prepare('UPDATE control_users SET password_hash=?,auth_version=auth_version+1,version=version+1,updated_at=? WHERE id=?')->execute([$job['passwordHash'],time(),$owner['id']]);
   nodenoControlAudit($db,$root,'maintenance:cpanel','recover-password','team',$owner['id'],['jobHash'=>hash('sha256',$job['nonce']),'mfaPreserved'=>true]);
   return ['status'=>'password_recovered','email'=>'hamzaozbalkan@gmail.com','mfaPreserved'=>true,'accountPreserved'=>true];
  });
 }
 if(($job['action']??'')==='configure-stripe'){
  if(array_diff(array_keys($job),[...$common,'expectedVersion','accountId','credentials'])||($job['accountId']??'')!=='acct_1UaASFLFNjlPPKTy'||!is_int($job['expectedVersion']??null)||!is_array($job['credentials']??null)||array_diff(array_keys($job['credentials']),['secretKey','webhookSecret'])||!nodenoPaymentCredentialsMatch(['mode'=>'live','credentials'=>$job['credentials']]))throw new InvalidArgumentException('maintenance_stripe_invalid');
  $cfg=nodenoPaymentConfiguration($db,$root);if(($cfg['version']??0)!==$job['expectedVersion'])throw new InvalidArgumentException('maintenance_version_conflict');
  if(!empty($cfg['credentials']['secretKey'])&&(($cfg['accountId']??'')!==$job['accountId']||($cfg['mode']??'')!=='live'))throw new InvalidArgumentException('maintenance_existing_account_protected');
  $account=($provider??'nodenoPaymentStripe')($job['credentials'],'GET','/v1/account');if(($account['id']??'')!==$job['accountId']||empty($account['charges_enabled']))throw new InvalidArgumentException('maintenance_stripe_account_not_ready');
  if(!empty($cfg['credentials']['secretKey'])&&$cfg['credentials']!==$job['credentials'])throw new InvalidArgumentException('maintenance_existing_credentials_protected');
  $seller=$cfg['seller']??['name'=>'PTYS Technologies L.L.C.','address'=>'30 N Gould St Ste N, Sheridan, WY 82801, United States','email'=>'info@ptys.com.tr','termsVersion'=>'','terms'=>array_fill_keys(['tr','en','ru','ar'],''),'returns'=>array_fill_keys(['tr','en','ru','ar'],''),'taxConfirmed'=>false,'authorityConfirmed'=>true];
  $saved=['version'=>($cfg['version']??0)+1,'enabled'=>false,'mode'=>'live','accountId'=>$job['accountId'],'seller'=>$seller,'verifiedAt'=>time(),'webhookVerifiedAt'=>null,'credentials'=>nodenoControlEncrypt($root,json_encode($job['credentials'],JSON_THROW_ON_ERROR),'stripe-credentials')];
  nodenoControlTransaction($db,static function()use($db,$root,$job,$saved):void{nodenoPaymentSaveConfiguration($db,$saved,$job['expectedVersion']);nodenoControlAudit($db,$root,'maintenance:cpanel','configure','payments','stripe',['jobHash'=>hash('sha256',$job['nonce']),'accountId'=>$job['accountId'],'mode'=>'live','enabled'=>false]);});
  return ['status'=>'stripe_configured','accountId'=>$job['accountId'],'mode'=>'live','accountVerified'=>true,'keyEncrypted'=>true,'checkoutEnabled'=>false];
 }
 throw new InvalidArgumentException('maintenance_action_invalid');
}
if(PHP_SAPI==='cli'&&realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__){
 umask(0077);$nonce=$argv[1]??'';if(!preg_match('/^[a-f0-9]{64}$/D',$nonce))exit(2);
 $home=dirname(__DIR__);$seed=__DIR__.'/job-'.$nonce.'.json';$receipt=__DIR__.'/receipt-'.$nonce.'.json';$lockFile=__DIR__.'/job-'.$nonce.'.lock';
 if(is_file($receipt)||is_link($seed)||!is_file($seed)||filesize($seed)>100000)exit(0);
 $lock=fopen($lockFile,'c');if(!$lock||!flock($lock,LOCK_EX|LOCK_NB))exit(0);
 try{
  if(is_file($receipt))exit(0);chmod($seed,0600);$job=json_decode(file_get_contents($seed),true,16,JSON_THROW_ON_ERROR);if(!is_array($job)||($job['nonce']??null)!==$nonce)throw new InvalidArgumentException('maintenance_job_invalid');
  $runtime=require $home.'/nodeno-runtime.php';require_once $runtime['privateRoot'].'/payment-admin.php';$root=nodenoAccountStorage($runtime['storageRoot']);$db=nodenoControlDatabase($root);
  $result=nodenoPrivateMaintenance($db,$root,$job);$result['at']=time();file_put_contents($receipt,json_encode($result,JSON_THROW_ON_ERROR),LOCK_EX);chmod($receipt,0600);unlink($seed);
 }catch(Throwable $e){$error=$e instanceof InvalidArgumentException?$e->getMessage():'maintenance_failed';file_put_contents($receipt,json_encode(['status'=>'failed','error'=>$error,'at'=>time()],JSON_THROW_ON_ERROR),LOCK_EX);chmod($receipt,0600);if(is_file($seed)&&!is_link($seed))unlink($seed);}
 finally{flock($lock,LOCK_UN);fclose($lock);}
}
