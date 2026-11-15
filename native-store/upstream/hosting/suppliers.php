<?php
declare(strict_types=1);
require_once __DIR__.'/supplier-watch.php';

/** Private supplier records; never included in the public catalogue projection. */
function nodenoSupplierSeed():array {
 $file=__DIR__.'/supplier-catalog.json';
 if(!is_file($file)||is_link($file))return ['suppliers'=>[],'products'=>[]];
 $seed=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);
 if(($seed['schema']??null)!==1)throw new NodenoControlHttpError(503,'supplier_catalog_invalid');
 return $seed;
}
function nodenoSupplierRows(PDO $db,string $resource):array {
 $q=$db->prepare('SELECT id FROM control_records WHERE resource=? ORDER BY updated_at DESC,id LIMIT 10000');$q->execute([$resource]);
 return array_map(static fn($r)=>nodenoControlRead($db,$resource,$r['id']),$q->fetchAll());
}
function nodenoSupplierSave(array $ctx,string $resource,string $id,array $data,int $version=1):array {
 $db=$ctx['db'];$json=json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);$now=time();
 $db->prepare('INSERT INTO control_records(resource,id,data_json,version,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(resource,id) DO UPDATE SET data_json=excluded.data_json,version=excluded.version,updated_at=excluded.updated_at')->execute([$resource,$id,$json,$version,$now,$now]);
 $db->prepare('INSERT INTO control_record_versions(resource,record_id,version,data_json,actor_id,created_at) VALUES(?,?,?,?,?,?)')->execute([$resource,$id,$version,$json,$ctx['user']['id'],$now]);
 nodenoControlAudit($db,$ctx['root'],$ctx['user']['id'],'supplier_save',$resource,$id,['version'=>$version]);
 return nodenoControlRead($db,$resource,$id);
}
function nodenoSupplierInteger($v,int $min=1,int $max=10000000000):int {
 if(!is_int($v)||$v<$min||$v>$max)throw new NodenoControlHttpError(422,'supplier_number_invalid');return $v;
}
function nodenoSupplierText($v,int $limit=1000):string {
 if(!is_string($v)||strlen($v)>$limit||preg_match('//u',$v)!==1||preg_match('/[\x00-\x1f]/',$v))throw new NodenoControlHttpError(422,'supplier_text_invalid');return trim($v);
}
function nodenoSupplierOverview(array $ctx,array $seed):array {
 $seed=nodenoSupplierEffectiveSeed($ctx['db'],$seed);
 $lists=nodenoSupplierRows($ctx['db'],'supplierLists');$reminders=[];
 foreach($seed['suppliers']as $s)if(!empty($s['priceListRequired'])){
  $last=null;foreach($lists as $l)if(($l['data']['supplierId']??'')===$s['id']&&($l['data']['status']??'')==='approved')$last=max($last??0,$l['data']['receivedAt']);
  $reminders[]=['supplierId'=>$s['id'],'title'=>$s['title'],'lastReceivedAt'=>$last,'dueAt'=>$last?$last+15*86400:null,'due'=>$last===null||time()>=$last+15*86400];
 }
 return ['suppliers'=>$seed['suppliers'],'products'=>$seed['products'],'purchases'=>nodenoSupplierRows($ctx['db'],'supplierPurchases'),'lists'=>$lists,'reminders'=>$reminders,'priceWatch'=>nodenoPaintWatchOverview($ctx['db']),'paintImport'=>['heldCount'=>count($seed['paintImport']['held']??[]),'sourcePendingCount'=>count($seed['paintImport']['sourcePending']??[]),'reviewRows'=>$seed['paintImport']['reviewRows']??[],'checkedAt'=>$seed['paintImport']['checkedAt']??null],'at'=>time()];
}
function nodenoSupplierEffectiveSeed(PDO $db,array $seed):array {
 $mappings=array_column(nodenoSupplierRows($db,'supplierMappings'),null,'id');
 foreach($seed['products']as &$p)if(isset($mappings[$p['id']])){
  $row=$mappings[$p['id']];$changed=false;foreach(['supplierId','sourceCode','sourceUrl']as $key)if(($p[$key]??null)!==($row['data'][$key]??null))$changed=true;
  $p=array_merge($p,$row['data'],['mappingVersion'=>$row['version']]);
  if($changed){$p['sourcePriceMinor']=null;$p['priceStatus']='mapping_review_required';unset($p['priceFetchedAt'],$p['sourceEvidence']);}
 }unset($p);return $seed;
}
function nodenoSupplierMapping(array $ctx,array $body,array $seed):array {
 $id=nodenoSupplierText($body['productId']??'',100);$p=array_column($seed['products'],null,'id')[$id]??null;
 $s=array_column($seed['suppliers'],null,'id')[$body['supplierId']??'']??null;
 if(!$p||!$s)throw new NodenoControlHttpError(422,'supplier_product_mismatch');
 $old=nodenoControlRead($ctx['db'],'supplierMappings',$id);
 if(!is_int($body['version']??null)||$body['version']!==($old['version']??0))throw new NodenoControlHttpError(409,'version_conflict');
 $url=nodenoSupplierText($body['sourceUrl']??'',2000);
 if($url!==''){
  $host=parse_url($url,PHP_URL_HOST);$expected=parse_url($s['url']??'',PHP_URL_HOST);
  if(!$expected||!filter_var($url,FILTER_VALIDATE_URL)||parse_url($url,PHP_URL_SCHEME)!=='https'||$host!==$expected||parse_url($url,PHP_URL_USER)||parse_url($url,PHP_URL_PASS)||parse_url($url,PHP_URL_PORT)||parse_url($url,PHP_URL_FRAGMENT))throw new NodenoControlHttpError(422,'supplier_source_url_invalid');
 }
 $code=nodenoSupplierText($body['sourceCode']??'',200);
 return nodenoSupplierSave($ctx,'supplierMappings',$id,['supplierId'=>$s['id'],'sourceCode'=>$code,'sourceUrl'=>$url?:null],($old['version']??0)+1);
}
function nodenoSupplierPurchase(array $ctx,array $body,array $seed):array {
 $d=$body['data']??null;if(!is_array($d))throw new NodenoControlHttpError(422,'data_required');
 $p=array_column($seed['products'],null,'id')[$d['productId']??'']??null;
 if(!$p||($d['supplierId']??'')!==$p['supplierId'])throw new NodenoControlHttpError(422,'supplier_product_mismatch');
 $quantity=$d['quantity']??null;if(!is_string($quantity)||!preg_match('/^[0-9]{1,7}(?:\.[0-9]{1,3})?$/D',$quantity))throw new NodenoControlHttpError(422,'supplier_quantity_invalid');
 [$whole,$fraction]=array_pad(explode('.',$quantity),2,'');$mill=(int)$whole*1000+(int)str_pad($fraction,3,'0');if($mill<1||$mill>1000000000)throw new NodenoControlHttpError(422,'supplier_quantity_invalid');
 $cost=nodenoSupplierInteger($d['unitCostMinor']??null);if($mill>intdiv(PHP_INT_MAX-500,$cost))throw new NodenoControlHttpError(422,'supplier_number_invalid');$at=nodenoSupplierInteger($d['purchasedAt']??null,946684800,time()+300);
 $unit=$d['unit']??'';$currency=$d['currency']??'';
 if(!in_array($unit,['adet','set','metre','m2','paket'],true)||!in_array($currency,['TRY','USD','EUR','GBP'],true))throw new NodenoControlHttpError(422,'supplier_unit_currency_invalid');
 // A real purchase is one immutable receipt. Further partial deliveries get new receipts.
 $out=['productId'=>$p['id'],'supplierId'=>$p['supplierId'],'sourceCode'=>$p['sourceCode'],'quantity'=>$quantity,'quantityMilli'=>$mill,'unit'=>$unit,'unitCostMinor'=>$cost,'totalMinor'=>intdiv($mill*$cost+500,1000),'currency'=>$currency,'purchasedAt'=>$at,'reference'=>nodenoSupplierText($d['reference']??''),'orderReference'=>nodenoSupplierText($d['orderReference']??''),'note'=>nodenoSupplierText($d['note']??'',2000)];
 return nodenoSupplierSave($ctx,'supplierPurchases',nodenoControlId('buy_'),$out);
}
function nodenoSupplierPriceMinor(string $v):int {
 $v=trim($v);if(!preg_match('/^\d{1,9}(?:[.,]\d{1,2})?$/D',$v))throw new NodenoControlHttpError(422,'supplier_price_invalid');
 $parts=preg_split('/[.,]/',$v);return nodenoSupplierInteger((int)$parts[0]*100+(int)str_pad($parts[1]??'',2,'0'));
}
function nodenoSupplierCurrentList(PDO $db,string $supplierId):?array {
 $id=nodenoControlSetting($db,'supplier_current_list:'.$supplierId,null);
 if(is_string($id))return nodenoControlRead($db,'supplierLists',$id);
 return null;
}
function nodenoSupplierList(array $ctx,array $body,array $seed):array {
 $supplier=array_column($seed['suppliers'],null,'id')[$body['supplierId']??'']??null;
 if(!$supplier)throw new NodenoControlHttpError(422,'supplier_unknown');
 $currency=$body['currency']??'';$unit=$body['unit']??'';$tax=$body['taxBasis']??'';
 if(!in_array($currency,['TRY','USD','EUR','GBP'],true)||!in_array($unit,['adet','set','metre','m2','paket'],true)||!in_array($tax,['vat_included','vat_excluded'],true))throw new NodenoControlHttpError(422,'supplier_unit_currency_invalid');
 $at=nodenoSupplierInteger($body['effectiveAt']??null,946684800,time()+366*86400);$csv=$body['csv']??null;
 if(!is_string($csv)||strlen($csv)>1500000||preg_match('//u',$csv)!==1)throw new NodenoControlHttpError(422,'supplier_csv_invalid');
 $lines=preg_split('/\r?\n/',trim(preg_replace('/^\xEF\xBB\xBF/','',$csv)));if(count($lines)<2||count($lines)>10001)throw new NodenoControlHttpError(422,'supplier_csv_invalid');
 $delimiter=str_contains($lines[0],';')?';':',';$headers=str_getcsv(array_shift($lines),$delimiter,'"','');
 if($headers!==['sourceCode','unitPrice'])throw new NodenoControlHttpError(422,'supplier_csv_headers');
 $previous=[];$current=nodenoSupplierCurrentList($ctx['db'],$supplier['id']);$baseline=$current['id']??null;
 if($current&&$current['data']['currency']===$currency&&$current['data']['unit']===$unit&&$current['data']['taxBasis']===$tax)$previous=array_column($current['data']['rows'],null,'sourceCode');
 $byCode=[];foreach($seed['products']as $p)if($p['supplierId']===$supplier['id'])$byCode[$p['sourceCode']][]=$p['id'];
 $rows=[];$seen=[];
 foreach($lines as $line){if(trim($line)==='')continue;$cells=str_getcsv($line,$delimiter,'"','');if(count($cells)!==2)throw new NodenoControlHttpError(422,'supplier_csv_invalid');$code=nodenoSupplierText($cells[0],200);if($code===''||isset($seen[$code])||preg_match('/^[=+@\-]/',$code))throw new NodenoControlHttpError(422,'supplier_csv_duplicate_or_formula');$seen[$code]=true;$minor=nodenoSupplierPriceMinor($cells[1]);$old=$previous[$code]['unitPriceMinor']??null;$ids=$byCode[$code]??[];$rows[]=['sourceCode'=>$code,'productIds'=>$ids,'unitPriceMinor'=>$minor,'previousMinor'=>$old,'deltaMinor'=>$old===null?null:$minor-$old,'status'=>count($ids)>1?'ambiguous':(!$ids?'unmapped':($old===null?'new':($minor===$old?'unchanged':'changed')))];}
 if(!$rows)throw new NodenoControlHttpError(422,'supplier_csv_invalid');
 $missing=array_values(array_diff(array_keys($previous),array_keys($seen)));
 return nodenoSupplierSave($ctx,'supplierLists',nodenoControlId('list_'),['supplierId'=>$supplier['id'],'currency'=>$currency,'unit'=>$unit,'taxBasis'=>$tax,'effectiveAt'=>$at,'receivedAt'=>time(),'sourceSha256'=>hash('sha256',$csv),'sourceCsv'=>$csv,'baselineId'=>$baseline,'rows'=>$rows,'missingCodes'=>$missing,'status'=>'draft']);
}
function nodenoSupplierApprove(array $ctx,array $body):array {
 $id=nodenoSupplierText($body['id']??'',100);$row=nodenoControlRead($ctx['db'],'supplierLists',$id);
 if(!$row||!is_int($body['version']??null)||$row['version']!==$body['version']||$row['data']['status']!=='draft')throw new NodenoControlHttpError(409,'version_conflict');
 $current=nodenoSupplierCurrentList($ctx['db'],$row['data']['supplierId']);
 if(($current['id']??null)!==$row['data']['baselineId'])throw new NodenoControlHttpError(409,'supplier_baseline_changed');
 $data=$row['data'];$data['status']='approved';$data['approvedAt']=time();$result=nodenoSupplierSave($ctx,'supplierLists',$id,$data,$row['version']+1);nodenoControlSetSetting($ctx['db'],'supplier_current_list:'.$data['supplierId'],$id);return ['approved'=>true,'data'=>$result];
}
function nodenoSupplierCommand(array $ctx,string $action,string $method,array $body,array $seed):array {
 nodenoControlRequire($ctx,$method==='GET'?'catalog.read':'catalog.write',$method!=='GET');
 if($method==='GET'&&$action==='overview')return nodenoSupplierOverview($ctx,$seed);
 if($method!=='POST'||!in_array($action,['purchases','lists','approve','mappings','watch-settings','watch-ack'],true))throw new NodenoControlHttpError(405,'method_not_allowed');
 $key=$body['idempotencyKey']??null;if(!is_string($key))throw new NodenoControlHttpError(422,'idempotency_key_required');
 return nodenoControlCommand($ctx,$key,[$action,$body],static function()use($ctx,$action,$body,$seed){$effective=nodenoSupplierEffectiveSeed($ctx['db'],$seed);return match($action){'purchases'=>nodenoSupplierPurchase($ctx,$body,$effective),'lists'=>nodenoSupplierList($ctx,$body,$effective),'approve'=>nodenoSupplierApprove($ctx,$body),'mappings'=>nodenoSupplierMapping($ctx,$body,$seed),default=>nodenoPaintWatchCommand($ctx,$action,$body)};});
}
