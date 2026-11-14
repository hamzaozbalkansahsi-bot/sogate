<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/SeoTest.php
 * Açıklama   : Gerçek ürün/fiyat/stok schema'sı, canonical ve sahte puan yokluğu.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Seo};
final class SeoTest extends TestCase
{
    public function testProductSchemaUsesCurrentPriceAndActualStockWithoutInventedRatings():void
    {$s=new TestShop(1);self::assertTrue(class_exists(Seo::class),'PHP ürün SEO modülü eksik.');$id=$s->f->db->one('SELECT product_id FROM variants WHERE id=?',[$s->variant])['product_id'];$seo=(new Seo($s->f->db,$s->f->config))->product($id,'tr');self::assertSame('149.00',$seo['schema']['offers'][0]['price']);self::assertSame('https://schema.org/InStock',$seo['schema']['offers'][0]['availability']);self::assertArrayNotHasKey('aggregateRating',$seo['schema']);self::assertStringNotContainsString('?', $seo['canonical']);$s->f->db->execute('UPDATE variant_prices SET amount_minor=12345 WHERE variant_id=?',[$s->variant]);self::assertSame('123.45',(new Seo($s->f->db,$s->f->config))->product($id,'tr')['schema']['offers'][0]['price']);}
}
