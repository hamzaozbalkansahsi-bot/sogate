import test from 'node:test';
import assert from 'node:assert/strict';
import {productAbout,productSuggestions,productShareData,shareChannels,withoutColorSuffix} from '../web/product-presentation.js';

test('product titles move only a known separated colour suffix into its own field',()=>{
 assert.equal(withoutColorSuffix('Handy Mate Masif 5li Elbise Askısı-Naturel','Naturel'),'Handy Mate Masif 5li Elbise Askısı');
 assert.equal(withoutColorSuffix('Raf — White (Oak)','White (Oak)'),'Raf');
 assert.equal(withoutColorSuffix('White Oak koleksiyonu','White Oak'),'White Oak koleksiyonu');
 assert.equal(withoutColorSuffix('Oakland','Oak'),'Oakland');
});

test('product about separates repeated identity from the actual features in all four languages',()=>{
 const p={id:'2541',code:'Ndn-HMA-012-NT-5',name:{tr:'Askı',en:'Hanger',ru:'Вешалка',ar:'شماعة'},variantColor:{tr:'Naturel',en:'Natural',ru:'Натуральный',ar:'طبيعي'},description:{tr:'Askı. Renk: Naturel. Ürün kodu: Ndn-HMA-012-NT-5.',en:'Hanger. Finish: Natural. Product code: Ndn-HMA-012-NT-5.',ru:'Вешалка. Отделка: Натуральный. Код товара: Ndn-HMA-012-NT-5.',ar:'شماعة. اللون: طبيعي. رمز المنتج: Ndn-HMA-012-NT-5.'},specs:[{label:{tr:'Ürün Özellikleri'},value:{tr:'Masif ahşap\n5 adet\nMasif ahşap',en:'Solid wood\nSet of 5',ru:'Массив\n5 штук',ar:'خشب صلب\n5 قطع'}}]};
 for(const [locale,want]of [['tr',['Masif ahşap','5 adet']],['en',['Solid wood','Set of 5']],['ru',['Массив','5 штук']],['ar',['خشب صلب','5 قطع']]]){
  const result=productAbout(p,locale);assert.deepEqual(result.paragraphs,[]);assert.deepEqual(result.highlights,want);
 }
});

test('about preserves meaningful prose, scope notes and measurements with decimal points',()=>{
 const p={name:{tr:'Raf'},code:'Ndn-RAF-1',description:{tr:'Raf. Bu parça yalnızca üst modülü içerir. Ölçüler: 120 x 25.5 x 20 cm. Renk: Sarı. Ürün kodu: Ndn-RAF-1.'},specs:[{label:{tr:'Ürün Ölçüleri'},value:{tr:'120 x 25.5 x 20 cm'}},{label:{tr:'Ürün Rengi'},value:{tr:'Sarı'}}]};
 assert.deepEqual(productAbout(p,'tr').paragraphs,['Bu parça yalnızca üst modülü içerir.']);
 p.description.tr='Nemden uzak tutun. Özel <malzeme> için bakım bilgilerini okuyun.';
 assert.deepEqual(productAbout(p,'tr').paragraphs,[p.description.tr]);
});

test('suggestions exclude the selected model and repeated colour variants across shelves',()=>{
 const categories=[{id:'root',parentId:null},{id:'chairs',parentId:'root'},{id:'tables',parentId:'root'},{id:'other',parentId:null}];
 const p={id:'1',modelId:'chair-a',categoryIds:['root','chairs']};
 const products=[p,{id:'2',modelId:'chair-a',categoryIds:['chairs']},{id:'3',modelId:'chair-b',categoryIds:['root','chairs']},{id:'4',modelId:'chair-b',categoryIds:['chairs']},{id:'5',modelId:'table-a',categoryIds:['root','tables']},{id:'6',modelId:'unrelated',categoryIds:['other']}];
 const s=productSuggestions(p,products,categories,['2','3','6','missing']);
 assert.deepEqual(s.similar.map(p=>p.id),['3']);assert.deepEqual(s.complementary.map(p=>p.id),['5']);assert.deepEqual(s.recent.map(p=>p.id),['3','6']);
 assert.ok(![...s.similar,...s.complementary,...s.recent].some(p=>p.modelId==='chair-a'));
});

test('sharing includes selected product URL and exact Turkish invitation; channels encode it safely',()=>{
 const data=productShareData({title:'Askı',url:'https://nodenohome.com/?product=2541&lang=tr',locale:'tr'});
 assert.equal(data.text,'Görmeni istediğim bir ürün var; https://nodenohome.com/?product=2541&lang=tr');
 assert.equal(data.url,'https://nodenohome.com/?product=2541&lang=tr');
 const links=shareChannels(data);assert.equal(new URL(links.whatsapp).searchParams.get('text'),data.text);
 assert.equal(new URL(links.facebook).searchParams.get('u'),data.url);
 assert.equal(new URL(links.x).searchParams.get('text'),data.text);
 assert.ok(decodeURIComponent(links.email).includes(data.text));assert.ok(decodeURIComponent(links.sms).includes(data.text));
 assert.throws(()=>productShareData({title:'x',url:'javascript:alert(1)',locale:'tr'}));
 assert.throws(()=>productShareData({title:'x',url:'https://evil.example/?product=1',locale:'tr'}));
});
