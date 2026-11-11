/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/mixed-tax.test.ts
 * Açıklama   : Karma sınıf vergisinde tamsayı ve indirim dağılımı sözleşmesi.
 */
import {describe,it,expect} from 'vitest';
import {calculateMixedProductTax,applyShippingTax} from '../../src/server/shipping-tax';
import {HttpError} from '../../src/server/security';

describe('KDV dahil karma SKU sınıfı hesabı',()=>{
 it('küresel kuponu satırlara dağıtır ve her satırın kendi oranını uygular',()=>{
  const result=calculateMixedProductTax([{grossMinor:36003,rateBps:2000},{grossMinor:22006,rateBps:1000}],9862);
  expect(result.subtotalMinor).toBe(58009);expect(result.discountMinor).toBe(9862);expect(result.grossAfterDiscountMinor).toBe(48147);
  expect(result.lines.map(line=>line.discountMinor)).toEqual([6121,3741]);
  expect(result.lines.map(line=>line.taxMinor)).toEqual([4980,1660]);expect(result.goodsTaxMinor).toBe(6640);
  expect(result.lines.map(line=>line.netMinor)).toEqual([24902,16605]);
 });
 it('kargo vergi payını ürün satırlarına dağıtmaz veya dahil toplamı şişirmez',()=>{
  const products=calculateMixedProductTax([{grossMinor:36003,rateBps:2000},{grossMinor:22006,rateBps:1000}],9862);
  const result=applyShippingTax({subtotalMinor:products.subtotalMinor,discountMinor:products.discountMinor,shippingMinor:1200,taxMinor:products.goodsTaxMinor,totalMinor:49347},{id:'shipping-test',rateBps:2000,source:'Yalnız test'});
  expect(result.goodsTaxMinor).toBe(6640);expect(result.shippingTaxMinor).toBe(200);expect(result.taxMinor).toBe(6840);expect(result.totalMinor).toBe(49347);
 });
 it('sıfır oran, tam indirim ve ücretsiz satırda negatif/veri kaybı üretmez',()=>{
  const zero=calculateMixedProductTax([{grossMinor:0,rateBps:2000},{grossMinor:100,rateBps:0}],100);
  expect(zero.lines.map(line=>line.discountMinor)).toEqual([0,100]);expect(zero.goodsTaxMinor).toBe(0);expect(zero.grossAfterDiscountMinor).toBe(0);
  expect(calculateMixedProductTax([{grossMinor:0,rateBps:0}],0).lines[0].taxMinor).toBe(0);
 });
 it('bir alt birimlik indirim deterministiktir, satır toplamları korunur',()=>{
  const result=calculateMixedProductTax([{grossMinor:1,rateBps:2000},{grossMinor:1,rateBps:1000},{grossMinor:1,rateBps:0}],1);
  expect(result.lines.map(line=>line.discountMinor)).toEqual([1,0,0]);
  expect(result.lines.reduce((sum,line)=>sum+line.discountMinor,0)).toBe(1);
  expect(result.lines.reduce((sum,line)=>sum+line.netMinor+line.taxMinor,0)).toBe(2);
 });
 it('kesirli/negatif/aşırı tutar, geçersiz oran ve subtotalı aşan indirimi reddeder',()=>{
  for(const lines of [[{grossMinor:1.1,rateBps:2000}],[{grossMinor:-1,rateBps:2000}],[{grossMinor:9e12+1,rateBps:0}],[{grossMinor:1,rateBps:10001}],[{grossMinor:1,rateBps:-1}]])expect(()=>calculateMixedProductTax(lines,0)).toThrow(HttpError);
  expect(()=>calculateMixedProductTax([{grossMinor:1,rateBps:0}],2)).toThrow(HttpError);
  expect(()=>calculateMixedProductTax([{grossMinor:9e12,rateBps:2000},{grossMinor:1,rateBps:1000}],0)).toThrow(HttpError);
  expect(()=>calculateMixedProductTax([],0)).toThrow(HttpError);
 });
});
