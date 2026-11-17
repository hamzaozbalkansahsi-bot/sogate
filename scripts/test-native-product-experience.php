<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-product-experience.php
 * Açıklama   : İlk HTML ürün modelinin kaynak, mahremiyet, kaçış ve bağlantı kurallarını sınar.
 */
declare(strict_types=1);
require_once __DIR__.'/../native-store/storefront/product-experience.php';
function nodenoSeoEscape(mixed $v):string{return htmlspecialchars((string)$v,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
function nodenoSeoLink(string $kind,string $locale,array $values=[]):string{$query=['lang'=>$locale,'page'=>$kind];foreach(['category','product']as $key)if(isset($values[$key]))$query[$key]=$values[$key];return '/test/?'.http_build_query($query,'','&',PHP_QUERY_RFC3986);}
function nodenoSeoPhoto(array $p,array $catalog,string $locale,bool $lazy=true):string{return '<img src="/test/media/'.nodenoSeoEscape($p['id']).'/0" alt="">';}
$categories=[['id'=>'root','name'=>['tr'=>'İç Giyim'],'parentId'=>null],['id'=>'night','name'=>['tr'=>'Gecelikler'],'parentId'=>'root'],['id'=>'costume','name'=>['tr'=>'Kostümler'],'parentId'=>'root'],['id'=>'empty','name'=>['tr'=>'Boş'],'parentId'=>null]];
$make=static fn($id,$category='night',$extra=[])=>array_replace(['id'=>$id,'code'=>'seo-'.$id,'name'=>['tr'=>'Dantel detaylı model '.$id],'brand'=>'JUBELS','images'=>['/media/'.$id.'/0'],'categoryIds'=>['root',$category]],$extra);
$product=$make('one');$products=[$product,$make('two'),$make('three'),$make('four'),$make('five','costume'),$make('six','costume'),$make('seven','costume'),$make('hidden','night',['hidden'=>true]),$make('draft','night',['published'=>false]),$make('no-photo','night',['images'=>[]]),$make('duplicate','night',['modelId'=>'two'])];$catalog=compact('products','categories');$checks=[];
$check=static function(string $name,bool $condition)use(&$checks):void{if(!$condition)throw new RuntimeException('FAILED:'.$name);$checks[]=$name;};
$check('only-public-photographed-unique',array_column(sexogatePxVisible($products),'id')===['one','two','three','four','five','six','seven']);
$before=json_encode($catalog,JSON_THROW_ON_ERROR);$model=sexogatePxDiscovery($product,$catalog);$check('catalog-unchanged',json_encode($catalog,JSON_THROW_ON_ERROR)===$before);
foreach(['similar','complementary','selection','popular']as $key)$check('current-excluded-'.$key,!in_array('one',array_column($model[$key],'id'),true));
$check('no-false-popularity',!$model['hasPopularity']&&$model['popular']===[]);
$forged=sexogatePxDiscovery($product,$catalog,['productPopularity'=>['source'=>'supplier-sold','asOf'=>'2026-11-17','counts'=>['two'=>999]]]);$check('supplier-popularity-rejected',!$forged['hasPopularity']);
$real=sexogatePxDiscovery($product,$catalog,['productPopularity'=>['source'=>'fulfilled-order-lines','asOf'=>'2026-11-17','counts'=>['two'=>2,'three'=>7,'unknown'=>100,'draft'=>200]]]);$check('known-order-metric-only',array_column($real['popular'],'id')===['three','two']);
$mosaics=true;foreach($model['collections']as $group)$mosaics=$mosaics&&count($group['products'])===3&&$group['count']>=3&&!in_array('hidden',array_column($group['products'],'id'),true);$check('real-collection-mosaics',$mosaics&&count($model['collections'])>=2);
$check('empty-category-links-absent',!in_array('empty',array_column(array_column($model['links'],'params'),'category'),true));
$cms=sexogatePxDiscovery($product,$catalog,['collections'=>[['id'=>'curated','data'=>['enabled'=>true,'title'=>'Bordo seçkisi','productIds'=>'one,two,three,hidden']]]]);$check('actual-cms-collection',$cms['collections'][0]['id']==='curated'&&$cms['collections'][0]['count']===3);
$facts=sexogatePxFacts(array_replace($product,['storefrontFacts'=>['materials'=>'Polyester','sizes'=>'S/M, L/XL','dimensions'=>'2,6 cm'],'specs'=>[['label'=>['tr'=>'Malzeme'],'value'=>['tr'=>'Polyester']]]]),'tr',['materials'=>'Malzeme','sizes'=>'Beden seçenekleri']);$check('decimals-and-unique-facts',count($facts)===3&&$facts[1]['value']==='2,6 cm');
$translated=sexogatePxFacts(array_replace($product,['storefrontStory'=>['en'=>['fields'=>[['key'=>'colors','title'=>'Colour options','value'=>'yellow'],['key'=>'composition','title'=>'Material composition','value'=>'95% polyester, 5% elastane'],['key'=>'productCode','title'=>'Product code','value'=>'seo-one']]]],'storefrontFacts'=>['colors'=>'Sarı']]),'en',['colors'=>'Colour options']);$check('translated-fields-and-code-outside-highlights',count($translated)===2&&$translated[0]['value']==='yellow'&&$translated[1]['id']==='composition');
$storyProduct=array_replace($product,['description'=>['tr'=>"Giriş.\n\nÖlçü 2,6 cm.\n\nİğne oyası detayı."],'storefrontStory'=>['tr'=>['intro'=>'Giriş.']]]);$story=sexogatePxStory($storyProduct,'tr');$check('paragraphs-preserved',$story['paragraphs']===['Ölçü 2,6 cm.','İğne oyası detayı.']);
$copy=sexogatePxCopy('tr');$html=sexogatePxStoryHtml($product,$catalog,'tr',$copy,['intro'=>'<img onerror=bad()>','paragraphs'=>['<script>bad()</script>'],'bullets'=>[],'packageContents'=>[]]);$check('prose-escaped',!str_contains($html,'<script>')&&str_contains($html,'&lt;script&gt;'));
$check('continuation-present-only-with-content',str_contains($html,'<details'));
$empty=sexogatePxStoryHtml($product,$catalog,'tr',$copy,['intro'=>'Kısa giriş.','paragraphs'=>[],'bullets'=>[],'packageContents'=>[]]);$check('empty-continuation-absent',!str_contains($empty,'<details'));
$html=sexogatePxFeatures(array_replace($product,['privateRetailReference'=>12345]),$copy,$facts);$check('sku-visible-private-price-absent',str_contains($html,'seo-one')&&!str_contains($html,'12345'));
$policy=['productExperience'=>['returns'=>['tr'=>['title'=>'İade ve iptal','paragraphs'=>['Gerçek politika özeti.'],'items'=>[['title'=>'Koruyucu unsur','body'=>'Kaynak kuralı.']]]]]];$html=sexogatePxReturns($policy,'tr',$copy);$check('policy-object-readable',str_contains($html,'Kaynak kuralı.')&&!str_contains($html,'Array')&&!str_contains($html,'page=help'));
$check('brand-link-preserves-facet',str_contains(sexogatePxLink('catalog','tr',['brand'=>'İstanbul Markası']),'brand=%C4%B0stanbul%20Markas%C4%B1'));
$check('collection-link-preserves-target',str_contains(sexogatePxLink('catalog','tr',['collection'=>'curated']),'collection=curated'));
if(in_array('--model-json',$argv,true)){echo json_encode($model,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);exit;}
echo json_encode(['passed'=>count($checks),'checks'=>$checks,'realProviderCalled'=>false,'sourceSnapshotChanged'=>false],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR).PHP_EOL;
