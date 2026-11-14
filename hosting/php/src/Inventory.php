<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Inventory.php
 * Açıklama   : Fiziksel depo/lot/set ve ayrı tedarikçi bulunabilirliği ile stok hareketleri.
 */
declare(strict_types=1);
namespace Sexogate;
final class Inventory
{
    public function __construct(private Database $db,private Config $config){}
    public function receive(string $variant,int $quantity,string $reason,string $key,Principal $actor):array
    {
        $actor->require('inventory',true);RuleViolation::ensure($quantity>0&&$quantity<=1000000&&mb_strlen(trim($reason))>=5,'INVALID_RECEIPT','Adet ve belge/gerekçeyi kontrol edin.',400);
        return (new Audit($this->db))->command($actor,$key,[$variant,$quantity,$reason],function()use($variant,$quantity,$reason,$key,$actor){
            $this->definition('bundle-definition');$this->db->one('SELECT id FROM variants WHERE id=? FOR UPDATE',[$variant]);$v=$this->db->one('SELECT lot_tracking FROM variants WHERE id=?',[$variant]);RuleViolation::ensure($v,'VARIANT_NOT_FOUND','Stok kodu bulunamadı.',404);
            RuleViolation::ensure(!(bool)$v['lot_tracking']&&!$this->db->one('SELECT 1 FROM bundle_components WHERE bundle_variant_id=?',[$variant]),'LOT_OR_BUNDLE_RECEIPT','Lotlu ürün veya set üst kodu bu girişten alınamaz.');
            $changed=$this->db->execute("UPDATE inventory_balance SET on_hand=on_hand+? WHERE variant_id=? AND warehouse_id='main'",[$quantity,$variant]);RuleViolation::ensure($changed===1,'INVENTORY_NOT_FOUND','Ana depo bakiyesi kurulmadı.');
            $this->db->execute("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference,actor_id) VALUES(?,'main','receipt',?,?,?,?)",[$variant,$quantity,$reason,'receipt:'.$key,$actor->id]);(new Audit($this->db))->record($actor,'receive','inventory',$variant,['quantity'=>$quantity]);return ['variantId'=>$variant,'quantity'=>$quantity];
        });
    }
    public function definition(string $name,bool $exclusive=false):void
    {RuleViolation::ensure($this->db->one('SELECT name FROM commerce_definition_locks WHERE name=? '.($exclusive?'FOR UPDATE':'FOR SHARE'),[$name]),'DEFINITION_LOCK_MISSING','Stok tanım kilidi kurulmadı.',503);}
    public function warehouse(string $id):int
    {
        $day=(new \DateTimeImmutable('now',new \DateTimeZone('Europe/Istanbul')))->format('Y-m-d');
        $sql="WITH parts AS(SELECT component_variant_id id,quantity FROM bundle_components WHERE bundle_variant_id=? UNION ALL SELECT id,1 FROM variants WHERE id=? AND NOT EXISTS(SELECT 1 FROM bundle_components WHERE bundle_variant_id=?)),held AS(SELECT variant_id,SUM(quantity) qty FROM reservations WHERE warehouse_id='main' AND status='active' AND expires_at>CURRENT_TIMESTAMP(3) GROUP BY variant_id),lot_held AS(SELECT rl.lot_id,SUM(rl.quantity) qty FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.warehouse_id='main' AND r.status='active' AND r.expires_at>CURRENT_TIMESTAMP(3) GROUP BY rl.lot_id),lot_stock AS(SELECT l.variant_id,SUM(GREATEST(0,lb.on_hand-COALESCE(h.qty,0))) available FROM inventory_lots l JOIN inventory_lot_balances lb ON lb.lot_id=l.id AND lb.warehouse_id='main' LEFT JOIN lot_held h ON h.lot_id=l.id WHERE l.quarantined=false AND l.recall_reference IS NULL AND(l.expires_at IS NULL OR l.expires_at>?) GROUP BY l.variant_id) SELECT COALESCE(MIN(FLOOR(GREATEST(0,CASE WHEN v.lot_tracking=true THEN LEAST(COALESCE(l.available,0),COALESCE(b.on_hand,0)-COALESCE(h.qty,0))-COALESCE(b.safety_stock,0) ELSE COALESCE(b.on_hand,0)-COALESCE(b.safety_stock,0)-COALESCE(h.qty,0) END)/p.quantity)),0) available FROM parts p JOIN variants v ON v.id=p.id LEFT JOIN inventory_balance b ON b.variant_id=p.id AND b.warehouse_id='main' LEFT JOIN held h ON h.variant_id=p.id LEFT JOIN lot_stock l ON l.variant_id=p.id";
        return (int)$this->db->one($sql,[$id,$id,$id,$day])['available'];
    }
    public function offers(string $id,string $country='TR',string $currency='TRY'):array
    {return $this->db->all('SELECT a.* FROM supplier_offer_availability a JOIN variants v ON v.id=a.variant_id WHERE a.variant_id=? AND a.country=? AND a.currency=? AND(a.fixture=false OR ?=true) AND v.lot_tracking=false AND NOT EXISTS(SELECT 1 FROM bundle_components WHERE bundle_variant_id=v.id) ORDER BY a.cost_minor,a.supplier_id,a.id',[$id,$country,$currency,$this->config->local()?1:0]);}
    public function available(string $id):int
    {$v=$this->db->one('SELECT fulfillment_mode FROM variants WHERE id=?',[$id]);if(!$v)return 0;$own=$v['fulfillment_mode']==='dropship'?0:$this->warehouse($id);if($v['fulfillment_mode']==='warehouse')return $own;$offers=$this->offers($id);return max($own,$offers?max(array_map('intval',array_column($offers,'available'))):0);}
    public function plan(array $items,array $country,bool $locked):array
    {
        $ids=array_column($items,'id');$components=$this->db->all('SELECT * FROM bundle_components WHERE bundle_variant_id IN('.Database::slots($ids).') ORDER BY component_variant_id,bundle_variant_id',$ids);
        $physical=array_values(array_unique(array_merge($ids,array_column($components,'component_variant_id'))));sort($physical,SORT_STRING);
        if($locked){$this->db->all("SELECT variant_id FROM inventory_balance WHERE warehouse_id='main' AND variant_id IN(".Database::slots($physical).') ORDER BY variant_id FOR UPDATE',$physical);$this->db->all('SELECT id FROM supplier_offers WHERE variant_id IN('.Database::slots($ids).') ORDER BY id FOR UPDATE',$ids);}
        $used=[];$stock=[];$lines=[];$groups=[];
        foreach($items as $item){
            $parts=array_values(array_filter($components,fn($p)=>$p['bundle_variant_id']===$item['id']));RuleViolation::ensure(!$parts||$item['fulfillment_mode']==='warehouse','SUPPLIER_BUNDLE_UNSUPPORTED','Setler yalnız kendi depomuzdan hazırlanabilir.');
            foreach($parts as $part){RuleViolation::ensure(!$this->db->one('SELECT 1 FROM bundle_components WHERE bundle_variant_id=?',[$part['component_variant_id']]),'NESTED_BUNDLE_DISABLED','İç içe set desteklenmiyor.');$v=$this->db->one('SELECT v.active,p.fixture FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=?',[$part['component_variant_id']]);RuleViolation::ensure($v&&(bool)$v['active']&&(!(bool)$v['fixture']||$this->config->local()),'BUNDLE_COMPONENT_UNAVAILABLE','Set bileşeni kullanılamıyor.');}
            $partRows=$parts?:[['component_variant_id'=>$item['id'],'quantity'=>1]];$own=$this->warehouse($item['id']);
            foreach($partRows as $part)$own=min($own,intdiv(max(0,$this->warehouse($part['component_variant_id'])-($used[$part['component_variant_id']]??0)),(int)$part['quantity']));
            $source=$item['fulfillment_mode']!=='dropship'&&$own>=$item['quantity']?'warehouse':'supplier';$offer=null;
            if($source==='supplier'&&$item['fulfillment_mode']!=='warehouse'&&!$parts&&!(bool)$item['lot_tracking'])foreach($this->offers($item['id'],$country['code'],$country['currency']) as $candidate)if((int)$candidate['available']>=$item['quantity']){$offer=$candidate;break;}
            RuleViolation::ensure($source==='warehouse'||$offer,'FULFILLMENT_UNAVAILABLE','Bu adet için doğrulanmış gönderim kaynağı bulunamadı.');
            $key=$source==='warehouse'?'warehouse':'supplier:'.$offer['supplier_id'];$cost=(int)$item['cost_minor'];
            if($source==='warehouse'){$groups[$key]=['key'=>$key,'source'=>'warehouse','shippingMinor'=>(int)$country['shipping_minor'],'handlingMinor'=>0];$cost=0;foreach($partRows as $part){$id=$part['component_variant_id'];$qty=(int)$part['quantity']*(int)$item['quantity'];$used[$id]=($used[$id]??0)+$qty;$stock[$id]=($stock[$id]??0)+$qty;$partCost=(int)$this->db->one('SELECT cost_minor FROM variants WHERE id=?',[$id])['cost_minor'];$cost=Money::sum([$cost,Money::multiply($partCost,(int)$part['quantity'])]);}}
            else{$groups[$key]=['key'=>$key,'source'=>'supplier','supplierId'=>$offer['supplier_id'],'routeId'=>$offer['route_id'],'shippingMinor'=>(int)$offer['shipping_minor'],'handlingMinor'=>(int)$offer['handling_minor'],'minDays'=>(int)$offer['min_days'],'maxDays'=>(int)$offer['max_days'],'reference'=>$offer['route_reference'],'contractReference'=>$offer['contract_reference'],'returnReference'=>$offer['return_reference'],'carrier'=>$offer['carrier']];$cost=(int)$offer['cost_minor'];}
            $lines[]=['variantId'=>$item['id'],'quantity'=>(int)$item['quantity'],'source'=>$source,'groupKey'=>$key,'offerId'=>$offer['id']??null,'unitCostMinor'=>$cost,'mode'=>$item['fulfillment_mode'],'components'=>array_map(fn($p)=>['variantId'=>$p['component_variant_id'],'quantity'=>(int)$p['quantity']],$parts)];
        }
        return ['lines'=>$lines,'groups'=>array_values($groups),'stock'=>$stock,'shippingMinor'=>Money::sum(array_column($groups,'shippingMinor')),'handlingMinor'=>Money::sum(array_column($groups,'handlingMinor'))];
    }
    public function reserve(string $order,string $expires,array $plan):array
    {
        $groupIds=[];foreach($plan['groups'] as $i=>$g){$id=Database::id();$groupIds[$g['key']]=$id;$this->db->execute('INSERT INTO order_fulfillment_groups(id,order_id,source,supplier_id,snapshot) VALUES(?,?,?,?,?)',[$id,$order,$g['source'],$g['supplierId']??null,$this->config->json($g+['number'=>$i+1])]);}
        foreach($plan['lines'] as $line)if($line['source']==='supplier')$this->db->execute('INSERT INTO supplier_reservations(order_id,variant_id,offer_id,quantity,expires_at) VALUES(?,?,?,?,?)',[$order,$line['variantId'],$line['offerId'],$line['quantity'],$expires]);
        foreach($plan['stock'] as $variant=>$quantity){$id=Database::id();$this->db->execute("INSERT INTO reservations(id,order_id,variant_id,warehouse_id,quantity,expires_at) VALUES(?,?,?,'main',?,?)",[$id,$order,$variant,$quantity,$expires]);$this->reserveLots($id,$variant,$quantity);}
        return $groupIds;
    }
    private function reserveLots(string $reservation,string $variant,int $quantity):void
    {
        if(!(bool)$this->db->one('SELECT lot_tracking FROM variants WHERE id=?',[$variant])['lot_tracking'])return;
        $day=(new \DateTimeImmutable('now',new \DateTimeZone('Europe/Istanbul')))->format('Y-m-d');$lots=$this->db->all("SELECT l.id,b.on_hand,COALESCE((SELECT SUM(rl.quantity) FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE rl.lot_id=l.id AND r.warehouse_id='main' AND r.status='active' AND r.expires_at>CURRENT_TIMESTAMP(3)),0) held FROM inventory_lots l JOIN inventory_lot_balances b ON b.lot_id=l.id AND b.warehouse_id='main' WHERE l.variant_id=? AND l.quarantined=false AND l.recall_reference IS NULL AND(l.expires_at IS NULL OR l.expires_at>?) ORDER BY(l.expires_at IS NULL),l.expires_at,l.id FOR UPDATE",[$variant,$day]);
        foreach($lots as $lot){$take=min($quantity,max(0,(int)$lot['on_hand']-(int)$lot['held']));if(!$take)continue;$this->db->execute('INSERT INTO reservation_lots(reservation_id,lot_id,quantity) VALUES(?,?,?)',[$reservation,$lot['id'],$take]);$quantity-=$take;if(!$quantity)break;}RuleViolation::ensure($quantity===0,'LOT_STOCK_UNAVAILABLE','Uygun lot stoğu kalmadı.');
    }
    public function lotsValid(array $r):bool
    {
        if(!(bool)$this->db->one('SELECT lot_tracking FROM variants WHERE id=?',[$r['variant_id']])['lot_tracking'])return true;
        $day=(new \DateTimeImmutable('now',new \DateTimeZone('Europe/Istanbul')))->format('Y-m-d');$lots=$this->db->all('SELECT rl.quantity,b.on_hand,l.variant_id,l.quarantined,l.recall_reference,l.expires_at FROM reservation_lots rl JOIN inventory_lots l ON l.id=rl.lot_id JOIN inventory_lot_balances b ON b.lot_id=l.id AND b.warehouse_id=? WHERE rl.reservation_id=? ORDER BY l.id FOR UPDATE',[$r['warehouse_id'],$r['id']]);
        if(array_sum(array_column($lots,'quantity'))!==(int)$r['quantity'])return false;foreach($lots as $lot)if($lot['variant_id']!==$r['variant_id']||(bool)$lot['quarantined']||$lot['recall_reference']!==null||($lot['expires_at']!==null&&$lot['expires_at']<=$day)||(int)$lot['on_hand']<(int)$lot['quantity'])return false;return true;
    }
    public function consume(array $r):void
    {
        RuleViolation::ensure($this->db->execute('UPDATE inventory_balance SET on_hand=on_hand-? WHERE variant_id=? AND warehouse_id=? AND on_hand>=?',[$r['quantity'],$r['variant_id'],$r['warehouse_id'],$r['quantity']])===1,'STOCK_CONFLICT','Ödeme stoğu doğrulanamadı.');
        $lots=$this->db->all('SELECT lot_id,quantity FROM reservation_lots WHERE reservation_id=? ORDER BY lot_id',[$r['id']]);
        if($lots)foreach($lots as $lot){RuleViolation::ensure($this->db->execute('UPDATE inventory_lot_balances SET on_hand=on_hand-? WHERE lot_id=? AND warehouse_id=? AND on_hand>=?',[$lot['quantity'],$lot['lot_id'],$r['warehouse_id'],$lot['quantity']])===1,'LOT_STOCK_CONFLICT','Lot stoğu doğrulanamadı.');$this->db->execute("INSERT INTO inventory_movements(variant_id,warehouse_id,lot_id,type,quantity,reason,reference) VALUES(?,?,?,'sale',?,'Doğrulanmış ödeme lot tüketimi',?)",[$r['variant_id'],$r['warehouse_id'],$lot['lot_id'],-$lot['quantity'],'payment:'.$r['order_id'].':'.$r['variant_id'].':'.$lot['lot_id']]);}
        else $this->db->execute("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference) VALUES(?,?,'sale',?,'Doğrulanmış ödeme',?)",[$r['variant_id'],$r['warehouse_id'],-$r['quantity'],'payment:'.$r['order_id'].':'.$r['variant_id']]);
    }
}
