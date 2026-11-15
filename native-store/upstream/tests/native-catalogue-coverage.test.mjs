import test from 'node:test';
import assert from 'node:assert/strict';
import {verifyNativeCatalogue} from '../lib/native-locales.mjs';
import {nativeLocales} from '../web/locale-runtime.js';
test('a new catalogue cannot bypass native coverage while codes and explicit native values remain intact',()=>{
 const dictionaries=Object.fromEntries(nativeLocales.map(locale=>[locale,{translations:{'White':'native-'+locale}}]));
 const product={code:'ND683',color:{tr:'Beyaz',en:'White',ru:'Белый',ar:'أبيض'},model:{tr:'Bohera',en:'Bohera',ru:'Bohera',ar:'Bohera'}};
 assert.doesNotThrow(()=>verifyNativeCatalogue(product,dictionaries));
 product.description={tr:'Açıklama',en:'Unreviewed new prose',ru:'Описание',ar:'وصف'};
 assert.throws(()=>verifyNativeCatalogue(product,dictionaries),/Native catalogue translation missing/);
 for(const locale of nativeLocales)product.description[locale]='Explicit translated prose '+locale;
 assert.doesNotThrow(()=>verifyNativeCatalogue(product,dictionaries));
});
