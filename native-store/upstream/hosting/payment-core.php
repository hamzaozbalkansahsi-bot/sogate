<?php
declare(strict_types=1);
require_once __DIR__.'/door-commerce.php';

// Catalogue amounts are net. Round tax once per measured/quantity line, in kuruş.
function nodenoPaymentQuote(array $catalog,array $items,string $country):array {
 if($country!=='TR')throw new InvalidArgumentException('payment_country_not_supported');
 $quote=nodenoCommerceQuote($catalog,$items,$country,'TRY');
 if(!$quote['minimumEligible'])throw new InvalidArgumentException('payment_minimum_not_reached');
 if($quote['requiresQuote'])throw new InvalidArgumentException('payment_price_unavailable');
 $products=array_column($catalog['products'],null,'id');$lines=[];$net=0;$vat=0;
 foreach($quote['lines']as $line){
  $product=$products[$line['id']];$rate=match($line['productType']){'furniture'=>10,'door','cabinet-front'=>20,default=>null};
  if($rate===null||($product['currency']??'TRY')!=='TRY')throw new InvalidArgumentException('payment_product_not_supported');
  // Reservations are not yet connected to the inventory ledger. Never promise a controlled unit twice.
  if($product['stockKnown']??false)throw new InvalidArgumentException('payment_stock_reservation_required');
  $amount=$line['lineTotalMinor'];
  if(!is_int($amount)||$amount<=0||$amount>99999999)throw new InvalidArgumentException('payment_amount_invalid');
  $tax=intdiv($amount*$rate+50,100);$net+=$amount;$vat+=$tax;
  if($net+$vat>99999999)throw new InvalidArgumentException('payment_amount_invalid');
  $lines[]=$line+['netMinor'=>$amount,'vatRate'=>$rate,'vatMinor'=>$tax,'totalMinor'=>$amount+$tax];
 }
 $result=['schema'=>1,'country'=>'TR','currency'=>'TRY','catalogRevision'=>$quote['priceRevision'],'commerceRevision'=>$quote['revision'],'lines'=>$lines,'netMinor'=>$net,'vatMinor'=>$vat,'totalMinor'=>$net+$vat,'freight'=>['kind'=>'included','includedInCharge'=>true,'feeMinor'=>0]];
 $result['revision']=hash('sha256',json_encode($result,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));return $result;
}

function nodenoPaymentContact(array $input):array {
 if(array_diff(array_keys($input),['name','email','phone','delivery','sameBilling','billing']))throw new InvalidArgumentException('payment_contact_invalid');
 $text=static function($value,int $min,int $max,bool $multiline=false):string{
  if(!is_string($value)||!preg_match('//u',$value))throw new InvalidArgumentException('payment_contact_invalid');$value=trim($value);
  $value=str_replace(["\r\n","\r"],"\n",$value);if(strlen($value)<$min||strlen($value)>$max||preg_match($multiline?'/[<>\x00-\x08\x0b-\x1f\x7f]/u':'/[<>\x00-\x1f\x7f]/u',$value))throw new InvalidArgumentException('payment_contact_invalid');return $value;
 };
 $name=$text($input['name']??null,2,360);$email=$text($input['email']??null,3,254);$phone=$text($input['phone']??null,7,30);
 if(!filter_var($email,FILTER_VALIDATE_EMAIL)||!preg_match('/^[+0-9() .-]+$/D',$phone)||strlen(preg_replace('/\D/','',$phone))<7||strlen(preg_replace('/\D/','',$phone))>15)throw new InvalidArgumentException('payment_contact_invalid');
 $address=static function($value)use($text):array{
  if(!is_array($value)||array_diff(array_keys($value),['name','country','city','district','postalCode','line1','line2']))throw new InvalidArgumentException('payment_address_invalid');
  $out=[];foreach(['name'=>[2,360,false],'country'=>[2,80,false],'city'=>[2,300,false],'district'=>[0,300,false],'postalCode'=>[0,20,false],'line1'=>[5,1200,true],'line2'=>[0,750,true]]as $key=>$limits)$out[$key]=$text($value[$key]??'',...$limits);
  if(!in_array(strtolower($out['country']),['tr','türkiye','turkiye','turkey'],true))throw new InvalidArgumentException('payment_country_not_supported');$out['country']='TR';return $out;
 };
 if(!is_bool($input['sameBilling']??null))throw new InvalidArgumentException('payment_contact_invalid');
 $delivery=$address($input['delivery']??null);$billing=$input['sameBilling']?$delivery:$address($input['billing']??null);
 return ['name'=>$name,'email'=>$email,'phone'=>$phone,'delivery'=>$delivery,'sameBilling'=>$input['sameBilling'],'billing'=>$billing];
}

function nodenoPaymentVerifySignature(string $raw,string $header,string $secret,int $now):bool {
 if(strlen($header)>8192||$secret==='')throw new InvalidArgumentException('payment_signature_invalid');$timestamps=[];$signatures=[];
 foreach(explode(',',$header)as $part){$pair=explode('=',trim($part),2);if(count($pair)!==2)continue;if($pair[0]==='t')$timestamps[]=$pair[1];if($pair[0]==='v1')$signatures[]=$pair[1];}
 if(count($timestamps)!==1||!preg_match('/^[0-9]{10,11}$/D',$timestamps[0])||abs($now-(int)$timestamps[0])>300)throw new InvalidArgumentException('payment_signature_invalid');
 $expected=hash_hmac('sha256',$timestamps[0].'.'.$raw,$secret);
 foreach($signatures as $signature)if(strlen($signature)===64&&hash_equals($expected,$signature))return true;
 throw new InvalidArgumentException('payment_signature_invalid');
}

function nodenoPaymentEvent(array $order,array $event):array {
 $session=$event['data']['object']??[];$ignore=['status'=>'ignored'];
 if(!in_array($event['type']??'', ['checkout.session.completed','checkout.session.async_payment_succeeded','checkout.session.expired','checkout.session.async_payment_failed'],true))return $ignore;
 if(!is_bool($event['livemode']??null)||(bool)$order['live']!==$event['livemode']||($event['account']??'')!==$order['stripe_account_id']||($session['id']??'')!==$order['stripe_session_id']||($session['client_reference_id']??'')!==$order['id']||($session['metadata']['nodeno_order_id']??'')!==$order['id']||($session['amount_total']??null)!==$order['total_minor']||strtoupper($session['currency']??'')!==$order['currency'])return ['status'=>'mismatch'];
 if($event['type']==='checkout.session.expired')return ['status'=>'expired'];
 if($event['type']==='checkout.session.async_payment_failed')return ['status'=>'failed'];
 if(($session['payment_status']??'')!=='paid')return ['status'=>'pending'];
 $intent=$session['payment_intent']??null;if(!is_string($intent)||!preg_match('/^pi_[a-zA-Z0-9_]+$/D',$intent))return ['status'=>'mismatch'];
 return ['status'=>'paid','paymentIntent'=>$intent];
}
