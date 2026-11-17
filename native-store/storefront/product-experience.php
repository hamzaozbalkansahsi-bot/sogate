<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-experience.php
 * Açıklama   : Ürün ayrıntılarını ve gerçek koleksiyon önerilerini ilk HTML'de sunar.
 */
declare(strict_types=1);
function sexogatePxCopy(string $locale):array{
 static $copy=null;if($copy===null){$file=__DIR__.'/sexogate-product-experience-copy.json';if(!is_file($file))$file=__DIR__.'/product-experience-copy.json';$copy=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);}return $copy[$locale]??$copy['en'];
}
function sexogatePxLocal(mixed $value,string $locale='tr'):string{
 if(is_string($value))return trim($value);if(!is_array($value))return '';$text=$value[$locale]??$value['en']??$value['tr']??'';return is_string($text)?trim($text):'';
}
function sexogatePxClean(string $value):string{return trim(preg_replace('/\s+/u',' ',$value)??'');}
function sexogatePxKey(array $p):string{return (string)(!empty($p['modelId'])?$p['modelId']:$p['id']);}
function sexogatePxVisible(array $products):array{
 $seen=[];$result=[];foreach($products as $p){if(!is_array($p)||empty($p['id'])||($p['published']??true)===false||!empty($p['hidden'])||empty($p['images']))continue;$key=sexogatePxKey($p);if(isset($seen[$key]))continue;$seen[$key]=true;$result[]=$p;}return $result;
}
function sexogatePxMembers(array $products,array $categories,string $id):array{
 $family=[$id=>true];$changed=true;while($changed){$changed=false;foreach($categories as $row)if(isset($family[$row['parentId']??''])&&!isset($family[$row['id']])){$family[$row['id']]=true;$changed=true;}}
 return array_values(array_filter($products,static fn($p)=>array_intersect_key(array_flip($p['categoryIds']??[]),$family)!==[]));
}
function sexogatePxFacts(array $product,string $locale,array $labels):array{
 $result=[];$seen=[];$keys=[];$add=static function(string $id,string $label,string $value)use(&$result,&$seen,&$keys):void{
  $label=sexogatePxClean($label);$value=sexogatePxClean($value);$identity=strtolower(strtr($label,['I'=>'ı','İ'=>'i','Ş'=>'ş','Ğ'=>'ğ','Ü'=>'ü','Ö'=>'ö','Ç'=>'ç']));if($label===''||$value===''||preg_match_all('/./us',$value)>600||isset($seen[$identity])||isset($keys[$id]))return;$seen[$identity]=true;$keys[$id]=true;$result[]=['id'=>$id,'label'=>$label,'value'=>$value];
 };
 foreach($product['storefrontStory'][$locale]['fields']??[]as $row)if(($row['key']??'')!=='productCode')$add($row['key'],$row['title'],$row['value']);
 foreach(['materials','dimensions','diameter','weight','volume','sizes','colors','battery','ingredients','package','origin','manufacturer']as $key){$value=sexogatePxLocal($product['storefrontFacts'][$key]??null,$locale);if($value!=='')$add($key,$labels[$key]??$key,$value);}
 foreach($product['specs']??[]as $index=>$row)$add('spec-'.$index,sexogatePxLocal($row['label']??null,$locale),sexogatePxLocal($row['value']??null,$locale));return $result;
}
function sexogatePxStory(array $product,string $locale):array{
 $story=$product['storefrontStory'][$locale]??$product['storefrontStory']['en']??$product['storefrontStory']['tr']??[];$body=array_values(array_filter(array_map('trim',preg_split('/\n\s*\n/u',sexogatePxLocal($product['description']??null,$locale))?:[]),static fn($v)=>$v!==''));
 $intro=sexogatePxLocal($story['intro']??null,$locale);if($intro==='')$intro=array_shift($body)??sexogatePxLocal($product['name']??null,$locale);$lines=static fn($items)=>is_array($items)?array_values(array_filter(array_map(static fn($v)=>sexogatePxLocal($v),$items),static fn($v)=>$v!=='')):[];
 $paragraphs=$lines($story['paragraphs']??[]);if(!$paragraphs)$paragraphs=$body;$seen=[sexogatePxClean($intro)=>true];$rest=[];foreach($paragraphs as $v){$key=sexogatePxClean($v);if($key===''||isset($seen[$key]))continue;$seen[$key]=true;$rest[]=$v;}
 return ['intro'=>$intro,'paragraphs'=>$rest,'bullets'=>$lines($story['bullets']??[]),'packageContents'=>$lines($story['packageContents']??[]),'care'=>sexogatePxLocal($story['care']??null,$locale),'safety'=>sexogatePxLocal($story['safety']??null,$locale)];
}
function sexogatePxDiscovery(array $product,array $catalog,array $config=[]):array{
 $products=sexogatePxVisible($catalog['products']??[]);$categories=$catalog['categories']??[];$others=array_values(array_filter($products,static fn($p)=>sexogatePxKey($p)!==sexogatePxKey($product)));$byId=array_column($products,null,'id');$current=array_fill_keys($product['categoryIds']??[],true);$map=array_column($categories,null,'id');$roots=[];
 foreach($current as $id=>$_){$at=$id;$seen=[];while(!empty($map[$at]['parentId'])&&!isset($seen[$at])){$seen[$at]=true;$at=$map[$at]['parentId'];}$roots[$at]=true;}
 $similar=array_values(array_filter($others,static function($p)use($current,$map){foreach($p['categoryIds']??[]as $id)if(isset($current[$id])&&!empty($map[$id]['parentId']))return true;return false;}));$used=[];foreach($similar as $p)$used[sexogatePxKey($p)]=true;
 $complementary=array_values(array_filter($others,static function($p)use($used,$roots,$categories){if(isset($used[sexogatePxKey($p)]))return false;foreach($roots as $id=>$_)if(sexogatePxMembers([$p],$categories,$id))return true;return false;}));$selection=array_slice(sexogatePxVisible([...$similar,...$complementary,...$others]),0,12);
 $popularity=$config['productPopularity']??[];$counts=($popularity['source']??'')==='fulfilled-order-lines'&&is_string($popularity['asOf']??null)&&strtotime($popularity['asOf'])!==false&&is_array($popularity['counts']??null)?$popularity['counts']:null;$popular=[];
 if($counts!==null){$popular=array_values(array_filter($others,static fn($p)=>is_int($counts[$p['id']]??null)&&$counts[$p['id']]>0));usort($popular,static fn($a,$b)=>$counts[$b['id']]<=>$counts[$a['id']]?:strcmp($a['id'],$b['id']));$popular=array_slice($popular,0,12);}
 $collections=[];$targets=[];foreach($config['collections']??[]as $row){if(($row['data']['enabled']??null)!==true)continue;$ids=$row['data']['productIds']??[];if(is_string($ids))$ids=array_map('trim',explode(',',$ids));$members=sexogatePxVisible(array_values(array_filter(array_map(static fn($id)=>$byId[$id]??null,$ids))));if(count($members)<3)continue;$title=$row['data']['title']??[];if(!$title)foreach($row['data']as $key=>$value)if(str_starts_with($key,'title_'))$title[substr($key,6)]=$value;if(sexogatePxLocal($title)==='')continue;$collections[]=['id'=>(string)$row['id'],'title'=>$title,'products'=>array_slice($members,0,3),'count'=>count($members),'params'=>['collection'=>(string)$row['id']]];$targets['collection:'.$row['id']]=true;if(count($collections)===6)break;}
 $ordered=[...array_values(array_filter($categories,static fn($c)=>isset($current[$c['id']]))),...array_values(array_filter($categories,static fn($c)=>isset($current[$c['parentId']??'']))),...array_values(array_filter($categories,static fn($c)=>isset($roots[$c['id']]))),...$categories];
 foreach($ordered as $category){if(count($collections)===6)break;if(isset($targets['category:'.$category['id']]))continue;$members=sexogatePxMembers($products,$categories,$category['id']);if(count($members)<3)continue;$targets['category:'.$category['id']]=true;$collections[]=['id'=>$category['id'],'title'=>$category['name'],'products'=>array_slice($members,0,3),'count'=>count($members),'params'=>['category'=>$category['id']]];}
 $links=[];$used=[];foreach($ordered as $c){if(count($links)===9)break;if(isset($used[$c['id']])||!sexogatePxMembers($products,$categories,$c['id']))continue;$used[$c['id']]=true;$links[]=['title'=>$c['name'],'params'=>['category'=>$c['id']]];}$brand=sexogatePxClean((string)(($product['brand']??'')?:($product['productBrand']??'')));if($brand!==''&&count(array_filter($products,static fn($p)=>sexogatePxClean((string)(($p['brand']??'')?:($p['productBrand']??'')))===$brand))>1)$links[]=['title'=>$brand,'params'=>['brand'=>$brand]];
 return ['similar'=>array_slice($similar,0,12),'complementary'=>array_slice($complementary,0,12),'selection'=>$selection,'popular'=>$popular,'hasPopularity'=>count($popular)>0,'collections'=>$collections,'links'=>$links,'recent'=>[]];
}
function sexogatePxParagraphs(string $text):string{
 $html='';foreach(preg_split('/\n\s*\n/u',$text)?:[]as $value)if(trim($value)!=='')$html.='<p>'.nodenoSeoEscape(trim($value)).'</p>';return $html;
}
function sexogatePxArrow():string{return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>';}
function sexogatePxChevron():string{return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6-6 6"/></svg>';}
function sexogatePxLink(string $kind,string $locale,array $values=[]):string{
 $link=nodenoSeoLink($kind,$locale,$values);foreach(['collection','brand','size','color','q']as $key)if(isset($values[$key])&&is_string($values[$key])&&$values[$key]!=='')$link.=(str_contains($link,'?')?'&':'?').rawurlencode($key).'='.rawurlencode($values[$key]);return $link;
}
function sexogatePxHighlights(array $p,string $locale,array $c,array $facts):string{
 if(!$facts)return '';$e='nodenoSeoEscape';$html='<section class="product-spec-overview sg-product-highlights" aria-labelledby="product-highlights-title"><div class="spec-overview-heading"><h2 id="product-highlights-title">'.$e($c['highlights']).'</h2><a class="specs-all-link" href="#product-specs" data-specs-link data-sg-open-features>'.$e($c['allFeatures']).sexogatePxArrow().'</a></div><dl class="sg-highlight-grid">';
 foreach(array_slice($facts,0,8)as $row)$html.='<div data-spec-fact="'.$e($row['id']).'"><dt>'.$e($row['label']).'</dt><dd>'.$e($row['value']).'</dd></div>';return $html.'</dl></section>';
}
function sexogatePxStoryHtml(array $p,array $catalog,string $locale,array $c,array $story):string{
 $e='nodenoSeoEscape';$body='';foreach($story['paragraphs']as $value)$body.=sexogatePxParagraphs($value);if($story['bullets']){$body.='<ul class="sg-story-bullets">';foreach($story['bullets']as $value)$body.='<li>'.$e($value).'</li>';$body.='</ul>';}
 if($story['packageContents']){$body.='<section class="sg-story-package"><h3>'.$e($c['packageContents']).'</h3><ul>';foreach($story['packageContents']as $value)$body.='<li>'.$e($value).'</li>';$body.='</ul></section>';}
 return '<div class="sg-product-story sg-product-editorial"><figure>'.nodenoSeoPhoto($p,$catalog,$locale).'</figure><div><p class="sg-product-intro">'.$e($story['intro']).'</p>'.($body!==''?'<details class="sg-story-details" data-sg-story-details><summary class="sg-more-link"><span class="sg-when-closed">'.$e($c['more']).'</span><span class="sg-when-open">'.$e($c['less']).'</span>'.sexogatePxChevron().'</summary><div class="sg-story-expanded">'.$body.'</div></details>':'').'</div></div>';
}
function sexogatePxFeatures(array $p,array $c,array $facts):string{
 if(!empty($p['code']))$facts[]=['id'=>'code','label'=>$c['code'],'value'=>$p['code']];if(!$facts)return '';$e='nodenoSeoEscape';$html='<details class="sg-all-features sg-product-attributes" id="sg-all-features"><summary><span class="sg-when-closed">'.$e($c['allFeatures']).'</span><span class="sg-when-open">'.$e($c['hideFeatures']).'</span>'.sexogatePxChevron().'</summary><div class="sg-features-body"><dl class="sg-feature-list sg-attribute-table">';foreach($facts as $row)$html.='<div><dt>'.$e($row['label']).'</dt><dd>'.$e($row['value']).'</dd></div>';return $html.'</dl></div></details>';
}
function sexogatePxReturns(array $config,string $locale,array $c):string{
 $policy=$config['productExperience']['returns'][$locale]??[];$file=__DIR__.'/sexogate-product-return-policy.json';if(!$policy&&is_file($file)){$all=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);$policy=$all[$locale]??$all['en']??$all['tr']??[];}$e='nodenoSeoEscape';$html='<section class="detail-section sg-product-returns" id="product-faq" tabindex="-1" aria-labelledby="sg-product-returns-title"><h2 id="sg-product-returns-title">'.$e($c['returns']).'</h2><details class="sg-inline-policy" data-sg-returns-details><summary>'.$e($policy['title']??$c['returns']).sexogatePxChevron().'</summary><div>';
 foreach($policy['paragraphs']??[]as $v)$html.=sexogatePxParagraphs($v);if(!empty($policy['items'])){$html.='<ul>';foreach($policy['items']as $v)$html.='<li>'.(is_string($v)?$e($v):'<strong>'.$e($v['title']??'').'</strong><span>'.$e($v['body']??'').'</span>').'</li>';$html.='</ul>';}
 return $html.'<p>'.$e($c['returnGuidance']).'</p><a class="sg-inline-return-action" href="'.$e(nodenoSeoLink('return-center',$locale)).'" data-nav>'.$e($c['startReturn']).sexogatePxArrow().'</a></div></details></section>';
}
function sexogatePxCollections(array $model,array $catalog,string $locale,array $c):string{
 if(!$model['collections'])return '';$e='nodenoSeoEscape';$html='<section class="product-shelf sg-product-collections" aria-labelledby="sg-product-collections-title"><div class="section-heading"><h2 id="sg-product-collections-title">'.$e($c['collections']).'</h2></div><div class="product-row sg-collection-rail" role="region" tabindex="0" aria-label="'.$e($c['collections']).'">';
 foreach($model['collections']as $group){$html.='<a class="sg-product-collection" href="'.$e(sexogatePxLink('catalog',$locale,$group['params'])).'" data-nav data-sg-product-collection="'.$e($group['id']).'"><h3>'.$e(sexogatePxLocal($group['title'],$locale)).'</h3><span class="sg-collection-mosaic">';foreach($group['products']as $p)$html.='<span>'.nodenoSeoPhoto($p,$catalog,$locale).'</span>';$html.='</span><span class="sg-collection-caption"><span>'.$group['count'].' '.$e($c['productCount']).'</span><strong>'.$e($c['collectionAction']).sexogatePxArrow().'</strong></span></a>';}
 return $html.'</div></section>';
}
function sexogatePxShelf(string $key,string $title,array $products,array $catalog,string $locale,array $ui):string{
 if(!$products)return '';$e='nodenoSeoEscape';$html='<section class="product-shelf sg-product-shelf" id="product-shelf-'.$e($key).'"><div class="section-heading"><h2>'.$e($title).'</h2></div><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="'.$e($title).'">';foreach(array_slice($products,0,12)as $p)$html.=sexogateHomeCard($p,$catalog,$locale,$ui);return $html.'</div></section>';
}
function sexogateProductBody(array $product,array $catalog,string $locale,array $variants,array $config=[]):string{
 require_once __DIR__.'/sexogate-storefront-home.php';$c=sexogatePxCopy($locale);$e='nodenoSeoEscape';$file=__DIR__.'/sexogate-storefront-copy.json';$labels=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR)[$locale];$ui=json_decode((string)file_get_contents(__DIR__.'/sexogate-storefront-ui-copy.json'),true,64,JSON_THROW_ON_ERROR)[$locale];$facts=sexogatePxFacts($product,$locale,$labels);$story=sexogatePxStory($product,$locale);$model=sexogatePxDiscovery($product,$catalog,$config);
 $brand=(string)($product['brand']??$product['productBrand']??'');$html='<div class="wrap product-page">'.nodenoSeoCrumbHtml(nodenoSeoBreadcrumb($catalog,$product,$locale)).'<div class="product-detail-layout"><section class="product-gallery"><div class="gallery-main">'.nodenoSeoPhoto($product,$catalog,$locale,false).'</div></section><div class="product-purchase"><header class="product-title-block"><div class="product-heading">'.($brand!==''?'<span class="product-brand">'.$e($brand).'</span>':'').'<h1 id="product-title" tabindex="-1">'.$e(nodenoSeoName($product,$locale)).'</h1></div><div class="product-identifiers"><bdi class="product-code" dir="ltr">'.$e($c['code']).': '.$e($product['code']).'</bdi></div></header><p class="detail-price">'.nodenoSeoPrice($product,$locale).'</p>'.sexogatePxHighlights($product,$locale,$c,$facts).'</div></div>';
 $nav=[['product-information',$c['information']],['product-specs',$c['features']]];if($story['care']!==''||$story['safety']!=='')$nav[]=['product-questions',$c['care']];$nav[]=['product-faq',$c['returns']];$html.='<nav class="product-section-nav sg-product-section-nav" aria-label="'.$e($c['information']).'">';foreach($nav as [$id,$text])$html.='<a href="#'.$id.'" data-specs-link data-sg-product-section>'.$e($text).'</a>';$html.='</nav>';
 $html.='<section class="detail-section" id="product-information"><h2>'.$e($c['information']).'</h2>'.sexogatePxStoryHtml($product,$catalog,$locale,$c,$story).'</section><section class="detail-section product-specifications" id="product-specs" tabindex="-1" aria-labelledby="product-specifications-title"><h2 id="product-specifications-title">'.$e($c['features']).'</h2>'.sexogatePxFeatures($product,$c,$facts).'</section>';
 if($story['care']!==''||$story['safety']!==''){$html.='<section class="detail-section sg-product-care" id="product-questions" tabindex="-1"><h2>'.$e($c['care']).'</h2><div class="sg-care-grid">';foreach(['care','safety']as $key)if($story[$key]!=='')$html.='<article><h3>'.$e($c[$key]).'</h3>'.sexogatePxParagraphs($story[$key]).'</article>';$html.='</div></section>';}
 $html.=sexogatePxReturns($config,$locale,$c).'<div class="sg-product-feedback"><button type="button" data-sg-feedback="'.$e($product['id']).'"><span>'.$e($c['feedback']).'</span>'.sexogatePxArrow().'</button></div>'.sexogatePxCollections($model,$catalog,$locale,$c);
 $html.=sexogatePxShelf('productSimilar',$c['similar'],$model['similar'],$catalog,$locale,$ui).sexogatePxShelf('productComplementary',$c['recommendations'],$model['complementary']?:$model['selection'],$catalog,$locale,$ui).sexogatePxShelf('selection',$model['hasPopularity']?$c['popular']:$c['selection'],$model['hasPopularity']?$model['popular']:$model['selection'],$catalog,$locale,$ui);
 if($model['links']){$html.='<section class="detail-section sg-related-discovery" aria-labelledby="sg-related-discovery-title"><h2 id="sg-related-discovery-title">'.$e($c['related']).'</h2><nav class="sg-related-chips" aria-label="'.$e($c['related']).'">';foreach($model['links']as $link)$html.='<a href="'.$e(sexogatePxLink('catalog',$locale,$link['params'])).'" data-nav>'.$e(sexogatePxLocal($link['title'],$locale)).'</a>';$html.='</nav></section>';}
 return $html.'</div>';
}
