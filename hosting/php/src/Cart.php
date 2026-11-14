<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Cart.php
 * Açıklama   : Hashlenmiş anonim token, kayıt sahipliği ve sunucu fiyatlı sepet.
 */
declare(strict_types=1);
namespace Sexogate;
final class Cart
{
    public function __construct(private Database $db,private Config $config){}
    public static function token(string $token):string{RuleViolation::ensure((bool)preg_match('/\A[A-Za-z0-9_-]{32,128}\z/',$token),'INVALID_CART','Sepet anahtarı geçersiz.',401);return hash('sha256',$token);}
    public function row(string $token,?string $caller=null,bool $lock=false,bool $create=true):array
    {
        $hash=self::token($token);if($create)$this->db->execute('INSERT INTO carts(token_hash) VALUES(?) ON DUPLICATE KEY UPDATE token_hash=token_hash',[$hash]);$row=$this->db->one('SELECT id,user_id,currency FROM carts WHERE token_hash=?'.($lock?' FOR UPDATE':''),[$hash]);
        RuleViolation::ensure($row&&($row['user_id']===null||$row['user_id']===$caller),'CART_NOT_FOUND','Sepet bulunamadı. Sepetinizi yenileyin.',404);return $row;
    }
    public function get(string $token,string $currency='TRY',?string $caller=null):array
    {RuleViolation::ensure(in_array($currency,['TRY','EUR','USD','GBP'],true),'INVALID_CURRENCY','Para birimi desteklenmiyor.',400);$this->row($token,$caller);return $this->db->transaction(fn()=> $this->project($this->row($token,$caller,false,false),$currency),true);}
    public function set(string $token,string $variant,int $quantity,?string $caller=null):array
    {return (new ShoppingCart($this->db,$this->config))->command($token,['action'=>'set','variantId'=>$variant,'quantity'=>$quantity],$caller,true);}
    public function project(array $cart,string $currency):array
    {
        $rows=$this->db->all('SELECT ci.variant_id variantId,ci.quantity,ci.selected,p.id productId,p.slug,p.name productName,p.name_en productNameEn,v.name variantName,v.name_en variantNameEn,p.image,v.price_minor priceMinor,vp.amount_minor displayPriceMinor FROM cart_items ci JOIN variants v ON v.id=ci.variant_id JOIN products p ON p.id=v.product_id LEFT JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=? AND vp.amount_minor>0 AND vp.valid_from<=CURRENT_TIMESTAMP(3) AND(vp.valid_until IS NULL OR vp.valid_until>CURRENT_TIMESTAMP(3)) WHERE ci.cart_id=? AND(p.fixture=false OR ?=true) ORDER BY p.name,v.name',[$currency,$cart['id'],$this->config->local()?1:0]);$totals=[];$display=[];$complete=true;$inventory=new Inventory($this->db,$this->config);
        foreach($rows as &$r){$r['selected']=(bool)$r['selected'];$r['options']=$this->db->all('SELECT id,name,name_en,color,size,price_minor,currency FROM variants WHERE product_id=? AND active=true ORDER BY name',[$r['productId']]);$r['priceMinor']=(int)$r['priceMinor'];$r['quantity']=(int)$r['quantity'];$r['displayPriceMinor']=$r['displayPriceMinor']===null?null:(int)$r['displayPriceMinor'];$r['available']=$inventory->available($r['variantId']);if($r['selected']){$totals[]=Money::multiply($r['priceMinor'],$r['quantity']);if($r['displayPriceMinor']===null)$complete=false;else $display[]=Money::multiply($r['displayPriceMinor'],$r['quantity']);}}unset($r);
        return ['id'=>$cart['id'],'revision'=>ShoppingCart::revision((new ShoppingCart($this->db,$this->config))->raw($cart['id'])),'count'=>array_sum(array_column($rows,'quantity')),'selectedCount'=>count(array_filter($rows,fn($r)=>$r['selected'])),'items'=>$rows,'subtotalMinor'=>Money::sum($totals),'currency'=>$cart['currency'],'displayCurrency'=>$currency,'displaySubtotalMinor'=>$complete?Money::sum($display):null,'pricesComplete'=>$complete];
    }
}
