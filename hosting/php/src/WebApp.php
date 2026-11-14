<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/WebApp.php
 * Açıklama   : Ana ekrana ekleme için kişisel veri içermeyen, alt yola bağlı uygulama manifesti.
 */
declare(strict_types=1);
namespace Sexogate;
final class WebApp
{
    public static function manifest(Config $config):array
    {$assets=$config->get('asset_prefix',$config->path('/assets')).'/brand/app/';return ['id'=>$config->path('/'),'name'=>'SEXOGATE','short_name'=>'SEXOGATE','description'=>'Tutkunu Keşfet. Yetişkinlere özel koleksiyonlar.','lang'=>'tr','start_url'=>$config->path('/'),'scope'=>$config->path('/'),'display'=>'standalone','background_color'=>'#FBF4EF','theme_color'=>'#5A0A20','icons'=>[['src'=>$assets.'app-icon-192.png','sizes'=>'192x192','type'=>'image/png','purpose'=>'any'],['src'=>$assets.'app-icon-512.png','sizes'=>'512x512','type'=>'image/png','purpose'=>'any'],['src'=>$assets.'app-maskable-512.png','sizes'=>'512x512','type'=>'image/png','purpose'=>'maskable']]];}
}
