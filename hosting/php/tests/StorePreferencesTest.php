<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/StorePreferencesTest.php
 * Açıklama   : Para gösterimi, ülke izni ve tahsilat kuralının karışmamasını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{StorePreferences,Fixtures,Principal,Markets,Catalog,RuleViolation};
final class StorePreferencesTest extends TestCase
{
    public function testDisplayPreferenceDoesNotRequireOpeningDeliverySales():void
    {$f=new TestDatabase();$s=new StorePreferences($f->db,$f->config);self::assertSame('TRY',$s->update([],['currency'=>'TRY'])['currency']);}
    public function testDisplayPriceRequiresActualPriceListAndCountryRequiresReview():void
    {$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$s=new StorePreferences($f->db,$f->config);self::assertSame(['TRY'],$s->currencies());$id=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];(new Markets($f->db,$f->config))->price(['variantId'=>$id,'currency'=>'EUR','amountMinor'=>800],new Principal('admin','admin',true));$pref=$s->update([],['currency'=>'EUR','country'=>'TR']);self::assertSame('EUR',$pref['currency']);$p=(new Catalog($f->db,$f->config))->product('saten-bag-detayi','EUR');self::assertSame(800,$p['variants'][0]['display_price_minor']);self::assertSame(14900,$p['variants'][0]['price_minor']);$this->expectException(RuleViolation::class);$s->update($pref,['country'=>'DE']);}
    public function testHomeUsesTheSelectedDisplayPriceWithoutChangingChargeCurrency():void
    {$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$id=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];(new Markets($f->db,$f->config))->price(['variantId'=>$id,'currency'=>'EUR','amountMinor'=>800],new Principal('admin','admin',true));$session=new Symfony\Component\HttpFoundation\Session\Session(new Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage());$session->set('store_preferences',['currency'=>'EUR','country'=>'TR']);$r=(new Sexogate\Kernel($f->db,$f->config,$session))->handle(Symfony\Component\HttpFoundation\Request::create('/test/'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString(Sexogate\Money::format(800,'EUR','tr'),$r->getContent());self::assertStringNotContainsString(Sexogate\Money::format(14900,'TRY','tr'),$r->getContent());self::assertSame('TRY',$f->db->one('SELECT currency FROM variants WHERE id=?',[$id])['currency']);}
}
