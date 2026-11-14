<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/OperationsHttpTest.php
 * Açıklama   : Paket ve iade ekranlarının gerçek veriye ve rol sınırlarına bağlandığını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\{Request};
use Symfony\Component\HttpFoundation\Session\{Session};
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
use Sexogate\Kernel;
final class OperationsHttpTest extends TestCase
{
    private function session(TestShop $s,string $role):Session
    {$s->f->db->execute('INSERT INTO `user`(id,name,email,emailVerified,role,twoFactorEnabled) VALUES(?,?,?,true,?,true)',['staff-'.$role,'Çalışan','staff-'.$role.'@example.invalid',$role]);$session=new Session(new MockArraySessionStorage());foreach(['user_id'=>'staff-'.$role,'epoch'=>0,'mfa'=>true,'auth_at'=>time(),'last_seen'=>time()] as $key=>$value)$session->set($key,$value);return $session;}
    public function testStaffOrderPageExposesPackagingFormsFromTheOrder():void
    {$s=new TestShop();$k=new Kernel($s->f->db,$s->f->config,$this->session($s,'admin'));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/yonetim/siparis/'.$s->order['orderId']));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('Paket hazırlığı',$r->getContent());self::assertStringContainsString('TEST-01',$r->getContent());}
    public function testGuestOrderPageSupportsReturnsWithoutARequiredAccount():void
    {$s=new TestShop();$k=new Kernel($s->f->db,$s->f->config,new Session(new MockArraySessionStorage()));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/siparis/'.$s->order['orderId'].'?token='.$s->order['trackingToken']));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('/api/returns',$r->getContent());}
    public function testWarehouseOrderApiNeverReturnsMoneyOrEmail():void
    {$s=new TestShop();$k=new Kernel($s->f->db,$s->f->config,$this->session($s,'warehouse'));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/admin/orders/'.$s->order['orderId']));self::assertSame(200,$r->getStatusCode());$json=$r->getContent();foreach(['cost_minor','total_minor','unit_minor','email'] as $field)self::assertStringNotContainsString('"'.$field.'"',$json);}
    public function testCustomerOrderApiDoesNotExposeInternalPackageTerms():void
    {$s=new TestShop();$s->f->db->execute("UPDATE order_fulfillment_groups SET snapshot=JSON_SET(snapshot,'$.contractReference','TEST özel sözleşme','$.returnReference','TEST özel iade sözleşmesi') WHERE order_id=?",[$s->order['orderId']]);$k=new Kernel($s->f->db,$s->f->config,new Session(new MockArraySessionStorage()));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/orders/'.$s->order['orderId'].'?token='.$s->order['trackingToken']));self::assertSame(200,$r->getStatusCode());foreach(['handlingMinor','contractReference','returnReference','supplierId','routeId','costSources'] as $field)self::assertStringNotContainsString('"'.$field.'"',$r->getContent());self::assertStringContainsString('"shippingMinor"',$r->getContent());}
}
