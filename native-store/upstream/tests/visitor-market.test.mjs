import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {countryLocale, visitorMarket, initialLocale} from '../web/visitor-market.js';

test('country and supported language are independent: Turkey stays retail even with English or Arabic',()=>{
 for(const language of ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']){
  assert.equal(visitorMarket('TR').international,false);
  assert.equal(initialLocale({requested:language,stored:'ru',country:'TR'}),language);
 }
 for(const country of ['GB','US'])assert.equal(countryLocale(country),'en');
 for(const country of ['RU','BY'])assert.equal(countryLocale(country),'ru');
 for(const country of ['IQ','SY','SA','AE','EG'])assert.equal(countryLocale(country),'ar');
 for(const [country,locale]of Object.entries({TR:'tr',DE:'de',AZ:'az',KZ:'kk',KG:'ky',TM:'tk',UZ:'uz',IR:'fa'}))assert.equal(countryLocale(country),locale);
 for(const country of [null,'','ZZ','EU','xx','<script>'])assert.deepEqual(visitorMarket(country),{country:null,international:false});
 assert.equal(visitorMarket('DE').international,true);
});
test('explicit language, saved manual choice, country default and unknown fallback keep their precedence',()=>{
 assert.equal(initialLocale({requested:'ar',stored:'tr',country:'DE'}),'ar');
 assert.equal(initialLocale({requested:'invalid',stored:'ru',country:'DE'}),'ru');
 assert.equal(initialLocale({country:'IQ'}),'ar');
 assert.equal(initialLocale({country:'DE'}),'de');
 assert.equal(initialLocale({country:null}),'tr');
 assert.equal(initialLocale({stored:'en',country:'TR'}),'en');
});
test('PHP uses direct peer IP only, handles both address families, and matches locale precedence',()=>{
 const result=spawnSync('artifacts/runtime-php/php.exe',['tests/fixtures/visitor-market.php'],{encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);const rows=JSON.parse(result.stdout);
 for(const row of rows){assert.deepEqual(row.market,visitorMarket(row.country));assert.equal(row.locale,initialLocale(row.input));}
});
