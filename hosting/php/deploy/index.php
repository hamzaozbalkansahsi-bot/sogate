<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/deploy/index.php
 * Açıklama   : Yalnız özel test sürümüne bağlanan Apache/PHP ön denetleyicisi.
 */
declare(strict_types=1);
ini_set('display_errors','0');
$active=__DIR__.'/app/active.php';$id=is_file($active)?require $active:null;
if(!is_string($id)||!preg_match('/\A[a-f0-9]{24}\z/',$id)){http_response_code(503);header('Cache-Control: no-store');header('X-Robots-Tag: noindex, nofollow');exit('Kurulum hazırlanıyor.');}
define('SEXOGATE_CONFIG',__DIR__.'/app/config.local.json');require __DIR__.'/app/releases/'.$id.'/public/index.php';
