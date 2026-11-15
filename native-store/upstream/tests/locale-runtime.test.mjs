import test from 'node:test';
import assert from 'node:assert/strict';
import {localeCopy,localizedValue,registerLocaleDictionary,resetLocaleDictionaries,localizeDataTree,hasLocaleData,ensureLocale,ensureLocaleData} from '../web/locale-runtime.js';
test('native locale views translate nested copy while preserving keys, source and model invariants',()=>{
 resetLocaleDictionaries();registerLocaleDictionary('de',{schema:1,locale:'de',translations:{'Colour':'Farbe','White':'Weiß','A desk':'Ein Schreibtisch'}});
 const source={tr:{color:'Renk',items:['Beyaz']},en:{color:'Colour',items:['White']},ru:{},ar:{}};
 const copy=localeCopy(source);assert.equal(copy.de.color,'Farbe');assert.deepEqual(copy.de.items,['Weiß']);assert.equal(source.en.color,'Colour');
 assert.equal(localizedValue({tr:'Georgia',en:'Georgia',ru:'Georgia',ar:'Georgia'},'de'),'Georgia');
 assert.equal(localizedValue({tr:'Masa',en:'A desk',ru:'Стол',ar:'مكتب'},'de'),'Ein Schreibtisch');
});
test('catalogue localization preserves JSON facts and adds only the selected lazy view',()=>{
 resetLocaleDictionaries();registerLocaleDictionary('de',{schema:1,locale:'de',translations:{White:'Weiß'}});
 const data={color:{tr:'Beyaz',en:'White',ru:'Белый',ar:'أبيض'},sku:'ND683',price:800},before=JSON.stringify(data);
 assert.equal(localizeDataTree(data,'tr'),data);assert.equal(Object.hasOwn(data.color,'de'),false);
 localizeDataTree(data,'de');assert.equal(data.color.de,'Weiß');assert.equal(Object.hasOwn(data.color,'kk'),false);assert.equal(JSON.stringify(data),before);
});
test('long product prose loads once on demand, remains strict, and binds to the same inventory',async()=>{
 resetLocaleDictionaries();const requests=[];
 const description={tr:'Açıklama',en:'Detailed product description',ru:'Описание',ar:'وصف'};
 const fetcher=async url=>{requests.push(url);return {ok:true,json:async()=>({schema:1,locale:'de',sourceInventorySha256:'inventory-a',translations:url.includes('.catalogue.')?{'Detailed product description':'Ausführliche Produktbeschreibung'}:{White:'Weiß'}})}};
 await ensureLocale('de',{fetcher});assert.equal(requests.length,1);assert.equal(hasLocaleData({description},'de'),false);
 await Promise.all([ensureLocaleData({description},'de',{fetcher}),ensureLocaleData({description},'de',{fetcher})]);
 assert.equal(requests.length,2);assert.equal(hasLocaleData({description},'de'),true);assert.equal(localizedValue(description,'de'),'Ausführliche Produktbeschreibung');
 assert.equal(localizedValue({en:'White'},'de'),'Weiß');
 assert.throws(()=>registerLocaleDictionary('de',{schema:1,locale:'de',sourceInventorySha256:'another',translations:{White:'Falsch'}},{merge:true}),/locale_inventory_mismatch/);
 await assert.rejects(()=>ensureLocaleData({en:'Missing prose',tr:'Eksik',ru:'',ar:''},'de',{fetcher}),/locale_catalogue_incomplete/);
});
test('missing native strings fail visibly instead of silently substituting English or Turkish',()=>{
 resetLocaleDictionaries();assert.throws(()=>localizedValue({tr:'Beyaz',en:'White'},'az'),/locale_dictionary_unavailable/);
 registerLocaleDictionary('az',{schema:1,locale:'az',translations:{White:'Ağ'}});assert.throws(()=>localizedValue({en:'Unknown text'},'az'),/locale_translation_missing/);
 assert.equal(localizedValue({en:'White'},'az'),'Ağ');assert.equal(localizedValue(null,'az'),'');
 assert.throws(()=>registerLocaleDictionary('../de',{schema:1,locale:'de',translations:{}}),/invalid_locale/);
});
