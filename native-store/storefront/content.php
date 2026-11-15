<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/content.php
 * Açıklama   : Gerçek ürün verisini kısa anlatım ve okunabilir özelliklere dönüştürür; kaynak kaydı değiştirmez.
 */
declare(strict_types=1);
function sexogateStorefrontCopy():array{
 static $copy=null;if($copy===null){$file=__DIR__.'/sexogate-storefront-copy.json';if(!is_file($file))$file=__DIR__.'/copy.json';$copy=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);}return $copy;
}
function sexogateStorefrontClean(mixed $value,int $limit=220):string{
 if(!is_string($value))return '';$value=trim(preg_replace('/\s+/u',' ',strip_tags($value))??'');if($value===''||preg_match('/^(?:none|null|undefined)$/iu',$value))return '';
 if(preg_match('/medikal|sertifik|su geçirme|cilt dost|tedavi|kesin sonuç|maksimum|orgazm|performans.{0,30}art/iu',$value))return '';
 $value=preg_split('/\s*(?:Kullanım\s*(?:Talimatları|Şekli|Tavsiyeleri)|Ürün Açıklaması|Uyarılar|Özellikler)\s*:/iu',$value)[0];
 if(preg_match_all('/./us',$value)>$limit)return '';return trim($value," \t\n\r\0\x0B:;");
}
function sexogateStorefrontProduct(array $product):array{
 if(($product['catalogOrigin']??'')!=='sexogate-suppliers-v1')return $product;
 $copy=sexogateStorefrontCopy();$facts=$product['facts']??[];$name=(string)($product['name']['tr']??'');$dimensions=(string)($facts['dimensions']??'');$rows=[];
 $add=static function(string $key,mixed $value)use(&$rows):void{$value=sexogateStorefrontClean($value);if($value!=='')$rows[$key]=$value;};
 // İçe aktarılan alan bir reklam paragrafı olabilir; yalnız açık malzeme adını göster.
 $materialText=(string)($facts['materials']??'').' '.$name;
 if(preg_match_all('/\b(PVC|ABS|TPE|TPR|silikon|silicone|paslanmaz çelik|polyester|poliamid|elastan|pamuk)\b/iu',$materialText,$materials))$add('materials',implode(', ',array_unique($materials[1])));
 if(preg_match('/(?<!\d)(\d+(?:[,.]\d+)?)\s*(cm|mm)\b/iu',$name,$match))$add('dimensions',$match[1].' '.$match[2]);
 elseif(preg_match('/^(\d+(?:[,.]\d+)?(?:\s*[x×]\s*\d+(?:[,.]\d+)?){0,2})\s*(cm|mm)\b/iu',trim($dimensions),$match))$add('dimensions',$match[1].' '.$match[2]);
 foreach(['diameter'=>'/(?:çap|diameter)\s*:?\s*(\d+(?:[,.]\d+)?)\s*(cm|mm)\b/iu','weight'=>'/(?:ağırlık|weight)\s*:?\s*(\d+(?:[,.]\d+)?)\s*(kg|gr|g)\b/iu']as $key=>$pattern)if(preg_match($pattern,$dimensions,$match))$add($key,$match[1].' '.$match[2]);
 if(preg_match('/(?<!\d)(\d+(?:[,.]\d+)?)\s*(ml|litre|liter)\b/iu',$name,$match))$add('volume',$match[1].' '.$match[2]);
 foreach(['sizes'=>'sizeOptions','colors'=>'colorOptions','battery'=>'batteryInformation','ingredients'=>'ingredients','manufacturer'=>'manufacturer','origin'=>'origin','package'=>'packageDimensions']as $key=>$source)$add($key,$facts[$source]??null);
 $care=sexogateStorefrontClean($facts['care']??null,900);$safety=sexogateStorefrontClean($facts['safety']??null,900);$descriptors=[];
 foreach(['/vantuz/iu'=>'vantuz tabanlı','/kumandal/iu'=>'kumandalı','/titreşim/iu'=>'titreşimli','/şarj/iu'=>'şarjlı','/jartiyer/iu'=>'jartiyer detaylı','/dantel/iu'=>'dantel detaylı','/saten/iu'=>'saten dokulu','/su bazlı/iu'=>'su bazlı']as $pattern=>$text)if(preg_match($pattern,$name))$descriptors[]=$text;
 if(preg_match('/(\d+)\s*fonksiyon/iu',$name,$match))array_unshift($descriptors,$match[1].' fonksiyonlu');
 $trIntro='';$kind=preg_match('/gecelik/iu',$name)?'gecelik':(preg_match('/seti|set |set$/iu',$name)?'set':(preg_match('/kayganlaştırıcı/iu',$name)?'jel':'model'));
 if($descriptors){$prefix=implode(', ',array_slice($descriptors,0,3));$prefix=preg_replace_callback('/^./u',static fn($m)=>strtoupper(strtr($m[0],['i'=>'İ','ı'=>'I','ş'=>'Ş','ğ'=>'Ğ','ç'=>'Ç','ö'=>'Ö','ü'=>'Ü'])),$prefix);$trIntro=$prefix.' '.$kind.'.';}
 if(isset($rows['dimensions']))$trIntro.=($trIntro!==''?' Ölçüsü '.$rows['dimensions'].'.':$rows['dimensions'].' ölçüsündeki model'.(isset($rows['diameter'])?', '.$rows['diameter'].' çapındadır.':'.'));
 if(isset($rows['materials']))$trIntro.=($trIntro!==''?' ':'').'Malzeme: '.$rows['materials'].'.';
 if(isset($rows['volume']))$trIntro.=($trIntro!==''?' ':'').'Hacmi '.$rows['volume'].'.';
 if($trIntro==='')$trIntro=rtrim(sexogateStorefrontClean($name,250),'.').'.';
 $story=[];$specs=[];foreach($rows as $key=>$value){$label=[];$values=[];foreach($copy as $locale=>$labels){$label[$locale]=$labels[$key];$values[$locale]=$value;}$specs[]=['label'=>$label,'value'=>$values];}
 foreach($copy as $locale=>$labels){$intro=$locale==='tr'?$trIntro:rtrim((string)($product['name'][$locale]??$product['name']['en']??''),'.').'.';$story[$locale]=['intro'=>$intro,'care'=>$care,'safety'=>$safety];$paragraphs=[$intro];foreach($rows as $key=>$value)$paragraphs[]=$labels[$key].': '.$value.'.';if($care!=='')$paragraphs[]=$labels['care'].': '.$care;if($safety!=='')$paragraphs[]=$labels['safety'].': '.$safety;$product['description'][$locale]=implode("\n\n",$paragraphs);}
 $product['storefrontStory']=$story;$product['storefrontFacts']=$rows;$product['specs']=$specs;return $product;
}
