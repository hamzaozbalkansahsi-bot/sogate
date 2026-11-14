<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Money.php
 * Açıklama   : Alt-birim para, yuvarlama ve taşmayan tamsayı dağılımı.
 */
declare(strict_types=1);
namespace Sexogate;
use Brick\Math\BigInteger;
final class Money
{
    public const LIMIT=9000000000000;
    public static function parseDecimal(string $value):int
    {RuleViolation::ensure((bool)preg_match('/\A(0|[1-9][0-9]{0,10})(?:[,.]([0-9]{1,2}))?\z/',trim($value),$m),'INVALID_MONEY','Tutarı örneğin149,50 biçiminde girin.',400);return self::amount((string)BigInteger::of($m[1])->multipliedBy(100)->plus((int)str_pad($m[2]??'',2,'0')));}
    public static function amount(mixed $value):int
    {
        RuleViolation::ensure(is_int($value)||(is_string($value)&&preg_match('/\A(?:0|[1-9][0-9]{0,12})\z/D',$value)),'INVALID_MONEY','Para tutarı geçersiz.',400);
        $n=(int)$value;RuleViolation::ensure($n>=0&&$n<=self::LIMIT,'INVALID_MONEY','Para tutarı izin verilen sınırı aşıyor.',400);return $n;
    }
    public static function sum(array $values):int
    {$sum=BigInteger::zero();foreach($values as $v)$sum=$sum->plus(self::amount($v));return self::amount((string)$sum);}
    public static function multiply(int $price,int $quantity):int
    {RuleViolation::ensure($quantity>=0&&$quantity<=1000000,'INVALID_QUANTITY','Adet geçersiz.',400);return self::amount((string)BigInteger::of(self::amount($price))->multipliedBy($quantity));}
    public static function basisPoints(int $value,int $rate):int
    {RuleViolation::ensure($rate>=0&&$rate<=10000,'INVALID_RATE','Oran geçersiz.',400);return BigInteger::of(self::amount($value))->multipliedBy($rate)->plus(5000)->quotient(10000)->toInt();}
    public static function inclusiveTax(int $gross,int $rate):int
    {$divisor=10000+$rate;RuleViolation::ensure($rate>=0&&$rate<=10000,'INVALID_RATE','Vergi oranı geçersiz.',400);return BigInteger::of(self::amount($gross))->multipliedBy($rate)->plus(intdiv($divisor,2))->quotient($divisor)->toInt();}
    public static function allocate(int $total,array $weights):array
    {
        self::amount($total);$sum=self::sum($weights);RuleViolation::ensure($sum>0,'INVALID_ALLOCATION','Dağıtım ağırlığı geçersiz.',400);$shares=[];$rank=[];
        foreach(array_values($weights) as $i=>$w){[$q,$r]=BigInteger::of($total)->multipliedBy($w)->quotientAndRemainder($sum);$shares[$i]=$q->toInt();$rank[]=['i'=>$i,'r'=>$r];}
        usort($rank,fn($a,$b)=>$b['r']->compareTo($a['r'])?:$a['i']<=>$b['i']);$remaining=$total-array_sum($shares);
        foreach($rank as $r){if($remaining--<=0)break;$shares[$r['i']]++;}return $shares;
    }
    public static function mixed(array $lines,int $discount):array
    {
        RuleViolation::ensure(count($lines)>0,'INVALID_PRODUCT_TAX','Ürün vergi hesabı için satır gerekir.',400);
        $gross=array_map(fn($l)=>self::amount($l['grossMinor']),$lines);$subtotal=self::sum($gross);self::amount($discount);
        RuleViolation::ensure($discount<=$subtotal,'INVALID_DISCOUNT','İndirim ürün tutarını aşamaz.',400);
        $shares=$subtotal===0?array_fill(0,count($lines),0):self::allocate($discount,$gross);$result=[];
        foreach($lines as $i=>$line){$tax=self::inclusiveTax($gross[$i]-$shares[$i],$line['rateBps']);$result[]=$line+['discountMinor'=>$shares[$i],'taxMinor'=>$tax,'netMinor'=>$gross[$i]-$shares[$i]-$tax];}
        return ['subtotalMinor'=>$subtotal,'discountMinor'=>$discount,'grossAfterDiscountMinor'=>$subtotal-$discount,'goodsTaxMinor'=>array_sum(array_column($result,'taxMinor')),'lines'=>$result];
    }
    public static function format(int $amount,string $currency='TRY',string $locale='tr'):string
    {
        $digits=['TRY'=>2,'EUR'=>2,'USD'=>2,'GBP'=>2];RuleViolation::ensure(isset($digits[$currency]),'INVALID_CURRENCY','Para birimi desteklenmiyor.',400);self::amount($amount);
        $whole=intdiv($amount,100);$fraction=str_pad((string)($amount%100),2,'0',STR_PAD_LEFT);$grouped=preg_replace('/\B(?=(\d{3})+(?!\d))/', $locale==='tr'?'.':',',(string)$whole);
        return $grouped.($locale==='tr'?',':'.').$fraction.' '.(['TRY'=>'₺','EUR'=>'€','USD'=>'$','GBP'=>'£'][$currency]);
    }
}
