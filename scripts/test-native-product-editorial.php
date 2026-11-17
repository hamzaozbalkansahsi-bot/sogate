<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-product-editorial.php
 * Açıklama   : Gerçek 958 üründe anlatımı, başlık/paket ayrımını ve ticari alanların değişmezliğini sınar.
 */
declare(strict_types=1);
require dirname(__DIR__).'/native-store/storefront/content.php';
$root=dirname(__DIR__);$selection=json_decode(file_get_contents($root.'/.local/native-marketplace-selection.json'),true,512,JSON_THROW_ON_ERROR);$file=$selection['path'].'/catalog-data.json';$before=hash_file('sha256',$file);$catalog=json_decode(file_get_contents($file),true,512,JSON_THROW_ON_ERROR);$extra=json_decode(file_get_contents($root.'/native-store/storefront/product-editorial-data.json'),true,512,JSON_THROW_ON_ERROR);$checks=0;$titles=0;$min=PHP_INT_MAX;$jubels=null;
function editorialCheck(bool $ok,string $key):void{global $checks;if(!$ok)throw new RuntimeException($key);$checks++;}
foreach(array_slice($catalog['products'],2194)as $product){
 $result=sexogateStorefrontProduct($product,$extra['products'][$product['id']]);
 foreach(['sku','code','brand','salePriceMinor','currency','facts','variantColor','variationSelectionRequired','eligibilityHold','stockKnown','stockQuantity','published','hidden','images','visualApprovedIndices']as $key)editorialCheck(($result[$key]??null)===($product[$key]??null),'protected_'.$key.'_'.$product['id']);
 editorialCheck(isset($result['storefrontStory']['tr']['paragraphs'],$result['storefrontStory']['en']['fields']),'rich_story_'.$product['id']);
 foreach(['tr','en']as $locale){editorialCheck(trim($result['storefrontStory'][$locale]['intro'])!=='','intro_'.$locale);editorialCheck(trim($result['description'][$locale])!=='','description_'.$locale);editorialCheck(!preg_match('/yorumlarını inceleyin|Trendyol.{0,120}satın alın/iu',$result['description'][$locale]),'no_platform_cta');}
 editorialCheck(!str_contains($result['name']['tr'],'*'),'no_star_title');
 editorialCheck(sexogateStorefrontProduct($result,$extra['products'][$product['id']])===$result,'idempotent_'.$product['id']);
 $titles+=(int)($result['name']['tr']!==$product['name']['tr']);$min=min($min,strlen($result['description']['tr']));
 if($product['sku']==='seo-16561-Serisi')$jubels=$result;
}
editorialCheck($jubels!==null,'jubels_found');editorialCheck($jubels['name']['tr']==='Bordo Kalp ve Dantel Detaylı Mini Gecelik Takımı','jubels_clean_title');editorialCheck(count($jubels['storefrontStory']['tr']['packageContents'])===3,'jubels_package');editorialCheck(str_contains(strtolower($jubels['description']['tr']),'polyester'),'jubels_actual_material');editorialCheck(!str_contains($jubels['description']['tr'],'T100'),'care_code_not_instruction');editorialCheck(str_contains($jubels['description']['en'],'skirt'),'actual_english_package');
$manual=$jubels;$manual['description']['tr']='Bu takımı bordo dantel ve kalp detaylarını birlikte arayanlar için seçtik. Üç parçayı birlikte veya ayrı kombinleyebilirsiniz.';$kept=sexogateStorefrontProduct($manual,$extra['products'][$manual['id']]);editorialCheck(str_contains($kept['description']['tr'],'birlikte veya ayrı kombinleyebilirsiniz'),'manual_prose_preserved');
$renamed=$jubels;$renamed['name']['tr']='Tek Parça Body';$renamed['facts']['materials']='Pamuk';$renamed=sexogateStorefrontProduct($renamed,$extra['products'][$renamed['id']]);editorialCheck($renamed['storefrontStory']['tr']['packageContents']===[],'stale_source_package_not_restored');
$meta=$jubels;$meta['description']['tr'].='\nYeni işletme notu.';$meta['seoTitle']['tr']='Bordo dantel seçkisi | SEXOGATE';$meta['seoDescription']['tr']='Bordo takımın malzeme, beden ve paket içeriğini inceleyin.';$meta=sexogateStorefrontProduct($meta,$extra['products'][$meta['id']]);editorialCheck($meta['seoTitle']['tr']==='Bordo dantel seçkisi | SEXOGATE'&&$meta['seoDescription']['tr']==='Bordo takımın malzeme, beden ve paket içeriğini inceleyin.','operator_seo_copy_preserved');
$decimal=$jubels;$decimal['name']['tr']='2.6 cm PVC Model';$decimal['facts']['dimensions']='2.6 cm';$decimal=sexogateStorefrontProduct($decimal,[]);editorialCheck(str_contains($decimal['name']['tr'],'2.6'),'decimal_preserved');editorialCheck(hash_file('sha256',$file)===$before,'frozen_catalog_unchanged');
editorialCheck(sexogateStorefrontClean('MEDİKAL SİLİKON')==='','upper_medical_claim_rejected');editorialCheck(sexogateStorefrontClean('SUYA DAYANIKLI')==='','upper_water_claim_rejected');
editorialCheck(sexogateStorefrontClean('Tehlikeli Değil')==='','classification_not_safety_instruction');editorialCheck(sexogateStorefrontClean('Ürünü temiz ve kuru bir yerde saklayın.')==='Ürünü temiz ve kuru bir yerde saklayın.','real_care_instruction_preserved');
editorialCheck(sexogateEditorialTitle('DILDO PENIS MINI')['title']==='Dildo Penis Mini','turkish_loanword_case');editorialCheck(sexogateEditorialTitle('Marka Marka Vibratör FWM1','Marka')['title']==='Vibratör FWM1','separate_brand_and_model_case');editorialCheck(sexogateEditorialTitle('Model (*Kullanım Uyarısı*Yalnız Haricen)')['package']===[],'warning_not_package');
editorialCheck(sexogateEditorialEnglish('Sarı')==='yellow','english_yellow');editorialCheck(sexogateEditorialTitle('GLIMMER GOLD')['title']==='Glimmer Gold','english_collection_case');editorialCheck(sexogateEditorialTitle('İncisiSırt Detayı')['title']==='İncisi Sırt Detayı','joined_title_words');
editorialCheck(sexogateEditorialTitle('Medikal Silikon Su Geçirmez Zevk Artırıcı Model')['title']==='Silikon Model','unsupported_title_claims_removed');
editorialCheck(sexogateEditorialTitle('MEDİKAL SİLİKON SUYA DAYANIKLI MODEL')['title']==='Silikon Model','uppercase_unsupported_title_claims_removed');
editorialCheck(sexogateEditorialTitle('Kalınlaştıcı Uzatıcı Tam Otomatik Penis Pompası')['title']==='Tam Otomatik Penis Pompası','unproven_enlargement_title_removed');
function sexogateRuntimeAdminSource(string $uri):bool{return $uri==='/api/admin/schema';}
$sourceProduct=$catalog['products'][2194];$_SERVER['REQUEST_URI']='/api/admin/schema';editorialCheck(sexogateStorefrontContextProduct($sourceProduct)===$sourceProduct,'admin_source_projection_not_duplicated');$_SERVER['REQUEST_URI']='/api/catalog';editorialCheck(isset(sexogateStorefrontContextProduct($sourceProduct)['storefrontStory']['tr']['intro']),'customer_keeps_full_editorial');unset($_SERVER['REQUEST_URI']);
foreach(['This penis sleeve.','This boxer shorts.','This tarot cards.']as $fragment)editorialCheck(!str_contains($jubels['description']['en'],$fragment),'english_sentence_not_fragment');
$manualEn=$jubels;$manualEn['description']['en']='The burgundy set combines lace accents with a matching skirt. The three pieces can be worn together.';$manualEn=sexogateStorefrontProduct($manualEn,$extra['products'][$manualEn['id']]);editorialCheck(str_contains($manualEn['description']['en'],'can be worn together'),'manual_english_preserved');
echo json_encode(['passed'=>$checks,'products'=>count($extra['products']),'titlesCleaned'=>$titles,'minimumTrDescriptionBytes'=>$min,'jubels'=>['title'=>$jubels['name']['tr'],'titleEn'=>$jubels['name']['en'],'description'=>$jubels['description']['tr'],'descriptionEn'=>$jubels['description']['en'],'story'=>$jubels['storefrontStory']['tr']],'sourcePreserved'=>true,'realApiCalled'=>false],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
