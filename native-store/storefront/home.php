<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/home.php
 * Açıklama   : Ana sayfanın ilk HTML'sini istemciyle aynı küçük resimli kartlarla üretir.
 */
declare(strict_types=1);
function sexogateHomeIcon(string $name):string{
 $paths=['arrow'=>'M4 12h15m-6-6 6 6-6 6','heart'=>'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z','cart'=>'M2 3h3l3 13h11l3-10H6m3 15h.01M18 21h.01','compare'=>'M5 3v18M12 3v18M19 3v18M2 8h6m1 8h6m1-6h6','bookmark'=>'M6 3h12v18l-6-4-6 4Z'];
 return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="'.$paths[$name].'"/></svg>';
}
function sexogateHomeCard(array $product,array $catalog,string $locale,array $labels):string{
 $escape='nodenoSeoEscape';$id=$escape($product['id']);$name=$escape(nodenoSeoName($product,$locale));$link=$escape(nodenoSeoLink('product',$locale,['product'=>$product['id']]));
 $card='<article class="product-card"><div class="product-card-stage"><a class="product-stage" href="'.$link.'" data-product="'.$id.'">'.nodenoSeoPhoto($product,$catalog,$locale).'</a><button class="product-save" type="button" data-save="'.$id.'" aria-label="'.$escape($labels['favorites']).': '.$name.'" aria-pressed="false">'.sexogateHomeIcon('heart').'</button></div>';
 $card.='<div class="product-info"><h3><a href="'.$link.'" data-product="'.$id.'">'.$name.'</a></h3><p class="card-color">'.$escape(nodenoSeoLocal($product['variantColor']??[],$locale)).'</p><p class="pricing-note card-price-compact"><span class="card-price-main"><bdi class="product-price" data-price="'.$id.'" dir="auto">'.nodenoSeoPrice($product,$locale).'</bdi></span></p>';
 $card.='<button type="button" class="button card-add" data-add="'.$id.'">'.sexogateHomeIcon('cart').'<span>'.$escape($labels['add']).'</span></button><div class="card-tools"><button type="button" class="card-compare" data-compare="'.$id.'" aria-pressed="false">'.sexogateHomeIcon('compare').'<span>'.$escape($labels['compare']).'</span></button><button type="button" class="icon-button" data-collect="'.$id.'" aria-label="'.$escape($labels['addCollection']).': '.$name.'">'.sexogateHomeIcon('bookmark').'</button></div></div></article>';
 return $card;
}
function sexogateStorefrontHome(array $catalog,array $config,string $locale):string{
 $escape='nodenoSeoEscape';$ui=json_decode((string)file_get_contents(__DIR__.'/sexogate-storefront-ui-copy.json'),true,32,JSON_THROW_ON_ERROR);$labels=$ui[$locale];$copy=sexogateStorefrontCopy()[$locale];$brand=json_decode((string)file_get_contents(__DIR__.'/sexogate-store-copy.json'),true,32,JSON_THROW_ON_ERROR)[$locale];
 $products=nodenoSeoDistinct(nodenoSeoProducts($catalog));$roots=[];$shortcuts='';$arrow=sexogateHomeIcon('arrow');$all=$escape(nodenoSeoLink('catalog',$locale));
 foreach($catalog['categories']??[]as $category){if(!empty($category['parentId']))continue;$members=nodenoSeoProducts($catalog,$category['id']);if(!$members)continue;$photo=$members[0];$category['photo']=$photo;$roots[]=$category;$name=$escape(nodenoSeoLocal($category['name'],$locale));$href=$escape(nodenoSeoLink('catalog',$locale,['category'=>$category['id']]));$shortcuts.='<a href="'.$href.'" data-nav><span>'.nodenoSeoPhoto($photo,$catalog,$locale,false).'</span><strong>'.$name.'</strong></a>';}
 $featured=null;if(!empty($config['appearance']['enabled']))foreach($products as $product)if($product['id']===($config['appearance']['heroProductId']??'')){$featured=$product;break;}
 $cards='';if($featured)$cards.='<a class="sg-campaign-card" href="'.$escape(nodenoSeoLink('product',$locale,['product'=>$featured['id']])).'" data-product="'.$escape($featured['id']).'"><span class="sg-campaign-image">'.nodenoSeoPhoto($featured,$catalog,$locale,false).'</span><span class="sg-campaign-caption"><strong>'.$escape(nodenoSeoName($featured,$locale)).'</strong>'.$arrow.'</span></a>';
 foreach(array_slice($roots,0,$featured?3:4)as $category){$href=$escape(nodenoSeoLink('catalog',$locale,['category'=>$category['id']]));$cards.='<a class="sg-campaign-card" href="'.$href.'" data-nav><span class="sg-campaign-image">'.nodenoSeoPhoto($category['photo'],$catalog,$locale,false).'</span><span class="sg-campaign-caption"><strong>'.$escape(nodenoSeoLocal($category['name'],$locale)).'</strong>'.$arrow.'</span></a>';}
 $title=!empty($config['appearance']['enabled'])&&trim((string)($config['appearance']['heroTitle_'.$locale]??''))!==''?$config['appearance']['heroTitle_'.$locale]:$brand['slogan'];
 $body='<div class="wrap home-page sg-home sg-market-home"><nav class="sg-home-shortcuts" aria-label="'.$escape(nodenoSeoCopy($locale)['categories']).'">'.$shortcuts.'</nav><div class="sg-home-heading"><h1 tabindex="-1">'.$escape($title).'</h1><a class="text-link" href="'.$all.'" data-nav>'.$escape($labels['allProducts']).$arrow.'</a></div><section class="sg-campaign-grid" aria-label="'.$escape($copy['collection']).'">'.$cards.'</section>';
 if($products){$items='';foreach(array_slice($products,0,12)as $product)$items.=sexogateHomeCard($product,$catalog,$locale,$labels);$body.='<section class="product-shelf sg-product-shelf"><div class="section-heading"><h2>'.$escape($copy['selection']).'</h2><a class="text-link" href="'.$all.'" data-nav>'.$escape($labels['allProducts']).'</a></div><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="'.$escape($copy['selection']).'">'.$items.'</div></section>';}
 return $body.'</div>';
}
