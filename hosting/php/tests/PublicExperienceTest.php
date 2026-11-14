<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/PublicExperienceTest.php
 * Açıklama   : Yaş bildirimi sonrası hesapsız vitrin, korunan admin ve gerçek ana ekran ikon sözleşmesi.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Config,Fixtures,Kernel};
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
final class PublicExperienceTest extends TestCase
{
    private function kernel(TestDatabase $f):Kernel
    {(new Fixtures($f->db,$f->config))->policies();$config=new Config(['env'=>'test','base_path'=>'/test','app_url'=>'https://sexogate.com/test','secret'=>$f->config->get('secret'),'payment_provider'=>'test','stage_access'=>true,'stage_user'=>'test-reviewer','stage_password_sha256'=>hash('sha256','TEST-only-access-pass'),'db_dsn'=>$f->config->get('db_dsn'),'db_user'=>$f->config->get('db_user'),'db_password'=>$f->config->get('db_password')]);return new Kernel($f->db,$config,new Session(new MockArraySessionStorage()));}
    public function testCustomersCanBrowseWithoutTheStaffTestGate():void
    {$f=new TestDatabase();$k=$this->kernel($f);foreach(['/','/urunler','/rehber'] as $path){$r=$k->handle(Request::create('https://sexogate.com/test'.$path));self::assertSame(200,$r->getStatusCode(),$path);self::assertStringNotContainsString('form action="/test/_access"',$r->getContent());}$r=$k->handle(Request::create('https://sexogate.com/test/yonetim/giris'));self::assertSame(401,$r->getStatusCode());self::assertStringContainsString('/test/_access',$r->getContent());self::assertSame(401,$k->handle(Request::create('https://sexogate.com/test/api/admin/catalog'))->getStatusCode());}
    public function testVisibleCreditIsRemovedWhileTheAgeChoicesRemain():void
    {$f=new TestDatabase();$k=$this->kernel($f);foreach(['/','/en/'] as $path){$r=$k->handle(Request::create('https://sexogate.com/test'.$path));self::assertSame(200,$r->getStatusCode());foreach(['PTYS Technoligess','Hamza ÖZBALKAN'] as $credit)self::assertStringNotContainsString($credit,$r->getContent());self::assertStringContainsString('id="age-accept"',$r->getContent());self::assertStringContainsString('id="age-exit"',$r->getContent());self::assertStringContainsString('apple-touch-icon',$r->getContent());}}
    public function testManifestHasRealPngAssetsAndStaysInsideTheTestApplication():void
    {$f=new TestDatabase();$k=$this->kernel($f);$r=$k->handle(Request::create('https://sexogate.com/test/manifest.webmanifest'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('application/manifest+json',$r->headers->get('Content-Type'));$m=json_decode($r->getContent(),true,32,JSON_THROW_ON_ERROR);self::assertSame('SEXOGATE',$m['name']);self::assertSame('/test/',$m['start_url']);self::assertSame('/test/',$m['scope']);self::assertSame('standalone',$m['display']);$sizes=[];foreach($m['icons'] as $icon){self::assertStringStartsWith('/test/assets/',$icon['src']);$file=dirname(__DIR__).'/public/assets/brand/app/'.basename($icon['src']);self::assertFileExists($file);$dimensions=getimagesize($file);self::assertSame($icon['sizes'],$dimensions[0].'x'.$dimensions[1]);$sizes[]=$icon['sizes'];}self::assertContains('192x192',$sizes);self::assertContains('512x512',$sizes);self::assertTrue(in_array('maskable',array_column($m['icons'],'purpose'),true));}
}
