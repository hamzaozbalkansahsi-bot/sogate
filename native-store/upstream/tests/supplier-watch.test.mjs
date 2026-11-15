import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
const php=path.resolve('artifacts/runtime-php/php.exe');
const product=`['id'=>'paint-1','title'=>'Bianca Stella','supplierId'=>'trendyol-942066','sourceCode'=>'TYCB6E5B2372B36C30','sourceUrl'=>'https://www.trendyol.com/bianca/test-p-819338039?merchantId=942066','sourcePriceMinor'=>199900,'salePriceMinor'=>259870,'sourceVariant'=>['productId'=>'819338039','merchantId'=>'942066','itemNumber'=>'1094585601','barcode'=>'HT100010','color'=>'yasemin','selectedSize'=>'1 L'],'priceWatch'=>true]`;
function run(code,root=''){const r=spawnSync(php,['-r',`require 'hosting/control-http.php';${code}`,root],{encoding:'utf8'});assert.equal(r.status,0,r.stderr||r.stdout);return JSON.parse(r.stdout);}
test('source parser binds seller, product, package and variant; rejects redirects and external URLs',()=>{
 const d=run(`$p=${product};$body=file_get_contents('artifacts/bianca-20261112/sample-pinned.html');$a=nodenoPaintWatchParse($body,$p);$p['sourceVariant']['merchantId']='584353';$bad=false;try{nodenoPaintWatchParse($body,$p);}catch(Throwable $e){$bad=true;}echo json_encode([$a,$bad,nodenoPaintWatchUrl('https://www.trendyol.com/bianca/test-p-819338039?merchantId=942066'),nodenoPaintWatchUrl('https://evil.test/x-p-819338039?merchantId=942066'),nodenoPaintWatchUrl('https://www.trendyol.com/x-p-819338039?merchantId=942066&redirect=evil')]);`);
 assert.equal(d[0].priceMinor,199900);assert.deepEqual(d.slice(1),[true,true,false,false]);
});
test('price history alerts once per change; network failures preserve known values and retail prices',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-paint-watch-'));
 const d=run(`$db=nodenoControlDatabase($argv[1]);$p=${product};nodenoPaintWatchObserve($db,$p,['priceMinor'=>199900,'currency'=>'TRY'],null,1000);nodenoPaintWatchObserve($db,$p,['priceMinor'=>219900,'currency'=>'TRY'],null,2000);nodenoPaintWatchObserve($db,$p,['priceMinor'=>219900,'currency'=>'TRY'],null,3000);nodenoPaintWatchObserve($db,$p,null,'source_request_failed',4000);nodenoPaintWatchObserve($db,$p,null,'source_request_failed',5000);echo json_encode([nodenoPaintWatchOverview($db),$p['salePriceMinor']]);`,root);
 assert.equal(d[0].alerts.length,2);assert.equal(d[0].states['paint-1'].lastPriceMinor,219900);assert.equal(d[0].states['paint-1'].lastSuccessAt,3000);assert.equal(d[1],259870);assert.equal(d[0].alerts.find(x=>x.data.kind==='price_changed').data.suggestedSaleMinor,285870);
});
test('canonical source redirects retain product and seller and reject foreign or changed identities',()=>{
 const d=run(`$p=${product};$ok=nodenoPaintWatchRedirect($p['sourceUrl'],'/pd/bianca/test-p-819338039');$bad=[];foreach(['https://evil.test/x-p-819338039','//evil.test/x-p-819338039','/pd/bianca/x-p-819338040','/pd/bianca/x-p-819338039?merchantId=1','/pd/bianca/x-p-819338039?redirect=evil']as $url){try{nodenoPaintWatchRedirect($p['sourceUrl'],$url);$bad[]=false;}catch(Throwable $e){$bad[]=true;}}echo json_encode([$ok,$bad]);`);
 assert.equal(d[0],'https://www.trendyol.com/pd/bianca/test-p-819338039?merchantId=942066');assert.deepEqual(d[1],[true,true,true,true,true]);
});
test('watcher pauses after rate limiting and mapped URLs invalidate evidence',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-paint-limit-'));
 const d=run(`$db=nodenoControlDatabase($argv[1]);$p=${product};$p['sourceWatchIdentity']=nodenoPaintWatchIdentity($p);$count=0;$a=nodenoPaintWatchTick($db,['products'=>[$p]],function()use(&$count){$count++;throw new RuntimeException('source_access_limited');});$b=nodenoPaintWatchTick($db,['products'=>[$p]],function()use(&$count){$count++;return '';});echo json_encode([$a,$b,$count,nodenoPaintWatchOverview($db)]);`,root);
 assert.equal(d[2],1);assert.ok(d[1].pausedUntil);assert.equal(d[3].states['paint-1'].error,'source_access_limited');
});
test('read-only operators cannot acknowledge alerts or disable monitoring',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-paint-rbac-'));
 const d=run(`$db=nodenoControlDatabase($argv[1]);$ctx=['db'=>$db,'root'=>$argv[1],'user'=>['id'=>'reader'],'permissions'=>['catalog.read']];$bad=false;try{nodenoSupplierCommand($ctx,'watch-settings','POST',['enabled'=>false,'idempotencyKey'=>'paint_watch_123456789'],['products'=>[]]);}catch(NodenoControlHttpError $e){$bad=$e->status===403;}echo json_encode($bad);`,root);assert.equal(d,true);
});
