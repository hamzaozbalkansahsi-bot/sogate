<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/MarketsTest.php
 * Açıklama   : Süreli ülke onayları, çakışmayan vergi, fiyat snapshot'ı ve gerçek kaynaklı kur kabulü.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Markets,Principal,CheckoutPolicy,RuleViolation};
final class MarketsTest extends TestCase
{
    public function testForeignWarehouseCheckoutIsBlockedUntilCostCurrencySnapshotsAreImplemented():void
    {$shop=new TestShop();$f=$shop->f;$item=$f->db->one('SELECT * FROM variants WHERE id=?',[$shop->variant]);$item['quantity']=1;$country=$f->db->one("SELECT * FROM country_rules WHERE code='TR'");$country['currency']='EUR';try{(new \Sexogate\Inventory($f->db,$f->config))->plan([$item],$country,false);self::fail('TRY depo maliyeti EUR maliyet gibi kullanıldı.');}catch(RuleViolation $e){self::assertSame('WAREHOUSE_CURRENCY_UNCONFIGURED',$e->rule);}}
    private function service(TestDatabase $f):Markets{self::assertTrue(class_exists(Markets::class),'PHP ülke ve fiyat yönetimi eksik.');return new Markets($f->db,$f->config);}
    private function country(Markets $s,Principal $a):void{$s->country(['code'=>'DE','name'=>'Almanya','currency'=>'EUR','shippingMinor'=>2500,'ageMethod'=>'declaration','timeZone'=>'Europe/Berlin','deliveryTerm'=>'DAP','restrictions'=>'Taşıma ve ürün kabulüne tabidir.'],$a);}
    public function testCountryNeedsEveryReviewedGateAndAnExpiredApprovalClosesCheckout():void
    {
        $f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);$this->country($s,$a);$p=new CheckoutPolicy($f->db,$f->config);
        try{$s->enable('DE',true,$a);self::fail('Onaysız ülke açıldı.');}catch(RuleViolation){}
        foreach(['product','age','payment','shipping','tax','legal'] as $gate)$s->review('DE',$gate,true,'TEST ülke inceleme belgesi '.$gate,gmdate('c',time()+86400),$a);
        $s->enable('DE',true,$a);self::assertSame('EUR',$p->country('DE','EUR')['currency']);
        $f->db->execute("UPDATE market_approvals SET valid_until=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE) WHERE country='DE' AND gate='age'");
        $this->expectException(RuleViolation::class);$p->country('DE','EUR');
    }
    public function testTaxIntervalsCannotOverlapAndSourceIsPreserved():void
    {
        $f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);$this->country($s,$a);
        $id=$s->tax(['kind'=>'goods','country'=>'DE','productClass'=>'textile','rateBps'=>1900,'validFrom'=>gmdate('c',time()-86400),'validUntil'=>gmdate('c',time()+86400),'reference'=>'TEST resmî vergi inceleme kaynağı'],$a)['id'];
        self::assertSame('TEST resmî vergi inceleme kaynağı',(new CheckoutPolicy($f->db,$f->config))->tax('DE','textile')['source']);
        try{$s->tax(['kind'=>'goods','country'=>'DE','productClass'=>'textile','rateBps'=>2000,'validFrom'=>gmdate('c',time()-3600),'validUntil'=>gmdate('c',time()+172800),'reference'=>'TEST çakışan dönem'],$a);self::fail('Vergi dönemi çakıştı.');}catch(RuleViolation){}
        self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM tax_rules')['n']);self::assertSame($id,(new CheckoutPolicy($f->db,$f->config))->tax('DE','textile')['id']);
    }
    public function testNewPriceListsCannotChangeExistingOrderAmounts():void
    {
        $shop=new TestShop();$s=$this->service($shop->f);$s->price(['variantId'=>$shop->variant,'currency'=>'TRY','amountMinor'=>17900],$shop->admin);$s->price(['variantId'=>$shop->variant,'currency'=>'EUR','amountMinor'=>1999],$shop->admin);
        self::assertSame(14900,(int)$shop->f->db->one('SELECT unit_minor FROM order_items')['unit_minor']);self::assertSame(17900,(int)$shop->f->db->one('SELECT price_minor FROM variants WHERE id=?',[$shop->variant])['price_minor']);self::assertSame(1999,(int)$shop->f->db->one("SELECT amount_minor FROM variant_prices WHERE variant_id=? AND currency='EUR'",[$shop->variant])['amount_minor']);
    }
    public function testCurrencyConversionRequiresFreshSourceAndUsesIntegerRounding():void
    {
        $f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);
        try{$s->convert(10000,'TRY','USD');self::fail('Kur uyduruldu.');}catch(RuleViolation){}
        $s->rate(['base'=>'TRY','quote'=>'USD','rate'=>'0,029999','bufferBps'=>100,'rounding'=>'nearest','observedAt'=>gmdate('c',time()-1),'validUntil'=>gmdate('c',time()+3600),'reference'=>'TEST doğrulanmış kur kaynağı'],$a);
        $result=$s->convert(10000,'TRY','USD');self::assertSame(303,$result['amountMinor']);self::assertSame('TEST doğrulanmış kur kaynağı',$result['source']);
        $f->db->execute('UPDATE exchange_rates SET observed_at=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 2 HOUR),valid_until=DATE_SUB(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE)');$this->expectException(RuleViolation::class);$s->convert(10000,'TRY','USD');
    }
    public function testWarehouseCannotChangeMarketsOrPrices():void
    {$f=new TestDatabase();$s=$this->service($f);$this->expectException(RuleViolation::class);$this->country($s,new Principal('warehouse','warehouse',true));}
    public function testChangingCountryTermsInvalidatesEarlierReviewGeneration():void
    {$f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);$this->country($s,$a);foreach(['product','age','payment','shipping','tax','legal'] as $gate)$s->review('DE',$gate,true,'TEST ülke onayı '.$gate,gmdate('c',time()+86400),$a);$s->enable('DE',true,$a);$s->country(['code'=>'DE','name'=>'Almanya','currency'=>'EUR','shippingMinor'=>3500,'deliveryTerm'=>'DAP','restrictions'=>'Yeni tarife'],$a);self::assertSame(1,(int)$f->db->one("SELECT review_generation FROM country_rules WHERE code='DE'")['review_generation']);self::assertSame(6,(int)$f->db->one('SELECT COUNT(*) n FROM market_approvals')['n']);$this->expectException(RuleViolation::class);$s->enable('DE',true,$a);}
    public function testTaxReplacementCannotExtendAnAlreadyClosedRule():void
    {$f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);$this->country($s,$a);$old=$s->tax(['kind'=>'goods','country'=>'DE','productClass'=>'textile','rateBps'=>1900,'validFrom'=>gmdate('c',time()-259200),'validUntil'=>gmdate('c',time()-172800),'reference'=>'TEST kapanmış vergi dönemi'],$a);$this->expectException(RuleViolation::class);$s->tax(['kind'=>'goods','country'=>'DE','productClass'=>'textile','rateBps'=>1900,'validFrom'=>gmdate('c',time()-3600),'validUntil'=>gmdate('c',time()+86400),'replaceId'=>$old['id'],'reference'=>'TEST yeni vergi dönemi'],$a);}
    public function testProviderBasedAgeRuleCannotBeSatisfiedByTheEntryNotice():void
    {$f=new TestDatabase();$s=$this->service($f);$a=new Principal('admin','admin',true);$s->country(['code'=>'DE','name'=>'İzole ülke kuralı','currency'=>'EUR','shippingMinor'=>2500,'ageMethod'=>'provider_required','timeZone'=>'Europe/Berlin'],$a);foreach(['product','age','payment','shipping','tax','legal'] as $gate)$s->review('DE',$gate,true,'TEST ülke inceleme belgesi '.$gate,gmdate('c',time()+86400),$a);$s->enable('DE',true,$a);$this->expectException(RuleViolation::class);(new CheckoutPolicy($f->db,$f->config))->country('DE','EUR');}
}
