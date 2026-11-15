<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';

function nodenoMarketForCountry(?string $value):array {
 $countries='AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW';
 $country=is_string($value)&&in_array($value,explode(' ',$countries),true)?$value:null;
 return ['country'=>$country,'international'=>$country!==null&&$country!=='TR'];
}
function nodenoInitialLocale(mixed $requested,mixed $stored,?string $country):string {
 foreach([$requested,$stored] as $value)if(in_array($value,NODENO_STORE_LOCALES,true))return $value;
 $country=nodenoMarketForCountry($country)['country'];
 if($country===null||$country==='TR')return 'tr';
 $native=['DE'=>'de','AT'=>'de','CH'=>'de','LI'=>'de','AZ'=>'az','KZ'=>'kk','KG'=>'ky','TM'=>'tk','UZ'=>'uz','IR'=>'fa'];if(isset($native[$country]))return $native[$country];
 if(in_array($country,['RU','BY','KZ','KG'],true))return 'ru';
 return in_array($country,['AE','BH','DJ','DZ','EG','IQ','JO','KM','KW','LB','LY','MA','MR','OM','PS','QA','SA','SD','SO','SY','TN','YE'],true)?'ar':'en';
}
function nodenoIpCountry(string $ip,string $root):?string {
 // No X-Forwarded-For / CF-IPCountry trust: this hosting currently has no trusted proxy configuration.
 if(str_starts_with(strtolower($ip),'::ffff:'))$ip=substr($ip,7);
 if(!filter_var($ip,FILTER_VALIDATE_IP,FILTER_FLAG_NO_PRIV_RANGE|FILTER_FLAG_NO_RES_RANGE))return null;
 $packed=inet_pton($ip);if($packed===false)return null;
 $width=strlen($packed);$recordSize=2*$width+2;$path=$root.'/geo-v'.($width===4?'4':'6').'.bin';
 $file=@fopen($path,'rb');if($file===false)return null;
 try{
  $stat=fstat($file);$size=$stat['size']??0;if($size===0||$size%$recordSize!==0)return null;
  $lo=0;$hi=intdiv($size,$recordSize)-1;
  while($lo<=$hi){$mid=intdiv($lo+$hi,2);if(fseek($file,$mid*$recordSize)!==0)return null;$row=fread($file,$recordSize);if(strlen($row)!==$recordSize)return null;
   if(strcmp($packed,substr($row,0,$width))<0)$hi=$mid-1;
   elseif(strcmp($packed,substr($row,$width,$width))>0)$lo=$mid+1;
   else return nodenoMarketForCountry(substr($row,-2))['country'];
  }
  return null;
 }catch(Throwable $error){return null;}
 finally{fclose($file);}
}
function nodenoVisitorMarket(array $server,string $root):array {
 $ip=$server['REMOTE_ADDR']??'';
 return nodenoMarketForCountry(is_string($ip)?nodenoIpCountry($ip,$root):null);
}
