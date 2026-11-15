import {test} from 'node:test';
import assert from 'node:assert/strict';
import {translateText,translationIsComplete,translateCategory,categoryTranslationIsComplete} from '../lib/translations.mjs';

test('furniture titles put the furniture noun before feature details and preserve measurements',()=>{
  const source='Diamond Sürgülü 5 Raflı Çok Amaçlı Dolap - Mat Beyaz 91x105x37 cm (GxYxD)';
  const en=translateText(source,'en',{kind:'title'});
  assert.ok(en.startsWith('Diamond Storage cabinet'));
  assert.ok(en.includes('5 shelves'));
  assert.ok(en.includes('91x105x37 cm'));
  assert.equal(translationIsComplete(source,'en',{kind:'title'}),true);
});

test('recognized numbered technical features translate without losing counts',()=>{
  assert.equal(translateText('2 adet sabit raf','en',{kind:'specValue'}),'2 fixed shelves');
  assert.equal(translationIsComplete('2 adet sabit raf','en',{kind:'specValue'}),true);
  assert.equal(translateText('Ürün 3 Koliden oluşmaktadır.','en',{kind:'specValue'}),'3 packages');
});

test('unrecognized technical lines remain entirely in their source language',()=>{
  const source='Özel Raflı gövde ile yeni teknoloji';
  assert.equal(translateText(source,'en',{kind:'specValue'}),source);
  assert.equal(translateText(source,'ru',{kind:'specValue'}),source);
  assert.equal(translateText(source,'ar',{kind:'specValue'}),source);
  assert.equal(translationIsComplete(source,'en',{kind:'specValue'}),false);
});

test('known lines still translate beside an explicitly incomplete source line',()=>{
  const source='Beyaz\nÖzel Raflı gövde ile yeni teknoloji';
  assert.equal(translateText(source,'en',{kind:'specValue'}),'White\nÖzel Raflı gövde ile yeni teknoloji');
  assert.equal(translationIsComplete(source,'en',{kind:'specValue'}),false);
});

test('all four locales have precise category terms rather than exposing slugs',()=>{
  assert.equal(translateCategory(null,'yatak-odasi','tr'),'Yatak odası');
  assert.equal(translateCategory(null,'yatak-odasi','en'),'Bedroom');
  assert.equal(translateCategory(null,'yatak-odasi','ru'),'Спальня');
  assert.equal(translateCategory(null,'yatak-odasi','ar'),'غرفة النوم');
  assert.equal(categoryTranslationIsComplete(null,'yatak-odasi','ar'),true);
});
