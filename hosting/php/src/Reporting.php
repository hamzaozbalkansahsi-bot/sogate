<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Reporting.php
 * Açıklama   : Gerçek tahsilat/iade, sipariş katkısı ve maliyetsiz stok uyarıları.
 */
declare(strict_types=1);
namespace Sexogate;
use Brick\Math\BigInteger;
final class Reporting
{
    public function __construct(private Database $db,private Config $config){}
    private function range(?string $from,?string $to):array
    {$tz=new \DateTimeZone('Europe/Istanbul');$today=new \DateTimeImmutable('today',$tz);$from=$from?:$today->modify('-30 days')->format('Y-m-d');$to=$to?:$today->format('Y-m-d');$a=\DateTimeImmutable::createFromFormat('!Y-m-d',$from,$tz);$b=\DateTimeImmutable::createFromFormat('!Y-m-d',$to,$tz);RuleViolation::ensure($a&&$b&&$a->format('Y-m-d')===$from&&$b->format('Y-m-d')===$to&&$a<=$b&&$a->diff($b)->days<=3660,'REPORT_DATE_INVALID','Rapor tarih aralığını kontrol edin.',400);return [$a->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d H:i:s'),$b->modify('+1 day')->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d H:i:s')];}
    public function sales(string $currency,?string $from,?string $to,Principal $actor):array
    {$actor->require('finance');RuleViolation::ensure(in_array($currency,['TRY','EUR','USD','GBP'],true),'INVALID_CURRENCY','Para birimini kontrol edin.',400);[$a,$b]=$this->range($from,$to);return $this->db->transaction(function()use($currency,$a,$b){$r=$this->db->one("SELECT COUNT(*) orders,COALESCE(SUM(p.amount_minor),0) captured,COALESCE(SUM(p.refunded_minor),0) refunded,COALESCE(SUM(o.tax_minor),0) tax,COALESCE(SUM(o.cost_minor),0) cost,COALESCE(SUM(o.fee_minor+o.advertising_minor+o.return_provision_minor),0) expenses FROM payments p JOIN orders o ON o.id=p.order_id WHERE p.currency=? AND p.status IN('succeeded','partially_refunded','refunded') AND o.created_at>=? AND o.created_at<?",[$currency,$a,$b]);$refundTax=(int)$this->db->one("SELECT COALESCE(SUM(f.tax_minor),0) n FROM refunds f JOIN payments p ON p.id=f.payment_id JOIN orders o ON o.id=p.order_id WHERE f.status='succeeded' AND p.currency=? AND o.created_at>=? AND o.created_at<?",[$currency,$a,$b])['n'];$captured=Money::amount($r['captured']);$refunded=Money::amount($r['refunded']);$n=(int)$r['orders'];$net=$captured-$refunded;$tax=Money::amount($r['tax'])-$refundTax;$failures=(int)$this->db->one("SELECT COUNT(*) n FROM payments p JOIN orders o ON o.id=p.order_id WHERE p.currency=? AND p.status='failed' AND o.created_at>=? AND o.created_at<?",[$currency,$a,$b])['n'];$exceptions=(int)$this->db->one("SELECT COUNT(*) n FROM orders WHERE currency=? AND status='payment_exception' AND created_at>=? AND created_at<?",[$currency,$a,$b])['n'];return ['currency'=>$currency,'orders'=>$n,'capturedMinor'=>$captured,'refundedMinor'=>$refunded,'netCapturedMinor'=>$net,'taxMinor'=>$tax,'recordedCostMinor'=>Money::amount($r['cost']),'recordedExpensesMinor'=>Money::amount($r['expenses']),'contributionMinor'=>$net-$tax-(int)$r['cost']-(int)$r['expenses'],'averageOrderMinor'=>$n?BigInteger::of($captured)->plus(intdiv($n,2))->quotient($n)->toInt():0,'paymentFailures'=>$failures,'paymentExceptions'=>$exceptions,'costsComplete'=>false,'empty'=>$n===0];},true);}
    public function lowStock(Principal $actor):array
    {$actor->require('inventory');$rows=$this->db->all("SELECT v.id,v.sku,p.name,b.on_hand,b.quarantine,b.minimum_stock,b.safety_stock FROM inventory_balance b JOIN variants v ON v.id=b.variant_id JOIN products p ON p.id=v.product_id WHERE b.warehouse_id='main' AND v.active=true ORDER BY b.on_hand-b.minimum_stock,v.sku LIMIT 200");$result=[];$i=new Inventory($this->db,$this->config);foreach($rows as $row){$row['available']=$i->warehouse($row['id']);if($row['available']<=(int)$row['minimum_stock'])$result[]=$row;}return $result;}
}
