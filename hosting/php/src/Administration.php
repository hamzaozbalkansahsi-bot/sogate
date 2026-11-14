<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Administration.php
 * Açıklama   : Atomik kurulum ayarları, son yönetici koruması ve denetimli kuyruk retry.
 */
declare(strict_types=1);
namespace Sexogate;
final class Administration
{
    public function __construct(private Database $db,private Config $config){}
    public function settings(array $values,Principal $actor):array
    {
        $actor->require('settings',true);$allowed=['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone','seller.bankAccount'];foreach($values as $key=>$value)RuleViolation::ensure(in_array($key,$allowed,true)&&is_string($value)&&mb_strlen($value)<=2000,'INVALID_SETTING','İşletme ayarlarını kontrol edin.',400);
        return $this->db->transaction(function()use($values,$actor){$changed=false;foreach($values as $key=>$value){$old=$this->db->one('SELECT value FROM settings WHERE `key`=? FOR UPDATE',[$key]);$changed=$changed||!$old||json_decode($old['value'],true)!==$value;$json=json_encode($value,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);$this->db->execute('INSERT INTO settings(`key`,value) VALUES(?,?) ON DUPLICATE KEY UPDATE value=?,updated_at=CURRENT_TIMESTAMP(3)',[$key,$json,$json]);}if($changed){$this->db->execute("UPDATE legal_documents SET status='archived' WHERE status='effective' AND fixture=false");$this->db->execute("INSERT INTO settings(`key`,value) VALUES('launch.legalApproved','false') ON DUPLICATE KEY UPDATE value='false',updated_at=CURRENT_TIMESTAMP(3)");}(new Audit($this->db))->record($actor,'settings','settings','seller',['fields'=>array_keys($values),'legalReviewRequired'=>$changed]);return ['done'=>true,'legalReviewRequired'=>$changed];});
    }
    public function sellerSettings(Principal $actor):array
    {$actor->require('settings');$rows=$this->db->all("SELECT `key`,value FROM settings WHERE `key` IN('seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone','seller.bankAccount')");$values=[];foreach($rows as $r)$values[$r['key']]=json_decode($r['value'],true);return $values;}
    public function role(string $user,string $role,Principal $actor):array
    {$actor->require('settings',true);RuleViolation::ensure(in_array($role,['admin','catalog','warehouse','support','finance','marketing','customer'],true),'INVALID_ROLE','Rolü kontrol edin.',400);return $this->db->transaction(function()use($user,$role,$actor){$admins=$this->db->all("SELECT id FROM `user` WHERE role='admin' ORDER BY id FOR UPDATE");$target=$this->db->one('SELECT role FROM `user` WHERE id=? FOR UPDATE',[$user]);RuleViolation::ensure($target,'USER_NOT_FOUND','Kullanıcı bulunamadı.',404);RuleViolation::ensure($target['role']!=='admin'||$role==='admin'||count($admins)>1,'LAST_ADMINISTRATOR','Son yöneticinin yetkisi kaldırılamaz.');$this->db->execute('UPDATE `user` SET role=?,php_session_version=php_session_version+1 WHERE id=?',[$role,$user]);(new Audit($this->db))->record($actor,'role','users',$user,['from'=>$target['role'],'to'=>$role]);return ['id'=>$user,'role'=>$role];});}
    public function users(Principal $actor):array
    {$actor->require('settings');return $this->db->all('SELECT id,name,email,role,twoFactorEnabled FROM `user` ORDER BY name LIMIT 100');}
    public function jobs(Principal $actor):array
    {$actor->require('settings');return $this->db->all('SELECT id,type,status,attempts,max_attempts,last_error,available_at,created_at FROM jobs ORDER BY created_at DESC LIMIT 100');}
    public function retryJob(string $id,Principal $actor):array
    {$actor->require('settings',true);return $this->db->transaction(function()use($id,$actor){$r=$this->db->one('SELECT status FROM jobs WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($r&&$r['status']==='failed','JOB_NOT_RETRYABLE','Yalnız başarısız işler yeniden kuyruğa alınabilir.');$this->db->execute("UPDATE jobs SET status='pending',attempts=0,generation=generation+1,lease_until=NULL,last_error=NULL,available_at=CURRENT_TIMESTAMP(3) WHERE id=?",[$id]);(new Audit($this->db))->record($actor,'retry','jobs',$id);return ['id'=>$id,'status'=>'pending'];});}
    public function audit(Principal $actor):array
    {$actor->require('settings');return $this->db->all('SELECT actor_id,action,resource,resource_id,created_at FROM audit_log ORDER BY created_at DESC LIMIT 200');}
    public function invoice(string $order,string $provider,string $reference,string $kind,string $note,Principal $actor):array
    {$actor->require('finance',true);foreach(['seller.name','seller.taxNumber','seller.address'] as $key){$row=$this->db->one('SELECT value FROM settings WHERE `key`=?',[$key]);RuleViolation::ensure($row&&is_string(json_decode($row['value'],true))&&trim(json_decode($row['value'],true))!=='','SELLER_NOT_CONFIGURED','Mali belge kaydı için gerçek satıcı bilgileri gerekir.');}RuleViolation::ensure(mb_strlen(trim($provider))>=2&&mb_strlen($provider)<=100&&mb_strlen(trim($reference))>=3&&mb_strlen($reference)<=200&&in_array($kind,['e-invoice','e-archive','external-invoice'],true)&&mb_strlen(trim($note))>=5&&mb_strlen($note)<=2000,'INVOICE_REFERENCE_INVALID','Gerçek dış sistem belge referansını kontrol edin.',400);return $this->db->transaction(function()use($order,$provider,$reference,$kind,$note,$actor){RuleViolation::ensure($this->db->one('SELECT id FROM orders WHERE id=? FOR UPDATE',[$order]),'ORDER_NOT_FOUND','Sipariş bulunamadı.',404);$old=$this->db->one('SELECT id,order_id FROM invoice_references WHERE provider=? AND external_reference=?',[$provider,$reference]);if($old){RuleViolation::ensure($old['order_id']===$order,'INVOICE_REFERENCE_CONFLICT','Belge başka siparişe bağlı.');return ['id'=>$old['id']];}$id=Database::id();$this->db->execute('INSERT INTO invoice_references(id,order_id,provider,external_reference,document_kind,note,actor_id) VALUES(?,?,?,?,?,?,?)',[$id,$order,$provider,$reference,$kind,$note,$actor->id]);(new Audit($this->db))->record($actor,'reference','invoices',$id);return ['id'=>$id];});}
}
