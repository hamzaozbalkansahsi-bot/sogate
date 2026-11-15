<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Availability.php
 * Açıklama   : Depo/lot/set ve doğrulanmış tedarikçi stoklarını tek toplu sorguda hesaplar.
 */
declare(strict_types=1);
namespace Sexogate;
final class Availability
{
    public function __construct(private Database $db,private Config $config){}
    public function query(?array $ids=null,string $country='TR',string $currency='TRY'):array
    {
        $condition=$ids===null?'':' WHERE v.id IN('.Database::slots($ids).')';
        $sql="WITH req AS(SELECT v.id,v.fulfillment_mode,v.lot_tracking FROM variants v$condition),
         parts AS(SELECT r.id target,b.component_variant_id id,b.quantity FROM req r JOIN bundle_components b ON b.bundle_variant_id=r.id UNION ALL SELECT r.id,r.id,1 FROM req r WHERE NOT EXISTS(SELECT 1 FROM bundle_components b WHERE b.bundle_variant_id=r.id)),
         held AS(SELECT variant_id,SUM(quantity) qty FROM reservations WHERE warehouse_id='main' AND status='active' AND expires_at>CURRENT_TIMESTAMP(3) AND variant_id IN(SELECT id FROM parts) GROUP BY variant_id),
         lot_held AS(SELECT rl.lot_id,SUM(rl.quantity) qty FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.warehouse_id='main' AND r.status='active' AND r.expires_at>CURRENT_TIMESTAMP(3) AND r.variant_id IN(SELECT id FROM parts) GROUP BY rl.lot_id),
         lot_stock AS(SELECT l.variant_id,SUM(GREATEST(0,lb.on_hand-COALESCE(h.qty,0))) available FROM inventory_lots l JOIN inventory_lot_balances lb ON lb.lot_id=l.id AND lb.warehouse_id='main' LEFT JOIN lot_held h ON h.lot_id=l.id WHERE l.quarantined=false AND l.recall_reference IS NULL AND(l.expires_at IS NULL OR l.expires_at>?) AND l.variant_id IN(SELECT id FROM parts) GROUP BY l.variant_id),
         own_stock AS(SELECT p.target,COALESCE(MIN(FLOOR(GREATEST(0,CASE WHEN v.lot_tracking=true THEN LEAST(COALESCE(l.available,0),COALESCE(b.on_hand,0)-COALESCE(h.qty,0))-COALESCE(b.safety_stock,0) ELSE COALESCE(b.on_hand,0)-COALESCE(b.safety_stock,0)-COALESCE(h.qty,0) END)/p.quantity)),0) available FROM parts p JOIN variants v ON v.id=p.id LEFT JOIN inventory_balance b ON b.variant_id=p.id AND b.warehouse_id='main' LEFT JOIN held h ON h.variant_id=p.id LEFT JOIN lot_stock l ON l.variant_id=p.id GROUP BY p.target),
         supplied AS(SELECT a.variant_id,MAX(a.available) available FROM supplier_offer_availability a JOIN req r ON r.id=a.variant_id WHERE a.country=? AND a.currency=? AND(a.fixture=false OR ?=true) AND r.lot_tracking=false AND NOT EXISTS(SELECT 1 FROM bundle_components b WHERE b.bundle_variant_id=r.id) GROUP BY a.variant_id)
         SELECT r.id,CASE r.fulfillment_mode WHEN 'warehouse' THEN COALESCE(o.available,0) WHEN 'dropship' THEN COALESCE(s.available,0) ELSE GREATEST(COALESCE(o.available,0),COALESCE(s.available,0)) END available FROM req r LEFT JOIN own_stock o ON o.target=r.id LEFT JOIN supplied s ON s.variant_id=r.id";
        $day=(new \DateTimeImmutable('now',new \DateTimeZone('Europe/Istanbul')))->format('Y-m-d');
        return [$sql,array_merge($ids??[],[$day,$country,$currency,$this->config->local()?1:0])];
    }
    public function many(array $ids,string $country='TR',string $currency='TRY'):array
    {if(!$ids)return [];[$sql,$args]=$this->query(array_values(array_unique($ids)),$country,$currency);$out=[];foreach($this->db->all($sql,$args) as $r)$out[$r['id']]=(int)$r['available'];return $out;}
}
