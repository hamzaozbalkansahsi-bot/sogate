import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import path from 'node:path';

const php=process.env.PHP_BINARY||path.resolve('artifacts/runtime-php/php.exe');
const module=path.resolve('hosting/payment-core.php');
function run(code,input={}){
 assert.ok(existsSync(module),'Server payment module must implement the quote and verification contract');
 const p=spawnSync(php,['-r',`require $argv[1];$in=json_decode(stream_get_contents(STDIN),true,64,JSON_THROW_ON_ERROR);${code}`,module],{input:JSON.stringify(input),encoding:'utf8'});
 assert.equal(p.status,0,p.stderr||p.stdout);return JSON.parse(p.stdout);
}
const furniture={id:'f1',code:'REAL-F1',name:{tr:'Dolap'},currency:'TRY',salePriceMinor:10001};
const door={id:'d1',code:'REAL-D1',name:{tr:'Kapı'},productType:'door',currency:'TRY',salePriceMinor:20003,door:{charges:{},glassAvailable:false}};
const front={id:'c1',code:'REAL-C1',name:{tr:'Kapak'},productType:'cabinet-front',currency:'TRY',salePriceMinor:12345,front:{minimumApplies:true}};
const catalog={products:[furniture,door,front],meta:{controlRevision:7}};
const quote=(items,extra={})=>run(`try{echo json_encode(nodenoPaymentQuote($in['catalog'],$in['items'],$in['country']??'TR'));}catch(InvalidArgumentException $e){echo json_encode(['error'=>$e->getMessage()]);}`,{catalog,items,...extra});
test('net furniture gains 10% VAT and domestic shipping is included',()=>{
 const q=quote([{id:'f1',quantity:3}]);
 assert.equal(q.netMinor,30003);assert.equal(q.vatMinor,3000);assert.equal(q.totalMinor,33003);
 assert.equal(q.lines[0].vatRate,10);assert.equal(q.currency,'TRY');
 assert.deepEqual(q.freight,{kind:'included',includedInCharge:true,feeMinor:0});
 assert.match(q.revision,/^[a-f0-9]{64}$/);
});
test('door MOQ and 20% VAT use the verified server price',()=>{
 assert.equal(quote([{id:'d1',quantity:4}]).error,'payment_minimum_not_reached');
 const q=quote([{id:'d1',quantity:5}]);assert.equal(q.netMinor,100015);assert.equal(q.vatMinor,20003);assert.equal(q.totalMinor,120018);
 assert.equal(q.lines[0].vatRate,20);
});
test('measured fronts round aggregate area once before 20% VAT',()=>{
 const q=quote([{id:'c1',quantity:5,options:{widthMm:1001,heightMm:1000,application:'solid'}}]);
 assert.equal(q.netMinor,61787);assert.equal(q.vatMinor,12357);assert.equal(q.totalMinor,74144);
 assert.equal(q.lines[0].quantity,5);
});
test('unpriced, unsupported, hidden, quote-only, client-price and foreign delivery lines cannot be charged',()=>{
 assert.ok(quote([{id:'f1',quantity:1,unitPriceMinor:1}]).error);
 assert.equal(quote([{id:'f1',quantity:1}],{country:'DE'}).error,'payment_country_not_supported');
 for(const change of [{salePriceMinor:null},{hidden:true},{currency:'USD'},{productType:'door-profile'}]){
  const c={products:[{...furniture,...change}],meta:{}};
  assert.ok(run(`try{echo json_encode(nodenoPaymentQuote($in['catalog'],[['id'=>'f1','quantity'=>1]],'TR'));}catch(InvalidArgumentException $e){echo json_encode(['error'=>$e->getMessage()]);}`,{catalog:c}).error);
 }
 assert.ok(quote([{id:'d1',quantity:5,options:{height:250}}]).error);
});
test('quote revision changes when a published product amount changes',()=>{
 const a=quote([{id:'f1',quantity:1}]);
 const b=run(`$in['catalog']['products'][0]['salePriceMinor']++;echo json_encode(nodenoPaymentQuote($in['catalog'],[['id'=>'f1','quantity'=>1]],'TR'));`,{catalog});
 assert.notEqual(a.revision,b.revision);
});
test('stock-controlled products stay closed until reservations exist and multiline delivery addresses are accepted',()=>{
 const c={products:[{...furniture,stockKnown:true,stockQuantity:10}]};
 assert.ok(run(`try{echo json_encode(nodenoPaymentQuote($in, [['id'=>'f1','quantity'=>1]],'TR'));}catch(InvalidArgumentException $e){echo json_encode(['error'=>$e->getMessage()]);}`,c).error);
 const contact={name:'Guest Buyer',email:'buyer@example.test',phone:'+905551112233',sameBilling:true,delivery:{name:'Guest Buyer',country:'TR',city:'İzmir',district:'',postalCode:'',line1:'Example Street\nApartment 12',line2:''}};
 assert.equal(run(`echo json_encode(nodenoPaymentContact($in));`,contact).delivery.line1,contact.delivery.line1);
});
test('contact validation keeps personal data out of quote and rejects foreign or malformed addresses',()=>{
 const contact={name:'Guest Buyer',email:'buyer@example.org',phone:'+905551112233',delivery:{name:'Guest Buyer',country:'TR',city:'İzmir',district:'Buca',postalCode:'35000',line1:'Example street 12',line2:''},sameBilling:true};
 const r=run(`$out=[];foreach([$in,$in+['ignored'=>'x'],array_replace($in,['email'=>'not-email']),array_replace($in,['delivery'=>array_replace($in['delivery'],['country'=>'DE'])])]as $value){try{$out[]=nodenoPaymentContact($value);}catch(InvalidArgumentException $e){$out[]=['error'=>$e->getMessage()];}}echo json_encode($out);`,contact);
 assert.equal(r[0].billing.country,'TR');assert.equal(r[0].email,contact.email);
 for(const value of r.slice(1))assert.ok(value.error);
});
test('raw signed bodies allow rotated v1 signatures but reject stale, future, altered and duplicate-timestamp messages',()=>{
 const r=run(`$raw='{"id":"evt_fixture"}';$secret='whsec_isolated_fixture';$now=1800000000;$sig=hash_hmac('sha256',$now.'.'.$raw,$secret);$check=static function($r,$h)use($secret,$now){try{return nodenoPaymentVerifySignature($r,$h,$secret,$now);}catch(InvalidArgumentException $e){return false;}};echo json_encode([$check($raw,'t='.$now.',v1=bad,v1='.$sig),$check($raw.' ','t='.$now.',v1='.$sig),$check($raw,'t='.($now-301).',v1='.$sig),$check($raw,'t='.($now+301).',v1='.$sig),$check($raw,'t='.$now.',t='.$now.',v1='.$sig)]);`);
 assert.deepEqual(r,[true,false,false,false,false]);
});
test('paid events must match the saved account, mode, session, reference, amount and currency',()=>{
 const result=run(`$o=['id'=>'order_abc','stripe_session_id'=>'cs_test_fixture','stripe_account_id'=>'acct_fixture','live'=>0,'total_minor'=>11000,'currency'=>'TRY'];$event=['id'=>'evt_fixture','type'=>'checkout.session.completed','livemode'=>false,'account'=>'acct_fixture','data'=>['object'=>['id'=>'cs_test_fixture','client_reference_id'=>'order_abc','metadata'=>['nodeno_order_id'=>'order_abc'],'payment_status'=>'paid','amount_total'=>11000,'currency'=>'try','payment_intent'=>'pi_fixture']]];$out=[nodenoPaymentEvent($o,$event)];foreach(['amount','currency','mode','account','session','reference','unpaid']as $case){$e=$event;if($case==='amount')$e['data']['object']['amount_total']=1;if($case==='currency')$e['data']['object']['currency']='usd';if($case==='mode')$e['livemode']=true;if($case==='account')$e['account']='acct_other';if($case==='session')$e['data']['object']['id']='cs_other';if($case==='reference')$e['data']['object']['client_reference_id']='order_other';if($case==='unpaid')$e['data']['object']['payment_status']='unpaid';$out[]=nodenoPaymentEvent($o,$e);}echo json_encode($out);`);
 assert.equal(result[0].status,'paid');assert.equal(result[0].paymentIntent,'pi_fixture');
 for(const r of result.slice(1))assert.notEqual(r.status,'paid');
});
