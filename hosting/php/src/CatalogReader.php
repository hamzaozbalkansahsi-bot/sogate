<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/CatalogReader.php
 * Açıklama   : Ortak sunucu araması, kategori ağacı, fiyat ve toplu katalog projeksiyonu.
 */
declare(strict_types=1);
namespace Sexogate;
final class CatalogReader
{
    private const FIELDS='p.id,p.slug,p.name,p.name_en,p.description,p.description_en,p.category,p.image,p.brand,p.material,p.warnings,p.care,p.manufacturer,p.origin,p.attributes';
    public function __construct(private Database $db,private Config $config){}
    private function currency(string $currency):void{RuleViolation::ensure(in_array($currency,['TRY','EUR','USD','GBP'],true),'INVALID_CURRENCY','Para birimini kontrol edin.',400);}
    public function categories():array
    {
        $rows=$this->db->all("WITH RECURSIVE branches(root,slug) AS(SELECT slug,slug FROM categories WHERE active=true UNION ALL SELECT b.root,c.slug FROM branches b JOIN categories c ON c.parent_slug=b.slug WHERE c.active=true) SELECT c.slug,c.name,c.name_en,c.parent_slug,c.sort_order,COUNT(DISTINCT p.id) product_count,COALESCE(c.image,MIN(p.image)) image FROM categories c LEFT JOIN branches b ON b.root=c.slug LEFT JOIN products p ON p.category=b.slug AND p.status='published' AND(p.fixture=false OR ?=true) WHERE c.active=true GROUP BY c.slug ORDER BY c.sort_order,c.name COLLATE utf8mb4_tr_0900_ai_ci",[$this->config->local()?1:0]);
        foreach($rows as &$r)$r['product_count']=(int)$r['product_count'];return $rows;
    }
    public function descendants(string $slug):array
    {$rows=$this->db->all('SELECT slug,parent_slug FROM categories WHERE active=true');if(!in_array($slug,array_column($rows,'slug'),true))return [];$ids=[$slug];for($i=0;$i<count($ids);$i++)foreach($rows as $r)if($r['parent_slug']===$ids[$i]&&!in_array($r['slug'],$ids,true))$ids[]=$r['slug'];return $ids;}
    public function total():int{return (int)$this->db->one("SELECT COUNT(*) n FROM products p JOIN categories c ON c.slug=p.category AND c.active=true WHERE p.status='published' AND(p.fixture=false OR ?=true)",[$this->config->local()?1:0])['n'];}
    public function search(array $filters=[],string $locale='tr',string $currency='TRY'):array
    {
        $this->currency($currency);foreach($filters as $v)RuleViolation::ensure(is_string($v)||is_int($v),'INVALID_FILTER','Filtre değerini kontrol edin.',400);
        $page=max(1,min(100000,(int)($filters['page']??1)));$where=["p.status='published'","(p.fixture=false OR ?=true)",'EXISTS(SELECT 1 FROM categories c WHERE c.slug=p.category AND c.active=true)'];$args=[$this->config->local()?1:0];$rank=[];
        if(trim((string)($filters['q']??''))!==''){$rank=(new CatalogSearch($this->db,$this->config))->rank((string)$filters['q'],$locale);$where[]=$rank?'p.id IN('.Database::slots($rank).')':'false';$args=array_merge($args,$rank);}
        if(($filters['category']??'')!==''){$ids=$this->descendants((string)$filters['category']);$where[]=$ids?'p.category IN('.Database::slots($ids).')':'false';$args=array_merge($args,$ids);}
        foreach(['brand','material'] as $field)if(($filters[$field]??'')!==''){RuleViolation::ensure(mb_strlen((string)$filters[$field])<=150,'INVALID_FILTER','Filtreyi kontrol edin.',400);$where[]='p.'.$field.'=?';$args[]=$filters[$field];}
        $variant=['fv.product_id=p.id','fv.active=true'];$join=" LEFT JOIN variant_prices fvp ON fvp.variant_id=fv.id AND fvp.currency=? AND fvp.amount_minor>0 AND fvp.valid_from<=CURRENT_TIMESTAMP(3) AND(fvp.valid_until IS NULL OR fvp.valid_until>CURRENT_TIMESTAMP(3))";$variantArgs=[$currency];
        if(($filters['available']??'')==='1'){[$stock,$stockArgs]=(new Availability($this->db,$this->config))->query();$join.=' JOIN('.$stock.') sa ON sa.id=fv.id';$variantArgs=array_merge($variantArgs,$stockArgs);$variant[]='sa.available>0';}
        foreach(['minPrice'=>'>=','maxPrice'=>'<='] as $field=>$op)if(($filters[$field]??'')!==''){$variant[]='fvp.amount_minor'.$op.'?';$variantArgs[]=Money::parseDecimal((string)$filters[$field]);}
        foreach(['color','size'] as $field)if(($filters[$field]??'')!==''){RuleViolation::ensure(mb_strlen((string)$filters[$field])<=100,'INVALID_FILTER','Seçeneği kontrol edin.',400);$variant[]='fv.'.$field.'=?';$variantArgs[]=$filters[$field];}
        $where[]='EXISTS(SELECT 1 FROM variants fv'.$join.' WHERE '.implode(' AND ',$variant).')';$args=array_merge($args,$variantArgs);
        if(($filters['exclude']??'')!==''){$where[]='p.id<>?';$args[]=$filters['exclude'];}
        $condition=implode(' AND ',$where);$price="(SELECT MIN(vp.amount_minor) FROM variants sv JOIN variant_prices vp ON vp.variant_id=sv.id AND vp.currency='$currency' AND vp.amount_minor>0 AND vp.valid_from<=CURRENT_TIMESTAMP(3) AND(vp.valid_until IS NULL OR vp.valid_until>CURRENT_TIMESTAMP(3)) WHERE sv.product_id=p.id AND sv.active=true)";$name=$locale==='en'?'p.name_en':'p.name';$sortArgs=[];
        $sort=match($filters['sort']??'recommended'){'price-asc'=>"($price IS NULL),$price ASC,p.id",'price-desc'=>"($price IS NULL),$price DESC,p.id",'name','name-asc'=>$name.' COLLATE utf8mb4_tr_0900_ai_ci,p.id','name-desc'=>$name.' COLLATE utf8mb4_tr_0900_ai_ci DESC,p.id',default=>$rank?'FIELD(p.id,'.Database::slots($rank).')':'p.created_at DESC,p.id'};
        if($rank&&!in_array($filters['sort']??'recommended',['price-asc','price-desc','name','name-asc','name-desc'],true))$sortArgs=$rank;
        $total=(int)$this->db->one('SELECT COUNT(*) n FROM products p WHERE '.$condition,$args)['n'];$rows=$this->db->all('SELECT '.self::FIELDS.' FROM products p WHERE '.$condition.' ORDER BY '.$sort.' LIMIT 24 OFFSET '.(($page-1)*24),array_merge($args,$sortArgs));
        return ['rows'=>$this->hydrate($rows,$currency,$filters),'total'=>$total,'page'=>$page,'currency'=>$currency];
    }
    public function byIds(array $ids,string $currency='TRY'):array
    {if(!$ids)return [];$this->currency($currency);$ids=array_values(array_unique($ids));RuleViolation::ensure(count($ids)<=1000,'CATALOG_LIMIT','Ürün seçimini daraltın.',400);$rows=$this->db->all('SELECT '.self::FIELDS." FROM products p JOIN categories c ON c.slug=p.category AND c.active=true WHERE p.id IN(".Database::slots($ids).") AND p.status='published' AND(p.fixture=false OR ?=true)",array_merge($ids,[$this->config->local()?1:0]));$rows=$this->hydrate($rows,$currency);$map=array_column($rows,null,'id');return array_values(array_filter(array_map(fn($id)=>$map[$id]??null,$ids)));}
    public function product(string $slug,string $currency='TRY'):?array
    {$id=$this->db->one("SELECT p.id FROM products p JOIN categories c ON c.slug=p.category AND c.active=true WHERE p.slug=? AND p.status='published' AND(p.fixture=false OR ?=true)",[$slug,$this->config->local()?1:0]);return $id?($this->byIds([$id['id']],$currency)[0]??null):null;}
    public function hydrate(array $rows,string $currency='TRY',array $filters=[]):array
    {
        if(!$rows)return [];$ids=array_column($rows,'id');$variants=$this->db->all('SELECT v.id,v.product_id,v.sku,v.name,v.name_en,v.price_minor,v.currency,v.color,v.size,v.measurements,v.weight_grams,v.battery_type,v.battery_capacity_mah,vp.amount_minor display_price_minor FROM variants v LEFT JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=? AND vp.amount_minor>0 AND vp.valid_from<=CURRENT_TIMESTAMP(3) AND(vp.valid_until IS NULL OR vp.valid_until>CURRENT_TIMESTAMP(3)) WHERE v.product_id IN('.Database::slots($ids).') AND v.active=true ORDER BY v.id',array_merge([$currency],$ids));$stock=(new Availability($this->db,$this->config))->many(array_column($variants,'id'));$group=[];
        foreach($variants as $v){$v['price_minor']=(int)$v['price_minor'];$v['display_price_minor']=$v['display_price_minor']===null?null:(int)$v['display_price_minor'];$v['display_currency']=$currency;$v['price_available']=$v['display_price_minor']!==null;$v['available']=$stock[$v['id']]??0;$keep=true;foreach(['color','size'] as $field)if(($filters[$field]??'')!==''&&$v[$field]!==$filters[$field])$keep=false;foreach(['minPrice'=>1,'maxPrice'=>-1] as $field=>$sign)if(($filters[$field]??'')!==''&&($v['display_price_minor']===null||$sign*$v['display_price_minor']<$sign*Money::parseDecimal((string)$filters[$field])))$keep=false;if(($filters['available']??'')==='1'&&$v['available']<1)$keep=false;if($keep)$group[$v['product_id']][]=$v;}
        $media=[];foreach($this->db->all('SELECT id,product_id,variant_id,path,alt_tr,alt_en FROM product_media WHERE product_id IN('.Database::slots($ids).') ORDER BY sort_order,id',$ids) as $m)$media[$m['product_id']][]=$m;
        foreach($rows as &$p){$p['variants']=$group[$p['id']]??[];usort($p['variants'],fn($a,$b)=>($a['display_price_minor']===null)<=>($b['display_price_minor']===null)?:($a['display_price_minor']??0)<=>($b['display_price_minor']??0)?:strcmp($a['id'],$b['id']));$p['attributes']=json_decode($p['attributes']??'{}',true)?:[];$p['media']=$media[$p['id']]??[];if(!in_array($p['image'],array_column($p['media'],'path'),true))array_unshift($p['media'],['id'=>'primary','variant_id'=>null,'path'=>$p['image'],'alt_tr'=>$p['name'],'alt_en'=>$p['name_en']]);}
        unset($p);return $rows;
    }
}
