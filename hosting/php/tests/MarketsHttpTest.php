<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/MarketsHttpTest.php
 * Açıklama   : Ülke/vergi/belge ve finans fiyat ekranlarının sunucu yetki sınırını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Kernel,Fixtures};
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
final class MarketsHttpTest extends TestCase
{
    public function testAdminPagesAndCountryCommandsWorkWithoutOpeningUnreviewedSales():void
    {
        $f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();$f->db->execute("INSERT INTO `user`(id,name,email,emailVerified,role,twoFactorEnabled) VALUES('staff','İşletme','markets@example.invalid',true,'admin',true)");$session=new Session(new MockArraySessionStorage());foreach(['user_id'=>'staff','epoch'=>0,'mfa'=>true,'auth_at'=>time(),'last_seen'=>time()] as $key=>$value)$session->set($key,$value);$k=new Kernel($f->db,$f->config,$session);
        foreach(['/yonetim/pazarlar','/yonetim/fiyatlar','/yonetim/uygunluk'] as $path)self::assertSame(200,$k->handle(Request::create('http://127.0.0.1:3183/test'.$path))->getStatusCode(),$path);
        $csrf=json_decode($k->handle(Request::create('http://127.0.0.1:3183/test/api/session'))->getContent(),true)['csrfToken'];$request=fn($body)=>Request::create('http://127.0.0.1:3183/test/api/admin/markets','POST',[],[],[],['CONTENT_TYPE'=>'application/json','HTTP_ORIGIN'=>'http://127.0.0.1:3183','HTTP_X_CSRF_TOKEN'=>$csrf],json_encode($body));
        $r=$k->handle($request(['action'=>'country','code'=>'DE','name'=>'İzole test ülkesi','currency'=>'EUR','shipping'=>'25,00','ageMethod'=>'declaration','timeZone'=>'Europe/Berlin']));self::assertSame(200,$r->getStatusCode());self::assertSame(0,(int)$f->db->one("SELECT enabled FROM country_rules WHERE code='DE'")['enabled']);
        $f->db->execute("UPDATE `user` SET role='finance' WHERE id='staff'");self::assertSame(403,$k->handle($request(['action'=>'country','code'=>'US']))->getStatusCode());self::assertSame(200,$k->handle(Request::create('http://127.0.0.1:3183/test/yonetim/fiyatlar'))->getStatusCode());self::assertSame(403,$k->handle(Request::create('http://127.0.0.1:3183/test/yonetim/pazarlar'))->getStatusCode());
    }
}
