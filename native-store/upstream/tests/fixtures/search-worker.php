<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli')exit(1);
$in=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);$private=$in['private'];$storage=$in['storage'];$_SERVER['DOCUMENT_ROOT']='';require_once $private.'/search-notifications.php';require_once $private.'/control-indexnow.php';require_once $private.'/blog-worker.php';
$now=time();$b=nodenoBlogTick($storage,$private,$in['public'],$now);$sent=[];$transport=static function($urls,$key,$endpoint)use(&$sent){$sent[]=$urls;return ['httpStatus'=>200];};
$bootstrap=['key'=>'d9af889838b591967667b2dbe1d423a3','endpoint'=>'https://yandex.com/indexnow','baselineUrls'=>$in['baseline']];
$first=nodenoSearchTick($storage,$private,$bootstrap,$now,$transport);$second=nodenoSearchTick($storage,$private,$bootstrap,$now+60,$transport);$db=nodenoControlDatabase(nodenoAccountStorage($storage));$catalog=json_decode(file_get_contents($private.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$p=$catalog['products'][0];$id=(string)$p['id'];$changed=json_encode(['priceMinor'=>12345]);$db->prepare('INSERT INTO control_records(resource,id,data_json,version,published_json,published_version,created_at,updated_at,published_at)VALUES(?,?,?,?,?,?,?,?,?)')->execute(['products',$id,$changed,1,$changed,1,$now,$now,$now]);nodenoControlSetSetting($db,'public_revision',1);unset($catalog,$p);
$third=nodenoSearchTick($storage,$private,$bootstrap,$now+301,$transport);
$bank=nodenoBlogReadBank($private);$draft=$bank['articles'][2];$blogDb=nodenoBlogDatabase($storage);nodenoBlogPublishNow($blogDb,$bank,$draft['id'],$in['public'],$now+302,'test-editor',$private);$fourth=nodenoSearchTick($storage,$private,$bootstrap,$now+602,$transport);
echo json_encode(['blog'=>$b,'first'=>$first,'second'=>$second,'third'=>$third,'fourth'=>$fourth,'sent'=>$sent,'changedProduct'=>$id,'newArticleSlug'=>$draft['slug']],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
