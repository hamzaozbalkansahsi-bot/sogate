<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/variants.php
 * Açıklama   : Kaynak seçeneklerinden doğrulanabilir beden/renk şeması ve değişmez sipariş seçimi oluşturur.
 */
declare(strict_types=1);
function sexogateSelectionValues(?string $text):array{
 return array_values(array_unique(array_filter(array_map('trim',explode(',',(string)$text)),static fn($v)=>$v!=='')));
}
function sexogateSelectionSchema(array $product,array $work):array{
 $facts=$product['facts']??$work['facts'];$groups=['size'=>sexogateSelectionValues($facts['sizeOptions']??null),'color'=>sexogateSelectionValues($facts['colorOptions']??null)];$source=$work['sourceVariants']??[];$rows=[];$unknown=false;
 foreach($source as $variant){$values=[];
  foreach($variant['attributes']??[]as $value){$name=strtolower((string)($value['name']??''));$axis=match($name){'beden','size'=>'size','renk','color','colour'=>'color',default=>null};if($axis===null){$unknown=true;continue;}$label=trim((string)($value['value']??''));if($label!==''){$values[$axis]=$label;if(!in_array($label,$groups[$axis],true))$groups[$axis][]=$label;}}
  foreach($variant['variantValues']??[]as $value){$label=trim((string)($value['name']??''));$matches=array_keys(array_filter($groups,static fn($labels)=>in_array($label,$labels,true)));if(count($matches)!==1){$unknown=true;continue;}$values[$matches[0]]=$label;}
  if($values)$rows[]=['reference'=>(string)($variant['id']??''),'sku'=>is_string($variant['sku']??null)&&$variant['sku']!==''?$variant['sku']:null,'active'=>($variant['isActive']??true)===true,'labels'=>$values];
 }
 $axes=[];foreach($groups as $key=>$labels)if($labels)$axes[]=['id'=>$key,'label'=>$key==='size'?'Beden':'Renk','values'=>array_map(static fn($label)=>['id'=>substr(hash('sha256',$label),0,12),'label'=>$label],$labels)];
 $required=(bool)$axes||(bool)$source;$variants=[];
 foreach($rows as $row){$values=[];foreach($axes as $axis){$label=$row['labels'][$axis['id']]??(count($axis['values'])===1?$axis['values'][0]['label']:null);if($label===null){$unknown=true;continue 2;}$values[$axis['id']]=substr(hash('sha256',$label),0,12);}$variants[]=['id'=>substr(hash('sha256',$row['reference'].json_encode($values)),0,16),'sourceVariantId'=>$row['reference'],'sourceSku'=>$row['sku'],'values'=>$values,'active'=>$row['active']];}
 // Flat public selectors are independent options, never invented supplier SKUs or stock.
 $seen=[];foreach($variants as $variant)if($variant['active']){$key=json_encode($variant['values']);if(isset($seen[$key]))$unknown=true;$seen[$key]=true;}
 $mode=$source?'matrix':'options';$blocked=$required&&(!$axes||($source&&(!$variants||$unknown)));
 return ['required'=>$required,'mode'=>$mode,'blocked'=>$blocked,'axes'=>$axes,'variants'=>$variants];
}
function sexogateSelectionRequired(array $product):bool{return ($product['variantSelection']['required']??false)===true;}
function sexogateSelectionEditorText(array $product,array $values,array $work):string{
 foreach(['sizeOptions','colorOptions']as $key)if(isset($values[$key]))$product['facts'][$key]=$values[$key];$schema=sexogateSelectionSchema($product,$work);if(!$schema['required'])return 'Bu ürün için beden veya renk seçeneği kayıtlı değil.';
 $parts=[];foreach($schema['axes']as $axis)$parts[]=$axis['label'].': '.implode(', ',array_column($axis['values'],'label'));
 $parts[]=$schema['blocked']?'Kaynak seçenekleri eksik veya belirsiz. Sepete ekleme kapalı.':'Sepete eklerken bütün seçenekler müşteri tarafından belirlenir.';$parts[]=$schema['mode']==='matrix'?'Yalnız kaynakta kayıtlı, aktif seçenek birleşimleri kabul edilir.':'Kaynağın bağımsız seçenekleri saklanır; tedarikçi varyant kodu veya stok miktarı üretilmez.';
 return implode("\n",$parts);
}
function sexogateSelectionProduct(array $product):array{
 static $index=null;if($index===null)$index=json_decode(file_get_contents(__DIR__.'/catalog-selections.json'),true,128,JSON_THROW_ON_ERROR);$row=$index[$product['id']]??null;if(!$row)throw new RuntimeException('selection_index_missing');
 if(($product['facts']['sizeOptions']??null)===$row['sizeOptions']&&($product['facts']['colorOptions']??null)===$row['colorOptions'])return $row['schema'];
 return sexogateSelectionSchema($product,sexogateCatalogWork(__DIR__,$product['id']));
}
function sexogateSelectionLine(array $product,array $item):array{
 $schema=$product['variantSelection']??[];$axes=$schema['axes']??[];$selection=$item['options']['selection']??null;
 if(!sexogateSelectionRequired($product)||!$axes||($schema['blocked']??false)||!is_array($selection)||array_is_list($selection))throw new InvalidArgumentException('variant_selection_required');
 if(($item['id']??null)!==$product['id']||!is_int($item['quantity']??null)||$item['quantity']<1||$item['quantity']>99||array_diff(array_keys($item),['id','quantity','key','options'])||array_keys($item['options'])!==['selection']||count($selection)!==count($axes))throw new InvalidArgumentException('variant_selection_invalid');
 $clean=[];foreach($axes as $axis){$value=$selection[$axis['id']]??null;if(!is_string($value)||!in_array($value,array_column($axis['values'],'id'),true))throw new InvalidArgumentException('variant_selection_invalid');$clean[$axis['id']]=$value;}
 if($schema['mode']==='matrix'){$match=false;foreach($schema['variants']as $variant)if($variant['active']&&$variant['values']===$clean){$match=true;break;}if(!$match)throw new InvalidArgumentException('variant_combination_unavailable');}
 $key=$product['id'].'~'.implode('.',array_values($clean));if(isset($item['key'])&&$item['key']!==$key)throw new InvalidArgumentException('variant_key_invalid');
 return ['id'=>$product['id'],'quantity'=>$item['quantity'],'key'=>$key,'options'=>['selection'=>$clean]];
}
function sexogateSelectionSnapshot(array $product,array $item):array{
 $line=sexogateSelectionLine($product,$item);$schema=$product['variantSelection'];$attributes=[];
 foreach($schema['axes']as $axis){$value=array_values(array_filter($axis['values'],static fn($v)=>$v['id']===$line['options']['selection'][$axis['id']]))[0];$attributes[]=['axis'=>$axis['id'],'label'=>$axis['label'],'value'=>$value['label']];}
 $source=null;if($schema['mode']==='matrix')foreach($schema['variants']as $variant)if($variant['active']&&$variant['values']===$line['options']['selection']){$source=$variant;break;}
 return ['schema'=>1,'attributes'=>$attributes,'summary'=>implode(' · ',array_map(static fn($v)=>$v['label'].': '.$v['value'],$attributes)),'sourceVariantId'=>$source['sourceVariantId']??null,'sourceSku'=>$source['sourceSku']??null,'productCode'=>$product['code']??null];
}
function sexogateSelectionAccountLine(array $product,array $item,bool $strict):array{
 if(!isset($item['options'])){if(array_diff(array_keys($item),['id','quantity','pendingSelection'])||isset($item['pendingSelection'])&&$item['pendingSelection']!==true)throw new InvalidArgumentException('variant_selection_invalid');return ['id'=>$product['id'],'quantity'=>$item['quantity'],'pendingSelection'=>true];}
 try{return sexogateSelectionLine($product,$item);}catch(InvalidArgumentException $error){if($strict)throw $error;return ['id'=>$product['id'],'quantity'=>$item['quantity'],'pendingSelection'=>true];}
}
