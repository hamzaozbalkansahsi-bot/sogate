import test from 'node:test';import assert from 'node:assert/strict';
import {countryLabel} from '../web/country-labels.js';
import {registerLocaleDictionary,resetLocaleDictionaries} from '../web/locale-runtime.js';
test('native country names do not depend on browser Intl falling back to Turkish',()=>{
 resetLocaleDictionaries();registerLocaleDictionary('kk',{schema:1,locale:'kk',translations:{Germany:'Германия',Turkey:'Түркия','Türkiye':'Түркия',Kazakhstan:'Қазақстан'}});
 const saved=Intl.DisplayNames;Intl.DisplayNames=class{constructor(){throw new Error('browser locale data unavailable')}};
 try{assert.equal(countryLabel('DE','kk'),'Германия');assert.equal(countryLabel('KZ','kk'),'Қазақстан');assert.equal(countryLabel('DE','tr'),'Almanya');assert.equal(countryLabel('US','kk'),'Америка Құрама Штаттары');assert.equal(countryLabel('US','tr'),'Amerika Birleşik Devletleri');assert.equal(countryLabel('ZZ','kk'),'ZZ');}finally{Intl.DisplayNames=saved;}
});
