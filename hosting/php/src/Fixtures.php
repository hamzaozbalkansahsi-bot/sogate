<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Fixtures.php
 * Açıklama   : Yalnız ayrı test DB'sinde açıkça test sayılan alışveriş kabul kurallarını hazırlar.
 */
declare(strict_types=1);
namespace Sexogate;
final class Fixtures
{
    public function __construct(private Database $db,private Config $config){}
    public function policies():void
    {
        $name=$this->db->one('SELECT DATABASE() name')['name'];RuleViolation::ensure($this->config->local()&&str_ends_with($name,'_test'),'ISOLATED_TEST_REQUIRED','Örnek kurallar yalnız ayrı test ortamında kullanılabilir.',503);
        $old=$this->db->one("SELECT fixture FROM country_rules WHERE code='TR'");RuleViolation::ensure(!$old||(bool)$old['fixture'],'REAL_COUNTRY_PRESENT','Gerçek ülke ayarları örnek kurallarla değiştirilemez.');
        $this->db->execute("INSERT INTO categories(slug,name,name_en) VALUES('ic-giyim','İç Giyim','Lingerie') ON DUPLICATE KEY UPDATE slug=slug");
        $this->db->execute("INSERT INTO warehouses(id,name) VALUES('main','Ana depo') ON DUPLICATE KEY UPDATE id=id");
        $this->db->execute("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES('TR','Türkiye',true,true,true,true,true,true,true,500,'TRY',true) ON DUPLICATE KEY UPDATE code=code");
        $fields=[];foreach([['fullName','Ad soyad','Full name',2,120],['phone','Telefon','Phone',7,30],['line1','Adres','Address',5,300],['city','Şehir','City',2,100],['postalCode','Posta kodu','Postal code',3,15]] as [$id,$tr,$en,$min,$max])$fields[]=['id'=>$id,'label'=>['tr'=>$tr,'en'=>$en],'required'=>true,'minLength'=>$min,'maxLength'=>$max,'format'=>'text'];
        if(!$this->db->one("SELECT id FROM country_address_profiles WHERE country='TR'"))$this->db->execute("INSERT INTO country_address_profiles(country,version,fields,status,fixture,reference,created_by,approved_by,approved_at) VALUES('TR',1,?,'approved',true,'LOCAL-TEST-ADDRESS','fixture-admin','fixture-admin',CURRENT_TIMESTAMP(3))",[$this->config->json($fields)]);
        if(!$this->db->one("SELECT id FROM tax_rules WHERE country='TR'"))$this->db->execute("INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,fixture) VALUES('TR','*',2000,'2020-01-01',true)");
        foreach(['tr','en'] as $locale)foreach(['privacy','terms'] as $kind){
            if($this->db->one('SELECT id FROM legal_documents WHERE kind=? AND locale=?',[$kind,$locale]))continue;
            $body=$locale==='tr'?'Bu belge yalnız özel test ortamındaki alışveriş akışının doğrulanması içindir. Canlı satış için işletme bilgileri ve hukuk onayı gerekir.':'This document is only for a private test purchase. Live sales require seller details and legal approval.';
            $this->db->execute("INSERT INTO legal_documents(kind,locale,version,title,body,body_hash,status,fixture,seller_snapshot,approved_by,effective_at) VALUES(?,?,1,?,?,?,'effective',true,JSON_OBJECT('fixture',true),'fixture-admin','2020-01-01')",[$kind,$locale,$kind==='privacy'?($locale==='tr'?'Test aydınlatma metni':'Test privacy notice'):($locale==='tr'?'Test satış koşulları':'Test terms'),$body,hash('sha256',$body)]);
        }
    }
    public function catalog(Principal $admin):void
    {
        $name=$this->db->one('SELECT DATABASE() name')['name'];RuleViolation::ensure($this->config->local()&&str_ends_with($name,'_test'),'ISOLATED_TEST_REQUIRED','Örnek katalog yalnız ayrı test ortamında kullanılabilir.',503);
        $catalog=new Catalog($this->db,$this->config);$stock=new Inventory($this->db,$this->config);
        foreach([['Saten Bağ Detayı','Satin Tie Detail','saten-bag-detayi','01',14900],['Bordo Göz Bandı','Burgundy Eye Mask','bordo-goz-bandi','02',18900],['Dantel Bileklik','Lace Wrist Accessory','dantel-bileklik','03',12900]] as [$tr,$en,$slug,$image,$price]){
            if($this->db->one('SELECT id FROM products WHERE slug=?',[$slug]))continue;
            $p=$catalog->create(['name'=>$tr,'nameEn'=>$en,'slug'=>$slug,'category'=>'ic-giyim','sku'=>'TEST-'.strtoupper($image),'variantName'=>'Bordo','variantNameEn'=>'Burgundy','priceMinor'=>$price,'costMinor'=>0,'image'=>'/media/atelier-'.$image.'.svg','fixture'=>true,'description'=>'Bordo tonlarında aksesuar. Malzeme, ölçü ve bakım bilgileri gerçek ürün kaydıyla tamamlanır.','descriptionEn'=>'Burgundy accessory. Material, measurements and care details require the actual product record.'],$admin);
            $stock->receive($p['variantId'],10,'İzole test mal kabulü','fixture-receipt-'.$p['variantId'],$admin);$catalog->approve($p['id'],'TR',$admin);
        }
    }
}
