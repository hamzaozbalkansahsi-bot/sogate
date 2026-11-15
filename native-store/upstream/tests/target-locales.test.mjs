import test from 'node:test';
import assert from 'node:assert/strict';
import {storeLocales,localeForCountry,localeCurrency,isRtlLocale,normalizeStoreLocale} from '../lib/locale-registry.mjs';
import {countryLocale} from '../web/visitor-market.js';
import {countryPreference,languagePreference} from '../web/market-preferences.js';
test('every export target selects its native store language, never a substitute English or Russian page',()=>{
 for(const [country,locale]of Object.entries({TR:'tr',DE:'de',GB:'en',AZ:'az',KZ:'kk',TM:'tk',UZ:'uz',KG:'ky',IR:'fa',IQ:'ar',SY:'ar'})){
  assert.equal(localeForCountry(country),locale);assert.equal(countryLocale(country),locale);assert.equal(countryPreference(country).locale,locale);assert.equal(languagePreference(locale).currency,localeCurrency(locale));
 }
 assert.equal(storeLocales.length,11);assert.equal(new Set(storeLocales).size,11);assert.equal(localeForCountry('ZZ'),null);
});
test('language tags, RTL and country currencies are validated independently',()=>{
 for(const l of storeLocales)assert.equal(normalizeStoreLocale(l),l);
 for(const l of ['ar','fa'])assert.equal(isRtlLocale(l),true);
 for(const l of ['de','az','kk','tk','uz','ky'])assert.equal(isRtlLocale(l),false);
 for(const bad of ['<script>','de-DE-x-evil','ZZ','../../fa'])assert.equal(normalizeStoreLocale(bad),null);
 assert.equal(localeCurrency('de'),'EUR');assert.equal(localeCurrency('az'),'AZN');assert.equal(localeCurrency('kk'),'KZT');
 for(const l of ['tk','uz','ky','fa'])assert.equal(localeCurrency(l),'USD');
});
