<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/CatalogPresentation.php
 * Açıklama   : Döngüsüz kategori ağacı ve gerçek ürün/varyant görsellerinin denetimli yönetimi.
 */
declare(strict_types=1);
namespace Sexogate;
final class CatalogPresentation
{
    public function __construct(private Database $db,private Config $config){}
    private function text(mixed $s,int $max=300):string
    {RuleViolation::ensure(is_string($s)&&mb_check_encoding($s,'UTF-8')&&mb_strlen(trim($s))>0&&mb_strlen($s)<=$max,'INVALID_TEXT','Metni ve uzunluğunu kontrol edin.',400);return trim($s);}
    public function localImage(string $path):void
    {
        RuleViolation::ensure(str_starts_with($path,'/media/')&&!str_contains($path,'..')&&!str_contains($path,"\0"),'INVALID_MEDIA','Kayıtlı yerel görsel seçin.',400);
        if(str_starts_with($path,'/media/uploads/')){RuleViolation::ensure($this->db->one('SELECT path FROM media_assets WHERE path=?',[$path]),'INVALID_MEDIA','Kayıtlı görsel bulunamadı.',400);return;}
        $root=realpath(dirname(__DIR__).'/public/assets/media');$file=realpath(dirname(__DIR__).'/public/assets'.$path);RuleViolation::ensure($root&&$file&&str_starts_with($file,$root.DIRECTORY_SEPARATOR)&&is_file($file),'INVALID_MEDIA','Kayıtlı görsel bulunamadı.',400);
    }
    public function category(array $i,Principal $actor):array
    {
        $actor->require('catalog',true);$slug=$i['slug']??'';RuleViolation::ensure(is_string($slug)&&strlen($slug)<=120&&preg_match('/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/',$slug),'INVALID_SLUG','Kategori bağlantısını kontrol edin.',400);$name=$this->text($i['name']??null);$en=$this->text($i['nameEn']??null);$parent=$i['parent']??null;if($parent==='')$parent=null;RuleViolation::ensure($parent===null||is_string($parent),'CATEGORY_PARENT','Üst kategoriyi kontrol edin.',400);$active=$i['active']??true;RuleViolation::ensure(is_bool($active),'INVALID_CATEGORY','Kategori durumunu kontrol edin.',400);$order=$i['sortOrder']??0;RuleViolation::ensure((is_int($order)||is_string($order)&&ctype_digit($order))&&(int)$order>=0&&(int)$order<=100000,'INVALID_ORDER','Sıra0–100000 arasında olmalıdır.',400);$image=$i['image']??null;if($image!==null&&$image!==''){$this->text($image,1000);$this->localImage($image);}
        return $this->db->transaction(function()use($slug,$name,$en,$parent,$active,$order,$image,$actor){$rows=$this->db->all('SELECT slug,parent_slug,active FROM categories ORDER BY slug FOR UPDATE');$map=array_column($rows,null,'slug');if($parent!==null)RuleViolation::ensure(isset($map[$parent])&&(!$active||(bool)$map[$parent]['active']),'CATEGORY_PARENT','Etkin üst kategori seçin.',400);$cursor=$parent;$seen=[$slug=>true];while($cursor!==null){RuleViolation::ensure(!isset($seen[$cursor]),'CATEGORY_CYCLE','Kategori kendi altına taşınamaz.',400);$seen[$cursor]=true;$cursor=$map[$cursor]['parent_slug']??null;}$old=$map[$slug]??null;$image??=$this->db->one('SELECT image FROM categories WHERE slug=?',[$slug])['image']??null;
            $this->db->execute('INSERT INTO categories(slug,name,name_en,parent_slug,sort_order,image,active) VALUES(?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE name=VALUES(name),name_en=VALUES(name_en),parent_slug=VALUES(parent_slug),sort_order=VALUES(sort_order),image=VALUES(image),active=VALUES(active)',[$slug,$name,$en,$parent,(int)$order,$image,(int)$active]);
            if(!$active){$ids=[$slug];for($n=0;$n<count($ids);$n++)foreach($rows as $r)if($r['parent_slug']===$ids[$n]&&!in_array($r['slug'],$ids,true))$ids[]=$r['slug'];$this->db->execute('UPDATE categories SET active=false WHERE slug IN('.Database::slots($ids).')',$ids);$this->db->execute("UPDATE products SET status='closed' WHERE category IN(".Database::slots($ids).") AND status='published'",$ids);}
            (new Audit($this->db))->record($actor,$old?'update':'create','categories',$slug);return ['slug'=>$slug];});
    }
    public function media(array $i,Principal $actor):array
    {
        $actor->require('catalog',true);$product=$i['productId']??'';$variant=$i['variantId']??null;if($variant==='')$variant=null;$path=$this->text($i['path']??null,1000);$this->localImage($path);$tr=$this->text($i['altTr']??null,300);$en=$this->text($i['altEn']??null,300);$rights=$this->text($i['rightsReference']??null,2000);$order=$i['sortOrder']??0;RuleViolation::ensure((is_int($order)||is_string($order)&&ctype_digit($order))&&(int)$order>=0&&(int)$order<=100000,'INVALID_ORDER','Görsel sırasını kontrol edin.',400);
        return (new Audit($this->db))->command($actor,(string)($i['key']??''),['media',$i],function()use($product,$variant,$path,$tr,$en,$rights,$order,$actor){RuleViolation::ensure($this->db->one('SELECT id FROM products WHERE id=? FOR UPDATE',[$product]),'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);if($variant!==null)RuleViolation::ensure(is_string($variant)&&$this->db->one('SELECT id FROM variants WHERE id=? AND product_id=?',[$variant,$product]),'INVALID_VARIANT','Seçenek bu ürüne ait değil.',400);RuleViolation::ensure((int)$this->db->one('SELECT COUNT(*) n FROM product_media WHERE product_id=?',[$product])['n']<30,'MEDIA_LIMIT','Bir üründe en fazla30 görsel olabilir.');$id=Database::id();$this->db->execute('INSERT INTO product_media(id,product_id,variant_id,path,alt_tr,alt_en,rights_reference,sort_order,created_by) VALUES(?,?,?,?,?,?,?,?,?)',[$id,$product,$variant,$path,$tr,$en,$rights,$order,$actor->id]);$this->db->execute('UPDATE products SET updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$product]);(new Audit($this->db))->record($actor,'add','product_media',$id);return ['id'=>$id];});
    }
    public function removeMedia(string $id,Principal $actor):array
    {$actor->require('catalog',true);return $this->db->transaction(function()use($id,$actor){$r=$this->db->one('SELECT product_id FROM product_media WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($r,'MEDIA_NOT_FOUND','Görsel bulunamadı.',404);$this->db->execute('DELETE FROM product_media WHERE id=?',[$id]);$this->db->execute('UPDATE products SET updated_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$r['product_id']]);(new Audit($this->db))->record($actor,'unlink','product_media',$id);return ['removed'=>true];});}
}
