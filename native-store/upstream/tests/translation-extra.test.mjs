import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {extraTranslations,extraTranslate,extraTranslationIsComplete} from '../lib/translation-extra.mjs';
import {translateText,translationIsComplete} from '../lib/translations.mjs';

const locales=['en','ru','ar'];
const options={kind:'specValue'};
const merchantPolicy=/garanti|warranty|teslimat|kargo|sipariş|ödeme|0850|fiyat|iade/iu;

test('all 955 curated technical source lines have translations in every target language',()=>{
  const translated=new Map(extraTranslations.map(row=>[row.tr,row]));
  assert.equal(translated.size,955);
  assert.equal(extraTranslations.length,translated.size,'Duplicate exact source lines');
  for(const row of extraTranslations){
    const {tr}=row;
    for(const locale of locales){
      assert.ok(row[locale]?.trim(),`Missing ${locale}: ${tr}`);
      assert.notEqual(row[locale],tr,`Untranslated ${locale}: ${tr}`);
      assert.equal(translationIsComplete(tr,locale,options),true,`Core lookup omitted ${locale}: ${tr}`);
    }
  }
});

test('all merchant-safe technical specifications across the 667 source products are complete',()=>{
  const catalogue=JSON.parse(readFileSync(new URL('../data/catalog-source.json',import.meta.url),'utf8'));
  assert.equal(catalogue.products.length,667);
  for(const product of catalogue.products)for(const spec of product.specs??[]){
    if(merchantPolicy.test(spec.label))continue;
    for(const line of spec.value.split(/\r?\n/)){
      if(merchantPolicy.test(line))continue;
      for(const locale of locales)assert.equal(translationIsComplete(line,locale,options),true,`${product.code} ${locale}: ${line}`);
    }
  }
});

test('complete electrical and load instructions retain all technical values',()=>{
  const examples=[
    ['Çalışma Voltaji: AC100-240V Frekans 50/60 Hz',['100','240','50','60']],
    ['Çalışma Ortam Sıcaklığı: -10 / +40 Santigrat Derece',['10','40']],
    ['72-117 cm arası çalışma yüksekliğine sahiptir.',['72','117']],
    ['Bu masa en fazla 60 kg yük kaldırabilir. Daha fazla yük koymaktan, üzerine oturmayınız, yükselti aracı veya merdiven amacı ile üzerine çıkmayınız ve bu amaçla kesinlikle kullanmayınız.',['60']],
    ['Malzeme : 1 mm boru profil ve 2 mm sac',['1','2']],
    ['%30 Pamuk + %30 Keten + %40 Polyester kumaş',['30','30','40']],
  ];
  for(const [tr,numbers] of examples)for(const locale of locales){
    const text=translateText(tr,locale,options);
    for(const number of numbers)assert.ok(text.includes(number),`${locale} lost ${number}: ${tr}`);
    assert.doesNotMatch(text,/[çğıİşŞ]/u,`${locale} retained a Turkish fragment: ${text}`);
    assert.ok(extraTranslationIsComplete(tr,locale));
  }
});

test('armrest mechanisms preserve distinctions between USB-C and C-type cable channels',()=>{
  for(const locale of locales){
    assert.ok(extraTranslate('4D ayarlanabilir Kolçak',locale).includes('4D'));
    assert.ok(extraTranslate('C tipi ve standart usb şarj girişi mevcuttur.',locale).includes('USB-C'));
    assert.ok(!extraTranslate("C tipi masa üstü kablo kanalı ve 2'li USB şarj girişi",locale).includes('USB-C'));
  }
});

test('an unknown specification remains the exact original and is reported incomplete',()=>{
  const source='Henüz tanımlanmamış özgün mekanizma 123 mm';
  for(const locale of locales){
    assert.equal(extraTranslate(source,locale),source);
    assert.equal(extraTranslationIsComplete(source,locale),false);
    assert.equal(translateText(source,locale,options),source);
    assert.equal(translationIsComplete(source,locale,options),false);
  }
});
