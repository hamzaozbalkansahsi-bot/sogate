<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Editorial.php
 * Açıklama   : NODENO blog akışı için sürümlü arama, konu, içindekiler ve gerçek ilgili kayıtlar.
 */
declare(strict_types=1);
namespace Sexogate;
final class Editorial
{
    public function __construct(private Database $db,private Config $config){}
    public function listing(string $locale,array $filters=[]):array
    {
        foreach($filters as $v)RuleViolation::ensure(is_string($v)||is_int($v),'INVALID_FILTER','Blog filtresini kontrol edin.',400);$q=mb_substr(trim((string)($filters['q']??'')),0,100);$topic=mb_substr((string)($filters['topic']??''),0,100);$page=max(1,min(10000,(int)($filters['page']??1)));
        $from=" FROM content_entries e JOIN content_publications p ON p.entry_id=e.id JOIN content_revisions r ON r.entry_id=p.entry_id AND r.version=p.version WHERE e.kind='guide' AND e.locale=? AND e.archived=false AND p.publish_at<=CURRENT_TIMESTAMP(3) AND NOT EXISTS(SELECT 1 FROM content_publications later WHERE later.entry_id=p.entry_id AND later.publish_at<=CURRENT_TIMESTAMP(3) AND(later.publish_at>p.publish_at OR(later.publish_at=p.publish_at AND later.version>p.version)))";$args=[$locale];
        $topics=$this->db->all("SELECT DISTINCT JSON_UNQUOTE(JSON_EXTRACT(r.metadata,'$.topic')) topic".$from." AND JSON_TYPE(JSON_EXTRACT(r.metadata,'$.topic'))='STRING' ORDER BY topic LIMIT 100",$args);
        if($q!==''){$needle='%'.str_replace(['=','%','_'],['==','=%','=_'],$q).'%';$from.=" AND(r.title COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=' OR r.summary COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=' OR r.body COLLATE utf8mb4_tr_0900_ai_ci LIKE ? ESCAPE '=')";array_push($args,$needle,$needle,$needle);}
        if($topic!==''){$from.=" AND JSON_UNQUOTE(JSON_EXTRACT(r.metadata,'$.topic'))=?";$args[]=$topic;}$total=(int)$this->db->one('SELECT COUNT(*) n'.$from,$args)['n'];$rows=$this->db->all('SELECT e.id,e.slug,r.title,r.summary,r.metadata,p.publish_at'.$from.' ORDER BY p.publish_at DESC,e.id LIMIT 12 OFFSET '.(($page-1)*12),$args);foreach($rows as &$r){$r['metadata']=json_decode($r['metadata'],true);$r['cover']=$this->cover($r['metadata']['cover']??null);}return compact('rows','total','page','topics','q','topic');
    }
    private function cover(mixed $value):?string
    {return is_string($value)&&preg_match('~\A/(?:media|brand)/[a-zA-Z0-9_/-]+\.(?:webp|png|jpg|svg)\z~',$value)?$value:null;}
    public function article(string $slug,string $locale):array
    {
        $entry=(new Content($this->db,$this->config))->find('guide',$slug,$locale);RuleViolation::ensure($entry,'NOT_FOUND','Yazı bulunamadı.',404);$sections=[];$part=['title'=>'','paragraphs'=>[]];$text=str_replace(["\r\n","\r"],"\n",$entry['body']);
        foreach(preg_split('/\n\s*\n/u',$text) as $block){$lines=explode("\n",$block);foreach($lines as $line){if(preg_match('/^#{1,3}\s+(.+)$/u',$line,$m)){if($part['title']!==''||$part['paragraphs'])$sections[]=$part;$part=['title'=>trim($m[1]),'paragraphs'=>[]];}elseif(trim($line)!=='')$part['paragraphs'][]=$line;}}if($part['title']!==''||$part['paragraphs'])$sections[]=$part;foreach($sections as $i=>&$section)$section['id']='bolum-'.($i+1);unset($section);
        $topic=is_string($entry['metadata']['topic']??null)?$entry['metadata']['topic']:'';$related=array_values(array_filter($this->listing($locale,$topic!==''?['topic'=>$topic]:[])['rows'],fn($p)=>$p['id']!==$entry['id']));$products=[];$ids=$entry['metadata']['relatedProductIds']??[];if(is_array($ids))foreach(array_slice($ids,0,8) as $id){if(!is_string($id))continue;$p=$this->db->one("SELECT slug FROM products WHERE id=? AND status='published' AND(fixture=false OR ?=true)",[$id,$this->config->local()?1:0]);if($p&&($p=(new Catalog($this->db,$this->config))->product($p['slug'])))$products[]=$p;}
        return $entry+['sections'=>$sections,'cover'=>$this->cover($entry['metadata']['cover']??null),'related'=>array_slice($related,0,3),'products'=>$products,'readingMinutes'=>max(1,(int)ceil(mb_strlen($text)/1100))];
    }
}
