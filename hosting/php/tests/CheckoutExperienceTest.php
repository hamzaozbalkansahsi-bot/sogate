<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CheckoutExperienceTest.php
 * Açıklama   : Ayrı fatura adresinin sunucu doğrulaması ve değişmez sipariş kaydı.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Cart,Commerce,RuleViolation};
final class CheckoutExperienceTest extends TestCase
{
    public function testSeparateBillingAddressIsValidatedAndStoredWithTheOrder():void
    {$s=new TestShop(1,false);$f=$s->f;$token=bin2hex(random_bytes(32));(new Cart($f->db,$f->config))->set($token,$s->variant,1);$c=new Commerce($f->db,$f->config);$i=['email'=>'billing@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16)),'sameBilling'=>false,'billingFullName'=>'Fatura Alıcısı','billingLine1'=>'İzmir Çeşme fatura adresi','billingCity'=>'İzmir','billingPostalCode'=>'35000'];$i['quoteToken']=$c->quote($token,$i)['quoteToken'];$o=$c->checkout($token,$i);$snapshot=json_decode($f->db->one('SELECT snapshot FROM orders WHERE id=?',[$o['orderId']])['snapshot'],true);self::assertArrayHasKey('billingAddress',$snapshot);self::assertSame('İzmir',$snapshot['billingAddress']['city']);self::assertSame('Fatura Alıcısı',$snapshot['billingAddress']['fullName']);self::assertSame('İstanbul',json_decode($f->db->one('SELECT address FROM orders WHERE id=?',[$o['orderId']])['address'],true)['city']);}
    public function testMissingSeparateBillingCannotCreateAnOrder():void
    {$s=new TestShop(1,false);$f=$s->f;$token=bin2hex(random_bytes(32));(new Cart($f->db,$f->config))->set($token,$s->variant,1);$c=new Commerce($f->db,$f->config);$i=['email'=>'billing@example.invalid','fullName'=>'Hamza ÖZBALKAN','phone'=>'05000000000','line1'=>'Şişli Çeşme adresi','city'=>'İstanbul','postalCode'=>'34000','privacyAccepted'=>true,'termsAccepted'=>true,'idempotencyKey'=>bin2hex(random_bytes(16)),'sameBilling'=>false];$i['quoteToken']=$c->quote($token,$i)['quoteToken'];$this->expectException(RuleViolation::class);$c->checkout($token,$i);}
}
