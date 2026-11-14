<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/DiscoveryTest.php
 * Açıklama   : NODENO listeleme/keşif sözleşmesini gerçek SEXOGATE kataloğuyla sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Catalog,Fixtures,Principal};
final class DiscoveryTest extends TestCase
{
    private function shop():array{$f=new TestDatabase();$x=new Fixtures($f->db,$f->config);$x->policies();$x->catalog(new Principal('admin','admin',true));return [$f,new Catalog($f->db,$f->config)];}
    public function testPriceFiltersSortAndSkuSearchUseServerData():void
    {[$f,$c]=$this->shop();$r=$c->search(['minPrice'=>'140,00','maxPrice'=>'200,00','sort'=>'price-desc']);self::assertSame(2,$r['total']);self::assertSame(18900,$r['rows'][0]['variants'][0]['price_minor']);self::assertSame(1,$c->search(['q'=>'TEST01'])['total']);self::assertSame(1,$c->search(['q'=>'Detayı Saten'])['total']);}
    public function testUnavailableFilterAndUnknownSortAreSafe():void
    {[$f,$c]=$this->shop();$id=$f->db->one("SELECT id FROM variants WHERE sku='TEST-01'")['id'];$f->db->execute('UPDATE inventory_balance SET safety_stock=on_hand WHERE variant_id=?',[$id]);$r=$c->search(['available'=>'1']);self::assertSame(2,$r['total']);self::assertSame(3,$c->search(['sort'=>'price;DROP TABLE products'])['total']);}
    public function testRelatedProductsExcludeCurrentAndDraftItems():void
    {[$f,$c]=$this->shop();$p=$c->product('saten-bag-detayi');$r=$c->related($p['id']);self::assertCount(2,$r);self::assertNotContains($p['id'],array_column($r,'id'));$f->db->execute("UPDATE products SET status='draft' WHERE id=?",[$r[0]['id']]);self::assertCount(1,$c->related($p['id']));}
    public function testDiscoveryScreensExposeRealMenusQuickViewAndRelatedProducts():void
    {[$f,$c]=$this->shop();$k=new \Sexogate\Kernel($f->db,$f->config,new \Symfony\Component\HttpFoundation\Session\Session(new \Symfony\Component\HttpFoundation\Session\Storage\MockArraySessionStorage()));$r=$k->handle(\Symfony\Component\HttpFoundation\Request::create('/test/kategoriler'));self::assertSame(200,$r->getStatusCode());self::assertStringContainsString('class="category-tile-grid"',$r->getContent());self::assertStringNotContainsString('id="catalog-menu"',$r->getContent());$r=$k->handle(\Symfony\Component\HttpFoundation\Request::create('/test/urun/saten-bag-detayi'));self::assertStringContainsString('data-image-zoom',$r->getContent());self::assertStringContainsString('Benzer ürünler',$r->getContent());$r=$k->handle(\Symfony\Component\HttpFoundation\Request::create('/test/api/product/saten-bag-detayi'));self::assertSame(200,$r->getStatusCode());self::assertStringNotContainsString('cost_minor',$r->getContent());}
}
