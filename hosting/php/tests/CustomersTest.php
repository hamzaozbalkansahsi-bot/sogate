<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CustomersTest.php
 * Açıklama   : Adres/favori sahipliği, deterministik sepet birleşmesi ve bağımsız izin kayıtları.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Customers,Fixtures,Principal,Cart,RuleViolation};
final class CustomersTest extends TestCase
{
    private function setupStore():TestDatabase
    {$f=new TestDatabase();$fixtures=new Fixtures($f->db,$f->config);$fixtures->policies();$fixtures->catalog(new Principal('fixture-admin','admin',true));foreach(['a','b'] as $u)$f->db->execute('INSERT INTO `user`(id,name,email,emailVerified,role) VALUES(?,?,?,true,?)',[$u,'Müşteri '.$u,$u.'@example.invalid','customer']);return $f;}
    public function testAddressesKeepTurkishAndDenyOtherOwners():void
    {$f=$this->setupStore();self::assertTrue(class_exists(Customers::class),'Müşteri PHP modülü eksik.');$c=new Customers($f->db,$f->config);$a=$c->saveAddress('a',['label'=>'İş','country'=>'TR','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000']);self::assertSame('İstanbul',$c->addresses('a')[0]['fields']['city']);self::assertSame([],$c->addresses('b'));$this->expectException(RuleViolation::class);$c->deleteAddress('b',$a['id']);}
    public function testMergingTwoGuestCartsIntoOneAccountAddsEachQuantityOnce():void
    {$f=$this->setupStore();self::assertTrue(class_exists(Customers::class),'Müşteri PHP modülü eksik.');$c=new Customers($f->db,$f->config);$cart=new Cart($f->db,$f->config);$v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$a=bin2hex(random_bytes(32));$b=bin2hex(random_bytes(32));$one=bin2hex(random_bytes(32));$two=bin2hex(random_bytes(32));$cart->set($a,$v,1);$cart->set($b,$v,2);$c->mergeCart($a,$one,'a');$c->mergeCart($b,$two,'a');self::assertSame(3,$cart->get($two,'TRY','a')['items'][0]['quantity']);self::assertSame([], $cart->get($b)['items']);try{$cart->get($two,'TRY','b');self::fail('Diğer kullanıcı sepete erişti.');}catch(RuleViolation $e){self::assertSame(404,$e->status);}}
    public function testFavoritesAndConsentAreOwnedAndNeverAssumeMarketingApproval():void
    {$f=$this->setupStore();self::assertTrue(class_exists(Customers::class),'Müşteri PHP modülü eksik.');$c=new Customers($f->db,$f->config);$p=$f->db->one('SELECT id FROM products LIMIT 1')['id'];$c->favorite('a',$p,true);self::assertCount(1,$c->favorites('a'));self::assertSame([],$c->favorites('b'));self::assertFalse($c->preferences('a')['marketing']);$c->setPreferences('a',['marketing'=>false,'analytics'=>false,'privateNotifications'=>true]);self::assertFalse($c->preferences('a')['analytics']);self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM consent_events')['n']);}
    public function testAuthenticatedCheckoutOwnsTheOrderEvenWithANewAnonymousCookie():void
    {$f=$this->setupStore();$v=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$token=bin2hex(random_bytes(32));(new Cart($f->db,$f->config))->set($token,$v,1);$input=['email'=>'a@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16))];$c=new Sexogate\Commerce($f->db,$f->config);$input['quoteToken']=$c->quote($token,$input,'a')['quoteToken'];$order=$c->checkout($token,$input,'a');self::assertSame('a',$f->db->one('SELECT user_id FROM orders WHERE id=?',[$order['orderId']])['user_id']);self::assertNotNull($c->order($order['orderId'],null,'a'));}
}
