<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/variant-build.php
 * Açıklama   : Özel kaynak dosyalarını her vitrin isteğinde açmadan küçük seçenek indeksi derler.
 */
declare(strict_types=1);
require __DIR__.'/variants.php';$private=$argv[1]??'';if(!str_contains($private,'native-stage-'))throw new RuntimeException('selection_build_scope');
$catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$work=[];$result=[];
foreach($catalog['products']as $product){$prefix=substr(explode('_',$product['id'])[2],0,2);if(!isset($work[$prefix]))$work[$prefix]=json_decode(file_get_contents($private.'/catalog-workbench/'.$prefix.'.json'),true,128,JSON_THROW_ON_ERROR);$row=$work[$prefix][$product['id']];$result[$product['id']]=['sizeOptions'=>$product['facts']['sizeOptions']??null,'colorOptions'=>$product['facts']['colorOptions']??null,'schema'=>sexogateSelectionSchema($product,$row)];}
file_put_contents($private.'/catalog-selections.json',json_encode($result,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR));
echo json_encode(['compiledSelectionProducts'=>count($result),'runtimeSourceWorkbenchRead'=>false]).PHP_EOL;
