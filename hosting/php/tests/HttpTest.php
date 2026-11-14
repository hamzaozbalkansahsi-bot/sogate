<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/HttpTest.php
 * Açıklama   : Gerçek DB ile alt yol, SSR, CSRF, origin ve varsayılan kapalı HTTP sınırını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
use Sexogate\{Kernel,Fixtures};
final class HttpTest extends TestCase
{
    public function testPhpRendersTheStoreAndAllLinksStayInTestPrefix():void
    {$f=new TestDatabase();(new Fixtures($f->db,$f->config))->policies();$kernel=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));$r=$kernel->handle(Request::create('http://127.0.0.1:3183/test/'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('SEXOGATE',$r->getContent());self::assertStringContainsString('/test/urunler',$r->getContent());self::assertStringContainsString('noindex',$r->headers->get('X-Robots-Tag'));self::assertStringContainsString('no-store',$r->headers->get('Cache-Control'));}
    public function testPrivateAdminAndSourcePathsNeverExposeData():void
    {$f=new TestDatabase();$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));self::assertSame(401,$k->handle(Request::create('http://127.0.0.1:3183/test/api/admin/catalog'))->getStatusCode());$r=$k->handle(Request::create('http://127.0.0.1:3183/test/app/config.local.json'));self::assertGreaterThanOrEqual(400,$r->getStatusCode());self::assertStringNotContainsString('db_password',$r->getContent());}
    public function testMissingOriginAndCsrfAreRejectedBeforeAnyCartWrite():void
    {$f=new TestDatabase();$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/cart','POST',[],[],[],['CONTENT_TYPE'=>'application/json'],'{"variantId":"v","quantity":1}'));self::assertSame(403,$r->getStatusCode());$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/cart','POST',[],[],[],['CONTENT_TYPE'=>'application/json','HTTP_ORIGIN'=>'http://127.0.0.1:3183'],'{"variantId":"v","quantity":1}'));self::assertSame(403,$r->getStatusCode());self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM cart_items')['n']);}
    public function testUnknownPrefixAndLargeJsonFailClosed():void
    {$f=new TestDatabase();$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));self::assertSame(404,$k->handle(Request::create('http://127.0.0.1:3183/'))->getStatusCode());$r=$k->handle(Request::create('http://127.0.0.1:3183/test/api/cart','POST',[],[],[],['CONTENT_TYPE'=>'application/json','HTTP_ORIGIN'=>'http://127.0.0.1:3183'],str_repeat('x',33000)));self::assertSame(413,$r->getStatusCode());}
}
