<?php
declare(strict_types=1);
require_once __DIR__.'/social-providers.php';

function nodenoStudioAsset(PDO $db,string $root,string $body,string $extension,string $mime):string {
 if(!in_array($extension,['png','mp3'],true)||strlen($body)>12000000)throw new RuntimeException('Invalid social asset');
 $hash=hash('sha256',$body);$folder=nodenoStudioRoot($root);$file=$folder.'/'.$hash.'.'.$extension;
 if(is_link($file))throw new RuntimeException('Unsafe asset path');
 if(!is_file($file)){$temporary=$folder.'/'.bin2hex(random_bytes(16)).'.tmp';if(file_put_contents($temporary,$body,LOCK_EX)!==strlen($body))throw new RuntimeException('Asset write failed');chmod($temporary,0600);if(!rename($temporary,$file))throw new RuntimeException('Asset finalize failed');}
 $db->prepare('INSERT OR IGNORE INTO social_assets(hash,extension,mime,bytes,created_at) VALUES(?,?,?,?,?)')->execute([$hash,$extension,$mime,strlen($body),time()]);return $hash;
}

function nodenoStudioOriginal(array $p,string $private,string $vault,string $publicRoot,int $index=0):string {
 $url=$p['images'][$index]??$p['images'][0]??'';$path=(string)parse_url($url,PHP_URL_PATH);$expected=null;
 if(preg_match('~^/media/([A-Za-z0-9_-]+)/([0-9]+)$~D',$path,$m)){
  if(str_starts_with($m[1],'door-')||str_starts_with($m[1],'front-')){
   $front=str_starts_with($m[1],'front-');$data=json_decode(file_get_contents($private.'/'.($front?'cabinet-fronts.json':'door-catalog.json')),true,64,JSON_THROW_ON_ERROR);if(($data['publicationReady']??false)!==true)throw new RuntimeException('Unapproved catalogue image');
   $product=null;foreach($data['products']??[] as $entry)if($entry['id']===$m[1]){$product=$entry;break;}$hash=$product['assetHashes'][(int)$m[2]]??null;$asset=$data['assets'][$hash]??null;
   if(!$asset||!is_string($hash)||!preg_match('/^[a-f0-9]{64}$/D',$hash)||!preg_match('~^/assets/(?:doors|fronts)/[a-f0-9]{64}\.(?:jpg|png|webp)$~D',$asset['path']??''))throw new RuntimeException('Unapproved catalogue image');
   $copy=$p;$copy['images']=[$asset['path']];$body=nodenoStudioOriginal($copy,$private,$vault,$publicRoot,0);if(!hash_equals($hash,hash('sha256',$body)))throw new RuntimeException('Catalogue image hash changed');return $body;
  }
  $approved=json_decode(file_get_contents($private.'/media-approved.json'),true);$source=$approved['references'][$m[1].':'.$m[2]]??null;$row=$source?$approved['images'][$source]??null:null;
  if(!$row||!in_array($row['state'],['approved_unmodified','approved_cleaned'],true))throw new RuntimeException('Unapproved social image');
  $extensions=['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp','image/avif'=>'avif'];$extension=$extensions[$row['mime']]??null;if(!$extension)throw new RuntimeException('Social image format unavailable');$file=$vault.'/'.$row['outputSha'].'.'.$extension;$expected=$row['outputSha'];$base=$vault;
 }elseif(preg_match('~^/assets/(?:suppliers|doors|fronts)/[A-Za-z0-9_./-]+\.(?:png|jpe?g|webp)$~D',$path)&&!str_contains($path,'..')){$file=$publicRoot.$path;$base=$publicRoot.'/assets';$manifest=json_decode(file_get_contents($private.'/release.json'),true);$expected=$manifest['files']['public'.$path]??null;if(!is_string($expected)||!preg_match('/^[a-f0-9]{64}$/D',$expected))throw new RuntimeException('Unapproved public image');}
 else throw new RuntimeException('Unapproved social image path');
 $resolved=realpath($file);$base=realpath($base);if(!$resolved||!$base||is_link($file)||!str_starts_with(str_replace('\\','/',$resolved),rtrim(str_replace('\\','/',$base),'/').'/')||filesize($resolved)>20000000)throw new RuntimeException('Social image unavailable');
 $body=file_get_contents($resolved);if($expected&&!hash_equals($expected,hash('sha256',$body)))throw new RuntimeException('Social image hash changed');return $body;
}

