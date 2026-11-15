<?php
declare(strict_types=1);
require dirname(__DIR__,2).'/hosting/visitor-market.php';
function check(bool $ok,string $label):void{if(!$ok)throw new RuntimeException($label);}
$root=sys_get_temp_dir().'/nodeno-geo-'.bin2hex(random_bytes(8));mkdir($root);
try{
 file_put_contents($root.'/geo-v4.bin',inet_pton('8.8.8.0').inet_pton('8.8.8.255').'US'.inet_pton('88.255.0.0').inet_pton('88.255.255.255').'TR');
 file_put_contents($root.'/geo-v6.bin',inet_pton('2001:4860::').inet_pton('2001:4860:ffff:ffff:ffff:ffff:ffff:ffff').'US');
 foreach(['8.8.8.0','8.8.8.8','8.8.8.255','::ffff:8.8.8.8','2001:4860::8888'] as $ip)check(nodenoIpCountry($ip,$root)==='US','US range '.$ip);
 check(nodenoIpCountry('88.255.3.2',$root)==='TR','Turkey');
 foreach(['8.8.7.255','8.8.9.0','127.0.0.1','::1','10.0.0.1','fc00::1','garbage'] as $ip)check(nodenoIpCountry($ip,$root)===null,'unknown/reserved');
 $server=['REMOTE_ADDR'=>'88.255.3.2','HTTP_CF_IPCOUNTRY'=>'DE','HTTP_X_FORWARDED_FOR'=>'8.8.8.8'];
 check(nodenoVisitorMarket($server,$root)['country']==='TR','ignore forged proxy headers');
 check(nodenoVisitorMarket(['HTTP_CF_IPCOUNTRY'=>'DE'],$root)['country']===null,'missing peer');
 check(nodenoIpCountry('8.8.8.8',$root.'/missing')===null,'missing DB fails closed');
 file_put_contents($root.'/geo-v4.bin','truncated');
 check(nodenoIpCountry('8.8.8.8',$root)===null,'damaged DB fails closed');
 $rows=[];
 foreach(['TR','DE','GB','AZ','TM','IR','IQ','SY','KZ','KG','RU',null,'ZZ'] as $country){foreach([[null,null],['ar','tr'],['de','ru']] as [$requested,$stored]){$input=compact('requested','stored','country');$rows[]=['country'=>$country,'market'=>nodenoMarketForCountry($country),'input'=>$input,'locale'=>nodenoInitialLocale($requested,$stored,$country)];}}
 echo json_encode($rows,JSON_THROW_ON_ERROR);
}finally{foreach(glob($root.'/*') as $file)unlink($file);rmdir($root);}
