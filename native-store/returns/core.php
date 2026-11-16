<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/returns/core.php
 * Açıklama   : Sipariş snapshot’ına bağlı iade, birim tahsisi ve değişmez mali kayıt kurallarını uygular.
 */
declare(strict_types=1);

function sgReturnError(int $status,string $code):never{throw new NodenoControlHttpError($status,$code);}
function sgReturnJson(array $value):string{return json_encode($value,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);}
function sgReturnSchema(PDO $db):void{nodenoPaymentSchema($db);$db->exec((string)file_get_contents(__DIR__.'/sg-returns-001.sql'));}
function sgReturnText(mixed $v,int $max=1500):string{if(!is_string($v)||strlen($v)>$max||!preg_match('//u',$v)||preg_match('/[<>\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u',$v))sgReturnError(422,'return_text_invalid');return trim($v);}
function sgReturnInt(mixed $v,int $min=0,int $max=99999999999):int{if(!is_int($v)||$v<$min||$v>$max)sgReturnError(422,'return_number_invalid');return $v;}
function sgReturnCase(PDO $db,string $code):array{$q=$db->prepare('SELECT * FROM sg_return_cases WHERE code=?');$q->execute([$code]);$row=$q->fetch();if(!$row)sgReturnError(404,'return_not_found');return $row;}
function sgReturnEvent(PDO $db,string $code,string $kind,string $actor,array $data,int $now):void{$db->prepare('INSERT INTO sg_return_events(case_code,kind,actor,details_json,created_at)VALUES(?,?,?,?,?)')->execute([$code,$kind,$actor,sgReturnJson($data),$now]);}
function sgReturnOrderLines(array $order):array{
 $snapshot=json_decode($order['snapshot_json'],true,64,JSON_THROW_ON_ERROR);$lines=[];$gross=$net=$vat=0;
 foreach($snapshot['lines']??[]as $i=>$line){
  $quantity=sgReturnInt($line['quantity']??null,1,999);$lineNet=sgReturnInt($line['netMinor']??null);$lineVat=sgReturnInt($line['vatMinor']??null);$lineGross=sgReturnInt($line['totalMinor']??null,1);
  if($lineNet+$lineVat!==$lineGross)sgReturnError(409,'order_tax_snapshot_inconsistent');
  $key=substr(hash('sha256',sgReturnJson([$order['id'],$i,$line['id']??null,$line['options']??[]])),0,32);
  $lines[$key]=['key'=>$key,'quantity'=>$quantity,'netMinor'=>$lineNet,'vatMinor'=>$lineVat,'totalMinor'=>$lineGross,'snapshot'=>$line];$net+=$lineNet;$vat+=$lineVat;$gross+=$lineGross;
 }
 if(!$lines||$gross>(int)$order['total_minor']||($snapshot['netMinor']??null)!==$net||($snapshot['vatMinor']??null)!==$vat)sgReturnError(409,'order_snapshot_inconsistent');
 // A paid shipping charge needs its own historical tax allocation; never infer a current rate.
 if($gross!==(int)$order['total_minor'])sgReturnError(409,'shipping_tax_snapshot_review_required');
 return $lines;
}
function sgReturnUnitAllocation(int $amount,int $quantity,array $units):int{$sum=0;foreach($units as $i){sgReturnInt($i,0,$quantity-1);$sum+=intdiv($amount*($i+1),$quantity)-intdiv($amount*$i,$quantity);}return $sum;}
function sgReturnPost(PDO $db,string $event,?string $case,string $order,string $currency,string $kind,array $entries,string $reference,int $now):void{
 $debit=$credit=0;$valid=[];
 foreach($entries as $entry){$d=sgReturnInt($entry['debit']??0);$c=sgReturnInt($entry['credit']??0);if(($d>0)==($c>0))sgReturnError(500,'journal_entry_invalid');if(!preg_match('/^[a-z_]{3,50}$/D',$entry['account']??''))sgReturnError(500,'journal_account_invalid');$debit+=$d;$credit+=$c;$valid[]=['account'=>$entry['account'],'debit'=>$d,'credit'=>$c];}
 if($debit!==$credit||$debit===0)sgReturnError(500,'journal_not_balanced');
 $json=sgReturnJson($valid);$q=$db->prepare('SELECT * FROM sg_return_journal WHERE event_key=?');$q->execute([$event]);if($old=$q->fetch()){if($old['entries_json']!==$json||$old['currency']!==$currency||$old['order_id']!==$order||$old['kind']!==$kind||$old['reference']!==$reference)sgReturnError(409,'journal_replay_changed');return;}
 $db->prepare('INSERT INTO sg_return_journal VALUES(?,?,?,?,?,?,?,?)')->execute([$event,$case,$order,$currency,$kind,$json,$reference,$now]);
}
function sgReturnPlan(PDO $db,array $order,array $requested):array{
  $all=sgReturnOrderLines($order);$allocated=[];$gross=$net=$vat=0;
  foreach($requested as $key=>$quantity){
   if(!is_string($key)||!isset($all[$key]))sgReturnError(422,'return_line_unknown');$quantity=sgReturnInt($quantity,1,999);$line=$all[$key];$used=[];
   $q=$db->prepare("SELECT l.units_json FROM sg_return_lines l JOIN sg_return_cases c ON c.code=l.case_code WHERE c.order_id=?AND l.line_key=?AND c.status NOT IN('rejected','cancelled')");$q->execute([$order['id'],$key]);foreach($q->fetchAll()as $r)$used=[...$used,...json_decode($r['units_json'],true)];
   $units=[];for($i=0;$i<$line['quantity']&&count($units)<$quantity;$i++)if(!in_array($i,$used,true))$units[]=$i;
   if(count($units)!==$quantity)sgReturnError(409,'return_quantity_exceeded');
   $n=sgReturnUnitAllocation($line['netMinor'],$line['quantity'],$units);$v=sgReturnUnitAllocation($line['vatMinor'],$line['quantity'],$units);$g=$n+$v;$net+=$n;$vat+=$v;$gross+=$g;$allocated[$key]=['quantity'=>$quantity,'units'=>$units,'net'=>$n,'vat'=>$v,'gross'=>$g,'snapshot'=>$line['snapshot']];
  }
 return ['lines'=>$allocated,'grossMinor'=>$gross,'netMinor'=>$net,'vatMinor'=>$vat,'quoteHash'=>hash('sha256',sgReturnJson([$order['id'],$allocated]))];
}
function sgReturnCreate(PDO $db,string $root,array $order,string $actor,array $body,array $policy,int $now):array{
 if(array_diff(array_keys($body),['key','reason','note','locale','lines','sealOpened','packingAcknowledged','quoteHash']))sgReturnError(422,'return_request_invalid');
 if(!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$body['key']??'')||!in_array($body['reason']??'',['withdrawal','defective','wrong_item','missing_parts','shipping_damage'],true)||!is_bool($body['sealOpened']??null)||(isset($body['packingAcknowledged'])&&!is_bool($body['packingAcknowledged'])))sgReturnError(422,'return_request_invalid');
 if(!is_array($body['lines']??null)||!$body['lines']||count($body['lines'])>30)sgReturnError(422,'return_lines_invalid');
 $note=sgReturnText($body['note']??'');$locale=in_array($body['locale']??'',['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'],true)?$body['locale']:'tr';$requested=$body['lines'];ksort($requested);$body['lines']=$requested;
 $command=hash('sha256',$actor.':'.$body['key']);$hash=hash('sha256',sgReturnJson([$order['id'],$body]));
 return nodenoControlTransaction($db,static function()use($db,$root,$order,$actor,$body,$policy,$now,$note,$locale,$requested,$command,$hash):array{
  $q=$db->prepare('SELECT * FROM sg_return_commands WHERE key_hash=?');$q->execute([$command]);if($old=$q->fetch()){if(!hash_equals($old['request_hash'],$hash))sgReturnError(409,'return_request_changed');return json_decode($old['response_json'],true);}
  $fresh=nodenoPaymentOrder($db,$order['id']);if(!$fresh||$fresh['paid_at']===null||!in_array($fresh['status'],['paid','partially_refunded','refunded'],true))sgReturnError(409,'paid_order_required');
  $plan=sgReturnPlan($db,$fresh,$requested);$allocated=$plan['lines'];$gross=$plan['grossMinor'];$net=$plan['netMinor'];$vat=$plan['vatMinor'];
  if(isset($body['quoteHash'])&&(!is_string($body['quoteHash'])||!hash_equals($plan['quoteHash'],$body['quoteHash'])))sgReturnError(409,'return_preview_changed');
  $flags=[];if($body['sealOpened'])$flags[]='seal_opened';if(empty($policy['approved']))$flags[]='policy_review';if(empty($policy['deliveryConfirmedAt']))$flags[]='delivery_date_unknown';
  $code='SGR-'.gmdate('ymd',$now).'-'.strtoupper(bin2hex(random_bytes(6)));
  $db->prepare('INSERT INTO sg_return_cases(code,order_id,actor_hash,reason,note_envelope,locale,currency,gross_minor,net_minor,vat_minor,policy_json,review_flags_json,requested_at,updated_at)VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)')->execute([$code,$fresh['id'],$actor,$body['reason'],nodenoControlEncrypt($root,$note,'return:'.$code),$locale,$fresh['currency'],$gross,$net,$vat,sgReturnJson($policy),sgReturnJson($flags),$now,$now]);
  foreach($allocated as $key=>$line)$db->prepare('INSERT INTO sg_return_lines VALUES(?,?,?,?,?,?,?,?)')->execute([$code,$key,$line['quantity'],sgReturnJson($line['units']),sgReturnJson($line['snapshot']),$line['gross'],$line['net'],$line['vat']]);
  sgReturnEvent($db,$code,'requested',$actor,['reason'=>$body['reason'],'packingAcknowledged'=>$body['packingAcknowledged']??false,'reviewFlags'=>$flags],$now);$result=['code'=>$code,'status'=>'requested','version'=>1];$db->prepare('INSERT INTO sg_return_commands VALUES(?,?,?,?)')->execute([$command,$hash,sgReturnJson($result),$now]);return $result;
 });
}
function sgReturnApprove(PDO $db,array $case,string $actor,array $body,int $now):void{
 if($case['status']!=='received')sgReturnError(409,'return_receipt_required');$qc=json_decode($case['qc_json'],true);if(empty($qc['inspectionComplete']))sgReturnError(409,'return_inspection_required');
 $order=nodenoPaymentOrder($db,$case['order_id']);$q=$db->prepare("SELECT COALESCE(SUM(c.gross_minor),0)FROM sg_return_cases c LEFT JOIN sg_return_jobs j ON j.case_code=c.code AND j.kind='refund' LEFT JOIN payment_refund_items r ON r.id=j.provider_ref WHERE c.order_id=?AND c.refund_state IN('queued','blocked','pending')AND r.id IS NULL");$q->execute([$order['id']]);$held=(int)$q->fetchColumn();
 if((int)$case['gross_minor']+$held+(int)$order['refunded_minor']+(int)$order['refund_pending_minor']>(int)$order['total_minor'])sgReturnError(409,'return_refund_reconciliation_required');
 $entries=[];if($case['net_minor']>0)$entries[]=['account'=>'sales_returns','debit'=>(int)$case['net_minor']];if($case['vat_minor']>0)$entries[]=['account'=>'vat_pending_correction','debit'=>(int)$case['vat_minor']];$entries[]=['account'=>'refunds_payable','credit'=>(int)$case['gross_minor']];
 sgReturnPost($db,'return-accept-'.$case['code'],$case['code'],$order['id'],$case['currency'],'sales_return',$entries,'order-snapshot',$now);
 foreach(['refund','fiscal']as $kind)$db->prepare('INSERT INTO sg_return_jobs(id,case_code,kind,status,amount_minor,currency,request_json,next_at,created_at,updated_at)VALUES(?,?,?,?,?,?,?,?,?,?)')->execute(['sgr_'.$kind.'_'.hash('sha256',$case['code']),$case['code'],$kind,'queued',$case['gross_minor'],$case['currency'],sgReturnJson(['orderId'=>$order['id'],'caseCode'=>$case['code'],'grossMinor'=>(int)$case['gross_minor'],'netMinor'=>(int)$case['net_minor'],'vatMinor'=>(int)$case['vat_minor']]),$now,$now,$now]);
 $db->prepare("UPDATE sg_return_cases SET status='approved',refund_state='queued',fiscal_state='review' WHERE code=?")->execute([$case['code']]);
}
function sgReturnCommand(PDO $db,string $code,string $actor,array $body,int $now):array{
 if(!is_int($body['version']??null)||!is_string($body['action']??null))sgReturnError(422,'return_command_invalid');
 return nodenoControlTransaction($db,static function()use($db,$code,$actor,$body,$now):array{
  $c=sgReturnCase($db,$code);if((int)$c['version']!==$body['version'])sgReturnError(409,'version_conflict');$action=$body['action'];
  if($action==='shipping'){
   if(!in_array($c['status'],['requested','awaiting_dispatch'],true))sgReturnError(409,'return_transition_invalid');$carrier=sgReturnText($body['carrier']??'',120);$handoff=sgReturnText($body['handoffCode']??'',100);$ref=sgReturnText($body['evidenceRef']??'',200);$expires=sgReturnInt($body['expiresAt']??null,$now+60,$now+90*86400);if($carrier===''||$handoff===''||$ref==='')sgReturnError(422,'real_carrier_code_required');
   $db->prepare("UPDATE sg_return_cases SET status='awaiting_dispatch',shipping_json=?WHERE code=?")->execute([sgReturnJson(['carrier'=>$carrier,'handoffCode'=>$handoff,'expiresAt'=>$expires,'evidenceRef'=>$ref,'customerPacks'=>true,'customerHandsOver'=>true]),$code]);
  }elseif($action==='dispatch'){
   if($c['status']!=='awaiting_dispatch')sgReturnError(409,'return_transition_invalid');$s=json_decode($c['shipping_json'],true);$tracking=sgReturnText($body['trackingNumber']??'',100);if($tracking===''||empty($s['handoffCode']))sgReturnError(422,'return_tracking_required');$s['trackingNumber']=$tracking;$s['handedOverAt']=$now;$db->prepare("UPDATE sg_return_cases SET status='in_transit',shipping_json=?WHERE code=?")->execute([sgReturnJson($s),$code]);
  }elseif($action==='receive'){
   if(!in_array($c['status'],['in_transit','awaiting_dispatch'],true))sgReturnError(409,'return_transition_invalid');$q=['receivedAt'=>$now,'disposition'=>'quarantine','inspectionComplete'=>false,'stockIncreased'=>false];$db->prepare("UPDATE sg_return_cases SET status='received',qc_json=?WHERE code=?")->execute([sgReturnJson($q),$code]);
  }elseif($action==='inspect'){
   if($c['status']!=='received'||!in_array($body['disposition']??'',['quarantine','return_to_supplier','sealed_resalable','damaged'],true)||($body['inspectionComplete']??false)!==true)sgReturnError(422,'inspection_required');if($body['disposition']==='sealed_resalable'&&in_array('seal_opened',json_decode($c['review_flags_json'],true),true))sgReturnError(409,'opened_seal_cannot_be_resalable');$q=json_decode($c['qc_json'],true);$q+=['stockIncreased'=>false];$q['inspectionComplete']=true;$q['disposition']=$body['disposition'];$q['evidenceRef']=sgReturnText($body['evidenceRef']??'',200);if($q['evidenceRef']==='')sgReturnError(422,'inspection_evidence_required');$db->prepare('UPDATE sg_return_cases SET qc_json=?WHERE code=?')->execute([sgReturnJson($q),$code]);
  }elseif($action==='approve')sgReturnApprove($db,$c,$actor,$body,$now);
  elseif(in_array($action,['reject','cancel'],true)){
   if(in_array($c['status'],['approved','closed','rejected','cancelled'],true))sgReturnError(409,'return_transition_invalid');$reason=sgReturnText($body['decisionReason']??'',1000);if($reason==='')sgReturnError(422,'decision_reason_required');$db->prepare('UPDATE sg_return_cases SET status=?WHERE code=?')->execute([$action==='reject'?'rejected':'cancelled',$code]);
  }else sgReturnError(422,'return_action_unknown');
  $db->prepare('UPDATE sg_return_cases SET version=version+1,updated_at=?WHERE code=?')->execute([$now,$code]);sgReturnEvent($db,$code,$action,$actor,['decisionReason'=>$body['decisionReason']??null],$now);return sgReturnCase($db,$code);
 });
}
function sgReturnFiscalConfirm(PDO $db,string $code,string $actor,array $body,int $now):array{
 return nodenoControlTransaction($db,static function()use($db,$code,$actor,$body,$now):array{
  $c=sgReturnCase($db,$code);if(!in_array($c['status'],['approved','closed'],true))sgReturnError(409,'return_approval_required');
  $op=$body['operation']??'';if(!in_array($op,['cancellation','return_invoice','credit_document'],true))sgReturnError(422,'fiscal_operation_required');$original=sgReturnText($body['originalRef']??'',150);$corrective=sgReturnText($body['correctiveRef']??'',150);$evidence=sgReturnText($body['evidenceRef']??'',200);if($original===''||$corrective===''||$evidence==='')sgReturnError(422,'external_fiscal_evidence_required');
  $order=nodenoPaymentOrder($db,$c['order_id']);if($op==='cancellation'&&(int)$c['gross_minor']!==(int)$order['total_minor'])sgReturnError(409,'partial_return_cannot_cancel_invoice');
  $q=$db->prepare('SELECT * FROM sg_return_fiscal WHERE case_code=?');$q->execute([$code]);if($old=$q->fetch()){if($old['operation']!==$op||$old['original_ref']!==$original||$old['corrective_ref']!==$corrective||$old['evidence_ref']!==$evidence)sgReturnError(409,'fiscal_confirmation_changed');return $old;}
  $q=$db->prepare('SELECT case_code FROM sg_return_fiscal WHERE corrective_ref=?');$q->execute([$corrective]);if($q->fetch())sgReturnError(409,'fiscal_reference_already_linked');
  $db->prepare('INSERT INTO sg_return_fiscal(case_code,operation,original_ref,corrective_ref,evidence_ref,actor,confirmed_at)VALUES(?,?,?,?,?,?,?)')->execute([$code,$op,$original,$corrective,$evidence,$actor,$now]);
  if($c['vat_minor']>0)sgReturnPost($db,'return-tax-'.$code,$code,$c['order_id'],$c['currency'],'tax_correction',[['account'=>'vat_payable','debit'=>(int)$c['vat_minor']],['account'=>'vat_pending_correction','credit'=>(int)$c['vat_minor']]],$corrective,$now);
  $db->prepare("UPDATE sg_return_cases SET fiscal_state='confirmed',status=CASE WHEN refund_state='succeeded' THEN 'closed' ELSE status END,version=version+1,updated_at=?WHERE code=?")->execute([$now,$code]);$db->prepare("UPDATE sg_return_jobs SET status='succeeded',updated_at=?WHERE case_code=?AND kind='fiscal'")->execute([$now,$code]);sgReturnEvent($db,$code,'fiscal_confirmed',$actor,['operation'=>$op,'origin'=>'manual_external_confirmation'],$now);return ['confirmed'=>true,'origin'=>'manual_external_confirmation'];
 });
}
function sgReturnExpense(PDO $db,array $order,?array $case,string $actor,array $body,int $now):void{
 $kind=$body['kind']??'';if(!in_array($kind,['payment_fee','outbound_shipping','return_shipping','packaging','cost_recovery'],true))sgReturnError(422,'expense_kind_invalid');$amount=sgReturnInt($body['amountMinor']??null,1);$ref=sgReturnText($body['evidenceRef']??'',200);$key=sgReturnText($body['key']??'',100);if($ref===''||!preg_match('/^[A-Za-z0-9_-]{16,100}$/D',$key))sgReturnError(422,'expense_evidence_required');
 if($kind==='cost_recovery'&&(!$case||(json_decode($case['qc_json'],true)['disposition']??'')!=='sealed_resalable'))sgReturnError(409,'cost_recovery_not_confirmed');
 nodenoControlTransaction($db,static function()use($db,$order,$case,$actor,$body,$now,$kind,$amount,$ref,$key):void{
  $command=hash('sha256','return-expense:'.$actor.':'.$key);$requestHash=hash('sha256',sgReturnJson([$order['id'],$case['code']??null,$kind,$amount,$ref]));$q=$db->prepare('SELECT request_hash FROM sg_return_commands WHERE key_hash=?');$q->execute([$command]);if($previous=$q->fetch()){if(!hash_equals($previous['request_hash'],$requestHash))sgReturnError(409,'expense_request_changed');return;}
  $entries=$kind==='cost_recovery'?[['account'=>'inventory_recovery','debit'=>$amount],['account'=>'cost_of_sales','credit'=>$amount]]:[['account'=>$kind.'_expense','debit'=>$amount],['account'=>'cash','credit'=>$amount]];
  sgReturnPost($db,'expense-'.hash('sha256',$order['id'].':'.$kind.':'.$ref),$case['code']??null,$order['id'],$order['currency'],$kind,$entries,$ref,$now);$db->prepare('INSERT INTO sg_return_commands VALUES(?,?,?,?)')->execute([$command,$requestHash,sgReturnJson(['recorded'=>true]),$now]);
 });
}
