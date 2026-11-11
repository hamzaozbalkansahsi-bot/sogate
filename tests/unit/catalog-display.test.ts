/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/catalog-display.test.ts
 * Açıklama   : Kartın SQL min fiyat sıralamasıyla aynı fiyatı ve ona ait seçeneği göstermesini sınar.
 */
import {describe,it,expect} from 'vitest';
import {selectCatalogDisplay} from '../../src/shared/catalog-display';
import type {Currency,Variant} from '../../src/shared/contracts';
function option(id:string,displayPriceMinor:number|null,displayCurrency:Currency='TRY'):Variant{return {id,sku:id,name:`Türkçe ${id}`,nameEn:`English ${id}`,priceMinor:9999,currency:'TRY',displayPriceMinor,displayCurrency,available:1};}
describe('Kart fiyatı ve varyant temsili',()=>{
 it('SQL min fiyatıyla sıralanan A(1000,100), B(200) kartlarını 100,200 olarak temsil eder',()=>{
  const first=option('önceki',1000),cheap=option('sonraki',100),middle=option('ikinci',200),a=selectCatalogDisplay([first,cheap],'TRY'),b=selectCatalogDisplay([middle],'TRY');expect([a.priceMinor,b.priceMinor]).toEqual([100,200]);expect(a.variant).toBe(cheap);expect(a.variant?.name).toBe('Türkçe sonraki');expect(a.variant?.nameEn).toBe('English sonraki');
 });
 it('yalnız seçili gösterim para birimine bakar; temel TRY fiyatını döviz fiyatı yapmaz',()=>{
  const cheapTry=option('TRY',1),eur=option('EUR',250,'EUR');expect(selectCatalogDisplay([cheapTry,eur],'EUR')).toEqual({variant:eur,priceMinor:250});expect(selectCatalogDisplay([cheapTry],'USD').priceMinor).toBeNull();
 });
 it('eşleşen varyant altkümesinden seçim yapar',()=>{
  const matching=option('eşleşen-L',500);expect(selectCatalogDisplay([matching],'TRY')).toEqual({variant:matching,priceMinor:500});
 });
 it('eksik fiyatı sıfıra dönüştürmez ve boş listede varyant uydurmaz',()=>{
  const missing=option('eksik',null);expect(selectCatalogDisplay([missing],'TRY')).toEqual({variant:missing,priceMinor:null});expect(selectCatalogDisplay([],'GBP')).toEqual({variant:undefined,priceMinor:null});
 });
 it('sıfır, negatif, kesirli, sonsuz ve güvenli aralık dışı fiyatlar sunucudaki geçerli fiyat değildir',()=>{
  for(const value of [0,-1,1.2,Infinity,NaN,9_000_000_000_001])expect(selectCatalogDisplay([option('geçersiz',value)],'TRY').priceMinor).toBeNull();
 });
 it('geçersiz erken değer geçerli en düşük fiyatı gölgelemez',()=>{
  const valid=option('geçerli',250);expect(selectCatalogDisplay([option('boş',null),option('yanlış',NaN),valid],'TRY')).toEqual({variant:valid,priceMinor:250});
 });
 it('eşit fiyatlarda sunucunun varyant sırasını korur, kaynak diziyi değiştirmez',()=>{
  const first=option('bir',100),second=option('iki',100),variants=Object.freeze([first,second]);expect(selectCatalogDisplay(variants,'TRY').variant).toBe(first);expect(variants).toEqual([first,second]);
 });
});
