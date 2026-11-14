<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/SuppliersHttpTest.php
 * Açıklama   : Tedarikçi ekranları ve API komutlarının MFA/rol/CSRF ile bağlandığını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Kernel};
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
final class SuppliersHttpTest extends TestCase
{
    public function testSupplierAdministrationRendersAndWarehouseCannotCallItsApi():void
    {
        $f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();
        $f->db->execute("INSERT INTO `user`(id,name,email,emailVerified,role,twoFactorEnabled) VALUES('staff','İşletme yöneticisi','supplier-admin@example.invalid',true,'admin',true)");
        $session=new Session(new MockArraySessionStorage());foreach(['user_id'=>'staff','epoch'=>0,'mfa'=>true,'auth_at'=>time(),'last_seen'=>time()] as $key=>$value)$session->set($key,$value);
        $kernel=new Kernel($f->db,$f->config,$session);$page=$kernel->handle(Request::create('http://127.0.0.1:3183/test/yonetim/tedarikciler'));self::assertSame(200,$page->getStatusCode());self::assertStringContainsString('Tahsis mutabakatı',$page->getContent());
        $token=json_decode($kernel->handle(Request::create('http://127.0.0.1:3183/test/api/session'))->getContent(),true)['csrfToken'];
        $request=fn()=>Request::create('http://127.0.0.1:3183/test/api/admin/suppliers','POST',[],[],[],['CONTENT_TYPE'=>'application/json','HTTP_ORIGIN'=>'http://127.0.0.1:3183','HTTP_X_CSRF_TOKEN'=>$token],json_encode(['action'=>'save','name'=>'İzole İstanbul tedarikçi','leadDays'=>2]));
        self::assertSame(200,$kernel->handle($request())->getStatusCode());
        $f->db->execute("UPDATE `user` SET role='warehouse' WHERE id='staff'");self::assertSame(403,$kernel->handle($request())->getStatusCode());self::assertSame(403,$kernel->handle(Request::create('http://127.0.0.1:3183/test/yonetim/tedarikciler'))->getStatusCode());
    }
}
