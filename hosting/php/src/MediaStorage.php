<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/MediaStorage.php
 * Açıklama   : Etkin içeriği reddeden, metadata temizleyen kalıcı özel görsel depolama.
 */
declare(strict_types=1);
namespace Sexogate;
use Symfony\Component\HttpFoundation\BinaryFileResponse;
final class MediaStorage
{
    public function __construct(private Database $db,private Config $config){}
    private function root():string
    {$root=$this->config->get('media_root');RuleViolation::ensure($root!==''&&!str_contains($root,"\0"),'MEDIA_STORAGE_REQUIRED','Görsel depolama ayarı eksik.',503);if(!is_dir($root)&&!mkdir($root,0700,true)&&!is_dir($root))throw new RuleViolation('MEDIA_STORAGE_FAILED','Görsel kaydedilemedi.',503);return rtrim($root,'/\\');}
    public function upload(string $raw,string $rights,Principal $actor):array
    {
        $actor->require('catalog',true);RuleViolation::ensure(strlen($raw)>0&&strlen($raw)<=4194304,'MEDIA_SIZE','Görsel en fazla4 MB olabilir.',400);$info=@getimagesizefromstring($raw);RuleViolation::ensure($info&&in_array($info['mime']??'',['image/jpeg','image/png','image/webp'],true)&&$info[0]>0&&$info[1]>0&&$info[0]*$info[1]<=16000000,'MEDIA_FORMAT','JPEG, PNG veya WebP görsel seçin; en fazla16 megapiksel kabul edilir.',400);RuleViolation::ensure(mb_check_encoding($rights,'UTF-8')&&mb_strlen(trim($rights))>=5&&mb_strlen($rights)<=2000,'MEDIA_RIGHTS_REQUIRED','Görselin kullanım hakkı veya kaynak referansını belirtin.',400);
        $image=@imagecreatefromstring($raw);RuleViolation::ensure($image!==false,'MEDIA_FORMAT','Görsel çözümlenemedi.',400);
        try{
            if($info['mime']==='image/jpeg'&&function_exists('exif_read_data')){$temp=tmpfile();try{fwrite($temp,$raw);$exif=@exif_read_data(stream_get_meta_data($temp)['uri']);$orientation=(int)($exif['Orientation']??1);if(in_array($orientation,[2,4,5,7],true))imageflip($image,$orientation===4?IMG_FLIP_VERTICAL:IMG_FLIP_HORIZONTAL);$degrees=match($orientation){3=>180,5,8=>90,6,7=>-90,default=>0};if($degrees){$rotated=imagerotate($image,$degrees,0);imagedestroy($image);$image=$rotated;}}finally{fclose($temp);}}
            $width=imagesx($image);$height=imagesy($image);$ratio=min(1,1600/max($width,$height));$width=max(1,(int)round($width*$ratio));$height=max(1,(int)round($height*$ratio));$scaled=imagescale($image,$width,$height,IMG_BICUBIC_FIXED);RuleViolation::ensure($scaled!==false,'MEDIA_FORMAT','Görsel işlenemedi.',400);try{imagealphablending($scaled,false);imagesavealpha($scaled,true);ob_start();try{RuleViolation::ensure(imagewebp($scaled,null,88),'MEDIA_FORMAT','Görsel işlenemedi.',400);$bytes=ob_get_contents();}finally{ob_end_clean();}}finally{imagedestroy($scaled);}
        }finally{imagedestroy($image);}
        $sha=hash('sha256',$bytes);$path='/media/uploads/'.$sha.'.webp';$file=$this->root().'/'.$sha.'.webp';
        if(!is_file($file)){$temporary=$file.'.'.bin2hex(random_bytes(8)).'.tmp';try{RuleViolation::ensure(file_put_contents($temporary,$bytes,LOCK_EX)===strlen($bytes),'MEDIA_STORAGE_FAILED','Görsel kaydedilemedi.',503);chmod($temporary,0600);RuleViolation::ensure(rename($temporary,$file),'MEDIA_STORAGE_FAILED','Görsel kaydedilemedi.',503);}finally{if(is_file($temporary))unlink($temporary);}}
        RuleViolation::ensure(hash_equals($sha,hash_file('sha256',$file)),'MEDIA_STORAGE_CHANGED','Görsel bütünlüğü doğrulanamadı.',503);
        $this->db->execute('INSERT INTO media_assets(path,sha256,width,height,bytes,rights_reference,created_by) VALUES(?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE path=path',[$path,$sha,$width,$height,strlen($bytes),trim($rights),$actor->id]);(new Audit($this->db))->record($actor,'upload','media',$sha,['bytes'=>strlen($bytes)]);return ['path'=>$path,'width'=>$width,'height'=>$height,'bytes'=>strlen($bytes),'sha256'=>$sha];
    }
    public function response(string $name,?Principal $actor):BinaryFileResponse
    {
        RuleViolation::ensure(preg_match('/\A[a-f0-9]{64}\.webp\z/',$name),'NOT_FOUND','Görsel bulunamadı.',404);$path='/media/uploads/'.$name;$record=$this->db->one('SELECT path FROM media_assets WHERE path=?',[$path]);RuleViolation::ensure($record,'NOT_FOUND','Görsel bulunamadı.',404);$admin=$actor&&$actor->mfa&&in_array($actor->role,['admin','catalog'],true);
        if(!$admin){$published=$this->db->one("SELECT p.id FROM products p WHERE p.status='published' AND(p.fixture=false OR ?=true) AND(p.image=? OR EXISTS(SELECT 1 FROM product_media m WHERE m.product_id=p.id AND m.path=?)) LIMIT 1",[$this->config->local()?1:0,$path,$path]);$category=$this->db->one('SELECT slug FROM categories WHERE active=true AND image=? LIMIT 1',[$path]);RuleViolation::ensure($published||$category,'NOT_FOUND','Görsel bulunamadı.',404);}
        $file=$this->root().'/'.$name;RuleViolation::ensure(is_file($file),'NOT_FOUND','Görsel bulunamadı.',404);return new BinaryFileResponse($file,200,['Content-Type'=>'image/webp','X-Content-Type-Options'=>'nosniff','Cache-Control'=>'private, no-store']);
    }
}
