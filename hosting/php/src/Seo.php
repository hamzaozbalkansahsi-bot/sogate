<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Seo.php
 * Açıklama   : Gerçek yayın/fiyat/stoktan ürün metaverisi, schema ve teknik kontrol raporu.
 */
declare(strict_types=1);
namespace Sexogate;
final class Seo
{
    public function __construct(private Database $db,private Config $config){}
    public function product(string $id,string $locale):array
    {
        $p=$this->db->one("SELECT * FROM products WHERE id=? AND status='published' AND(fixture=false OR ?=true)",[$id,$this->config->local()?1:0]);RuleViolation::ensure($p,'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);$en=$locale==='en';$data=json_decode($p['seo'],true);$name=$en?$p['name_en']:$p['name'];$description=$en?$p['description_en']:$p['description'];$route=$this->db->one('SELECT slug FROM product_routes WHERE product_id=? AND locale=?',[$id,$locale]);$canonical=$this->config->url(($en?'/en':'').'/urun/'.($route['slug']??$p['slug']));$title=$data[$locale]['title']??$name;$meta=$data[$locale]['description']??mb_substr(preg_replace('/\s+/u',' ',strip_tags($description)),0,160);$variants=$this->db->all('SELECT v.id,v.sku,v.barcode,v.name,v.name_en,vp.amount_minor FROM variants v JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=\'TRY\' AND vp.amount_minor>0 AND vp.valid_from<=CURRENT_TIMESTAMP(3) AND(vp.valid_until IS NULL OR vp.valid_until>CURRENT_TIMESTAMP(3)) WHERE v.product_id=? AND v.active=true ORDER BY v.id',[$id]);$offers=[];
        foreach($variants as $v){$amount=Money::amount($v['amount_minor']);$offers[]=['@type'=>'Offer','sku'=>$v['sku'],'price'=>intdiv($amount,100).'.'.str_pad((string)($amount%100),2,'0',STR_PAD_LEFT),'priceCurrency'=>'TRY','availability'=>(new Inventory($this->db,$this->config))->available($v['id'])>0?'https://schema.org/InStock':'https://schema.org/OutOfStock','url'=>$canonical];}
        $image=$this->config->get('asset_prefix',$this->config->path('/assets')).$p['image'];$origin=parse_url($this->config->get('app_url'));$image=$origin['scheme'].'://'.$origin['host'].(isset($origin['port'])?':'.$origin['port']:'').$image;$schema=['@context'=>'https://schema.org','@type'=>'Product','name'=>$name,'description'=>$description,'image'=>[$image],'url'=>$canonical,'hasAdultConsideration'=>'https://schema.org/SexualContentConsideration'];if($p['brand']!=='')$schema['brand']=['@type'=>'Brand','name'=>$p['brand']];if(count($variants)===1)$schema['sku']=$variants[0]['sku'];if($offers)$schema['offers']=$offers;$alternates=[];foreach($this->db->all('SELECT locale,slug FROM product_routes WHERE product_id=?',[$id]) as $r)if(in_array($r['locale'],['tr','en'],true)&&($r['locale']==='tr'||trim($p['name_en'])!==''))$alternates[$r['locale']]=$this->config->url(($r['locale']==='en'?'/en':'').'/urun/'.$r['slug']);return ['title'=>$title,'description'=>$meta,'canonical'=>$canonical,'alternates'=>$alternates,'schema'=>$schema];
    }
    public function audit(Principal $actor):array
    {$actor->require('catalog');$rows=$this->db->all('SELECT id,slug,name,name_en,description,description_en,image,status,seo FROM products ORDER BY updated_at DESC LIMIT 500');$titles=[];$result=[];foreach($rows as $r){$issues=[];$seo=json_decode($r['seo'],true);foreach(['tr','en'] as $l){$title=$seo[$l]['title']??($l==='tr'?$r['name']:$r['name_en']);$desc=$seo[$l]['description']??($l==='tr'?$r['description']:$r['description_en']);if(trim($title)==='')$issues[]=$l.':title';if(trim($desc)==='')$issues[]=$l.':description';if(isset($titles[$l.':'.$title]))$issues[]=$l.':duplicate-title';$titles[$l.':'.$title]=true;}if(!str_starts_with($r['image'],'/media/')||!is_file(dirname(__DIR__).'/public/assets'.$r['image']))$issues[]='image';$result[]=['id'=>$r['id'],'name'=>$r['name'],'slug'=>$r['slug'],'status'=>$r['status'],'issues'=>$issues];}return ['rows'=>$result,'reviewed'=>count($result),'rankingGuarantee'=>false];}
    public function sitemap():string
    {$rows=$this->db->all("SELECT r.locale,r.slug,p.updated_at FROM product_routes r JOIN products p ON p.id=r.product_id WHERE p.status='published' AND(p.fixture=false OR ?=true) AND r.locale IN('tr','en') ORDER BY p.id,r.locale LIMIT 50000",[$this->config->local()?1:0]);$xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';foreach($rows as $r){$url=$this->config->url(($r['locale']==='en'?'/en':'').'/urun/'.$r['slug']);$xml.='<url><loc>'.htmlspecialchars($url,ENT_XML1|ENT_QUOTES,'UTF-8').'</loc><lastmod>'.gmdate('c',strtotime($r['updated_at'].' UTC')).'</lastmod></url>';}return $xml.'</urlset>';}
}
