<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ContentHttpTest.php
 * Açıklama   : Yayımlanan rehberin SSR içeriği ve HTML enjeksiyonu sınırı.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Content,Principal,Kernel};
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Session\Session;
use Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage;
final class ContentHttpTest extends TestCase
{
    public function testPublishedGuideRendersAndNeverExecutesStoredHtml():void
    {$f=new TestDatabase();$c=new Content($f->db,$f->config);$a=new Principal('admin','admin',true);$e=$c->save(['kind'=>'guide','slug'=>'bakim','locale'=>'tr','title'=>'Ölçü ve Özellikler','summary'=>'Kısa bilgi','body'=>'<script>window.attack=true</script> Güvenli Alışveriş'],$a);$c->publish($e['id'],$a);$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));$r=$k->handle(Request::create('http://127.0.0.1:3183/test/rehber/bakim'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('Güvenli Alışveriş',$r->getContent());self::assertStringNotContainsString('<script>window.attack',$r->getContent());}
}
