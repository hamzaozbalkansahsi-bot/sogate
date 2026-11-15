import test from 'node:test';import assert from 'node:assert/strict';import {spawnSync}from'node:child_process';import path from'node:path';
import {trafficAttribution}from'../web/store-insights.js';
test('attribution retains only a source category and host, never a full URL or search query',()=>{
 assert.deepEqual(trafficAttribution('https://nodenohome.com/','https://www.google.com/search?q=private@example.test'),{source:'search',referrer:'www.google.com'});
 assert.deepEqual(trafficAttribution('https://nodenohome.com/?utm_campaign=private@example.test','https://instagram.com/path?token=secret'),{source:'campaign',referrer:'instagram.com'});
 assert.deepEqual(trafficAttribution('https://nodenohome.com/','https://nodenohome.com/?private=secret'),{source:'direct',referrer:''});
 assert.deepEqual(trafficAttribution('https://nodenohome.com/','https://127.0.0.1/private'),{source:'unknown',referrer:''});
});
test('consented analytics include real country/device/source aggregates and never invent demographics',()=>{
 const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',`require 'hosting/control-analytics.php';$root=sys_get_temp_dir().'/nodeno-report-'.bin2hex(random_bytes(8));$db=nodenoControlDatabase($root);$t=nodenoControlConsent($db,$root,true,null);$c=['products'=>[['id'=>'p1']]];$meta=['locale'=>'tr','device'=>'mobile','market'=>'US','source'=>'search','referrer'=>'www.google.com'];nodenoControlEvent($db,$root,$t,$meta+['event'=>'visit','productId'=>''],$c);nodenoControlEvent($db,$root,$t,$meta+['event'=>'view','productId'=>'p1'],$c);$ctx=['db'=>$db,'root'=>$root,'user'=>['id'=>'fixture'],'permissions'=>['*']];echo json_encode(nodenoControlAnalyticsReport($ctx));`],{encoding:'utf8'});
 assert.equal(r.status,0,r.stderr);const v=JSON.parse(r.stdout);assert.equal(v.summary.visitors,1);assert.equal(v.summary.visitorDays,1);assert.equal(v.countries[0].market,'US');assert.equal(v.sources[0].source,'search');assert.equal(v.demographics.available,false);assert.deepEqual(v.demographics.ageGroups,[]);assert.deepEqual(v.demographics.genders,[]);
});
