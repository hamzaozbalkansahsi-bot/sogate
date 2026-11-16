<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-marketplace-payload.php
 * Açıklama   : Gerçek derlemede kaynak kodu, %15 fiyat, medya, varyant ve arşiv korumasını izole veritabanında doğrular.
 */
declare(strict_types=1);
$repo=dirname(__DIR__);$package=json_decode(file_get_contents($repo.'/.local/native-stage-package.json'),true);$private=$package['bundle'].'/private';require $private.'/control-http.php';
$installer=file_get_contents($repo.'/native-store/deploy/install.php');$stop=strpos($installer,"\nini_set('display_errors'");if($stop===false)throw new RuntimeException('INSTALLER_FUNCTION_BOUNDARY_CHANGED');$temp=tempnam(sys_get_temp_dir(),'sg-provenance-');file_put_contents($temp,substr($installer,0,$stop));try{require $temp;}finally{unlink($temp);}
$catalog=json_decode(file_get_contents($private.'/catalog.json'),true);$source=json_decode(file_get_contents($private.'/catalog-sources.json'),true);$new=array_values(array_filter($catalog['products'],static fn($p)=>($p['catalogOrigin']??'')==='sexogate-marketplaces-v1'));$checks=[];
function marketplaceCheck(bool $ok,string $key):void{global $checks;if(!$ok)throw new RuntimeException($key);$checks[]=$key;}
marketplaceCheck(count($new)>0&&count($catalog['products'])===2194+count($new),'new_and_archived_namespaces');marketplaceCheck(sexogateNativeCategoryTree($catalog['categories'],$catalog['products']),'category_tree_valid');
$codes=[];$approved=0;$variants=0;
foreach($catalog['products']as $p){if(!sexogateNativeProductProvenance($p,$catalog['catalogOrigin']))throw new RuntimeException('source_profile_invalid');if(isset($codes[$p['code']]))throw new RuntimeException('duplicate_sku');$codes[$p['code']]=true;}
marketplaceCheck(true,'all_source_profiles_and_skus_valid');
foreach($new as $p){marketplaceCheck(str_starts_with($p['code'],'seo-'),'source_code_prefix');marketplaceCheck($p['salePriceMinor']===intdiv($p['privateRetailReference']*115+50,100),'markup_15_final_integer');marketplaceCheck(!$p['stockKnown']&&$p['stockQuantity']===null&&!$p['referencePriceVerified']&&$p['additionalDiscountPercent']===0,'no_fake_inventory_or_discount');$schema=sexogateSelectionProduct($p);if($schema['required'])$variants++;$approved+=count($p['visualApprovedIndices'])>0&&!$p['eligibilityHold'];}
marketplaceCheck($approved>0&&$variants>0,'reviewed_covers_and_real_options');
$bad=$new[0];$bad['sourceVendor']='nodeno';marketplaceCheck(!sexogateNativeProductProvenance($bad,$catalog['catalogOrigin']),'foreign_brand_data_rejected');$bad=$new[0];$bad['code']='xsh-relabelled';marketplaceCheck(!sexogateNativeProductProvenance($bad,$catalog['catalogOrigin']),'wrong_code_prefix_rejected');marketplaceCheck(!sexogateNativeProductProvenance($new[0],'sexogate-suppliers-v1'),'marketplace_cannot_claim_supplier_origin');
$state=sys_get_temp_dir().'/sexogate-marketplace-test-'.bin2hex(random_bytes(8));mkdir($state,0700);$db=nodenoControlDatabase($state);$id='isolated-marketplace-review';$db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at)VALUES(?,?,?,?,?,?,?,?)')->execute([$id,'isolated@example.invalid','İzole yönetim','owner','not-a-web-login','not-a-web-login',time(),time()]);$ctx=['db'=>$db,'root'=>$state,'user'=>['id'=>$id,'role'=>'owner'],'permissions'=>['*']];$_SESSION=['elevatedAt'=>time()];
$first=sexogateCatalogAdmin($ctx,'catalog-import','POST',['dataset'=>$source['dataset'],'offset'=>2194],$catalog,[]);$second=sexogateCatalogAdmin($ctx,'catalog-import','POST',['dataset'=>$source['dataset'],'offset'=>2194],$catalog,[]);marketplaceCheck($first===$second&&(int)$db->query("SELECT COUNT(*)FROM control_records WHERE resource='products'")->fetchColumn()===min(40,count($new)),'batch_import_idempotent');
$record=nodenoControlRead($db,'products',$new[0]['id']);$data=$record['data'];$data['priceMinor']+=123;$saved=nodenoControlResource($ctx,'products',$new[0]['id'],'PUT',['version'=>$record['version'],'data'=>$data],$catalog,[]);$again=sexogateCatalogAdmin($ctx,'catalog-import','POST',['dataset'=>$source['dataset'],'offset'=>2194],$catalog,[]);marketplaceCheck(nodenoControlRead($db,'products',$new[0]['id'])['data']['priceMinor']===$data['priceMinor'],'manual_price_survives_replay');
$editor=sexogateCatalogEditor($new[0],[],$private);marketplaceCheck(str_contains($editor['initialMarkup'],'%15')&&str_starts_with($editor['sourceUrl'],'https://www.trendyol.com/'),'admin_real_source_and_rule');
echo json_encode(['passed'=>count($checks),'newProducts'=>count($new),'publishCandidates'=>$approved,'productsWithOptions'=>$variants,'isolatedDatabase'=>true,'publishedToRemote'=>false],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
