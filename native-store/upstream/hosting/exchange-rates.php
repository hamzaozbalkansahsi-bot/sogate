<?php
declare(strict_types=1);

function nodenoFxWeek(DateTimeImmutable $now):string {
 $day=$now->setTimezone(new DateTimeZone('Europe/Istanbul'))->setTime(0,0);
 return $day->modify('-'.((int)$day->format('N')-1).' days')->format('Y-m-d');
}
function nodenoFxParse(string $body,?string $expectedDate=null):array {
 if(strlen($body)>150000||preg_match('/<!DOCTYPE|<!ENTITY/i',$body))throw new RuntimeException('fx_source_invalid');
 $previous=libxml_use_internal_errors(true);
 try{$xml=simplexml_load_string($body,SimpleXMLElement::class,LIBXML_NONET);if(!$xml||$xml->getName()!=='Tarih_Date')throw new RuntimeException('fx_source_invalid');}
 finally{libxml_clear_errors();libxml_use_internal_errors($previous);}
 $raw=(string)$xml['Tarih'];$date=DateTimeImmutable::createFromFormat('!d.m.Y',$raw,new DateTimeZone('Europe/Istanbul'));
 if(!$date||$date->format('d.m.Y')!==$raw||($expectedDate!==null&&$date->format('Y-m-d')!==$expectedDate))throw new RuntimeException('fx_source_date_invalid');
 $rates=[];foreach($xml->Currency as $row){$code=(string)$row['CurrencyCode'];$amount=trim((string)$row->ForexSelling);$unit=(string)$row->Unit;
  if($amount==='')continue;
  if(!preg_match('/^[A-Z]{3}$/D',$code)||isset($rates[$code])||!preg_match('/^\d{1,7}(?:\.\d{1,6})?$/D',$amount)||!preg_match('/^[1-9]\d{0,3}$/D',$unit))throw new RuntimeException('fx_source_rate_invalid');
  $parts=explode('.',$amount);$micros=(int)$parts[0]*1000000+(int)str_pad($parts[1]??'',6,'0');if($micros<=0)throw new RuntimeException('fx_source_rate_invalid');
  $rates[$code]=['rateMicros'=>$micros,'unit'=>(int)$unit,'date'=>$date->format('Y-m-d')];
 }
 if(!isset($rates['USD'],$rates['EUR']))throw new RuntimeException('fx_source_incomplete');
 return ['date'=>$date->format('Y-m-d'),'rates'=>$rates,'sha256'=>hash('sha256',$body)];
}
function nodenoFxUrl(string $date):string {return 'https://www.tcmb.gov.tr/kurlar/'.substr($date,0,4).substr($date,5,2).'/'.substr($date,8,2).substr($date,5,2).substr($date,0,4).'.xml';}
function nodenoFxFetch(array $dates):array {
 $multi=curl_multi_init();$handles=[];
 foreach($dates as $date){$handle=curl_init(nodenoFxUrl($date));curl_setopt_array($handle,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_CONNECTTIMEOUT=>4,CURLOPT_TIMEOUT=>9,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_HTTPHEADER=>['Accept: application/xml','User-Agent: NODENO-FX/1.0'],CURLOPT_PROTOCOLS=>CURLPROTO_HTTPS]);curl_multi_add_handle($multi,$handle);$handles[$date]=$handle;}
 do{$status=curl_multi_exec($multi,$active);if($active)curl_multi_select($multi,.2);}while($active&&$status===CURLM_OK);
 $result=[];foreach($handles as $date=>$handle){$body=curl_multi_getcontent($handle);$result[$date]=['status'=>curl_errno($handle)?0:(int)curl_getinfo($handle,CURLINFO_HTTP_CODE),'body'=>is_string($body)?$body:''];curl_multi_remove_handle($multi,$handle);}$handles=[];$handle=null;$multi=null;return $result;
}
function nodenoFxBuild(DateTimeImmutable $now,callable $fetcher):array {
 $now=$now->setTimezone(new DateTimeZone('Europe/Istanbul'));$week=nodenoFxWeek($now);$today=$now->format('Y-m-d');$dates=[];
 for($day=new DateTimeImmutable($week,new DateTimeZone('Europe/Istanbul'));$day->format('Y-m-d')<=$today;$day=$day->modify('+1 day'))if((int)$day->format('N')<=5)$dates[]=$day->format('Y-m-d');
 $responses=$fetcher($dates);$days=[];
 foreach($dates as $date){$response=$responses[$date]??[];if(($response['status']??0)===404)continue;if(($response['status']??0)!==200)throw new RuntimeException('fx_source_unavailable');$days[]=nodenoFxParse($response['body'],$date);}
 $carry=false;
 if(!$days){$carry=true;for($back=1;$back<=10;$back++){$date=$now->modify('-'.$back.' days');if((int)$date->format('N')>5)continue;$key=$date->format('Y-m-d');if($key>=$week)continue;$response=$fetcher([$key])[$key]??[];if(($response['status']??0)===404)continue;if(($response['status']??0)!==200)throw new RuntimeException('fx_source_unavailable');$days[]=nodenoFxParse($response['body'],$key);break;}}
 if(!$days)throw new RuntimeException('fx_source_unavailable');
 $rates=[];$sources=[];foreach($days as $day){$sources[]=['date'=>$day['date'],'url'=>nodenoFxUrl($day['date']),'sha256'=>$day['sha256']];foreach($day['rates']as $code=>$rate){$old=$rates[$code]??null;if(!$old||$rate['rateMicros']*$old['unit']>$old['rateMicros']*$rate['unit'])$rates[$code]=$rate;}}
 ksort($rates);$data=['schema'=>1,'base'=>'TRY','policy'=>'week_to_date_highest_forex_selling','timezone'=>'Europe/Istanbul','weekStart'=>$week,'asOf'=>$today,'carriedForward'=>$carry,'rates'=>$rates,'sources'=>$sources];
 $data['revision']=hash('sha256',json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES));$data['verifiedAt']=$now->getTimestamp();$data['validUntil']=$now->getTimestamp()+1800;return $data;
}
function nodenoFxSnapshot(string $storage,?DateTimeImmutable $now=null):array {
 $now??=new DateTimeImmutable('now',new DateTimeZone('Europe/Istanbul'));$file=$storage.'/exchange-rates-v1.json';$old=null;
 if(is_file($file)&&!is_link($file)){try{$old=json_decode((string)file_get_contents($file),true,32,JSON_THROW_ON_ERROR);}catch(Throwable $e){}}
 $valid=is_array($old)&&($old['schema']??null)===1&&($old['weekStart']??null)===nodenoFxWeek($now)&&($old['asOf']??null)===$now->format('Y-m-d')&&($old['verifiedAt']??0)<=$now->getTimestamp()+60;
 if($valid&&($old['validUntil']??0)>$now->getTimestamp())return $old;
 $lockPath=$storage.'/exchange-rates.lock';if(is_link($lockPath))throw new RuntimeException('fx_storage_invalid');$lock=fopen($lockPath,'c');if(!$lock)throw new RuntimeException('fx_storage_unavailable');
 try{if(!flock($lock,LOCK_EX|LOCK_NB)){if($valid&&$now->getTimestamp()-$old['verifiedAt']<21600)return $old+['refreshPending'=>true];throw new RuntimeException('fx_refresh_pending');}
  try{$snapshot=nodenoFxBuild($now,'nodenoFxFetch');$temporary=$file.'.'.bin2hex(random_bytes(8));if(file_put_contents($temporary,json_encode($snapshot,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),LOCK_EX)===false)throw new RuntimeException('fx_storage_unavailable');chmod($temporary,0600);if(!rename($temporary,$file)){unlink($temporary);throw new RuntimeException('fx_storage_unavailable');}return $snapshot;}
  catch(Throwable $e){if($valid&&$now->getTimestamp()-$old['verifiedAt']<21600)return $old+['stale'=>true];throw $e;}
 }finally{flock($lock,LOCK_UN);fclose($lock);}
}
function nodenoFxConvert(int $tryMinor,array $rate,int $exponent=2):int {
 if($tryMinor<0||!is_int($rate['rateMicros']??null)||$rate['rateMicros']<=0||!is_int($rate['unit']??null)||$rate['unit']<1||$rate['unit']>10000||$exponent<0||$exponent>3)throw new RuntimeException('fx_amount_invalid');
 // Decimal long multiplication/division avoids floats and optional PHP extensions.
 $factor=1000000*$rate['unit']*(10**$exponent);$carry=0;$numerator='';
 foreach(array_reverse(str_split((string)$tryMinor))as $digit){$part=(int)$digit*$factor+$carry;$numerator=($part%10).$numerator;$carry=intdiv($part,10);}while($carry){$numerator=($carry%10).$numerator;$carry=intdiv($carry,10);}
 $denominator=100*$rate['rateMicros'];if(!is_int($denominator)||$denominator>intdiv(PHP_INT_MAX,10))throw new RuntimeException('fx_amount_overflow');
 $remainder=0;$quotient='';foreach(str_split($numerator)as $digit){$remainder=$remainder*10+(int)$digit;$quotient.=intdiv($remainder,$denominator);$remainder%=$denominator;}
 $quotient=ltrim($quotient,'0')?:'0';$limit='9007199254740991';if(strlen($quotient)>strlen($limit)||(strlen($quotient)===strlen($limit)&&strcmp($quotient,$limit)>0))throw new RuntimeException('fx_amount_overflow');
 $amount=(int)$quotient;if($remainder*2>=$denominator)$amount++;if($amount>9007199254740991)throw new RuntimeException('fx_amount_overflow');return $amount;
}
