/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-notification-worker.mjs
 * Açıklama   : Bildirim gövdesini, güvenli bağlantıyı ve önbelleksiz service worker davranışını sınar.
 */
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
const code=readFileSync(new URL('../native-store/storefront/notifications-sw.js',import.meta.url),'utf8');
function setup(){const handlers={},shown=[],opened=[];const self={addEventListener:(type,fn)=>{handlers[type]=fn;},registration:{scope:'https://sexogate.com/test/',showNotification:async(title,options)=>{shown.push({title,...options});}},clients:{matchAll:async()=>[],openWindow:async url=>{opened.push(url);}}};vm.runInNewContext(code,{self,URL});return{handlers,shown,opened};}
test('only valid stock event displays a private notification',async()=>{const s=setup();let done;s.handlers.push({data:{json:()=>({tag:'a'.repeat(64),url:'/test/?product=sg_test_product',body:'PRIVATE PRODUCT NAME'})},waitUntil:p=>{done=p;}});await done;assert.equal(s.shown.length,1);assert.equal(s.shown[0].title,'SEXOGATE');assert.ok(!s.shown[0].body.includes('PRIVATE PRODUCT'));assert.equal(s.shown[0].actions[0].title,'İncele');assert.equal(s.shown[0].icon,'https://sexogate.com/test/assets/brand/app/app-icon-192.png');});
test('off-origin, outside-scope and malformed events are ignored',()=>{for(const url of ['https://evil.example/test/?product=sg_item','/yonetim/?product=sg_item','/test/?product=other']){const s=setup();s.handlers.push({data:{json:()=>({tag:'a'.repeat(64),url})},waitUntil:()=>assert.fail('unsafe notification')});assert.equal(s.shown.length,0);}});
test('click opens only the same scoped application',async()=>{const s=setup();let done,closed=false;s.handlers.notificationclick({notification:{data:{url:'https://sexogate.com/test/?product=sg_item'},close:()=>{closed=true;}},waitUntil:p=>{done=p;}});await done;assert.equal(closed,true);assert.deepEqual(s.opened,['https://sexogate.com/test/?product=sg_item']);});
test('worker does not register an HTTP cache or fetch handler',()=>{const s=setup();assert.deepEqual(Object.keys(s.handlers).sort(),['notificationclick','push']);assert.ok(!code.includes('caches.'));});
