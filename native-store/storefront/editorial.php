<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/editorial.php
 * Açıklama   : Gerçek niteliklerden başlık, paket içeriği ve ürün anlatımı üretir; özel kaynağı müşteriye döndürmez.
 */
declare(strict_types=1);
function sexogateEditorialFingerprint(array $product):string{return hash('sha256',json_encode([$product['name']??[],$product['description']??[],$product['facts']??[],$product['code']??''],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR));}
function sexogateEditorialLower(string $text):string{return strtolower(strtr($text,['İ'=>'i','I'=>'ı','Ş'=>'ş','Ğ'=>'ğ','Ü'=>'ü','Ö'=>'ö','Ç'=>'ç']));}
function sexogateEditorialUpper(string $text):string{return strtoupper(strtr($text,['i'=>'İ','ı'=>'I','ş'=>'Ş','ğ'=>'Ğ','ü'=>'Ü','ö'=>'Ö','ç'=>'Ç']));}
function sexogateEditorialCase(string $text):string{
 $acronyms=['PVC','ABS','TPE','TPR','USB','BDSM','LED','G','XL','XXL','S','M','L','TR','CN'];
 $text=preg_replace_callback('/[\p{L}]+(?:\d+[\p{L}\d-]*)?/u',static function($m)use($acronyms){$word=$m[0];if(preg_match('/\d/',$word))return $word;if(in_array(strtoupper($word),$acronyms,true))return strtoupper($word);$lower=sexogateEditorialLower($word);$correct=['dıldo'=>'dildo','penıs'=>'penis','vıbratör'=>'vibratör','vıbrator'=>'vibratör','sılıkon'=>'silikon','mını'=>'mini','jartıyer'=>'jartiyer','realıstık'=>'realistik','işlevlı'=>'işlevli','glımmer'=>'glimmer'];$lower=$correct[$lower]??$lower;if($word===sexogateEditorialUpper($word)||$word===sexogateEditorialLower($word))return preg_replace_callback('/^./u',static fn($a)=>sexogateEditorialUpper($a[0]),$lower);return $word;},$text)??$text;
 return str_replace([' Ve ',' İle ',' Veya ',' İçin '],[' ve ',' ile ',' veya ',' için '],$text);
}
function sexogateEditorialData(array $product):array{
 static $data=null;if($data===null){$file=__DIR__.'/sexogate-product-editorial-data.json';if(!is_file($file))$file=__DIR__.'/product-editorial-data.json';$data=is_file($file)?json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR):[];}
 $entry=$data['products'][$product['id']??'']??[];return ($entry['sku']??null)===($product['sku']??null)?$entry:[];
}
function sexogateEditorialTitle(string $title,string $brand=''):array{
 $title=trim(html_entity_decode(strip_tags($title),ENT_QUOTES|ENT_HTML5,'UTF-8'));$package=[];
 $title=preg_replace('/(?<=[a-zçğıöşü])(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])/u',' ',$title)??$title;
 $title=preg_replace_callback('/\(([^()]*)\)/u',static function($m)use(&$package){$inside=$m[1];if(!str_contains($inside,'*'))return $m[0];$parts=preg_split('/\s*\*+\s*/u',$inside);$parts=array_values(array_filter(array_map('trim',$parts)));if(count($parts)<2)return str_replace('*',' ',$m[0]);foreach($parts as $part)if(!preg_match('/babydol|etek|çorap|sütyen|külot|jartiyer|body|gecelik|eldiven|maske|kemer|kırbaç|kelepçe|tasma|bağı|dildo|vibratör|plug|kılıf/iu',sexogateEditorialLower($part)))return str_replace('*',' ',$m[0]);foreach($parts as $part){$part=sexogateStorefrontClean($part,100);if($part!=='')$package[]=sexogateEditorialCase($part);}return '';},$title)??$title;
 if($package)$title=preg_replace('/\b\d+\s*(?:Parça|PARÇA|parça)\b\s*/u','',$title)??$title;
 $title=preg_replace('/\*+|[!]{2,}|[_]{2,}/u',' ',$title)??$title;
 if($brand!==''){$quoted=preg_quote($brand,'/');$title=preg_replace('/^(?:'.$quoted.'\s+)+/iu','',$title)??$title;}
 $title=sexogateEditorialCase($title);$title=preg_replace('/\b(?:medikal\s+(?=silikon)|su\s+geçirmez|suya\s+dayanıklı|sertifikalı|cilt\s+dostu|hipoalerjenik|antialerjik|kesin\s+sonuç|maksimum\s+uyarılma|zevk\s+artırıcı|büyütücü|kalınlaştırıcı|kalınlaştıcı|uzatıcı|sertleştirici|geciktirici)\b/iu','',$title)??$title;
 $title=trim(preg_replace('/\s+/u',' ',$title)??$title," \t\n\r:;-|.");$title=sexogateEditorialCase($title);return ['title'=>$title,'package'=>array_values(array_unique($package))];
}
function sexogateEditorialEnglish(string $value):string{
 $value=preg_replace('/(?<!\p{L})Sarı(?!\p{L})/iu','yellow',$value)??$value;
 $map=['Siyah'=>'black','Beyaz'=>'white','Bordo'=>'burgundy','Kırmızı'=>'red','Mavi'=>'blue','Mor'=>'purple','Pembe'=>'pink','Fuşya'=>'fuchsia','Yeşil'=>'green','Gri'=>'grey','Ten'=>'nude','Şeffaf'=>'transparent','Çok Renkli'=>'multicolour','Polyester'=>'polyester','Poliamid'=>'polyamide','Elastan'=>'elastane','Pamuk'=>'cotton','Silikon'=>'silicone','Paslanmaz Çelik'=>'stainless steel','Dantel'=>'lace','Tül'=>'tulle','Saten'=>'satin','Örme'=>'knitted','Dokuma'=>'woven','Düz'=>'plain','Kalp'=>'heart','Askılı'=>'strappy','V Yaka'=>'V-neck','V Yaka'=>'V-neck','Regular'=>'regular','Mini'=>'mini','Manuel'=>'manual','Şarjlı'=>'rechargeable','Pilli'=>'battery-powered','Var'=>'yes','Babydol'=>'babydoll','Babydoll'=>'babydoll','Etek'=>'skirt','File Çorap'=>'fishnet stockings','Çorap'=>'stockings','Eldiven'=>'gloves','Maske'=>'mask','Türkiye'=>'Türkiye','Çin'=>'China'];
 $value=trim($value);foreach($map as $tr=>$en)$value=preg_replace('/(?<!\p{L})'.preg_quote($tr,'/').'(?!\p{L})/iu',$en,$value)??$value;
 $value=preg_replace('/(\d+)\s*[%]\s*/u','$1% ',$value)??$value;$value=preg_replace('/[%]\s*(\d+)/u','$1%',$value)??$value;
 $value=str_replace(['Türkiye','Çin','ABD','Birleşik Krallık','Almanya'],['Turkey','China','USA','United Kingdom','Germany'],$value);return preg_match('/[ıİşŞğĞçÇöÖüÜ]/u',$value)?'':$value;
}
function sexogateEditorialType(array $product,string $name):array{
 $name=sexogateEditorialLower($name);
 foreach(['/pijama/u'=>['pijama takımı','pyjama set'],'/göğüs.{0,15}(?:klips|kelepçe)|nipple clamp/u'=>['göğüs klipsi','nipple clamp'],'/anahtarlık/u'=>['anahtarlık','keyring'],'/çark/u'=>['çark oyunu','spinner game'],'/kırbaç/u'=>['kırbaç','whip'],'/fetish tüy|fetiş tüy/u'=>['tüy aksesuarı','feather accessory']]as $pattern=>$type)if(preg_match($pattern,$name))return $type;
 if(preg_match('/tarot/u',$name))return ['tarot kartları','tarot cards'];
 if(preg_match('/\btablet/u',$name))return ['tablet','tablet'];if(preg_match('/\bkapsül/u',$name))return ['kapsül','capsule'];if(preg_match('/\bhap\b/u',$name))return ['hap','pill'];
 if(preg_match('/gecelik/iu',$name)){$set=(bool)preg_match('/takım|set/iu',$name);$mini=(bool)preg_match('/mini/iu',$name);return [($mini?'mini ':'').'gecelik'.($set?' takımı':''),($mini?'mini ':'').($set?'nightwear set':'nightdress')];}
 $categoryIds=$product['categoryIds']??[];$category=end($categoryIds);$suffix=is_string($category)?substr($category,strrpos($category,'_')+1):'';
 $types=['machines'=>['seks makinesi','sex machine'],'dice'=>['oyun zarı','game dice'],'cards'=>['kart oyunu','card game'],'games'=>['çift oyunu','couples game'],'breastforms'=>['giyilebilir göğüs formu','wearable breast form'],'chastity'=>['kafes ve kilit aksesuarı','cage and lock accessory'],'positioning'=>['pozisyon desteği','positioning aid'],'sleeves'=>['penis kılıfı','penis sleeve'],'plugs'=>['anal oyuncak','anal toy'],'rings'=>['penis halkası','penis ring'],'masturbators'=>['mastürbatör','masturbator'],'vibrators'=>['vibratör','vibrator'],'dildos'=>['dildo','dildo'],'pumps'=>['vakum pompası','vacuum pump'],'lubricants'=>['kayganlaştırıcı','personal lubricant'],'oils'=>['masaj yağı','massage oil'],'condoms'=>['prezervatif','condom'],'cleaners'=>['bakım ürünü','care product'],'straps'=>['kemer ve bağlama aksesuarı','harness accessory'],'bodies'=>['body','bodysuit'],'briefs'=>['külot','briefs'],'bras'=>['sütyen','bra'],'dresses'=>['elbise','dress'],'tanks'=>['atlet','undershirt'],'shapewear'=>['korse','shapewear'],'pajamas'=>['pijama takımı','pyjama set'],'robes'=>['sabahlık','robe'],'leggings'=>['tayt','leggings'],'thermal'=>['termal içlik','thermal underwear'],'tights'=>['çorap','stockings'],'boxers'=>['boxer','boxer shorts'],'sets'=>['iç giyim takımı','lingerie set'],'garters'=>['jartiyer takımı','garter set'],'costumes'=>['kostüm','costume']];
 if(isset($types[$suffix])&&!preg_match('/\b(?:tablet|hap|kapsül|ilaç)\b/iu',$name))return $types[$suffix];
 foreach(['/\b(?:tablet|hap|kapsül)/iu'=>['ürün','product'],'/gecelik/iu'=>[str_contains(sexogateEditorialLower($name),'mini')?'mini gecelik takımı':'gecelik','nightwear set'],'/jartiyer/iu'=>['jartiyer takımı','garter set'],'/vücut çorab/iu'=>['vücut çorabı','body stocking'],'/penis.{0,24}kılıf|penis dildo kılıf/iu'=>['penis kılıfı','penis sleeve'],'/penis.{0,24}halka|halka.{0,24}penis/iu'=>['penis halkası','penis ring'],'/pompa/iu'=>['vakum pompası','vacuum pump'],'/plug/iu'=>['anal plug','anal plug'],'/mastürbat|masturbat/iu'=>['mastürbatör','masturbator'],'/vibrat/iu'=>['vibratör','vibrator'],'/dildo/iu'=>['dildo','dildo'],'/kayganlaştır/iu'=>['kayganlaştırıcı','personal lubricant'],'/zar/iu'=>['oyun zarı','game dice'],'/kart/iu'=>['kart oyunu','card game'],'/kelepçe/iu'=>['kelepçe seti','restraint set'],'/kostüm/iu'=>['kostüm','costume'],'/boxer/iu'=>['boxer','boxer shorts'],'/sütyen/iu'=>['sütyen','bra'],'/külot/iu'=>['külot','briefs']]as $pattern=>$kind)if(preg_match($pattern,$name))return $kind;
 foreach(['sg_lingerie'=>['iç giyim','lingerie'],'sg_accessories'=>['fantezi aksesuarı','fantasy accessory'],'sg_care'=>['bakım ürünü','care product'],'sg_couples'=>['çift ürünü','couples accessory'],'sg_toys'=>['yetişkin ürünü','adult product']]as $id=>$type)if(in_array($id,$categoryIds,true))return $type;
 return ['ürün','product'];
}
function sexogateEditorialNarrative(string $description,string $name,string $sku):array{
 $result=[];foreach(preg_split('/(?<=[.!?])\s+|\r?\n/u',$description)as $sentence){$sentence=trim($sentence);$lower=sexogateEditorialLower($sentence);if($sentence===''||preg_match('/Ürün kodu\s*:|Product code\s*:/iu',$sentence)||(str_contains($lower,'trendyol')&&preg_match('/yorumlarını inceleyin|satın alın/u',$lower)))continue;if(rtrim($sentence,'.')===rtrim($name,'.'))continue;if(preg_match('/^(?:Malzeme|Ölçü|Beden seçenekleri|Renk seçenekleri|Material|Dimensions|Size options|Colour options)\s*:/iu',$sentence))continue;$clean=sexogateStorefrontClean($sentence,1500);if($clean!==''&&strlen($clean)>35)$result[]=$clean;}
 return array_values(array_unique($result));
}
function sexogateEditorialEnrich(array $product,array $original,array $rows,array $entry):array{
 $attrs=[];foreach($entry['attributes']??[]as $attribute){$value=sexogateStorefrontClean($attribute['value']??null,500);if($value!=='')$attrs[$attribute['name']]=$value;}
 if(isset($entry['catalogFacts'])&&($original['facts']??[])!==$entry['catalogFacts'])$attrs=[];
 $title=sexogateEditorialTitle((string)($original['name']['tr']??''),(string)($original['brand']??''));$product['name']['tr']=$title['title'];$product['modelName']['tr']=$title['title'];$product['seoTitle']['tr']=$title['title'];
 [$typeTr,$typeEn]=sexogateEditorialType($product,$title['title']);$featuresTr=[];$featuresEn=[];
 foreach(['/kalp/iu'=>['kalp','heart detail'],'/dantel/iu'=>['dantel','lace detail'],'/vantuz/iu'=>['vantuz tabanı','suction base'],'/kumandalı/iu'=>['uzaktan kumanda','remote control'],'/titreşim(?!siz)/iu'=>['titreşim','vibration'],'/şarjlı|şarj edileb/iu'=>['şarjlı kullanım','rechargeable operation'],'/damarlı|tırtıklı/iu'=>['dokulu yüzey','textured surface'],'/ayarlanabilir/iu'=>['ayarlanabilir yapı','adjustable design'],'/telefon kontrollü|app controlled/iu'=>['telefonla kontrol','phone control'],'/ileri geri|gidip gel/iu'=>['ileri geri hareket','reciprocating movement'],'/çift giriş|\b2\s*(?:adet\s*)?giriş/iu'=>['iki girişli yapı','two-opening design'],'/üç giriş|\b3\s*(?:adet\s*)?giriş/iu'=>['üç girişli yapı','three-opening design'],'/transparan|şeffaf/iu'=>['şeffaf tasarım','transparent design'],'/\bfile\b/iu'=>['file ayrıntıları','mesh details']]as $pattern=>$pair)if(preg_match($pattern,sexogateEditorialLower($title['title']))){$featuresTr[]=$pair[0];$featuresEn[]=$pair[1];}
 $colors=$rows['colors']??'';$enColor=sexogateEditorialEnglish($colors);$enFeatures=array_values(array_intersect($featuresEn,['heart detail','lace detail','suction base','remote control','vibration','textured surface']));
 $enName=trim(($enColor!==''?ucfirst($enColor).' ':'').$typeEn.($enFeatures?' with '.implode(' and ',array_slice($enFeatures,0,2)):''));$enName=str_replace('heart detail and lace detail','heart and lace details',$enName);$enName=str_replace([' With ',' And ',' Of '],[' with ',' and ',' of '],ucwords($enName));
 if($typeEn==='product')$enName='Product';
 if(!$enColor&&!$enFeatures)$enName.=' – '.(string)($original['code']??'');$product['name']['en']=$product['modelName']['en']=$product['seoTitle']['en']=$enName;
 $count=null;if(preg_match('/\b(\d+)\s*(?:Parça|parça|’lü|\x{0027}lü|’li|\x{0027}li)/u',(string)($original['name']['tr']??'').' '.($attrs['Paket İçeriği']??''),$m))$count=(int)$m[1];if($count===null&&$title['package'])$count=count($title['package']);
 $sourceName=$entry['catalogName']['tr']??null;$sourceNameMatches=is_string($sourceName)&&in_array($original['name']['tr']??null,[$sourceName,sexogateEditorialTitle($sourceName,(string)($original['brand']??''))['title']],true);$sourceFactsMatch=!isset($entry['catalogFacts'])||($original['facts']??[])===$entry['catalogFacts'];
 $packageTr=$title['package'];if(!$packageTr&&$sourceFactsMatch&&$sourceNameMatches&&isset($entry['rawOriginalTitle']))$packageTr=sexogateEditorialTitle($entry['rawOriginalTitle'])['package'];$packageEn=array_values(array_filter(array_map('sexogateEditorialEnglish',$packageTr)));
 $composition=$attrs['Materyal Bileşeni']??($rows['materials']??'');$weave=$attrs['Kumaş Tipi']??($attrs['Dokuma Tipi']??'');
 $extraFields=['composition'=>['Materyal bileşeni','Material composition',$composition],'fabric'=>['Kumaş yapısı','Fabric construction',$weave],'pattern'=>['Desen','Pattern',$attrs['Desen']??''],'neckline'=>['Yaka','Neckline',$attrs['Yaka Tipi']??''],'sleeve'=>['Kol tipi','Sleeve style',$attrs['Kol Tipi']??''],'fit'=>['Kalıp','Fit',$attrs['Kalıp']??''],'operation'=>['Çalışma biçimi','Operation',$attrs['Çalışma Tipi']??''],'vibration'=>['Titreşim','Vibration',$attrs['Titreşim']??'']];
 if(preg_match('/\b(\d+)\s*(?:modlu|fonksiyonlu|farklı mod)/iu',$title['title'],$mode))$extraFields['modes']=['Mod sayısı','Mode count',$mode[1]];
 if(preg_match('/(?<!\d)(\d+(?:[,.]\d+)?)\s*(kg|gr|g)\b/iu',$title['title'],$mass))$extraFields['productWeight']=['Ürün ağırlığı','Product weight',$mass[1].' '.$mass[2]];
 $extraFields['productCode']=['Ürün kodu','Product code',(string)($product['code']??'')];
 if($count!==null)$extraFields['pieceCount']=['Parça sayısı','Piece count',(string)$count];
 $copy=sexogateStorefrontCopy();$stories=[];
 foreach(['tr','en']as $locale){$isTr=$locale==='tr';$fields=[];$paragraphs=[];$bullets=[];$name=$isTr?$title['title']:$enName;$manual=sexogateEditorialNarrative((string)($original['description'][$locale]??''),(string)($original['name'][$locale]??''),(string)($original['sku']??''));
  if($isTr){$intro=$featuresTr?$typeTr.', '.implode(' ve ',array_slice($featuresTr,0,3)).' özelliklerini bir araya getirir.':$title['title'].'.';$intro=preg_replace_callback('/^./u',static fn($m)=>sexogateEditorialUpper($m[0]),$intro);if($colors!=='')$intro.=' Renk: '.sexogateEditorialLower($colors).'.';if(isset($rows['dimensions']))$intro.=' Ölçüsü '.$rows['dimensions'].'.';}
  else{$plural=in_array($typeEn,['tarot cards','game dice','briefs','stockings','boxer shorts','leggings'],true);$article=preg_match('/^[aeiou]/',$typeEn)?'an':'a';$intro=$featuresEn?($plural?'These ':'This ').$typeEn.($plural?' feature ':' features ').implode(', ',array_slice($featuresEn,0,3)).'.':($plural?'This model is listed as '.$typeEn.'.':'This is '.$article.' '.$typeEn.' model.');if($enColor!=='')$intro.=' Colour: '.$enColor.'.';if(isset($rows['dimensions']))$intro.=' Dimensions: '.$rows['dimensions'].'.';}
  if($typeTr==='ürün'&&$isTr)$intro=$title['title'].'.';if($manual){$intro=array_shift($manual);$paragraphs=$manual;}
  $package=$isTr?$packageTr:$packageEn;if($package)$paragraphs[]=($isTr?'Takım içeriği: ':'The set contains ').implode(', ',$package).'.';elseif($count!==null)$paragraphs[]=($isTr?'Paket '.$count.' parçadan oluşur.':'The pack contains '.$count.' pieces.');
  if($composition!==''){$value=$isTr?$composition:sexogateEditorialEnglish($composition);if($value!=='')$paragraphs[]=($isTr?'Materyal bileşeni '.$value.'.':'Material composition: '.$value.'.');}
  if($weave!==''){$value=$isTr?sexogateEditorialLower($weave):sexogateEditorialEnglish($weave);if($value!=='')$paragraphs[]=($isTr?'Kumaşı '.$value.' yapıdadır.':'Fabric construction: '.$value.'.');}
  $detail=[];foreach(['sizes','volume','diameter','weight','battery','origin']as $key)if(isset($rows[$key])){$value=$isTr?$rows[$key]:sexogateEditorialEnglish($rows[$key]);if($value!=='')$detail[]=($copy[$locale][$key]??$key).': '.$value;}
  if($detail)$paragraphs[]=implode('; ',$detail).'.';
  foreach($rows as $key=>$rawValue){$value=$isTr?$rawValue:sexogateEditorialEnglish($rawValue);if($value==='')continue;$label=$copy[$locale][$key]??$key;$fields[]=['title'=>$label,'value'=>$value,'key'=>$key];}
  foreach($extraFields as $key=>[$labelTr,$labelEn,$rawValue]){if($rawValue==='')continue;$value=$isTr||$key==='productCode'?$rawValue:sexogateEditorialEnglish($rawValue);if($value!=='')$fields[]=['title'=>$isTr?$labelTr:$labelEn,'value'=>$value,'key'=>$key];}
  if($featuresTr)$fields[]=['title'=>$isTr?'Tasarım ayrıntıları':'Design details','value'=>implode(', ',$isTr?$featuresTr:$featuresEn),'key'=>'design'];
  foreach($featuresTr as $i=>$feature)$bullets[]=$isTr?preg_replace_callback('/^./u',static fn($m)=>sexogateEditorialUpper($m[0]),$feature):ucfirst($featuresEn[$i]);
  $care=sexogateStorefrontClean($original['facts']['care']??null,1500);$safety=sexogateStorefrontClean($original['facts']['safety']??null,1500);
  foreach(['care'=>['Bakım Talimatı','Yıkama Talimatı'],'safety'=>['Ürün Güvenliği Bilgisi','Kullanım Uyarısı']]as $target=>$keys)if($$target==='')foreach($keys as $key)if(isset($attrs[$key])&&preg_match('/\s/u',$attrs[$key])&&!preg_match('/^[A-Z]\d+$/D',$attrs[$key])){$$target=$attrs[$key];break;}
  if(!$isTr){$care=sexogateEditorialEnglish($care);$safety=sexogateEditorialEnglish($safety);}
  $paragraphs=array_values(array_unique(array_filter($paragraphs,static fn($v)=>$v!==''&&$v!==$intro)));
  $stories[$locale]=['intro'=>$intro,'paragraphs'=>$paragraphs,'bullets'=>$bullets,'packageContents'=>$package,'care'=>$care,'safety'=>$safety,'fields'=>$fields,'specGroups'=>[['title'=>$isTr?'Ürün özellikleri':'Product details','fields'=>$fields]]];
  $body=[$intro,...$paragraphs];foreach($fields as $field)$body[]=$field['title'].': '.$field['value'].'.';if($care!=='')$body[]=($isTr?'Bakım: ':'Care: ').$care;if($safety!=='')$body[]=($isTr?'Kullanım uyarısı: ':'Safety: ').$safety;
  $product['description'][$locale]=implode("\n\n",array_values(array_unique($body)));$product['seoDescription'][$locale]=$intro;
  foreach(['seoTitle'=>'catalogSeoTitle','seoDescription'=>'catalogSeoDescription']as $field=>$snapshot){$prior=$original[$field][$locale]??'';$default=$entry[$snapshot][$locale]??null;if(is_string($default)&&is_string($prior)&&$prior!==$default&&$prior!==($original['name'][$locale]??'')){$manualMeta=sexogateStorefrontClean($prior,$field==='seoTitle'?300:500);if($manualMeta!=='')$product[$field][$locale]=$manualMeta;}}
 }
 foreach($copy as $locale=>$labels)if(!isset($stories[$locale])){$existing=sexogateEditorialNarrative((string)($original['description'][$locale]??''),'',(string)($original['sku']??''));$intro=$existing[0]??(string)($original['name'][$locale]??$title['title']);$stories[$locale]=['intro'=>$intro,'paragraphs'=>array_slice($existing,1)];$product['description'][$locale]=$original['description'][$locale]??$intro;}
 $stories['tr']['projectionHash']=sexogateEditorialFingerprint($product);$product['storefrontStory']=$stories;$product['storefrontFacts']=$rows;return $product;
}
