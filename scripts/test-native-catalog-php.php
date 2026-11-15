<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-catalog-php.php
 * Açıklama   : İzole SQLite üzerinde gerçek katalog doğrulaması, yetki ve fiyat korumasını sınar.
 */
declare(strict_types=1);
$root=dirname(__DIR__);$package=json_decode((string)file_get_contents($root.'/.local/native-stage-package.json'),true,512,JSON_THROW_ON_ERROR);$private=$package['bundle'].'/private';require $private.'/control-http.php';
$catalog=json_decode((string)file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$source=json_decode((string)file_get_contents($private.'/catalog-sources.json'),true,512,JSON_THROW_ON_ERROR);$state='D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-check-'.bin2hex(random_bytes(8));mkdir($state,0700);$db=nodenoControlDatabase($state);$checks=[];
function verify(bool $ok,string $name):void{global $checks;if(!$ok)throw new RuntimeException($name);$checks[]=$name;}
function denied(callable $action,int $status,string $name):void{try{$action();}catch(NodenoControlHttpError $e){verify($e->status===$status,$name);return;}throw new RuntimeException($name);}
foreach(['a','b']as $suffix)$db->prepare('INSERT INTO control_users(id,email,display_name,role,password_hash,totp_secret,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)')->execute(['isolated_'.$suffix,$suffix.'@example.invalid','İzole test','owner',password_hash('isolated-catalog-check-only',PASSWORD_BCRYPT),'isolated-no-web-login',time(),time()]);
$actor=['id'=>'isolated_a','role'=>'owner'];$ctx=['db'=>$db,'root'=>$state,'user'=>$actor,'permissions'=>['*']];$_SESSION=['elevatedAt'=>time()];
$product=$catalog['products'][0];$id=$product['id'];$data=sexogateCatalogInitial($product,$private);$without=$catalog;$without['products'][0]['images']=[];$data['visible']=false;$data['coverIndex']=0;$data['imageApprovedIndices']='';sexogateCatalogValidate('products',$id,$data,$without);verify(true,'image_missing_draft_allowed');
$data['visible']=true;denied(fn()=>sexogateCatalogValidate('products',$id,$data,$without),422,'image_missing_publication_denied');
denied(fn()=>sexogateCatalogValidate('products',$id,['barcode'=>'12345678'],$catalog),422,'invalid_barcode');denied(fn()=>sexogateCatalogValidate('products',$id,['imageApprovedIndices'=>'00'],$catalog),422,'image_index_canonical');denied(fn()=>sexogateCatalogValidate('products',$id,['sku'=>$catalog['products'][1]['code']],$catalog),422,'duplicate_sku');
$operations=array_replace($ctx,['user'=>['id'=>'isolated_b','role'=>'operations'],'permissions'=>nodenoControlPermissions('operations')]);denied(fn()=>sexogateCatalogAdmin($operations,'catalog-source','GET',[],$catalog,[]),403,'operations_source_denied');$_SESSION['elevatedAt']=time()-301;denied(fn()=>sexogateCatalogAdmin($ctx,'catalog-import','POST',['dataset'=>$source['dataset'],'offset'=>0],$catalog,[]),403,'fresh_mfa_required');$_SESSION['elevatedAt']=time();
$body=['dataset'=>$source['dataset'],'offset'=>0];$first=sexogateCatalogAdmin($ctx,'catalog-import','POST',$body,$catalog,[]);verify($first['created']===40,'first_batch_real_resource_save');$record=nodenoControlRead($db,'products',$id);$updated=$record['data'];$updated['priceMinor']+=123;$saved=nodenoControlResource($ctx,'products',$id,'PUT',['version'=>$record['version'],'data'=>$updated],$catalog,[]);$before=nodenoControlRead($db,'products',$id);
$second=sexogateCatalogAdmin(array_replace($ctx,['user'=>['id'=>'isolated_b','role'=>'owner']]),'catalog-import','POST',$body,$catalog,[]);$after=nodenoControlRead($db,'products',$id);verify($second['created']===0&&$second['preserved']===40&&$before===$after,'new_actor_reimport_preserves_manual_price_and_version');
$replay=sexogateCatalogAdmin($ctx,'catalog-import','POST',$body,$catalog,[]);verify($replay===$first&&(int)$db->query("SELECT COUNT(*) FROM control_records WHERE resource='products'")->fetchColumn()===40,'command_replay_idempotent');
denied(fn()=>sexogateCatalogValidate('products',$catalog['products'][1]['id'],['sku'=>$updated['sku']],$catalog,$db),422,'overridden_sku_unique');$projected=sexogateCatalogProjection($product,['visible'=>false,'materials'=>'Doğrulanmış test değeri']);verify($projected['attributes'][0]['value']['tr']==='Doğrulanmış test değeri'&&$projected['stockQuantity']===null,'edited_facts_project_without_fake_stock');
echo json_encode(['passed'=>count($checks),'checks'=>$checks,'isolated'=>true,'realCharging'=>false],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
