<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-storefront-content.php
 * Açıklama   : Okunabilir ürün özetinin ölçüleri ayırmasını ve doğrulanmamış iddia üretmemesini sınar.
 */
declare(strict_types=1);require dirname(__DIR__).'/native-store/storefront/content.php';
$product=['catalogOrigin'=>'sexogate-suppliers-v1','name'=>['tr'=>'11 cm Vantuzlu Jel Anal Plug','en'=>'Compact model'],'facts'=>['dimensions'=>'11 cm Çap: 3,8 cm Ağırlık: 93 gr Kullanım Talimatları: uzun kaynak metni','materials'=>'PVC','colorOptions'=>'Kırmızı'],'description'=>['tr'=>'Maksimum uyarılma sağlar.']];$result=sexogateStorefrontProduct($product);$checks=0;
function expect(bool $value):void{global $checks;if(!$value)throw new RuntimeException('storefront_content_failed');$checks++;}
expect($result['storefrontFacts']['dimensions']==='11 cm');expect($result['storefrontFacts']['diameter']==='3,8 cm');expect($result['storefrontFacts']['weight']==='93 gr');expect(!str_contains($result['description']['tr'],'Kullanım Talimatları'));expect(!str_contains($result['description']['tr'],'Maksimum'));expect(count($result['storefrontStory'])===11);expect(substr_count($result['description']['tr'],'11 cm Vantuzlu')===0);expect(!array_key_exists('manufacturer',$result['storefrontFacts']));expect($product['description']['tr']==='Maksimum uyarılma sağlar.');
expect(sexogateStorefrontClean('Medikal silikon')==='');expect(sexogateStorefrontClean('none')==='');expect(sexogateStorefrontProduct(['name'=>['tr'=>'Başka kaynak']])===['name'=>['tr'=>'Başka kaynak']]);$bad=$product;$bad['facts']['materials']='Ürünün hijyenik ve doğal yapısının daha uzun süre korunması için kaliteli malzemelerden üretilmiştir';expect(!isset(sexogateStorefrontProduct($bad)['storefrontFacts']['materials']));$bad['facts']['materials']='Cilt dostu, yumuşak silikon Yüzey: Pürüzsüz ve kaygan';expect(sexogateStorefrontProduct($bad)['storefrontFacts']['materials']==='silikon');echo json_encode(['passed'=>$checks,'sourceRecordUnchanged'=>true,'inventedFacts'=>false],JSON_THROW_ON_ERROR);
