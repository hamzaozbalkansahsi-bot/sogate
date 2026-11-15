<?php
declare(strict_types=1);

function nodenoFrontOptions(array $input):array {
 if(array_diff(array_keys($input),['widthMm','heightMm','application']))throw new InvalidArgumentException('front_options_invalid');
 $o=['widthMm'=>$input['widthMm']??0,'heightMm'=>$input['heightMm']??0,'application'=>$input['application']??'solid'];
 if(!is_int($o['widthMm'])||$o['widthMm']<1||$o['widthMm']>5000||!is_int($o['heightMm'])||$o['heightMm']<1||$o['heightMm']>5000||!in_array($o['application'],['solid','glazed','drawer','long'],true))throw new InvalidArgumentException('front_measurements_required');return $o;
}
function nodenoFrontLineKey(string $id,array $o):string {return $id.'@'.$o['widthMm'].'x'.$o['heightMm'].'-'.$o['application'];}
function nodenoFrontCartLine(array $item,array $p):array {
 if(array_diff(array_keys($item),['id','quantity','key','options'])||!is_array($item['options']??null))throw new InvalidArgumentException('front_options_invalid');
 $o=nodenoFrontOptions($item['options']);$key=nodenoFrontLineKey($p['id'],$o);if(isset($item['key'])&&$item['key']!==$key)throw new InvalidArgumentException('front_line_key_invalid');return ['id'=>$p['id'],'quantity'=>$item['quantity'],'key'=>$key,'options'=>$o];
}
function nodenoFrontAreaCost(int $rate,int $areaMm2):int {
 // rate <= 100000000 minor/m² and accepted dimensions keep this below PHP_INT_MAX.
 if($rate<0||$rate>100000000||$areaMm2<0||$areaMm2>250000000000)throw new InvalidArgumentException('front_amount_invalid');
 $whole=intdiv($areaMm2,1000000)*$rate;$remainder=$areaMm2%1000000;return $whole+intdiv($remainder*$rate+500000,1000000);
}
function nodenoFrontPrice(array $p,array $input,int $quantity):array {
 $o=nodenoFrontOptions($input);if($quantity<1||$quantity>10000)throw new InvalidArgumentException('front_quantity_invalid');
 $area=$o['widthMm']*$o['heightMm'];$totalArea=$area*$quantity;$rate=$p['salePriceMinor']??null;$quoted=!is_int($rate)||$rate<=0||($o['application']==='glazed'&&empty($p['front']['glazingPriceVerified']));
 return ['areaMm2'=>$totalArea,'unitAreaMm2'=>$area,'unitRateMinor'=>$rate,'unitPriceMinor'=>$quoted?null:nodenoFrontAreaCost($rate,$area),'lineTotalMinor'=>$quoted?null:nodenoFrontAreaCost($rate,$totalArea),'requiresQuote'=>$quoted];
}
