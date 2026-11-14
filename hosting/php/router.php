<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/router.php
 * Açıklama   : Yalnız yerel PHP sunucusunda test alt yolunu ve güvenli varlıkları sunar.
 */
declare(strict_types=1);
$path=rawurldecode(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH)?:'/');
if(preg_match('~\A/test/assets/([a-zA-Z0-9_./-]+)\z~',$path,$m)&&!str_contains($m[1],'..')){
    $file=__DIR__.'/public/assets/'.$m[1];
    if(is_file($file)){
        $types=['css'=>'text/css','js'=>'application/javascript','svg'=>'image/svg+xml','woff2'=>'font/woff2','txt'=>'text/plain'];$ext=pathinfo($file,PATHINFO_EXTENSION);
        if(isset($types[$ext])){header('Content-Type: '.$types[$ext]);header('X-Content-Type-Options: nosniff');readfile($file);return;}
    }
    http_response_code(404);return;
}
require __DIR__.'/public/index.php';
