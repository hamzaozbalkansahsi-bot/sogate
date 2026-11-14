<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Database.php
 * Açıklama   : PDO parametreleri, UTC/InnoDB işlemleri ve güvenli deadlock tekrarları.
 */
declare(strict_types=1);
namespace Sexogate;
use PDO;
use PDOException;
final class Database
{
    public readonly PDO $pdo;
    public function __construct(Config $config)
    {
        $this->pdo=new PDO($config->get('db_dsn'),$config->get('db_user'),$config->get('db_password'),[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_EMULATE_PREPARES=>false,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC,PDO::MYSQL_ATTR_MULTI_STATEMENTS=>false]);
        $this->pdo->exec("SET SESSION time_zone='+00:00',sql_mode='STRICT_ALL_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ZERO_DATE,NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION',innodb_lock_wait_timeout=10");
    }
    public function all(string $sql,array $args=[]):array{$s=$this->pdo->prepare($sql);$s->execute($args);return $s->fetchAll();}
    public function one(string $sql,array $args=[]):?array{return $this->all($sql,$args)[0]??null;}
    public function execute(string $sql,array $args=[]):int{$s=$this->pdo->prepare($sql);$s->execute($args);return $s->rowCount();}
    public function transaction(callable $work,bool $readOnly=false):mixed
    {
        if($this->pdo->inTransaction())throw new \LogicException('NESTED_TRANSACTION_REQUIRES_CALLER_CONNECTION');
        for($attempt=0;;$attempt++){
            $committing=false;
            try{
                $this->pdo->exec('SET TRANSACTION ISOLATION LEVEL READ COMMITTED');
                $this->pdo->exec($readOnly?'START TRANSACTION READ ONLY':'START TRANSACTION READ WRITE');
                $result=$work($this);$committing=true;$this->pdo->commit();return $result;
            }catch(\Throwable $e){
                if($this->pdo->inTransaction())$this->pdo->rollBack();
                if($committing||$attempt>=3||!$e instanceof PDOException||!in_array((int)($e->errorInfo[1]??0),[1205,1213],true))throw $e;
                usleep(random_int(20000,65000));
            }
        }
    }
    public static function id():string
    {$b=random_bytes(16);$b[6]=chr((ord($b[6])&15)|64);$b[8]=chr((ord($b[8])&63)|128);$h=bin2hex($b);return substr($h,0,8).'-'.substr($h,8,4).'-'.substr($h,12,4).'-'.substr($h,16,4).'-'.substr($h,20);}
    public static function slots(array $values):string{RuleViolation::ensure(count($values)>0,'EMPTY_QUERY_SET','İşlem kümesi boş.',400);return implode(',',array_fill(0,count($values),'?'));}
}
