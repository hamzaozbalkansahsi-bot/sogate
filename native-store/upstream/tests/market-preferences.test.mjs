import test from 'node:test';
import assert from 'node:assert/strict';
import {languagePreference,countryPreference,restorePreference} from '../web/market-preferences.js';
test('a language change resets the display currency and never changes the delivery country',()=>{
 for(const [locale,currency]of Object.entries({tr:'TRY',en:'USD',ru:'RUB',ar:'SAR',de:'EUR',az:'AZN',kk:'KZT',tk:'USD',uz:'USD',ky:'USD',fa:'USD'}))assert.deepEqual(languagePreference(locale),{locale,currency,source:'language'});
 assert.equal(languagePreference('invalid').locale,'en');
});
test('map country selection pairs a supported language with the country currency',()=>{
 for(const [country,locale,currency]of [['TR','tr','TRY'],['DE','de','EUR'],['GB','en','GBP'],['KZ','kk','KZT'],['AZ','az','AZN'],['IQ','ar','USD']])assert.deepEqual(countryPreference(country),{locale,currency,source:'country',country});
 assert.throws(()=>countryPreference('ZZ'));
});
test('old mismatched currencies are migrated while an explicit override survives refresh',()=>{
 assert.equal(restorePreference('tr','KZT').currency,'TRY');
 assert.equal(restorePreference('tr',{locale:'ru',currency:'KZT',source:'country'}).currency,'TRY');
 assert.equal(restorePreference('tr',{locale:'tr',currency:'KZT',source:'manual'}).currency,'KZT');
 assert.equal(restorePreference('de',countryPreference('DE')).currency,'EUR');
 assert.equal(restorePreference('tr',{locale:'tr',currency:'BAD',source:'manual'}).currency,'TRY');
});
