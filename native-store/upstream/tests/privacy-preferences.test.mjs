import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import {createShoppingExperience} from '../web/shopping-ui.js';
import {createInsightsClient} from '../web/store-insights.js';

let privacy={};
try{privacy=await import('../web/privacy-preferences.js');}catch(error){if(error.code!=='ERR_MODULE_NOT_FOUND')throw error;}
const memory=values=>{const map=new Map(Object.entries(values||{}));return{getItem:key=>map.get(key)??null,setItem:(key,value)=>map.set(key,String(value)),removeItem:key=>map.delete(key)};};
const now=1800000000000;
test('expanded analytics asks again after an old affirmative choice but preserves a refusal',()=>{
 const record={schema:2,granted:true,decidedAt:now-1000,expiresAt:now-1000+90*86400000};const storage=memory({'nodeno.analytics.consent.v1':JSON.stringify(record),'nodeno.cart.v1':'keep'});
 assert.equal(privacy.readPrivacyPreference(storage,now),null);assert.equal(storage.getItem('nodeno.cart.v1'),'keep');storage.setItem('nodeno.analytics.consent.v1',JSON.stringify({...record,granted:false}));assert.equal(privacy.readPrivacyPreference(storage,now),false);
});

test('expired or legacy affirmative consent never permits optional history and leaves requested cart intact',()=>{
 assert.equal(typeof privacy.optionalPersonalizationAllowed,'function');
 const storage=memory({'nodeno.analytics.consent.v1':'true','nodeno.recent.v1':'["2395"]','nodeno.searches.v1':'["desk"]','nodeno.cart.v1':'[{"id":"2395","quantity":1}]'});
 assert.equal(privacy.optionalPersonalizationAllowed(storage,now),false);
 assert.equal(privacy.readPrivacyPreference(storage,now),null);
 assert.equal(storage.getItem('nodeno.recent.v1'),null);assert.equal(storage.getItem('nodeno.searches.v1'),null);assert.ok(storage.getItem('nodeno.cart.v1'));
 privacy.savePrivacyPreference(true,{storage,now,eventTarget:null});assert.equal(privacy.optionalPersonalizationAllowed(storage,now+7775999999),true);
 assert.equal(privacy.optionalPersonalizationAllowed(storage,now+7776000000),false);
 assert.equal(privacy.readPrivacyPreference(storage,now+7776000000),null);
});

test('withdrawal clears optional history and tells active views even if the server is temporarily unavailable',async()=>{
 assert.equal(typeof privacy.setOptionalPreference,'function');
 const storage=memory(),target=new EventTarget(),changes=[];target.addEventListener('nodeno:privacy-change',e=>changes.push(e.detail));
 privacy.savePrivacyPreference(true,{storage,now,eventTarget:target});storage.setItem('nodeno.recent.v1','["2395"]');storage.setItem('nodeno.searches.v1','["desk"]');
 await assert.rejects(privacy.setOptionalPreference(false,{storage,now:now+1000,eventTarget:target,request:async()=>{throw new Error('offline');}}),/offline/);
 assert.equal(privacy.optionalPersonalizationAllowed(storage,now+1001),false);assert.equal(storage.getItem('nodeno.recent.v1'),null);assert.equal(storage.getItem('nodeno.searches.v1'),null);assert.equal(changes.at(-1).granted,false);
});

test('an unacknowledged or late affirmative reply cannot override a newer refusal',async()=>{
 assert.equal(typeof privacy.setOptionalPreference,'function');
 const storage=memory();let finish;
 const granting=privacy.setOptionalPreference(true,{storage,now,eventTarget:null,request:()=>new Promise(resolve=>finish=resolve)});
 await privacy.setOptionalPreference(false,{storage,now:now+1,eventTarget:null,request:async()=>({granted:false})});finish({granted:true});await granting;
 assert.equal(privacy.optionalPersonalizationAllowed(storage,now+2),false);
 await assert.rejects(privacy.setOptionalPreference(true,{storage,now:now+3,eventTarget:null,request:async()=>({granted:false})}));
 assert.equal(privacy.optionalPersonalizationAllowed(storage,now+4),false);
});

