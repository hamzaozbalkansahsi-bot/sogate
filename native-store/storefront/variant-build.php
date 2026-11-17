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
$catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$groups=[];$result=[];
foreach($catalog['products']as $index=>$product){$prefix=substr(explode('_',$product['id'])[2],0,2);$groups[$prefix][]=$index;}
// Her özel kova bir kez okunur; tüm ham açıklamalar aynı anda bellekte tutulmaz.
foreach($groups as $prefix=>$indices){
 $work=json_decode(file_get_contents($private.'/catalog-workbench/'.$prefix.'.json'),true,128,JSON_THROW_ON_ERROR);
 foreach($indices as $index){$product=$catalog['products'][$index];$row=$work[$product['id']];$result[$product['id']]=['sizeOptions'=>$product['facts']['sizeOptions']??null,'colorOptions'=>$product['facts']['colorOptions']??null,'schema'=>sexogateSelectionSchema($product,$row)];}
 unset($work,$row);
}
file_put_contents($private.'/catalog-selections.json',json_encode($result,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR));
echo json_encode(['compiledSelectionProducts'=>count($result),'runtimeSourceWorkbenchRead'=>false]).PHP_EOL;
