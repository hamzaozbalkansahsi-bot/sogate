<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/StorePreferences.php
 * Açıklama   : Dil, gösterim para birimi ve doğrulanmış teslimat ülkesini ayrı tutar.
 */
declare(strict_types=1);
namespace Sexogate;
final class StorePreferences
{
    public function __construct(private Database $db,private Config $config){}
    public function currencies():array
    {$rows=$this->db->all("SELECT DISTINCT vp.currency FROM variant_prices vp JOIN variants v ON v.id=vp.variant_id AND v.active=true JOIN products p ON p.id=v.product_id AND p.status='published' WHERE vp.amount_minor>0 AND vp.valid_from<=CURRENT_TIMESTAMP(3) AND(vp.valid_until IS NULL OR vp.valid_until>CURRENT_TIMESTAMP(3)) AND(p.fixture=false OR ?=true)",[$this->config->local()?1:0]);return array_values(array_unique(array_merge(['TRY'],array_column($rows,'currency'))));}
    public function countries():array
    {
        $out=[];foreach($this->db->all('SELECT code,name,currency,review_generation FROM country_rules WHERE enabled=true AND(fixture=false OR ?=true)',[$this->config->local()?1:0]) as $r){try{(new CheckoutPolicy($this->db,$this->config))->country($r['code'],$r['currency']);(new CheckoutPolicy($this->db,$this->config))->profile($r['code']);$out[]=['code'=>$r['code'],'name'=>$r['name'],'currency'=>$r['currency']];}catch(RuleViolation){}}
        return $out;
    }
    public function read(array $saved):array
    {$currency=in_array($saved['currency']??'', ['TRY','EUR','USD','GBP'],true)?$saved['currency']:'TRY';$countries=$this->countries();$country=in_array($saved['country']??'',array_column($countries,'code'),true)?$saved['country']:($countries[0]['code']??'TR');return ['currency'=>$currency,'country'=>$country,'currencies'=>$this->currencies(),'countries'=>$countries];}
    public function update(array $saved,array $input):array
    {$current=$this->read($saved);$currency=$input['currency']??$current['currency'];$country=$input['country']??$current['country'];RuleViolation::ensure(is_string($currency)&&in_array($currency,$current['currencies'],true),'CURRENCY_UNAVAILABLE','Bu para birimi için güncel katalog fiyatı bulunmuyor.',400);RuleViolation::ensure(!array_key_exists('country',$input)||is_string($country)&&in_array($country,array_column($current['countries'],'code'),true),'COUNTRY_NOT_ALLOWED','Bu teslimat ülkesi satışa açık değil.',400);return ['currency'=>$currency,'country'=>$country];}
}
