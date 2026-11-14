<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ComplianceTest.php
 * Açıklama   : Sürümlü adres profili ve SKU/model/taşıyıcıya bağlı gerçek belge kabul sınırları.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Compliance,Markets,CheckoutPolicy,Catalog,Principal,RuleViolation};
final class ComplianceTest extends TestCase
{
    private function service(TestDatabase $f):Compliance{self::assertTrue(class_exists(Compliance::class),'PHP belge ve adres kuralı yönetimi eksik.');return new Compliance($f->db,$f->config);}
    private function fields(string $lineLabel='Adres'):array
    {return [['id'=>'fullName','label'=>['tr'=>'Ad soyad','en'=>'Full name'],'required'=>true,'minLength'=>2,'maxLength'=>120,'format'=>'text'],['id'=>'line1','label'=>['tr'=>$lineLabel,'en'=>'Address'],'required'=>true,'minLength'=>5,'maxLength'=>300,'format'=>'text'],['id'=>'city','label'=>['tr'=>'Şehir','en'=>'City'],'required'=>true,'minLength'=>2,'maxLength'=>100,'format'=>'text']];}
    public function testNewAddressVersionCannotChangeThePreviouslyApprovedFields():void
    {$f=new TestDatabase();$c=$this->service($f);$a=new Principal('admin','admin',true);(new Markets($f->db,$f->config))->country(['code'=>'DE','name'=>'Almanya','currency'=>'EUR','shippingMinor'=>2500],$a);$one=$c->address(['country'=>'DE','fields'=>$this->fields(),'reference'=>'TEST adres inceleme belgesi'],$a);try{(new CheckoutPolicy($f->db,$f->config))->profile('DE');self::fail('Taslak profil seçildi.');}catch(RuleViolation){}$c->approveAddress($one['id'],$a);$two=$c->address(['country'=>'DE','fields'=>$this->fields('Açık adres'),'reference'=>'TEST yeni adres inceleme belgesi'],$a);$c->approveAddress($two['id'],$a);self::assertSame($two['id'],(new CheckoutPolicy($f->db,$f->config))->profile('DE')['id']);$old=$f->db->one('SELECT status,fields FROM country_address_profiles WHERE id=?',[$one['id']]);self::assertSame('archived',$old['status']);self::assertSame('Adres',json_decode($old['fields'],true)[1]['label']['tr']);}
    public function testDocumentNeedsModelReviewAndRevocationBlocksCheckoutAgain():void
    {$s=new TestShop();$c=$this->service($s->f);$c->eligibility(['variantId'=>$s->variant,'country'=>'TR','requiredDocumentKind'=>'model-compliance','reference'=>'TEST SKU belge kapsamı'],$s->admin);try{(new Catalog($s->f->db,$s->f->config))->approve($s->f->db->one('SELECT product_id FROM variants WHERE id=?',[$s->variant])['product_id'],'TR',$s->admin);self::fail('Belgesiz ülke yayını açıldı.');}catch(RuleViolation){}$doc=$c->document(['variantId'=>$s->variant,'country'=>'TR','kind'=>'model-compliance','modelReference'=>'TEST-01','reference'=>'TEST üretici model belgesi','validFrom'=>gmdate('Y-m-d',time()-86400),'validUntil'=>gmdate('Y-m-d',time()+31536000)],$s->admin);$c->reviewDocument($doc['id'],'TEST yetkili belge incelemesi',$s->admin);(new Catalog($s->f->db,$s->f->config))->approve($s->f->db->one('SELECT product_id FROM variants WHERE id=?',[$s->variant])['product_id'],'TR',$s->admin);(new CheckoutPolicy($s->f->db,$s->f->config))->eligible($s->variant,'TR');$c->revokeDocument($doc['id'],'TEST belgenin iptal teyidi',$s->admin);$this->expectException(RuleViolation::class);(new CheckoutPolicy($s->f->db,$s->f->config))->eligible($s->variant,'TR');}
    public function testTurkishCarrierNameUsesTheSameNormalizationAsTheDatabaseRule():void
    {$s=new TestShop();$c=$this->service($s->f);$s->f->db->execute("UPDATE variants SET battery_type='TEST li-ion' WHERE id=?",[$s->variant]);$c->carrier(['variantId'=>$s->variant,'country'=>'TR','carrier'=>'İSTANBUL KARGO','accepted'=>true,'reference'=>'TEST pil taşıma kabul belgesi','validUntil'=>gmdate('c',time()+86400)],$s->admin);self::assertNotNull($s->f->db->one("SELECT variant_id FROM shipping_approvals WHERE variant_id=? AND carrier=LOWER('İSTANBUL KARGO') AND accepted=true",[$s->variant]));(new CheckoutPolicy($s->f->db,$s->f->config))->eligible($s->variant,'TR');$fulfillment=new Sexogate\Fulfillment($s->f->db,$s->f->config);$task=$fulfillment->prepare($s->order['orderId'],[['variantId'=>$s->variant,'quantity'=>2]],bin2hex(random_bytes(16)),$s->admin);foreach(['pick','pack'] as $phase)$fulfillment->scan($task['id'],'TEST-01',$phase,2,bin2hex(random_bytes(16)),$s->admin);self::assertSame('shipped',$fulfillment->ship($task['id'],'İSTANBUL KARGO','TEST-UTF8-TRACK',bin2hex(random_bytes(16)),$s->admin)['status']);}
    public function testWarehouseCannotApproveAProductDocument():void
    {$f=new TestDatabase();$c=$this->service($f);$this->expectException(RuleViolation::class);$c->reviewDocument('none','TEST inceleme',new Principal('warehouse','warehouse',true));}
}
