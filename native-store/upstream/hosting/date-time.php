<?php
declare(strict_types=1);
// Shared human display only. Never use this formatter to serialize API or database timestamps.
function nodenoDateCountry(?string $country=null):string {$value=$country??($_COOKIE['nodeno_market_country']??'TR');return is_string($value)&&preg_match('/^[A-Z]{2}$/D',$value)?$value:'TR';}
function nodenoDateRegion(?string $country=null):array {
 $country=nodenoDateCountry($country);$map=[
 'TR'=>['tr_TR','Europe/Istanbul','d/m/Y',false],'GB'=>['en_GB','Europe/London','d/m/Y',false],'US'=>['en_US','America/New_York','m/d/Y',true],'CA'=>['en_CA','America/Toronto','Y-m-d',true],'AU'=>['en_AU','Australia/Sydney','d/m/Y',true],'NZ'=>['en_NZ','Pacific/Auckland','d/m/Y',true],
 'DE'=>['de_DE','Europe/Berlin','d.m.Y',false],'AT'=>['de_AT','Europe/Vienna','d.m.Y',false],'CH'=>['de_CH','Europe/Zurich','d.m.Y',false],'RU'=>['ru_RU','Europe/Moscow','d.m.Y',false],'AZ'=>['az_AZ','Asia/Baku','d.m.Y',false],'KZ'=>['kk_KZ','Asia/Almaty','d.m.Y',false],'TM'=>['tk_TM','Asia/Ashgabat','d.m.Y',false],'UZ'=>['uz_UZ','Asia/Tashkent','d/m/Y',false],'KG'=>['ky_KG','Asia/Bishkek','d.m.Y',false],
 'IR'=>['fa_IR','Asia/Tehran','Y/m/d',false],'IQ'=>['ar_IQ','Asia/Baghdad','d/m/Y',true],'SY'=>['ar_SY','Asia/Damascus','d/m/Y',true],'SA'=>['ar_SA','Asia/Riyadh','d/m/Y',true],'AE'=>['ar_AE','Asia/Dubai','d/m/Y',true],'EG'=>['ar_EG','Africa/Cairo','d/m/Y',true],
 'FR'=>['fr_FR','Europe/Paris','d/m/Y',false],'IT'=>['it_IT','Europe/Rome','d/m/Y',false],'ES'=>['es_ES','Europe/Madrid','d/m/Y',false],'NL'=>['nl_NL','Europe/Amsterdam','d-m-Y',false],'CN'=>['zh_CN','Asia/Shanghai','Y/m/d',false],'JP'=>['ja_JP','Asia/Tokyo','Y/m/d',false],'IN'=>['en_IN','Asia/Kolkata','d/m/Y',true],
 ];static $registry=null;if($registry===null){$file=is_file(__DIR__.'/date-time-regions.json')?__DIR__.'/date-time-regions.json':dirname(__DIR__).'/data/date-time-regions.json';$registry=is_file($file)?json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR)['regions']:[];}
 $saved=$registry[$country]??null;$row=$saved?[$saved['locale'],$saved['timeZone'],$saved['datePattern'],$saved['hour12']]:($map[$country]??['en_'.$country,'UTC','d/m/Y',false]);$zone=$row[1];$preferred=$_COOKIE['nodeno_date_timezone']??null;
 if($country!=='TR'&&is_string($preferred)&&in_array($preferred,DateTimeZone::listIdentifiers(DateTimeZone::ALL_WITH_BC),true)){try{$candidate=new DateTimeZone($preferred);$place=$candidate->getLocation();if(is_array($place)&&($place['country_code']??'')===$country)$zone=$preferred;}catch(Throwable $e){}}
 return ['country'=>$country,'locale'=>$row[0],'timeZone'=>$zone,'datePattern'=>$row[2],'hour12'=>$row[3],'digits'=>$saved['digits']??str_split('0123456789'),'hourCycle'=>$saved['hourCycle']??($row[3]?'h12':'h23'),'timeParts'=>$saved['timeParts']??null,'dayPeriods'=>$saved['dayPeriods']??['am'=>'AM','pm'=>'PM']];
}
function nodenoDateDigits(string $text,array $region):string {return strtr($text,array_combine(str_split('0123456789'),$region['digits']));}
function nodenoDateValue($value):?DateTimeImmutable {
 try{if($value instanceof DateTimeInterface)return DateTimeImmutable::createFromInterface($value);if(is_int($value)||is_float($value))return new DateTimeImmutable('@'.(int)$value);if(is_string($value)&&$value!=='')return new DateTimeImmutable($value,new DateTimeZone('UTC'));}catch(Throwable $e){}return null;
}
function nodenoHumanDate($value,?string $country=null):string {
 $region=nodenoDateRegion($country);$date=nodenoDateValue($value);if($date===null)return '';$civil=is_string($value)&&preg_match('/^\d{4}-\d{2}-\d{2}$/D',$value);if($civil&&$date->format('Y-m-d')!==$value)return '';$zone=$civil?'UTC':$region['timeZone'];$date=$date->setTimezone(new DateTimeZone($zone));
 return nodenoDateDigits($date->format($region['datePattern']),$region);
}
function nodenoHumanTime($value,?string $country=null):string {
 $region=nodenoDateRegion($country);$date=nodenoDateValue($value);if($date===null)return '';$date=$date->setTimezone(new DateTimeZone($region['timeZone']));
 if(is_array($region['timeParts'])){$out='';$hour=(int)$date->format('G');$cycle=$region['hourCycle'];$shown=$cycle==='h12'?($hour%12?:12):($cycle==='h11'?$hour%12:($cycle==='h24'&&$hour===0?24:$hour));foreach($region['timeParts']as $part){$type=$part['type'];$out.=$type==='hour'?str_pad((string)$shown,2,'0',STR_PAD_LEFT):($type==='minute'?$date->format('i'):($type==='dayPeriod'?$region['dayPeriods'][$hour<12?'am':'pm']:($part['value']??'')));}return nodenoDateDigits($out,$region);}
 return nodenoDateDigits($date->format($region['hour12']?'h:i A':'H:i'),$region);
}
function nodenoHumanDateTime($value,?string $country=null):string {$day=nodenoHumanDate($value,$country);return $day===''?'':$day.' '.nodenoHumanTime($value,$country);}
