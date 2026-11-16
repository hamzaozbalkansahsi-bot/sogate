<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/home-model.php
 * Açıklama   : İlk HTML için yayımlanmış ürünlerden dengeli ana sayfa rafları seçer.
 */
declare(strict_types=1);
function sexogateHomeUnique(array $products):array{$seen=[];$result=[];foreach($products as $p){$id=(string)($p['modelId']??$p['id']);if(($p['published']??true)===false||!empty($p['hidden'])||empty($p['images'])||isset($seen[$id]))continue;$seen[$id]=true;$result[]=$p;}return $result;}
function sexogateHomeMembers(array $products,array $categories,string $id):array{$family=[$id=>true];$changed=true;while($changed){$changed=false;foreach($categories as $c)if(isset($family[$c['parentId']??''])&&!isset($family[$c['id']])){$family[$c['id']]=true;$changed=true;}}return array_values(array_filter($products,static fn($p)=>array_intersect_key(array_flip($p['categoryIds']??[]),$family)!==[]));}
function sexogateHomeBalanced(array $products,array $categories,array $roots,int $limit=8,array $excluded=[]):array{
 $queues=array_map(static fn($c)=>sexogateHomeMembers($products,$categories,$c['id']),$roots);$seen=[];foreach($excluded as $p)$seen[(string)($p['modelId']??$p['id'])]=true;$result=[];$position=0;
 while(count($result)<$limit&&array_filter($queues,static fn($q)=>$position<count($q))){foreach($queues as $queue){$p=$queue[$position]??null;if($p!==null&&!isset($seen[(string)($p['modelId']??$p['id'])])){$seen[(string)($p['modelId']??$p['id'])]=true;$result[]=$p;if(count($result)===$limit)break;}}$position++;}
 foreach($products as $p)if(count($result)<$limit&&!isset($seen[(string)($p['modelId']??$p['id'])])){$seen[(string)($p['modelId']??$p['id'])]=true;$result[]=$p;}return $result;
}
function sexogateHomeModel(array $catalog,array $options=[]):array{
 $products=sexogateHomeUnique($catalog['products']??[]);$categories=$catalog['categories']??[];$members=static fn($id)=>sexogateHomeMembers($products,$categories,$id);$roots=array_values(array_filter($categories,static fn($c)=>empty($c['parentId'])&&$members($c['id'])!==[]));$rootIds=array_column($roots,'id');
 $shortcuts=array_slice([...$roots,...array_values(array_filter($categories,static fn($c)=>in_array($c['parentId']??'',$rootIds,true)&&$members($c['id'])!==[]))],0,10);$selection=sexogateHomeBalanced($products,$categories,$roots);$selected=$lingerie=null;
 foreach($roots as $c){if($c['id']===($options['category']??''))$selected=$c;if($c['id']==='sg_lingerie')$lingerie=$c;}
 $pool=$lingerie?$members($lingerie['id']):[];$selectedIds=array_map(static fn($p)=>(string)($p['modelId']??$p['id']),$selection);$unused=array_values(array_filter($pool,static fn($p)=>!in_array((string)($p['modelId']??$p['id']),$selectedIds,true)));$lingerieProducts=array_slice(count($unused)>=8?$unused:$pool,0,8);
 $featured=null;foreach($products as $p)if($p['id']===($options['featuredId']??''))$featured=$p;$campaigns=$featured?[['product'=>$featured,'category'=>null]]:[];foreach(array_slice($roots,0,$featured?3:4)as $c)$campaigns[]=['category'=>$c,'product'=>$members($c['id'])[0]];
 $discovery=$selected?array_slice($members($selected['id']),0,8):sexogateHomeBalanced($products,$categories,$roots,8,[...$selection,...$lingerieProducts]);
 return compact('products','roots','shortcuts','selection','lingerie','lingerieProducts','campaigns','selected','discovery');
}
