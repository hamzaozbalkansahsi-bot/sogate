<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Catalog.php
 * Açıklama   : PHP kataloğu, varyant/yayın işlemi ve maliyetsiz müşteri/depo projeksiyonları.
 */
declare(strict_types=1);
namespace Sexogate;
final class Catalog
{
    public function __construct(private Database $db,private Config $config){}
    public function validateDraft(array $data):array
    {
        foreach(['name','nameEn','category','sku','variantName'] as $field)RuleViolation::ensure(is_string($data[$field]??null)&&mb_strlen(trim($data[$field]))>0&&mb_strlen($data[$field])<=300,'INVALID_PRODUCT','Ürün alanlarını kontrol edin.',400);
        RuleViolation::ensure(preg_match('/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/',$data['slug']??'')&&strlen($data['slug'])<=120,'INVALID_SLUG','Ürün bağlantısını kontrol edin.',400);
        RuleViolation::ensure(str_starts_with($data['image']??'','/media/')&&!str_contains($data['image'],'..'),'INVALID_MEDIA','Yetkili yerel katalog görseli seçin.',400);
        $price=Money::amount($data['priceMinor']??null);$cost=Money::amount($data['costMinor']??0);$fixture=($data['fixture']??false)===true;RuleViolation::ensure(!$fixture||$this->config->local(),'FIXTURE_NOT_ALLOWED','Örnek ürün üretime eklenemez.',503);
        return ['priceMinor'=>$price,'costMinor'=>$cost,'fixture'=>$fixture];
    }
    public function create(array $data,Principal $actor):array
    {
        $actor->require('catalog',true);$this->validateDraft($data);
        return $this->db->transaction(fn()=>$this->insertDraft($data,$actor));
    }
    public function insertDraft(array $data,Principal $actor):array
    {
        $actor->require('catalog',true);
        if(!$this->db->pdo->inTransaction())throw new \LogicException('CATALOG_TRANSACTION_REQUIRED');
        $validated=$this->validateDraft($data);$price=$validated['priceMinor'];$cost=$validated['costMinor'];$fixture=$validated['fixture'];
            $id=Database::id();$variant=Database::id();$this->db->execute('INSERT INTO products(id,slug,name,name_en,description,description_en,category,image,fixture,brand,material) VALUES(?,?,?,?,?,?,?,?,?,?,?)',[$id,$data['slug'],trim($data['name']),trim($data['nameEn']),$data['description']??'',$data['descriptionEn']??'',$data['category'],$data['image'],$fixture?1:0,$data['brand']??'',$data['material']??'']);
            $this->db->execute('INSERT INTO variants(id,product_id,sku,name,name_en,price_minor,cost_minor,tax_class) VALUES(?,?,?,?,?,?,?,?)',[$variant,$id,$data['sku'],$data['variantName'],$data['variantNameEn']??$data['variantName'],$price,$cost,$data['taxClass']??'*']);
            $this->db->execute("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES(?,'TRY',?)",[$variant,$price]);$this->db->execute("INSERT INTO inventory_balance(variant_id,warehouse_id) VALUES(?,'main')",[$variant]);
            (new Audit($this->db))->record($actor,'create','products',$id);return ['id'=>$id,'variantId'=>$variant];
    }
    public function approve(string $id,string $country,Principal $actor):void
    {
        $actor->require('settings',true);$this->db->transaction(function()use($id,$country,$actor){
            RuleViolation::ensure($this->db->one('SELECT code FROM country_rules WHERE code=?',[$country]),'COUNTRY_NOT_CONFIGURED','Ülke kaydı gerekir.');$product=$this->db->one('SELECT * FROM products WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($product,'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);RuleViolation::ensure(!(bool)$product['fixture']||$this->config->local(),'FIXTURE_NOT_ALLOWED','Örnek ürün yayımlanamaz.',503);
            foreach($this->db->all('SELECT id FROM variants WHERE product_id=? ORDER BY id FOR UPDATE',[$id]) as $v){$this->db->execute('INSERT INTO product_eligibility(variant_id,country,approved,approved_by,approved_at) VALUES(?,?,true,?,CURRENT_TIMESTAMP(3)) ON DUPLICATE KEY UPDATE approved=true,approved_by=?,approved_at=CURRENT_TIMESTAMP(3)',[$v['id'],$country,$actor->id,$actor->id]);(new CheckoutPolicy($this->db,$this->config))->eligible($v['id'],$country);}
            $this->db->execute("UPDATE products SET status='published',updated_at=CURRENT_TIMESTAMP(3) WHERE id=?",[$id]);(new Audit($this->db))->record($actor,'publish','products',$id,['country'=>$country]);
        });
    }
    public function search(array $filters=[]):array
    {
        $page=max(1,min(100000,(int)($filters['page']??1)));$where=["p.status='published'","(p.fixture=false OR ?=true)"];$args=[$this->config->local()?1:0];
        if(trim($filters['q']??'')!==''){$q=mb_substr(trim($filters['q']),0,100);$q=str_replace(['=','%','_'],['==','=%','=_'],$q);$where[]="(p.name COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=' OR p.name_en COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=')";array_push($args,'%'.$q.'%','%'.$q.'%');}
        if(($filters['category']??'')!==''){$where[]='p.category=?';$args[]=$filters['category'];}
        $condition=implode(' AND ',$where);$total=(int)$this->db->one('SELECT COUNT(*) n FROM products p WHERE '.$condition,$args)['n'];
        $rows=$this->db->all('SELECT p.id,p.slug,p.name,p.name_en,p.description,p.description_en,p.category,p.image,p.brand,p.material,p.warnings,p.care,p.manufacturer,p.origin FROM products p WHERE '.$condition.' ORDER BY p.created_at DESC,p.id LIMIT 24 OFFSET '.(($page-1)*24),$args);
        $inventory=new Inventory($this->db,$this->config);foreach($rows as &$p){$p['variants']=$this->db->all('SELECT id,sku,name,name_en,price_minor,currency,color,size FROM variants WHERE product_id=? AND active=true ORDER BY id',[$p['id']]);foreach($p['variants'] as &$v){$v['price_minor']=(int)$v['price_minor'];$v['available']=$inventory->available($v['id']);}}unset($p,$v);
        return ['rows'=>$rows,'total'=>$total,'page'=>$page];
    }
    public function product(string $slug):?array
    {$id=$this->db->one("SELECT id FROM products WHERE slug=? AND status='published' AND(fixture=false OR ?=true)",[$slug,$this->config->local()?1:0]);if(!$id)return null;foreach($this->search()['rows'] as $row)if($row['id']===$id['id'])return $row;return $this->detail($id['id']);}
    private function detail(string $id):?array
    {$p=$this->db->one('SELECT id,slug,name,name_en,description,description_en,category,image,brand,material,warnings,care,manufacturer,origin FROM products WHERE id=?',[$id]);if(!$p)return null;$p['variants']=$this->db->all('SELECT id,sku,name,name_en,price_minor,currency,color,size FROM variants WHERE product_id=? AND active=true ORDER BY id',[$id]);foreach($p['variants'] as &$v)$v['available']=(new Inventory($this->db,$this->config))->available($v['id']);return $p;}
    public function admin(Principal $actor):array
    {
        RuleViolation::ensure($actor->mfa&&in_array($actor->role,['admin','catalog','warehouse','finance'],true),'FORBIDDEN','Bu liste için yetkiniz yok.',403);
        $cost=$actor->costs()?',v.cost_minor':'';return $this->db->all("SELECT p.id,p.name,p.status,v.id variant_id,v.sku,v.price_minor,v.fulfillment_mode,b.on_hand,b.quarantine,b.safety_stock$cost FROM products p JOIN variants v ON v.product_id=p.id LEFT JOIN inventory_balance b ON b.variant_id=v.id AND b.warehouse_id='main' ORDER BY p.created_at DESC LIMIT 100");
    }
    public function archive(string $id,Principal $actor):array
    {$actor->require('catalog',true);return $this->db->transaction(function()use($id,$actor){RuleViolation::ensure($this->db->one('SELECT id FROM products WHERE id=? FOR UPDATE',[$id]),'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);$this->db->execute("UPDATE products SET status='archived',updated_at=CURRENT_TIMESTAMP(3) WHERE id=?",[$id]);$this->db->execute('UPDATE variants SET active=false WHERE product_id=?',[$id]);(new Audit($this->db))->record($actor,'archive','products',$id);return ['id'=>$id,'archived'=>true];});}
}
