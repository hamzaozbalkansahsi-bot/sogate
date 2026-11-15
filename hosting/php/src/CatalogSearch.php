<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/CatalogSearch.php
 * Açıklama   : Özgün metni değiştirmeyen Türkçe normalleştirme ve kontrollü yazım toleransı.
 */
declare(strict_types=1);
namespace Sexogate;
final class CatalogSearch
{
    public function __construct(private Database $db,private Config $config){}
    public static function normalize(string $s):string
    {$s=mb_strtolower(strtr(mb_substr($s,0,2000),['İ'=>'i','I'=>'ı']),'UTF-8');$s=\Normalizer::normalize($s,\Normalizer::FORM_KD);return trim(strtr(preg_replace('/\p{M}/u','',$s),['ı'=>'i','أ'=>'ا','إ'=>'ا','آ'=>'ا','ى'=>'ي']));}
    public static function oneEdit(string $a,string $b):bool
    {
        if($a===$b)return true;$a=mb_str_split($a);$b=mb_str_split($b);$n=count($a);$m=count($b);if(abs($n-$m)>1)return false;$i=0;while($i<$n&&$i<$m&&$a[$i]===$b[$i])$i++;
        if($n===$m)return array_slice($a,$i+1)===array_slice($b,$i+1)||($i+1<$n&&$a[$i]===$b[$i+1]&&$a[$i+1]===$b[$i]&&array_slice($a,$i+2)===array_slice($b,$i+2));
        return $n>$m?array_slice($a,$i+1)===array_slice($b,$i):array_slice($a,$i)===array_slice($b,$i+1);
    }
    public function rank(string $query,string $locale='tr'):array
    {
        $needle=self::normalize(mb_substr(trim($query),0,100));$terms=array_slice(preg_split('/[^\p{L}\p{N}]+/u',$needle,-1,PREG_SPLIT_NO_EMPTY),0,8);if(!$terms)return [];
        $code=preg_replace('/[^\p{L}\p{N}]/u','',$needle);$sku=[];
        if(preg_match('/\d/u',$code))foreach($this->db->all("SELECT DISTINCT v.product_id FROM variants v JOIN products p ON p.id=v.product_id WHERE v.active=true AND p.status='published' AND(p.fixture=false OR ?=true) AND REPLACE(REPLACE(REPLACE(LOWER(v.sku),'-',''),'_',''),' ','') LIKE ?",[$this->config->local()?1:0,'%'.$code.'%']) as $r)$sku[$r['product_id']]=true;
        $statement=$this->db->pdo->prepare("SELECT p.id,p.name,p.name_en,p.brand,p.material,c.name category_name,c.name_en category_name_en FROM products p JOIN categories c ON c.slug=p.category WHERE p.status='published' AND(p.fixture=false OR ?=true) ORDER BY p.created_at DESC,p.id");$statement->execute([$this->config->local()?1:0]);$matches=[];$position=0;
        while($p=$statement->fetch(\PDO::FETCH_ASSOC)){
            $position++;$name=self::normalize($locale==='en'?$p['name_en']:$p['name']);$body=self::normalize(implode(' ',[$p['name'],$p['name_en'],$p['brand'],$p['material'],$p['category_name'],$p['category_name_en']]));$words=preg_split('/[^\p{L}\p{N}]+/u',$body,-1,PREG_SPLIT_NO_EMPTY);$score=isset($sku[$p['id']])?1200:0;$ok=true;
            if(!$score)foreach($terms as $term){if(str_contains($body,$term)){$prefix=false;foreach($words as $word)if(str_starts_with($word,$term)){$prefix=true;break;}$score+=$prefix?20:10;}else{$fuzzy=false;if(mb_strlen($term)>=4&&!preg_match('/\d/u',$term))foreach($words as $word)if(mb_strlen($word)>=4&&self::oneEdit($term,$word)){$fuzzy=true;break;}if(!$fuzzy){$ok=false;break;}$score+=2;}}
            if(!$ok)continue;if($name===$needle)$score+=500;elseif(str_starts_with($name,$needle))$score+=200;$matches[]=['id'=>$p['id'],'score'=>$score,'position'=>$position];
        }
        usort($matches,fn($a,$b)=>$b['score']<=>$a['score']?:$a['position']<=>$b['position']);return array_column($matches,'id');
    }
}
