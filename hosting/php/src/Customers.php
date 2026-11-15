<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Customers.php
 * Açıklama   : Kayıt sahipliğiyle adres/favori/tercihler ve deterministik sunucu sepeti birleşmesi.
 */
declare(strict_types=1);
namespace Sexogate;
final class Customers
{
    public function __construct(private Database $db,private Config $config){}
    private function user(string $id,bool $lock=false):void
    {RuleViolation::ensure($id!==''&&$this->db->one('SELECT id FROM `user` WHERE id=?'.($lock?' FOR UPDATE':''),[$id]),'AUTH_REQUIRED','Giriş yapın.',401);}
    public function addresses(string $user):array
    {$this->user($user);$rows=$this->db->all('SELECT id,label,country,fields,created_at FROM customer_addresses WHERE user_id=? ORDER BY created_at,id LIMIT 50',[$user]);foreach($rows as &$r)$r['fields']=json_decode($r['fields'],true);return $rows;}
    public function saveAddress(string $user,array $input):array
    {$this->user($user);$label=trim($input['label']??'');RuleViolation::ensure(mb_strlen($label)>=1&&mb_strlen($label)<=100,'ADDRESS_LABEL_INVALID','Adres adı gerekir.',400);$policy=new CheckoutPolicy($this->db,$this->config);return $this->db->transaction(function()use($user,$input,$label,$policy){$this->user($user,true);$id=$input['id']??Database::id();$existing=isset($input['id'])?$this->db->one('SELECT id FROM customer_addresses WHERE id=? AND user_id=? FOR UPDATE',[$id,$user]):null;if(isset($input['id']))RuleViolation::ensure($existing,'ADDRESS_NOT_FOUND','Adres bulunamadı.',404);$profile=$policy->profile($input['country']??'');$fields=$policy->address($input,$profile);if($existing)$this->db->execute('UPDATE customer_addresses SET label=?,country=?,fields=?,profile_id=? WHERE id=? AND user_id=?',[$label,$profile['country'],$this->config->json($fields),$profile['id'],$id,$user]);else{RuleViolation::ensure((int)$this->db->one('SELECT COUNT(*) n FROM customer_addresses WHERE user_id=?',[$user])['n']<50,'ADDRESS_LIMIT','En fazla50 adres kaydedilebilir.');$this->db->execute('INSERT INTO customer_addresses(id,user_id,label,fields,country,profile_id) VALUES(?,?,?,?,?,?)',[$id,$user,$label,$this->config->json($fields),$profile['country'],$profile['id']]);}return ['id'=>$id];});}
    public function deleteAddress(string $user,string $id):void
    {$this->user($user);RuleViolation::ensure($this->db->execute('DELETE FROM customer_addresses WHERE id=? AND user_id=?',[$id,$user])===1,'ADDRESS_NOT_FOUND','Adres bulunamadı.',404);}
    public function favorite(string $user,string $product,bool $selected):array
    {$this->user($user);return (new PersonalShopping($this->db,$this->config))->legacyFavorite($user,$product,$selected);}
    public function favorites(string $user):array
    {$this->user($user);return $this->db->all("SELECT p.id,p.name,p.name_en,p.slug,p.image FROM favorites f JOIN products p ON p.id=f.product_id WHERE f.user_id=? AND p.status='published' AND(p.fixture=false OR ?=true) ORDER BY p.name LIMIT 200",[$user,$this->config->local()?1:0]);}
    public function preferences(string $user):array
    {$this->user($user);$r=$this->db->one('SELECT marketing,analytics,private_notifications FROM customer_preferences WHERE user_id=?',[$user]);return ['marketing'=>(bool)($r['marketing']??false),'analytics'=>(bool)($r['analytics']??false),'privateNotifications'=>(bool)($r['private_notifications']??true)];}
    public function setPreferences(string $user,array $input):array
    {$this->user($user);foreach(['marketing','analytics','privateNotifications'] as $key)RuleViolation::ensure(is_bool($input[$key]??null),'INVALID_PREFERENCES','İzin alanlarını açıkça seçin.',400);$v=array_intersect_key($input,array_flip(['marketing','analytics','privateNotifications']));return $this->db->transaction(function()use($user,$v){$this->db->execute('INSERT INTO customer_preferences(user_id,marketing,analytics,private_notifications) VALUES(?,?,?,?) ON DUPLICATE KEY UPDATE marketing=?,analytics=?,private_notifications=?,updated_at=CURRENT_TIMESTAMP(3)',[$user,(int)$v['marketing'],(int)$v['analytics'],(int)$v['privateNotifications'],(int)$v['marketing'],(int)$v['analytics'],(int)$v['privateNotifications']]);$this->db->execute('INSERT INTO consent_events(id,user_id,preferences,policy_version) VALUES(?,?,?,?)',[Database::id(),$user,$this->config->json($v),'privacy-preferences-v1']);return $v;});}
    public function mergeCart(string $anonymous,string $newToken,string $user):array
    {
        $hash=Cart::token($newToken);Cart::token($anonymous);RuleViolation::ensure($anonymous!==$newToken,'CART_ROTATION_REQUIRED','Girişte sepet anahtarı yenilenmelidir.');return $this->db->transaction(function()use($anonymous,$hash,$user){$this->user($user,true);$cart=new Cart($this->db,$this->config);$source=$cart->row($anonymous,null,true);RuleViolation::ensure(!$this->db->one("SELECT id FROM orders WHERE cart_id=? AND status='awaiting_payment' AND expires_at>CURRENT_TIMESTAMP(3)",[$source['id']]),'CART_CHECKOUT_ACTIVE','Ödemesi devam eden sepet birleştirilemez.');$target=$this->db->one("SELECT c.id FROM carts c WHERE c.user_id=? AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=c.id AND o.status='awaiting_payment' AND o.expires_at>CURRENT_TIMESTAMP(3)) ORDER BY c.updated_at DESC,c.id LIMIT 1 FOR UPDATE",[$user]);
            if(!$target){$this->db->execute('UPDATE carts SET user_id=?,token_hash=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$user,$hash,$source['id']]);return ['merged'=>true,'capped'=>false];}
            $rows=$this->db->all('SELECT variant_id,quantity FROM cart_items WHERE cart_id=? ORDER BY variant_id',[$source['id']]);$capped=false;foreach($rows as $row){$existing=$this->db->one('SELECT quantity FROM cart_items WHERE cart_id=? AND variant_id=? FOR UPDATE',[$target['id'],$row['variant_id']]);$sum=(int)($existing['quantity']??0)+(int)$row['quantity'];RuleViolation::ensure($sum<=99,'CART_MERGE_LIMIT','Sepetler birleştirilince bir ürün99 adedi aşıyor. Sepet adedini düzenleyip yeniden deneyin.');$q=$sum;$this->db->execute('INSERT INTO cart_items(cart_id,variant_id,quantity) VALUES(?,?,?) ON DUPLICATE KEY UPDATE quantity=?',[$target['id'],$row['variant_id'],$q,$q]);}$this->db->execute('DELETE FROM cart_items WHERE cart_id=?',[$source['id']]);$this->db->execute('UPDATE carts SET token_hash=?,updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$hash,$target['id']]);return ['merged'=>true,'capped'=>$capped];});
    }
}
