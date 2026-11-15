<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/bin/source-catalog.php
 * Açıklama   : Yerel katalog toplama çıktısını yalnız inceleme tablolarına aktarır.
 */
declare(strict_types=1);
require dirname(__DIR__).'/vendor/autoload.php';
try{$o=getopt('',['config:','file:','vendor:']);$c=Sexogate\Config::load($o['config']??dirname(__DIR__).'/config.local.json');Sexogate\RuleViolation::ensure($c->local(),'LOCAL_REVIEW_ONLY','Bu CLI yalnız geliştirme/test içindir.',403);$db=new Sexogate\Database($c);$file=$o['file']??'';$key='source:'.hash('sha256',($o['vendor']??'').(is_file($file)?hash_file('sha256',$file):''));$result=(new Sexogate\SourceCatalog($db,$c))->import($file,$o['vendor']??'',$key,new Sexogate\Principal('local-catalog-import','admin',true));echo json_encode($result,JSON_THROW_ON_ERROR).PHP_EOL;}catch(Throwable $e){fwrite(STDERR,($e instanceof Sexogate\RuleViolation?$e->rule:'SOURCE_IMPORT_FAILED').PHP_EOL);exit(1);}
