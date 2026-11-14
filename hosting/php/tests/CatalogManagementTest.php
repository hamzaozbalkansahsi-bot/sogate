<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/CatalogManagementTest.php
 * Açıklama   : Arşivlemenin geçmiş siparişi koruyup yeni satışı kapattığını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Catalog,Commerce,Cart,RuleViolation};
final class CatalogManagementTest extends TestCase
{
    public function testArchivePreservesOrderSnapshotAndStopsNewSales():void
    {$s=new TestShop(1);self::assertTrue(method_exists(Catalog::class,'archive'),'PHP katalog arşivleme işlemi eksik.');$p=$s->f->db->one('SELECT product_id FROM variants WHERE id=?',[$s->variant])['product_id'];(new Catalog($s->f->db,$s->f->config))->archive($p,$s->admin);$o=(new Commerce($s->f->db,$s->f->config))->order($s->order['orderId'],$s->order['trackingToken']);self::assertSame('Saten Bağ Detayı',$o['items'][0]['name']);$this->expectException(RuleViolation::class);(new Cart($s->f->db,$s->f->config))->set(bin2hex(random_bytes(32)),$s->variant,1);}
}
