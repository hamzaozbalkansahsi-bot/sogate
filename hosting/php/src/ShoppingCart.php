<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/ShoppingCart.php
 * Açıklama   : NODENO sepet davranışlarının sahiplikli, atomik ve sürüm korumalı sunucu karşılığı.
 */
declare(strict_types=1);
namespace Sexogate;
final class ShoppingCart
{
    public function __construct(private Database $db,private Config $config){}
    public function raw(string $id):array{return $this->db->all('SELECT variant_id,quantity,selected FROM cart_items WHERE cart_id=? ORDER BY variant_id',[$id]);}
    public static function revision(array $rows):string
    {$clean=array_map(fn($r)=>['id'=>$r['variant_id'],'q'=>(int)$r['quantity'],'selected'=>(bool)$r['selected']],$rows);usort($clean,fn($a,$b)=>strcmp($a['id'],$b['id']));return hash('sha256',json_encode($clean,JSON_THROW_ON_ERROR));}
    private function validate(string $variant,int $quantity):void
    {RuleViolation::ensure($quantity>=1&&$quantity<=99,'INVALID_QUANTITY','Adet 1 ile 99 arasında olmalıdır.',400);RuleViolation::ensure($this->db->one("SELECT v.id FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=? AND v.active=true AND p.status='published' AND(p.fixture=false OR ?=true)",[$variant,$this->config->local()?1:0]),'PRODUCT_UNAVAILABLE','Ürün satışa açık değil.');RuleViolation::ensure((new Inventory($this->db,$this->config))->available($variant)>=$quantity,'INSUFFICIENT_STOCK','İstenen adet stokta yok.');}
    private function write(string $cart,string $variant,int $quantity,bool $selected=true):void
    {$this->validate($variant,$quantity);$this->db->execute('INSERT INTO cart_items(cart_id,variant_id,quantity,selected) VALUES(?,?,?,?) ON DUPLICATE KEY UPDATE quantity=VALUES(quantity),selected=VALUES(selected)',[$cart,$variant,$quantity,(int)$selected]);}
    public function command(string $token,array $input,?string $caller=null,bool $legacy=false):array
    {
        return $this->db->transaction(function()use($token,$input,$caller,$legacy){
            $cartService=new Cart($this->db,$this->config);$cart=$cartService->row($token,$caller,true);$id=$cart['id'];$before=$this->raw($id);$revision=self::revision($before);$action=$input['action']??'';RuleViolation::ensure(in_array($action,['add','set','remove','clear','replace','select','undo'],true),'UNKNOWN_ACTION','Sepet işlemi bulunamadı.',400);
            if(!in_array($action,['add','undo'],true)&&!$legacy)RuleViolation::ensure(is_string($input['revision']??null)&&hash_equals($revision,$input['revision']),'CART_CHANGED','Sepet başka bir işlemle değişti. Güncel sepeti yeniden inceleyin.');
            $map=array_column($before,null,'variant_id');$variant=$input['variantId']??'';RuleViolation::ensure(is_string($variant)&&strlen($variant)<=128,'INVALID_VARIANT','Ürün seçimini kontrol edin.',400);$undo=null;
            if($action==='undo'){
                $value=$input['undoToken']??'';RuleViolation::ensure(is_string($value)&&preg_match('/\A[a-f0-9]{64}\z/',$value),'UNDO_UNAVAILABLE','Geri alma artık kullanılamıyor.');$record=$this->db->one('SELECT *,expires_at>CURRENT_TIMESTAMP(3) fresh FROM cart_undo WHERE token_hash=? AND cart_id=? FOR UPDATE',[hash('sha256',$value),$id]);RuleViolation::ensure($record&&(bool)$record['fresh']&&$record['consumed_at']===null,'UNDO_UNAVAILABLE','Geri alma süresi doldu veya işlem daha önce kullanıldı.');RuleViolation::ensure(hash_equals($record['after_revision'],$revision),'CART_CHANGED','Sepet değiştiği için önceki işlem geri alınamaz.');$rows=json_decode($record['before_rows'],true,32,JSON_THROW_ON_ERROR);foreach($rows as $r)$this->validate($r['variant_id'],(int)$r['quantity']);$this->db->execute('DELETE FROM cart_items WHERE cart_id=?',[$id]);foreach($rows as $r)$this->write($id,$r['variant_id'],(int)$r['quantity'],(bool)$r['selected']);$this->db->execute('UPDATE cart_undo SET consumed_at=CURRENT_TIMESTAMP(3) WHERE token_hash=?',[hash('sha256',$value)]);
            }elseif(in_array($action,['add','set'],true)){
                $quantity=$input['quantity']??null;RuleViolation::ensure(is_int($quantity)&&$quantity>=0&&$quantity<=99&&($action!=='add'||$quantity>=1),'INVALID_QUANTITY','Adedi kontrol edin.',400);if($action==='add')$quantity+=(int)($map[$variant]['quantity']??0);if($quantity===0){$this->db->execute('DELETE FROM cart_items WHERE cart_id=? AND variant_id=?',[$id,$variant]);$undo=true;}else $this->write($id,$variant,$quantity,(bool)($map[$variant]['selected']??true));
            }elseif($action==='replace'){
                $target=$input['targetVariantId']??'';RuleViolation::ensure(is_string($target)&&isset($map[$variant]),'INVALID_VARIANT','Sepet seçeneği bulunamadı.',400);$source=$this->db->one('SELECT product_id FROM variants WHERE id=?',[$variant]);$to=$this->db->one('SELECT product_id FROM variants WHERE id=?',[$target]);RuleViolation::ensure($source&&$to&&$source['product_id']===$to['product_id'],'INVALID_VARIANT','Yalnız aynı ürünün seçenekleri değiştirilebilir.',400);if($variant!==$target){$quantity=(int)$map[$variant]['quantity']+(int)($map[$target]['quantity']??0);$selected=(bool)$map[$variant]['selected']||(bool)($map[$target]['selected']??false);$this->write($id,$target,$quantity,$selected);$this->db->execute('DELETE FROM cart_items WHERE cart_id=? AND variant_id=?',[$id,$variant]);}
            }elseif($action==='clear'){$this->db->execute('DELETE FROM cart_items WHERE cart_id=?',[$id]);$undo=true;}
            else{
                $ids=$input['variantIds']??($action==='remove'?[$variant]:[]);RuleViolation::ensure(is_array($ids)&&array_is_list($ids)&&count($ids)<=100,'INVALID_SELECTION','Sepet seçimini kontrol edin.',400);foreach($ids as $v)RuleViolation::ensure(is_string($v)&&isset($map[$v]),'INVALID_SELECTION','Seçili ürün sepette bulunamadı.',400);$ids=array_values(array_unique($ids));
                if($action==='remove'){if($ids)$this->db->execute('DELETE FROM cart_items WHERE cart_id=? AND variant_id IN('.Database::slots($ids).')',array_merge([$id],$ids));$undo=true;}
                else{$this->db->execute('UPDATE cart_items SET selected=false WHERE cart_id=?',[$id]);if($ids)$this->db->execute('UPDATE cart_items SET selected=true WHERE cart_id=? AND variant_id IN('.Database::slots($ids).')',array_merge([$id],$ids));}
            }
            $after=$this->raw($id);RuleViolation::ensure(count($after)<=100,'CART_LIMIT','Sepette en fazla 100 ürün seçeneği olabilir.',400);$result=$cartService->project($cart,'TRY');
            if($undo===true&&$before!==$after){$value=bin2hex(random_bytes(32));$this->db->execute('INSERT INTO cart_undo(token_hash,cart_id,before_rows,after_revision,expires_at) VALUES(?,?,?,?,DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 8 SECOND))',[hash('sha256',$value),$id,$this->config->json($before),self::revision($after)]);$result+=['undoToken'=>$value,'undoSeconds'=>8];}
            $this->db->execute('UPDATE carts SET updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$id]);return $result;
        });
    }
}
