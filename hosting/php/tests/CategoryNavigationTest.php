<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CategoryNavigationTest.php
 * Açıklama   : NODENO mobil kategori bağlantısının tam kart sayfasını açma sözleşmesi.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Fixtures,Principal,Kernel};
use Symfony\Component\HttpFoundation\{Request,Session\Session,Session\Storage\MockArraySessionStorage};
final class CategoryNavigationTest extends TestCase
{
    public function testMobileCategoryIsAFullPageLinkWithRealCountsAndImages():void
    {$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));$k=new Kernel($f->db,$f->config,new Session(new MockArraySessionStorage()));$html=$k->handle(Request::create('/test/'))->getContent();$dom=new DOMDocument();$old=libxml_use_internal_errors(true);$dom->loadHTML('<?xml encoding="UTF-8">'.$html,LIBXML_NONET);libxml_clear_errors();libxml_use_internal_errors($old);$xp=new DOMXPath($dom);$nodes=$xp->query('//nav[contains(@class,"mobile-bottom-nav")]/a');self::assertCount(5,$nodes);self::assertSame('/test/kategoriler',$nodes->item(1)->getAttribute('href'));self::assertSame('/test/hesap',$nodes->item(4)->getAttribute('href'));$r=$k->handle(Request::create('/test/kategoriler'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('Tüm kategoriler',$r->getContent());self::assertStringContainsString('category-tile-photo',$r->getContent());self::assertStringContainsString('3 ürün',$r->getContent());}
}