function nodenoStudioHeadline(string $topic,string $locale,string $tone,string $private,string $publicRoot):string {
 if(!in_array($topic,['coffee','work','storage','entry','living','kids','diy'],true)||!in_array($locale,NODENO_SOCIAL_LOCALES,true)||!in_array($tone,['ink','white'],true))throw new RuntimeException('Invalid campaign template');
 $path='/assets/social-headlines/headline-'.$topic.'-'.$locale.'-'.$tone.'.png';$manifest=json_decode(file_get_contents($private.'/release.json'),true);$expected=$manifest['files']['public'.$path]??null;$file=$publicRoot.$path;
 if(!is_string($expected)||!is_file($file)||is_link($file)||filesize($file)>1000000||!hash_equals($expected,hash_file('sha256',$file)))throw new RuntimeException('Unapproved campaign template');return file_get_contents($file);
}

function nodenoStudioRenderImage(PDO $db,string $root,array $post,array $product,string $private,string $vault,string $publicRoot):array {
 if(!function_exists('imagecreatefromstring'))throw new RuntimeException('image_renderer_unavailable');
 $w=1080;$h=1350;$hashes=[];$payload=json_decode($post['payload_json']??'{}',true);
 $profile=nodenoStudioCreativeProfile($product);$frames=$profile['frames']??[];
 $count=$post['format']==='carousel'?max(1,min(3,count($frames))):1;
 for($i=0;$i<$count;$i++){
  $frame=$frames[$i]??null;$body=nodenoStudioOriginal($product,$private,$vault,$publicRoot,$frame['index']??$product['coverIndex']??0);$size=getimagesizefromstring($body);if(!$size||$size[0]*$size[1]>50000000)throw new RuntimeException('Social image too large');$source=imagecreatefromstring($body);if(!$source)throw new RuntimeException('Social image decoding failed');
  if($frame&&!hash_equals($frame['sha256'],hash('sha256',$body)))throw new RuntimeException('Creative source changed');
  $canvas=imagecreatetruecolor($w,$h);$ivory=imagecolorallocate($canvas,245,242,233);$navy=imagecolorallocate($canvas,23,45,56);$lime=imagecolorallocate($canvas,216,236,129);$white=imagecolorallocate($canvas,255,255,255);imagefill($canvas,0,0,$ivory);
  if($frame){
   [$cx,$cy,$cw,$ch]=$frame['crop'];if($cx<0||$cy<0||$cw<=0||$ch<=0||$cx+$cw>1.0001||$cy+$ch>1.0001)throw new RuntimeException('Invalid reviewed crop');
   // Keep the reviewed photo's aspect ratio; never stretch product geometry.
   $targetH=$h;$targetW=(int)round($h*($cw*$size[0])/($ch*$size[1]));if($targetW>$w){$targetW=$w;$targetH=(int)round($w*($ch*$size[1])/($cw*$size[0]));}
   imagecopyresampled($canvas,$source,(int)(($w-$targetW)/2),(int)(($h-$targetH)/2),(int)round($cx*$size[0]),(int)round($cy*$size[1]),$targetW,$targetH,(int)round($cw*$size[0]),(int)round($ch*$size[1]));
  }else{$scale=min($w/$size[0],$h/$size[1]);$dw=(int)round($size[0]*$scale);$dh=(int)round($size[1]*$scale);imagecopyresampled($canvas,$source,(int)(($w-$dw)/2),(int)(($h-$dh)/2),0,0,$dw,$dh,$size[0],$size[1]);}
  $tone=$frame['tone']??'ink';$markFile=$publicRoot.'/assets/brand/social-logo'.($tone==='white'?'-white':'').'.png';$manifest=json_decode(file_get_contents($private.'/release.json'),true);$expected=$manifest['files']['public/assets/brand/'.basename($markFile)]??null;
  $verified=is_string($expected)&&is_file($markFile)&&!is_link($markFile)&&hash_equals($expected,hash_file('sha256',$markFile));if($profile&&!$verified)throw new RuntimeException('Approved wordmark missing');
  if($verified){$mark=imagecreatefrompng($markFile);if(!$mark)throw new RuntimeException('Wordmark decoding failed');$markW=210;$markH=(int)round($markW*imagesy($mark)/imagesx($mark));imagecopyresampled($canvas,$mark,$w-$markW-44,42,0,0,$markW,$markH,imagesx($mark),imagesy($mark));unset($mark);}
  ob_start();imagepng($canvas,null,6);$png=ob_get_clean();unset($canvas,$source);$hashes[]=nodenoStudioAsset($db,$root,$png,'png','image/png');
 }
 return $hashes;
}

