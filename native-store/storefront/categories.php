<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/categories.php
 * Açıklama   : Kategori gezintisinin ilk HTML yanıtını istemciyle aynı kart düzeninde üretir.
 */
declare(strict_types=1);
function sexogateCategoryLink(string $page,string $locale,array $params=[]):string{
 return '/?'.http_build_query(['page'=>$page,'lang'=>$locale]+array_filter($params,static fn($v)=>$v!==''),'','&',PHP_QUERY_RFC3986);
}
function sexogateCategoryBody(array $catalog,string $locale,array $values):string{
 require_once __DIR__.'/sexogate-storefront-home.php';
 $e='nodenoSeoEscape';$copy=json_decode((string)file_get_contents(__DIR__.'/sexogate-category-copy.json'),true,32,JSON_THROW_ON_ERROR)[$locale];
 $ui=json_decode((string)file_get_contents(__DIR__.'/sexogate-storefront-ui-copy.json'),true,32,JSON_THROW_ON_ERROR)[$locale];
 $categories=$catalog['categories']??[];$members=[];foreach($categories as $v)$members[$v['id']]=nodenoSeoDistinct(nodenoSeoProducts($catalog,$v['id']));
 $roots=array_values(array_filter($categories,static fn($v)=>empty($v['parentId'])&&!empty($members[$v['id']])));
 $children=static fn(string $id):array=>array_values(array_filter($categories,static fn($v)=>($v['parentId']??'')===$id&&!empty($members[$v['id']])));
 $name=static fn(array $v):string=>$e(nodenoSeoLocal($v['name'],$locale));$link=static fn(string $page,array $params=[]):string=>$e(sexogateCategoryLink($page,$locale,$params));
 $arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>';
 $grid='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><path d="m16 15 4 3-4 3"/></svg>';
 $photo=static fn(array $v):string=>!empty($members[$v['id']])?nodenoSeoPhoto($members[$v['id']][0],$catalog,$locale,false):$grid;
 $active=null;foreach($roots as $root){if($root['id']===($values['category']??''))$active=$root;foreach($children($root['id'])as $child)if($child['id']===($values['category']??''))$active=$root;}
 $search='<div class="sg-category-search"><a href="'.$link('home').'" data-nav aria-label="'.$e($copy['back']).'">'.$arrow.'</a><form data-sg-category-search role="search" method="get"><input type="hidden" name="page" value="catalog"><input type="hidden" name="lang" value="'.$e($locale).'"><label class="sr-only" for="sg-category-query">'.$e($copy['search']).'</label><input id="sg-category-query" name="q" type="search" placeholder="'.$e($copy['search']).'"><button type="submit" aria-label="'.$e($copy['search']).'"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg></button></form></div>';
 if($active===null){
  $cards='';foreach($roots as $v)$cards.='<a class="category-tile" href="'.$link('categories',['category'=>$v['id']]).'" data-nav data-category-tile="'.$e($v['id']).'"><span class="category-tile-caption"><strong>'.$name($v).'</strong><span>'.count($members[$v['id']]).' '.$e($copy['products']).'</span></span><span class="category-tile-photo">'.$photo($v).'</span></a>';
  return '<div class="wrap category-browser sg-categories sg-category-landing">'.$search.'<header class="category-browser-heading"><h1 tabindex="-1">'.$e($copy['allCategories']).'</h1><a href="'.$link('catalog').'" data-nav>'.$e($ui['allProducts']).$arrow.'</a></header><a class="sg-category-discover" href="'.$link('catalog').'" data-nav><span><strong>'.$e($copy['discover']).'</strong><span>'.$e($copy['discoverBody']).'</span></span>'.$grid.$arrow.'</a><div class="category-tile-grid sg-category-cards">'.$cards.'</div></div>';
 }
 $groups=$children($active['id']);$selected=null;foreach($groups as $v)if($v['id']===($values['section']??$values['category']??''))$selected=$v;$current=$selected??$active;$tiles=$children($current['id']);
 $tabs='<a href="'.$link('categories').'" data-nav>'.$grid.'<span>'.$e($copy['allCategories']).'</span></a>';foreach($roots as $v)$tabs.='<a href="'.$link('categories',['category'=>$v['id']]).'" data-nav'.($v['id']===$active['id']?' aria-current="page"':'').'>'.$name($v).'</a>';
 $rail='<a href="'.$link('categories',['category'=>$active['id']]).'" data-nav'.($selected===null?' aria-current="page"':'').'>'.$e($ui['allProducts']).'</a>';foreach($groups as $v)$rail.='<a href="'.$link('categories',['category'=>$active['id'],'section'=>$v['id']]).'" data-nav'.($v['id']===($selected['id']??'')?' aria-current="page"':'').'>'.$name($v).'</a>';
 $allLink=$link('catalog',['category'=>$current['id']]);$tileHtml='<a class="sg-subcategory-tile" href="'.$allLink.'" data-nav><span class="sg-category-all">'.$grid.'</span><strong>'.$e($copy['viewAll']).'</strong></a>';
 foreach($tiles as $v)$tileHtml.='<a class="sg-subcategory-tile" href="'.$link($children($v['id'])?'categories':'catalog',['category'=>$v['id']]).'" data-nav data-category-tile="'.$e($v['id']).'"><span>'.$photo($v).'</span><strong>'.$name($v).'</strong></a>';
 $picks='';if($selected!==null||!$tiles){foreach(array_slice($members[$current['id']],0,8)as $p)$picks.=sexogateHomeCard($p,$catalog,$locale,$ui);$picks='<div class="section-heading"><h2>'.$e($copy['categorySelection']).'</h2></div><div class="product-grid sg-category-picks">'.$picks.'</div>';}
 return '<div class="wrap category-browser sg-categories sg-category-explorer">'.$search.'<nav class="sg-category-tabs" aria-label="'.$e($copy['allCategories']).'">'.$tabs.'</nav><div class="sg-category-columns"><nav class="sg-category-rail" aria-label="'.$name($active).'">'.$rail.'</nav><section class="sg-category-content"><div class="sg-category-section-heading"><h1 tabindex="-1">'.$name($current).'</h1><a class="category-view-all" href="'.$allLink.'" data-nav>'.$e($copy['viewAll']).$arrow.'</a></div><div class="sg-subcategory-grid">'.$tileHtml.'</div>'.$picks.'</section></div></div>';
}
