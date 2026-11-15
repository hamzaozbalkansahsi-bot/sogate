import test from 'node:test';
import assert from 'node:assert/strict';
import {formatMoney} from '../web/shop-core.js';
import {setCurrency} from '../web/currency.js?v=target-locales-20261111-r1';
test('native languages format amounts with their own locale instead of Turkish punctuation',()=>{
 setCurrency('TRY');
 for(const locale of ['de','az','kk','tk','uz','ky','fa'])assert.equal(formatMoney(1234567,locale),new Intl.NumberFormat(locale,{style:'currency',currency:'TRY'}).format(12345.67),locale);
});
