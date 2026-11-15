<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Information.php
 * Açıklama   : Kamuya açık footer verisi ve onaylı hukuk ile test taslağının ayrı sunumu.
 */
declare(strict_types=1);
namespace Sexogate;
final class Information
{
    public const LEGAL=['kvkk'=>'privacy','gizlilik'=>'privacy-policy','mesafeli-satis'=>'terms','iade'=>'returns','cerez'=>'cookies','teslimat'=>'delivery'];
    public function __construct(private Database $db,private Config $config){}
    public function footer():array
    {
        $row=$this->db->one("SELECT value FROM settings WHERE `key`='seller.supportEmail'");$email=$row?json_decode($row['value'],true):'info@sexogate.com';if(!is_string($email)||!filter_var($email,FILTER_VALIDATE_EMAIL))$email='info@sexogate.com';
        return ['email'=>$email,'social'=>[['name'=>'Instagram','url'=>'https://www.instagram.com/sexogate/'],['name'=>'Facebook','url'=>'https://www.facebook.com/profile.php?id=61596759171927'],['name'=>'X','url'=>'https://x.com/sexogate'],['name'=>'TikTok','url'=>'https://www.tiktok.com/@sexogate']]];
    }
    public function legal(string $slug,string $locale):array
    {
        $kind=self::LEGAL[$slug]??null;RuleViolation::ensure($kind,'NOT_FOUND','Belge bulunamadı.',404);
        $doc=$this->db->one("SELECT title,body,version,body_hash FROM legal_documents WHERE kind=? AND locale=? AND status='effective' AND fixture=false AND effective_at<=CURRENT_TIMESTAMP(3) ORDER BY version DESC LIMIT 1",[$kind,$locale]);
        if($doc)return ['title'=>$doc['title'],'body'=>$doc['body'],'sections'=>[],'draft'=>false,'version'=>(int)$doc['version'],'hash'=>$doc['body_hash']];
        RuleViolation::ensure($this->config->local(),'NOT_FOUND','Onaylı belge henüz yayımlanmadı.',404);$drafts=json_decode(file_get_contents(__DIR__.'/Information/legal-drafts.json'),true,32,JSON_THROW_ON_ERROR);$doc=$drafts[$locale][$slug];return $doc+['body'=>'','draft'=>true,'version'=>null,'hash'=>null];
    }
    public function siteMap(string $locale):array
    {
        $tr=$locale==='tr';$main=[];foreach([['/','Ana sayfa','Home'],['/urunler','Tüm ürünler','Products'],['/koleksiyonlar','Koleksiyonlar','Collections'],['/blog','Blog','Blog'],['/rehber','Rehber','Guides'],['/sss','Sık sorulan sorular','FAQ'],['/iletisim','İletişim','Contact']] as [$path,$a,$b])$main[]=['path'=>$path,'label'=>$tr?$a:$b];
        $categories=array_map(fn($c)=>['path'=>'/kategori/'.$c['slug'],'label'=>$tr?$c['name']:$c['name_en']],$this->db->all('SELECT slug,name,name_en FROM categories WHERE active=true ORDER BY name'));
        $legal=[];foreach(self::LEGAL as $slug=>$kind){try{$d=$this->legal($slug,$locale);$legal[]=['path'=>'/yasal/'.$slug,'label'=>$d['title']];}catch(RuleViolation){}}
        $articles=array_map(fn($c)=>['path'=>'/rehber/'.$c['slug'],'label'=>$c['title']],(new Content($this->db,$this->config))->listing('guide',$locale));
        return [['title'=>$tr?'Mağaza':'Store','links'=>$main],['title'=>$tr?'Kategoriler':'Categories','links'=>$categories],['title'=>$tr?'Bilgilendirme':'Information','links'=>$legal],['title'=>$tr?'Blog ve rehber':'Blog and guides','links'=>$articles]];
    }
}
