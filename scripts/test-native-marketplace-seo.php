<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-marketplace-seo.php
 * Açıklama   : Gerçek paket ürünlerinin bütün dillerde SSR ve şemasını, bilinmeyen marka dahil uyarıları hata sayarak sınar.
 */
declare(strict_types=1);
$repo=dirname(__DIR__);$package=json_decode(file_get_contents($repo.'/.local/native-stage-package.json'),true,512,JSON_THROW_ON_ERROR);$private=$package['bundle'].'/private';require $private.'/control-http.php';require_once $private.'/sexogate-catalog.php';require_once $private.'/seo.php';
set_error_handler(static function(int $severity,string $message,string $file,int $line):bool{if(error_reporting()&$severity)throw new ErrorException($message,0,$severity,$file,$line);return true;});
$catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$config=json_decode(file_get_contents($private.'/config.json'),true,512,JSON_THROW_ON_ERROR);$checks=0;$pages=0;$public=[];$unknown=0;
function seoCheck(bool $ok,string $name):void{global $checks;if(!$ok)throw new RuntimeException($name);$checks++;}
foreach($catalog['products']as &$product){
 if(($product['catalogOrigin']??'')!=='sexogate-marketplaces-v1')continue;
 $initial=sexogateCatalogInitial($product,$private);
 if(in_array(mb_strtolower(trim($initial['brand']??''),'UTF-8'),['genel markalar','markasız','markasiz','diğer','diger'],true))$initial['brand']='';
 $product=sexogateCatalogProjection($product,$initial);
 if(nodenoSeoVisible($product)){$public[]=$product;if($product['brand']==='')$unknown++;}
}unset($product);
seoCheck(count($public)>0&&$unknown>0,'unknown_brand_fixture_present');
foreach($public as $product)foreach(NODENO_SEO_LOCALES as $locale){
 $page=nodenoSeoPage($catalog,$config,['product'=>$product['id'],'lang'=>$locale]);$pages++;
 seoCheck($page['status']===200,'published_product_ssr_200');
 $schema=null;foreach($page['jsonld']as $entry)if(($entry['@type']??'')==='Product')$schema=$entry;
 seoCheck(is_array($schema)&&($schema['sku']??'')===$product['code'],'real_sku_in_schema');
 seoCheck(!isset($schema['aggregateRating'])&&!isset($schema['review']),'no_invented_reviews');
 if($product['brand']==='')seoCheck(!isset($schema['brand']),'unknown_brand_is_omitted');else seoCheck(($schema['brand']['name']??'')===$product['brand'],'real_brand_preserved');
 if(isset($schema['offers'])){seoCheck(($schema['offers']['price']??null)===nodenoSeoAmount($product['salePriceMinor'])&&($schema['offers']['priceCurrency']??null)==='TRY','real_price_in_schema');seoCheck(!isset($schema['offers']['availability']),'unknown_stock_not_instock');}
 seoCheck(!str_contains(json_encode($schema,JSON_THROW_ON_ERROR),'privateRetailReference'),'private_cost_not_in_schema');
 seoCheck(is_string($page['body'])&&str_contains($page['body'],nodenoSeoEscape($product['code'])),'ssr_body_contains_real_code');
}
restore_error_handler();echo json_encode(['passed'=>$checks,'publicProducts'=>count($public),'pages'=>$pages,'locales'=>count(NODENO_SEO_LOCALES),'unknownBrands'=>$unknown,'release'=>$package['release'],'dataset'=>$package['dataset'],'testSha256'=>hash_file('sha256',__FILE__),'warningsAsErrors'=>true,'networkCalled'=>false,'realPayments'=>false],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR).PHP_EOL;
