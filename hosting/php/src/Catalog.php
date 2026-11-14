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
        foreach($filters as $value)RuleViolation::ensure(is_string($value)||is_int($value),'INVALID_FILTER','Filtre değerini kontrol edin.',400);
        $page=max(1,min(100000,(int)($filters['page']??1)));$where=["p.status='published'","(p.fixture=false OR ?=true)"];$args=[$this->config->local()?1:0];
        $query=$filters['q']??'';RuleViolation::ensure(is_string($query),'INVALID_SEARCH','Arama metnini kontrol edin.',400);$terms=preg_split('/\s+/u',mb_substr(trim($query),0,100),-1,PREG_SPLIT_NO_EMPTY);$terms=array_slice($terms,0,8);
        foreach($terms as $term){if(!preg_match('/[\p{L}\p{N}]/u',$term)){$where[]='false';continue;}$q=str_replace(['=','%','_'],['==','=%','=_'],$term);$compact=preg_replace('/[^\p{L}\p{N}]/u','',$term);$where[]="(p.name COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=' OR p.name_en COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=' OR p.brand LIKE ? ESCAPE '=' OR EXISTS(SELECT 1 FROM variants sv WHERE sv.product_id=p.id AND REPLACE(REPLACE(REPLACE(sv.sku,'-',''),'_',''),' ','') LIKE ?))";array_push($args,'%'.$q.'%','%'.$q.'%','%'.$q.'%','%'.$compact.'%');}
        if(($filters['category']??'')!==''){$where[]='p.category=?';$args[]=$filters['category'];}
        foreach(['brand','material'] as $field)if(($filters[$field]??'')!==''){RuleViolation::ensure(is_string($filters[$field])&&mb_strlen($filters[$field])<=150,'INVALID_FILTER','Filtreyi kontrol edin.',400);$where[]='p.'.$field.'=?';$args[]=$filters[$field];}
        $variant=['fv.product_id=p.id','fv.active=true'];$variantArgs=[];
        foreach(['minPrice'=>'>=','maxPrice'=>'<='] as $field=>$operator)if(($filters[$field]??'')!==''){$variant[]='fv.price_minor'.$operator.'?';$variantArgs[]=Money::parseDecimal((string)$filters[$field]);}
        foreach(['color','size'] as $field)if(($filters[$field]??'')!==''){RuleViolation::ensure(is_string($filters[$field])&&mb_strlen($filters[$field])<=100,'INVALID_FILTER','Filtreyi kontrol edin.',400);$variant[]='fv.'.$field.'=?';$variantArgs[]=$filters[$field];}
        $where[]='EXISTS(SELECT 1 FROM variants fv WHERE '.implode(' AND ',$variant).')';$args=array_merge($args,$variantArgs);
        if(($filters['exclude']??'')!==''){$where[]='p.id<>?';$args[]=$filters['exclude'];}
        $condition=implode(' AND ',$where);
        if(($filters['available']??'')==='1'){
            $candidates=$this->db->all('SELECT p.id FROM products p WHERE '.$condition.' LIMIT 5001',$args);RuleViolation::ensure(count($candidates)<=5000,'SEARCH_FILTER_TOO_BROAD','Stok filtresinden önce kategori veya aramayı daraltın.',400);$ids=[];$stock=new Inventory($this->db,$this->config);foreach($candidates as $candidate)foreach($this->db->all('SELECT id FROM variants WHERE product_id=? AND active=true',[$candidate['id']]) as $v)if($stock->available($v['id'])>0){$ids[]=$candidate['id'];break;}$condition.=$ids?' AND p.id IN('.Database::slots($ids).')':' AND false';$args=array_merge($args,$ids);
        }
        $price="(SELECT MIN(sv.price_minor) FROM variants sv WHERE sv.product_id=p.id AND sv.active=true)";$sort=match($filters['sort']??'recommended'){'price-asc'=>$price.' ASC,p.id','price-desc'=>$price.' DESC,p.id','name'=>'p.name COLLATE utf8mb4_tr_0900_ai_ci,p.id',default=>'p.created_at DESC,p.id'};
        $total=(int)$this->db->one('SELECT COUNT(*) n FROM products p WHERE '.$condition,$args)['n'];
        $rows=$this->db->all('SELECT p.id,p.slug,p.name,p.name_en,p.description,p.description_en,p.category,p.image,p.brand,p.material,p.warnings,p.care,p.manufacturer,p.origin FROM products p WHERE '.$condition.' ORDER BY '.$sort.' LIMIT 24 OFFSET '.(($page-1)*24),$args);
        $inventory=new Inventory($this->db,$this->config);foreach($rows as &$p){$p['variants']=$this->db->all('SELECT id,sku,name,name_en,price_minor,currency,color,size FROM variants WHERE product_id=? AND active=true ORDER BY id',[$p['id']]);foreach($p['variants'] as &$v){$v['price_minor']=(int)$v['price_minor'];$v['available']=$inventory->available($v['id']);}}unset($p,$v);
        return ['rows'=>$rows,'total'=>$total,'page'=>$page];
    }
    public function related(string $id,int $limit=4):array
    {$p=$this->db->one("SELECT category FROM products WHERE id=? AND status='published'",[$id]);if(!$p)return [];return array_slice($this->search(['category'=>$p['category'],'exclude'=>$id])['rows'],0,max(1,min(12,$limit)));}
    public function categories():array
    {return $this->db->all("SELECT c.slug,c.name,c.name_en,(SELECT COUNT(*) FROM products p WHERE p.category=c.slug AND p.status='published' AND(p.fixture=false OR ?=true)) product_count,(SELECT p.image FROM products p WHERE p.category=c.slug AND p.status='published' AND(p.fixture=false OR ?=true) ORDER BY p.created_at DESC LIMIT 1) image FROM categories c WHERE c.active=true ORDER BY c.name",[$this->config->local()?1:0,$this->config->local()?1:0]);}
    public function facets():array
    {$result=[];foreach(['brand','material'] as $field)$result[$field]=$this->db->all("SELECT DISTINCT p.".$field." value FROM products p WHERE p.status='published' AND(p.fixture=false OR ?=true) AND p.".$field."<>'' ORDER BY p.".$field." LIMIT 100",[$this->config->local()?1:0]);foreach(['color','size'] as $field)$result[$field]=$this->db->all("SELECT DISTINCT v.".$field." value FROM variants v JOIN products p ON p.id=v.product_id WHERE v.active=true AND p.status='published' AND(p.fixture=false OR ?=true) AND v.".$field." IS NOT NULL AND v.".$field."<>'' ORDER BY v.".$field." LIMIT 100",[$this->config->local()?1:0]);return $result;}
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