function nodenoStudioVideoRequest(array $p,array $payload,string $platform,?array $music=null):array {
 $clips=[];$images=array_slice($p['images'],0,4);foreach($images as $index=>$image){$url='https://nodenohome.com'.parse_url($image,PHP_URL_PATH);$clips[]=['asset'=>['type'=>'image','src'=>$url],'start'=>$index*4,'length'=>4,'fit'=>'contain','effect'=>'zoomIn','transition'=>['in'=>'fade','out'=>'fade']];}
 $timeline=['background'=>'#F5F2E9','tracks'=>[['clips'=>$clips]]];
 if($music)$timeline['soundtrack']=['src'=>$music['url'],'effect'=>'fadeInFadeOut','volume'=>0.3];
 $logo=['asset'=>['type'=>'image','src'=>'https://nodenohome.com/assets/brand/social-logo.png'],'start'=>0,'length'=>count($images)*4,'position'=>'topRight','scale'=>0.14,'offset'=>['x'=>-0.04,'y'=>-0.04]];
 array_unshift($timeline['tracks'],['clips'=>[$logo]]);
 return ['timeline'=>$timeline,'output'=>['format'=>'mp4','resolution'=>'hd','aspectRatio'=>'9:16','fps'=>30]];
}

function nodenoStudioRenderVideo(PDO $db,string $root,array $post,array $p,array $settings,?callable $transport=null):array {
 $payload=json_decode($post['payload_json'],true);$music=null;
 if(!empty($payload['musicId'])){$q=$db->prepare('SELECT data_json FROM social_music WHERE id=?');$q->execute([$payload['musicId']]);$json=$q->fetchColumn();$music=$json?json_decode($json,true):null;if(!$music||!nodenoStudioMusicAllowed($music,$post['platform'],$post['locale']==='tr'?'TR':'*',time()))throw new NodenoControlHttpError(422,'social_music_license_required');$hash=basename(parse_url($music['url'],PHP_URL_PATH),'.mp3');$db->prepare('UPDATE social_assets SET public=1 WHERE hash=?')->execute([$hash]);}
 if(!empty($payload['renderId'])){
  $r=nodenoStudioSend($db,$root,'GET','/render/'.rawurlencode($payload['renderId']).'?data=false',null,$transport,'shotstack');$render=$r['data']['response']??[];
  if($r['code']===200&&($render['status']??'')==='done'){$u=parse_url($render['url']??'');$host=$u['host']??'';if(($u['scheme']??'')!=='https'||isset($u['user'])||!($host==='cdn.shotstack.io'||preg_match('/^shotstack-[a-z0-9-]+\.s3[.a-z0-9-]*\.amazonaws\.com$/D',$host)))throw new RuntimeException('Untrusted video result');$payload['videoUrl']=$render['url'];$payload['videoVerifiedAt']=time();}
  elseif(($render['status']??'')==='failed')throw new RuntimeException('video_render_failed');return $payload;
 }
 if(!nodenoStudioReserve($db,$settings,'video','video_'.$post['id'],time()))throw new NodenoControlHttpError(422,'social_budget_or_video_connection_required');
 $r=nodenoStudioSend($db,$root,'POST','/render',nodenoStudioVideoRequest($p,$payload,$post['platform'],$music),$transport,'shotstack');if($r['code']!==201||empty($r['data']['response']['id']))throw new RuntimeException('video_render_confirmation_required');$payload['renderId']=(string)$r['data']['response']['id'];return $payload;
}

function nodenoStudioServeAsset(string $hash,string $extension,string $root,bool $authorised=false):bool {
 if(!preg_match('/^[a-f0-9]{64}$/D',$hash)||!in_array($extension,['png','mp3'],true))return false;$db=nodenoControlDatabase($root);nodenoStudioSchema($db);$q=$db->prepare('SELECT * FROM social_assets WHERE hash=? AND extension=?');$q->execute([$hash,$extension]);$row=$q->fetch();if(!$row||(!$authorised&&!$row['public']))return false;$file=nodenoStudioRoot($root).'/'.$hash.'.'.$extension;
 if(!is_file($file)||is_link($file)||filesize($file)!==(int)$row['bytes']||!hash_equals($hash,hash_file('sha256',$file)))return false;
 header('Content-Type: '.$row['mime']);header('Content-Length: '.$row['bytes']);header('X-Content-Type-Options: nosniff');header('X-Robots-Tag: noindex, nofollow');header('Cache-Control: '.($authorised?'private, no-store':'public, max-age=86400, immutable'));if(($_SERVER['REQUEST_METHOD']??'GET')!=='HEAD')readfile($file);return true;
}
