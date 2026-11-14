<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Fulfillment.php
 * Açıklama   : Siparişe bağlı toplama/paketleme ve stok tekrar düşmeden kısmi sevk.
 */
declare(strict_types=1);
namespace Sexogate;
final class Fulfillment
{
    public function __construct(private Database $db,private Config $config){}
    public function prepare(string $order,array $items,string $key,Principal $actor):array
    {
        $actor->require('shipping',true);RuleViolation::ensure(count($items)>0&&count($items)<=100,'INVALID_PACKAGE','Paket ürünlerini seçin.',400);usort($items,fn($a,$b)=>strcmp($a['variantId']??'',$b['variantId']??''));RuleViolation::ensure(count(array_unique(array_column($items,'variantId')))===count($items),'INVALID_PACKAGE','Paket satırları tekrarlanamaz.',400);
        return (new Audit($this->db))->command($actor,$key,['prepare',$order,$items],function()use($order,$items,$actor){$o=$this->paid($order);$this->assertLots($order);$id=Database::id();$this->db->execute('INSERT INTO fulfillment_tasks(id,order_id) VALUES(?,?)',[$id,$order]);
            foreach($items as $item){$variant=$item['variantId']??'';$q=$item['quantity']??0;RuleViolation::ensure(is_int($q)&&$q>0&&$q<=1000000,'INVALID_QUANTITY','Paket adedini kontrol edin.',400);$line=$this->db->one('SELECT quantity,fulfillment_source FROM order_items WHERE order_id=? AND variant_id=?',[$order,$variant]);$sent=$this->sent($order,$variant);$held=(int)$this->db->one("SELECT COALESCE(SUM(i.quantity),0) n FROM fulfillment_task_items i JOIN fulfillment_tasks t ON t.id=i.task_id WHERE t.order_id=? AND i.variant_id=? AND t.status IN('picking','packing','packed')",[$order,$variant])['n'];RuleViolation::ensure($line&&$line['fulfillment_source']==='warehouse'&&$sent+$held+$q+$this->cancelledQuantity($order,$variant)<=(int)$line['quantity'],'PACKAGE_QUANTITY','Adet kalan depo siparişini aşıyor veya başka pakete ayrılmış.');$this->db->execute('INSERT INTO fulfillment_task_items(task_id,variant_id,quantity) VALUES(?,?,?)',[$id,$variant,$q]);}
            (new Audit($this->db))->record($actor,'prepare','fulfillment_tasks',$id);return ['id'=>$id,'status'=>'picking'];});
    }
    private function paid(string $order):array
    {$o=$this->db->one('SELECT id,status,payment_status,address FROM orders WHERE id=? FOR UPDATE',[$order]);RuleViolation::ensure($o&&in_array($o['status'],['confirmed','partially_shipped'],true)&&in_array($o['payment_status'],['succeeded','partially_refunded'],true),'ORDER_NOT_SHIPPABLE','Sipariş sevke uygun değil.');return $o;}
    private function cancelledQuantity(string $order,string $variant):int
    {return (int)$this->db->one("SELECT COALESCE(SUM(undispatched_quantity),0) n FROM returns WHERE order_id=? AND variant_id=? AND status IN('approved','received','inspected','refund_pending','refund_failed','refunded')",[$order,$variant])['n'];}
    private function sent(string $order,string $variant):int
    {return (int)$this->db->one('SELECT COALESCE(SUM(i.quantity),0) n FROM shipment_items i JOIN shipments s ON s.id=i.shipment_id WHERE s.order_id=? AND i.variant_id=?',[$order,$variant])['n'];}
    public function assertLots(string $order):void
    {$day=(new \DateTimeImmutable('now',new \DateTimeZone('Europe/Istanbul')))->format('Y-m-d');$bad=$this->db->one('SELECT l.id FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id JOIN inventory_lots l ON l.id=rl.lot_id WHERE r.order_id=? AND(l.quarantined=true OR l.recall_reference IS NOT NULL OR(l.expires_at IS NOT NULL AND l.expires_at<=?)) LIMIT 1 FOR SHARE',[$order,$day]);RuleViolation::ensure(!$bad,'LOT_NOT_SHIPPABLE','Sipariş lotu karantinada, geri çağrılmış veya süresi dolmuş.');}
    private function task(string $id):array
    {$ref=$this->db->one('SELECT order_id FROM fulfillment_tasks WHERE id=?',[$id]);RuleViolation::ensure($ref,'PACKAGE_NOT_FOUND','Paket bulunamadı.',404);$this->paid($ref['order_id']);$task=$this->db->one('SELECT * FROM fulfillment_tasks WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($task,'PACKAGE_NOT_FOUND','Paket bulunamadı.',404);return $task;}
    public function scan(string $id,string $barcode,string $phase,int $quantity,string $key,Principal $actor):array
    {
        $actor->require('shipping',true);RuleViolation::ensure(in_array($phase,['pick','pack'],true)&&$quantity>0&&$quantity<=1000000,'INVALID_SCAN','İşlem ve adedi kontrol edin.',400);
        return (new Audit($this->db))->command($actor,$key,['scan',$id,$barcode,$phase,$quantity],function()use($id,$barcode,$phase,$quantity,$actor){$t=$this->task($id);RuleViolation::ensure($t['status']===($phase==='pick'?'picking':'packing'),'PACKAGE_PHASE','Paketin işlem aşaması uygun değil.');$rows=$this->db->all('SELECT i.*,v.sku,v.barcode FROM fulfillment_task_items i JOIN variants v ON v.id=i.variant_id WHERE i.task_id=? ORDER BY i.variant_id FOR UPDATE',[$id]);$match=array_values(array_filter($rows,fn($r)=>($r['barcode']!==null&&$r['barcode']!==''?$r['barcode']:$r['sku'])===$barcode));RuleViolation::ensure(count($match)===1,'BARCODE_MISMATCH','Okunan kod bu pakette tek bir ürünle eşleşmiyor.');$row=$match[0];$column=$phase==='pick'?'picked_quantity':'packed_quantity';RuleViolation::ensure((int)$row[$column]+$quantity<=(int)$row['quantity'],'SCAN_QUANTITY','Okunan adet paket adedini aşıyor.');$this->db->execute("UPDATE fulfillment_task_items SET $column=$column+? WHERE task_id=? AND variant_id=?",[$quantity,$id,$row['variant_id']]);$left=(int)$this->db->one("SELECT COUNT(*) n FROM fulfillment_task_items WHERE task_id=? AND $column<quantity",[$id])['n'];$status=$left===0?($phase==='pick'?'packing':'packed'):$t['status'];$this->db->execute('UPDATE fulfillment_tasks SET status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$status,$id]);(new Audit($this->db))->record($actor,$phase,'fulfillment_tasks',$id,['quantity'=>$quantity]);return ['id'=>$id,'status'=>$status];});
    }
    public function ship(string $task,string $carrier,string $tracking,string $key,Principal $actor):array
    {
        $actor->require('shipping',true);$carrier=trim($carrier);$tracking=trim($tracking);RuleViolation::ensure(mb_strlen($carrier)>=2&&mb_strlen($carrier)<=100&&mb_strlen($tracking)>=3&&mb_strlen($tracking)<=200&&!preg_match('/[\x00-\x1f\x7f]|^(test|fake|demo|ornek|örnek|sahte)$/iu',$tracking),'TRACKING_REQUIRED','Taşıyıcı ve gerçek takip numarasını girin.',400);
        return (new Audit($this->db))->command($actor,$key,['ship',$task,$carrier,$tracking],function()use($task,$carrier,$tracking,$actor){$t=$this->task($task);RuleViolation::ensure($t['status']==='packed','PACKAGE_NOT_PACKED','Paketleme doğrulaması tamamlanmadı.');$this->assertLots($t['order_id']);$o=$this->db->one('SELECT address FROM orders WHERE id=?',[$t['order_id']]);$country=json_decode($o['address'],true)['country'];$rows=$this->db->all('SELECT i.*,o.snapshot,o.fulfillment_group_id FROM fulfillment_task_items i JOIN order_items o ON o.variant_id=i.variant_id AND o.order_id=? WHERE i.task_id=? ORDER BY i.variant_id',[$t['order_id'],$task]);
            foreach($rows as $r){RuleViolation::ensure((int)$r['packed_quantity']===(int)$r['quantity'],'PACKAGE_NOT_PACKED','Paket adedi doğrulanmadı.');$snap=json_decode($r['snapshot'],true);$ids=array_column($snap['bundleComponents']??[],'variantId')?:[$r['variant_id']];foreach($ids as $v){$restricted=$this->db->one('SELECT battery_type,liquid FROM variants WHERE id=?',[$v]);if(!empty($restricted['battery_type'])||!empty($restricted['liquid']))RuleViolation::ensure($this->db->one('SELECT variant_id FROM shipping_approvals WHERE variant_id=? AND country=? AND carrier=LOWER(?) AND accepted=true AND reviewed_by IS NOT NULL AND CHAR_LENGTH(TRIM(reference))>0 AND(valid_until IS NULL OR valid_until>CURRENT_TIMESTAMP(3)) FOR SHARE',[$v,$country,$carrier]),'CARRIER_ACCEPTANCE_REQUIRED','Bu taşıyıcı için ürün kabulü doğrulanmadı.');}}
            $id=Database::id();$this->db->execute('INSERT INTO shipments(id,order_id,fulfillment_group_id,carrier,tracking_number) VALUES(?,?,?,?,?)',[$id,$t['order_id'],$rows[0]['fulfillment_group_id'],$carrier,$tracking]);foreach($rows as $r)$this->db->execute('INSERT INTO shipment_items(shipment_id,variant_id,quantity) VALUES(?,?,?)',[$id,$r['variant_id'],$r['quantity']]);$all=$this->db->all('SELECT variant_id,quantity,fulfillment_source FROM order_items WHERE order_id=?',[$t['order_id']]);$complete=true;$own=true;foreach($all as $line){$sent=$this->sent($t['order_id'],$line['variant_id']);RuleViolation::ensure($sent<=(int)$line['quantity'],'SHIPMENT_QUANTITY','Sevk adedi siparişi aşıyor.');if($sent!==(int)$line['quantity']){$complete=false;if($line['fulfillment_source']==='warehouse')$own=false;}}$status=$complete?'shipped':'partially_shipped';$this->db->execute('UPDATE orders SET status=?,fulfillment_status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$status,$status,$t['order_id']]);$this->db->execute("UPDATE order_fulfillment_groups SET status=?,updated_at=CURRENT_TIMESTAMP(3) WHERE order_id=? AND source='warehouse'",[$own?'shipped':'partially_shipped',$t['order_id']]);$this->db->execute("UPDATE fulfillment_tasks SET status='shipped',shipment_id=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?",[$id,$task]);(new Audit($this->db))->record($actor,'ship','shipments',$id);return ['id'=>$id,'status'=>$status];});
    }
    public function detail(string $id,Principal $actor):array
    {
        $actor->require('orders');$warehouse=$actor->role==='warehouse';
        $financial=in_array($actor->role,['admin','finance'],true);$shipping=in_array($actor->role,['admin','warehouse','support'],true);
        $scope=$warehouse?" AND EXISTS(SELECT 1 FROM order_items own WHERE own.order_id=orders.id AND own.fulfillment_source='warehouse')":'';
        $o=$this->db->one('SELECT id,number,status,payment_status,fulfillment_status,created_at'.($shipping?',address':'').($financial?',currency,total_minor,cost_minor':'').' FROM orders WHERE id=?'.$scope,[$id]);
        RuleViolation::ensure($o,'ORDER_NOT_FOUND','Sipariş bulunamadı.',404);if(isset($o['address']))$o['address']=json_decode($o['address'],true);
        $o['items']=$this->db->all('SELECT variant_id,name,sku,quantity,fulfillment_source'.($financial?',unit_minor,cost_minor':'').' FROM order_items WHERE order_id=?'.($warehouse?" AND fulfillment_source='warehouse'":''),[$id]);
        $o['tasks']=$this->db->all('SELECT id,status,shipment_id FROM fulfillment_tasks WHERE order_id=? ORDER BY created_at',[$id]);
        foreach($o['tasks'] as &$t)$t['items']=$this->db->all('SELECT i.*,v.sku,v.barcode FROM fulfillment_task_items i JOIN variants v ON v.id=i.variant_id WHERE task_id=?',[$t['id']]);unset($t);
        $o['shipments']=$this->db->all('SELECT s.id,s.carrier,s.tracking_number,s.status FROM shipments s LEFT JOIN order_fulfillment_groups g ON g.id=s.fulfillment_group_id WHERE s.order_id=?'.($warehouse?" AND g.source='warehouse'":'').' ORDER BY s.created_at',[$id]);return $o;
    }

}
