<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-installer.php
 * Açıklama   : Kurucunun saf manifest/katalog sınırlarını gerçek pakette, HTTP ve kurulum olmadan doğrular.
 */
declare(strict_types=1);
$root=dirname(__DIR__);$source=file_get_contents($root.'/native-store/deploy/install.php');$stop=strpos($source,"\nini_set('display_errors'");
if($stop===false)throw new RuntimeException('installer_function_boundary_changed');
$temporary=tempnam(sys_get_temp_dir(),'sexogate-installer-pure-');file_put_contents($temporary,substr($source,0,$stop));try{require $temporary;}finally{unlink($temporary);}
$package=json_decode(file_get_contents($root.'/.local/native-stage-package.json'),true,512,JSON_THROW_ON_ERROR);
$manifest=json_decode(file_get_contents($package['bundle'].'/deployment-manifest.json'),true,512,JSON_THROW_ON_ERROR);
$catalog=json_decode(file_get_contents($package['bundle'].'/private/catalog.json'),true,512,JSON_THROW_ON_ERROR);
$zip=new ZipArchive();if($zip->open($package['archive'])!==true)throw new RuntimeException('actual_archive_unavailable');$files=$zip->numFiles;$zip->close();$checks=[];
function installerCheck(bool $condition,string $name):void{global $checks;if(!$condition)throw new RuntimeException($name);$checks[]=$name;}
installerCheck(sexogateNativeManifestValid($manifest,$package['release'],$files),'actual_manifest_and_archive_count');
installerCheck(sexogateNativeCatalogValid($catalog,$manifest),'actual_catalog_provenance');
installerCheck(sexogateNativeEntrySizeValid('private/catalog.json',26608336,79000000)&&!sexogateNativeEntrySizeValid('private/catalog.json',32000001,79000000),'expanded_catalog_bounded');
installerCheck(!sexogateNativeEntrySizeValid('private/other.json',25000001,79000000)&&!sexogateNativeEntrySizeValid('private/catalog.json',26608336,80000001)&&!sexogateNativeEntrySizeValid('private/catalog.json',-1,0),'other_file_and_total_limits_preserved');
installerCheck($manifest['products']===count($catalog['products'])&&$manifest['products']>2194&&$files>2000,'actual_marketplace_and_sdk_package');
$empty=$manifest;$empty['products']=0;$empty['dataset']=null;
installerCheck(sexogateNativeManifestValid($empty,$package['release'],$files)&&sexogateNativeCatalogValid(['brand'=>['name'=>'SEXOGATE'],'products'=>[],'categories'=>[]],$empty),'empty_catalog_supported');
$legacy=$manifest;$legacy['products']=2194;$legacyCatalog=$catalog;$legacyCatalog['products']=array_slice($catalog['products'],0,2194);$legacyCatalog['catalogOrigin']='sexogate-suppliers-v1';
installerCheck(sexogateNativeManifestValid($legacy,$package['release'],$files)&&sexogateNativeCatalogValid($legacyCatalog,$legacy),'legacy_catalog_supported');
$dynamic=$manifest;$dynamic['products']++;$dynamicCatalog=$catalog;$extra=$catalog['products'][2194];$extra['id']='sg_ty_'.substr(hash('sha256','isolated-installer-dynamic-count'),0,16);$extra['code']='seo-isolated-installer-dynamic-count';$dynamicCatalog['products'][]=$extra;
installerCheck(sexogateNativeManifestValid($dynamic,$package['release'],$files)&&sexogateNativeCatalogValid($dynamicCatalog,$dynamic),'v2_count_is_dynamic');
installerCheck(!sexogateNativeCatalogValid($catalog,$dynamic),'wrong_catalog_count_rejected');
$bad=$manifest;$bad['checkoutEnabled']=true;installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'checkout_enabled_rejected');
$bad=$manifest;$bad['previewOnly']=false;installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'non_preview_rejected');
$bad=$manifest;$bad['schema']=2;installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'unknown_schema_rejected');
$bad=$manifest;$bad['products']=20001;installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'huge_product_count_rejected');
$bad=$manifest;$bad['products']='2325';installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'string_product_count_rejected');
installerCheck(!sexogateNativeManifestValid($manifest,$package['release'],5001),'huge_archive_file_count_rejected');
installerCheck(!sexogateNativeManifestValid($manifest,$package['release'],$files+1),'archive_file_count_mismatch_rejected');
$bad=$manifest;$bad['fingerprint']=str_repeat('0',64);installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'fingerprint_mismatch_rejected');
$bad=$manifest;$bad['files'][array_key_first($bad['files'])]='invalid';installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'invalid_file_hash_rejected');
$bad=$manifest;$bad['files']['private/../escape.php']=str_repeat('a',64);installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files+1),'unsafe_archive_path_rejected');
$bad=$manifest;$bad['domain']='another.example';installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'foreign_domain_rejected');
$bad=$manifest;$bad['mount']='/';installerCheck(!sexogateNativeManifestValid($bad,$package['release'],$files),'main_site_mount_rejected');
$bad=$catalog;$bad['catalogOrigin']='arbitrary-catalog';installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'arbitrary_catalog_origin_rejected');
$bad=$catalog;$bad['products'][2194]['sourceVendor']='nodeno';installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'foreign_vendor_rejected');
$bad=$catalog;$bad['products'][2194]['code']='xsh-relabelled';installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'marketplace_code_identity_rejected');
$bad=$catalog;$bad['products'][0]['id']='sg_ty_'.substr(hash('sha256','wrong-supplier-prefix'),0,16);installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'supplier_namespace_mismatch_rejected');
foreach(['published'=>true,'hidden'=>false,'stockKnown'=>true,'stockQuantity'=>5]as $field=>$value){$bad=$catalog;$bad['products'][2194][$field]=$value;installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'unsafe_'.$field.'_rejected');}
$bad=$catalog;$bad['products'][2194]['id']=$bad['products'][2195]['id'];installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'duplicate_product_identity_rejected');
$bad=$catalog;$bad['products'][2194]['code']=$bad['products'][2195]['code'];installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'duplicate_product_code_rejected');
$bad=$catalog;$bad['products'][2194]['categoryIds']=['unknown-category'];installerCheck(!sexogateNativeCatalogValid($bad,$manifest),'unknown_category_rejected');
echo json_encode(['passed'=>count($checks),'release'=>$package['release'],'products'=>$manifest['products'],'archiveFiles'=>$files,'checks'=>$checks,'pureValidationOnly'=>true,'networkCalled'=>false,'installed'=>false],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR).PHP_EOL;
