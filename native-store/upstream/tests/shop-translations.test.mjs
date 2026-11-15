import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {registerLocaleDictionary,nativeLocales} from '../web/locale-runtime.js';
import {shopCopy,locales,shopTranslate} from '../web/shop-i18n.js';

test('storefront controls have complete text in all eleven supported languages',async()=>{
 for(const locale of nativeLocales)registerLocaleDictionary(locale,JSON.parse(await readFile(new URL('../web/locales/'+locale+'.json',import.meta.url),'utf8')));
 const source=(await Promise.all(['app.js','shopping-ui.js'].map(file=>readFile(new URL('../web/'+file,import.meta.url),'utf8')))).join('\n');
 const html=await readFile(new URL('../web/index.html',import.meta.url),'utf8');
 const keys=new Set([...source.matchAll(/(?<![.\w])t\('([^']+)'\)/g)].map(match=>match[1]));
 for(const key of ['compare','collections','recent','productMaterial','productScope','specGroupFeatures','unitPrice','code','productColor','dimensionWidth','dimensionHeight','dimensionDepth','fitTooLarge','fitUnknown','fitCheck','fitFits','save','removeCollectionItem'])keys.add(key);
 for(const match of html.matchAll(/data-(?:i18n|label|placeholder)="([^"]+)"/g))keys.add(match[1]);
 assert.ok(keys.size>50,'The page control vocabulary must be checked');
 for(const locale of locales){
  assert.deepEqual(Object.keys(shopCopy[locale]).sort(),Object.keys(shopCopy.tr).sort());
  for(const key of keys){
   assert.equal(typeof shopCopy[locale][key],'string',`${locale}: ${key}`);
   assert.ok(shopCopy[locale][key].trim(),`${locale}: ${key}`);
   assert.equal(shopTranslate(key,locale),shopCopy[locale][key]);
  }
 }
});
