<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/PersonalShopping.php
 * Açıklama   : Anonim/hesap favorileri, sürümlü özel listeler, karşılaştırma ve açık aktarım.
 */
declare(strict_types=1);
namespace Sexogate;
final class PersonalShopping
{
    public function __construct(private Database $db,private Config $config){}
    public static function guestKey(string $token):string{return 'g:'.Cart::token($token);}
    private function owner(string $token,?string $user):string
    {
        (new Cart($this->db,$this->config))->row($token,$user);
        if($user!==null)RuleViolation::ensure($this->db->one('SELECT id FROM `user` WHERE id=?',[$user]),'AUTH_REQUIRED','Giriş yapın.',401);
        return $user===null?self::guestKey($token):'u:'.$user;
    }
    private function empty(?string $user):array
    {return ['version'=>0,'favorites'=>$user===null?[]:array_column($this->db->all('SELECT product_id FROM favorites WHERE user_id=? ORDER BY product_id',[$user]),'product_id'),'compare'=>[],'lists'=>[]];}
    private function read(string $key,?string $user,bool $lock=false):array
    {
        $r=$this->db->one('SELECT version,payload,expires_at<=CURRENT_TIMESTAMP(3) expired FROM shopping_states WHERE owner_key=?'.($lock?' FOR UPDATE':''),[$key]);
        if(!$r)return $this->empty($user);
        if((bool)$r['expired'])return ['version'=>(int)$r['version']]+$this->empty($user);
        return ['version'=>(int)$r['version']]+json_decode($r['payload'],true,32,JSON_THROW_ON_ERROR);
    }
    private function locked(string $key,?string $user):array
    {
        $initial=$this->empty($user);unset($initial['version']);
        $this->db->execute('INSERT INTO shopping_states(owner_key,user_id,payload,expires_at) VALUES(?,?,?,'.($user===null?'DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 7 DAY)':'NULL').') ON DUPLICATE KEY UPDATE owner_key=owner_key',[$key,$user,$this->config->json($initial)]);
        $row=$this->db->one('SELECT expires_at,expires_at<=CURRENT_TIMESTAMP(3) expired FROM shopping_states WHERE owner_key=? FOR UPDATE',[$key]);
        if((bool)$row['expired'])$this->db->execute('UPDATE shopping_states SET payload=?,expires_at=DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 7 DAY) WHERE owner_key=?',[$this->config->json($initial),$key]);
        return $this->read($key,$user,true);
    }
    public function get(string $token,?string $user=null):array{return $this->read($this->owner($token,$user),$user);}
    public function purgeExpired():int
    {
        // Ürün tercihleri silinir; eski istemci sürümünün yeniden geçerli olmaması için hash/sürüm korunur.
        return $this->db->execute("UPDATE shopping_states SET payload=?,version=version+1,updated_at=CURRENT_TIMESTAMP(3) WHERE user_id IS NULL AND expires_at<=CURRENT_TIMESTAMP(3) AND(COALESCE(JSON_LENGTH(payload,'$.favorites'),0)>0 OR COALESCE(JSON_LENGTH(payload,'$.compare'),0)>0 OR COALESCE(JSON_LENGTH(payload,'$.lists'),0)>0) ORDER BY owner_key LIMIT 1000",[$this->config->json(['favorites'=>[],'compare'=>[],'lists'=>[]])]);
    }
    private function lockUser(?string $user):void{if($user!==null)RuleViolation::ensure($this->db->one('SELECT id FROM `user` WHERE id=? FOR UPDATE',[$user]),'AUTH_REQUIRED','Giriş yapın.',401);}
    public function legacyFavorite(string $user,string $id,bool $selected):array
    {
        return $this->db->transaction(function()use($user,$id,$selected){$this->lockUser($user);$key='u:'.$user;$s=$this->locked($key,$user);if($selected){$this->published([$id]);$s['favorites']=array_values(array_unique([...$s['favorites'],$id]));}else $s['favorites']=array_values(array_diff($s['favorites'],[$id]));$this->save($key,$user,$s);return ['selected'=>$selected];});
    }
    private function version(array $state,mixed $version):void
    {RuleViolation::ensure(is_int($version)&&$version===$state['version'],'SHOPPING_CHANGED','Listeniz başka bir işlemle değişti. Güncel listeyi yeniden inceleyin.',409);}
    private function ids(mixed $ids):array
    {RuleViolation::ensure(is_array($ids)&&array_is_list($ids)&&count($ids)<=200,'INVALID_SELECTION','Ürün seçimini kontrol edin.',400);foreach($ids as $id)RuleViolation::ensure(is_string($id)&&$id!==''&&strlen($id)<=128,'INVALID_SELECTION','Ürün seçimini kontrol edin.',400);return array_values(array_unique($ids));}
    private function published(array $ids):void
    {if(!$ids)return;$found=$this->db->all("SELECT id FROM products WHERE id IN(".Database::slots($ids).") AND status='published' AND(fixture=false OR ?=true)",array_merge($ids,[$this->config->local()?1:0]));RuleViolation::ensure(count($found)===count($ids),'PRODUCT_UNAVAILABLE','Seçili ürünlerden biri artık yayında değil.');}
    private function name(mixed $name):string
    {RuleViolation::ensure(is_string($name)&&mb_strlen(trim($name))>=1&&mb_strlen(trim($name))<=60&&!preg_match('/[\x00-\x1f\x7f]/u',$name),'INVALID_LIST_NAME','Liste adı1–60 karakter olmalı ve kontrol karakteri içermemelidir.',400);return trim($name);}
    private function limits(array $state):void
    {RuleViolation::ensure(count($state['favorites'])<=200,'FAVORITES_LIMIT','En fazla200 favori kaydedebilirsiniz.');RuleViolation::ensure(count($state['compare'])<=4,'COMPARE_LIMIT','Aynı anda en fazla4 ürün karşılaştırabilirsiniz.');RuleViolation::ensure(count($state['lists'])<=20,'LIST_LIMIT','En fazla20 özel liste oluşturabilirsiniz.');$total=0;foreach($state['lists'] as $l){RuleViolation::ensure(count($l['items'])<=100,'LIST_ITEM_LIMIT','Bir listede en fazla100 ürün bulunabilir.');$total+=count($l['items']);}RuleViolation::ensure($total<=1000,'LIST_TOTAL_LIMIT','Listelerinizde toplam en fazla1000 ürün bulunabilir.');}
    private function save(string $key,?string $user,array $state):array
    {
        $this->limits($state);$version=$state['version']+1;unset($state['version']);
        $this->db->execute('UPDATE shopping_states SET payload=?,version=?,updated_at=CURRENT_TIMESTAMP(3),expires_at='.($user===null?'DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 7 DAY)':'NULL').' WHERE owner_key=?',[$this->config->json($state),$version,$key]);
        if($user!==null){$this->db->execute('DELETE FROM favorites WHERE user_id=?',[$user]);foreach($state['favorites'] as $id)$this->db->execute('INSERT INTO favorites(user_id,product_id) VALUES(?,?)',[$user,$id]);}
        return ['version'=>$version]+$state;
    }
    public function command(string $token,array $i,?string $user=null):array
    {
        return $this->db->transaction(function()use($token,$i,$user){
            $this->lockUser($user);(new Cart($this->db,$this->config))->row($token,$user,true);$key=$this->owner($token,$user);$s=$this->locked($key,$user);$this->version($s,$i['version']??null);$action=$i['action']??'';
            if(in_array($action,['favorite','compare'],true)){
                $ids=$this->ids([$i['productId']??null]);$id=$ids[0];$field=$action==='favorite'?'favorites':'compare';RuleViolation::ensure(is_bool($i['selected']??null),'INVALID_SELECTION','Seçimi açıkça belirtin.',400);
                if($i['selected']){$this->published([$id]);$s[$field]=array_values(array_unique([...$s[$field],$id]));}else $s[$field]=array_values(array_diff($s[$field],[$id]));
            }elseif($action==='compare-clear')$s['compare']=[];
            elseif($action==='list-create'){$items=$this->ids($i['productIds']??[]);$this->published($items);$s['lists'][]=['id'=>bin2hex(random_bytes(16)),'name'=>$this->name($i['name']??null),'items'=>$items];}
            elseif(in_array($action,['list-rename','list-remove','list-add','list-remove-items'],true)){
                $index=array_search($i['listId']??null,array_column($s['lists'],'id'),true);RuleViolation::ensure($index!==false,'LIST_NOT_FOUND','Liste bulunamadı.',404);
                if($action==='list-rename')$s['lists'][$index]['name']=$this->name($i['name']??null);
                elseif($action==='list-remove')array_splice($s['lists'],$index,1);
                else{$ids=$this->ids($i['productIds']??null);if($action==='list-add'){$this->published($ids);$s['lists'][$index]['items']=array_values(array_unique([...$s['lists'][$index]['items'],...$ids]));}else $s['lists'][$index]['items']=array_values(array_diff($s['lists'][$index]['items'],$ids));}
            }else throw new RuleViolation('UNKNOWN_ACTION','Alışveriş işlemi bulunamadı.',400);
            return $this->save($key,$user,$s);
        });
    }
    public function addToCart(string $token,array $i,?string $user=null):array
    {
        return $this->db->transaction(function()use($token,$i,$user){
            $this->lockUser($user);$cartService=new Cart($this->db,$this->config);$cart=$cartService->row($token,$user,true);$s=$this->locked($this->owner($token,$user),$user);$this->version($s,$i['version']??null);$source=$i['source']??'';
            if($source==='favorites')$allowed=$s['favorites'];else{$n=array_search($i['listId']??null,array_column($s['lists'],'id'),true);RuleViolation::ensure($source==='list'&&$n!==false,'LIST_NOT_FOUND','Liste bulunamadı.',404);$allowed=$s['lists'][$n]['items'];}
            $ids=$this->ids($i['productIds']??[]);RuleViolation::ensure($ids&&count($ids)<=100&&!array_diff($ids,$allowed),'INVALID_SELECTION','Seçili ürünler bu listede bulunmalıdır.',400);$this->published($ids);$choices=$i['variants']??[];RuleViolation::ensure(is_array($choices),'INVALID_VARIANT','Ürün seçeneklerini kontrol edin.',400);$insert=[];
            foreach($ids as $id){$rows=$this->db->all('SELECT id FROM variants WHERE product_id=? AND active=true ORDER BY id',[$id]);$target=$choices[$id]??(count($rows)===1?$rows[0]['id']:null);RuleViolation::ensure(is_string($target)&&in_array($target,array_column($rows,'id'),true),'VARIANT_REQUIRED','Beden, renk veya ürün seçeneğini belirleyin.',400);if($this->db->one('SELECT variant_id FROM cart_items WHERE cart_id=? AND variant_id=?',[$cart['id'],$target]))continue;RuleViolation::ensure((new Inventory($this->db,$this->config))->available($target)>0,'INSUFFICIENT_STOCK','Seçili ürünlerden biri stokta yok.');$insert[]=$target;}
            $count=(int)$this->db->one('SELECT COUNT(*) n FROM cart_items WHERE cart_id=?',[$cart['id']])['n'];RuleViolation::ensure($count+count($insert)<=100,'CART_LIMIT','Sepette en fazla100 seçenek bulunabilir.');foreach($insert as $id)$this->db->execute('INSERT INTO cart_items(cart_id,variant_id,quantity,selected) VALUES(?,?,1,true)',[$cart['id'],$id]);$this->db->execute('UPDATE carts SET updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$cart['id']]);return $cartService->project($cart,'TRY')+['added'=>count($insert)];
        });
    }
    public function transferPreview(string $guestKey,string $token,string $user):array
    {RuleViolation::ensure(str_starts_with($guestKey,'g:')&&strlen($guestKey)===66,'TRANSFER_UNAVAILABLE','Aktarım bulunamadı.',404);return ['source'=>$this->read($guestKey,null),'target'=>$this->get($token,$user)];}
    public function transfer(string $guestKey,string $token,string $user,array $i):array
    {
        RuleViolation::ensure(($i['confirmed']??false)===true,'TRANSFER_CONSENT_REQUIRED','Cihazdaki favori ve listelerin aktarımını açıkça onaylayın.',400);
        return $this->db->transaction(function()use($guestKey,$token,$user,$i){
            $this->lockUser($user);$key=$this->owner($token,$user);RuleViolation::ensure(str_starts_with($guestKey,'g:')&&strlen($guestKey)===66,'TRANSFER_UNAVAILABLE','Aktarım bulunamadı.',404);$keys=[$key,$guestKey];sort($keys,SORT_STRING);$states=[];foreach($keys as $k)$states[$k]=$this->locked($k,$k===$key?$user:null);$target=$states[$key];$source=$states[$guestKey];$this->version($target,$i['version']??null);$this->version($source,$i['sourceVersion']??null);
            $target['favorites']=array_values(array_unique([...$target['favorites'],...$source['favorites']]));foreach($source['lists'] as $list){$n=array_search($list['id'],array_column($target['lists'],'id'),true);if($n===false)$target['lists'][]=$list;else $target['lists'][$n]['items']=array_values(array_unique([...$target['lists'][$n]['items'],...$list['items']]));}$result=$this->save($key,$user,$target);$source['favorites']=[];$source['lists']=[];$this->save($guestKey,null,$source);return $result;
        });
    }
    public function workspace(string $token,?string $user,string $view,string $listId='',string $currency='TRY',string $locale='tr'):array
    {
        RuleViolation::ensure(in_array($view,['favorites','compare','lists'],true),'NOT_FOUND','Sayfa bulunamadı.',404);$state=$this->get($token,$user);$active=null;$ids=[];
        if($view==='lists'){foreach($state['lists'] as $list)if($list['id']===$listId)$active=$list;if($listId!=='')RuleViolation::ensure($active,'LIST_NOT_FOUND','Liste bulunamadı.',404);if(!$active)$active=$state['lists'][0]??null;$ids=$active['items']??[];}else $ids=$state[$view==='compare'?'compare':'favorites'];
        $products=(new CatalogReader($this->db,$this->config))->byIds($ids,$currency);$comparison=[];
        if($view==='compare'){
            $definitions=[['price',$locale==='tr'?'Fiyat':'Price'],['sku','SKU'],['brand',$locale==='tr'?'Marka':'Brand'],['material',$locale==='tr'?'Malzeme':'Material'],['sizes',$locale==='tr'?'Beden':'Size'],['colors',$locale==='tr'?'Renk':'Colour'],['manufacturer',$locale==='tr'?'Üretici':'Manufacturer'],['origin',$locale==='tr'?'Menşe':'Origin']];
            foreach($definitions as [$field,$label]){$values=[];foreach($products as $p){$v=$p['variants'][0]??null;$values[]=match($field){'price'=>$v&&$v['price_available']?Money::format($v['display_price_minor'],$currency,$locale):'—','sku'=>implode(', ',array_column($p['variants'],'sku')),'sizes'=>implode(', ',array_unique(array_filter(array_column($p['variants'],'size')))),'colors'=>implode(', ',array_unique(array_filter(array_column($p['variants'],'color')))),default=>$p[$field]?:'—'};}$comparison[]=['label'=>$label,'values'=>$values,'different'=>count(array_unique($values))>1];}
        }
        return ['view'=>$view,'shopping'=>$state,'products'=>$products,'activeList'=>$active,'unavailableCount'=>count($ids)-count($products),'comparison'=>$comparison];
    }
}
