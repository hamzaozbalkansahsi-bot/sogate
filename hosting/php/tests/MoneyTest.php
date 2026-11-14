<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/MoneyTest.php
 * Açıklama   : Tam alt-birim para ve büyük tamsayı dağılım sınırlarını sınar.
 */
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Sexogate\Money;
use Sexogate\RuleViolation;
final class MoneyTest extends TestCase
{
    public function testHumanDecimalInputPreservesMinorUnitsWithoutFloatingPoint():void
    {self::assertTrue(method_exists(Money::class,'parseDecimal'),'Ondalık para girişi eksik.');self::assertSame(14950,Money::parseDecimal('149,50'));self::assertSame(5,Money::parseDecimal('0.05'));self::assertSame(12500,Money::parseDecimal('125'));$this->expectException(Sexogate\RuleViolation::class);Money::parseDecimal('1e4');}
    public function testIntegerValuesNeverUseFloat(): void
    {
        self::assertSame(12501, Money::amount('12501'));
        self::assertSame(9000000000000, Money::amount('9000000000000'));
        $this->expectException(RuleViolation::class); Money::amount(12.5);
    }
    public function testAllocationDoesNotOverflowPhpIntegers(): void
    {
        $shares=Money::allocate(8999999999999,[3000000000000,3000000000000,3000000000000]);
        self::assertSame(8999999999999,array_sum($shares));
        self::assertSame([3000000000000,3000000000000,2999999999999],$shares);
    }
    public function testMixedInclusiveTaxAndPartialAllocation(): void
    {
        $result=Money::mixed([['grossMinor'=>10000,'rateBps'=>2000],['grossMinor'=>10000,'rateBps'=>1000]],1001);
        self::assertSame(20000,$result['subtotalMinor']); self::assertSame(1001,$result['discountMinor']);
        self::assertSame([501,500],array_column($result['lines'],'discountMinor'));
        self::assertSame(1583+864,$result['goodsTaxMinor']);
    }
    public function testMoneyLimitsAreEnforcedBeforeTruncation(): void
    {
        $this->expectException(RuleViolation::class); Money::amount('9000000000001');
    }
    public function testZeroAndRoundingAreDeterministic(): void
    {
        self::assertSame([1,0,0],Money::allocate(1,[1,1,1]));
        self::assertSame(167,Money::inclusiveTax(1000,2000));
        self::assertSame(500,Money::basisPoints(10000,500));
    }
}
