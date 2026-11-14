<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Backup.php
 * Açıklama   : İşlemsel PHP test yedeği, doğrulanmış şifreleme ve yalnız yeni yerel DB'ye geri yükleme.
 */
declare(strict_types=1);
namespace Sexogate;
final class Backup
{
    public function __construct(private Database $db,private Config $config){}
    public function snapshot():array
    {
        $tables=$this->db->all("SELECT TABLE_NAME name,ENGINE engine FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME");
        foreach($tables as $t)RuleViolation::ensure(preg_match('/\A[A-Za-z0-9_]+\z/',$t['name'])&&$t['engine']==='InnoDB','BACKUP_ENGINE_UNSUPPORTED','Tutarlı yedek için bütün tablolar InnoDB olmalıdır.',503);
        $this->db->pdo->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');$this->db->pdo->exec('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY');
        try{$result=[];foreach($tables as $t){$name=$t['name'];$columns=$this->db->all('SELECT COLUMN_NAME name,DATA_TYPE type,GENERATION_EXPRESSION expression_value FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? ORDER BY ORDINAL_POSITION',[$name]);$rows=in_array($name,['php_sessions','php_login_limits'],true)?[]:$this->db->all('SELECT * FROM `'.$name.'`');$encoded=[];foreach($rows as $row){$v=[];foreach($columns as $col)$v[]=$row[$col['name']]===null?null:base64_encode((string)$row[$col['name']]);$encoded[]=json_encode($v,JSON_THROW_ON_ERROR);}sort($encoded,SORT_STRING);$result[$name]=['columns'=>$columns,'rows'=>array_map(fn($r)=>json_decode($r,true,512,JSON_THROW_ON_ERROR),$encoded),'count'=>count($encoded),'sha256'=>hash('sha256',implode("\n",$encoded))];}
            $this->db->pdo->commit();return ['version'=>1,'createdAt'=>gmdate('c'),'omittedEphemeralTables'=>['php_sessions','php_login_limits'],'tables'=>$result];
        }catch(\Throwable $e){if($this->db->pdo->inTransaction())$this->db->pdo->rollBack();throw $e;}
    }
    public static function encrypt(array $snapshot,string $key):string
    {RuleViolation::ensure(strlen($key)===32,'BACKUP_KEY_INVALID','Yedek anahtarı geçersiz.',503);$nonce=random_bytes(12);$tag='';$plain=gzencode(json_encode($snapshot,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE),6);$cipher=openssl_encrypt($plain,'aes-256-gcm',$key,OPENSSL_RAW_DATA,$nonce,$tag,'SGPHPB1');if($cipher===false)throw new \RuntimeException('BACKUP_ENCRYPT_FAILED');return 'SGPHPB1'.$nonce.$tag.$cipher;}
    public static function decrypt(string $archive,string $key):array
    {RuleViolation::ensure(strlen($key)===32&&strlen($archive)>35&&str_starts_with($archive,'SGPHPB1'),'BACKUP_INVALID','Yedek doğrulanamadı.',400);$plain=openssl_decrypt(substr($archive,35),'aes-256-gcm',$key,OPENSSL_RAW_DATA,substr($archive,7,12),substr($archive,19,16),'SGPHPB1');RuleViolation::ensure($plain!==false,'BACKUP_AUTHENTICATION_FAILED','Yedek doğrulanamadı.',400);$json=gzdecode($plain,100000000);RuleViolation::ensure($json!==false,'BACKUP_INVALID','Yedek doğrulanamadı.',400);return json_decode($json,true,512,JSON_THROW_ON_ERROR);}
    public function restoreLocal(array $snapshot):array
    {
        $name=$this->db->one('SELECT DATABASE() name')['name'];RuleViolation::ensure($this->config->local()&&str_starts_with($this->config->get('db_dsn'),'mysql:host=127.0.0.1;port=55433;')&&preg_match('/\Asexogate_php_[a-f0-9]{16}_test\z/',$name),'LOCAL_RESTORE_ONLY','Geri yükleme yalnız yeni izole yerel DB için açıktır.',503);
        foreach(['user','products','orders'] as $table)RuleViolation::ensure((int)$this->db->one('SELECT COUNT(*) n FROM `'.$table.'`')['n']===0,'RESTORE_TARGET_NOT_EMPTY','Geri yükleme hedefi boş olmalıdır.');
        $empty=$this->snapshot();$tables=$snapshot['tables']??[];RuleViolation::ensure(($snapshot['version']??0)===1&&array_keys($tables)===array_keys($empty['tables']),'BACKUP_SCHEMA_MISMATCH','Yedek şeması farklı.');
        foreach($tables as $table=>$data){RuleViolation::ensure($data['columns']===$empty['tables'][$table]['columns'],'BACKUP_SCHEMA_MISMATCH','Yedek alanları farklı.');$rows=array_map(fn($r)=>json_encode($r,JSON_THROW_ON_ERROR),$data['rows']);sort($rows,SORT_STRING);RuleViolation::ensure($data['count']===count($rows)&&hash_equals($data['sha256'],hash('sha256',implode("\n",$rows))),'BACKUP_HASH_MISMATCH','Yedek içeriği farklı.');}
        $triggers=[];foreach($this->db->all('SELECT TRIGGER_NAME name FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()') as $row){$trigger=$row['name'];if(!preg_match('/\A[A-Za-z0-9_]+\z/',$trigger))throw new \RuntimeException('TRIGGER_NAME_INVALID');$triggers[$trigger]=$this->db->one('SHOW CREATE TRIGGER `'.$trigger.'`')['SQL Original Statement'];}
        foreach($triggers as $trigger=>$ddl)$this->db->pdo->exec('DROP TRIGGER `'.$trigger.'`');$this->db->pdo->exec('SET FOREIGN_KEY_CHECKS=0');
        try{foreach($tables as $table=>$data){$this->db->pdo->exec('TRUNCATE TABLE `'.$table.'`');$writable=array_filter($data['columns'],fn($c)=>$c['expression_value']==='');$columns=array_column($writable,'name');$sql='INSERT INTO `'.$table.'`(`'.implode('`,`',$columns).'`) VALUES('.Database::slots($columns).')';$statement=$this->db->pdo->prepare($sql);
                foreach($data['rows'] as $row){$position=0;foreach($writable as $i=>$column){$encoded=$row[$i];$value=$encoded===null?null:base64_decode($encoded,true);if($encoded!==null&&$value===false)throw new \RuntimeException('BACKUP_ENCODING_INVALID');$binary=in_array($data['columns'][$i]['type'],['blob','mediumblob','longblob','tinyblob','binary','varbinary'],true);$statement->bindValue(++$position,$value,$value===null?\PDO::PARAM_NULL:($binary?\PDO::PARAM_LOB:\PDO::PARAM_STR));}$statement->execute();}}
        }finally{$this->db->pdo->exec('SET FOREIGN_KEY_CHECKS=1');foreach($triggers as $ddl)$this->db->pdo->exec($ddl);}
        $restored=$this->snapshot();foreach($tables as $table=>$data)RuleViolation::ensure($restored['tables'][$table]['sha256']===$data['sha256']&&$restored['tables'][$table]['count']===$data['count'],'RESTORE_HASH_MISMATCH','Geri yükleme doğrulaması başarısız.',503);
        $foreign=$this->db->all('SELECT TABLE_NAME child,CONSTRAINT_NAME fk,COLUMN_NAME child_col,REFERENCED_TABLE_NAME parent,REFERENCED_COLUMN_NAME parent_col FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION');$groups=[];foreach($foreign as $f)$groups[$f['child'].':'.$f['fk']][]=$f;
        foreach($groups as $fields){$child=$fields[0]['child'];$parent=$fields[0]['parent'];$on=implode(' AND ',array_map(fn($f)=>'c.`'.$f['child_col'].'`=p.`'.$f['parent_col'].'`',$fields));$nonnull=implode(' AND ',array_map(fn($f)=>'c.`'.$f['child_col'].'` IS NOT NULL',$fields));$missing=(int)$this->db->one('SELECT COUNT(*) n FROM `'.$child.'` c LEFT JOIN `'.$parent.'` p ON '.$on.' WHERE '.$nonnull.' AND p.`'.$fields[0]['parent_col'].'` IS NULL')['n'];RuleViolation::ensure($missing===0,'RESTORE_FOREIGN_KEY_INVALID','Geri yüklenen kayıt ilişkileri tutarsız.',503);}
        return ['tables'=>count($tables),'rows'=>array_sum(array_column($tables,'count')),'foreignKeys'=>count($groups),'hashesVerified'=>true];
    }
}
