<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';
require_once __DIR__.'/payment-store.php';

function nodenoPaymentSecretKeyValid($key,string $mode):bool {
 if(!in_array($mode,['test','live'],true)||!is_string($key)||strlen($key)>512)return false;
 $prefix=$mode==='test'?'(?:sk|rk|rkcs)':'(?:sk|rk)';
 return preg_match('/^'.$prefix.'_'.$mode.'_[A-Za-z0-9]{16,}$/D',$key)===1;
}
function nodenoPaymentStripeEncode(array $form):string {
 $normalize=static function($value)use(&$normalize){if(is_array($value))return array_map($normalize,$value);return is_bool($value)?($value?'true':'false'):$value;};
 return http_build_query($normalize($form),'','&',PHP_QUERY_RFC3986);
}
function nodenoPaymentStripe(array $credentials,string $method,string $path,array $form=[],?string $idempotency=null):array {
 if(!in_array($method,['GET','POST'],true)||(!in_array($path,['/v1/account','/v1/checkout/sessions'],true)&&!($method==='GET'&&preg_match('~^/v1/events/evt_[A-Za-z0-9_]+$~D',$path))))throw new RuntimeException('Unsupported Stripe operation');
 $key=$credentials['secretKey']??'';if(!nodenoPaymentSecretKeyValid($key,'test')&&!nodenoPaymentSecretKeyValid($key,'live'))throw new NodenoControlHttpError(503,'payment_not_configured');
 $headers=['Authorization: Bearer '.$key,'Accept: application/json','Stripe-Version: 2026-10-28.endive'];
 if($idempotency!==null){if(!preg_match('/^[a-zA-Z0-9_-]{1,200}$/D',$idempotency))throw new RuntimeException('Invalid provider idempotency');$headers[]='Idempotency-Key: '.$idempotency;}
 $response='';$tooLarge=false;$curl=curl_init('https://api.stripe.com'.$path);
 curl_setopt_array($curl,[CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_HTTPHEADER=>$headers,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>35,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_PROTOCOLS=>CURLPROTO_HTTPS,CURLOPT_WRITEFUNCTION=>static function($handle,string $part)use(&$response,&$tooLarge):int{if(strlen($response)+strlen($part)>2000000){$tooLarge=true;return 0;}$response.=$part;return strlen($part);}]);
 if($method==='POST')curl_setopt($curl,CURLOPT_POSTFIELDS,nodenoPaymentStripeEncode($form));
 $ok=curl_exec($curl);$status=curl_getinfo($curl,CURLINFO_RESPONSE_CODE);curl_close($curl);
 if($ok===false||$tooLarge)throw new NodenoControlHttpError(503,'payment_provider_unavailable');
 try{$data=json_decode($response,true,64,JSON_THROW_ON_ERROR);}catch(Throwable $e){throw new NodenoControlHttpError(503,'payment_provider_unavailable');}
 if($status<200||$status>=300||!is_array($data))throw new NodenoControlHttpError(503,$status===401||$status===403?'payment_provider_authentication':'payment_provider_unavailable');return $data;
}
function nodenoPaymentStripeForm(array $order,array $private,string $origin):array {
 if(!preg_match('~^https://(www\.)?nodenohome\.com(\.tr)?$~D',$origin)&&!preg_match('~^http://127\.0\.0\.1:[0-9]+$~D',$origin))throw new RuntimeException('Invalid return origin');
 $quote=json_decode($order['snapshot_json'],true,64,JSON_THROW_ON_ERROR);$locale=$order['locale'];$items=[];
 foreach($quote['lines']as $line){$name=nodenoLocaleLocal($line['name']??$line['code'],$locale);$name=implode('',array_slice(preg_split('//u',$name,-1,PREG_SPLIT_NO_EMPTY),0,190)).' × '.$line['quantity'];$items[]=['quantity'=>1,'price_data'=>['currency'=>'try','unit_amount'=>$line['totalMinor'],'product_data'=>['name'=>$name,'metadata'=>['nodeno_product_id'=>$line['id'],'vat_rate'=>(string)$line['vatRate']]]]];}
 $return=$origin.'/?page=checkout&lang='.rawurlencode($locale).'&payment='.$private['returnToken'];
 $messages=['tr'=>'Kargo/ambar alıcı ödemelidir; ürün bedeline dahil değildir.','en'=>'Freight is paid directly to the carrier by the recipient and is not included.','ru'=>'Доставка оплачивается получателем напрямую перевозчику и не включена в стоимость.','ar'=>'يدفع المستلم رسوم الشحن مباشرة إلى شركة النقل، وهي غير مشمولة في ثمن المنتجات.'];
 return ['mode'=>'payment','allowed_payment_method_types'=>['card'],'adaptive_pricing'=>['enabled'=>false],'line_items'=>$items,'customer_email'=>$private['contact']['email'],'client_reference_id'=>$order['id'],'metadata'=>['nodeno_order_id'=>$order['id']],'payment_intent_data'=>['metadata'=>['nodeno_order_id'=>$order['id']]],'success_url'=>$return,'cancel_url'=>$return.'&cancelled=1','expires_at'=>(int)$order['created_at']+3600,'custom_text'=>['submit'=>['message'=>nodenoLocaleCopy($messages,$locale)]]];
}
