<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/SupplierApiHttp.php
 * Açıklama   : Sabit resmî API ucuna TLS doğrulamalı ve DNS sabitli sınırlı katalog GET'i.
 */
declare(strict_types=1);
namespace Sexogate;
use Symfony\Component\HttpFoundation\IpUtils;
final class SupplierApiHttp
{
    public static function publicIp(string $ip):bool
    {return filter_var($ip,FILTER_VALIDATE_IP,FILTER_FLAG_NO_PRIV_RANGE|FILTER_FLAG_NO_RES_RANGE)!==false&&!IpUtils::checkIp($ip,['0.0.0.0/8','100.64.0.0/10','192.0.0.0/24','192.0.2.0/24','198.18.0.0/15','198.51.100.0/24','203.0.113.0/24','224.0.0.0/4','240.0.0.0/4','::/128','::ffff:0:0/96','64:ff9b::/96','64:ff9b:1::/48','100::/64','2001:db8::/32','ff00::/8']);}
    public static function endpoint(string $resource,int $page):string
    {RuleViolation::ensure(in_array($resource,['products','categories'],true)&&$page>=1&&$page<=200,'SOURCE_API_INVALID_REQUEST','API sayfasını kontrol edin.',400);$query=['per_page'=>100,'page'=>$page,'orderby'=>$resource==='products'?'id':'name','order'=>'asc'];if($resource==='products')$query['stock_status']='instock,outofstock,onbackorder';else $query['hide_empty']='false';return 'https://www.xshopum.com/wp-json/wc/store/v1/products'.($resource==='categories'?'/categories':'').'?'.http_build_query($query,'','&',PHP_QUERY_RFC3986);}
    public function fetch(string $resource,int $page):array
    {
        $url=self::endpoint($resource,$page);RuleViolation::ensure(extension_loaded('curl'),'SOURCE_API_CURL_REQUIRED','Sunucuda güvenli HTTP istemcisi etkin değil.',503);$host='www.xshopum.com';$records=@dns_get_record($host,DNS_A|DNS_AAAA);$ips=[];foreach($records?:[] as $record)if(isset($record['ip'])||isset($record['ipv6']))$ips[]=$record['ip']??$record['ipv6'];RuleViolation::ensure($ips,'SOURCE_API_DNS','Tedarikçi adresi çözümlenemedi.',503);foreach($ips as $ip)RuleViolation::ensure(self::publicIp($ip),'SOURCE_API_PRIVATE_NETWORK','Tedarikçi ağ adresi uygun değil.',503);usort($ips,fn($a,$b)=>str_contains($a,':')<=>str_contains($b,':'));$pin=str_contains($ips[0],':')?'['.$ips[0].']':$ips[0];$body='';$total=null;$tooLarge=false;
        $curl=curl_init($url);curl_setopt_array($curl,[CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_TIMEOUT=>15,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_PROTOCOLS=>CURLPROTO_HTTPS,CURLOPT_PROXY=>'',CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_RESOLVE=>[$host.':443:'.$pin],CURLOPT_USERAGENT=>'SEXOGATE-Catalog-Review/1.0',CURLOPT_HTTPHEADER=>['Accept: application/json'],CURLOPT_ENCODING=>'',CURLOPT_HEADERFUNCTION=>static function($handle,$line)use(&$total){if(preg_match('/\AX-WP-Total:\s*(\d+)\s*\z/i',trim($line),$m))$total=(int)$m[1];return strlen($line);},CURLOPT_WRITEFUNCTION=>static function($handle,$chunk)use(&$body,&$tooLarge){if(strlen($body)+strlen($chunk)>8388608){$tooLarge=true;return 0;}$body.=$chunk;return strlen($chunk);}]);
        try{$ok=curl_exec($curl);$errno=curl_errno($curl);$status=(int)curl_getinfo($curl,CURLINFO_RESPONSE_CODE);}finally{curl_close($curl);}RuleViolation::ensure(!$tooLarge,'SOURCE_API_SIZE','API yanıtı boyut sınırını aşıyor.',503);RuleViolation::ensure($ok!==false,$errno===CURLE_OPERATION_TIMEDOUT?'SOURCE_API_TIMEOUT':'SOURCE_API_NETWORK','Tedarikçi bağlantısı tamamlanamadı.',503);return ['status'=>$status,'total'=>$total,'body'=>$body];
    }
}
