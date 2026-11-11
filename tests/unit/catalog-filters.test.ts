/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/catalog-filters.test.ts
 * Açıklama   : Katalog sorgularının tekil, sınırlı ve Türkçe veriyi koruyan sözleşmesini sınar.
 */
import {describe,it,expect} from 'vitest';
import {parseCatalogQuery,validateCatalogFilter} from '../../src/server/commerce/catalog';

describe('Katalog sorgu sınırı',()=>{
 it('Türkçe marka, beden, renk ve güç türünü değiştirmeden okur',()=>{
  expect(parseCatalogQuery(new URLSearchParams({q:'İç Giyim',brand:'Özgür Atölye',size:'Özel Ölçü',color:'Gül Kurusu',power:'Şarjlı USB-C',material:'İpek',min:'1099',max:'30000',available:'1',locale:'tr',currency:'EUR',page:'2',sort:'price-asc'}))).toEqual({q:'İç Giyim',brand:'Özgür Atölye',size:'Özel Ölçü',color:'Gül Kurusu',power:'Şarjlı USB-C',material:'İpek',min:1099,max:30000,available:true,locale:'tr',currency:'EUR',page:2,sort:'price_asc'});
 });
 it('varsayılan dili ayrı tercihten alır; fiyat ve ülke kuralı üretmez',()=>{
  expect(parseCatalogQuery(new URLSearchParams(),{locale:'en',currency:'GBP'})).toEqual({locale:'en',currency:'GBP',page:1,sort:'newest'});
 });
 it('yalnız tanımlı iki gerçek özellik işaretini ve tekrar etmeyen değerleri kabul eder',()=>{
  const query=new URLSearchParams('features=liquid&features=hygiene-sealed');expect(parseCatalogQuery(query).features).toEqual(['liquid','hygiene-sealed']);
  for(const raw of ['features=waterproof','features=medical','features=liquid&features=liquid'])expect(()=>parseCatalogQuery(new URLSearchParams(raw))).toThrow();
 });
 it.each(['page=NaN','page=Infinity','page=0','page=1.2','page=100001','min=-1','min=','max=9000000000001','min=900&max=100','available=true','sort=random','currency=BTC','locale=ar','lotTracking=1','stock=5','q=a&q=b','brand=a&brand=b'])('belirsiz veya desteklenmeyen sorguyu reddeder: %s',raw=>{
  expect(()=>parseCatalogQuery(new URLSearchParams(raw))).toThrow();
 });
 it('alan uzunluğunu ve kontrol karakterlerini sınırlarken kalıcı Türkçe veriye dokunmaz',()=>{
  const invalid:Record<string,string>[]=[{q:'a'.repeat(121)},{brand:'b'.repeat(201)},{color:'Bordo\u0000'},{power:'pil\nşarj'}];for(const query of invalid)expect(()=>parseCatalogQuery(new URLSearchParams(query))).toThrow();
  expect(validateCatalogFilter({q:'  ölçü  ',brand:'İpek & Şıklık'}).brand).toBe('İpek & Şıklık');
 });
 it('doğrudan sunucu çağrısında da sayıları, rol dışı alanları ve SQL sort girdisini reddeder',()=>{
  for(const filter of [{page:NaN},{min:Infinity},{min:1.1},{available:'false'},{sort:'name;DROP TABLE products'},{costMinor:100},{features:['certified']}])expect(()=>validateCatalogFilter(filter)).toThrow();
 });
 it('ürün detay adresinde yalnız dil ve gösterim para birimini kabul eder',()=>{
  expect(parseCatalogQuery(new URLSearchParams('locale=en&currency=USD'),{},true)).toMatchObject({locale:'en',currency:'USD'});
  expect(()=>parseCatalogQuery(new URLSearchParams('brand=Örnek'),{},true)).toThrow();
 });
});
