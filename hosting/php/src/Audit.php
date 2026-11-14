<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Audit.php
 * Açıklama   : İşlem izini ve gövdeye/aktöre bağlı idempotent yönetim komutlarını saklar.
 */
declare(strict_types=1);
namespace Sexogate;
final class Audit
{
    public function __construct(private Database $db){}
    public function record(Principal $actor,string $action,string $resource,string $id,array $details=[]):void
    {$this->db->execute('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES(?,?,?,?,?)',[$actor->id,$action,$resource,$id,json_encode($details,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE)]);}
    public function command(Principal $actor,string $key,array $body,callable $work):array
    {
        RuleViolation::ensure(strlen($key)>=16&&strlen($key)<=128,'IDEMPOTENCY_REQUIRED','Geçerli işlem anahtarı gerekir.',400);$hash=hash('sha256',json_encode([$actor->id,$body],JSON_THROW_ON_ERROR));$lock='sg:command:'.substr(hash('sha256',$key),0,48);
        RuleViolation::ensure((int)$this->db->one('SELECT GET_LOCK(?,10) acquired',[$lock])['acquired']===1,'COMMAND_BUSY','İşlem sürüyor. Aynı anahtarla yeniden deneyin.');
        try{return $this->db->transaction(function()use($actor,$key,$hash,$work){$old=$this->db->one('SELECT * FROM php_commands WHERE idempotency_key=? FOR UPDATE',[$key]);if($old){RuleViolation::ensure(hash_equals($old['request_hash'],$hash)&&$old['actor_id']===$actor->id,'IDEMPOTENCY_CONFLICT','İşlem anahtarı farklı içerik için kullanılmış.');return json_decode($old['result'],true,512,JSON_THROW_ON_ERROR);}$result=$work();$this->db->execute('INSERT INTO php_commands(idempotency_key,request_hash,actor_id,result) VALUES(?,?,?,?)',[$key,$hash,$actor->id,json_encode($result,JSON_THROW_ON_ERROR)]);return $result;});}finally{$this->db->one('SELECT RELEASE_LOCK(?) released',[$lock]);}
    }
}
