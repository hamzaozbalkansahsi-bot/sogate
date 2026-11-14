<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ReportingTest.php
 * Açıklama   : Gerçek ödeme verisi ve depo rolünün finans raporu sınırı.
 */
declare(strict_types=1);
require_once __DIR__.'/TestShop.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Reporting,Principal,RuleViolation};
final class ReportingTest extends TestCase
{
    public function testRevenueComesFromActualCapturedOrdersInOneCurrency():void
    {$s=new TestShop(2);self::assertTrue(class_exists(Reporting::class),'PHP raporlama modülü eksik.');$r=(new Reporting($s->f->db,$s->f->config))->sales('TRY',null,null,$s->admin);self::assertSame(1,$r['orders']);self::assertSame(30300,$r['capturedMinor']);self::assertSame(30300,$r['averageOrderMinor']);self::assertSame(0,$r['refundedMinor']);self::assertArrayNotHasKey('netProfit',$r);}
    public function testWarehouseCannotRequestSalesOrCustomerData():void
    {$s=new TestShop();self::assertTrue(class_exists(Reporting::class),'PHP raporlama modülü eksik.');$this->expectException(RuleViolation::class);(new Reporting($s->f->db,$s->f->config))->sales('TRY',null,null,new Principal('warehouse','warehouse',true));}
    public function testEmptyDateInputsUseTheDefaultReportingPeriod():void
    {$s=new TestShop(1);$r=(new Reporting($s->f->db,$s->f->config))->sales('TRY','','',$s->admin);self::assertSame(1,$r['orders']);}
}
