<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/bin/verify-restore.php
 * Açıklama   : Uzak test yedeğini yalnız rastgele yeni yerel DB'ye açıp hash/ilişki kontrolü yapar.
 */
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);require dirname(__DIR__).'/vendor/autoload.php';require dirname(__DIR__).'/tests/TestDatabase.php';
$temporary=null;
try{
    $key=hex2bin(getenv('SEXOGATE_BACKUP_KEY')?:'');
    $encoded=getenv('SEXOGATE_BACKUP_FILE_B64');
    $file=$encoded!==false?base64_decode($encoded,true):(getenv('SEXOGATE_BACKUP_FILE')?:'');
    if(!is_string($file)||!is_file($file))throw new RuntimeException('BACKUP_FILE_REQUIRED');
    $snapshot=Sexogate\Backup::decrypt(file_get_contents($file),$key);
    $history=$snapshot['tables']['schema_migrations']??null;
    if(!is_array($history)||empty($history['rows']))throw new RuntimeException('BACKUP_MIGRATIONS_REQUIRED');
    $columns=array_column($history['columns'],'name');$verified=[];
    $root=dirname(__DIR__,3);$canonical=$root.'/migrations/mysql';
    foreach($history['rows'] as $values){
        $row=array_combine($columns,array_map(fn($value)=>$value===null?null:base64_decode($value,true),$values));
        $name=$row['name']??'';
        if(!preg_match('/\A\d{3}_[a-z0-9_]+\.sql\z/',$name)||($row['state']??'')!=='applied'||isset($verified[$name]))throw new RuntimeException('BACKUP_MIGRATIONS_INVALID');
        $source=$canonical.'/'.$name;
        if(!is_file($source)||!hash_equals(hash_file('sha256',$source),$row['checksum']??''))throw new RuntimeException('BACKUP_MIGRATIONS_CHANGED');
        $verified[$name]=$source;
    }
    ksort($verified,SORT_STRING);
    $temporary=$root.'/.local/php-restore-migrations-'.bin2hex(random_bytes(12));
    if(!mkdir($temporary,0700))throw new RuntimeException('RESTORE_DIRECTORY_FAILED');
    foreach($verified as $name=>$source)if(!copy($source,$temporary.'/'.$name))throw new RuntimeException('RESTORE_MIGRATION_COPY_FAILED');
    $f=new TestDatabase($temporary);
    $result=(new Sexogate\Backup($f->db,$f->config))->restoreLocal($snapshot);
    (new Sexogate\Migrations($f->db))->apply($temporary);
    $result['sourceMigrations']=count($verified);$result['migrationChecksumsVerified']=true;
    (new Sexogate\Migrations($f->db))->apply($canonical);
    $result['currentMigrations']=(int)$f->db->one("SELECT COUNT(*) n FROM schema_migrations WHERE state='applied'")['n'];
    $result['forwardMigrationVerified']=true;
    echo json_encode($result,JSON_THROW_ON_ERROR);
}
catch(Throwable $e){fwrite(STDERR,json_encode(['restored'=>false,'errorType'=>get_class($e),'rule'=>$e instanceof Sexogate\RuleViolation?$e->rule:null]));exit(1);}
finally{if($temporary!==null&&is_dir($temporary)){foreach(glob($temporary.'/*.sql') as $file)unlink($file);rmdir($temporary);}}
