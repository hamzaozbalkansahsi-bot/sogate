/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/bundle-management.test.ts
 * Açıklama   : Set önizlemesinin eklenen, çıkarılan ve adedi değişen fiziksel satırları doğru ayırmasını sınar.
 */
import {describe,expect,it} from 'vitest';
import {bundleDifferences} from '../../src/shared/bundle-management';
describe('Bundle changes',()=>{
 it('does not treat row ordering as a composition change',()=>expect(bundleDifferences([{variantId:'a',quantity:2},{variantId:'b',quantity:1}],[{variantId:'b',quantity:1},{variantId:'a',quantity:2}])).toEqual([]));
 it('shows a new component with a zero previous quantity',()=>expect(bundleDifferences([],[{variantId:'a',quantity:2}])).toEqual([{variantId:'a',beforeQuantity:0,afterQuantity:2}]));
 it('shows removed components with a zero new quantity',()=>expect(bundleDifferences([{variantId:'a',quantity:2}],[])).toEqual([{variantId:'a',beforeQuantity:2,afterQuantity:0}]));
 it('keeps unchanged rows out of a quantity preview',()=>expect(bundleDifferences([{variantId:'a',quantity:2},{variantId:'b',quantity:1}],[{variantId:'a',quantity:3},{variantId:'b',quantity:1}])).toEqual([{variantId:'a',beforeQuantity:2,afterQuantity:3}]));
 it('sorts changed SKU IDs deterministically without modifying the input',()=>{const before=[{variantId:'z',quantity:2}],after=[{variantId:'b',quantity:1},{variantId:'a',quantity:3}];expect(bundleDifferences(before,after).map(row=>row.variantId)).toEqual(['a','b','z']);expect(before).toEqual([{variantId:'z',quantity:2}]);expect(after[0].variantId).toBe('b');});
});
