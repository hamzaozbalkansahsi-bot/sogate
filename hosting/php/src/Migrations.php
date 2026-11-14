<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Migrations.php
 * Açıklama   : Aynı MySQL migration kaynağını checksum, kilit ve yarım DDL korumasıyla uygular.
 */
declare(strict_types=1);
namespace Sexogate;
final class Migrations
{
    public function __construct(private readonly Database $db){}
    public function apply(string $directory):void
    {
        $files=glob($directory.'/*.sql');sort($files,SORT_STRING);if(!$files)throw new \RuntimeException('MIGRATIONS_REQUIRED');$sources=[];
        foreach($files as $file){$name=basename($file);if(!preg_match('/\A\d{3}_[a-z0-9_]+\.sql\z/',$name))throw new \RuntimeException('MIGRATION_NAME_INVALID');$sql=file_get_contents($file);if(!mb_check_encoding($sql,'UTF-8'))throw new \RuntimeException('MIGRATION_UTF8_INVALID');$sources[$name]=['hash'=>hash('sha256',$sql),'statements'=>self::split($sql)];}
        $schema=$this->db->one('SELECT DATABASE() name')['name'];$lock='sexogate:migrate:'.substr(hash('sha256',$schema),0,40);
        if((int)$this->db->one('SELECT GET_LOCK(?,10) acquired',[$lock])['acquired']!==1)throw new \RuntimeException('MIGRATION_LOCK_UNAVAILABLE');
        try{
            $this->db->pdo->exec("CREATE TABLE IF NOT EXISTS schema_migrations(name VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,checksum CHAR(64) CHARACTER SET ascii NOT NULL,state ENUM('running','applied','failed') NOT NULL,statement_index INT NOT NULL DEFAULT 0,started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),applied_at DATETIME(3),error_code VARCHAR(64) CHARACTER SET ascii) ENGINE=InnoDB");
            $history=$this->db->all('SELECT name,checksum,state FROM schema_migrations ORDER BY name');$done=[];$latest='';
            foreach($history as $row){if($row['state']!=='applied')throw new \RuntimeException('MIGRATION_DIRTY');if(!isset($sources[$row['name']])||!hash_equals($sources[$row['name']]['hash'],$row['checksum']))throw new \RuntimeException('MIGRATION_HISTORY_CHANGED');$done[$row['name']]=true;$latest=$row['name'];}
            foreach($sources as $name=>$source){
                if(isset($done[$name]))continue;if($latest!==''&&strcmp($name,$latest)<=0)throw new \RuntimeException('MIGRATION_ORDER_INVALID');
                $this->db->execute("INSERT INTO schema_migrations(name,checksum,state) VALUES(?,?,'running')",[$name,$source['hash']]);$index=0;
                try{foreach($source['statements'] as $statement){$this->db->execute('UPDATE schema_migrations SET statement_index=? WHERE name=?',[++$index,$name]);$this->db->pdo->exec($statement);}$this->db->execute("UPDATE schema_migrations SET state='applied',applied_at=CURRENT_TIMESTAMP(3) WHERE name=?",[$name]);}
                catch(\Throwable $e){$this->db->execute("UPDATE schema_migrations SET state='failed',error_code=? WHERE name=?",['MYSQL_'.(int)($e instanceof \PDOException?($e->errorInfo[1]??0):0),$name]);throw new \RuntimeException('MIGRATION_FAILED');}
            }
        }finally{$this->db->one('SELECT RELEASE_LOCK(?) released',[$lock]);}
    }
    public static function split(string $sql):array
    {
        $out=[];$buffer='';$delimiter=';';$quote='';$line=false;$block=false;$hasSql=false;$n=strlen($sql);
        for($i=0;$i<$n;$i++){
            $c=$sql[$i];$next=$sql[$i+1]??'';
            if($line){$buffer.=$c;if($c==="\n")$line=false;continue;}
            if($block){$buffer.=$c;if($c==='*'&&$next==='/'){$buffer.='/';$i++;$block=false;}continue;}
            if($quote!==''){$buffer.=$c;if($c==='\\'&&$quote!=='`'){if($next==='')throw new \RuntimeException('MIGRATION_SYNTAX_INVALID');$buffer.=$next;$i++;}elseif($c===$quote){if($next===$quote){$buffer.=$next;$i++;}else $quote='';}continue;}
            if(($i===0||$sql[$i-1]==="\n")&&preg_match('/^[\t ]*DELIMITER[\t ]+([^\s]+)[\t ]*(?:\r?\n|$)/i',substr($sql,$i),$m)){
                if($hasSql)throw new \RuntimeException('MIGRATION_SYNTAX_INVALID');$delimiter=$m[1];$buffer='';$i+=strlen($m[0])-1;continue;
            }
            if($c==='-'&&$next==='-'&&ctype_space($sql[$i+2]??' ')){$line=true;$buffer.='--';$i++;continue;}
            if($c==='#'){$line=true;$buffer.=$c;continue;}
            if($c==='/'&&$next==='*'){$block=true;$buffer.='/*';$i++;continue;}
            if(substr($sql,$i,strlen($delimiter))===$delimiter){if($hasSql)$out[]=trim($buffer);$buffer='';$hasSql=false;$i+=strlen($delimiter)-1;continue;}
            if(in_array($c,["'",'"','`'],true))$quote=$c;
            $buffer.=$c;if(!ctype_space($c))$hasSql=true;
        }
        if($quote!==''||$block||$hasSql)throw new \RuntimeException('MIGRATION_SYNTAX_INVALID');return $out;
    }
}
