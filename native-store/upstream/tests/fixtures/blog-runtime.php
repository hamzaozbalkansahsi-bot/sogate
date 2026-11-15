<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') exit(1);
$input=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);
$root=dirname(__DIR__,2);
if(isset($input['workingDirectory']))chdir($input['workingDirectory']);
if(!is_file($root.'/hosting/blog-worker.php')){echo '{"available":false}';exit;}
$operation=$input['operation']??'tick';
if($operation==='http-health'){
 define('NODENO_RUNTIME_LIBRARY',true);
 require $input['public'].'/index.php';
 $_SERVER['REQUEST_URI']='/api/health';$_SERVER['REQUEST_METHOD']='GET';$_SERVER['DOCUMENT_ROOT']=$input['public'];
 ob_start();nodenoRun();$body=ob_get_clean();
 echo json_encode(['available'=>true,'result'=>['status'=>http_response_code(),'body'=>json_decode($body,true,512,JSON_THROW_ON_ERROR)]],JSON_THROW_ON_ERROR);exit;
}
require $root.'/hosting/blog-worker.php';
try{
 if($operation==='tick')$result=nodenoBlogTick($input['storage'],$input['private'],$input['public'],$input['now']);
 elseif($operation==='media-health')$result=nodenoBlogMediaHealth($input['storage'],$input['private'],$input['public']);
 elseif($operation==='series'){$result=[];foreach($input['times'] as $stamp)$result[]=['at'=>$stamp]+nodenoBlogTick($input['storage'],$input['private'],$input['public'],$stamp);}
 else{
  $db=nodenoBlogDatabase($input['storage']);$bank=nodenoBlogReadBank($input['private']);
  if($operation==='read')$result=['published'=>nodenoBlogPublished($db,$bank,$input['locale']??'tr',$input['options']??[]),'article'=>isset($input['slug'])?nodenoBlogArticle($db,$bank,$input['slug'],$input['locale']??'tr'):null,'status'=>nodenoBlogStatus($db,$bank)];
  elseif($operation==='command')$result=nodenoBlogCommand($db,$bank,$input['action'],$input['body']??[],'test-editor',$input['now']);
  elseif($operation==='lock'){$lock=fopen($input['storage'].'/blog-worker.lock','c');flock($lock,LOCK_EX);$result=nodenoBlogTick($input['storage'],$input['private'],$input['public'],$input['now']);flock($lock,LOCK_UN);fclose($lock);}
  elseif($operation==='stale-bank')$result=nodenoBlogPublishNow($db,$input['bank'],$input['id'],$input['public'],$input['now'],'test-editor');
  elseif($operation==='admin'){
   require $root.'/hosting/control-auth.php';require $root.'/hosting/blog-admin.php';
   $_SESSION['elevatedAt']=time();$ctx=['root'=>$input['storage'],'publicRoot'=>$input['public'],'db'=>null,'user'=>empty($input['user'])?null:['id'=>'test-editor'],'permissions'=>$input['permissions']??[]];
   $result=nodenoBlogAdmin($ctx,$input['route']??'blog',$input['method']??'GET',$input['body']??[],$input['private']);
  }else throw new RuntimeException('invalid_fixture_operation');
 }
 echo json_encode(['available'=>true,'result'=>$result],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
}catch(Throwable $e){echo json_encode(['available'=>true,'error'=>get_class($e),'code'=>$e instanceof NodenoControlHttpError?$e->errorCode:$e->getMessage()],JSON_THROW_ON_ERROR);}
