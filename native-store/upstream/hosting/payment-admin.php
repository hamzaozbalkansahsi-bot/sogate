<?php
declare(strict_types=1);
require_once __DIR__.'/payment-stripe.php';

function nodenoShippingSeller(array $seller):array {
 $sections=json_decode('{"tr": "4. Kargo, ambar ve ek hizmetler\nTürkiye içi standart kargo veya ambar sevkiyatı ürün fiyatına dahildir; ayrıca taşıyıcıya taşıma bedeli ödenmez. Yurt dışı teslimatlarda nakliye, gümrükleme ve ilgili maliyetler için ayrı teklif alınır. Kata çıkarma ve montaj gibi ek hizmetler, ayrıca belirtilmedikçe dahil değildir; ücretli ek hizmetler açık onay olmadan eklenmez.", "en": "4. Freight and additional services\nStandard delivery within Türkiye is included in the product price; no separate freight payment to the carrier is required. International freight, customs clearance and related costs require a separate quotation. Carrying upstairs and installation are excluded unless stated; paid additional services require explicit consent.", "ru": "4. Доставка и дополнительные услуги\nСтандартная доставка по Турции включена в цену товара; отдельно оплачивать перевозчику доставку не требуется. Международная перевозка, таможенное оформление и связанные расходы согласуются в отдельном предложении. Подъём и установка не включены, если не указано иное; платные дополнительные услуги требуют явного согласия.", "ar": "4. الشحن والخدمات الإضافية\nالشحن القياسي داخل تركيا مشمول في سعر المنتج ولا تُدفع رسوم شحن منفصلة للناقل. يتطلب الشحن الدولي والتخليص الجمركي والتكاليف ذات الصلة عرضاً منفصلاً. لا يشمل السعر الصعود للطوابق أو التركيب ما لم يُذكر ذلك، وتتطلب الخدمات الإضافية المدفوعة موافقة صريحة."}',true,32,JSON_THROW_ON_ERROR);
 foreach($seller['terms']??[]as $locale=>$text){if(isset($sections[$locale]))$seller['terms'][$locale]=preg_replace('/(^|\n\n)4\..*?(?=\n\n5\.)/su',"\n\n".$sections[$locale],$text,1);}
 $seller['termsVersion']=preg_replace('/-shipping-20261112$/','',$seller['termsVersion']??'').'-shipping-20261112';return $seller;
}
function nodenoPaymentConfiguration(PDO $db,string $root):array {
 $value=nodenoControlSetting($db,'payment:stripe',[]);if(isset($value['credentials']))$value['credentials']=json_decode(nodenoControlDecrypt($root,$value['credentials'],'stripe-credentials'),true,8,JSON_THROW_ON_ERROR);if(isset($value['retiredWebhooks']))$value['retiredWebhooks']=json_decode(nodenoControlDecrypt($root,$value['retiredWebhooks'],'stripe-retired-webhooks'),true,16,JSON_THROW_ON_ERROR);if(isset($value['seller']))$value['seller']=nodenoShippingSeller($value['seller']);return $value;
}
function nodenoPaymentReady(array $config,bool $allowTest=false):bool {
 return ($config['enabled']??false)===true&&in_array($config['mode']??'', $allowTest?['live','test']:['live'],true)&&!empty($config['accountId'])&&!empty($config['verifiedAt'])&&!empty($config['webhookVerifiedAt'])&&nodenoPaymentCredentialsMatch($config)&&nodenoPaymentSellerReady($config['seller']??[]);
}
function nodenoPaymentCredentialsMatch(array $cfg):bool {return nodenoPaymentSecretKeyValid($cfg['credentials']['secretKey']??null,$cfg['mode']??'')&&is_string($cfg['credentials']['webhookSecret']??null)&&preg_match('/^whsec_[A-Za-z0-9]{16,}$/D',$cfg['credentials']['webhookSecret'])===1;}
function nodenoPaymentTermsRevision(array $seller):string {return hash('sha256',json_encode($seller,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));}
function nodenoPaymentSellerReady(array $seller):bool {
 if(($seller['taxConfirmed']??false)!==true||($seller['authorityConfirmed']??false)!==true)return false;
 foreach(['name','address','email','termsVersion']as $key)if(!is_string($seller[$key]??null)||trim($seller[$key])==='')return false;
 foreach(['terms','returns']as $key)foreach(['tr','en','ru','ar']as $lang)if(strlen(trim($seller[$key][$lang]??''))<20)return false;
 return filter_var($seller['email'],FILTER_VALIDATE_EMAIL)!==false;
}
function nodenoPaymentSettingsView(array $cfg):array {
 return ['enabled'=>$cfg['enabled']??false,'ready'=>nodenoPaymentReady($cfg),'mode'=>$cfg['mode']??'test','accountId'=>$cfg['accountId']??null,'keyConfigured'=>!empty($cfg['credentials']['secretKey']),'webhookConfigured'=>!empty($cfg['credentials']['webhookSecret']),'verifiedAt'=>$cfg['verifiedAt']??null,'webhookVerifiedAt'=>$cfg['webhookVerifiedAt']??null,'seller'=>$cfg['seller']??null,'version'=>$cfg['version']??0];
}
function nodenoPaymentSaveConfiguration(PDO $db,array $saved,int $expected):void {
 nodenoControlTransaction($db,static function()use($db,$saved,$expected):void{
  $current=nodenoControlSetting($db,'payment:stripe',[]);if(($current['version']??0)!==$expected)throw new NodenoControlHttpError(409,'version_conflict');nodenoControlSetSetting($db,'payment:stripe',$saved);
 });
}
function nodenoPaymentAdmin(array $ctx,string $route,string $method,array $body):array {
 $db=$ctx['db'];$root=$ctx['root'];nodenoPaymentSchema($db);
 if($route==='payment-orders'&&$method==='GET'){
  nodenoControlRequire($ctx,'operations.read');$rows=$db->query('SELECT o.*,COALESCE(r.amount_minor,0) AS refunded_minor,COALESCE(r.pending_minor,0) AS refund_pending_minor,r.refund_status FROM payment_orders o LEFT JOIN payment_refunds r ON r.order_id=o.id ORDER BY o.created_at DESC LIMIT 300')->fetchAll();
  return ['data'=>array_map(static function($row)use($root){$p=nodenoPaymentPrivate($root,$row);return nodenoPaymentPublic($row)+['contact'=>$p['contact'],'snapshot'=>json_decode($row['snapshot_json'],true),'seller'=>json_decode($row['seller_json'],true)];},$rows)];
 }
 $actor=nodenoControlRequire($ctx,'payments.manage',$method!=='GET');$cfg=nodenoPaymentConfiguration($db,$root);
 if($route==='payments'&&$method==='GET')return nodenoPaymentSettingsView($cfg);
 if($route==='payments/verify'&&$method==='POST'){
  $account=nodenoPaymentStripe($cfg['credentials']??[],'GET','/v1/account');
  if(($account['id']??'')!==($cfg['accountId']??'')||empty($account['charges_enabled']))throw new NodenoControlHttpError(422,'payment_account_not_ready');
  $saved=nodenoControlSetting($db,'payment:stripe',[]);if(($saved['version']??0)!==($cfg['version']??0))throw new NodenoControlHttpError(409,'version_conflict');$saved['verifiedAt']=time();$saved['version']=($saved['version']??0)+1;nodenoPaymentSaveConfiguration($db,$saved,$cfg['version']??0);nodenoControlAudit($db,$root,$actor['id'],'verify','payments','stripe',['accountId'=>$saved['accountId']]);return nodenoPaymentSettingsView(nodenoPaymentConfiguration($db,$root));
 }
 if($route!=='payments'||$method!=='PUT')throw new NodenoControlHttpError(405,'method_not_allowed');
 if(($body['version']??null)!==($cfg['version']??0))throw new NodenoControlHttpError(409,'version_conflict');
 if(array_diff(array_keys($body),['version','enabled','mode','accountId','secretKey','webhookSecret','seller'])||!is_bool($body['enabled']??null)||!in_array($body['mode']??'', ['test','live'],true)||!preg_match('/^acct_[A-Za-z0-9]+$/D',$body['accountId']??''))throw new NodenoControlHttpError(422,'payment_configuration_invalid');
 $credentials=$cfg['credentials']??[];$changed=false;
 foreach(['secretKey','webhookSecret']as $key)if(($body[$key]??'')!==''){
  $value=$body[$key];if($key==='secretKey'?!nodenoPaymentSecretKeyValid($value,$body['mode']):(!is_string($value)||strlen($value)>512||!preg_match('/^whsec_[A-Za-z0-9]{16,}$/D',$value)))throw new NodenoControlHttpError(422,'payment_credential_invalid');
  if(($credentials[$key]??'')!==$value)$changed=true;$credentials[$key]=$value;
 }
 $switch=$body['mode']!==($cfg['mode']??'test')||$body['accountId']!==($cfg['accountId']??'');
 if($switch&&(!is_string($body['secretKey']??null)||($body['secretKey']??'')===''||($body['secretKey']??'')===($cfg['credentials']['secretKey']??null)||!is_string($body['webhookSecret']??null)||($body['webhookSecret']??'')===''||($body['webhookSecret']??'')===($cfg['credentials']['webhookSecret']??null)))throw new NodenoControlHttpError(422,'payment_credentials_required');
 if(!nodenoPaymentCredentialsMatch(['mode'=>$body['mode'],'credentials'=>$credentials]))throw new NodenoControlHttpError(422,'payment_credential_invalid');
 $retired=array_values(array_filter($cfg['retiredWebhooks']??[],static fn($entry)=>$entry['expiresAt']>time()));
 if(($changed||$switch)&&!empty($cfg['credentials']['webhookSecret']))$retired[]=['accountId'=>$cfg['accountId'],'mode'=>$cfg['mode'],'credentials'=>$cfg['credentials'],'webhookVerifiedAt'=>$cfg['webhookVerifiedAt']??null,'expiresAt'=>time()+604800];
 if(count($retired)>16)throw new NodenoControlHttpError(409,'payment_rotation_limit');
 $seller=$body['seller']??null;if(!is_array($seller)||array_diff(array_keys($seller),['name','address','email','taxConfirmed','authorityConfirmed','termsVersion','terms','returns']))throw new NodenoControlHttpError(422,'payment_seller_required');
 foreach(['name','address','email','termsVersion']as $key)if(!is_string($seller[$key]??null)||strlen($seller[$key])>1200||preg_match('/[<>\x00-\x1f]/',$seller[$key]))throw new NodenoControlHttpError(422,'payment_seller_required');
 if(($seller['email']!==''&&!filter_var($seller['email'],FILTER_VALIDATE_EMAIL))||!is_bool($seller['taxConfirmed']??null)||!is_bool($seller['authorityConfirmed']??null))throw new NodenoControlHttpError(422,'payment_seller_required');
 foreach(['terms','returns']as $key)foreach(['tr','en','ru','ar']as $lang)if(!is_string($seller[$key][$lang]??null)||strlen($seller[$key][$lang])>12000||preg_match('/[<>\x00-\x08\x0b-\x1f]/u',$seller[$key][$lang]))throw new NodenoControlHttpError(422,'payment_terms_required');
 $saved=['version'=>($cfg['version']??0)+1,'enabled'=>$body['enabled'],'mode'=>$body['mode'],'accountId'=>$body['accountId'],'seller'=>$seller,'verifiedAt'=>($changed||$switch)?null:($cfg['verifiedAt']??null),'webhookVerifiedAt'=>($changed||$switch)?null:($cfg['webhookVerifiedAt']??null),'credentials'=>nodenoControlEncrypt($root,json_encode($credentials,JSON_THROW_ON_ERROR),'stripe-credentials'),'retiredWebhooks'=>nodenoControlEncrypt($root,json_encode($retired,JSON_THROW_ON_ERROR),'stripe-retired-webhooks')];
 $ready=$saved;$ready['credentials']=$credentials;if($body['enabled']&&!nodenoPaymentReady($ready,true))throw new NodenoControlHttpError(422,'payment_verification_required');
 nodenoPaymentSaveConfiguration($db,$saved,$cfg['version']??0);nodenoControlAudit($db,$root,$actor['id'],'configure','payments','stripe',['mode'=>$body['mode'],'enabled'=>$body['enabled'],'version'=>$saved['version']]);return nodenoPaymentSettingsView($ready);
}
