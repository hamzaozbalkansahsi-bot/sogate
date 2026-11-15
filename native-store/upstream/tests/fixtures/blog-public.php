<?php
declare(strict_types=1);
require dirname(__DIR__,2).'/hosting/blog.php';
$a=['id'=>'a','slug'=>'olcu-plani','category'=>'planning','title'=>'Ölçü <script>alert(1)</script> planı','description'=>'Odayı ölçmek için özgün kontrol rehberi.','keywords'=>['oda ölçüsü'],'intro'=>'Önce duvarları ölçün.','sections'=>[['heading'=>'Deneme','paragraphs'=>['Gerçek örnek.']]],'checklist'=>['Geçişi deneyin.'],'tool'=>'space','related'=>[],'sources'=>[],'image'=>['url'=>'/assets/blog/a.svg','alt'=>'Ölçü çizimi','width'=>1200,'height'=>800,'kind'=>'original-diagram'],'publishedAt'=>'2026-11-12T09:31:00+03:00'];
$bank=['articles'=>[$a,array_replace($a,['id'=>'b','slug'=>'future-draft'])]];
$action=$argv[1]??'';
if($action==='article')$value=['html'=>nodenoBlogPageDocument('tr',$a,[$a],$bank,[])];
elseif($action==='sitemap')$value=['xml'=>nodenoBlogSitemapDocument([$a],$bank)];
elseif($action==='search')$value=['html'=>nodenoBlogPageDocument('tr',null,[$a],$bank,['q'=>'raf & dolap'])];
elseif($action==='arabic')$value=['html'=>nodenoBlogPageDocument('ar',null,[],$bank,['tool'=>'paint'])];
elseif($action==='tool-alternates')$value=['html'=>nodenoBlogPageDocument('tr',null,[],$bank,['tool'=>'paint'])];
elseif($action==='category-alternates')$value=['html'=>nodenoBlogPageDocument('tr',null,[],$bank,['category'=>'planning'],['page'=>2,'pages'=>3])];
elseif($action==='article-tool')$value=['html'=>nodenoBlogPageDocument('tr',$a,[$a],$bank,['tool'=>'paint'])];
else throw new RuntimeException('unknown_action');
echo json_encode($value,JSON_THROW_ON_ERROR);