test('an already open telemetry client stops sending when its stored permission expires',async()=>{
 let granted=true,sent=0;
 const client=createInsightsClient({read:()=>granted,write:value=>granted=value,request:async()=>{sent++;return{accepted:true};}});
 assert.equal(await client.event({event:'view'}),true);granted=null;assert.equal(await client.event({event:'view'}),false);assert.equal(sent,1);
});

test('search navigation still works without retaining searches until optional consent exists',()=>{
 const previousStorage=globalThis.localStorage,previousDocument=globalThis.document,storage=memory();globalThis.localStorage=storage;
 const input={value:'wardrobe',setAttribute(){},blur(){}},panel={hidden:false};globalThis.document={querySelector:selector=>selector==='#search'?input:selector==='#search-suggestions'?panel:null};
 let destination='';const ctx={state:()=>({locale:'en',catalog:{products:[]}}),read:(key,fallback)=>JSON.parse(storage.getItem(key)||'null')??fallback,write:(key,value)=>storage.setItem(key,JSON.stringify(value)),href:(page,args)=>page+'?q='+args.q,navigate:value=>destination=value};
 try{
  const experience=createShoppingExperience(ctx);experience.submitSearch();assert.equal(destination,'catalog?q=wardrobe');assert.equal(storage.getItem('nodeno.searches.v1'),null);
  assert.equal(typeof privacy.savePrivacyPreference,'function');privacy.savePrivacyPreference(true,{storage,eventTarget:null});experience.submitSearch();assert.deepEqual(JSON.parse(storage.getItem('nodeno.searches.v1')),['wardrobe']);
  privacy.savePrivacyPreference(false,{storage,eventTarget:null});input.value='table';experience.submitSearch();assert.equal(destination,'catalog?q=table');assert.equal(storage.getItem('nodeno.searches.v1'),null);
 }finally{if(previousStorage===undefined)delete globalThis.localStorage;else globalThis.localStorage=previousStorage;if(previousDocument===undefined)delete globalThis.document;else globalThis.document=previousDocument;}
});

test('recommendations erase expired visitors and the full 90-day-old bucket without needing a new analytics event',async()=>{
 const root=await mkdtemp(path.join(os.tmpdir(),'nodeno-privacy-expiry-'));
 const code=`require 'hosting/control-analytics.php';$db=nodenoControlDatabase($argv[1]);$token=nodenoControlConsent($db,$argv[1],true,null);$old=nodenoControlVisitor($argv[1],$token);$fresh=nodenoControlConsent($db,$argv[1],true,null);$active=nodenoControlVisitor($argv[1],$fresh);$db->prepare('UPDATE control_consents SET expires_at=? WHERE visitor=?')->execute([time()-1,$old]);$insert=$db->prepare('INSERT INTO control_events(visitor,day,event,product_id,locale,device,market) VALUES(?,?,?,?,?,?,?)');$insert->execute([$old,intdiv(time(),86400),'view','a','tr','mobile','']);$insert->execute([$active,intdiv(time(),86400)-91,'view','a','tr','mobile','']);$insert->execute([$active,intdiv(time(),86400)-90,'favorite','a','tr','mobile','']);$insert->execute([$active,intdiv(time(),86400),'cart','b','tr','mobile','']);nodenoControlRecommendations($db,['products'=>[['id'=>'a'],['id'=>'b']]],'');echo json_encode([(int)$db->query('SELECT COUNT(*) FROM control_events')->fetchColumn(),(int)$db->query('SELECT COUNT(*) FROM control_consents')->fetchColumn(),$db->query('SELECT product_id FROM control_events')->fetchColumn()]);`;
 const result=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code,root],{encoding:'utf8'});assert.equal(result.status,0,result.stderr||result.stdout);assert.deepEqual(JSON.parse(result.stdout),[1,1,'b']);
});
