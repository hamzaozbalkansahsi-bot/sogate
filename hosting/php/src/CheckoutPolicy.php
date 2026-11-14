<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/CheckoutPolicy.php
 * Açıklama   : Ülke, ürün belgesi, vergi, adres ve sürümlü hukuk kabul kapıları.
 */
declare(strict_types=1);
namespace Sexogate;
final class CheckoutPolicy
{
    public function __construct(private Database $db,private Config $config){}
    public function live():void
    {
        if($this->config->local())return;
        RuleViolation::ensure($this->config->flag('live_sales')&&$this->config->get('payment_provider')==='stripe','LIVE_SALES_CLOSED','Canlı satış hazırlığı tamamlanmadı.',503);
        $values=[];foreach($this->db->all('SELECT `key`,value FROM settings') as $row)$values[$row['key']]=json_decode($row['value'],true);
        foreach(['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone','seller.bankAccount'] as $key)RuleViolation::ensure(is_string($values[$key]??null)&&trim($values[$key])!=='','SELLER_NOT_CONFIGURED','Hukuki satıcı bilgileri tamamlanmadı.',503);
        foreach(['launch.providerApproved','launch.backupVerified','launch.securityReviewed','launch.legalApproved','launch.catalogVerified'] as $key)RuleViolation::ensure(($values[$key]??null)===true,'LAUNCH_NOT_APPROVED','Canlı satış onayları tamamlanmadı.',503);
    }
    public function country(string $code,string $currency):array
    {
        RuleViolation::ensure((bool)preg_match('/\A[A-Z]{2}\z/',$code)&&in_array($currency,['TRY','EUR','USD','GBP'],true),'INVALID_MARKET','Ülke veya para birimi geçersiz.',400);
        $r=$this->db->one('SELECT * FROM country_rules WHERE code=? FOR SHARE',[$code]);$ok=(bool)$r;
        foreach(['enabled','product_approved','age_approved','payment_approved','shipping_approved','tax_approved','legal_approved'] as $key)$ok=$ok&&!empty($r[$key]);
        RuleViolation::ensure($ok,'COUNTRY_NOT_APPROVED','Bu teslimat ülkesi için satış henüz açık değil.');RuleViolation::ensure($r['shipping_minor']!==null&&$r['currency']===$currency,'SHIPPING_NOT_CONFIGURED','Teslimat ücreti veya tahsilat para birimi yapılandırılmadı.');RuleViolation::ensure(!(bool)$r['fixture']||$this->config->local(),'FIXTURE_NOT_ALLOWED','Örnek ülke kuralıyla gerçek satış yapılamaz.',503);return $r;
    }
    public function eligible(string $id,string $country):void
    {
        $r=$this->db->one('SELECT * FROM product_eligibility WHERE variant_id=? AND country=? FOR SHARE',[$id,$country]);RuleViolation::ensure($r&&(bool)$r['approved']&&$r['approved_by'],'PRODUCT_NOT_ELIGIBLE','Stok kodunun ülke uygunluğu onaylanmalıdır.');
        if($r['required_document_kind'])RuleViolation::ensure($this->db->one('SELECT id FROM product_documents WHERE variant_id=? AND country=? AND kind=? AND reviewed=true AND reviewed_by IS NOT NULL AND CHAR_LENGTH(TRIM(reference))>0 AND valid_from<=CURRENT_DATE AND(valid_until IS NULL OR valid_until>=CURRENT_DATE) FOR SHARE',[$id,$country,$r['required_document_kind']]),'DOCUMENT_REQUIRED','Bu stok kodu ve ülke için geçerli belge gerekir.');
        $v=$this->db->one('SELECT battery_type,liquid FROM variants WHERE id=?',[$id]);
        if(($v['battery_type']??'')!==''||!empty($v['liquid']))RuleViolation::ensure($this->db->one('SELECT variant_id FROM shipping_approvals WHERE variant_id=? AND country=? AND accepted=true AND(valid_until IS NULL OR valid_until>CURRENT_TIMESTAMP(3)) FOR SHARE',[$id,$country]),'SHIPPING_NOT_APPROVED','Bu ürünün taşıma kabulü doğrulanmadı.');
    }
    public function tax(string $country,string $class):array
    {
        $rows=$this->db->all("SELECT t.*,s.value source FROM tax_rules t LEFT JOIN settings s ON s.`key`=CONCAT('tax.source.',t.id) WHERE t.country=? AND t.product_class=? AND t.valid_from<=CURRENT_TIMESTAMP(3) AND(t.valid_until IS NULL OR t.valid_until>CURRENT_TIMESTAMP(3)) FOR SHARE",[$country,$class]);
        RuleViolation::ensure(count($rows)===1,'PRODUCT_TAX_NOT_CONFIGURED','Bu ürün sınıfı için tek ve yürürlükte vergi kuralı gerekir.');$r=$rows[0];$source=$r['source']===null?null:json_decode($r['source'],true);
        RuleViolation::ensure(!(bool)$r['fixture']||$this->config->local(),'FIXTURE_NOT_ALLOWED','Örnek vergiyle gerçek satış yapılamaz.',503);RuleViolation::ensure($this->config->local()||(is_string($source)&&trim($source)!==''),'TAX_SOURCE_REQUIRED','Vergi kuralının onay kaynağı eksik.');return ['id'=>$r['id'],'productClass'=>$r['product_class'],'rateBps'=>(int)$r['rate_bps'],'validFrom'=>$r['valid_from'],'validUntil'=>$r['valid_until'],'source'=>$source,'fixture'=>(bool)$r['fixture']];
    }
    public function shippingTax(array $country):array
    {
        $r=$this->db->all('SELECT id,rate_bps,reference FROM shipping_tax_rules WHERE country=? AND approved=true AND valid_from<=CURRENT_TIMESTAMP(3) AND(valid_until IS NULL OR valid_until>CURRENT_TIMESTAMP(3)) FOR SHARE',[$country['code']]);
        if(count($r)===1)return ['id'=>$r[0]['id'],'rateBps'=>(int)$r[0]['rate_bps'],'source'=>$r[0]['reference']];
        RuleViolation::ensure(!$r&&(bool)$country['fixture']&&$this->config->local(),'SHIPPING_TAX_NOT_CONFIGURED','Kargo vergi kuralı onaylanmadı.');return ['id'=>null,'rateBps'=>0,'source'=>'Yalnız izole test kuralı'];
    }
    public function profile(string $country):array
    {
        $p=$this->db->one("SELECT id,country,version,fields FROM country_address_profiles WHERE country=? AND status='approved' AND approved_by IS NOT NULL AND(fixture=false OR ?=true) FOR SHARE",[$country,$this->config->local()?1:0]);RuleViolation::ensure($p,'ADDRESS_PROFILE_REQUIRED','Bu ülkenin adres kuralları hazırlanmadı.');$p['fields']=json_decode($p['fields'],true,512,JSON_THROW_ON_ERROR);return $p;
    }
    public function address(array $input,array $profile):array
    {
        $allowed=['fullName','phone','line1','city','region','district','postalCode'];$values=[];$configured=array_column($profile['fields'],'id');
        foreach($allowed as $id){$value=$input[$id]??'';RuleViolation::ensure(is_string($value),'INVALID_ADDRESS','Adres alanlarını kontrol edin.',400);$value=trim($value);if(!in_array($id,$configured,true))RuleViolation::ensure($value==='','UNEXPECTED_ADDRESS_FIELD','Ülkeye ait olmayan adres alanı gönderildi.',400);}
        foreach($profile['fields'] as $field){$id=$field['id'];RuleViolation::ensure(in_array($id,$allowed,true),'ADDRESS_PROFILE_INVALID','Adres kuralı geçersiz.',503);$v=trim($input[$id]??'');RuleViolation::ensure($v!==''||!$field['required'],'INVALID_ADDRESS','Zorunlu adres alanlarını doldurun.',400);if($v==='')continue;
            $controls=$id==='line1'?'/[\x00-\x09\x0b\x0c\x0e-\x1f\x7f-\x9f]/u':'/[\x00-\x1f\x7f-\x9f]/u';RuleViolation::ensure(mb_strlen($v)>=$field['minLength']&&mb_strlen($v)<=$field['maxLength']&&!preg_match($controls,$v),'INVALID_ADDRESS','Adres alanının uzunluğu veya biçimi geçersiz.',400);
            if($field['format']==='digits')RuleViolation::ensure((bool)preg_match('/\A\p{Nd}+\z/u',$v),'INVALID_ADDRESS','Sayısal adres alanını kontrol edin.',400);if($field['format']==='alphanumeric')RuleViolation::ensure((bool)preg_match('/\A[\p{L}\p{N} -]+\z/u',$v),'INVALID_ADDRESS','Adres alanını kontrol edin.',400);$values[$id]=$v;
        }return $values+['country'=>$profile['country'],'profileVersion'=>(int)$profile['version']];
    }
    public function agreements(string $locale):array
    {
        RuleViolation::ensure(in_array($locale,['tr','en'],true),'INVALID_LOCALE','Dil desteklenmiyor.',400);$rows=$this->db->all("SELECT * FROM legal_documents WHERE kind IN('privacy','terms') AND locale=? AND status='effective' AND effective_at<=CURRENT_TIMESTAMP(3) ORDER BY kind FOR SHARE",[$locale]);RuleViolation::ensure(count($rows)===2&&count(array_unique(array_column($rows,'kind')))===2,'LEGAL_DOCUMENTS_REQUIRED','Geçerli aydınlatma ve satış koşulları hazırlanmadı.');
        foreach($rows as $r)RuleViolation::ensure((!(bool)$r['fixture']||$this->config->local())&&$r['approved_by']&&hash_equals($r['body_hash'],hash('sha256',$r['body'])),'LEGAL_NOT_APPROVED','Hukuk metni onayı veya bütünlüğü doğrulanamadı.');return $rows;
    }
}
